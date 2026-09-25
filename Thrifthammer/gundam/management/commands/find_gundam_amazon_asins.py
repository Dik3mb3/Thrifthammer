"""
Find and optionally apply Amazon URLs for Gundam products that have none stored.

Searches by manufacturer barcode (EAN/JAN, stored in Product.barcode) rather
than by product name. A plain keyword/name search returns a lot of wrong
matches for Gunpla -- different color variants, different factions (AEUG vs
Titans), different grades, even completely unrelated products -- because so
many releases share near-identical names. Amazon's search API supports
passing a UPC/EAN/ISBN directly as the `keywords` parameter; requesting the
`itemInfo.externalIds` resource lets us read back the matched item's own
EAN/UPC and verify it equals what we searched for before trusting it. Same
"exact identifier, not fuzzy text" principle as the ISBN-anchored eBay
matching built for the Books feature.

A result is only accepted as VERIFIED if the returned item's EAN or UPC list
contains our exact barcode. Anything else is treated as not found rather than
guessed at.

Workflow:
  1. Run without --apply to see what the API would find (nothing written).
  2. Review the output chart. Add overrides to ASIN_OVERRIDES for any wrong
     results, or SKIP_SKUS (keyed by handle) for products with no real listing.
  3. Re-run with --apply to write the URLs to the database.

Products that already have an Amazon URL are always skipped.

Usage:
    python manage.py find_gundam_amazon_asins                          # dry run, all products
    python manage.py find_gundam_amazon_asins --apply                   # write to DB
    python manage.py find_gundam_amazon_asins --batch-tag zeta-gundam
"""

import time

from django.conf import settings
from django.core.management.base import BaseCommand

from gundam.models import CurrentPrice, Product
from products.models import Retailer
from scrapers.retailers.amazon_creators import AmazonCreatorsClient

# ─── Manual ASIN overrides ────────────────────────────────────────────────────
# Keyed by Product.handle (Gundam Planet's product slug). Add entries here when
# the barcode search returns the wrong product or no result but a correct
# ASIN is known some other way. These are permanent.
ASIN_OVERRIDES = {}

# Handles to explicitly exclude from Amazon URL discovery -- no correct ASIN
# available, product not sold standalone on Amazon, etc.
SKIP_SKUS = set()
# ─────────────────────────────────────────────────────────────────────────────

_CALL_DELAY = 1.1  # seconds between API calls -- keeps us under 1 TPS

_RESOURCES = [
    'itemInfo.title',
    'itemInfo.externalIds',
    'offersV2.listings.price',
    'offersV2.listings.condition',
]


def _build_url(asin):
    """Build a clean affiliate URL from an ASIN."""
    tag = settings.AMAZON_ASSOCIATE_TAG
    return f'https://www.amazon.com/dp/{asin}?tag={tag}'


def _safe(text):
    """Strip characters the Windows console (cp1252) can't print (e.g. Greek beta)."""
    return str(text).encode('cp1252', errors='replace').decode('cp1252')


def _best_new_price(item):
    """Extract the first new-condition listing price from a SearchItems result."""
    listings = item.get('offersV2', {}).get('listings', [])
    for listing in listings:
        if listing.get('condition', {}).get('value', 'New') != 'New':
            continue
        amount = listing.get('price', {}).get('money', {}).get('amount')
        if amount is not None:
            return float(amount)
    return None


def _external_ids(item):
    """Flatten the EAN/UPC display values returned for an item into one set."""
    ext = item.get('itemInfo', {}).get('externalIds', {})
    ids = set()
    for key in ('eans', 'upcs', 'isbns'):
        ids.update(ext.get(key, {}).get('displayValues', []))
    return ids


