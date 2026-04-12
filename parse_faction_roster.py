"""
parse_faction_roster.py
=======================
Parses a New Recruit faction roster HTML file and outputs:
  1. parser_output/<slug>_parsed.json  — structured unit data
  2. parser_output/<slug>_mapping.csv  — card -> DB name mapping template

On re-runs, the mapping CSV is MERGED: existing db_name / gw_sku / include
values are preserved, and only genuinely new cards get blank rows appended.
This means you only ever maintain one CSV per faction.

Usage:
    python parse_faction_roster.py <path/to/FACTION.html>
    python parse_faction_roster.py <path/to/FACTION.html> --output-dir some/other/dir

Requirements:
    pip install beautifulsoup4
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import date

from bs4 import BeautifulSoup

# Default output directory (relative to this script's location)
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'parser_output')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Strip whitespace and normalise non-breaking spaces."""
    return text.replace('\xa0', ' ').strip()


def normalize_save(value: str) -> str:
    """
    Ensure save/leadership values end with '+'.
    '3' -> '3+', '5+' -> '5+', '-' -> '-', 'N/A' -> 'N/A'
    """
    v = value.strip()
    if re.match(r'^\d+$', v):
        return v + '+'
    return v


def clean_keywords(raw: str) -> str:
    """
    Normalise weapon keyword strings.
    Strips surrounding whitespace, trailing commas, and extra spaces.
    '-' is treated as no keywords (returns empty string).
    """
    kw = raw.strip().rstrip(',').strip()
    return '' if kw == '-' else kw


def strip_arrow(name: str) -> str:
    """Remove the ➤ / > sub-profile arrow prefix from weapon names."""
    return re.sub(r'^[➤>]\s*', '', name).strip()


def slug_from_path(html_path: str) -> str:
    """
    Derive a clean file slug from the HTML filename.
    'POINTS_BLACK TEMPLAR.html' -> 'black_templar'
    'POINTS_GUARD.html'         -> 'guard'
    """
    base = os.path.splitext(os.path.basename(html_path))[0]
    base = re.sub(r'^POINTS[_\s]*', '', base, flags=re.IGNORECASE)
    return re.sub(r'[\s\-]+', '_', base).lower()


def detect_faction_name(soup: BeautifulSoup) -> str:
    """Read the faction name from the roster header, fall back gracefully."""
    header = soup.find(class_='roster-header')
    if header:
        text = clean_text(header.get_text())
        text = re.sub(r'\[.*?\]', '', text).strip()           # strip [11095pts]
        text = re.sub(r'^POINTS[_\s]+', '', text,             # strip POINTS_ prefix
                      flags=re.IGNORECASE).strip()
        if text:
            return text.title()
    return 'Unknown Faction'


# ---------------------------------------------------------------------------
# Core parsers
# ---------------------------------------------------------------------------

def parse_stat_rows(group_table) -> list[dict]:
    """
    Extract all model stat rows from a 'Unit MTSVWLDOC' profile-group table.
    Returns one dict per model row.
    """
    models = []
    for row in group_table.find_all('tr', class_='section profile row'):
        cells = [clean_text(td.get_text()) for td in row.find_all('td')]
        if len(cells) < 7:
            continue
        models.append({
            'model': cells[0],
            'M':     cells[1],
            'T':     cells[2],
            'SV':    normalize_save(cells[3]),
            'W':     cells[4],
            'LD':    normalize_save(cells[5]),
            'OC':    cells[6],
        })
    return models


def parse_weapon_rows(group_table, weapon_type: str) -> list[dict]:
    """
    Extract weapon profile rows from a Ranged or Melee profile-group table.
    weapon_type: 'ranged' or 'melee'
    """
    weapons = []
    for row in group_table.find_all('tr', class_='section profile row'):
        cells = [clean_text(td.get_text()) for td in row.find_all('td')]
        if len(cells) < 7:
            continue

        name         = strip_arrow(cells[0])
        keywords_raw = cells[7] if len(cells) > 7 else '-'
        keywords     = clean_keywords(keywords_raw)

        if weapon_type == 'ranged':
            weapons.append({
                'name':     name,
                'range':    cells[1],
                'A':        cells[2],
                'BS':       cells[3],
                'S':        cells[4],
                'AP':       cells[5],
                'D':        cells[6],
                'keywords': keywords,
            })
        else:  # melee — cells[1] is always 'Melee'
            weapons.append({
                'name':     name,
                'A':        cells[2],
                'WS':       cells[3],
                'S':        cells[4],
                'AP':       cells[5],
                'D':        cells[6],
                'keywords': keywords,
            })
    return weapons


def parse_ability_rows(group_table) -> tuple[list[dict], str | None, str | None]:
    """
    Extract ability rows from an 'Abilities / Description' table.
    Separates out Invulnerable Save and Feel No Pain into dedicated fields.
    Returns: (abilities, invuln_save, fnp_save)
    """
    abilities   = []
    invuln_save = None
    fnp_save    = None

    for row in group_table.find_all('tr', class_='section profile row'):
        cells = [clean_text(td.get_text()) for td in row.find_all('td')]
        if len(cells) < 2:
            continue

        aname = cells[0]
        adesc = cells[1]

        if aname == 'Invulnerable Save':
            invuln_save = adesc
        elif 'Feel No Pain' in aname:
            fnp_save = adesc
        else:
            abilities.append({'name': aname, 'description': adesc})

    return abilities, invuln_save, fnp_save


# ---------------------------------------------------------------------------
# Card parser
# ---------------------------------------------------------------------------

