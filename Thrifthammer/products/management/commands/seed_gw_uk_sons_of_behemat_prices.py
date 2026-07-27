"""
Seed Games Workshop UK prices for Sons of Behemat.

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
    ('SON-001', 'Kraken-eater Mega-Gargant', Decimal('135.00'),
     'https://www.warhammer.com/en-GB/shop/kraken-eater-mega-gargant-2022'),
    ('SON-002', 'Warstomper Mega-Gargant', Decimal('135.00'),
     'https://www.warhammer.com/en-GB/shop/warstomper-mega-gargant-2022'),
    ('SON-003', 'King Brodd', Decimal('135.00'),
     'https://www.warhammer.com/en-GB/shop/sons-of-behemat-king-brodd-2022'),
    ('SON-004', 'Gatebreaker Mega-Gargant', Decimal('135.00'),
     'https://www.warhammer.com/en-GB/shop/gatebreaker-mega-gargant-2022'),
    ('SON-005', 'Beast-smasher Mega-Gargant', Decimal('135.00'),
     'https://www.warhammer.com/en-GB/shop/beast-smasher-maga-gargant-2022'),
    ('SON-006', 'Mancrusher Gargant', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/sons-of-behemat-mancrusher-gargant-2022'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Sons of Behemat. Idempotent.'

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
                f'Seeded {seeded} Sons of Behemat GW UK prices. Skipped: {skipped}.'
            )
        )
