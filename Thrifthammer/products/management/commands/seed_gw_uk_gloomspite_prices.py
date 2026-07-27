"""
Seed Games Workshop UK prices for Gloomspite Gitz.

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
    ('70-894', 'Spearhead: Gloomspite Gitz – Snarlpack Huntaz', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-gloomspite-gitz-snarlpack-huntaz-2025'),
    ('89-06', 'Gloomspite Gitz Fanatics', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/sporesplatta-fanatics-2023'),
    ('89-10', 'Gloomspite Gitz Squig Herd', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Squig-Herd-2019'),
    ('89-11', 'Gloomspite Gitz Squig Hoppers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Squig-Hoppers-2019'),
    ('GG-001', 'Boingrot Bounderz', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/boingrot-bounderz-2023'),
    ('GG-002', 'Squigboss with Gnasha-squig', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-squigboss-with-gnasha-squig-2023'),
    ('GG-003', 'Loonboss on Giant Cave Squig', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Gloomspte-Gitz-Loonboss-On-Giant-Cave-Squig-2020'),
    ('GG-004', 'Loonboss on Mangler Squigs', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Loonboss-on-Mangler-Squigs-2019'),
    ('GG-005', 'Mangler Squigs', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Mangler-Squigs-2019'),
    ('GG-006', 'Trugg the Troggoth King', Decimal('64.50'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-trugg-the-troggoth-king-2024'),
    ('GG-007', 'Spider Riders', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Grot-Spider-Riders'),
    ('GG-008', 'Snarlfang Riders', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-snarlfang-riders-2023'),
    ('GG-009', 'Kragnos, the End of Empires', Decimal('115.00'),
     'https://www.warhammer.com/en-GB/shop/Kragnos-The-End-Of-Empires-2021'),
    ('GG-010', 'Dankhold Troggboss', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Dankhold-Troggboss-2019'),
    ('GG-011', 'Gobbapalooza', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Gobbapalooza-2019'),
    ('GG-012', 'Dankhold Troggoth', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Dankhold-Troggoth-2019'),
    ('GG-013', 'Sneaky Snufflers', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Sneaky-Snufflers-2019'),
    ('GG-014', 'Loonboss', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Loonboss-2019'),
    ('GG-015', 'Moonclan Shootas', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Grots-Shootas-2019'),
    ('GG-016', 'Endless Spells: Gloomspite Gitz', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-spells-gloomspite-gitz-2019'),
    ('GG-017', 'Bad Moon Loonshrine', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-gitz-bad-moon-loonshrine-2019'),
    ('GG-018', 'Loonsmasha Fanatics', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz:-Fanatics-2019'),
    ('GG-019', 'Skragrott the Loonking', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Skragrott-The-Loonking-2019'),
    ('GG-020', 'Moonclan Stabbas', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Grots-2019'),
    ('GG-021', 'Fungoid Cave-Shaman', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Moonclan-Grots-Snazzgar-Stinkmullett-2018'),
    ('GG-022', 'Fellwater Troggoths', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/Fellwater-Troggoths-2017'),
    ('GG-023', 'Doom Diver Catapult', Decimal('67.50'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-doom-diver-catapult-2025'),
    ('GG-024', 'Sunsteala Wheelas', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-sunsteala-wheelas-2025'),
    ('GG-025', 'Snarlpack Cavalry', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/gloosmpite-gitz-snarlpack-cavalry-2025'),
    ('GG-026', 'Snarlboss on War-Wheela', Decimal('62.00'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-snarlboss-on-war-wheela-2025'),
    ('GG-027', 'Snarlboss and Wolfgit Retinue', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-snarlboss-and-wolfgit-retinue-2025'),
    ('GG-028', 'Rabble-Rowza', Decimal('23.00'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-rabble-rowza-2023'),
    ('GG-029', 'Destruction Battletome: Gloomspite Gitz', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-gloomspite-gitz-2025-eng'),
    ('GG-030', 'Skitterstrand Arachnarok', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/skitterstrand-arachnarok-2023'),
    ('GG-031', 'Arachnarok Spider with Flinger', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/arachnarok-spider-with-flinger-2023'),
    ('GG-032', 'Webspinner Shaman on Arachnarok Spider', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/webspinner-shaman-on-arachnarok-spider-2023'),
    ('GG-033', 'Rockgut Troggoths', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Gloomspite-Gitz-Rockgut-Troggoths-2019'),
    ('GG-034', 'Arachnarok Spider with Spiderfang Warparty', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/Arachnarok-Spider-2017'),
    ('GG-035', 'Droggz da Sunchompa', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/gloomspite-gitz-droggz-da-sunchompa-2025'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Gloomspite Gitz. Idempotent.'

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
                f'Seeded {seeded} Gloomspite Gitz GW UK prices. Skipped: {skipped}.'
            )
        )
