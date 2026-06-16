"""
Seed Games Workshop UK prices for Adepta Sororitas (Sisters of Battle).

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
    ('AS-001', 'Armageddon Battalion: Adepta Sororitas',           Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/armageddon-battalion-adepta-sororitas-2026',                        True),
    ('AS-002', 'Kill Team: Celestian Insidiants',                   Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/kill-team-celestian-insidiants-2026',                              True),
    ('52-25',  'Adepta Sororitas Combat Patrol',                    Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-adepta-soritas-2024',                                True),
    ('AS-006', 'Aestred Thurga, Reliquant at Arms',                 Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Aestred-Thurga-Relinquant-At-Arms',                               True),
    ('AS-004', 'Codex: Adepta Sororitas',                           Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-adepta-sororitas-2024-eng',                                 True),
    ('AS-007', 'Adepta Sororitas Castigator',                       Decimal('57.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Castigator',                                     True),
    ('52-02',  'Adepta Sororitas Morvenn Vahl',                     Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Morvenn-Vahl-Abbess-Sanctorum-2021',                              True),
    ('AS-008', 'Adepta Sororitas Paragon Warsuits',                 Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Paragon-Warsuit-2021',                           True),
    ('52-22',  'Adepta Sororitas Celestian Sacresants',             Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Celestian-Sacresants-2021',                      True),
    ('AS-027', 'Adepta Sororitas Sister Dogmata',                   Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Sister-Dogmata-2021',                            True),
    ('AS-009', 'Adepta Sororitas Palatine',                         Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Palatine-2021',                                  True),
    ('AS-010', 'Adepta Sororitas Daemonifuge',                      Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Daemonifuge-Ephrael-Stern-and-Kyganil-2020',                      True),
    ('AS-012', 'Adepta Sororitas Rhino',                            Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Rhino-2020',                                     True),
    ('AS-013', 'Adepta Sororitas Repentia Squad',                   Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Repentia-Squad-2020',                            True),
    ('AS-014', 'Adepta Sororitas Canoness',                         Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Canoness-2020',                                  True),
    ('52-09',  'Adepta Sororitas Immolator',                        Decimal('52.50'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Immolator-2020',                                 True),
    ('AS-015', 'Adepta Sororitas Dialogus',                         Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Dialogus-2020',                                  True),
    ('AS-016', 'Adepta Sororitas Imagifier',                        Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Imagifier-2020',                                 True),
    ('AS-028', 'Adepta Sororitas Mortifiers',                       Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Mortifier-2020',                                 True),
    ('AS-029', 'Adepta Sororitas Penitent Engines',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Penitent-Engines-2020',                          True),
    ('AS-017', 'Adepta Sororitas Arco-flagellants',                 Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Arco-Flagellants-2020',                          True),
    ('AS-018', 'Adepta Sororitas Junith Eruita',                    Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Junith-Eruita-2020',                             True),
    ('AS-019', 'Adepta Sororitas Hospitaller',                      Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Hospitaller-2020',                               True),
    ('52-08',  'Adepta Sororitas Exorcist',                         Decimal('57.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Exorcist-2020',                                  True),
    ('52-15',  'Adepta Sororitas Retributor Squad',                 Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Retributor-Squad-2020',                          True),
    ('AS-020', 'Adepta Sororitas Triumph of Saint Katherine',       Decimal('74.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-The-Triumph-Of-St-Katherine-2020',               True),
    ('52-20',  'Adepta Sororitas Battle Sisters Squad',             Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Battle-Sisters-Squad-2020',                      True),
    ('AS-030', 'Adepta Sororitas Sister Superior Amalia Novena',    Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Sister-Superior-Amalia-Novena-2019',                              True),
    ('AS-021', 'Adepta Sororitas Celestine, the Living Saint',      Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Space-Marine-Celestine-The-Living-Saint-2018',                    True),
    ('AS-022', 'Adepta Sororitas Dominion Squad',                   Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Dominions-Celestians-2020',                      True),
    ('AS-003', 'Adepta Sororitas Intranzia Fraye',                  Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/adepta-sororitas-intranzia-fraye-dogmata-superior-2026',          True),
    ('AS-023', 'Adepta Sororitas Sisters Novitiate Squad',          Decimal('38.50'),  'https://www.warhammer.com/en-GB/shop/adepta-sororitas-sisters-novitiate-squad-2025',                   True),
    ('AS-005', 'Kill Team: Sanctifiers',                            Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/kill-team-sanctifiers-2025',                                      True),
    ('AS-024', 'Adepta Sororitas Canoness with Jump Pack',          Decimal('28.00'),  'https://www.warhammer.com/en-GB/shop/adepta-sororitas-canoness-with-jump-pack-2024',                   True),
    ('AS-025', 'Adepta Sororitas Ministorum Priest',                Decimal('23.00'),  'https://www.warhammer.com/en-GB/shop/adepta-sororitas-ministorum-priest-2024',                         True),
    ('AS-026', 'Adepta Sororitas Ministorum Priest with Vindictor', Decimal('23.00'),  'https://www.warhammer.com/en-GB/shop/adepta-sororitas-ministorum-priest-with-vindicator-2024',         True),
    ('AS-011', 'Adepta Sororitas Zephyrim Squad',                   Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Zephyrim-Squad-2020',                            True),
    ('52-12',  'Adepta Sororitas Seraphim Squad',                   Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Adepta-Sororitas-Seraphim-Squad-2020',                            True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Adepta Sororitas. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Adepta Sororitas GW UK prices. Skipped: {skipped}.')
