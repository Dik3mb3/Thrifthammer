"""
Seed Games Workshop UK prices for Seraphon.

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
    ('SR-001', 'Seraphon Aggradon Lancers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-aggradon-lancers-2023'),
    ('SR-002', 'Seraphon Bastiladon', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Bastiladon'),
    ('SR-003', 'Seraphon Engine of the Gods', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Engine-of-the-Gods'),
    ('SR-004', 'Seraphon Hunters of Huanchi', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-hunters-of-huanchi-2025'),
    ('SR-005', 'Seraphon Kroxigor', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-kroxigor-2023'),
    ('SR-006', 'Seraphon Kroxigor Warspawned', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-kroxigor-warspawned-2023'),
    ('SR-007', 'Seraphon Lord Kroak', Decimal('88.00'),
     'https://www.warhammer.com/en-GB/shop/Lord-Kroak-2021'),
    ('SR-008', 'Seraphon Raptadon Chargers', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/seraphon-raptadon-chargers-2023'),
    ('SR-009', 'Seraphon Raptadon Hunters', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/seraphon-raptadon-hunters-2023'),
    ('SR-010', 'Seraphon Realmshaper Engine', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Realmshaper-Engine-2020'),
    ('SR-011', 'Seraphon Ripperdactyl Riders', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Ripperdactyl-Riders'),
    ('SR-012', 'Seraphon Saurus Astrolith Bearer', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-saurus-astrolith-bearer-2023'),
    ('SR-013', 'Seraphon Saurus Guard', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Saurus-Guard'),
    ('SR-014', 'Seraphon Saurus Oldblood', Decimal('12.75'),
     'https://www.warhammer.com/en-GB/shop/Lizardmen-Saurus-Oldblood'),
    ('SR-015', 'Seraphon Saurus Oldblood on Carnosaur', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Saurus-Oldblood-on-Carnosaur'),
    ('SR-016', 'Seraphon Saurus Scar-Veteran on Aggradon', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-saurus-scar-veteran-on-aggradon-2023'),
    ('SR-017', 'Seraphon Saurus Scar-Veteran on Carnosaur', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Saurus-Scar-Veteran-on-Carnosaur'),
    ('SR-018', 'Seraphon Saurus Warriors', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-saurus-warriors-2023'),
    ('SR-019', 'Seraphon Skink Oracle on Troglodon', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Troglodons'),
    ('SR-020', 'Seraphon Skink Starpriest', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Skink-Starpriest'),
    ('SR-021', 'Seraphon Skink Starseer', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-skink-starseer-2023'),
    ('SR-022', 'Seraphon Skinks', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Skinks'),
    ('SR-023', 'Seraphon Slann Starmaster', Decimal('57.00'),
     'https://www.warhammer.com/en-GB/shop/seraphon-slann-starmaster-2023'),
    ('SR-024', 'Seraphon Spawn of Chotec', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/seraphon-spawn-of-chotec-2023'),
    ('SR-025', 'Seraphon Stegadon', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Stegadon'),
    ('SR-026', 'Seraphon Stegadon Chief', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/stegadon-chief-2023'),
    ('SR-027', 'Seraphon Terradon Riders', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Seraphon-Terradon-Riders'),
    ('SR-028', 'Spearhead: Seraphon – Sunblooded Prowlers', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-seraphon-sunblooded-prowlers-2025'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Seraphon. Idempotent.'

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
                f'Seeded {seeded} Seraphon GW UK prices. Skipped: {skipped}.'
            )
        )
