"""
Add Noble Knight affiliate tag to all stored Noble Knight product URLs.

Transforms every Noble Knight CurrentPrice URL from a bare product URL:
    https://www.nobleknight.com/P/2147483647/Space-Marines-Intercessors

Into a commission-earning affiliate URL:
    https://www.nobleknight.com/P/2147483647/Space-Marines-Intercessors?awid=1576

How commission works:
    Noble Knight pays commission based on the ?awid= parameter.
    Any Noble Knight URL containing ?awid=1576 earns commission when a
    user clicks it and makes a purchase within the cookie window.

Impact on the Noble Knight scraper:
    noble_knight.py strips the ?awid= parameter before fetching so that
    bot requests do not pollute Noble Knight's affiliate analytics.

Impact on the "View at Noble Knight" button:
    Templates render {{ cp.url }} as the href. With ?awid=1576 stored in
    the DB, every user click to Noble Knight earns potential commission.

Usage:
    # Dry run — shows what would change, saves nothing:
    python manage.py add_nk_affiliate_tags

    # Apply to local DB:
    python manage.py add_nk_affiliate_tags --apply
"""

from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Retailer

NK_AFFILIATE_ID = '1576'
NK_DOMAIN = 'nobleknight.com'


def _make_affiliate_url(url):
    """
    Return the URL with ?awid=1576 appended, replacing any existing awid value.

    Uses urlparse so existing query parameters (if any) are preserved and
    awid is set correctly rather than duplicated.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params['awid'] = [NK_AFFILIATE_ID]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))


class Command(BaseCommand):
    """Add Noble Knight affiliate tag to all stored NK product URLs."""

    help = 'Add ?awid=1576 affiliate parameter to all Noble Knight product URLs'

    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            '--apply',
            action='store_true',
            default=False,
            help='Actually save changes. Without this flag, runs as a dry run.',
        )

    def handle(self, *args, **options):
        """Execute the affiliate URL update."""
        apply = options['apply']

        if not apply:
            self.stdout.write(self.style.WARNING(
                'DRY RUN — no changes will be saved. Use --apply to save.\n'
            ))

        try:
            retailer = Retailer.objects.get(slug='noble-knight-games')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('Noble Knight retailer not found in DB.'))
            return

        # Also store the affiliate ID on the retailer record for reference
        if retailer.affiliate_id != NK_AFFILIATE_ID:
            if apply:
                retailer.affiliate_id = NK_AFFILIATE_ID
                retailer.save(update_fields=['affiliate_id'])
            self.stdout.write(
                self.style.SUCCESS(f'  {"Set" if apply else "Would set"} retailer.affiliate_id = {NK_AFFILIATE_ID}')
            )

        entries = (
            CurrentPrice.objects
            .filter(retailer=retailer)
            .exclude(url='')
            .exclude(url__isnull=True)
            .select_related('product')
        )

        total = entries.count()
        updated = 0
        already_tagged = 0
        skipped_non_nk = 0

        self.stdout.write(f'Found {total} Noble Knight CurrentPrice entries with URLs.\n')

        for entry in entries:
            url = entry.url

            # Skip any URL that is not actually a Noble Knight URL
            if NK_DOMAIN not in url:
                skipped_non_nk += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  [skip] Non-NK URL for {entry.product.name}: {url[:60]}'
                    )
                )
                continue

            # Skip if already correctly tagged
            if f'awid={NK_AFFILIATE_ID}' in url:
                already_tagged += 1
                continue

            new_url = _make_affiliate_url(url)

            self.stdout.write(
                f'  [{"APPLY" if apply else "dry-run"}] {entry.product.name[:50]}\n'
                f'    FROM: {url[:80]}\n'
                f'    TO:   {new_url}\n'
            )

            if apply:
                entry.url = new_url
                entry.save(update_fields=['url'])

            updated += 1

        # Summary
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(f'  Total entries:      {total}')
        self.stdout.write(
            self.style.SUCCESS(f'  {"Updated" if apply else "Would update"}: {updated}')
        )
        if already_tagged:
            self.stdout.write(f'  Already tagged:     {already_tagged}')
        if skipped_non_nk:
            self.stdout.write(self.style.WARNING(f'  Non-NK URLs:        {skipped_non_nk}'))
        self.stdout.write('-' * 60)

        if not apply and updated > 0:
            self.stdout.write(self.style.WARNING(
                f'\nRun with --apply to save these {updated} changes to the database.'
            ))
        elif apply and updated > 0:
            self.stdout.write(self.style.SUCCESS(
                f'\nDone. {updated} Noble Knight URLs now include the affiliate tag.'
            ))
