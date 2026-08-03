"""
Audit and optionally fix affiliate tracking tags on all retailer URLs.

Checks every CurrentPrice URL for the correct affiliate identifier:
  Amazon       — ?tag=thrifthammer7-20
  eBay (US)    — campid= (EPN campaign ID) + mkcid=1
  eBay UK      — campid= (separate EPN UK campaign ID) + mkcid=1
  Noble Knight — ?awid=1576

Games Workshop and Miniature Market have no affiliate programmes and
are intentionally skipped.

Usage:
  # Dry run — report only, no DB writes:
  python manage.py check_affiliate_urls

  # Auto-fix untagged URLs:
  python manage.py check_affiliate_urls --apply

  # Check a single retailer:
  python manage.py check_affiliate_urls --retailer amazon
  python manage.py check_affiliate_urls --retailer ebay
  python manage.py check_affiliate_urls --retailer ebay-uk
  python manage.py check_affiliate_urls --retailer noble-knight
"""

import re
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

from django.conf import settings
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice

# ── Affiliate identifiers ────────────────────────────────────────────────────

AMAZON_TAG   = 'thrifthammer7-20'
NK_AWID      = '1576'
# EPN static params — campid is appended separately from settings.
# mkrid is the marketplace rotation ID and differs between US and UK.
_EPN_STATIC     = 'mkcid=1&mkrid=711-53200-19255-0&toolid=10001&mkevt=1'
_EPN_STATIC_UK  = 'mkcid=1&mkrid=710-53481-19255-0&toolid=10001&mkevt=1'
# Fallback campid if the env var is not set (US matches migration 0008;
# UK matches the dedicated "UK Thrifthammer" EPN campaign).
_EPN_CAMPID_FALLBACK    = '5339151938'
_EPN_CAMPID_FALLBACK_UK = '5339181589'

_AMAZON_ASIN_RE = re.compile(r'/dp/([A-Z0-9]{10})')

# Retailer slugs that have affiliate programmes
AFFILIATE_RETAILERS = {
    'amazon':             'Amazon',
    'ebay':               'eBay',
    'ebay-uk':            'eBay UK',
    'noble-knight-games': 'Noble Knight',
}

# Retailer slugs explicitly excluded (no affiliate programme)
EXCLUDED_RETAILERS = {'games-workshop', 'miniature-market'}


# ── URL helpers ──────────────────────────────────────────────────────────────

def _check_amazon(url):
    """Return True if the Amazon URL carries the ThriftHammer affiliate tag."""
    return f'tag={AMAZON_TAG}' in url


def _fix_amazon(url):
    """Return a clean https://amazon.com/dp/ASIN?tag=... URL, or original if no ASIN."""
    match = _AMAZON_ASIN_RE.search(url)
    if not match:
        return url
    return f'https://www.amazon.com/dp/{match.group(1)}?tag={AMAZON_TAG}'


def _check_ebay(url, campid):
    """Return True if the eBay URL carries both mkcid=1 and the campid."""
    return 'mkcid=1' in url and f'campid={campid}' in url


def _fix_ebay(url, campid, static_params=_EPN_STATIC):
    """Strip old EPN params then append a fresh set including campid."""
    # Remove previously appended EPN block (everything from mkcid= onward)
    for marker in ('&mkcid=1', '?mkcid=1', 'mkcid=1'):
        idx = url.find(marker)
        if idx != -1:
            url = url[:idx].rstrip('?&')
            break
    separator = '&' if '?' in url else '?'
    return f'{url}{separator}{static_params}&campid={campid}'


def _check_nk(url):
    """Return True if the Noble Knight URL carries the awid affiliate param."""
    return f'awid={NK_AWID}' in url


