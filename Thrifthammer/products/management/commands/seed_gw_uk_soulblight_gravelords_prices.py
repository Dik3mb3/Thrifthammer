"""
Seed Games Workshop UK prices for Soulblight Gravelords.

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
    ('SG-001', 'Soulblight Gravelords – The Summons', Decimal('28.00'),
     'https://www.warhammer.com/en-GB/shop/warhammer-plus-soulblight-gravelords-the-summons-2025-year-5'),
    ('SG-003', 'Spearhead: Soulblight Gravelords – Deathrattle Tomb Host', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-soulblight-gravelords-deathrattle-tomb-host-2025'),
    ('SG-004', 'Ivya Volga, the Outcast', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-ivya-volga-2023'),
    ('SG-005', 'Lady Annika, the Thirsting Blade', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Lady-Annika-The-Thirsting-Blade-2021'),
    ('SG-006', 'Dire Wolves', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Soulblight-Gravelords-Dire-Wolves-2021'),
    ('SG-007', 'Radukar the Beast', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Soulblight-Gravelords-Radukar-The-Beast-2021'),
    ('SG-008', 'Belladamma Volga, First of the Vyrkos', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Belladamma-Volga-First-Of-The-Vyrkos-2021'),
    ('SG-009', 'Vengorian Lord', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Vengorian-Lord-2021'),
    ('SG-010', 'Blood Knights', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Soulblight-Gravelords-Blood-Knights-2021'),
    ('SG-011', 'Fell Bats', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Soulblight-Gravelords-Fell-Bats-2021'),
    ('SG-012', 'Lauka Vai, Mother of Nightmares', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Lauka-Vai-Mother-Of-Nightmares-2021'),
    ('SG-013', 'Vargheists', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Vargheists-2016'),
    ('SG-014', 'Neferata, Mortarch of Blood', Decimal('57.00'),
     'https://www.warhammer.com/en-GB/shop/Deathlords-Mortarchs-Neferata'),
    ('SG-015', 'Mannfred von Carstein, Mortarch of Night', Decimal('57.00'),
     'https://www.warhammer.com/en-GB/shop/Deathlords-Mortarchs-Mannfred'),
    ('SG-016', 'Nagash, Supreme Lord of the Undead', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/Deathlords-Nagash'),
    ('SG-017', 'Mortis Engine', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/Mortis-Engine'),
    ('SG-018', 'Coven Throne', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/Coven-Throne'),
    ('SG-019', 'Corpse Cart', Decimal('23.00'),
     'https://www.warhammer.com/en-GB/shop/Vampire-Counts-Corpse-Cart'),
    ('SG-020', 'Askurgan Trueblades', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-askurgan-trueblades-2025'),
    ('SG-021', 'Wight Lord on Skeletal Steed', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-wight-king-on-skeletal-steed-2025'),
    ('SG-022', 'Soulblight Gravelords: Manifestations', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-manifestations-2025'),
    ('SG-023', 'Cursed Sepulchre/Nexus of Grief', Decimal('52.00'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-cursed-sepulchre-2025'),
    ('SG-024', 'Deathrattle Skeletons', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-deathrattle-skeletons-2025'),
    ('SG-025', 'Barrow Knights', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-barrow-knights-2025'),
    ('SG-026', 'Barrow Guard', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-barrow-guard-2025'),
    ('SG-027', 'Vampire Lord on Nightmare Steed', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-vampire-lord-on-nightmare-steed-2025'),
    ('SG-028', 'Prince Vhordrai, Lord of the Crimson Keep', Decimal('118.00'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-prince-vhordrai-lord-of-the-crimson-keep-2025'),
    ('SG-029', 'Blades of the Hollow King', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-blades-of-the-hollow-king-2025'),
    ('SG-030', 'Sekhar, Fang of Nulahmia', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/soulblight-gravelords-sekhar-fang-of-nulahmia-2024'),
    ('SG-031', 'Death Battletome: Soulblight Gravelords', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-soulblight-gravelords-2025-eng'),
    ('SG-032', 'Kritza, the Rat Prince', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Kritza-The-Rat-Prince-2021'),
    ('SG-033', 'Radukar the Wolf', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Soulblight-Gravelords-Radukar-The-Wolf-2021'),
    ('SG-034', 'Deadwalker Zombies', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Deadwalker-Zombies-2021'),
    ('SG-035', 'Vampire Lord', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/Soulblight-Gravelords-Vampire-Lord-2021'),
    ('SG-036', 'Wight King', Decimal('12.75'),
     'https://www.warhammer.com/en-GB/shop/Deathrattle-Wight-King-2018'),
    ('SG-037', 'Necromancer', Decimal('12.75'),
     'https://www.warhammer.com/en-GB/shop/The-Deathmages-Necromancer-2016'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Soulblight Gravelords. Idempotent.'

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
                f'Seeded {seeded} Soulblight Gravelords GW UK prices. Skipped: {skipped}.'
            )
        )
