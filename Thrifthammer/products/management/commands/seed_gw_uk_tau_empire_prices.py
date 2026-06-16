"""
Seed Games Workshop UK prices for T'au Empire.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('56-06',  "T'au Fire Warriors",                                         Decimal('38.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Fire-Warriors-Breacher-Team-2017',                                  True),
    ('56-10',  "T'au Hammerhead Gunship",                                    Decimal('47.50'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Hammerhead-Gunship',                                         True),
    ('56-13',  "T'au Broadside Battlesuit",                                  Decimal('40.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-XV88-Broadside-Battlesuit-2017',                             True),
    ('56-14',  "T'au Stealth Battlesuits",                                   Decimal('42.50'),    'https://www.warhammer.com/en-GB/shop/kill-team-xv26-stealth-battlesuits-2026',                               True),
    ('56-15',  "T'au Crisis Battlesuits",                                    Decimal('54.50'),    'https://www.warhammer.com/en-GB/shop/XV8-Crisis-Battlesuits',                                                True),
    ('56-16',  "T'au Riptide Battlesuit",                                    Decimal('74.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-XV104-Riptide-Battlesuit-2017',                              True),
    ('56-19',  "T'au Pathfinders",                                           Decimal('29.50'),    'https://www.warhammer.com/en-GB/shop/Pathfinder-Team-2017',                                                  True),
    ('56-22',  "T'au Ethereal",                                              Decimal('21.50'),    'https://www.warhammer.com/en-GB/shop/tau-empire-ethereal-2022',                                              True),
    ('56-25',  "T'au Combat Patrol",                                         Decimal('105.00'),   'https://www.warhammer.com/en-GB/shop/combat-patrol-tau-empire-2024',                                         True),
    ('TE-001', "T'au Empire Tidewall Shieldline",                            Decimal('52.00'),    'https://www.warhammer.com/en-GB/shop/Tidewall-Shieldline',                                                   True),
    ('TE-002', "T'au Empire Kroot Hounds",                                   Decimal('27.00'),    'https://www.warhammer.com/en-GB/shop/tau-empire-kroot-hounds-2024',                                          True),
    ('TE-003', "T'au Empire The Twin Lance",                                 Decimal('67.00'),    'https://www.warhammer.com/en-GB/shop/tau-empire-the-twin-lance-2026',                                        True),
    ('TE-004', "T'au Empire Commander Farsight",                             Decimal('42.50'),    'https://www.warhammer.com/en-GB/shop/tau-empire-commander-farsight-2023',                                    True),
    ('TE-005', "T'au Empire Darkstrider",                                    Decimal('25.00'),    'https://www.warhammer.com/en-GB/shop/tau-empire-darkstrider-2022',                                           True),
    ('TE-006', "T'au Empire Commander Shadowsun",                            Decimal('35.50'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Commander-Shadowsun-2020',                                   True),
    ('TE-007', "T'au Empire Fire Warriors Breacher Team",                    Decimal('38.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Fire-Warriors-Breacher-Team-2017',                                  True),
    ('TE-008', "T'au Empire Fire Warriors Strike Team",                      Decimal('38.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Fire-Warriors-2017',                                         True),
    ('TE-009', "T'au Empire Commander",                                      Decimal('40.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Commander-2017',                                             True),
    ('TE-010', "T'au Empire Cadre Fireblade",                                Decimal('20.50'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Cadre-Fireblade-2017',                                       True),
    ('TE-011', "T'au Empire Ta'unar Supremacy Armour Heavy Rail Cannon Array", Decimal('81.00'), 'https://www.warhammer.com/en-GB/shop/Tau-KX139-Taunar-Heavy-Rail-Cannon-Array',                              True),
    ('TE-012', "T'au Empire Ta'unar Nexus Missile System",                   Decimal('81.00'),    'https://www.warhammer.com/en-GB/shop/KX139-Nexus-Meteor',                                                    True),
    ('TE-013', "T'au Empire Tidewall Droneport",                             Decimal('42.50'),    'https://www.warhammer.com/en-GB/shop/Tidewall-Droneport',                                                    True),
    ('TE-014', "T'au Empire Tactical Drones",                                Decimal('12.75'),    'https://www.warhammer.com/en-GB/shop/Tau-Drones-2015',                                                       True),
    ('TE-015', "T'au Empire XV95 Ghostkeel Battlesuit",                      Decimal('58.00'),    'https://www.warhammer.com/en-GB/shop/XV95-Ghostkeel-Battlesuit',                                             True),
    ('TE-016', "T'au Empire KV128 Stormsurge",                               Decimal('118.00'),   'https://www.warhammer.com/en-GB/shop/KV128-Stormsurge',                                                      True),
    ('TE-017', "T'au Empire Razorshark Strike Fighter",                      Decimal('55.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Razorshark-Strike-Fighter',                                  True),
    ('TE-018', "T'au Empire Sky Ray Gunship",                                Decimal('47.50'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Sky-Ray-Missile-Defence-Gunship',                            True),
    ('TE-019', "T'au Empire Sun Shark Bomber",                               Decimal('55.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Sun-Shark-Bomber',                                           True),
    ('TE-020', "T'au Empire Devilfish",                                      Decimal('40.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-TY7-Devilfish-2015',                                         True),
    ('TE-021', "Kill Team: Farstalker Kinband",                              Decimal('42.50'),    'https://www.warhammer.com/en-GB/shop/kill-team-farstalker-kinband-2024',                                     True),
    ('TE-022', "Kill Team: Vespid Stingwings",                               Decimal('42.50'),    'https://www.warhammer.com/en-GB/shop/kill-team-tau-empire-vespid-stingwings-2024',                           True),
    ('TE-023', "T'au Empire Kroot Lone-Spear",                               Decimal('35.50'),    'https://www.warhammer.com/en-GB/shop/tau-empire-kroot-lone-spear-2024',                                      True),
    ('TE-024', "T'au Empire Kroot Trail Shaper",                             Decimal('23.00'),    'https://www.warhammer.com/en-GB/shop/tau-empire-kroot-trail-shaper-2024',                                    True),
    ('TE-025', "T'au Empire Kroot Flesh Shaper",                             Decimal('23.00'),    'https://www.warhammer.com/en-GB/shop/tau-empire-kroot-flesh-shaper-2024',                                    True),
    ('TE-026', "T'au Empire Kroot War Shaper",                               Decimal('25.00'),    'https://www.warhammer.com/en-GB/shop/tau-empire-kroot-war-shaper-2024',                                      True),
    ('TE-027', "T'au Empire Krootox Rider",                                  Decimal('29.50'),    'https://www.warhammer.com/en-GB/shop/tau-empire-krootox-rider-2024',                                         True),
    ('TE-028', "T'au Empire Krootox Rampagers",                              Decimal('40.00'),    'https://www.warhammer.com/en-GB/shop/tau-empire-krootox-rampagers-2024',                                     True),
    ('TE-029', "Codex: T'au Empire",                                         Decimal('38.00'),    'https://www.warhammer.com/en-GB/shop/codex-tau-empire-2024-eng',                                             True),
    ('TE-030', "T'au Empire Tiger Shark AX-1-0",                             Decimal('215.00'),   'https://www.warhammer.com/en-GB/shop/Tau-Tigershark-AX-1-0-2017',                                            True),
    ('TE-031', "T'au Empire Ta'unar Supremacy Armour Fusion Eradicator",     Decimal('41.50'),    "https://www.warhammer.com/en-GB/shop/KX139-Ta'unar-Supremacy-Armour-Fusion-Eradicator",                      True),
    ('TE-032', "T'au Empire Ta'unar Supremacy Armour Pulse Ordnance Multi-driver", Decimal('81.00'), "https://www.warhammer.com/en-GB/shop/KX139-Ta'unar-Supremacy-Armour-Pulse-Ordnance-Multi-driver",         True),
    ('TE-033', "T'au Empire Ta'unar Supremacy Armour Tri-axis Ion Cannon",   Decimal('41.50'),    "https://www.warhammer.com/en-GB/shop/KX139-Ta'unar-Supremacy-Armour-Tri-axis-Ion-Cannon",                    True),
    ('TE-034', "T'au Empire Manta",                                          Decimal('1357.50'),  'https://www.warhammer.com/en-GB/shop/Tau-Manta',                                                              True),
    ('TE-035', "T'au Empire Firesight Team",                                 Decimal('32.50'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-Sniper-Drone-Team',                                          True),
    ('TE-036', "T'au Empire Piranha",                                        Decimal('27.00'),    'https://www.warhammer.com/en-GB/shop/Tau-Empire-TX4-Piranha-2015',                                           True),
    ('TE-037', "T'au Empire Kroot Carnivores",                               Decimal('35.50'),    'https://www.warhammer.com/en-GB/shop/tau-empire-kroot-carnivore-squad-2024',                                 True),
    ('KT-028', "Kill Team: Stealth Battlesuits",                             Decimal('42.50'),    'https://www.warhammer.com/en-GB/shop/kill-team-xv26-stealth-battlesuits-2026',                               True),
]


class Command(BaseCommand):
    help = "Seed GW UK prices for T'au Empire. Idempotent."

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

        self.stdout.write(f"Seeded {seeded} T'au Empire GW UK prices. Skipped: {skipped}.")