def _fix_nk(url):
    """Append or replace the awid param on a Noble Knight URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params['awid'] = [NK_AWID]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))


# ── Command ──────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    """Audit and optionally fix affiliate tracking on all retailer URLs."""

    help = 'Check every CurrentPrice URL for the correct affiliate tag (Amazon/eBay/NK).'

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            '--apply',
            action='store_true',
            default=False,
            help='Fix untagged URLs in the database. Without this flag, reports only.',
        )
        parser.add_argument(
            '--retailer',
            choices=['amazon', 'ebay', 'ebay-uk', 'noble-knight'],
            default=None,
            help='Limit the check to one retailer slug.',
        )

    def handle(self, *args, **options):
        """Execute the affiliate URL audit."""
        apply    = options['apply']
        retailer_filter = options['retailer']

        if not apply:
            self.stdout.write(self.style.WARNING(
                'DRY RUN — no changes will be saved. Use --apply to fix.\n'
            ))

        # Resolve EPN campaign IDs from settings (set via Railway env vars)
        ebay_campid    = getattr(settings, 'EBAY_AFFILIATE_CAMPAIGN_ID', '') or _EPN_CAMPID_FALLBACK
        ebay_uk_campid = getattr(settings, 'EBAY_UK_AFFILIATE_CAMPAIGN_ID', '') or _EPN_CAMPID_FALLBACK_UK

        # Map short CLI alias → DB slug
        slug_alias = {'noble-knight': 'noble-knight-games'}

        grand_total   = 0
        grand_tagged  = 0
        grand_missing = 0
        grand_fixed   = 0
        grand_no_url  = 0
        any_missing   = False

        for slug, display_name in AFFILIATE_RETAILERS.items():
            # CLI --retailer filter
            if retailer_filter:
                canonical = slug_alias.get(retailer_filter, retailer_filter)
                if slug != canonical and slug != retailer_filter:
                    continue

            self.stdout.write(
                self.style.MIGRATE_HEADING(f'\n── {display_name} ({slug}) ──')
            )

            entries = (
                CurrentPrice.objects
                .filter(retailer__slug=slug)
                .select_related('product', 'retailer')
                .order_by('product__name')
            )

            total   = entries.count()
            tagged  = 0
            missing = 0
            fixed   = 0
            no_url  = 0

            for entry in entries:
                url = entry.url or ''

                if not url:
                    no_url += 1
                    continue

                # ── Evaluate affiliate status ────────────────────────────
                if slug == 'amazon':
                    ok      = _check_amazon(url)
                    new_url = _fix_amazon(url) if not ok else url
                elif slug == 'ebay':
                    ok      = _check_ebay(url, ebay_campid)
                    new_url = _fix_ebay(url, ebay_campid) if not ok else url
                elif slug == 'ebay-uk':
                    ok      = _check_ebay(url, ebay_uk_campid)
                    new_url = _fix_ebay(url, ebay_uk_campid, _EPN_STATIC_UK) if not ok else url
                else:  # noble-knight-games
                    ok      = _check_nk(url)
                    new_url = _fix_nk(url) if not ok else url

                if ok:
                    tagged += 1
                else:
                    missing += 1
                    any_missing = True
                    self.stdout.write(
                        self.style.WARNING(
                            f'  [MISSING] {entry.product.name}\n'
                            f'    URL: {url[:90]}'
                        )
                    )
                    if apply and new_url != url:
                        entry.url = new_url
                        entry.save(update_fields=['url'])
                        fixed += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'    → FIXED: {new_url[:90]}')
                        )

            # Per-retailer summary
            self.stdout.write(
                f'  Total: {total}  |  '
                f'Tagged: {tagged}  |  '
                f'Missing: {missing}  |  '
                f'No URL: {no_url}'
                + (f'  |  Fixed: {fixed}' if apply else '')
            )

            grand_total   += total
            grand_tagged  += tagged
            grand_missing += missing
            grand_fixed   += fixed
            grand_no_url  += no_url

        # Grand summary
        self.stdout.write('\n' + '─' * 60)
        self.stdout.write(
            f'TOTAL  |  Checked: {grand_total}  |  '
            f'Tagged: {grand_tagged}  |  '
            f'Missing: {grand_missing}  |  '
            f'No URL: {grand_no_url}'
            + (f'  |  Fixed: {grand_fixed}' if apply else '')
        )
        self.stdout.write('─' * 60)

        if grand_missing == 0:
            self.stdout.write(self.style.SUCCESS(
                '\n✓ All affiliate URLs are correctly tagged.'
            ))
        elif apply:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Fixed {grand_fixed} URL(s). '
                f'{grand_missing - grand_fixed} could not be auto-fixed '
                '(no extractable ASIN/ID — check manually).'
                if grand_missing > grand_fixed
                else f'\n✓ Fixed all {grand_fixed} untagged URL(s).'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n⚠ {grand_missing} URL(s) missing affiliate tags. '
                'Run with --apply to fix.'
            ))
