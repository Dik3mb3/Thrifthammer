"""
Seed Games Workshop UK prices for Adeptus Mechanicus.

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
    ('59-25', 'Combat Patrol: Adeptus Mechanicus', Decimal('105.00'),
     'https://www.warhammer.com/en-GB/shop/combat-patrol-adeptus-mechanicus-2023'),
    ('MC-025', 'Codex: Adeptus Mechanicus', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/codex-adeptus-mechanicus-hb-eng-2023'),
    ('MC-021', 'Technoarcheologist', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/adeptus-mechanicus-technoarchaeologist-2022'),
    ('MC-013', 'Serberys Sulphurhounds', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Serberys-Sulphurhounds--2020'),
    ('MC-011', 'Pteraxii Sterylizors', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Pteraxii-Sterylizors-2020'),
    ('MC-002', 'Archaeopter Stratoraptor', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Archaeopter-Stratoraptor-2020'),
    ('MC-001', 'Archaeopter Fusilave', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Archaeopter-Fusilave-2020'),
    ('MC-012', 'Serberys Raiders', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Serberys-Raiders-2020'),
    ('MC-010', 'Pteraxii Skystalkers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Pteraxii-2020'),
    ('MC-003', 'Archaeopter Transvector', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Archaeopter-2020'),
    ('MC-023', 'Tech-Priest Manipulus', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Tech-priest-Manipulus-2020'),
    ('MC-018', 'Skorpius Dunerider', Decimal('52.50'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Skorpius-Dunerider-2019'),
    ('MC-017', 'Skorpius Disintegrator', Decimal('52.50'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Skorpius-Disintegrator-2019'),
    ('MC-014', 'Sicarian Infiltrators', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Sicarian-Infiltrators-2017'),
    ('MC-015', 'Sicarian Ruststalkers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Sicarians-2017'),
    ('59-10', 'Skitarii Rangers', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Skitarii-Rangers-2017'),
    ('59-11', 'Skitarii Vanguard', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Skitarii-Vanguard-2017'),
    ('59-14', 'Ironstrider Ballistarii', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Ironstrider-Ballistarius-2017'),
    ('MC-019', 'Sydonian Dragoon', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Sydonian-Dragoon-2017'),
    ('MC-005', 'Belisarius Cawl', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Belisarius-Cawl-2017'),
    ('MC-022', 'Tech-Priest Enginseer', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Astra-Militarum-Tech-Priest-Enginseer'),
    ('59-20', 'Electropriests (Corpuscarii)', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Ad-Mec-Corpuscarii-Electro-Priests'),
    ('59-06', 'Tech-Priest Dominus', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Ad-Mec-Tech-Priest-Dominus'),
    ('MC-006', 'Fulgurite Electro-Priests', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Ad-Mec-Fulgurite-Electro-Priests'),
    ('59-16', 'Dunecrawler', Decimal('52.50'),
     'https://www.warhammer.com/en-GB/shop/Onager-Dunecrawler'),
    ('MC-007', 'Hastarii', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/adeptus-mechanicus-hastarii-2026'),
    ('MC-024', 'Thulia Ghuld', Decimal('38.50'),
     'https://www.warhammer.com/en-GB/shop/adeptus-mechanicus-thulia-ghuld-2026'),
    ('MC-004', 'Kill Team: Battleclade', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/kill-team-battleclade-2025'),
    ('MC-020', 'Sydonian Skatros', Decimal('26.00'),
     'https://www.warhammer.com/en-GB/shop/adeptus-mechanicus-sydonian-skatros-2023'),
    ('MC-016', 'Skitarii Marshal', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/Adeptus-Mechanicus-Skitarii-Marshall-2021'),
    ('59-18', 'Kataphron Destroyers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Kataphron-Battle-Servitors-Destroyers-2017'),
    ('MC-009', 'Kataphron Breachers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Kataphron-Battle-Servitors-Breachers-2017'),
    ('MC-008', 'Kastelan Robots', Decimal('52.00'),
     'https://www.warhammer.com/en-GB/shop/Kastelan-Robots-2017'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Adeptus Mechanicus. Idempotent.'

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
                f'Seeded {seeded} AdMech GW UK prices. Skipped: {skipped}.'
            )
        )
