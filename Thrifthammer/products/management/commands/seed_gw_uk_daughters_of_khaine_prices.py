"""
Seed Games Workshop UK prices for Daughters of Khaine.

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
    ('70-12', 'Spearhead: Daughters of Khaine', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-khainite-shadow-coven-2026'),
    ('85-02', 'Daughters of Khaine Morathi-Khaine', Decimal('105.00'),
     'https://www.warhammer.com/en-GB/shop/Daughters-Of-Khaine-Morathi-2018'),
    ('85-06', 'Daughters of Khaine Witch Aelves', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Daughters-Of-Khaine-Witch-Aelves-2018'),
    ('85-17', 'Daughters of Khaine Sisters of Slaughter', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Daughters-Of-Khaine-Sisters-of-Slaughter-2018'),
    ('DOK-001', 'Blood Stalkers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Daughters-Of-Khaine-Melusai-Blood-Stalkers-2018'),
    ('DOK-002', 'Khinerai Lifetakers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Daughters-Of-Khaine-Khinerai-Lifetakers-2018'),
    ('DOK-003', 'Bloodwrack Shrine', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/Bloodwrack-Shine-2018'),
    ('DOK-004', 'Slaughter Queen on Cauldron of Blood', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/Slaughter-Queen-on-Cauldron-of-Blood-2018'),
    ('DOK-005', 'Hag Queen on Cauldron of Blood', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/Haq-Queen-on-Cauldron-Blood-2018'),
    ('DOK-006', 'Blood Sisters', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Daughters-Of-Khaine-Melusai-Blood-Sisters-2018'),
    ('DOK-007', 'Khinerai Heartrenders', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Daughters-Of-Khaine-Khinerai-Heartrenders-2018'),
    ('DOK-008', 'Shrine of Dark Tribute', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/daughters-of-khaine-shrine-of-dark-tribute-2026'),
    ('DOK-009', 'Melusai Ironscale', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/daughters-of-khaine-melusai-ironscale-2026'),
    ('DOK-010', 'Blood Hags', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/daughters-of-khaine-blood-hags-2026'),
    ('DOK-011', 'Order Battletome: Daughters of Khaine', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-daughters-of-khaine-2026-eng'),
    ('DOK-012', 'Khainite Shadowstalkers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/khainite-shadowstalkers-2022'),
    ('DOK-013', 'High Gladiatrix', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/daughters-of-khaine-high-gladiatrix-2022'),
    ('DOK-014', 'Endless Spells: Daughters of Khaine', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Daughters-Of-Khaine-2021'),
    ('DOK-015', 'Krethusa the Croneseer', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/daughters-of-khaine-krethusa-the-croneseer-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Daughters of Khaine. Idempotent.'

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
                f'Seeded {seeded} Daughters of Khaine GW UK prices. Skipped: {skipped}.'
            )
        )
