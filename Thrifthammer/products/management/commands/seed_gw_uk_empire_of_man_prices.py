"""
Seed Games Workshop UK prices for Empire of Man.

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
    ('EOM-001', 'Arcane Journal: Empire of Man', Decimal('16.50'),
     'https://www.warhammer.com/en-GB/shop/arcane-journal-empire-of-man-sb-2024-eng'),
    ('EOM-002', 'Empire Steam Tank', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-steam-tank-2025'),
    ('EOM-003', 'Helblaster Volley Gun & Helstorm Rocket Battery', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-helblaster-volley-gun-and-helstorm-rocket-battery-2025'),
    ('EOM-004', 'Empire Greatswords', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-greatswords-2025'),
    ('EOM-005', 'Flagellants', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-flagellants-2025'),
    ('EOM-006', 'State Missile Troops', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-state-missile-troops-2025'),
    ('EOM-007', 'Empire State Troops', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-empire-state-troops-2025'),
    ('EOM-008', 'Empire Engineer with Hochland Long Rifle', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-engineer-with-hochland-long-rifle-2025'),
    ('EOM-009', 'Cannons & Mortars', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-cannons-and-mortars-2024'),
    ('EOM-010', 'Demigryph Knights', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-demigryph-knights-2024'),
    ('EOM-011', 'Empire Pistoliers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-empire-pistoliers-2024'),
    ('EOM-012', 'Empire Knights', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-empire-knights-2024'),
    ('EOM-013', 'Free Company Militia', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-free-company-militia-2024'),
    ('EOM-014', 'General of the Empire on Imperial Griffon', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/general-of-the-empire-on-imperial-griffon-2024'),
    ('EOM-015', 'Commanders of the Empire', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-commanders-of-the-empire-2024'),
    ('EOM-016', 'Empire Archers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-archers-2025'),
    ('EOM-017', 'Captain of the Empire', Decimal('19.00'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-captain-of-the-empire-2025'),
    ('EOM-018', 'War Altar of Sigmar', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/empire-of-man-war-altar-of-sigmar-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Empire of Man. Idempotent.'

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
                f'Seeded {seeded} Empire of Man GW UK prices. Skipped: {skipped}.'
            )
        )
