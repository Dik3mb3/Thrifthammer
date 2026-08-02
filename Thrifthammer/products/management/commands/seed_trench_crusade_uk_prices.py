"""
Seed Trench Crusade UK prices.

Onboards a brand-new UK retailer (trenchcrusade.com) per Task B of the UK
retailer prompt. Mirrors the US `trench-crusade` retailer pattern used in
populate_trench_crusade_products.py (direct manufacturer, no GW row), but
as a genuinely separate UK-flagged Retailer row (US Trench Crusade has
is_uk=False).

Trench Crusade has no dedicated UK storefront yet -- the manufacturer's own
site prices EU/UK orders in EUR (confirmed via a user-provided screenshot of
trenchcrusade.com). Rather than displaying EUR on an otherwise all-GBP UK
site, prices below are the EUR listing converted to GBP at the EUR/GBP rate
on 2026-07-29 (~0.857, per Wise/XE) and rounded to the nearest ".99" retail
price, matching the rest of the UK catalog:
    TC-001  EUR 119.99 -> GBP 102.99
    TC-002  EUR  39.99 -> GBP  33.99
    TC-003  EUR  29.99 -> GBP  25.99
    TC-004  EUR  22.99 -> GBP  19.99
product.msrp_gbp is set to the same converted price (mirrors the Asmodee UK
pattern) so the UK site has a reference price to compute "% off" discount
badges against -- without it, gw_ref_price has nothing to fall back to and
no discount badge can render, even when eBay UK undercuts this price.

Run once on Railway startup via Procfile. Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_TRENCH_CRUSADE_UK_SLUG = 'trench-crusade-uk'

# (sku, label, gbp_price, url)
_PRICES = [
    ('TC-001', 'Trench Crusade Carcass Front', Decimal('102.99'),
     'https://www.trenchcrusade.com/product/pre-order-carcass-front/'),
    ('TC-002', 'Prussian Stosstruppen Warband', Decimal('33.99'),
     'https://www.trenchcrusade.com/product/prussian-stosstruppen-warband/'),
    ('TC-003', 'Prussian Stosstruppen', Decimal('25.99'),
     'https://www.trenchcrusade.com/product/prussian-stosstruppen/'),
    ('TC-004', 'New Antioch Sniper Priests', Decimal('19.99'),
     'https://www.trenchcrusade.com/product/new-antioch-sniper-priests/'),
]


class Command(BaseCommand):
    help = 'Seed Trench Crusade UK (GBP) prices and URLs. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_TRENCH_CRUSADE_UK_SLUG,
            defaults={
                'name': 'Trench Crusade UK',
                'website': 'https://www.trenchcrusade.com',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for sku, label, gbp_price, url in _PRICES:
            try:
                product = Product.objects.get(gw_sku=sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
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
                    'currency': 'GBP',
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Trench Crusade UK (GBP) prices. Skipped: {skipped}.'
            )
        )
