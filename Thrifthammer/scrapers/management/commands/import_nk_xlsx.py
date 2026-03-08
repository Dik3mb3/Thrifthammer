"""
Management command: import_nk_xlsx

Imports Noble Knight prices from an Octoparse-generated XLSX file into
CurrentPrice records, matching spreadsheet rows to our products by name.

Noble Knight XLSX format (columns):
    SKU          - NK product name (NOT a GW SKU — used for name matching)
    Game         - Game system (e.g. "Warhammer 40,000")
    Price        - USD price (e.g. 58.95)
    Item Number  - NK internal product ID
    URL          - Direct Noble Knight product URL

Matching strategy:
    For each active product in our DB, the command searches the spreadsheet
    for the best name match. Both sides are normalised — faction prefixes
    stripped, punctuation removed, edition years ignored — then scored by
    F1-like word overlap. A minimum score (--min-score, default 0.5) is
    required before a match is accepted.

Usage:
    # Preview matches without saving:
    python manage.py import_nk_xlsx --file "path/to/Adepta Sororitas SKUs.xlsx" --dry-run

    # Import matching rows:
    python manage.py import_nk_xlsx --file "path/to/Adepta Sororitas SKUs.xlsx"

    # Process an entire directory of XLSX files:
    python manage.py import_nk_xlsx --dir "path/to/SKUs/"

    # Raise/lower the match confidence threshold:
    python manage.py import_nk_xlsx --file "..." --min-score 0.6

Notes:
    - Prices are stored as-is from the spreadsheet (USD). Noble Knight is a
      US retailer so prices will display in USD on the site.
    - Products with no match above --min-score are silently skipped.
    - Safe to re-run — uses update_or_create.
    - Each product gets exactly one NK CurrentPrice row (best match wins).
"""

import os
import re
import glob
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ── Normalisation constants ────────────────────────────────────────────────────

# Words stripped from both product names and NK titles before matching.
# Includes edition years and non-product words that inflate similarity scores.
_SKIP_WORDS = frozenset({
    'edition', 'new', 'box', 'set', 'the', 'and', 'of', 'at',
    '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025',
    'index', 'codex', 'datacards',  # rulebooks — never match to miniatures
})

# Faction/game prefix phrases stripped before matching so that "adepta sororitas"
# in an NK title doesn't inflate the score for every Sororitas product equally.
_FACTION_PREFIXES = [
    'adepta sororitas', 'adeptus astartes', 'adeptus custodes',
    'adeptus mechanicus', 'adeptus titanicus', 'aeldari', 'age of sigmar',
    'blood angels', 'chaos daemons', 'chaos space marines',
    'dark angels', 'death guard', 'drukhari', 'genestealer cults',
    'grey knights', 'horus heresy', 'imperial guard', 'imperial knights',
    'kill team', 'leagues of votann', 'necromunda', 'necrons',
    'orks', 'orruk warclans', 'space marines', 'space wolves',
    'stormcast eternals', 'tau empire', 't\'au empire',
    'thousand sons', 'tyranids', 'warcry', 'warhammer 40000',
    'warhammer 40k', 'world eaters',
]

NK_RETAILER_SLUG = 'noble-knight-games'


