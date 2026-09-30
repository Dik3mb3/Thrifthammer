"""
Seed Corvus Belli official-listing links as a retailer row for Infinity.

Corvus Belli (the publisher) only shows prices in EUR, which this catalog
doesn't track as a currency -- MSRP for Infinity will come from Firestorm
Games UK in a later phase of this rollout. Until then, this command still
creates a real CurrentPrice row per product (url set, price=None,
not_available=True) so the official listing appears as a normal retailer
row in the Price Comparison table -- same as every other category -- rather
than relying solely on the page's separate "View Official Listing" button.

not_available=True (not a missing row) is what keeps the price/discount
cells rendering as a clean "-" instead of a blank/garbled price, while the
Buy button still links out correctly, since that button's visibility is
driven by url being set, not by not_available.

Covers the WHOLE Infinity category (not just one faction) -- Product.gw_url
is written by each faction's own populate_infinity_<faction>_products.py
command (PanOceania, Yu Jing, ...), and this command just picks up every
Infinity product that has one, regardless of faction. Re-run it after
adding a new faction's products and it will seed that faction's links too,
without needing its own copy of this command.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_CORVUS_BELLI_SLUG = 'corvus-belli-uk'


class Command(BaseCommand):
    help = 'Seed Corvus Belli official-listing links (no price yet) for every Infinity faction. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_CORVUS_BELLI_SLUG,
            defaults={
                'name': 'Corvus Belli',
                'website': 'https://store.corvusbelli.com',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for product in Product.objects.filter(category__slug='infinity'):
            if not product.gw_url:
                self.stderr.write(f'SKIP — {product.gw_sku} has no gw_url')
                skipped += 1
                continue

            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'url': product.gw_url,
                    'price': None,
                    'in_stock': False,
                    'not_available': True,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Corvus Belli Infinity links. Skipped: {skipped}.'
            )
        )
