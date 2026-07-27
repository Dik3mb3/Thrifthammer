"""
Seed Games Workshop UK prices for Blades of Khorne.

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
    ('70-17', 'Spearhead: Blades of Khorne', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-blades-of-khorne-fangs-of-the-blood-god-2025'),
    ('83-30', 'Blades of Khorne Bloodreavers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Khorne-Bloodreavers'),
    ('97-08', 'Blades of Khorne Bloodletters', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Daemons-Of-Khorne-Bloodletters-40k-2017'),
    ('BOK-001', 'Realmgore Ritualist', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/blades-of-khorne-realmgore-ritualist-2023'),
    ('BOK-002', 'Judgements of Khorne', Decimal('26.00'),
     'https://www.warhammer.com/en-GB/shop/Judgements-of-Khorne-2019'),
    ('BOK-003', 'Skullreapers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Khorne-Bloodbound-Skullreapers'),
    ('BOK-004', 'Mighty Skullcrushers', Decimal('65.00'),
     'https://www.warhammer.com/en-GB/shop/Khorne-Bloodbound-Mighty-Skullcrushers'),
    ('BOK-005', 'Wrathmongers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Khorne-Bloodbound-Wrathmongers'),
    ('BOK-006', 'Blood Warriors', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/Khorne-Bloodbound-Blood-Warriors'),
    ('BOK-007', 'Slaughterpriest', Decimal('23.00'),
     'https://www.warhammer.com/en-GB/shop/Khorne-Bloodbound-Slaughterpriest'),
    ('BOK-008', 'Deathbringer', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/blades-of-khorne-deathbringer-2025'),
    ('BOK-009', 'Chaos Battletome: Blades of Khorne', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-blades-of-khorne-2025-eng'),
    ('BOK-010', 'Skullgrinder', Decimal('23.00'),
     'https://www.warhammer.com/en-GB/shop/Khorne-Bloodbound-Skullgrinder'),
    ('BOK-011', 'Claws of Karanak', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/blades-of-khorne-claws-of-karanak-2025'),
    ('BOK-012', 'Goreblade Warband', Decimal('62.00'),
     'https://www.warhammer.com/en-GB/shop/blades-of-khorne-goreblade-warband-2025'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Blades of Khorne. Idempotent.'

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
                f'Seeded {seeded} Blades of Khorne GW UK prices. Skipped: {skipped}.'
            )
        )
