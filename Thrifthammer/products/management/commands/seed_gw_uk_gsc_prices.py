"""
Seed Games Workshop UK prices for Genestealer Cults.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('51-40',  'GSC Neophyte Hybrids',       Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/neophite-hybrids-2016',                           True),
    ('51-41',  'GSC Acolyte Hybrids',         Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/acolyte-hybrids-2016',                             True),
    ('51-42',  'GSC Broodcoven',              Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Broodcoven',                     True),
    ('51-43',  'GSC Magus',                   Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Magus-2019',                     True),
    ('51-44',  'GSC Aberrants',               Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Aberrants-2019',                 True),
    ('51-69',  'GSC Combat Patrol',           Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-genestealer-cults-2024',              True),
    ('GC-001', 'Codex: Genestealer Cults',   Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-genestealer-cults-2024-eng',                 True),
    ('GC-002', 'GSC Reductus Saboteur',       Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/genestealer-cults-reductus-saboteur-2022',         True),
    ('GC-003', 'GSC Kelermorph',              Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Kelermorph-2020',                True),
    ('GC-004', 'GSC Abominant',               Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Abominant-2019',                 True),
    ('GC-005', 'GSC Biophagus',               Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Biophagus-2019',                 True),
    ('GC-006', 'GSC Atalan Jackals',          Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Atalan-Jackals-2019',            True),
    ('GC-007', 'GSC Nexos',                   Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Nexos-2019',                     True),
    ('GC-008', 'GSC Locus',                   Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Locus-2019',                     True),
    ('GC-009', 'GSC Sanctus',                 Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Sanctus-2019',                   True),
    ('GC-010', 'GSC Goliath Rockgrinder',     Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/goliath-rockgrinder-2016',                         True),
    ('GC-011', 'GSC Goliath Truck',           Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/goliath-truck-2016',                               True),
    ('GC-012', 'GSC Acolyte Iconward',        Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/acolyte-iconward-2016',                            True),
    ('GC-013', 'GSC Hybrid Metamorphs',       Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/hybrid-metamorphs-2016',                           True),
    ('GC-014', 'GSC Benefictus',              Decimal('23.00'),  'https://www.warhammer.com/en-GB/shop/genestealer-cults-benefictus-2024',                True),
    ('GC-015', 'GSC Genestealers',            Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/tyranids-genestealers-2023',                       True),
    ('GC-016', 'GSC Achilles Ridgerunner',    Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Achilles-Ridgerunner-2019',      True),
    ('GC-017', 'GSC Jackal Alphus',           Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Jackal-Alphus-2019',             True),
    ('GC-018', 'GSC Clamavus',                Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Genestealer-Cults-Clamavus-2019',                  True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Genestealer Cults. Idempotent.'

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

        for sku, label, gbp_price, url, in_stock in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stdout.write(f'  SKIP {sku} ({label}) — not found in DB')
                skipped += 1
                continue
            for product in products:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'url': url,
                        'in_stock': in_stock,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(f'Seeded {seeded} Genestealer Cults GW UK prices. Skipped: {skipped}.')