class Command(BaseCommand):
    """
    Import Noble Knight prices from an Octoparse XLSX into CurrentPrice records.

    Matches spreadsheet rows to our products by normalised name similarity.
    Safe to re-run (idempotent).
    """

    help = 'Import Noble Knight prices from an Octoparse XLSX file.'

    def add_arguments(self, parser):
        """Register command-line arguments."""
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--file',
            type=str,
            metavar='PATH',
            help='Path to a single XLSX file to import.',
        )
        group.add_argument(
            '--dir',
            type=str,
            metavar='DIR',
            help='Directory of XLSX files to import (processes all *.xlsx).',
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
            default=0.5,
            metavar='SCORE',
            help='Minimum match score to accept (0.0–1.0, default: 0.5).',
        )
        parser.add_argument(
            '--name-filter',
            type=str,
            default=None,
            metavar='TEXT',
            help=(
                'Only match DB products whose name contains TEXT '
                '(case-insensitive). Auto-detected from the filename if omitted '
                '— e.g. "Adepta Sororitas SKUs.xlsx" filters to "Adepta Sororitas".'
            ),
        )

    # ── Entry point ────────────────────────────────────────────────────────────

    def handle(self, *args, **options):
        """Load XLSX file(s) and import matching prices."""
        dry_run = options['dry_run']
        min_score = options['min_score']

        # Resolve file list
        if options['file']:
            xlsx_files = [options['file']]
        else:
            pattern = os.path.join(options['dir'], '*.xlsx')
            xlsx_files = sorted(glob.glob(pattern))
            if not xlsx_files:
                raise CommandError(f'No .xlsx files found in: {options["dir"]}')

        # Validate retailer exists
        try:
            nk_retailer = Retailer.objects.get(slug=NK_RETAILER_SLUG)
        except Retailer.DoesNotExist:
            raise CommandError(
                f'Retailer "{NK_RETAILER_SLUG}" not found in DB. '
                'Run populate_products first.'
            )

        # Load all active products once (filtered per file below)
        all_products = list(Product.objects.filter(is_active=True))
        global_name_filter = options.get('name_filter')

        self.stdout.write(f'\nNoble Knight XLSX Import')
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Files      : {len(xlsx_files)}')
        self.stdout.write(f'  Products   : {len(all_products)} active')
        self.stdout.write(f'  Min score  : {min_score}')
        self.stdout.write(f'  Dry run    : {dry_run}')
        self.stdout.write('=' * 60 + '\n')

        total_imported = 0
        total_skipped = 0

        for xlsx_path in xlsx_files:
            imported, skipped = self._process_file(
                xlsx_path, all_products, nk_retailer, min_score, dry_run,
                name_filter=global_name_filter,
            )
            total_imported += imported
            total_skipped += skipped

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'  Imported : {total_imported}'))
        self.stdout.write(f'  Skipped  : {total_skipped} (no match above threshold)')
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n  DRY RUN — no changes saved to database.')
            )
        self.stdout.write('=' * 60 + '\n')

    # ── File processing ────────────────────────────────────────────────────────

    def _process_file(self, xlsx_path, all_products, nk_retailer, min_score, dry_run,
                      name_filter=None):
        """
        Process a single XLSX file.

        Products are filtered to those whose name contains name_filter (or the
        faction auto-detected from the filename) so that e.g. a Sororitas file
        only matches Sororitas products — not every other faction's Combat Patrol.

        Returns (imported_count, skipped_count).
        """
        try:
            import openpyxl
        except ImportError:
            raise CommandError(
                'openpyxl is required: pip install openpyxl'
            )

        if not os.path.isfile(xlsx_path):
            self.stderr.write(self.style.ERROR(f'File not found: {xlsx_path}'))
            return 0, 0

        # Auto-detect faction from filename if no explicit filter given.
        # "Adepta Sororitas SKUs.xlsx" → filter products by "Adepta Sororitas".
        if name_filter is None:
            basename = os.path.basename(xlsx_path)
            name_filter = re.sub(r'\s*SKUs?\.xlsx$', '', basename, flags=re.IGNORECASE).strip()

        # Filter to relevant faction products only — prevents "Combat Patrol"
        # from matching every faction when processing a single-faction file.
        faction_keyword = name_filter.lower()
        products = [
            p for p in all_products
            if faction_keyword in p.name.lower()
        ]

        self.stdout.write(
            f'--- {os.path.basename(xlsx_path)} '
            f'(filter: "{name_filter}", {len(products)} products) ---'
        )

        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        ws = wb.active
        nk_rows = [
            row for row in ws.iter_rows(min_row=2, values_only=True)
            if row[0]  # skip blank rows
        ]
        wb.close()

        if not nk_rows:
            self.stdout.write(self.style.WARNING('  No data rows found — skipping.'))
            return 0, 0

        imported = 0
        skipped = 0

        for product in products:
            best_score, best_row = self._best_match(product.name, nk_rows)

            if best_score < min_score or best_row is None:
                continue  # no match in this file for this product

            nk_name, _game, price_raw, _item_num, url = best_row

            price = self._parse_price(price_raw)
            url = str(url).strip() if url else ''

            self.stdout.write(
                f'  [{best_score:.2f}] {product.name}\n'
                f'         -> {nk_name}  ${price_raw}  {url[:70]}'
            )

            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=nk_retailer,
                    defaults={
                        'price': price,
                        'url': url,
                        'in_stock': True,
                        'not_available': price is None and not url,
                    },
                )

            imported += 1

        skipped = len(products) - imported

        self.stdout.write(
            f'  => {imported} matched, {skipped} skipped\n'
        )
        return imported, skipped

    # ── Name matching ──────────────────────────────────────────────────────────

    @staticmethod
    def _best_match(product_name, nk_rows):
        """
        Find the highest-scoring NK row for a given product name.

        Returns (score, row) or (0.0, None) if nothing meets the threshold.
        """
        p_words = Command._keywords(product_name)
        if not p_words:
            return 0.0, None

        best_score = 0.0
        best_row = None

        for row in nk_rows:
            nk_words = Command._keywords(str(row[0]))
            if not nk_words:
                continue
            shared = len(p_words & nk_words)
            score = 2 * shared / (len(p_words) + len(nk_words))
            if score > best_score:
                best_score = score
                best_row = row

        return best_score, best_row

    @staticmethod
    def _keywords(name):
        """
        Return the normalised keyword set for a product name.

        Strips faction prefixes, edition years, punctuation, and stop words,
        leaving only the meaningful distinguishing words for comparison.
        """
        text = name.lower()
        # Remove parenthetical editions: "(2021 Edition)", "(New)"
        text = re.sub(r'\(.*?\)', '', text)
        # Strip faction/game prefixes (longest first to avoid partial matches)
        for prefix in sorted(_FACTION_PREFIXES, key=len, reverse=True):
            text = text.replace(prefix, ' ')
        # Strip remaining punctuation (keep hyphens temporarily)
        text = re.sub(r'[^\w\s-]', ' ', text)
        text = re.sub(r'\s*-\s*', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        # Split and filter
        return {
            w for w in text.split()
            if len(w) > 2 and w not in _SKIP_WORDS
        }

    # ── Price parsing ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_price(raw):
        """
        Parse a price value from the spreadsheet cell.

        Returns Decimal or None.
        """
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
