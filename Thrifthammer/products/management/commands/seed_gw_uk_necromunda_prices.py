"""
Seed Games Workshop UK prices for Necromunda.

Creates the `games-workshop-uk` Retailer if it does not exist, sets
msrp_gbp on each matched Product, and creates/updates a CurrentPrice
record pointing at the GW UK product page.

4 products (NM-001 Hive Secundus, NM-002 Hive War, NM-003 Core Rulebook,
NM-016 Promethium Tanks Refuelling Station) have no entry in the source
UK sheet and are intentionally excluded -- no msrp_gbp, no CurrentPrice.
NM-023 (Thatos Pattern: Hab Module) reuses the price of NM-021 (Thatos
Pattern: Extended Hab Module, same £67.50) per user direction, but has
no confirmed UK product page -- url is left blank.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url)
_PRICES = [
    ('NM-004', 'Enforcer \'Sanctioner\' Pattern Automata', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-enforcer-sanctioner-automata-2023'),
    ('NM-006', 'Cawdor Gang', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Cawdor-Gang-2018'),
    ('NM-007', 'Delaque Gang', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Delaque-Gang-2018'),
    ('NM-008', 'Orlock Gang', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Orlock-Gang-2018'),
    ('NM-013', 'Palanite Enforcer Patrol', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Palanite-Enforcer-Patrol-2019'),
    ('NM-014', 'Cawdor Ridge Walkers', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-cawdor-ridge-walkers-2023'),
    ('NM-015', 'Promethium Tanks on Cargo-8 Ridgehauler Trailer', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/necromunda-promethium-tanks-on-cargo-8-trailer-2022'),
    ('NM-017', 'Escher Cutters', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-escher-cutters-2022'),
    ('NM-018', 'Cargo-8 Ridgehauler Gunner Frames', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/cargo-8-ridgehauler-gunner-frames-2022'),
    ('NM-019', 'Cargo-8 Ridgehauler Trailer', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/necromunda-cargo-8-ridgehauler-trailer-2022'),
    ('NM-020', 'Cargo-8 Ridgehauler', Decimal('64.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-cargo-8-ridgehauler-2022'),
    ('NM-021', 'Thatos Pattern: Extended Hab Module', Decimal('67.50'),
     'https://www.warhammer.com/en-GB/shop/thatos-pattern-extended-hab-module-2022'),
    ('NM-022', 'Thatos Pattern: Platforms & Walkways', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/thatos-pattern-platforms-and-walkways-2022'),
    ('NM-023', 'Thatos Pattern: Hab Module', Decimal('67.50'),
     ''),
    ('NM-024', 'Orlock Outrider Quads', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-orlock-outrider-quads-2022'),
    ('NM-025', 'Ash Waste Nomads Dustback Helamites', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/ash-waste-nomads-dustback-helamites-2022'),
    ('NM-026', 'Ash Waste Nomads War Party', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-ash-wastes-nomads-war-party-2022'),
    ('NM-027', 'Delaque Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-delaque-weapons-2022'),
    ('NM-028', 'Hive Scum', Decimal('14.00'),
     'https://www.warhammer.com/en-GB/shop/necromunda-hive-scum-2022'),
    ('NM-029', 'Van Saar Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-van-saar-weapons-and-upgrades-2021'),
    ('NM-030', 'Orlock Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-orlock-weapons-upgrades-2021'),
    ('NM-031', 'Delaque Nacht-Ghul, Psy-Gheists and Piscean Spektor', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/delaque-nacht-ghul-and-psy-gheists-2021'),
    ('NM-032', 'Cawdor Redemptionists', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Cawdor-Redemptionists-2021'),
    ('NM-033', 'Goliath Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Goliath-Weapons-and-Upgrades-2021'),
    ('NM-034', 'Escher Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Escher-Weapons-and-Upgrades-2021'),
    ('NM-035', 'Van Saar Archeoteks & Grav-cutters', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Van-Saar-Archeoteks-and-Grav-cutters-2020'),
    ('NM-036', 'Orlock Arms Masters and Wreckers', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Orlock-Arms-Masters-and-Wreckers-2020'),
    ('NM-037', '\'Jotunn\' H-Grade Industrial Servitor Ogryns', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/Jotunn-H-grade-Servitor-Ogryns-2020'),
    ('NM-038', 'Escher Death-maidens and Wyld Runners', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Escher-Death-Maidens-and-Wyld-Runners-2020'),
    ('NM-039', 'Goliath Stimmers and Forge-born', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Goliath-Stimmers-And-Forgeborn-2020'),
    ('NM-040', 'Palanite Subjugator Patrol', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Palanite-Subjugator-Patrol-2020'),
    ('NM-041', 'Luther Pattern Excavation Automata "Ambot"', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Ambot-2019'),
    ('NM-042', 'Necromunda Barricades and Objectives', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Barricades-Objectives-2017'),
    ('NM-043', 'Underhive Hangers-on', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/necromunda-underhive-hangers-on-2025'),
    ('NM-044', 'Palanite Enforcer Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-enforcer-weapons-and-upgrades-2025'),
    ('NM-045', 'Ironhead Squat Charter Masters and Drill Masters', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-ironhead-squat-charter-and-drill-masters-2025'),
    ('NM-046', 'Palanite Justicars', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/necromunda-palanite-justicars-2025'),
    ('NM-047', 'Ozostium Aranthus, the Divine Prince', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/necromunda-ozostium-aranthus-2025'),
    ('NM-048', 'Ashwing Helamites', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-nomads-ashwing-helamites-2025'),
    ('NM-049', 'Palanite Enforcer Captains & Sergeants', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-palatine-enforcer-captains-and-sergeants-2025'),
    ('NM-050', 'Zone Mortalis: Ruined Underhive Sector', Decimal('105.50'),
     'https://www.warhammer.com/en-GB/shop/zone-mortalis-ruined-underhive-sector-2025'),
    ('NM-051', 'Thatos Pattern Fortified Hab Module', Decimal('69.50'),
     'https://www.warhammer.com/en-GB/shop/thatos-pattern-fortified-hab-module-2025'),
    ('NM-052', 'Ash Waste Nomads: Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/ash-waste-nomads-weapons-and-upgrades-2025'),
    ('NM-053', 'Sha\'dar Hunters and Arthromite Spinewyrms', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/shadar-hunters-and-arthromite-spinewyrms-2025'),
    ('NM-054', 'Ironhead Squat Svenotar Scout Trikes', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/ironhead-squat-svenotar-scout-trikes-2024'),
    ('NM-055', 'Ironhead Squat Prospectors Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-squat-prospectors-weapons-and-upgrades-2024'),
    ('NM-056', 'Ironhead Squat Prospectors Exo-kyn', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-squat-prospectors-exo-kyn-2024'),
    ('NM-057', 'Van Saar Tek-hunters', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-van-saar-tek-hunters-2024'),
    ('NM-058', 'Malcadon, Yeld, and Jakara Spyre Hunters', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-malcadon-yeld-and-jakara-spyre-hunter-2024'),
    ('NM-059', 'Orrus Spyre Hunters', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-orrus-spyre-hunters-2024'),
    ('NM-060', 'Ruined Zone Mortalis', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-ruined-zone-mortalis-2024'),
    ('NM-061', 'Hive Data Stack Cluster', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-hive-data-stack-cluster-2024'),
    ('NM-062', 'Palanite Enforcer Tauros Venator', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/necromunda-palanite-enforcer-tauros-venator-2023'),
    ('NM-063', 'Van Saar Ash Wastes Arachni-rig', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-van-saar-ash-wastes-arachni-rig-2023'),
    ('NM-064', 'Goliath Maulters', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-goliath-maulers-2022'),
    ('NM-065', 'Zone Mortalis: Underhive Market', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-zone-mortalis-underhive-market-2021'),
    ('NM-066', 'Cawdor Weapons & Upgrades', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-cawdor-weapons-and-upgrades-2021'),
    ('NM-067', 'Zone Mortalis: Gang Stronghold', Decimal('64.50'),
     'https://www.warhammer.com/en-GB/shop/Zone-Mortalis-Gang-Stronghold-2020'),
    ('NM-068', 'Necromunda Zone Mortalis Platforms and Stairs', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/Zone-Mortalis-Platforms-And-Stairs-2020'),
    ('NM-069', 'Necromunda Zone Mortalis Columns and Walls', Decimal('62.00'),
     'https://www.warhammer.com/en-GB/shop/Zone-Mortalis-Columns-And-Walls-2020'),
    ('NM-070', 'Zone Mortalis: Floor Tile Set', Decimal('52.00'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Zone-Mortalis-Floor-Tile-Set-2019'),
    ('NM-071', 'Kal Jericho and Scabs', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Kal-Jerico-and-Scabs-2019'),
    ('NM-072', 'Trazior Pattern Sentry Guns', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/necromunda-trazior-pattern-sentry-guns-2024'),
    ('NM-073', 'Malstrain Genestealer Abomination Gang', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-genestealer-abomination-gang-2024'),
    ('NM-074', 'Corpse Grinder Cult Gang', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Necromunda-Corpse-Grinder-Cult-2020'),
    ('NM-075', 'Ironhead Squat Prospectors Gang', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/necromunda-ironhead-squat-prospectors-2022'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Necromunda. Idempotent.'

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
                f'Seeded {seeded} Necromunda GW UK prices. Skipped: {skipped}.'
            )
        )
