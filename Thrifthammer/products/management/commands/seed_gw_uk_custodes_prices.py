"""
Seed Games Workshop UK prices for Custodes.

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
    ('01-02',  'Adeptus Custodes Trajann Valoris',                              Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Captain-general-Trajann-Valoris-2018',                               True),
    ('01-07',  'Adeptus Custodes Shield-Captain',                               Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/adeptus-custodes-shield-captain-2024',                               True),
    ('01-08',  'Adeptus Custodes Custodian Guard',                              Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adeptus-Custodes-Custodian-Guard-2018',                              True),
    ('01-10',  'Adeptus Custodes Custodian Wardens',                            Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adeptus-Custodes-Custodian-Wardens-2018',                            True),
    ('01-11',  'Adeptus Custodes Vertus Praetors',                              Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adeptus-Custodes-Vertus-Praetors-2018',                              True),
    ('01-20',  'Adeptus Custodes Combat Patrol',                                Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-adeptus-custodes-2024',                                True),
    ('AC-001', 'Codex: Adeptus Custodes',                                       Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-adeptus-custodes-eng-2024',                                    True),
    ('AC-002', 'Custodes Allarus Custodians',                                   Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Adeptus-Custodes-Allarus-Custodians-2018',                           True),
    ('AC-003', 'Custodes Blade Champion',                                       Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/adeptus-custodes-blade-champion-2022',                               True),
    ('AC-004', 'Custodes Caladius Annihilator Grav-tank',                       Decimal('61.50'),  'https://www.warhammer.com/en-GB/shop/legio-custodes-caladius-grav-tank-annihilator-2026',                 True),
    ('AC-005', 'Custodes Caladius Grav-tank',                                   Decimal('61.50'),  'https://www.warhammer.com/en-GB/shop/legio-custodes-caladius-grav-tank-2026',                             True),
    ('AC-006', 'Custodes Contemptor Dreadnought',                               Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/legiones-astartes-contemptor-dreadnought-2022',                      True),
    ('AC-007', 'Custodes Coronus Grav-carrier',                                 Decimal('78.00'),  'https://www.warhammer.com/en-GB/shop/legio-custodes-coronus-grav-carrier-2026',                           True),
    ('AC-008', 'Custodes Custodian Dreadnought',                                Decimal('47.00'),  'https://www.warhammer.com/en-GB/shop/legio-custodes-custodian-dreadnought-2026',                          True),
    ('AC-009', 'Custodes Custodian Guard Sodality',                             Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/legio-custodes-custodian-guard-sodality-2026',                       True),
    ('AC-010', 'Custodes Prosecutor Squad',                                     Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Sisters-Of-Silence-2017',                                            True),
    ('AC-011', 'Custodes Sentinel Guard Sodality',                              Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/legio-custodes-sentinel-guard-sodality-2026',                        True),
    ('AC-012', 'Custodes Talons of the Emperor: Valerian and Aleya',            Decimal('37.00'),  'https://www.warhammer.com/en-GB/shop/Talons-Of-The-Emperor-Valerian-And-Aleya-2020',                      True),
    ('AC-013', 'Custodes Telemon Iliastus Accelerator Culverin',                Decimal('18.50'),  'https://www.warhammer.com/en-GB/shop/Legio-Custodes-Telemon-Dreadnought-Iliastus-Accelerator-Culverin-2017', True),
    ('AC-014', 'Custodes Venatari Sodality',                                    Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/legio-custodes-venatari-sodality-2026',                              True),
    ('AC-015', 'Custodes Vigilator Squad',                                      Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Vigilator-Squad',                                                    True),
    ('AC-016', 'Custodes Witchseeker Squad',                                    Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Witchseeker-Squad',                                                  True),
    ('AC-017', 'Legio Custodes Aquilon Terminators',                            Decimal('67.50'),  'https://www.warhammer.com/en-GB/shop/Legio-Custodes-Aquilon-Terminators-2017',                            True),
    ('AC-018', 'Legio Custodes Aquilon Terminators with Infernus Firepikes',    Decimal('67.50'),  'https://www.warhammer.com/en-GB/shop/Legio-Custodes-Aquilon-Terminators-with-Infernus-Firepikes-2017',    True),
    ('AC-019', 'Legio Custodes Ares Gunship',                                   Decimal('364.50'), 'https://www.warhammer.com/en-GB/shop/Legio-Custodes-Ares-Gunship-2019',                                   True),
    ('AC-020', 'Legio Custodes Gyrfalcon Pattern Jetbike',                      Decimal('48.50'),  'https://www.warhammer.com/en-GB/shop/Legio-Custodes-Gyrfalcon-Pattern-Jetbike',                           True),
    ('AC-021', 'Legio Custodes Orion Assault Dropship',                         Decimal('377.50'), 'https://www.warhammer.com/en-GB/shop/Custodes-Gunship-2017',                                              True),
    ('AC-022', 'Legio Custodes Pallas Grav-attack',                             Decimal('83.00'),  'https://www.warhammer.com/en-GB/shop/Legio-Custodes-Pallas-Grav-attack',                                  True),
    ('AC-023', 'Legio Custodes Shield Captain',                                 Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Legio-Custodes-Shield-Captain-2018',                                 True),
    ('AC-024', 'Legio Custodes Telemon Arachnus Storm Cannon',                  Decimal('18.50'),  'https://www.warhammer.com/en-GB/shop/Legio-Custodes-Telemon-Storm-Cannon-Arm-2017',                       True),
    ('AC-025', 'Legio Custodes Telemon Caestus',                                Decimal('18.50'),  'https://www.warhammer.com/en-GB/shop/Legio-custodes-heavy-dreadnought-arm-2017',                          True),
    ('AC-026', 'Legio Custodes Telemon Heavy Dreadnought Body',                 Decimal('66.50'),  'https://www.warhammer.com/en-GB/shop/Legio-custodes-heavy-dreadnought-body-2017',                         True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Custodes. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Custodes GW UK prices. Skipped: {skipped}.')
