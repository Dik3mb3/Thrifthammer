"""
Management command: import_gw_xlsx

Imports Games Workshop product data from an Octoparse-generated XLSX file.

For each active product in our DB it finds the best-matching row in the
spreadsheet and updates:
  - CurrentPrice (GW retailer)  — url, price, in_stock, not_available
  - Product                     — image_url, gw_url

Products that cannot be matched are marked not_available=True at GW so
the website shows "Not Available" rather than stale placeholder data.

GW XLSX format (4 columns from Octoparse):
    Title      - GW product name
    Title_URL  - Direct warhammer.com product page URL
    Image      - GW CDN image URL (WebP, 320×330)
    Like       - USD price (e.g. "$65.00")

Usage:
    # Preview matches without saving:
    python manage.py import_gw_xlsx --file "path/to/file.xlsx" --dry-run

    # Full import (updates prices, images, and gw_url):
    python manage.py import_gw_xlsx --file "path/to/file.xlsx"

    # Raise/lower the match confidence threshold (default 0.65):
    python manage.py import_gw_xlsx --file "..." --min-score 0.7

Notes:
    - Image URLs are stored with the ?fm=webp query param stripped so the
      full-resolution JPEG is served (same format as existing image_url values).
    - Safe to re-run — all writes use update_or_create / save().
    - Products with no match above --min-score are marked not_available at GW.
"""

import re
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ── Normalisation constants ────────────────────────────────────────────────────

_SKIP_WORDS = frozenset({
    'edition', 'new', 'box', 'set', 'the', 'and', 'of', 'at',
    '2014', '2015', '2016', '2017', '2018', '2019', '2020',
    '2021', '2022', '2023', '2024', '2025', '2026',
    'index', 'codex', 'datacards', 'datasheets',
    'squad', 'warriors', 'warrior', 'guard', 'veteran',
    # "prime" is too generic — "Tyranid Prime", "Archmagos Prime", "Taurox Prime"
    # all share it and it causes false cross-faction matches.
    'prime',
    # "team" appears in "Battlesuit Team", "Combat Team", etc.
    'team',
    # "armour" is shared by many HH products regardless of unit type, causing
    # e.g. "Praetor in Terminator Armour" → "Librarian in Terminator Armour".
    'armour',
    # "guardsmen" causes "Veteran Guardsmen" (not in GW sheet) to incorrectly
    # match "Traitor Guardsmen Squad". Without this keyword no match is found
    # and the product is correctly marked not_available.
    'guardsmen',
    # "dice" causes "Age of Sigmar Dice Set" → "Dice Cube" false match.
    'dice',
})

_FACTION_PREFIXES = [
    # Warhammer 40,000 factions
    'adepta sororitas', 'adeptus astartes', 'adeptus custodes',
    'adeptus mechanicus', 'adeptus titanicus', 'aeldari', 'astra militarum',
    'black templars', 'blood angels', 'chaos daemons', 'chaos space marines',
    'craftworlds', 'dark angels', 'death guard', 'deathwatch', 'drukhari',
    'genestealer cults', 'grey knights', 'horus heresy', 'imperial guard',
    'imperial knights', 'kill team', 'leagues of votann', 'necromunda',
    'necrons', 'necron',
    'orks', 'ork',
    'skitarii',
    'space marines', 'space marine',
    'space wolves', 'thousand sons', "t'au empire", 'tau empire', "t'au", 'tau',
    'tyranids', 'tyranid',
    'ultramarines', 'warhammer 40000', 'warhammer 40k', 'world eaters',
    # Age of Sigmar
    'age of sigmar', 'blades of khorne', 'cities of sigmar',
    'daughters of khaine', 'disciples of tzeentch', 'flesh-eater courts',
    'gloomspite gitz', 'lumineth realm-lords', 'maggotkin of nurgle',
    'nighthaunt', 'orruk warclans', 'ossiarch bonereapers',
    'skaven', 'slaves to darkness', 'stormcast eternals',
    'necromunda', 'warcry',
]

GW_RETAILER_SLUG = 'games-workshop'


