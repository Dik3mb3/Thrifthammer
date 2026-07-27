"""
Seed Games Workshop UK prices for Sylvaneth.

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
    ('SYL-001', 'Battleforce: Sylvaneth – Strongroot Grove', Decimal('155.00'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-strongroot-grove-2026'),
    ('SYL-002', 'Spearhead: Sylvaneth – Spitewing Flight', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-spitewing-flight-2026'),
    ('SYL-003', 'The Twisted Branch', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-the-twisted-branch-2026'),
    ('SYL-004', 'Twistweald', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/warcry-twistweald-2024'),
    ('SYL-005', 'The Lady of Vines', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-lady-of-vines-2022'),
    ('SYL-006', 'Gossamid Archers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-gossamid-archers-2022'),
    ('SYL-007', 'Arch-Revenant', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Druanti-The-Arch-Revenant-2020'),
    ('SYL-008', 'Awakened Wyldwood', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Awakened-Wyldwood-2019'),
    ('SYL-009', 'Endless Spells: Sylvaneth', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Sylvaneth-2019'),
    ('SYL-010', 'Kurnoth Hunters', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Kurnoth-Hunters'),
    ('SYL-011', 'Alarielle the Everqueen', Decimal('105.00'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Alarielle-the-Everqueen'),
    ('SYL-012', 'Dryads', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Dryads'),
    ('SYL-013', 'Branchwych', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-branchwych-2026'),
    ('SYL-014', 'Grove Guardian', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-grove-guardian-2026'),
    ('SYL-015', 'Order Battletome: Sylvaneth', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-sylvaneth-2026-eng'),
    ('SYL-016', 'Revenant Seekers', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-revenant-seekers-2022'),
    ('SYL-017', 'Spiterider Lancers', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-spiterider-lancers-2022'),
    ('SYL-018', 'Warsong Revenant', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Warsong-Revenant-2021'),
    ('SYL-019', 'Spite-Revenants', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Spite-Revenants'),
    ('SYL-020', 'Drycha Hamadreth', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Drycha-Hamadreth'),
    ('SYL-021', 'Tree-Revenants', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Tree-Revenants'),
    ('SYL-022', 'Spirit of Durthu', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Treelord-Durthu'),
    ('SYL-023', 'Treelord Ancient', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Treelord-Ancient'),
    ('SYL-024', 'Treelord', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Sylvaneth-Treelord'),
    ('SYL-025', 'Belthanos, First Thorn of Kurnoth', Decimal('69.50'),
     'https://www.warhammer.com/en-GB/shop/sylvaneth-belthanos-first-thorn-of-kurnoth-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Sylvaneth. Idempotent.'

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
                f'Seeded {seeded} Sylvaneth GW UK prices. Skipped: {skipped}.'
            )
        )
