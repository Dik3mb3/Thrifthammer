"""
Add Amazon affiliate tag to all stored Amazon product URLs.

Transforms every Amazon CurrentPrice URL from a bare ASIN URL:
    https://www.amazon.com/dp/B007RRZHLG

Into a commission-earning affiliate URL:
    https://www.amazon.com/dp/B007RRZHLG?tag=thrifthammer7-20

How commission works:
    Amazon pays commission based solely on the ?tag= parameter.
    Any Amazon URL containing ?tag=thrifthammer7-20 will earn commission
    when a user clicks it and makes a purchase. This is the exact same
    mechanism SiteStripe uses — SiteStripe just adds optional extra params
    (linkCode, linkId, language, ref_) that are NOT required for commission.

Impact on the Amazon scraper:
    The scraper calls _strip_to_asin_url() on every URL before fetching,
    which extracts just the /dp/ASIN part and ignores all query params.
    So the ?tag= parameter does NOT affect scraping at all.

Impact on the "View on Amazon" button:
    The template renders {{ cp.url }} as the href. With ?tag=thrifthammer7-20,
    every click to Amazon now earns potential commission.

Usage:
    # Dry run — shows what will change, saves nothing:
    python manage.py add_amazon_affiliate_tags

    # Apply to local DB:
    python manage.py add_amazon_affiliate_tags --apply

    # Apply to production (via Railway DATABASE_URL):
    DATABASE_URL=... python manage.py add_amazon_affiliate_tags --apply
"""

import re

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Retailer

ASSOCIATE_TAG = 'thrifthammer7-20'
ASIN_RE = re.compile(r'/dp/([A-Z0-9]{10})')


def _make_affiliate_url(url):
    """
    Build a clean affiliate URL from any Amazon product URL.

    Extracts the ASIN and returns:
        https://www.amazon.com/dp/ASIN?tag=thrifthammer7-20

    Returns None if no ASIN can be found.
    """
    match = ASIN_RE.search(url)
    if not match:
        return None
    asin = match.group(1)
    return f'https://www.amazon.com/dp/{asin}?tag={ASSOCIATE_TAG}'


class Command(BaseCommand):
    """Add Amazon affiliate tag to all stored Amazon product URLs."""

    help = 'Add ?tag=thrifthammer7-20 affiliate parameter to all Amazon product URLs'

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
            retailer = Retailer.objects.get(slug='amazon')
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR('Amazon retailer not found in DB.'))
            return

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
        no_asin = 0
        skipped_non_amazon = 0

        self.stdout.write(f'Found {total} Amazon CurrentPrice entries with URLs.\n')

        for entry in entries:
            url = entry.url

            # Skip non-Amazon URLs (shouldn't exist, but be safe)
            if 'amazon.com' not in url and 'amzn' not in url:
                skipped_non_amazon += 1
                self.stdout.write(
                    self.style.WARNING(f'  [skip] Non-Amazon URL for {entry.product.name}: {url[:60]}')
                )
                continue

            # Skip if already tagged with our associate tag
            if f'tag={ASSOCIATE_TAG}' in url:
                already_tagged += 1
                continue

            # Build the new affiliate URL
            new_url = _make_affiliate_url(url)

            if new_url is None:
                no_asin += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no ASIN] Cannot extract ASIN from: {url[:60]}'
                    )
                )
                continue

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
        if no_asin:
            self.stdout.write(self.style.WARNING(f'  No ASIN found:      {no_asin}'))
        if skipped_non_amazon:
            self.stdout.write(self.style.WARNING(f'  Non-Amazon URLs:    {skipped_non_amazon}'))
        self.stdout.write('-' * 60)

        if not apply and updated > 0:
            self.stdout.write(self.style.WARNING(
                f'\nRun with --apply to save these {updated} changes to the database.'
            ))
        elif apply and updated > 0:
            self.stdout.write(self.style.SUCCESS(
                f'\nDone. {updated} Amazon URLs now include the affiliate tag.'
            ))
