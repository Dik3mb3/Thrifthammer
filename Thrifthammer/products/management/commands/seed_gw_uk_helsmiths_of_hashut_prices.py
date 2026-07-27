"""
Seed Games Workshop UK prices for Helsmiths of Hashut.

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
    ('HOH-001', 'Spearhead: Helsmiths of Hashut – Helforge Host', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-hellsmiths-of-hashut-helforge-host-2026'),
    ('HOH-002', 'Urak Taar the First Daemonsmith', Decimal('98.00'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-urak-taar-the-first-daemonsmith-2025'),
    ('HOH-003', 'Deathshrieker Rocket Battery', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-deathshrieker-rocket-battery-2025'),
    ('HOH-004', 'Dominator Engine', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-dominator-engine-2025'),
    ('HOH-005', 'Hobgrot Vandalz', Decimal('38.50'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-hobgrot-vandalz-2025'),
    ('HOH-006', 'Infernal Cohort', Decimal('34.00'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-infernal-cohort-2025'),
    ('HOH-007', 'Infernal Razers', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-infernal-razers-2025'),
    ('HOH-008', 'War Despot', Decimal('24.00'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-war-despot-2025'),
    ('HOH-009', 'Chaos Battletome: Helsmiths of Hashut', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-helsmiths-of-hashut-2025-eng'),
    ('HOH-010', 'Bull Centaurs', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-bull-centaurs-2025'),
    ('HOH-011', 'Daemonsmith', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/helsmiths-of-hashut-daemonsmith-2025'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Helsmiths of Hashut. Idempotent.'

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
                f'Seeded {seeded} Helsmiths of Hashut GW UK prices. Skipped: {skipped}.'
            )
        )
