"""
Seed Games Workshop UK prices for Stormcast Eternals.

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
    ('96-11', 'Stormcast Eternals Liberators', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-liberators-2024'),
    ('96-12', 'Stormcast Eternals Knight-Judicator with Gryph-hounds', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-knight-judicator-with-gryph-hounds-2021'),
    ('96-14', 'Stormcast Eternals Lord-Celestant', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-lord-celestant-2024'),
    ('96-50', 'Stormcast Eternals Vindictors', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-vindictors-2021'),
    ('96-55', 'Stormcast Eternals Praetors', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-praetors-2021'),
    ('SE-001', 'Order Battletome: Stormcast Eternals', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-stormcast-eternals-hb-2024-eng'),
    ('SE-002', 'Warhammer Age of Sigmar: Introductory Set', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/age-of-sigmar-introductory-set-row-2026-eng'),
    ('SE-003', 'Warhammer Age of Sigmar: Starter Set', Decimal('69.50'),
     'https://www.warhammer.com/en-GB/shop/age-of-sigmar-starter-set-2024-eng'),
    ('SE-004', 'Stormcast Eternals Annihilators', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-annihilators-2021'),
    ('SE-005', 'Stormcast Eternals Vanguard-Hunters', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Vanguard-Hunters-2017'),
    ('SE-006', 'Stormcast Eternals Stormcoven', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-stormcoven-2024'),
    ('SE-007', 'Stormcast Eternals Karazai the Scarred', Decimal('105.50'),
     'https://www.warhammer.com/en-GB/shop/karazai-the-scarred-2021'),
    ('SE-008', 'Stormcast Eternals Krondys, Son of Dracothion', Decimal('105.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-krondys-son-of-dracothian-2021'),
    ('SE-009', 'Stormcast Eternals Annihilators with Meteoric Grandhammers', Decimal('37.00'),
     'https://www.warhammer.com/en-GB/shop/annihilators-with-meteoric-grandhammers-2021'),
    ('SE-010', 'Stormcast Eternals Vanquishers', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-vanquishers-2021'),
    ('SE-011', 'Stormcast Eternals Vigilors', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-vigilors-2021'),
    ('SE-012', 'Stormcast Eternals Lord-Commander Bastian Carthalos', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-lord-commander-bastian-carthalos-2021'),
    ('SE-013', 'Stormcast Eternals Stormstrike Chariot', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-stormstrike-chariot-2021'),
    ('SE-014', 'Stormcast Eternals Gardus Steel Soul', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Gardus-Steel-Soul-2021'),
    ('SE-015', 'Stormcast Eternals Endless Spells: Stormcast Eternals', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Battlemagic-Stormcast-2018'),
    ('SE-016', 'Stormcast Eternals Vandus Hammerhand', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Vandus-Hammerhand'),
    ('SE-017', 'Stormcast Eternals Vanguard-Palladors', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Vanguard-Palladors-2017'),
    ('SE-018', 'Stormcast Eternals Lord-Aquilor', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Lord-Aquilor-2017'),
    ('SE-019', 'Stormcast Eternals Gryph-hounds', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Gryph-hounds-2017'),
    ('SE-020', 'Stormcast Eternals Knight-Questor', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/knight-questor'),
    ('SE-021', 'Stormcast Eternals Drakesworn Templar', Decimal('115.00'),
     'https://www.warhammer.com/en-GB/shop/Drakesworn-Templar'),
    ('SE-022', 'Stormcast Eternals Lord-Celestant on Stardrake', Decimal('115.00'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Stardrake'),
    ('SE-023', 'Stormcast Eternals Celestant-Prime, Hammer of Sigmar', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Celestant-Prime'),
    ('SE-024', 'Stormcast Eternals Questor Soulsworn', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-questor-soulsworn-2025'),
    ('SE-025', 'Stormcast Eternals Stormreach Portal', Decimal('52.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-stormreach-portal-2024'),
    ('SE-026', 'Stormcast Eternals Lord-Imperatant', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-lord-imperatant-2024'),
    ('SE-027', 'Stormcast Eternals Knight-Arcanum', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-knight-arcanum-2024'),
    ('SE-028', 'Stormcast Eternals Prosecutors', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-prosecutors-2024'),
    ('SE-029', 'Stormcast Eternals Iridan the Witness', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-iridan-the-witness-2024'),
    ('SE-030', 'Stormcast Eternals Reclusians', Decimal('38.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-reclusians-2024'),
    ('SE-031', 'Stormcast Eternals Lord-Terminos', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-lord-terminos-2024'),
    ('SE-032', 'Stormcast Eternals Lord-Relictor', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-lord-relictor-2024'),
    ('SE-033', 'Stormcast Eternals Tornus the Redeemed', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-tornus-the-redeemed-2024'),
    ('SE-034', 'Stormcast Eternals Stormstrike Palladors', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-stormstrike-palladors-2024'),
    ('SE-035', 'Stormcast Eternals Ionus Cryptborn, Warden of Lost Souls', Decimal('88.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-ionus-cryptborn-2024'),
    ('SE-036', 'Stormcast Eternals The Blacktalons', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/the-blacktalons-2023'),
    ('SE-037', 'Stormcast Eternals Knight-Draconis', Decimal('80.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-knight-draconis-2021'),
    ('SE-038', 'Stormcast Eternals Stormdrake Guard', Decimal('80.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-stormdrake-guard-2021'),
    ('SE-039', 'Stormcast Eternals Knight-Relictor', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/stormcast-eternals-knight-relictor-2021'),
    ('SE-040', 'Stormcast Eternals Vanguard-Raptors With Longstrike Crossbows & Aetherwings', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Vanguard-Raptors-2017'),
    ('SE-041', 'Stormcast Eternals Tempestors', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Tempestors'),
    ('SE-042', 'Stormcast Eternals Lord-Celestant on Dracoth', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Lord-Celestant-on-Dracoth'),
    ('SE-043', 'Stormcast Eternals Vanguard-Raptors With Hurricane Crossbows & Aetherwings', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Vanguard-Raptors-with-Hurricaine-Crossbows-2017'),
    ('SE-044', 'Stormcast Eternals Desolators', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Desolators'),
    ('SE-045', 'Stormcast Eternals Concussors', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Concussors'),
    ('SE-046', 'Stormcast Eternals Fulminators', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Stormcast-Eternals-Dracothian-Guard'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Stormcast Eternals. Idempotent.'

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
                f'Seeded {seeded} Stormcast Eternals GW UK prices. Skipped: {skipped}.'
            )
        )
