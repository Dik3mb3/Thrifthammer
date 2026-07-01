"""
Management command: seed_nk_necromunda_prices

Seeds Noble Knight URLs and initial prices for Necromunda products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Items with price=None had no scraped price available; NK GitHub Actions
will populate prices on next run.

Usage:
    python manage.py seed_nk_necromunda_prices
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('necromunda-hive-secundus', 'Necromunda - Hive Secundus', Decimal('154.95'), 'https://www.nobleknight.com/P/2148177572/Necromunda---Hive-Secundus?awid=1576', True, False),
    ('necromunda-hive-war', 'Necromunda - Hive War', None, 'https://www.nobleknight.com/P/2147886574/Necromunda---Hive-War?awid=1576', False, False),
    ('necromunda-core-rulebook', 'Necromunda - Core Rulebook', Decimal('66.95'), 'https://www.nobleknight.com/P/2148067717/Necromunda---Core-Rulebook?awid=1576', True, False),
    ('enforcer-sanctioner-pattern-automata', "Enforcer Sanctioner Pattern Automata", None, 'https://www.nobleknight.com/P/2148097003/Enforcer-Sanctioner-Pattern-Automata?awid=1576', False, False),
    ('delaque-gang', 'Delaque Gang', Decimal('45.95'), 'https://www.nobleknight.com/P/2147739904/Delaque-Gang?awid=1576', True, False),
    ('orlock-gang', 'Orlock Gang', Decimal('45.95'), 'https://www.nobleknight.com/P/2147691646/Orlock-Gang?awid=1576', True, False),
    ('necromunda-escher-gang', 'Escher Gang (2017 Edition)', Decimal('45.05'), 'https://www.nobleknight.com/P/2147682880/Escher-Gang-2017-Edition?awid=1576', True, False),
    ('necromunda-goliath-gang', 'Goliath Gang', Decimal('47.95'), 'https://www.nobleknight.com/P/2147682879/Goliath-Gang?awid=1576', True, False),
    ('necromunda-van-saar-gang', 'Van Saar Gang', Decimal('45.95'), 'https://www.nobleknight.com/P/2147702850/Van-Saar-Gang?awid=1576', True, False),
    ('palanite-enforcer-patrol', 'Palanite Enforcer Patrol', Decimal('47.95'), 'https://www.nobleknight.com/P/2147761358/Palantite-Enforcer-Patrol?awid=1576', True, False),
    ('cawdor-ridge-walkers', 'Cawdor Ridge Walkers', Decimal('45.95'), 'https://www.nobleknight.com/P/2148046740/Cawdor-Ridge-Walkers?awid=1576', True, False),
    ('promethium-tanks-on-cargo-8-ridgehauler-trailer', 'Promethium Tanks on Cargo-8 Ridgehauler Trailer', Decimal('56.95'), 'https://www.nobleknight.com/P/2148014061/Promethium-Tanks-on-Cargo-8-Ridgehauler-Trailer?awid=1576', True, False),
    ('promethium-tanks-refuelling-station', 'Promethium Tanks Refuelling Station', Decimal('47.95'), 'https://www.nobleknight.com/P/2148014060/Promethium-Tanks-Refuelling-Station?awid=1576', True, False),
    ('escher-cutters', 'Escher Cutters', Decimal('47.95'), 'https://www.nobleknight.com/P/2148113291/Escher-Cutters?awid=1576', True, False),
    ('cargo-8-ridgehauler-trailer', 'Cargo-8 Ridgehauler Trailer', Decimal('55.95'), 'https://www.nobleknight.com/P/2147986332/Cargo-8-Ridgehauler-Trailer?awid=1576', True, False),
    ('cargo-8-ridgehauler', 'Cargo-8 Ridgehauler', Decimal('93.95'), 'https://www.nobleknight.com/P/2147986329/Cargo-8-Ridgehauler?awid=1576', True, False),
    ('thatos-pattern-extended-hab-module', 'Thatos Pattern - Extended Hab Module', Decimal('100.95'), 'https://www.nobleknight.com/P/2147980623/Thatos-Pattern---Extended-Hab-Module?awid=1576', True, False),
    ('thatos-pattern-platforms-walkways', 'Thatos Pattern - Platforms & Walkways', Decimal('73.95'), 'https://www.nobleknight.com/P/2147980625/Thatos-Pattern---Platforms-and-Walkways?awid=1576', True, False),
    ('thatos-pattern-hab-module', 'Thatos Pattern - Hab Module', Decimal('58.95'), 'https://www.nobleknight.com/P/2147980632/Thatos-Pattern---Hab-Module?awid=1576', True, False),
    ('orlock-outrider-quads', 'Orlock Outrider Quads', Decimal('45.50'), 'https://www.nobleknight.com/P/2147976037/Orlock-Outrider-Quads?awid=1576', True, False),
    ('ash-waste-nomads-dustback-helamites', 'Nomads - Dustback Helamites', Decimal('47.95'), 'https://www.nobleknight.com/P/2147976035/Nomads---Dustback-Helamites?awid=1576', True, False),
    ('ash-waste-nomads-war-party', 'Nomads - War Party', Decimal('47.95'), 'https://www.nobleknight.com/P/2147976039/Nomads---War-Party?awid=1576', True, False),
    ('delaque-weapons-upgrades', 'Delaque Weapons & Upgrades', Decimal('28.95'), 'https://www.nobleknight.com/P/2147953291/Delaque-Weapons-and-Upgrades?awid=1576', True, False),
    ('hive-scum', 'Hive Scum', Decimal('19.49'), 'https://www.nobleknight.com/P/2147953292/Hive-Scum?awid=1576', True, False),
    ('van-saar-weapons-upgrades', 'Van Saar Weapons & Upgrades', Decimal('28.95'), 'https://www.nobleknight.com/P/2147931895/Van-Saar-Weapons-and-Upgrades?awid=1576', True, False),
    ('orlock-weapons-upgrades', 'Orlock Weapons & Upgrades', Decimal('27.95'), 'https://www.nobleknight.com/P/2147915851/Orlock-Weapons-Upgrades?awid=1576', True, False),
    ('delaque-nacht-ghul-psy-gheists-and-piscean-spektor', 'Nacht-Ghul & Psy-Gheists', Decimal('46.95'), 'https://www.nobleknight.com/P/2147915847/Nacht-Ghul-and-Psy-Gheists?awid=1576', True, False),
    ('cawdor-redemptionists', 'Redemptionists (2021 Edition)', Decimal('45.50'), 'https://www.nobleknight.com/P/2147892314/Redemptionists?awid=1576', True, False),
    ('goliath-weapons-upgrades', 'Goliath Weapons & Upgrades', Decimal('28.95'), 'https://www.nobleknight.com/P/2147886576/Goliath-Weapons-and-Upgrades?awid=1576', True, False),
    ('escher-weapons-upgrades', 'Escher Weapons & Upgrades', Decimal('28.95'), 'https://www.nobleknight.com/P/2147886575/Escher-Weapons-and-Upgrades?awid=1576', True, False),
    ('van-saar-archeoteks-grav-cutters', 'Archeoteks & Grav-Cutters', Decimal('47.95'), 'https://www.nobleknight.com/P/2147854508/Archeoteks-and-Sky-Cutters?awid=1576', True, False),
    ('orlock-arms-masters-and-wreckers', 'Arms Masters & Wreckers', Decimal('46.95'), 'https://www.nobleknight.com/P/2147843412/Arms-Masters-and-Wreckers?awid=1576', True, False),
    ('jotunn-h-grade-industrial-servitor-ogryns', 'Jotunn H-Grade Servitor Ogryns', Decimal('43.95'), 'https://www.nobleknight.com/P/2147820006/Jotunn-H-Grade-Servitor-Ogryns?awid=1576', True, False),
    ('escher-death-maidens-and-wyld-runners', 'Escher Death Maidens & Wyld Runners', Decimal('47.95'), 'https://www.nobleknight.com/P/2147820005/Escher-Death-Maidens-and-Wyld-Runners?awid=1576', True, False),
    ('goliath-stimmers-and-forge-born', 'Goliath Stimmers & Forgeborn', Decimal('47.95'), 'https://www.nobleknight.com/P/2147794809/Goliath-Stimmers-and-Forgeborn?awid=1576', True, False),
    ('palanite-subjugator-patrol', 'Palanite Subjugator Patrol', Decimal('47.95'), 'https://www.nobleknight.com/P/2147793083/Palanite-Subjugator-Patrol?awid=1576', True, False),
    ('luther-pattern-excavation-automata-ambot', "Luther Pattern Excavation Automata 'Ambot'", Decimal('47.95'), 'https://www.nobleknight.com/P/2147746096/Luther-Pattern-Excavation-Automata-Ambot?awid=1576', True, False),
    ('necromunda-barricades-and-objectives', 'Barricades and Objectives', None, 'https://www.nobleknight.com/P/2147682877/Barricades-and-Objectives?awid=1576', False, False),
    ('underhive-hangers-on', 'Underhive Hangers-On', None, 'https://www.nobleknight.com/P/2148383646/Underhive-Hangers-On?awid=1576', False, False),
    ('palanite-enforcer-weapons-upgrades', 'Palanite Enforcer Weapons & Upgrades', Decimal('27.95'), 'https://www.nobleknight.com/P/2148383650/Palanite-Enforcer-Weapons-and-Upgrades?awid=1576', True, False),
    ('ironhead-squat-charter-masters-and-drill-masters', 'Ironhead Squat Charter & Drill Masters', Decimal('45.95'), 'https://www.nobleknight.com/P/2148383645/Ironhead-Squat-Charter-and-Drill-Masters?awid=1576', True, False),
    ('palanite-justicars', 'Palanite Justicars', Decimal('37.95'), 'https://www.nobleknight.com/P/2148383648/Palanite-Justicars?awid=1576', True, False),
    ('ozostium-aranthus-the-divine-prince', 'Ozostium Aranthus', Decimal('34.95'), 'https://www.nobleknight.com/P/2148383651/Ozostium-Aranthus?awid=1576', True, False),
    ('zone-mortalis-ruined-underhive-sector', 'Zone Mortalis - Underhive Sector', None, 'https://www.nobleknight.com/P/2147959753/Zone-Mortalis---Underhive-Sector?awid=1576', False, False),
    ('ash-waste-nomads-weapons-upgrades', 'Ash Waste Nomads Weapons & Upgrades', Decimal('28.95'), 'https://www.nobleknight.com/P/2148282543/Ash-Waste-Nomads-Weapons-and-Upgrades?awid=1576', True, False),
    ('shadar-hunters-and-arthromite-spinewyrms', "Sha'dar Hunters and Arthromite Spinewyrms", Decimal('45.05'), 'https://www.nobleknight.com/P/2148282553/Shadar-Hunters-and-Arthromite-Spinewyrms?awid=1576', True, False),
    ('ironhead-squat-svenotar-scout-trikes', 'Ironhead Squat Svenotar Scout Trikes', Decimal('45.95'), 'https://www.nobleknight.com/P/2148250124/Ironhead-Squat-Svenotar-Scout-Trikes?awid=1576', True, False),
    ('ironhead-squat-prospectors-weapons-upgrades', 'Ironhead Squat Prospectors Weapons and Upgrades', None, 'https://www.nobleknight.com/P/2148250133/Ironhead-Squat-Prospectors-Weapons-and-Upgrades?awid=1576', False, False),
    ('ironhead-squat-prospectors-exo-kyn', 'Ironhead Squat Prospectors Exo-Kyn', Decimal('41.95'), 'https://www.nobleknight.com/P/2148250130/Ironhead-Squat-Prospectors-Exo-Kyn?awid=1576', True, False),
    ('van-saar-tek-hunters', 'Van Saar Tek Hunters', None, 'https://www.nobleknight.com/P/2148481732/Van-Saar-Tek-Hunters?awid=1576', False, False),
    ('ruined-zone-mortalis', 'Ruined Zone Mortalis', Decimal('77.95'), 'https://www.nobleknight.com/P/2148177589/Ruined-Zone-Mortalis?awid=1576', True, False),
    ('hive-data-stack-cluster', 'Hive Data Stack Cluster', Decimal('47.95'), 'https://www.nobleknight.com/P/2148177579/Hive-Data-Stack-Cluster?awid=1576', True, False),
    ('palanite-enforcer-tauros-venator', 'Palanite Enforcer Tauros Venator', Decimal('54.95'), 'https://www.nobleknight.com/P/2148104937/Palanite-Enforcer-Tauros-Venator?awid=1576', True, False),
    ('van-saar-ash-wastes-arachni-rig', 'Van Saar Ash Wastes Arachni-Rig', Decimal('47.95'), 'https://www.nobleknight.com/P/2148090329/Van-Saar-Ash-Wastes-Arachni-Rig?awid=1576', True, False),
    ('zone-mortalis-underhive-market', 'Zone Mortalis - Underhive Market', Decimal('54.95'), 'https://www.nobleknight.com/P/2147944075/Zone-Mortalis---Underhive-Market?awid=1576', True, False),
    ('cawdor-weapons-upgrades', 'Cawdor Weapons & Upgrades', Decimal('27.95'), 'https://www.nobleknight.com/P/2147937631/Cawdor-Weapons-and-Upgrades?awid=1576', True, False),
    ('zone-mortalis-gang-stronghold', 'Gang Stronghold', Decimal('95.95'), 'https://www.nobleknight.com/P/2147843413/Gang-Stronghold?awid=1576', True, False),
    ('necromunda-zone-mortalis-platforms-and-stairs', 'Zone Mortalis - Platforms and Stairs', None, 'https://www.nobleknight.com/P/2147793087/Zone-Mortalis---Platforms-and-Stairs?awid=1576', False, False),
    ('necromunda-zone-mortalis-columns-and-walls', 'Zone Mortalis - Walls & Columns', Decimal('91.95'), 'https://www.nobleknight.com/P/2147793086/Zone-Mortalis---Walls-and-Columns?awid=1576', True, False),
    ('zone-mortalis-floor-tile-set', 'Zone Mortalis Floor Tile Set', None, 'https://www.nobleknight.com/P/2147772711/Zone-Mortalis-Floor-Tile-Set?awid=1576', False, False),
    ('kal-jericho-and-scabs', 'Kal Jericho and Scabs', Decimal('35.95'), 'https://www.nobleknight.com/P/2147752426/Kal-Jericho-and-Scabs?awid=1576', True, False),
    ('trazior-pattern-sentry-guns', 'Trazior Pattern Sentry Guns', None, 'https://www.nobleknight.com/P/2148262189/Trazior-Pattern-Sentry-Guns?awid=1576', False, False),
    ('malstrain-genestealer-abomination-gang', 'Malstrain Genestealers Abomination Gang', Decimal('46.95'), 'https://www.nobleknight.com/P/2148320064/Malstrain-Genestealers-Abomination-Gang?awid=1576', True, False),
    ('corpse-grinder-cult-gang', 'Corpse Grinder Cult', Decimal('47.95'), 'https://www.nobleknight.com/P/2147793084/Corpse-Grinder-Cult?awid=1576', True, False),
    ('ironhead-squat-prospectors-gang', 'Ironhead Squat Prospectors', Decimal('45.95'), 'https://www.nobleknight.com/P/2147986340/Ironhead-Squat-Prospectors?awid=1576', True, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Necromunda products."""

    help = 'seed_nk_necromunda_prices — Noble Knight URLs for Necromunda (NM-001–NM-075)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        nk_retailer = Retailer.objects.get(slug='noble-knight-games')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(slug=slug)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            self.stdout.write(f'  seeded NK: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_necromunda_prices complete. {seeded} record(s) seeded.'
        ))
