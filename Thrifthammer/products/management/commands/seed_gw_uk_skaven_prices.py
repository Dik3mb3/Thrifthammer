"""
Seed Games Workshop UK prices for Skaven.

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
    ('70-901', 'Spearhead: Skaven', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-skaven-2024'),
    ('90-10', 'Skaven Clanrats', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/skaven-clanrats-2024'),
    ('90-12', 'Skaven Plague Monks', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Pestilens-Plague-Monks'),
    ('90-17', 'Skaven Stormfiends', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Skaven-Stormfiends'),
    ('SK-001', 'Chaos Battletome: Skaven', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-skaven-2024-eng'),
    ('SK-002', 'Spearhead: City of Ash', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/city-of-ash-gaming-pack-2026-eng'),
    ('SK-003', 'Skaven Deathmaster', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-deathmaster-2022'),
    ('SK-004', 'Skaven Warlock Bombardier', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Skaven-Warlock-Bombardier-2020'),
    ('SK-005', 'Skaven Endless Spells: Skaven', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Skaven-2019'),
    ('SK-006', 'Skaven Gnawholes', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Skaven-Gnawhole-2019'),
    ('SK-007', 'Skaven Screaming Bell', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Screaming-Bell-2015'),
    ('SK-008', 'Skaven Plague Priest on Plague Furnace', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Pestilens-Plague-Furnace'),
    ('SK-009', 'Skaven Clawlord', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/Skaven-Warlord-2014'),
    ('SK-010', 'Skaven Doomwheel', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Skaven-Doomwheel'),
    ('SK-012', 'Skaven Thanquol and Boneripper', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-thanquol-on-boneripper-2024'),
    ('SK-013', 'Skaven Plaguepack', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-plaguepack-2024'),
    ('SK-014', 'Skaven Clawlord on Gnaw-beast', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-clawlord-on-gnaw-beast-2024'),
    ('SK-015', 'Skaven Rat Ogors', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-rat-ogors-2024'),
    ('SK-016', 'Skaven Arch-Warlock', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-arch-warlock-2024'),
    ('SK-017', 'Skaven Ratling Warpblaster', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/skaven-ratling-warpblaster-2024'),
    ('SK-018', 'Skaven Warplock Jezzails', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/skaven-warplock-jezzails-2024'),
    ('SK-019', 'Skaven Vizzik Skour, Prophet of the Horned Rat', Decimal('98.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-vizzik-skour-prophet-horned-rat-2024'),
    ('SK-020', 'Skaven Brood Terror', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/skaven-brood-terror-2024'),
    ('SK-021', 'Skaven Warlock Galvaneer', Decimal('23.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-warlock-galvaneer-2024'),
    ('SK-022', 'Skaven Acolyte Globadiers', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/skaven-acolyte-globadiers-2024'),
    ('SK-023', 'Skaven Warp-Grinder', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/skaven-warp-grinder-2024'),
    ('SK-024', 'Skaven Warpspark Weapon Battery', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/skaven-warpspark-weapon-battery-2024'),
    ('SK-025', 'Skaven Doom-Flayers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-doom-flayers-2024'),
    ('SK-026', 'Skaven Master Moulder', Decimal('23.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-master-moulder-2024'),
    ('SK-027', 'Skaven Hell Pit Abomination', Decimal('44.00'),
     'https://www.warhammer.com/en-GB/shop/Skaven-Hell-Pit-Abomination'),
    ('SK-028', 'Skaven Verminlord Warpseer', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Warpseer-2018'),
    ('SK-029', 'Skaven Lord Skreech Verminking', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Lord-Skreech-2018'),
    ('SK-030', 'Skaven Verminlord Warbringer', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Warbringer-2018'),
    ('SK-031', 'Skaven Verminlord Deceiver', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Deciever-2018'),
    ('SK-032', 'Skaven Verminlord Corruptor', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/Skaven-Pestilens-Verminlord-Corruptor'),
    ('SK-033', 'Skaven Warp Lightning Cannon', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Skaven-Warp-Lightning-Cannon-2015'),
    ('SK-034', 'Skaven Plagueclaw', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Pestilens-Plague-Claw-Catapult'),
    ('SK-035', 'Skaven Krittok Foulblade', Decimal('26.00'),
     'https://www.warhammer.com/en-GB/shop/skaven-krittok-foulblade-2024'),
    ('SK-036', 'Skaven Stormvermin', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/skaven-stormvermin-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Skaven. Idempotent.'

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
                f'Seeded {seeded} Skaven GW UK prices. Skipped: {skipped}.'
            )
        )
