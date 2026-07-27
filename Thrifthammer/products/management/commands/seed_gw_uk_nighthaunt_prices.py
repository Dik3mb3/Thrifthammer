"""
Seed Games Workshop UK prices for Nighthaunt.

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
    ('70-10', 'Nighthaunt Spearhead', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-cursed-shacklehorde-2025'),
    ('91-02', 'Nighthaunt Lady Olynder', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Nighthaunt-Lady-Olynder-2018'),
    ('91-06', 'Nighthaunt Hexwraiths', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/Nighthaunt-Hexwraiths-2018'),
    ('91-12', 'Nighthaunt Grimghast Reapers', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Nighthaunt-Grimghast-Reapers-2018'),
    ('91-14', 'Nighthaunt Bladegheist Revenants', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Nighthaunt-Bladegheist-Revenants-2018'),
    ('91-15', 'Nighthaunt Knight of Shrouds', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/nighthaunt-knight-of-the-shrouds-2025'),
    ('91-28', 'Nighthaunt Chainrasps', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Etb-Chainrasp-Hordes-2018'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Nighthaunt. Idempotent.'

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
                f'Seeded {seeded} Nighthaunt GW UK prices. Skipped: {skipped}.'
            )
        )
