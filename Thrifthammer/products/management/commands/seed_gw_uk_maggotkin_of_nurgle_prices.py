"""
Seed Games Workshop UK prices for Maggotkin of Nurgle.

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
    ('70-832', 'Spearhead: Maggotkin of Nurgle', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-maggotkin-of-nurgle-bubonic-cell-2026'),
    ('83-20', 'Maggotkin of Nurgle Plaguebearers', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Chaos-Daemons-Plaguebearers-of-Nurgle-2018'),
    ('83-22', 'Maggotkin of Nurgle Putrid Blightkings', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-putrid-blightkings-2026'),
    ('MON-001', 'Rotbringer Sorcerer', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-rotbringer-sorcerer-2021'),
    ('MON-002', 'Lord of Afflictions', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Lord-of-Afflictions-2018'),
    ('MON-003', 'Pusgoyle Blightlords', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Nurgle-Rotbringers-Pusgoyle-Blightlords-2018'),
    ('MON-004', 'Lord of Blights', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Nurgle-Rotbringers-Lord-Of-Blights-2018'),
    ('MON-005', 'Morbidex Twiceborn', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/Rotbringers-Morbidex-Twiceborn'),
    ('MON-006', 'Bloab Rotspawned', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/Rotbringers-Bloab-Rotspawned'),
    ('MON-007', 'The Glottkin', Decimal('88.00'),
     'https://www.warhammer.com/en-GB/shop/Rotbringers-The-Glottkin'),
    ('MON-008', 'Orghotts Daemonspew', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/Rotbringers-Orghotts-Daemonspew'),
    ('MON-009', 'Lord of Plagues', Decimal('12.75'),
     'https://www.warhammer.com/en-GB/shop/Rotbringers-Lord-of-Plagues'),
    ('MON-010', 'Gutrot Spume', Decimal('19.00'),
     'https://www.warhammer.com/en-GB/shop/Rotbringers-Gutrot-Spume'),
    ('MON-011', 'The Court of Gelgus Pust', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-court-of-gelgus-pust-2026'),
    ('MON-012', 'Cankerborn', Decimal('31.50'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-cankerborn-2026'),
    ('MON-013', 'Spoilpox Scrivener', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-spoilpox-scrivener-2026'),
    ('MON-014', 'Pox-Wretches', Decimal('36.00'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-pox-wretches-2026'),
    ('MON-015', 'Pestigors', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-pestigors-2026'),
    ('MON-016', 'Festus the Leechlord', Decimal('57.00'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-festus-the-leechlord-2026'),
    ('MON-017', 'Rotmire Creed', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-rotmire-creed-2025'),
    ('MON-018', 'Harbinger of Decay', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/harbinger-of-decay-2023'),
    ('MON-019', 'Chaos Battletome: Maggotkin of Nurgle', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-maggotkin-of-nurgle-2026-eng'),
    ('MON-020', 'Sloven Knights', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-sloven-knights-2026'),
    ('MON-021', 'Rotswords', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/maggotkin-of-nurgle-rotswords-2026'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Maggotkin of Nurgle. Idempotent.'

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
                f'Seeded {seeded} Maggotkin of Nurgle GW UK prices. Skipped: {skipped}.'
            )
        )
