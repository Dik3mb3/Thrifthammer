"""
Seed Corvus Belli official-listing links as a US retailer row for Infinity.

The US mirror of seed_corvus_belli_infinity_links (UK). The same official
Corvus Belli product URL (Product.gw_url) that the UK `corvus-belli-uk` row
uses is copied onto a US `corvus-belli` row, so the official listing appears
as a normal retailer row in the Price Comparison table on US pages too.

The row starts with price=None and not_available=True, which renders the
price/discount cells as a clean "-" while the Buy button still links out
(its visibility is driven by url being set). The per-faction
seed_mm_infinity_<faction>_prices commands then fill in the USD price: the
Miniature Market "Retail Price" from the user's spreadsheet, which is the
Corvus Belli US MSRP shown to users (also stored on Product.msrp).

The retailer is named "Corvus Belli US" because Retailer.name is unique and
the UK retailer is already named "Corvus Belli"; is_uk=False keeps it on US
pages and off UK pages.

Covers the WHOLE Infinity category (not just one faction) -- re-run it after
adding a new faction's products and it will seed that faction's links too.

Price, currency, in_stock and not_available are create-only: re-running this
command only refreshes the URL on an existing row, so a redeploy never resets
an MSRP already filled in by a seed_mm_infinity_* command.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_CORVUS_BELLI_US_SLUG = 'corvus-belli'


class Command(BaseCommand):
    help = 'Seed Corvus Belli official-listing links (US row, no price yet) for every Infinity faction. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_CORVUS_BELLI_US_SLUG,
            defaults={
                'name': 'Corvus Belli US',
                'website': 'https://store.corvusbelli.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
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
                defaults={'url': product.gw_url},
                create_defaults={
                    'url': product.gw_url,
                    'price': None,
                    'currency': 'USD',
                    'in_stock': False,
                    'not_available': True,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Corvus Belli US Infinity links. Skipped: {skipped}.'
            )
        )
