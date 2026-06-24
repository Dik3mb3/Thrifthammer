"""
Management command: seed_nk_blades_of_khorne_prices

Seeds Noble Knight CurrentPrice records for Blades of Khorne products
(BOK-001 to BOK-012) from the AOS Blades of Khorne - GW, NK, MM.xlsx (2026-06-24).

All 12 products have confirmed NK URLs.

Dual-kit notes:
  - BOK-003 Skullreapers and BOK-005 Wrathmongers share one NK listing
    (same physical box, builds either kit).

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_blades_of_khorne_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [

    # -- Heroes ----------------------------------------------------------------
    (
        'realmgore-ritualist',
        'Realmgore Ritualist',
        None,
        f'{_NK}/P/2148041466/Realmgore-Ritualist{_AFF}',
        True,
        False,
    ),
    (
        'slaughterpriest',
        'Slaughterpriest',
        None,
        f'{_NK}/P/2147597104/Slaughterpriest{_AFF}',
        True,
        False,
    ),
    (
        'deathbringer',
        'Aspiring Deathbringer w/ Goreaxe and Skullhammer',
        None,
        f'{_NK}/P/2147622153/Aspiring-Deathbringer-w-Goreaxe-and-Skullhammer{_AFF}',
        True,
        False,
    ),
    (
        'skullgrinder',
        'Skullgrinder',
        None,
        f'{_NK}/P/2147597105/Skullgrinder{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Skullreapers and Wrathmongers share one NK listing.
    (
        'skullreapers',
        'Wrathmongers',
        None,
        f'{_NK}/P/2148092160/Wrathmongers{_AFF}',
        True,
        False,
    ),
    (
        'wrathmongers',
        'Wrathmongers',
        None,
        f'{_NK}/P/2148092160/Wrathmongers{_AFF}',
        True,
        False,
    ),
    (
        'blood-warriors',
        'Blood Warriors',
        None,
        f'{_NK}/P/2148050435/Blood-Warriors{_AFF}',
        True,
        False,
    ),
    (
        'mighty-skullcrushers',
        'Mighty Skullcrushers',
        None,
        f'{_NK}/P/2147597080/Mighty-Skullcrushers{_AFF}',
        True,
        False,
    ),
    (
        'claws-of-karanak',
        'Claws of Karanak',
        None,
        f'{_NK}/P/2148054133/Claws-of-Karanak{_AFF}',
        True,
        False,
    ),
    (
        'goreblade-warband',
        'Blades of Khorne - Goreblade Warband',
        None,
        f'{_NK}/P/2148447207/Blades-of-Khorne---Goreblade-Warband{_AFF}',
        True,
        False,
    ),

    # -- Terrain / Endless Spells ----------------------------------------------
    (
        'judgements-of-khorne',
        'Judgements of Khorne',
        None,
        f'{_NK}/P/2147746900/Judgements-of-Khorne{_AFF}',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'chaos-battletome-blades-of-khorne',
        'Chaos Battletome - Blades of Khorne',
        None,
        f'{_NK}/P/2148330258/Chaos-Battletome---Blades-of-Khorne{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Blades of Khorne (all 12 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for BOK-001 to BOK-012 (12 products).'

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
            f'seed_nk_blades_of_khorne_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
