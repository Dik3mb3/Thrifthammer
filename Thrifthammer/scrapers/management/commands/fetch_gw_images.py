"""
Management command to fetch real product image URLs from the Games Workshop website.

Uses GW's Algolia search index (public read-only API) to match products by name
and retrieve the official 920x950 product image URL.

Usage:
    python manage.py fetch_gw_images            # update all products missing real images
    python manage.py fetch_gw_images --all      # re-fetch even products that already have GW images
    python manage.py fetch_gw_images --dry-run  # print matches without saving
"""

import json
import time
import urllib.request
import urllib.parse
from django.core.management.base import BaseCommand
from products.models import Product


# ── Algolia credentials (public read-only, embedded in GW's client-side JS) ──
ALGOLIA_APP_ID  = 'M5ZIQZNQ2H'
ALGOLIA_API_KEY = '92c6a8254f9d34362df8e6d96475e5d8'
ALGOLIA_INDEX   = 'prod-lazarus-product-en-us'
ALGOLIA_URL     = f'https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{ALGOLIA_INDEX}/query'
GW_CDN_BASE     = 'https://www.warhammer.com'
IMAGE_PATH_PREFIX = '/app/resources/catalog/product/920x950/'

# Delay between API calls to be polite
REQUEST_DELAY = 0.4  # seconds


def _algolia_search(query, hits=5):
    """Query GW's Algolia index and return hits list."""
    payload = json.dumps({
        'query': query,
        'hitsPerPage': hits,
        'attributesToRetrieve': ['name', 'sku', 'slug', 'images'],
    }).encode()

    req = urllib.request.Request(
        ALGOLIA_URL,
        data=payload,
        method='POST',
        headers={
            'X-Algolia-Application-Id': ALGOLIA_APP_ID,
            'X-Algolia-API-Key': ALGOLIA_API_KEY,
            'Content-Type': 'application/json',
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read()).get('hits', [])


def _best_image_url(hits, product_name):
    """
    Pick the best 920x950 JPEG image from Algolia hits.

    Strategy:
    1. Find the hit whose name most closely matches the product name
    2. From that hit's images list, take the first 920x950 JPEG (not threeSixty)
    Returns full CDN URL or None.
    """
    name_lower = product_name.lower()

    # Score hits by how many words from the product name appear in the hit name
    def score(hit):
        hit_name = hit.get('name', '').lower()
        words = [w for w in name_lower.split() if len(w) > 3]
        return sum(1 for w in words if w in hit_name)

    hits_sorted = sorted(hits, key=score, reverse=True)

    for hit in hits_sorted:
        for img_path in hit.get('images', []):
            if img_path.startswith(IMAGE_PATH_PREFIX) and img_path.endswith('.jpg'):
                return GW_CDN_BASE + img_path

    return None


class Command(BaseCommand):
    """Fetch real GW product images via Algolia and update image_url fields."""

    help = 'Fetches official Games Workshop product images and updates the database.'

    def add_arguments(self, parser):
        """Add --all and --dry-run flags."""
        parser.add_argument(
            '--all',
            action='store_true',
            help='Re-fetch images for all products, even those already updated.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print matches without saving to the database.',
        )

    def handle(self, *args, **options):
        """Main entry point — iterate products and fetch images."""
        fetch_all = options['all']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        # Build queryset: skip products that already have a real GW image unless --all
        qs = Product.objects.filter(is_active=True).order_by('name')
        if not fetch_all:
            qs = qs.exclude(image_url__startswith=GW_CDN_BASE)

        total    = qs.count()
        updated  = 0
        not_found = 0

        self.stdout.write(f'Processing {total} products...\n')

        for i, product in enumerate(qs, start=1):
            try:
                hits = _algolia_search(product.name)
                image_url = _best_image_url(hits, product.name)
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(f'  [error] {product.name[:50]} — {exc}')
                )
                time.sleep(REQUEST_DELAY * 3)
                continue

            if image_url:
                status = '[found]'
                updated += 1
                if not dry_run:
                    product.image_url = image_url
                    product.save(update_fields=['image_url'])
            else:
                status = '[miss ]'
                not_found += 1

            self.stdout.write(
                f'  {status} ({i}/{total}) {product.name[:50]}'
                + (f'\n          > {image_url}' if image_url else '')
            )

            time.sleep(REQUEST_DELAY)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone!  Updated: {updated}  |  Not found: {not_found}  |  Total: {total}'
            )
        )
