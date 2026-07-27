"""
Seed Games Workshop UK prices for Ossiarch Bonereapers.

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
    ('70-09', 'Spearhead: Ossiarch Bonereapers', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-ossiarch-bonereapers-kavalos-vanguard-2026'),
    ('94-10', 'Ossiarch Bonereapers Mortek Guard', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Mortek-Guard-2019'),
    ('94-12', 'Ossiarch Bonereapers Necropolis Stalkers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Necropolis-Stalkers-2019'),
    ('94-14', 'Ossiarch Bonereapers Gothizzar Harvester', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Gothizzar-Harvester-2019'),
    ('OBR-001', 'Battleforce: Ossiarch Bonereapers - Null Myriad Phalanx', Decimal('155.00'),
     'https://www.warhammer.com/en-GB/shop/ossiarch-bonereapers-null-myriad-phalanx-2026'),
    ('OBR-002', 'Regiment of Renown: Heralds of the Bone-tithe', Decimal('57.00'),
     'https://www.warhammer.com/en-GB/shop/ossiarch-bonereapers-heralds-of-the-bone-tithe-2026'),
    ('OBR-003', 'Mortisan Ossifector', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/ossiarch-bonereapers-mortisan-ossifector-2023'),
    ('OBR-004', 'Mortisan Soulmason', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Mortisan-Soulmason-2019'),
    ('OBR-005', 'Kavalos Deathriders', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Kavalos-Deathriders-2019'),
    ('OBR-006', 'Katakros, Mortarch of the Necropolis', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Katakros-Mortarch-Of-The-Necropolis-2019'),
    ('OBR-007', 'Arch-Kavalos Zandtos', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Arch-Kavalos-Zandtos-Dark-Lance-Of-Ossia-2019'),
    ('OBR-008', 'Endless Spells: Ossiarch Bonereapers', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Ossiarch-Bonereapers-2019'),
    ('OBR-009', 'Morghast Harbingers', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Morghast-Harbingers-2018'),
    ('OBR-010', 'Morghast Archai', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Morghast-Archai-2018'),
    ('OBR-011', 'Arkhan the Black, Mortarch of Sacrament', Decimal('57.00'),
     'https://www.warhammer.com/en-GB/shop/Deathlords-Mortarchs-Arkhan'),
    ('OBR-012', 'Mortisan Soulreaper', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/ossiarch-bonereapers-mortisan-soulreaper-2026'),
    ('OBR-013', 'Liege-Mortek', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/ossiarch-bonereapers-liege-mortek-2026'),
    ('OBR-014', 'Mortek Triaxes', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/ossiarch-bonereapers-mortek-triaxes-2026'),
    ('OBR-015', 'Liege-Kavalos on War Chariot', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/ossiarch-bonereapers-liege-kavalos-on-war-chariot-2026'),
    ('OBR-016', 'Death Battletome: Ossiarch Bonereapers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-ossiarch-bonereapers-2026-eng'),
    ('OBR-017', 'Warcry: Teratic Cohort', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/warcry-teratic-cohort-2024'),
    ('OBR-018', 'Mortek Crawler', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Mortek-Crawler-2019'),
    ('OBR-019', 'Mortisan Boneshaper', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Mortisan-Boneshaper-2019'),
    ('OBR-020', 'Bone-tithe Nexus', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/Ossiarch-Bonereapers-Bone-Tithe-Nexus-2019'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Ossiarch Bonereapers. Idempotent.'

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
                f'Seeded {seeded} Ossiarch Bonereapers GW UK prices. Skipped: {skipped}.'
            )
        )
