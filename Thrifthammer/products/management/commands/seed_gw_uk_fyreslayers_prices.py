"""
Seed Games Workshop UK prices for Fyreslayers.

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
    ('FYR-001', 'Spearhead: Fyreslayers', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-fyreslayers-2024'),
    ('FYR-002', 'Auric Flamekeeper', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/fyreslayers-auric-flamekeeper-2022'),
    ('FYR-003', 'Auric Runesmiter on Magmadroth', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/fyreslayers-auric-runesmiter-on-magmadroth-2022'),
    ('FYR-004', 'Gotrek Gurnisson', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Gotrek-Gurnisson-2019'),
    ('FYR-005', 'Magmic Invocations', Decimal('26.00'),
     'https://www.warhammer.com/en-GB/shop/Fyreslayers-Magmic-Invocations-2019'),
    ('FYR-006', 'Doomseeker', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Fyreslayer-Doomseeker-2019'),
    ('FYR-007', 'Grimwrath Berzerker', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Grimwrath-Berserker'),
    ('FYR-008', 'Hearthguard Berzerkers', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Hearthguard-Berzerkers'),
    ('FYR-009', 'Auric Hearthguard', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Auric-Hearthguard'),
    ('FYR-010', 'Vulkite Berzerkers', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Vulkite-Berserkers'),
    ('FYR-011', 'Auric Runemaster', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Auric-Runemaster'),
    ('FYR-012', 'Vulkyn Flameseekers', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/fyreslayers-vulkyn-flameseekers-2025'),
    ('FYR-013', 'Grimhold Exile', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/grimhold-exile-2023'),
    ('FYR-014', 'Magmic Battleforge', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Fyreslayers-Magmic-Battleforge-2019'),
    ('FYR-015', 'Auric Runeson on Magmadroth', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/fyreslayers-auric-runeson-on-magmadroth-2022'),
    ('FYR-016', 'Auric Runefather on Magmadroth', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/fyreslayers-auric-runefather-on-magmadroth-2022'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Fyreslayers. Idempotent.'

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
                f'Seeded {seeded} Fyreslayers GW UK prices. Skipped: {skipped}.'
            )
        )
