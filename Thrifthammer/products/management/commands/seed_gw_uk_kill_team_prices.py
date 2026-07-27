"""
Seed Games Workshop UK prices for Kill Team.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('KT-002', 'Killzone: Tomb World',                 Decimal('98.00'), 'https://www.warhammer.com/en-GB/shop/killzone-tomb-world-2025',                         True),
    ('KT-003', 'Kill Team: Starter Set',              Decimal('69.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-starter-set-2024-eng',                   True),
    ('KT-004', 'Kill Team: Battleclade',              Decimal('44.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-battleclade-2025',                        True),
    ('KT-005', 'Kill Team: Sanctifiers',              Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-sanctifiers-2025',                        True),
    ('KT-006', 'Kill Team: Goremongers',              Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-goremongers-2025',                        True),
    ('KT-007', 'Kill Team: Wrecka Krew',              Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-wrecka-krew-2025',                        True),
    ('KT-008', 'Kill Team: Fellgor Ravagers',         Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-fellgor-ravagers-2024',                   True),
    ('KT-009', 'Kill Team: Exaction Squad',           Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-exaction-squad-2024',                     True),
    ('KT-010', 'Kill Team: Imperial Navy Breachers',  Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-imperial-navy-breachers-2024',            True),
    ('KT-011', 'Kill Team: Tempestus Aquilons',       Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-tempestus-aquilons-2024',                 True),
    ('KT-012', 'Kill Team: Kasrkin',                  Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-kasrkin-2024',                            True),
    ('KT-013', 'Killzone: Bheta-Decima',              Decimal('78.00'), 'https://www.warhammer.com/en-GB/shop/killzone-bheta-decima-2024',                        True),
    ('KT-014', 'Killzone: Gallowdark',                Decimal('78.00'), 'https://www.warhammer.com/en-GB/shop/killzone-gallowdark-2024',                          True),
    ('KT-015', 'Kill Team: Equipment Pack',           Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/kill-team-upgrade-equipment-pack-2024',             True),
    ('KT-016', 'Kill Team: Brood Brothers',           Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-brood-brothers-2024',                     True),
    ('KT-017', 'Kill Team: Nemesis Claw',             Decimal('47.00'), 'https://www.warhammer.com/en-GB/shop/kill-team-nemesis-claw-2024',                       True),
    ('KT-018', 'Kill Team: Scout Squad',              Decimal('49.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-scout-squad-2024',                        True),
    ('KT-019', 'Kill Team: Ratlings',                 Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-ratlings-2025',                           True),
    ('KT-020', 'Kill Team: Hearthkyn Salvagers',      Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-hearthkyn-salvagers-2024',                True),
    ('KT-021', 'Kill Team: Hand of the Archon',       Decimal('36.00'), 'https://www.warhammer.com/en-GB/shop/kill-team-hand-of-the-archon-2024',                 True),
    ('KT-022', 'Kill Team: Hierotek Circle',          Decimal('47.00'), 'https://www.warhammer.com/en-GB/shop/kill-team-hierotek-circle-2024',                    True),
    ('KT-023', 'Kill Team: Farstalker Kinband',       Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-farstalker-kinband-2024',                 True),
    ('KT-024', 'Kill Team: Vespid Stingwings',        Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-tau-empire-vespid-stingwings-2024',       True),
    ('KT-025', 'Kill Team: Hernkyn Yaegirs',          Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-hernkyn-yaegirs-2024',                    True),
    ('KT-026', 'Kill Team: Wolf Scouts',              Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-wolf-scouts-2026',                        True),
    ('KT-027', 'Kill Team: Mandrakes',                Decimal('49.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-mandrakes-2024',                          True),
    ('KT-028', 'Kill Team: Stealth Battlesuits',      Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-xv26-stealth-battlesuits-2026',           True),
    ('KT-029', 'Kill Team: Canoptek Circle',          Decimal('47.00'), 'https://www.warhammer.com/en-GB/shop/kill-team-canoptek-circle-2025',                    True),
    ('KT-030', 'Kill Team: Raveners',                 Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-raveners-2025',                           True),
    ('KT-031', 'Killzone: Volkus',                    Decimal('85.00'), 'https://www.warhammer.com/en-GB/shop/killzone-volkus-2024',                              True),
    ('KT-032', 'Kill Team: Blades of Khaine',         Decimal('49.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-blades-of-khaine-2024',                   True),
    ('KT-033', 'Kill Team: Inquisitorial Agents',     Decimal('36.00'), 'https://www.warhammer.com/en-GB/shop/kill-team-inquisitorial-agents-2024',               True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices for Kill Team. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Kill Team GW UK prices. Skipped: {skipped}.')
