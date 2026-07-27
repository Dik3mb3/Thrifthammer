"""
Seed Games Workshop UK prices for Disciples of Tzeentch.

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
    ('70-839', 'Spearhead: Disciples of Tzeentch – Tzaangor Warflock', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-tzaangor-warflock-2026'),
    ('83-40', 'Disciples of Tzeentch Tzaangors', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Tzaangors-AoS'),
    ('97-11', 'Disciples of Tzeentch Pink Horrors', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/pink-horrors-2018'),
    ('DOT-001', 'Warcry: The Jade Obelisk', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/disciples-of-tzeentch-the-jade-obelisk-2025'),
    ('DOT-002', 'Curseling, Eye of Tzeentch', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/tzeentch-curseling-eye-of-tzeentch-2022'),
    ('DOT-003', 'Tzaangor Enlightened', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Tzaangor-Enlightened'),
    ('DOT-004', 'Tzaangor Shaman', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Tzaangor-Shaman'),
    ('DOT-005', 'Magister', Decimal('12.75'),
     'https://www.warhammer.com/en-GB/shop/Tzeentch-Arcanites-Magister'),
    ('DOT-006', 'Kairic Acolytes', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Kairic-Acolytes'),
    ('DOT-007', 'Ogroid Thaumaturge', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Ogrid-Thaumaturge'),
    ('DOT-008', 'Magister on Disc of Tzeentch', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/disciples-of-tzeentch-magister-on-disc-of-tzeentch-2026'),
    ('DOT-009', 'Fatemaster', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/disciples-of-tzeentch-fatemaster-2026'),
    ('DOT-010', 'Chaos Battletome: Disciples of Tzeentch', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-disciples-of-tzeentch-2026-eng'),
    ('DOT-011', 'Endless Spells: Disciples of Tzeentch', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Disciples-Of-Tzeentch-2020'),
    ('DOT-012', 'Argent Shards', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/disciples-of-tzeentch-argent-shards-2026'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Disciples of Tzeentch. Idempotent.'

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
                f'Seeded {seeded} Disciples of Tzeentch GW UK prices. Skipped: {skipped}.'
            )
        )
