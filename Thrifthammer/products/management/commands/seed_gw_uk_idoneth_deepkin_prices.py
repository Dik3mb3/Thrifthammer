"""
Seed Games Workshop UK prices for Idoneth Deepkin.

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
    ('IDK-001', 'Spearhead: Idoneth Deepkin – Akhelian Tide Guard', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-idoneth-deepkin-akhelian-tide-guard-2025'),
    ('IDK-002', 'Akhelian Thrallmaster', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/idoneth-deepkin-akhelian-thrallmaster-2022'),
    ('IDK-003', 'Akhelian Ishlaen Guard', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Idoneth-Deepkin-Akhelian-Ishlaen-Guard-2018'),
    ('IDK-004', 'Akhelian Leviadon', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/Idoneth-Deepkin-Akhelian-Leviadon-2018'),
    ('IDK-005', 'Akhelian Morrsarr Guard', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Idoneth-Deepkin-Akhelian-Guard-2018'),
    ('IDK-006', 'Akhelian Allopex', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Idoneth-Deepkin-Akhelian-Allopex-2018'),
    ('IDK-007', 'Isharann Tidecaster', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Idoneth-Deepkin-Isharann-Tidecaster-2018'),
    ('IDK-008', 'Akhelian King', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Akhelian-King-2018'),
    ('IDK-009', 'Namarti Reavers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Namarti-Reavers-2018'),
    ('IDK-010', 'Volturnos, High King of the Deep', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Volturnos-High-King-Of-The-Deep-2018'),
    ('IDK-011', 'Eidolon of Mathlann – Aspect of the Sea', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/Eidolon-Aspect-of-the-sea-2018'),
    ('IDK-012', 'Gloomtide Shipwreck', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Etheric-Vortex-Gloomtide-Shipwreck-2018'),
    ('IDK-013', 'Namarti Thralls', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Namarti-Thralls-2018'),
    ('IDK-014', 'Lotann, Warden of the Soul Ledgers', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Lotann-Warden-Of-The-Soul-Ledgers-2018'),
    ('IDK-015', 'Eidolon of Mathlann – Aspect of the Storm', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/Eidolon-Of-Mathlann-2018'),
    ('IDK-016', 'Idoneth Deepkin Manifestations', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/idoneth-deepkin-manifestations-2025'),
    ('IDK-017', 'Mathaela, Oracle of the Abyss', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/idoneth-deepkin-mathaela-oracle-of-the-abyss-2025'),
    ('IDK-018', 'Ikon of the Sea/Storm', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/idoneth-deepkin-ikon-of-the-sea-2025'),
    ('IDK-019', 'Order Battletome: Idoneth Deepkin', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-idoneth-deepkin-2025-eng'),
    ('IDK-020', 'Isharann Soulrender', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Idoneth-Deepkin-Isharann-Soulrender-2018'),
    ('IDK-021', 'Isharann Soulscryer', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/idoneth-deepkin-isharann-soulscryer-2025'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Idoneth Deepkin. Idempotent.'

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
                f'Seeded {seeded} Idoneth Deepkin GW UK prices. Skipped: {skipped}.'
            )
        )
