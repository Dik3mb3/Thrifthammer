"""
Management command: seed_nk_disciples_of_tzeentch_prices

Seeds Noble Knight CurrentPrice records for Disciples of Tzeentch products
(DOT-001 to DOT-012) from the AOS Disciples of Tzeentch - GW, NK, MM.xlsx (2026-06-24).

10 of 12 products have confirmed NK URLs.
No NK entries for: DOT-003 Tzaangor Enlightened, DOT-004 Tzaangor Shaman.

Dual-kit notes:
  - DOT-005 Magister and DOT-008 Magister on Disc of Tzeentch share one NK listing.

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_disciples_of_tzeentch_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    (
        'warcry-the-jade-obelisk',
        'Jade Obelisk, The',
        None,
        f'{_NK}/P/2148036066/Jade-Obelisk-The{_AFF}',
        True,
        False,
    ),
    (
        'curseling-eye-of-tzeentch',
        'Curseling Eye of Tzeentch',
        None,
        f'{_NK}/P/2148021540/Curseling-Eye-of-Tzeentch{_AFF}',
        True,
        False,
    ),
    # ⚠ Dual kit: Magister and Magister on Disc of Tzeentch share one NK listing.
    (
        'magister',
        'Magister on Disc of Tzeentch',
        None,
        f'{_NK}/P/2147841746/Magister-on-Disc-of-Tzeentch{_AFF}',
        True,
        False,
    ),
    (
        'magister-on-disc-of-tzeentch',
        'Magister on Disc of Tzeentch',
        None,
        f'{_NK}/P/2147841746/Magister-on-Disc-of-Tzeentch{_AFF}',
        True,
        False,
    ),
    (
        'ogroid-thaumaturge',
        'Ogroid Thaumaturge',
        None,
        f'{_NK}/P/2147653700/Ogroid-Thaumaturge{_AFF}',
        True,
        False,
    ),
    (
        'fatemaster',
        'Fatemaster',
        None,
        f'{_NK}/P/2148411212/Fatemaster{_AFF}',
        True,
        False,
    ),
    (
        'kairic-acolytes',
        'Kairic Acolytes',
        None,
        f'{_NK}/P/2147655398/Kairic-Acolytes{_AFF}',
        True,
        False,
    ),
    (
        'endless-spells-disciples-of-tzeentch',
        'Endless Spells - Disciples of Tzeentch',
        None,
        f'{_NK}/P/2147789480/Endless-Spells---Disciples-of-Tzeentch{_AFF}',
        True,
        False,
    ),
    (
        'argent-shards',
        'Argent Shards',
        None,
        f'{_NK}/P/2148411026/Argent-Shards{_AFF}',
        True,
        False,
    ),
    (
        'chaos-battletome-disciples-of-tzeentch',
        'Chaos Battletome - Disciples of Tzeentch',
        None,
        f'{_NK}/P/2148411063/Chaos-Battletome---Disciples-of-Tzeentch{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Disciples of Tzeentch (10 of 12 have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for DOT-001 to DOT-012 (10 products have NK URLs).'

    def handle(self, *args, **options):
        """Run the command."""
        nk = Retailer.objects.filter(name='Noble Knight Games').first()
        if not nk:
            self.stderr.write(self.style.ERROR('Noble Knight Games retailer not found.'))
            return

        created_count = 0
        updated_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stderr.write(self.style.WARNING(
                    f'  Product not found: {slug} -- skipping'
                ))
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_disciples_of_tzeentch_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
