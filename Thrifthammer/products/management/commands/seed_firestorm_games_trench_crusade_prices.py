"""
Seed Firestorm Games UK prices for Trench Crusade.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe.

SPECIAL CASE (explicit one-time user instruction, does not apply to any
other Firestorm category this session): unlike every other
seed_firestorm_games_*_prices command, this one DOES overwrite
product.msrp_gbp, using Firestorm's RRP (the higher, struck-through
price on each listing). Trench Crusade is not a Games Workshop product,
so games-workshop-uk never populates msrp_gbp for TC-XXX SKUs -- the
existing value was a EUR-to-GBP conversion estimate from the
manufacturer's own site (set in seed_trench_crusade_uk_prices.py).
Firestorm's real GBP RRP, as an actual UK retailer, is a more accurate
reference price, so the user asked for it to replace the converted
estimate here. Do not extend this msrp_gbp-overwrite behavior to any
other Firestorm command without an explicit new instruction.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). The CurrentPrice row always uses the lower (sale)
price. msrp_gbp uses the RRP (see special case above).

https://www.firestormgames.co.uk/wargames-miniatures/trench-crusade-
4/4 active DB Trench Crusade SKUs matched -- small catalog, no gaps.
Excluded: "Trench Crusade - Prussian Yeomen" (£23.74/£24.99, pre-order)
has no DB counterpart -- not one of our 4 tracked SKUs.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, label, sale_price_gbp, rrp_gbp, url)
_PRICES = [
    ('TC-001', 'Trench Crusade: Carcass Front', Decimal('90.00'), Decimal('100.00'),
     'https://www.firestormgames.co.uk/trench-crusade:-carcass-front?aff=6a4ab07d1c6f9'),
    ('TC-002', 'Trench Crusade - Prussian Stosstrupen Warband', Decimal('33.24'), Decimal('34.99'),
     'https://www.firestormgames.co.uk/trench-crusade---prussian-stosstrupen-warband?aff=6a4ab07d1c6f9'),
    ('TC-003', 'Trench Crusade - Prussian Stosstruppen', Decimal('23.74'), Decimal('24.99'),
     'https://www.firestormgames.co.uk/trench-crusade---prussian-stosstruppen?aff=6a4ab07d1c6f9'),
    ('TC-004', 'Trench Crusade - Sniper Priests', Decimal('18.99'), Decimal('19.99'),
     'https://www.firestormgames.co.uk/trench-crusade---sniper-priests?aff=6a4ab07d1c6f9'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Trench Crusade and refresh msrp_gbp from Firestorm RRP. Idempotent.'

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
        for sku, label, sale_price, rrp, url in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
                skipped += 1
                continue

            for product in products:
                if product.msrp_gbp != rrp:
                    product.msrp_gbp = rrp
                    product.save(update_fields=['msrp_gbp'])

                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': sale_price,
                        'currency': 'GBP',
                        'url': url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Firestorm Games Trench Crusade prices. Skipped: {skipped}.'
            )
        )
