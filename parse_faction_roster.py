"""
parse_faction_roster.py
=======================
Parses a New Recruit faction roster HTML file and outputs:
  1. <slug>_parsed.json  — structured unit data (stats, weapons, abilities)
  2. <slug>_mapping.csv  — template for mapping card names → DB names / GW SKUs

Usage:
    python parse_faction_roster.py <path/to/FACTION.html> [--output-dir <dir>]

Examples:
    python parse_faction_roster.py "C:/Users/khleu/Downloads/POINTS_GUARD.html"
    python parse_faction_roster.py "C:/Users/khleu/Downloads/POINTS_AELDARI.html" --output-dir parser_output

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Strip whitespace and normalise non-breaking spaces."""
    return text.replace('\xa0', ' ').strip()


def normalize_save(value: str) -> str:
    """
    Ensure save/leadership values end with '+'.
    e.g. '3' -> '3+', '5+' -> '5+', '-' -> '-', 'N/A' -> 'N/A'
    """
    v = value.strip()
    if re.match(r'^\d+$', v):
        return v + '+'
    return v


def strip_arrow(name: str) -> str:
    """Remove the ➤ / > sub-profile arrow prefix from weapon names."""
    return re.sub(r'^[➤>]\s*', '', name).strip()


def slug_from_path(html_path: str) -> str:
    """
    Derive a clean file slug from the HTML filename.
    'POINTS_BLACK TEMPLAR.html' -> 'black_templars'
    'POINTS_GUARD.html'         -> 'guard'
    """
    base = os.path.splitext(os.path.basename(html_path))[0]
    base = re.sub(r'^POINTS[_\s]*', '', base, flags=re.IGNORECASE)
    return re.sub(r'[\s\-]+', '_', base).lower()


def detect_faction_name(soup: BeautifulSoup) -> str:
    """
    Try to read the faction/army name from the roster header.
    Falls back to 'Unknown Faction' if not found.
    """
    header = soup.find(class_='roster-header')
    if header:
        text = clean_text(header.get_text())
        # Strip trailing point totals like '[11095pts]'
        text = re.sub(r'\[.*?\]', '', text).strip()
        # Strip 'POINTS_' / 'POINTS ' prefix that New Recruit adds to the filename
        text = re.sub(r'^POINTS[_\s]+', '', text, flags=re.IGNORECASE).strip()
        # Title-case for readability (e.g. 'BLACK TEMPLAR' -> 'Black Templar')
        if text:
            return text.title()
    return 'Unknown Faction'


# ---------------------------------------------------------------------------
# Core parsers
# ---------------------------------------------------------------------------

def parse_stat_rows(group_table) -> list[dict]:
    """
    Extract all model stat rows from a 'Unit MTSVWLDOC' profile-group table.
    Returns a list of dicts, one per model row.
    """
    models = []
    for row in group_table.find_all('tr', class_='section profile row'):
        cells = [clean_text(td.get_text()) for td in row.find_all('td')]
        if len(cells) < 7:
            continue
        models.append({
            'model':  cells[0],
            'M':      cells[1],
            'T':      cells[2],
            'SV':     normalize_save(cells[3]),
            'W':      cells[4],
            'LD':     normalize_save(cells[5]),
            'OC':     cells[6],
        })
    return models


