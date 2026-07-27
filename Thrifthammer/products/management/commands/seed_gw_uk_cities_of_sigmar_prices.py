"""
Seed Games Workshop UK prices for Cities of Sigmar.

Creates the `games-workshop-uk` Retailer if it does not exist, sets
msrp_gbp on each matched Product, and creates/updates a CurrentPrice
record pointing at the GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url)
_PRICES = [
    ('70-22', 'Spearhead: Cities of Sigmar', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-zenestras-zealots-2026'),
    ('86-15', 'Cities of Sigmar Freeguild Fusiliers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/freeguild-fusiliers-2023'),
    ('COS-002', 'Gate Gargants', Decimal('64.50'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-gate-gargants-2026'),
    ('COS-003', 'Mallus Forgepriest', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-mallus-forgepriest-2026'),
    ('COS-004', 'Jorvan Kreel, Heir of the Kraken', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-jorvan-kreel-heir-of-the-kraken-2026'),
    ('COS-005', 'Aqshian Pyrocaster', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-aqshian-pyrocaster-2026'),
    ('COS-006', 'Amethyst Knellmage', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-amethyst-knellmage-2026'),
    ('COS-007', 'Erasmus Zonn the Enlightened One', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-erasmus-zonn-the-enlightened-one-2026'),
    ('COS-008', 'Order Battletome: Cities of Sigmar 4th Edition', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-cities-of-sigmar-2026-eng'),
    ('COS-009', 'Dawner\'s Triumph', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-dawners-triumph-2026'),
    ('COS-010', 'Conqueror Cogfort', Decimal('125.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-conqueror-cogfort-2026'),
    ('COS-011', 'Cannonade Cogfort', Decimal('125.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-cannonade-cogfort-2026'),
    ('COS-012', 'Freeguild Grenadiers', Decimal('36.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-freeguild-grenadiers-2026'),
    ('COS-013', 'Freeguild Gallants', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-freeguild-gallants-2026'),
    ('COS-014', 'Galen and Doralia ven Denst', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/Galen-And-Doralia-Ven-Denst-2021'),
    ('COS-015', 'Wildercorps Hunters', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-wildercorps-hunters-2025'),
    ('COS-016', 'Saviours of Cinderfall', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/callis-toll-saviours-of-cinderfall-2024'),
    ('COS-017', 'Pontifex Zenestra, Matriarch of the Great Wheel', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/zenestra-matriarch-of-the-great-wheel-2023'),
    ('COS-018', 'Tahlia Vedra, Lioness of the Parch', Decimal('98.00'),
     'https://www.warhammer.com/en-GB/shop/tahlia-vedra-lioness-of-the-parch-2023'),
    ('COS-019', 'Fusil-Major on Ogor Warhulk', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/fusil-major-on-ogor-warhulk-2023'),
    ('COS-020', 'Freeguild Marshal and Relic Envoy', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/freeguild-marshal-and-relic-envoy-2023'),
    ('COS-021', 'Ironweld Great Cannon', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/ironweld-great-cannon-2023'),
    ('COS-022', 'Freeguild Steelhelms', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/freeguild-steelhelms-2023'),
    ('COS-023', 'Freeguild Command Corps', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/freeguild-command-corps-2023'),
    ('COS-024', 'Freeguild Cavaliers', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/freeguild-cavaliers-2023'),
    ('COS-025', 'Alchemite Warforger', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/alchemite-warforger-2023'),
    ('COS-026', 'Luminark of Hysh', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/cities-of-sigmar-luminark-of-hysh-2024'),
    ('COS-027', 'Freeguild Cavalier-Marshal', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/freeguild-cavalier-marshal-2023'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Cities of Sigmar. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_GW_UK_SLUG,
            defaults={
                'name': 'Games Workshop UK',
                'website': 'https://www.warhammer.com/en-GB/',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, label, gbp_price, url in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} ({label}) not in DB')
                skipped += 1
                continue

            if product.msrp_gbp != gbp_price:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': gbp_price,
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Cities of Sigmar GW UK prices. Skipped: {skipped}.'
            )
        )
