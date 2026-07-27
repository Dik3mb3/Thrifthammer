"""
Seed Games Workshop UK prices for Kharadron Overlords.

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
    ('KO-001', 'Spearhead: Kharadron Overlords – Grundstok Trailblazers', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-kharadron-overlords-grundstok-trailblazers-2025'),
    ('KO-002', 'Codewright', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/kharadron-overlords-codewright-2023'),
    ('KO-003', 'Endrinmaster with Dirigible Suit', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Endrinmaster-with-Dirigible-Suit-2020'),
    ('KO-004', 'Arkanaut Ironclad', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Arkanaut-Ironclad-2017'),
    ('KO-005', 'Skywardens', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Skyriggers-2017'),
    ('KO-006', 'Aether-Khemist', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Aether-Khemist-2017'),
    ('KO-007', 'Brokk Grungsson, Lord-Magnate of Barak-Nar', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Brokk-Grungsson-Lord-Magnate-Barak-nar-2017'),
    ('KO-008', 'Aetheric Navigator', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Aetheric-navigator-2017'),
    ('KO-009', 'Endrinriggers', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Endrinriggers-2017'),
    ('KO-010', 'Grundstok Thunderers', Decimal('34.00'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Grundstok-Thunderers-2017'),
    ('KO-011', 'Grundstok Gunhauler', Decimal('38.50'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Grundstok-Gunhauler-2017'),
    ('KO-012', 'Arkanaut Company', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Arkanaut-company-2017'),
    ('KO-013', 'Arkanaut Frigate', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Arkanaut-frigate-2017'),
    ('KO-014', 'Arkanaut Admiral', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Arkanaut-admiral-2017'),
    ('KO-015', 'Zontari Endrin Dock', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/kharadron-overlords-zontari-endrin-dock-2025'),
    ('KO-016', 'Null-Khemist', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/kharadron-overlords-null-khemist-2025'),
    ('KO-017', 'Vongrim Harpoon Crew', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/kharadron-overlords-vongrim-harpoon-crew-2025'),
    ('KO-018', 'Order Battletome: Kharadron Overlords', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-kharadron-overlords-2025-eng'),
    ('KO-019', 'Drekki Flynt', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/kharadron-overlords-drekki-flynt-2022'),
    ('KO-020', 'Endrinmaster with Endrinharness', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Kharadron-Overlords-Endrinmaster-2017'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Kharadron Overlords. Idempotent.'

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
                f'Seeded {seeded} Kharadron Overlords GW UK prices. Skipped: {skipped}.'
            )
        )