def parse_weapon_rows(group_table, weapon_type: str) -> list[dict]:
    """
    Extract all weapon profile rows from a Ranged or Melee profile-group table.
    weapon_type should be 'ranged' or 'melee'.
    """
    weapons = []
    for row in group_table.find_all('tr', class_='section profile row'):
        cells = [clean_text(td.get_text()) for td in row.find_all('td')]
        if len(cells) < 7:
            continue

        name = strip_arrow(cells[0])
        keywords_raw = cells[7] if len(cells) > 7 else '-'
        keywords = '' if keywords_raw == '-' else keywords_raw

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
        else:  # melee — cells[1] is always 'Melee', skip it
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
    Extract abilities from an 'Abilities / Description' profile-group table.
    Returns (abilities_list, invuln_save, fnp_save).
    Invulnerable Save and Feel No Pain are separated out as dedicated fields.
    """
    abilities = []
    invuln_save = None
    fnp_save = None

    for row in group_table.find_all('tr', class_='section profile row'):
        cells = [clean_text(td.get_text()) for td in row.find_all('td')]
        if len(cells) < 2:
            continue

        ability_name = cells[0]
        ability_desc = cells[1]

        if ability_name == 'Invulnerable Save':
            invuln_save = ability_desc
        elif 'Feel No Pain' in ability_name:
            fnp_save = ability_desc
        else:
            abilities.append({
                'name':        ability_name,
                'description': ability_desc,
            })

    return abilities, invuln_save, fnp_save


# ---------------------------------------------------------------------------
# Card parser
# ---------------------------------------------------------------------------

def parse_card(wrapper) -> dict:
    """Parse a single card-wrapper div into a structured unit dict."""
    # Name and points
    header = wrapper.find(class_='card-header')
    name_tag = header.find(class_='name') if header else None
    cost_tag = header.find(class_='cost') if header else None

    card_name = clean_text(name_tag.get_text()) if name_tag else 'Unknown'
    points_raw = clean_text(cost_tag.get_text()) if cost_tag else '0 pts'
    points_match = re.search(r'\d+', points_raw)
    points = int(points_match.group()) if points_match else 0

    # Collect profile-group tables and classify each by its header
    stat_models: list[dict] = []
    ranged_weapons: list[dict] = []
    melee_weapons: list[dict] = []
    abilities: list[dict] = []
    invuln_save: str | None = None
    fnp_save: str | None = None

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

    # Primary stats = first model row (the named character / base model)
    primary_stats = stat_models[0] if stat_models else {}

    return {
        'card_name':      card_name,
        'points':         points,
        'primary_stats':  primary_stats,
        'all_model_stats': stat_models,
        'invuln_save':    invuln_save,
        'fnp_save':       fnp_save,
        'ranged_weapons': ranged_weapons,
        'melee_weapons':  melee_weapons,
        'abilities':      abilities,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Parse a New Recruit faction roster HTML file.')
    parser.add_argument('html_file', help='Path to the faction HTML file')
    parser.add_argument('--output-dir', default=None,
                        help='Directory for output files (default: same as HTML file)')
    args = parser.parse_args()

    html_path = os.path.abspath(args.html_file)
    if not os.path.isfile(html_path):
        print(f'ERROR: File not found: {html_path}', file=sys.stderr)
        sys.exit(1)

    output_dir = os.path.abspath(args.output_dir) if args.output_dir else os.path.dirname(html_path)
    os.makedirs(output_dir, exist_ok=True)

    slug = slug_from_path(html_path)

    print(f'Parsing: {html_path}')
    print(f'Output:  {output_dir}')
    print(f'Slug:    {slug}')
    print()

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    faction_name = detect_faction_name(soup)
    wrappers = soup.find_all(class_='card-wrapper')

    print(f'Faction: {faction_name}')
    print(f'Cards found: {len(wrappers)}')
    print()

    units = []
    for i, wrapper in enumerate(wrappers):
        unit = parse_card(wrapper)
        units.append(unit)
        invuln_str = f'  invuln={unit["invuln_save"]}' if unit['invuln_save'] else ''
        print(f'  [{i+1:3d}] {unit["card_name"]} ({unit["points"]}pts)'
              f' | stats={len(unit["all_model_stats"])} models'
              f' | ranged={len(unit["ranged_weapons"])}'
              f' | melee={len(unit["melee_weapons"])}'
              f' | abilities={len(unit["abilities"])}'
              f'{invuln_str}')

    # ── Write JSON ──────────────────────────────────────────────────────────
    output = {
        'faction':        faction_name,
        'source_file':    os.path.basename(html_path),
        'extracted_date': str(date.today()),
        'total_cards':    len(units),
        'units':          units,
    }
    json_path = os.path.join(output_dir, f'{slug}_parsed.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f'\nWrote JSON: {json_path}')

    # ── Write mapping CSV ───────────────────────────────────────────────────
    csv_path = os.path.join(output_dir, f'{slug}_mapping.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['card_name', 'db_name', 'gw_sku', 'faction', 'include'])
        for unit in units:
            writer.writerow([unit['card_name'], '', '', faction_name, ''])
    print(f'Wrote CSV:  {csv_path}')
    print()
    print('Next step: fill in db_name, gw_sku, and include (yes/no) in the CSV,')
    print('then hand both files back for seed generation.')


if __name__ == '__main__':
    main()
