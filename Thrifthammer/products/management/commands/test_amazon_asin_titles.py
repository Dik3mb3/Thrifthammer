"""
Read-only test: verify Amazon ASINs match our stored product names.

For each product in the chosen faction that has an Amazon URL:
  1. Extract the ASIN from the stored URL.
  2. Call the Amazon Creators API GetItems with the itemInfo.title resource.
  3. Fuzzy-match the returned Amazon title against our product name.
  4. Print a report: MATCH / FUZZY / MISMATCH / NO ASIN / API ERROR.

This command writes nothing to the database.  It is safe to run at any time.

Usage:
    python manage.py test_amazon_asin_titles --faction necrons
    python manage.py test_amazon_asin_titles --faction space-marines
    python manage.py test_amazon_asin_titles --list-factions
"""

import difflib
import re
import time

import requests as _requests
from django.conf import settings
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Faction, Product
from scrapers.retailers.amazon_creators import AmazonCreatorsClient

# ASIN regex — same as the Creators client uses
_ASIN_RE = re.compile(r'/dp/([A-Z0-9]{10})')

# Score thresholds
_MATCH_THRESHOLD = 0.80   # >= 80 %  → MATCH (green)
_FUZZY_THRESHOLD = 0.50   # >= 50 %  → FUZZY (yellow), below → MISMATCH (red)

# Delay between batched API calls
_CALL_DELAY = 1.1


def _extract_asin(url):
    """Return the ASIN from an Amazon URL, or None if not found."""
    m = _ASIN_RE.search(url or '')
    return m.group(1) if m else None


def _score(our_name, amazon_title):
    """
    Return a similarity ratio between 0.0 and 1.0.

    Uses SequenceMatcher on lower-cased strings so capitalisation
    differences don't penalise legitimate matches.
    """
    return difflib.SequenceMatcher(
        None,
        our_name.lower(),
        amazon_title.lower(),
    ).ratio()


