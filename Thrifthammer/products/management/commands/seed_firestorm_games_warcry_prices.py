"""
Seed Firestorm Games UK prices for Warcry.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; games-workshop-uk already holds that
role for this category (see seed_gw_uk_warcry_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warhammer-age-of-sigmar---warcry
3 of 6 catalog SKUs matched, each opened and verified individually
(breadcrumb "Warcry Miniatures" + exact title match) on 2026-09-26.

Not matched:
- WC-002 (Jade Obelisk), WC-005 (Hunters of Huanchi) are not listed on
  Firestorm at all.
- WC-001 (Ydrilan Riverblades) is not sold standalone -- only bundled with
  a second warband in "Warcry: Pyre & Flood (English)" at £80.75. Not
  recorded as WC-001's price since that figure represents two warbands,
  not one; would misrepresent this SKU's actual cost.

All 3 matched are currently out of stock at Firestorm (Backorder/
Unavailable) -- seeded with the real price and in_stock=False, per the
sold-out-listing rule (never clear a real price just because a listing is
temporarily unavailable).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WC-003', Decimal('35.15'), 'https://www.firestormgames.co.uk/warcry-questor-soulsworn-warband?aff=6a4ab07d1c6f9', False),
    ('WC-004', Decimal('37.52'), 'https://www.firestormgames.co.uk/warcry-pyregheists?aff=6a4ab07d1c6f9', False),
    ('WC-006', Decimal('38.95'), 'https://www.firestormgames.co.uk/slaves-to-darkness-chaos-legionnaires?aff=6a4ab07d1c6f9', False),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warcry. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': 'https://www.firestormgames.co.uk/?aff=6a4ab07d1c6f9',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, gbp_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

            cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'GBP'}
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults=cp_defaults,
                create_defaults={**cp_defaults, 'price': gbp_price},
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Warcry Firestorm Games prices. Skipped: {skipped}.'
            )
        )