class Command(BaseCommand):
    """Find Amazon URLs for Gundam products via barcode search. Dry-run by default."""

    help = (
        'Search Amazon for Gundam products with no URL, by manufacturer barcode. '
        'Shows a chart of findings. Use --apply to write to DB.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-tag',
            help='Only search products with this batch_tag (e.g. zeta-gundam)',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Write found URLs to the database (default: dry run only)',
        )

    def handle(self, *args, **options):
        applying = options['apply']

        try:
            amazon_retailer = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('Amazon retailer not found in DB.'))
            return

        all_products = Product.objects.filter(is_active=True)
        if options['batch_tag']:
            all_products = all_products.filter(batch_tag=options['batch_tag'])
        all_products = list(all_products.order_by('name'))

        has_url = set(
            CurrentPrice.objects
            .filter(retailer=amazon_retailer, product__in=all_products)
            .exclude(url='').exclude(url__isnull=True)
            .values_list('product_id', flat=True)
        )

        candidates = [p for p in all_products if p.id not in has_url]
        skipped_count = len(all_products) - len(candidates)

        self.stdout.write(
            f'\nScope    : {"batch_tag=" + options["batch_tag"] if options["batch_tag"] else "all active Gundam products"}'
            f'\nMode     : {"APPLY - writing to DB" if applying else "DRY RUN - nothing will be written"}'
            f'\nMatching : barcode (EAN/UPC), verified against itemInfo.externalIds'
            f'\nHave URL : {skipped_count} (skipped)'
            f'\nNo URL   : {len(candidates)} (will search)'
        )

        if not candidates:
            self.stdout.write(self.style.SUCCESS(
                f'\nAll {len(all_products)} products already have Amazon URLs. Nothing to do.\n'
            ))
            return

        client = AmazonCreatorsClient()

        found = []       # (product, asin, amazon_title, api_price, source)
        not_found = []   # (product, reason)

        for idx, product in enumerate(candidates):
            if idx > 0:
                time.sleep(_CALL_DELAY)

            if product.handle in SKIP_SKUS:
                not_found.append((product, 'skipped'))
                continue

            if product.handle in ASIN_OVERRIDES:
                asin = ASIN_OVERRIDES[product.handle]
                found.append((product, asin, '(override - not searched)', None, 'OVERRIDE'))
                continue

            if not product.barcode:
                not_found.append((product, 'no barcode stored'))
                continue

            try:
                items = client.search_items(
                    keywords=product.barcode,
                    marketplace='www.amazon.com',
                    brand=None,
                    item_count=3,
                    resources=_RESOURCES,
                )
            except Exception as exc:
                detail = ''
                if hasattr(exc, 'response') and exc.response is not None:
                    try:
                        detail = str(exc.response.json())
                    except Exception:
                        detail = exc.response.text[:120]
                self.stderr.write(self.style.ERROR(
                    f'  API error for "{_safe(product.name)}": {exc}'
                    + (f'\n  Detail: {detail}' if detail else '')
                ))
                not_found.append((product, 'API error'))
                continue

            if not items:
                not_found.append((product, 'no results'))
                continue

            # Only accept a result whose own EAN/UPC list contains our exact
            # barcode -- a barcode-as-keywords search can still fall back to
            # a loose text match with no identifier overlap at all.
            verified = None
            for candidate_item in items:
                if product.barcode in _external_ids(candidate_item):
                    verified = candidate_item
                    break

            if verified is None:
                not_found.append((product, 'no EAN/UPC match in results'))
                continue

            asin = verified.get('asin', '')
            amazon_title = verified.get('itemInfo', {}).get('title', {}).get('displayValue', '-')
            api_price = _best_new_price(verified)

            if not asin:
                not_found.append((product, 'matched item had no ASIN'))
                continue

            found.append((product, asin, amazon_title, api_price, 'BARCODE'))

        self.stdout.write('')

        if found:
            self.stdout.write(
                f'{"#":<4} {"Product Name":<45} {"ASIN":<12} {"Price":>8}  {"Src":<8}  Amazon Title'
            )
            self.stdout.write('-' * 145)

            for i, (product, asin, amazon_title, api_price, source) in enumerate(found, 1):
                price_str = f'${api_price:.2f}' if api_price is not None else '-'
                src_style = self.style.WARNING if source == 'OVERRIDE' else self.style.SUCCESS
                name_safe = _safe(product.name)[:44]
                title_safe = _safe(amazon_title)
                self.stdout.write(src_style(
                    f'{i:<4} {name_safe:<45} {asin:<12} {price_str:>8}  {source:<8}  {title_safe}'
                ))

        if applying and found:
            self.stdout.write('')
            written = 0
            for product, asin, amazon_title, api_price, source in found:
                url = _build_url(asin)
                # api_price is None when the ASIN is verified (real barcode
                # match) but has no current live "New" offer. Store 0 rather
                # than leaving price null and marking not_available -- a
                # future price-refresh job can then re-check this exact ASIN
                # and pick up the real price once Amazon restocks it, instead
                # of the record being treated as "no listing exists".
                cp, created = CurrentPrice.objects.get_or_create(
                    retailer=amazon_retailer,
                    product=product,
                    defaults={
                        'url':           url,
                        'price':         api_price if api_price is not None else 0,
                        'in_stock':      api_price is not None,
                        'not_available': False,
                    },
                )
                if not created:
                    cp.url = url
                    cp.save(update_fields=['url'])
                written += 1
                self.stdout.write(f'  {"Created" if created else "Updated"}: {_safe(product.name)} -> {url}')
            self.stdout.write(self.style.SUCCESS(f'\n{written} URL(s) written to database.'))

        self.stdout.write('\n' + '-' * 50)
        self.stdout.write(self.style.SUCCESS(f'  Found via barcode : {sum(1 for *_, s in found if s == "BARCODE")}'))
        self.stdout.write(self.style.WARNING(f'  From overrides    : {sum(1 for *_, s in found if s == "OVERRIDE")}'))
        self.stdout.write(self.style.WARNING(f'  Still no URL      : {len(not_found)}'))
        if not_found:
            for p, reason in not_found:
                self.stdout.write(f'    - {_safe(p.name)}  ({reason})')

        if not applying:
            self.stdout.write(self.style.WARNING(
                '\nDry run complete. Review the chart above, add any overrides to '
                'ASIN_OVERRIDES in this file,\nthen re-run with --apply to write to the database.\n'
            ))
        else:
            self.stdout.write('')