class Command(BaseCommand):
    """Verify Amazon ASINs against Creators API titles for one faction."""

    help = 'Read-only ASIN title verification for one faction'

    def add_arguments(self, parser):
        """Add --faction and --list-factions arguments."""
        parser.add_argument(
            '--faction',
            type=str,
            default='',
            help='Faction slug (e.g. necrons, space-marines)',
        )
        parser.add_argument(
            '--list-factions',
            action='store_true',
            help='List available faction slugs and exit',
        )

    def handle(self, *args, **options):
        """Entry point — list factions or run verification."""
        if options['list_factions']:
            self._list_factions()
            return

        faction_slug = options['faction'].strip()
        if not faction_slug:
            self.stderr.write(
                self.style.ERROR(
                    'Please provide a faction slug: --faction necrons\n'
                    'Run with --list-factions to see available slugs.'
                )
            )
            return

        self._run(faction_slug)

    # -------------------------------------------------------------------------

    def _list_factions(self):
        """Print all faction slugs that have at least one active product."""
        factions = (
            Faction.objects
            .filter(products__is_active=True)
            .distinct()
            .order_by('name')
            .values_list('slug', 'name')
        )
        self.stdout.write('\nAvailable faction slugs:')
        for slug, name in factions:
            self.stdout.write(f'  {slug:<30} ({name})')
        self.stdout.write('')

    def _run(self, faction_slug):
        """Fetch ASINs for the faction, query the Creators API, print report."""
        # ── Resolve faction ──────────────────────────────────────────────────
        try:
            faction = Faction.objects.get(slug=faction_slug)
        except Faction.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    f'Faction "{faction_slug}" not found. '
                    'Run --list-factions to see valid slugs.'
                )
            )
            return

        self.stdout.write(f'\nFaction: {faction.name}')

        # ── Gather products with Amazon URLs ─────────────────────────────────
        amazon_entries = list(
            CurrentPrice.objects
            .filter(
                retailer__slug='amazon',
                product__faction=faction,
                product__is_active=True,
            )
            .exclude(url='')
            .exclude(url__isnull=True)
            .select_related('product')
        )

        if not amazon_entries:
            self.stdout.write(
                self.style.WARNING(
                    f'No Amazon URLs found for faction "{faction.name}".'
                )
            )
            return

        self.stdout.write(f'Products with Amazon URLs: {len(amazon_entries)}\n')

        # ── Extract ASINs ────────────────────────────────────────────────────
        rows = []  # list of (product_name, asin, url)
        no_asin = []

        for entry in amazon_entries:
            asin = _extract_asin(entry.url)
            if asin:
                rows.append((entry.product.name, asin, entry.url))
            else:
                no_asin.append(entry.product.name)

        if no_asin:
            self.stdout.write(self.style.WARNING('URLs with no parseable ASIN:'))
            for name in no_asin:
                self.stdout.write(f'  {name}')
            self.stdout.write('')

        if not rows:
            self.stdout.write(self.style.ERROR('No valid ASINs to look up.'))
            return

        # ── Call Creators API ────────────────────────────────────────────────
        client = AmazonCreatorsClient()

        # Temporarily extend the resources list to include itemInfo.title.
        # We do this on the payload directly rather than modifying the module constant.
        asins = [asin for _, asin, _ in rows]

        self.stdout.write(f'Querying Creators API for {len(asins)} ASINs...\n')

        api_results = {}  # ASIN → amazon_title or None

        batch_size = 10
        batches = [asins[i:i + batch_size] for i in range(0, len(asins), batch_size)]

        for idx, batch in enumerate(batches):
            if idx > 0:
                time.sleep(_CALL_DELAY)
            try:
                token = client.get_token()
                resp = _requests.post(
                    'https://creatorsapi.amazon/catalog/v1/getItems',
                    json={
                        'itemIds':     batch,
                        'partnerTag':  settings.AMAZON_ASSOCIATE_TAG,
                        'partnerType': 'Associates',
                        'resources':   [
                            'offersV2.listings.price',
                            'offersV2.listings.condition',
                            'itemInfo.title',
                        ],
                    },
                    headers={
                        'Authorization': f'Bearer {token}',
                        'x-marketplace': 'www.amazon.com',
                        'Content-Type':  'application/json; charset=utf-8',
                        'Accept':        'application/json',
                    },
                    timeout=20,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get('itemsResult', {}).get('items', [])
                for item in items:
                    asin = item.get('asin')
                    title = (
                        item.get('itemInfo', {})
                            .get('title', {})
                            .get('displayValue', '')
                    )
                    api_results[asin] = title or None

            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f'Batch {idx + 1} API error: {exc}')
                )
                # Mark batch ASINs as errored
                for asin in batch:
                    api_results.setdefault(asin, 'API_ERROR')

        # ── Print results ────────────────────────────────────────────────────
        match_count = fuzzy_count = mismatch_count = error_count = 0

        self.stdout.write(
            f'{"Product Name":<45} {"ASIN":<12} {"Score":>6}  {"Status":<10}  Amazon Title'
        )
        self.stdout.write('-' * 130)

        for product_name, asin, url in sorted(rows, key=lambda r: r[0]):
            amazon_title = api_results.get(asin)

            if amazon_title == 'API_ERROR':
                status = 'API ERROR'
                score_str = '  —'
                colour = self.style.ERROR
                error_count += 1
                display_title = ''
            elif amazon_title is None:
                status = 'NOT FOUND'
                score_str = '  —'
                colour = self.style.ERROR
                error_count += 1
                display_title = '(ASIN returned no result — may be invalid)'
            else:
                ratio = _score(product_name, amazon_title)
                score_str = f'{ratio:.0%}'
                if ratio >= _MATCH_THRESHOLD:
                    status = 'MATCH'
                    colour = self.style.SUCCESS
                    match_count += 1
                elif ratio >= _FUZZY_THRESHOLD:
                    status = 'FUZZY'
                    colour = self.style.WARNING
                    fuzzy_count += 1
                else:
                    status = 'MISMATCH'
                    colour = self.style.ERROR
                    mismatch_count += 1
                display_title = amazon_title

            line = (
                f'{product_name[:44]:<45} {asin:<12} {score_str:>6}  '
                f'{status:<10}  {display_title}'
            )
            self.stdout.write(colour(line))

        # ── Summary ──────────────────────────────────────────────────────────
        total = len(rows)
        self.stdout.write('\n' + '─' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'  MATCH     (≥80%): {match_count}/{total}')
        )
        self.stdout.write(
            self.style.WARNING(f'  FUZZY  (50–79%): {fuzzy_count}/{total}')
        )
        self.stdout.write(
            self.style.ERROR(f'  MISMATCH  (<50%): {mismatch_count}/{total}')
        )
        self.stdout.write(
            self.style.ERROR(f'  ERRORS/NOT FOUND: {error_count}/{total}')
        )
        self.stdout.write('')
