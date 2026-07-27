"""
Seed Games Workshop UK prices for Forces of the Emperor.

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
    ('FOE-001', 'Rapier Fire Support Battery', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-rapier-fire-support-battery-2026'),
    ('FOE-002', 'Rapier Direct Fire Battery', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-rapier-direct-fire-battery-2026'),
    ('FOE-003', 'Liber Auxilia: Solar Auxilia Army Book', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-liber-auxilia-2025-eng'),
    ('FOE-004', 'Charonite Ogryn Section', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-charonite-ogryn-section-2026'),
    ('FOE-005', 'Sentinel Guard Sodality', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/legio-custodes-sentinel-guard-sodality-2026'),
    ('FOE-006', 'Venatari Sodality', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/legio-custodes-venatari-sodality-2026'),
    ('FOE-007', 'Custodian Guard Sodality', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/legio-custodes-custodian-guard-sodality-2026'),
    ('FOE-008', 'Solar Auxilia: Combat Force', Decimal('105.00'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-solar-auxilia-combat-force-2025'),
    ('FOE-009', 'Malcador Infernus', Decimal('65.00'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-malcador-infernus-2025'),
    ('FOE-010', 'Valdor Tank Destroyer', Decimal('57.00'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-valdor-tank-destroyer-2025'),
    ('FOE-011', 'Arvus Lighter', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-arvus-lighter-2025'),
    ('FOE-012', 'Hermes Light/Veletaris Sentinel Squadron', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-hermes-sentinel-squadron-2024'),
    ('FOE-013', 'Solar Auxilia Basilisk/Medusa', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-basilisk-medusa-2024'),
    ('FOE-014', 'Solar Auxilia Leman Russ Assault Tank', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-leman-russ-assault-tank-2024'),
    ('FOE-015', 'Malcador Heavy Tank', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-malcador-2024'),
    ('FOE-016', 'Veletaris Storm Section', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-velataris-2024'),
    ('FOE-017', 'Aethon Heavy Sentinel', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-aethon-heavy-sentinel-2024'),
    ('FOE-018', 'Solar Auxilia Tactical Command Section', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-tactical-command-section-2024'),
    ('FOE-019', 'Solar Auxilia Lasrifle Section', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-lasrifle-section-2024'),
    ('FOE-020', 'Solar Auxilia Leman Russ Strike/Command Tank', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-leman-russ-strike-tank-2024'),
    ('FOE-021', 'Dracosan Armoured Transport', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/solar-auxilia-dracosan-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Forces of the Emperor. Idempotent.'

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
                f'Seeded {seeded} Forces of the Emperor GW UK prices. Skipped: {skipped}.'
            )
        )
