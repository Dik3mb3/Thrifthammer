"""
Management command to fetch real product image URLs from the Games Workshop website.

Scrapes GW product pages directly using the product slug to retrieve the official
920x950 CDN image URL from the page's og:image meta tag.

Usage:
    # Fetch images only for products that have no GW image yet:
    python manage.py fetch_gw_images

    # Re-fetch even products that already have a GW image:
    python manage.py fetch_gw_images --all

    # Target specific SKUs only (always re-fetches regardless of existing image):
    python manage.py fetch_gw_images --sku 41-04 41-05 55-24

    # Dry run — print what would be set without saving to DB:
    python manage.py fetch_gw_images --sku 41-04 41-05 --dry-run
"""

import re
import time
import urllib.request

from django.core.management.base import BaseCommand

from products.models import Product

GW_SHOP_BASE  = 'https://www.warhammer.com/en-US/shop/'
GW_CDN_BASE   = 'https://www.warhammer.com'
IMAGE_PATH_RE = re.compile(
    r'https://www\.warhammer\.com/app/resources/catalog/product/920x950/[^"\'>\s]+'
)

# Be polite — one request per second
REQUEST_DELAY = 1.0

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}


def _fetch_image_for_slug(slug):
    """
    Fetch the GW product page for the given slug and return the first
    920x950 CDN image URL found, or None if the page cannot be reached
    or contains no matching image.

    Args:
        slug: Product slug (e.g. 'blood-angels-commander-dante').

    Returns:
        Full CDN image URL string, or None.
    """
    url = GW_SHOP_BASE + slug
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None

    match = IMAGE_PATH_RE.search(html)
    return match.group(0) if match else None


class Command(BaseCommand):
    """Fetch official GW product images by scraping GW product pages."""

    help = (
        'Fetches 920x950 product images from www.warhammer.com and updates '
        'image_url fields. Uses the product slug to construct the page URL. '
        'Never overwrites existing images unless --all or --sku is given.'
    )

    def add_arguments(self, parser):
        """Register CLI arguments."""
        parser.add_argument(
            '--all',
            action='store_true',
            help='Re-fetch images for all products, even those that already have a GW URL.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be set without saving to the database.',
        )
        parser.add_argument(
            '--sku',
            nargs='+',
            metavar='SKU',
            default=None,
            help=(
                'Only process specific products by GW SKU. '
                'Accepts one or more values (e.g. --sku 41-04 41-05 55-24). '
                'Always re-fetches regardless of existing image. Ignores --all.'
            ),
        )

    def handle(self, *args, **options):
        """Main entry point."""
        fetch_all  = options['all']
        dry_run    = options['dry_run']
        sku_filter = options['sku']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        if sku_filter:
            # Targeted run: always re-fetch, regardless of existing image
            qs = (
                Product.objects
                .filter(gw_sku__in=sku_filter, is_active=True)
                .order_by('gw_sku')
            )
            missing = set(sku_filter) - set(qs.values_list('gw_sku', flat=True))
            if missing:
                self.stderr.write(self.style.ERROR(
                    f'SKUs not found in DB: {", ".join(sorted(missing))}'
                ))
            if not qs.exists():
                return
        else:
            qs = Product.objects.filter(is_active=True).order_by('slug')
            if not fetch_all:
                qs = qs.exclude(image_url__startswith=GW_CDN_BASE)

        total     = qs.count()
        found     = 0
        not_found = 0

        self.stdout.write(f'Processing {total} products...\n')

        for i, product in enumerate(qs, start=1):
            if not product.slug:
                self.stdout.write(
                    self.style.WARNING(f'  [skip ] ({i}/{total}) {product.name[:55]} — no slug')
                )
                not_found += 1
                continue

            image_url = _fetch_image_for_slug(product.slug)

            if image_url:
                found += 1
                old = (product.image_url or '')[-40:]
                self.stdout.write(
                    self.style.SUCCESS(f'  [found] ({i}/{total}) {product.gw_sku}  {product.name[:45]}')
                )
                self.stdout.write(f'           > {image_url}')
                if not dry_run:
                    product.image_url = image_url
                    product.save(update_fields=['image_url'])
            else:
                not_found += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  [miss ] ({i}/{total}) {product.gw_sku}  {product.name[:45]}'
                        f'\n           > {GW_SHOP_BASE}{product.slug}'
                    )
                )

            time.sleep(REQUEST_DELAY)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone.  Found: {found}  |  Not found: {not_found}  |  Total: {total}'
        ))
