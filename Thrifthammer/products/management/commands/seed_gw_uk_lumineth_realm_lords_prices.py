"""
Seed Games Workshop UK prices for Lumineth Realm-lords.

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
    ('70-11', 'Spearhead: Lumineth Realm-lords', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-hurakan-vanguard-2026'),
    ('87-08', 'Lumineth Realm-lords Alarith Stoneguard', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Relam-lords-Alarith-Stoneguard-2020'),
    ('87-10', 'Lumineth Realm-lords Vanari Auralan Wardens', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Vanari-Auralan-Wardens-2020'),
    ('LRL-001', 'Alarith Spirit of the Mountain', Decimal('80.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Sprit-of-the-Mountain-2020'),
    ('LRL-002', 'Alarith Stonemage', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Alarith-Stonemage-2020'),
    ('LRL-003', 'Archmage Teclis and Celennar, Spirit of Hysh', Decimal('118.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Archmage-Teclis-2020'),
    ('LRL-004', 'Avalenor, the Stoneheart King', Decimal('80.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Avalenor-The-Stoneheart-King-2020'),
    ('LRL-005', 'Ellania and Ellathor, Eclipsian Warsages', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Ellania-And-Ellathor-2021'),
    ('LRL-006', 'Endless Spells: Lumineth Realm-lords', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Lumineth-Realm-lords-2020'),
    ('LRL-007', 'Hurakan Spirit of the Wind', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Hurakan-Spirit-of-the-Wind-2021'),
    ('LRL-008', 'Hurakan Windchargers', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Hurakan-Windchargers-2021'),
    ('LRL-009', 'Hurakan Windmage', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Hurakan-Windmage-2021'),
    ('LRL-010', 'Lyrior Uthralle, Warden of Ymetrica', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Lyrior-Uthralle-2021'),
    ('LRL-011', 'Order Battletome: Lumineth Realm-lords', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-lumineth-realmlords-2026-eng'),
    ('LRL-012', 'Scinari Calligrave', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Scinari-Calligrave-2021'),
    ('LRL-013', 'Scinari Cathallar', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Scinari-Cathallar-2020'),
    ('LRL-014', 'Scinari Enlightener', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/lumineth-scinari-enlightener-2022'),
    ('LRL-015', 'Scinari Loreseeker', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Scinari-Loreseeker-2021'),
    ('LRL-016', 'Sevireth, Lord of the Seventh Wind', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Sevireth-Lord-of-the-Seventh-Wind-2021'),
    ('LRL-017', 'Shrine Luminor', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Shrine-Luminor-2021'),
    ('LRL-018', 'The Light of Eltharion', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-The-Light-of-Eltharion-2020'),
    ('LRL-019', 'Vanari Auralan Sentinels', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Vanari-Auralan-Sentinels-2020'),
    ('LRL-020', 'Vanari Bannerblade', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Vanari-Bannerblade-2021'),
    ('LRL-021', 'Vanari Bladelords', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Vanari-Bladelords-2021'),
    ('LRL-022', 'Vanari Dawnriders', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Lumineth-Realm-lords-Vanari-Dawnriders-2020'),
    ('LRL-023', 'Vanari Lord Regent (2021)', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Vanari-Lord-Regent-2021'),
    ('LRL-025', 'Vanari Starshard Ballista', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Vanari-Starshard-Ballista-2021'),
    ('LRL-026', 'Warcry Ydrilan Riverblades', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/warcry-ydrilan-riverblades-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Lumineth Realm-lords. Idempotent.'

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
                f'Seeded {seeded} Lumineth Realm-lords GW UK prices. Skipped: {skipped}.'
            )
        )
