"""
Seed Games Workshop UK prices for Ogor Mawtribes.

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
    ('OM-004', 'Bloodpelt Hunter', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/ogor-mawtribes-bloodpelt-hunter-2022'),
    ('OM-006', 'Great Mawpot', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Ogre-Mawtribes-Great-Mawpot-2019'),
    ('OM-007', 'Gnoblar Scraplauncher', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Scraplauncher-2018'),
    ('OM-008', 'Ironblaster', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Gutbusters-Ironblaster-2018'),
    ('OM-009', 'Thundertusk Beastriders', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/beastclaw-raiders-thundertusk-beastriders'),
    ('OM-010', 'Stonehorn Beastriders', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/beastclaw-raiders-stonehorn-beastriders'),
    ('OM-011', 'Huskard on Thundertusk', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/beastclaw-raiders-huskard-on-thundertusk'),
    ('OM-012', 'Huskard on Stonehorn', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/beastclaw-raiders-huskard-on-stonehorn'),
    ('OM-013', 'Frostlord on Thundertusk', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/beastclaw-raiders-frostlord-on-thundertusk'),
    ('OM-015', 'Frostlord on Stonehorn', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/beastclaw-raiders-frostlord-on-stonehorn'),
    ('OM-018', 'Gorger Mawpack', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/warcry-gorger-mawpack-2024'),
    ('OM-019', 'Mawpit', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/ogor-mawtribes-maw-pit-2023'),
    ('OM-022', 'Gnoblars', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Scraplauncher-2018'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Ogor Mawtribes. Idempotent.'

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
                f'Seeded {seeded} Ogor Mawtribes GW UK prices. Skipped: {skipped}.'
            )
        )