class Command(BaseCommand):
    """
    Import GW product data (URLs, images, prices) from an Octoparse XLSX.

    Matches spreadsheet rows to our products by normalised name similarity.
    Unmatched products are marked not_available at Games Workshop.
    Safe to re-run (idempotent).
    """

    help = 'Import Games Workshop product data (URL, image, price) from an Octoparse XLSX.'

    def add_arguments(self, parser):
        """Register command-line arguments."""
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            metavar='PATH',
            help='Path to the GW Octoparse XLSX file.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Preview matches without saving to the database.',
        )
        parser.add_argument(
            '--min-score',
            type=float,
            default=0.65,
            metavar='SCORE',
            help='Minimum match score to accept (0.0–1.0, default: 0.65).',
        )

    # ── Entry point ────────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        """Load XLSX and import matching GW product data."""
        try:
            import openpyxl
        except ImportError:
            raise CommandError('openpyxl is required: pip install openpyxl')

        dry_run = options['dry_run']
        min_score = options['min_score']
        xlsx_path = options['file']

        try:
            gw_retailer = Retailer.objects.get(slug=GW_RETAILER_SLUG)
        except Retailer.DoesNotExist:
            raise CommandError(
                f'Retailer "{GW_RETAILER_SLUG}" not found. Run populate_products first.'
            )

        # Load spreadsheet rows
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        ws = wb.active
        gw_rows = [
            row for row in ws.iter_rows(min_row=2, values_only=True)
            if row[0]
        ]
        wb.close()

        products = list(Product.objects.filter(is_active=True))

        self.stdout.write(f'\nGames Workshop XLSX Import')
        self.stdout.write('=' * 60)
        self.stdout.write(f'  File       : {xlsx_path}')
        self.stdout.write(f'  GW rows    : {len(gw_rows)}')
        self.stdout.write(f'  DB products: {len(products)} active')
        self.stdout.write(f'  Min score  : {min_score}')
        self.stdout.write(f'  Dry run    : {dry_run}')
        self.stdout.write('=' * 60 + '\n')

        matched_pks = set()
        imported = 0
        image_updated = 0
        msrp_updated = 0

        for product in products:
            # Use gw_search_name for exact lookup when set; fall back to fuzzy.
            if product.gw_search_name:
                candidates = self._exact_then_fuzzy(
                    product.gw_search_name, gw_rows, min_score
                )
            else:
                candidates = self._all_matches(product.name, gw_rows, min_score)
            if not candidates:
                continue

            # Pick cheapest from top-scoring cluster (handles duplicate listings)
            SCORE_TOLERANCE = 0.10
            best_score = candidates[0][0]
            chosen_score, chosen_row = candidates[0]
            chosen_price = None

            for score, row in candidates:
                if best_score - score > SCORE_TOLERANCE:
                    break
                p = self._parse_price(row[3])
                if p is not None and (chosen_price is None or p < chosen_price):
                    chosen_price = p
                    chosen_score, chosen_row = score, row

            gw_title, gw_url_raw, gw_image_raw, price_raw = chosen_row
            price = chosen_price or self._parse_price(price_raw)
            url = str(gw_url_raw).strip() if gw_url_raw else ''
            # Strip query params from image URL to get full-res JPEG
            image_url = str(gw_image_raw).split('?')[0] if gw_image_raw else ''

            edition_note = (
                f' ({len(candidates)} candidates, cheapest chosen)'
                if len(candidates) > 1 else ''
            )
            image_note = ' [img]' if image_url else ''

            self.stdout.write(
                f'  [{chosen_score:.2f}] {product.name}{edition_note}{image_note}\n'
                f'         -> {gw_title}  ${price_raw}  {url[:65]}'
            )

            if not dry_run:
                with transaction.atomic():
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=gw_retailer,
                        defaults={
                            'price': price,
                            'url': url,
                            'listing_title': str(gw_title).strip(),
                            'in_stock': True,
                            'not_available': False,
                        },
                    )
                    # Update product image, GW direct link, and MSRP
                    update_fields = []
                    if url and product.gw_url != url:
                        product.gw_url = url
                        update_fields.append('gw_url')
                    if image_url and product.image_url != image_url:
                        product.image_url = image_url
                        update_fields.append('image_url')
                        image_updated += 1
                    # Keep product.msrp in sync with GW's live price so all
                    # MSRP references across the site (army calculator, collection
                    # stats, discount columns) always reflect the current GW price.
                    if price is not None and product.msrp != price:
                        product.msrp = price
                        update_fields.append('msrp')
                        msrp_updated += 1
                    if update_fields:
                        product.save(update_fields=update_fields)

            matched_pks.add(product.pk)
            imported += 1

        # Mark unmatched products as "not available" at GW
        unmatched = [p for p in products if p.pk not in matched_pks]
        not_available_count = len(unmatched)

        if not dry_run and unmatched:
            for product in unmatched:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    defaults={
                        'price': None,
                        'url': '',
                        'listing_title': '',
                        'in_stock': False,
                        'not_available': True,
                    },
                )

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'  Matched  : {imported}'))
        self.stdout.write(f'  Images   : {image_updated} updated')
        self.stdout.write(f'  MSRP     : {msrp_updated} synced from GW price')
        self.stdout.write(f'  Not avail: {not_available_count} marked not available')
        if dry_run:
            self.stdout.write(self.style.WARNING('\n  DRY RUN — no changes saved.'))
        self.stdout.write('=' * 60 + '\n')

        # Auto-create UnitType entries for any new products added in this import
        if not dry_run:
            from django.core.management import call_command
            self.stdout.write('Syncing Army Calculator unit types...')
            call_command('sync_unit_types', verbosity=0)

    # ── Name matching ──────────────────────────────────────────────────────────

    @staticmethod
    def _exact_then_fuzzy(search_name, gw_rows, min_score):
        """
        When a product has a gw_search_name set, try an exact title match first
        (case-insensitive). If that fails, fall back to fuzzy keyword matching.

        This guarantees products like 'Khorne Berzerkers' or 'Infiltrator Squad'
        are always matched correctly even after spreadsheet reshuffling.
        """
        lower_search = search_name.lower().strip()
        for row in gw_rows:
            if str(row[0]).lower().strip() == lower_search:
                return [(1.0, row)]
        # Exact match not found — fall back to fuzzy
        return Command._all_matches(search_name, gw_rows, min_score)

    @staticmethod
    def _get_faction(text):
        """Return the first faction prefix found in text (longest-first), or None."""
        lower = text.lower()
        for prefix in sorted(_FACTION_PREFIXES, key=len, reverse=True):
            if prefix in lower:
                return prefix
        return None

    @staticmethod
    def _all_matches(product_name, gw_rows, min_score):
        """
        Return all GW rows whose name similarity meets min_score.

        Applies a faction-conflict penalty (-0.6) when our product belongs to
        faction A but the GW row explicitly names a different faction B, so
        "Combat Patrol: Blood Angels" won't match "Dark Angels Combat Patrol".

        Returns list of (score, row) tuples sorted by score descending.
        """
        p_words = Command._keywords(product_name)
        if not p_words:
            return []

        our_faction = Command._get_faction(product_name)
        matches = []

        for row in gw_rows:
            gw_title = str(row[0])
            g_words = Command._keywords(gw_title)
            if not g_words:
                continue
            shared = len(p_words & g_words)
            score = 2 * shared / (len(p_words) + len(g_words))

            if our_faction is not None:
                gw_faction = Command._get_faction(gw_title)
                if gw_faction is not None and gw_faction != our_faction:
                    score -= 0.6

            if score >= min_score:
                matches.append((score, row))

        return sorted(matches, key=lambda x: x[0], reverse=True)

    @staticmethod
    def _keywords(name):
        """
        Return the normalised keyword set for a product name.

        Strips faction prefixes, edition info, punctuation, and stop words.
        """
        text = name.lower()
        text = re.sub(r'\(.*?\)', '', text)
        for prefix in sorted(_FACTION_PREFIXES, key=len, reverse=True):
            text = text.replace(prefix, ' ')
        text = re.sub(r'[^\w\s-]', ' ', text)
        text = re.sub(r'\s*-\s*', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return {
            w for w in text.split()
            if len(w) > 2 and w not in _SKIP_WORDS
        }

    @staticmethod
    def _parse_price(raw):
        """Parse a price cell value. Returns Decimal or None."""
        if raw is None:
            return None
        try:
            cleaned = str(raw).replace('$', '').replace('£', '').replace(',', '').strip()
            price = Decimal(cleaned)
            if 0 < price < 2000:
                return price
        except (InvalidOperation, ValueError):
            pass
        return None
