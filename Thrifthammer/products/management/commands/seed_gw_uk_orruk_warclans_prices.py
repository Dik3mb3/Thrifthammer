"""
Seed Games Workshop UK prices for Orruk Warclans.

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
    ('70-892', 'Spearhead: Orruk Warclans', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-orruk-warclans-2024'),
    ('70-893', 'Spearhead: Orruk Warclans – Ironjawz Bigmob', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-orruk-warclans-ironjawz-bigmob-2025'),
    ('89-20', 'Orruk Warclans Ironjawz Brutes', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Ironjawz-Orruk-Brutes'),
    ('89-22', 'Orruk Warclans Gutrippaz', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/gutrippaz-2021'),
    ('89-30', 'Orruk Warclans Ardboys', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-ardboy-big-boss-2023'),
    ('OW-001', 'Hobgrot Slittaz', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-hobgrot-slittas-2021'),
    ('OW-002', 'Bossrokk Tower', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-bossrokk-tower-2025'),
    ('OW-003', 'Orruk Warclans Manifestations', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/manifestations-orruk-warclans-2025'),
    ('OW-004', 'Hobgrot Slittaboss', Decimal('23.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-hobgrot-slittaboss-2025'),
    ('OW-005', 'Swampcalla Shaman with Pot-grot', Decimal('26.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-swampcalla-shaman-with-pot-grot-2025'),
    ('OW-006', 'Killaboss with Stab-grot', Decimal('26.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-killa-boss-with-stab-grot-2025'),
    ('OW-007', 'Killaboss on Corpse-rippa Vulcha', Decimal('105.00'),
     'https://www.warhammer.com/en-GB/shop/killaboss-on-corpse-rippa-vulcha-2021'),
    ('OW-008', 'Snatchaboss on Sludgeraker Beast', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/snatchaboss-on-sludgeraker-beast-2021'),
    ('OW-009', 'Gobsprakk, The Mouth of Mork', Decimal('105.00'),
     'https://www.warhammer.com/en-GB/shop/gobsprakk-the-mouth-of-mork-2021'),
    ('OW-010', 'Marshcrawla Sloggoth', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/marshcrawla-sloggoth-2021'),
    ('OW-011', 'Swampboss Skumdrekk', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/swampboss-skumdrekk-2021'),
    ('OW-012', 'Beast-skewer Killbow', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-beast-skewer-killbow-2021'),
    ('OW-013', 'Gordrakk, the Fist of Gork', Decimal('88.00'),
     'https://www.warhammer.com/en-GB/shop/Ironjawz-Orruk-Gordrakk-on-Bigteef'),
    ('OW-014', 'Megaboss on Maw-krusha', Decimal('88.00'),
     'https://www.warhammer.com/en-GB/shop/Ironjawz-Orruk-Maw-Krusha'),
    ('OW-015', 'Gore-gruntas', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/Ironjawz-Orruk-Gore-Gruntas'),
    ('OW-016', 'Warchanter', Decimal('23.00'),
     'https://www.warhammer.com/en-GB/shop/Ironjawz-Orruk-Warchanter'),
    ('OW-017', 'Megaboss', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Ironjawz-Orruk-Megaboss'),
    ('OW-018', 'Monsta Killaz', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-kruleboyz-monsta-killaz-2025'),
    ('OW-019', 'Brute Ragerz', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-brute-ragerz-2023'),
    ('OW-020', 'Weirdbrute Wrekkaz', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-weirdbrute-wrekkaz-2023'),
    ('OW-021', 'Ardboy Big Boss', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-ardboy-big-boss-2023'),
    ('OW-022', 'Breaka-boss on Mirebrute Troggoth', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-breaka-boss-on-mirebrute-troggoth-2021'),
    ('OW-023', 'Destruction Battletome: Orruk Warclans', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-orruk-warclans-hb-2025-eng'),
    ('OW-024', 'Man-Skewer Boltboyz', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/man-skewer-boltboyz-2021'),
    ('OW-025', 'Weirdnob Shaman', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Ironjawz-Orruk-Weirdnob-Shaman'),
    ('OW-026', 'Zoggrok Anvilsmasha', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-zoggrok-anvilsmasha-2023'),
    ('OW-027', 'Maw-grunta Gouger', Decimal('52.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-maw-grunta-gougers-2023'),
    ('OW-028', 'Maw-grunta with Hakkin\' Krew', Decimal('52.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-maw-grunta-with-hakkin-krew-2023'),
    ('OW-029', 'Tuskboss on Maw-grunta', Decimal('52.00'),
     'https://www.warhammer.com/en-GB/shop/orruk-warclans-tuskboss-on-maw-grunta-2023'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Orruk Warclans. Idempotent.'

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
                f'Seeded {seeded} Orruk Warclans GW UK prices. Skipped: {skipped}.'
            )
        )
