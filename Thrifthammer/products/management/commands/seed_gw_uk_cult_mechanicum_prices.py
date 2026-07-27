"""
Seed Games Workshop UK prices for Cult Mechanicum.

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
    ('CM-001', 'Mechanicum: Combat Force', Decimal('105.00'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-mechanicum-combat-force-2025'),
    ('CM-002', 'Skitarii Battle-Pilgrym Marshal', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/skitarii-battle-pilgrym-marshal-2026'),
    ('CM-003', 'Vultarax Stratos-Automata', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-vultarax-stratos-automata-2026'),
    ('CM-004', 'Skitarii Battle-Pilgrym Corpus', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-skitarii-battle-pilgrym-corpus-2026'),
    ('CM-005', 'Ursarax Cohort', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-ursarax-cohort-2025'),
    ('CM-006', 'Krios Battle Tank/Venator', Decimal('47.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-krios-battle-tank-2025'),
    ('CM-007', 'Karacnos Assault Tank', Decimal('67.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-karacnos-assault-tank-2025'),
    ('CM-008', 'Thanatar Calix Siege-automata', Decimal('64.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-thanatar-calix-siege-automata-2025'),
    ('CM-009', 'Archmagos Prime', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-archmagos-prime-2024'),
    ('CM-010', 'Thallax Cohort', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-thallax-cohort-2024'),
    ('CM-011', 'Triaros Armoured Conveyor', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-triaros-armoured-conveyor-2024'),
    ('CM-012', 'Tech-thralls Covenant', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-tech-thralls-covenant-2024'),
    ('CM-013', 'Castellax Battle-automata Maniple', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-castellax-battle-automata-maniple-2024'),
    ('CM-014', 'Age of Darkness Armiger Helverins', Decimal('60.00'),
     'https://www.warhammer.com/en-GB/shop/questoris-households-armiger-helverin-talon-2022'),
    ('CM-015', 'Age of Darkness Armiger Warglaives', Decimal('60.00'),
     'https://www.warhammer.com/en-GB/shop/questoris-households-armiger-warglaive-talon-2022'),
    ('CM-016', 'Age of Darkness Knight Questoris', Decimal('115.00'),
     'https://www.warhammer.com/en-GB/shop/questoris-households-knight-questoris-2022'),
    ('CM-017', 'Myrmidon Destructor Host', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-myrmidon-destructor-host-2026'),
    ('CM-018', 'Thanatar Cavas Siege-automata', Decimal('64.50'),
     'https://www.warhammer.com/en-GB/shop/mechanicum-thanatar-cavas-siege-automata-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Cult Mechanicum. Idempotent.'

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
                f'Seeded {seeded} Cult Mechanicum GW UK prices. Skipped: {skipped}.'
            )
        )
