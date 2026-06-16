"""
Seed Games Workshop UK prices for Space Marines and successor chapters
(Imperial Fists, Iron Hands, Raven Guard, Salamanders, Ultramarines, White Scars).

GW sells all these under one Space Marines range; our DB splits them into
separate factions. filter(gw_sku=sku) is faction-agnostic so one command
covers all seven factions.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    # ── Space Marines ────────────────────────────────────────────────────────
    ('48-06',  'Space Marine Terminator Squad',              Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/space-marines-terminator-squad-2023',                         True),
    ('48-07',  'Space Marine Tactical Squad',                Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marine-Tactical-Squad-2020',                           True),
    ('48-15',  'Space Marine Devastator Squad',              Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marine-Devastator-Squad-2020',                         True),
    ('48-22',  'Space Marine Land Raider Crusader',          Decimal('71.50'), 'https://www.warhammer.com/en-GB/shop/Land-Raider-Crusader-2020',                                  True),
    ('48-25',  'Space Marine Whirlwind',                     Decimal('45.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marine-Whirlwind',                                     True),
    ('48-26',  'Space Marine Vindicator',                    Decimal('47.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marine-Vindicator-2020',                               True),
    ('48-27',  'Space Marine Hammerfall Bunker',             Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/Hammerfall-Bunker-2020',                                     True),
    ('48-28',  'Space Marine Firestrike Servo-Turrets',      Decimal('25.00'), 'https://www.warhammer.com/en-GB/shop/Primaris-Firestrike-Servo-turret-2020',                      True),
    ('48-30',  'Space Marine Librarian',                     Decimal('26.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Librarian-2020',                      True),
    ('48-32',  'Space Marine Chaplain',                      Decimal('26.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Chaplain-2020',                       True),
    ('48-33',  'Space Marine Apothecary',                    Decimal('26.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Apothecary-2020',                     True),
    ('48-34',  'Space Marine Ancient',                       Decimal('27.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-primaris-ancient-2022',                        True),
    ('48-37',  'Space Marine Company Heroes',                Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/space-marines-company-heroes-2023',                          True),
    ('48-38',  'Space Marine Bladeguard Veterans',           Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Bladeguard-Veterans-2020',                     True),
    ('48-39',  'Space Marine Eradicators',                   Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Eradicators-2020',                    True),
    ('48-40',  'Space Marine Outriders',                     Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Outriders-2020',                                             True),
    ('48-41',  'Space Marine Infiltrators',                  Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Infiltrators-2020',                   True),
    ('48-42',  'Space Marine Invader ATV',                   Decimal('32.50'), 'https://www.warhammer.com/en-GB/shop/Primaris-Invader-ATV-2020',                                  True),
    ('48-43',  'Space Marine Sternguard Veteran Squad',      Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-sternguard-veteran-squad-2023',                True),
    ('48-44',  'Space Marine Brutalis Dreadnought',          Decimal('52.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-brutalis-dreadnought-2023',                    True),
    ('48-45',  'Space Marine Infernus Squad',                Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-infernus-squad-2023',                          True),
    ('48-46',  'Space Marine Ballistus Dreadnought',         Decimal('44.50'), 'https://www.warhammer.com/en-GB/shop/space-marines-ballistus-dreadnought-2023',                   True),
    ('48-61',  'Space Marine Primaris Lieutenant',           Decimal('25.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-lieutenant-2023',                              True),
    ('48-62',  'Space Marine Primaris Captain',              Decimal('27.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marine-Primaris-Captain-2020',                         True),
    ('48-75',  'Space Marine Intercessors',                  Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Intercessors-2020',                   True),
    ('48-76',  'Space Marine Assault Intercessors',          Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Assault-Intercessors-2020',                                  True),
    ('48-85',  'Space Marine Repulsor',                      Decimal('58.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Repulsor-2020',                       True),
    ('48-92',  'Space Marine Aggressors',                    Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Aggressors-2020',                     True),
    ('48-93',  'Space Marine Redemptor Dreadnought',         Decimal('49.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Redemptor-Dreadnought-2020',          True),
    ('48-94',  'Space Marine Impulsor',                      Decimal('55.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Impulsor-2020',                       True),
    ('48-95',  'Space Marine Repulsor Executioner',          Decimal('71.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Repulsor-Executioner-2020',           True),
    ('48-96',  'Space Marine Incursors',                     Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Incursors-2020',                      True),
    ('48-97',  'Space Marine Inceptors',                     Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Inceptors-2020',                      True),
    ('48-98',  'Space Marine Primaris Eliminators',          Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Eliminators-2020',                    True),
    ('48-99',  'Ancient in Terminator Armour',               Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-ancient-in-terminator-armour-2025',            True),
    ('48-100', 'Assault Intercessors with Jump Packs',       Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-jump-pack-intercessors-2023',                  True),
    ('48-101', 'Captain in Gravis Armour',                   Decimal('27.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-captain-in-gravis-armour-2022',                True),
    ('48-102', 'Captain in Phobos Armour',                   Decimal('27.00'), 'https://www.warhammer.com/en-GB/shop/Primaris-Captain-In-Phobos-Armour-2020',                     True),
    ('48-103', 'Captain in Terminator Armour',               Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-captain-in-terminator-armour-2023',            True),
    ('48-104', 'Captain with Jump Pack',                     Decimal('27.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-captain-with-jump-pack-2023',                  True),
    ('48-105', 'Captain with Jump Pack and Relic Shield',    Decimal('27.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-captain-with-jump-pack-and-relic-shield-2025', True),
    ('48-106', 'Captain with Relic Shield',                  Decimal('27.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-captain-with-storm-shield-2023',               True),
    ('48-107', 'Centurion Assault Squad',                    Decimal('50.00'), 'https://www.warhammer.com/en-GB/shop/Centurion-Assault-Squad-2020',                               True),
    ('48-108', 'Centurion Devastator Squad',                 Decimal('50.00'), 'https://www.warhammer.com/en-GB/shop/Centurion-Devastator-Squad-2020',                            True),
    ('48-109', 'Chaplain on Bike',                           Decimal('35.50'), 'https://www.warhammer.com/en-GB/shop/Primaris-Chaplain-on-Bike-2020',                             True),
    ('48-110', 'Codex: Space Marines',                       Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/codex-space-marines-hb-2023-eng',                            True),
    ('48-111', 'Desolation Squad',                           Decimal('38.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-desolation-squad-2023',                        True),
    ('48-112', 'Drop Pods',                                  Decimal('52.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-drop-pods-2025',                               True),
    ('48-113', 'Gladiator Lancer',                           Decimal('58.00'), 'https://www.warhammer.com/en-GB/shop/Gladiator-Lancer-2020',                                      True),
    ('48-114', 'Gladiator Reaper',                           Decimal('58.00'), 'https://www.warhammer.com/en-GB/shop/Gladiator-Reaper-2020',                                      True),
    ('48-115', 'Gladiator Valiant',                          Decimal('58.00'), 'https://www.warhammer.com/en-GB/shop/Gladiator-2020',                                             True),
    ('48-116', 'Heavy Intercessor Squad',                    Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Heavy-Intercessors-2021',                      True),
    ('48-117', 'Hellblaster Squad',                          Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Hellblasters-2020',                   True),
    ('48-118', 'Invictor Tactical Warsuit',                  Decimal('44.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marine-Primaris-Invictor-Tactical-Warsuit-2020',       True),
    ('48-119', 'Land Raider Redeemer',                       Decimal('71.50'), 'https://www.warhammer.com/en-GB/shop/Landraider-Redeemer-2020',                                   True),
    ('48-120', 'Librarian in Terminator Armour',             Decimal('26.00'), 'https://www.warhammer.com/en-GB/shop/space-marine-librarian-in-terminator-armour-2023',           True),
    ('48-121', 'Lieutenant in Reiver Armour',                Decimal('25.00'), 'https://www.warhammer.com/en-GB/shop/Primaris-Lieutenant-In-Phobos-Armour-2020',                  True),
    ('48-122', 'Lieutenant with Power Sword',                Decimal('25.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marine-Primaris-Lieutenant-With-Power-Sword-2020',     True),
    ('48-123', 'Lieutenant with Storm Shield',               Decimal('25.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-lieutenant-with-storm-shield-2023',            True),
    ('48-124', 'Predator Destructor',                        Decimal('47.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Predator-2020',                                True),
    ('48-125', 'Primaris Librarian in Phobos Armour',        Decimal('25.00'), 'https://www.warhammer.com/en-GB/shop/Primaris-Librarian-In-Phobos-Armour-2020',                   True),
    ('48-126', 'Razorback',                                  Decimal('36.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Razorback-2020',                               True),
    ('48-127', 'Reiver Squad',                               Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Primaris-Reivers-2020',                        True),
    ('48-128', 'Rhino',                                      Decimal('36.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Rhino-2020',                                   True),
    ('48-129', 'Stormhawk Interceptor',                      Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/Stormhawk-Interceptor-2020',                                 True),
    ('48-130', 'Stormraven Gunship',                         Decimal('78.00'), 'https://www.warhammer.com/en-GB/shop/Stormraven-Gunship-2020',                                    True),
    ('48-131', 'Storm Speeder Hailstrike',                   Decimal('49.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Storm-Speeder-2020',                           True),
    ('48-132', 'Storm Speeder Hammerstrike',                 Decimal('49.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Storm-Speeder-Hammerstrike',                   True),
    ('48-133', 'Storm Speeder Thunderstrike',                Decimal('49.50'), 'https://www.warhammer.com/en-GB/shop/Space-Marines-Storm-Speeder-Thunderstrike',                  True),
    ('48-134', 'Stormtalon Gunship',                         Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/Stormtalon-Gunship-2020',                                    True),
    ('48-135', 'Techmarine',                                 Decimal('27.00'), 'https://www.warhammer.com/en-GB/shop/Primaris-Techmarine-2020',                                   True),
    ('48-136', 'Terminator Assault Squad',                   Decimal('42.50'), 'https://www.warhammer.com/en-GB/shop/space-marines-terminator-assault-squad-2025',                True),
    ('48-137', 'Venerable Dreadnought',                      Decimal('40.00'), 'https://www.warhammer.com/en-GB/shop/Space-Marine-Venerable-Dreadnought-2020',                    True),
    ('HA-051', 'Space Marine Chaplain in Terminator Armour', Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/space-marines-chaplain-in-terminator-armour-2023',           True),
    ('KT-018', 'Kill Team: Scout Squad',                     Decimal('49.50'), 'https://www.warhammer.com/en-GB/shop/kill-team-scout-squad-2024',                                 True),
    # ── Imperial Fists ───────────────────────────────────────────────────────
    ('60-01',  'Darnath Lysander',                           Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/imperial-fists-darnath-lysander-2025',                       True),
    ('60-02',  'Tor Garadon',                                Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/Imperial-Fists-Tor-Garadon-2020',                            True),
    # ── Iron Hands ───────────────────────────────────────────────────────────
    ('61-01',  'Caanok Var',                                 Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/iron-hands-caanok-var-2025',                                 True),
    ('61-02',  'Iron Father Feirros',                        Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/Iron-Hands-Feirros-2020',                                    True),
    # ── Raven Guard ──────────────────────────────────────────────────────────
    ('62-01',  'Aethon Shaan',                               Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/raven-guard-aethon-shaan-2025',                              True),
    ('62-02',  'Kayvaan Shrike',                             Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/Raven-Guard-Kayvaan-Shrike-2020',                            True),
    # ── Salamanders ──────────────────────────────────────────────────────────
    ('63-01',  'Adrax Agatone',                              Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/Salamanders-Adrax-Agatone-2020',                             True),
    ('63-02',  "Vulkan He'stan",                             Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/salamanders-vulkan-hestan-2025',                             True),
    # ── Ultramarines ─────────────────────────────────────────────────────────
    ('55-31',  'Captain Titus and The Wardens of Ultramar',  Decimal('57.00'), 'https://www.warhammer.com/en-GB/shop/captain-titus-and-the-wardens-of-ultramar-2026',             True),
    ('55-32',  'Cato Sicarius',                              Decimal('29.50'), 'https://www.warhammer.com/en-GB/shop/ultramarines-cato-sicarius-2025',                            True),
    ('55-33',  'Chief Librarian Tigurius',                   Decimal('29.50'), 'https://www.warhammer.com/en-GB/shop/Ultramarines-Chief-Librarian-Tigurius-2020',                 True),
    ('55-34',  'Ultramarines Upgrades and Transfers',        Decimal('23.00'), 'https://www.warhammer.com/en-GB/shop/ultramarines-upgrades-and-transfers-2025',                   True),
    ('55-35',  'Victrix Honour Guard',                       Decimal('38.50'), 'https://www.warhammer.com/en-GB/shop/ultramarines-victrix-honour-guard-2025',                     True),
    # ── White Scars ──────────────────────────────────────────────────────────
    ('64-01',  "Kor'sarro Khan",                             Decimal('29.00'), 'https://www.warhammer.com/en-GB/shop/White-Scars-KorSarro-Khan-2020',                             True),
    ('64-02',  'Suboden Khan',                               Decimal('38.50'), 'https://www.warhammer.com/en-GB/shop/white-scars-suboden-khan-2025',                              True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices for Space Marines and successor chapters. Idempotent.'

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

        for sku, label, gbp_price, url, in_stock in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stdout.write(f'  SKIP {sku} ({label}) — not found in DB')
                skipped += 1
                continue
            for product in products:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'url': url,
                        'in_stock': in_stock,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(f'Seeded {seeded} Space Marines GW UK prices. Skipped: {skipped}.')
