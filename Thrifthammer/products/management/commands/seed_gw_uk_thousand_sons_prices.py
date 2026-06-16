"""
Seed Games Workshop UK prices for Thousand Sons.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('43-02',              'Thousand Sons Magnus the Red',              Decimal('105.50'), 'https://www.warhammer.com/en-GB/shop/magnus-the-red',                            True),
    ('43-30',              'Thousand Sons Ahriman',                     Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/ahriman-arch-sorcerer-of-tzeentch',         True),
    ('43-35',              'Thousand Sons Rubric Marines',              Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/rubric-marines',                            True),
    ('43-36',              'Thousand Sons Scarab Occult Terminators',  Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/scarab-occult-terminators',                 True),
    ('43-38',              'Thousand Sons Exalted Sorcerers',          Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/exalted-sorcerers',                         True),
    ('43-79',              'Thousand Sons Infernal Master',            Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/thousand-sons-infernal-master-2022',         True),
    ('43-90',              'Thousand Sons Combat Patrol',               Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-thousand-sons-2025',          True),
    ('P-MUTALITH-VB',      'Mutalith Vortex Beast',                    Decimal('58.00'),  'https://www.warhammer.com/en-GB/shop/Mutalith-Vortex-Beast',                    True),
    ('P-PINK-HORRORS-40K', 'Pink Horrors of Tzeentch',                 Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/pink-horrors-2018',                         True),
    ('P-TS-CODEX-2023',    'Codex: Thousand Sons',                     Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-thousand-sons-hb-2025-eng',           True),
    ('P-TS-SEKHETAR-2025', 'Thousand Sons Sekhetar Robots',            Decimal('31.50'),  'https://www.warhammer.com/en-GB/shop/thousand-sons-sekhetar-robots-2025',        True),
    ('P-TZAANGOR-ENL',     'Tzaangor Enlightened',                     Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Tzaangor-Enlightened',                     True),
    ('P-TZAANGORS-40K',    'Thousand Sons Tzaangors',                  Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Tzaangors-AoS',                            True),
    ('P-TZAANGOR-SHAMAN',  'Tzaangor Shaman',                          Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Tzaangor-Shaman',                          True),
    ('P-TZAANGOR-UPG',     'Tzaangor Upgrade Pack',                    Decimal('9.50'),   'https://www.warhammer.com/en-GB/shop/Tzaangor-Upgrades-2018',                   True),
    ('P-TZEENTCH-BLUEHORRORS', 'Blue Horrors and Brimstone Horrors',   Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/blue-horrors-2016',                         True),
    ('P-TZEENTCH-FLAMERS', 'Flamers of Tzeentch',                      Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/flamers-of-tzeentch-2017',                  True),
    ('P-TZEENTCH-KAIROS',  'Kairos Fateweaver',                        Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/Kairos-Fateweaver-2017',                   True),
    ('P-TZEENTCH-LOC',     'Lord of Change',                           Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/lord-of-change-2016',                      True),
    ('P-TZEENTCH-SCREAMERS', 'Screamers of Tzeentch',                  Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/screamers-2016',                           True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices for Thousand Sons. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Thousand Sons GW UK prices. Skipped: {skipped}.')