def parse_card(wrapper) -> dict:
    """Parse a single card-wrapper div into a structured unit dict."""
    header   = wrapper.find(class_='card-header')
    name_tag = header.find(class_='name') if header else None
    cost_tag = header.find(class_='cost') if header else None

    card_name    = clean_text(name_tag.get_text()) if name_tag else 'Unknown'
    points_raw   = clean_text(cost_tag.get_text()) if cost_tag else '0 pts'
    points_match = re.search(r'\d+', points_raw)
    points       = int(points_match.group()) if points_match else 0

    stat_models: list[dict]   = []
    ranged_weapons: list[dict] = []
    melee_weapons: list[dict]  = []
    abilities: list[dict]      = []
    invuln_save: str | None    = None
    fnp_save: str | None       = None

    for group in wrapper.find_all(class_='profile-group'):
        thead = group.find('thead')
        if not thead:
            continue
        header_text = clean_text(thead.get_text())

        if header_text.startswith('Unit'):
            stat_models = parse_stat_rows(group)
        elif header_text.startswith('Ranged Weapons'):
            ranged_weapons = parse_weapon_rows(group, 'ranged')
        elif header_text.startswith('Melee Weapons'):
            melee_weapons = parse_weapon_rows(group, 'melee')
        elif header_text.startswith('Abilities'):
            abilities, invuln_save, fnp_save = parse_ability_rows(group)

    return {
        'card_name':       card_name,
        'points':          points,
        'primary_stats':   stat_models[0] if stat_models else {},
        'all_model_stats': stat_models,
        'invuln_save':     invuln_save,
        'fnp_save':        fnp_save,
        'ranged_weapons':  ranged_weapons,
        'melee_weapons':   melee_weapons,
        'abilities':       abilities,
    }


# ---------------------------------------------------------------------------
# CSV merge helpers
# ---------------------------------------------------------------------------

def load_existing_mapping(csv_path: str) -> dict[str, dict]:
    """
    Load an existing mapping CSV into a dict keyed by card_name.
    Returns {} if the file does not exist.
    """
    if not os.path.isfile(csv_path):
        return {}

    existing = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            existing[row['card_name']] = row
    return existing


def write_merged_mapping(csv_path: str, units: list[dict],
                         faction_name: str, existing: dict[str, dict]) -> tuple[int, int]:
    """
    Write the mapping CSV, preserving any existing db_name/gw_sku/include values.
    Returns (preserved_count, new_count).
    """
    preserved = 0
    new       = 0

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['card_name', 'db_name', 'gw_sku', 'faction', 'include'])

        for unit in units:
            name = unit['card_name']
            if name in existing:
                row = existing[name]
                writer.writerow([
                    name,
                    row.get('db_name', ''),
                    row.get('gw_sku', ''),
                    faction_name,
                    row.get('include', ''),
                ])
                preserved += 1
            else:
                writer.writerow([name, '', '', faction_name, ''])
                new += 1

    return preserved, new


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Entry point."""
    arg_parser = argparse.ArgumentParser(
        description='Parse a New Recruit faction roster HTML file.'
    )
    arg_parser.add_argument('html_file', help='Path to the faction HTML file')
    arg_parser.add_argument(
        '--output-dir', default=None,
        help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})',
    )
    args = arg_parser.parse_args()

    html_path  = os.path.abspath(args.html_file)
    if not os.path.isfile(html_path):
        print(f'ERROR: File not found: {html_path}', file=sys.stderr)
        sys.exit(1)

    output_dir = os.path.abspath(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    slug = slug_from_path(html_path)

    print(f'Parsing: {html_path}')
    print(f'Output:  {output_dir}')
    print(f'Slug:    {slug}')
    print()

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup         = BeautifulSoup(html, 'html.parser')
    faction_name = detect_faction_name(soup)
    wrappers     = soup.find_all(class_='card-wrapper')

    print(f'Faction: {faction_name}')
    print(f'Cards found: {len(wrappers)}')
    print()

    units = []
    for i, wrapper in enumerate(wrappers):
        unit = parse_card(wrapper)
        units.append(unit)
        invuln_str = f'  invuln={unit["invuln_save"]}' if unit['invuln_save'] else ''
        print(f'  [{i+1:3d}] {unit["card_name"]} ({unit["points"]}pts)'
              f' | {len(unit["all_model_stats"])} models'
              f' | {len(unit["ranged_weapons"])}R {len(unit["melee_weapons"])}M'
              f' | {len(unit["abilities"])} abilities'
              f'{invuln_str}')

    # ── Write JSON ──────────────────────────────────────────────────────────
    json_path = os.path.join(output_dir, f'{slug}_parsed.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'faction':        faction_name,
            'source_file':    os.path.basename(html_path),
            'extracted_date': str(date.today()),
            'total_cards':    len(units),
            'units':          units,
        }, f, indent=2, ensure_ascii=False)
    print(f'\nWrote JSON : {json_path}')

    # ── Write / merge mapping CSV ────────────────────────────────────────────
    csv_path = os.path.join(output_dir, f'{slug}_mapping.csv')
    existing = load_existing_mapping(csv_path)
    preserved, new = write_merged_mapping(csv_path, units, faction_name, existing)

    if existing:
        print(f'Merged CSV : {csv_path}')
        print(f'  -> {preserved} existing rows preserved, {new} new rows added')
    else:
        print(f'Wrote CSV  : {csv_path}')
        print(f'  -> {new} rows (fill in db_name, gw_sku, include=yes/no)')

    print()
    print('Next: open the CSV, fill in any blank rows, hand it back for seed generation.')


if __name__ == '__main__':
    main()
