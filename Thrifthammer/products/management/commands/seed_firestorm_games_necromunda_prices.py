"""
Seed Firestorm Games UK prices for Necromunda.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. Only
games-workshop-uk writes msrp_gbp.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.
RRP is only used as a matching aid to confirm which DB SKU a listing
corresponds to (it should equal Product.msrp_gbp for the matched SKU).

Necromunda products in the DB all share a single flat Faction ('Necromunda'
-- not gang-specific); matching was done against the full flat NM-XXX
product list in one pass.

https://www.firestormgames.co.uk/wargames-miniatures/necromunda-underhive
67/73 matched. Gaps (not carried by Firestorm): NM-001 Hive Secundus,
NM-002 Hive War, NM-003 Core Rulebook (core book/campaign supplements
aren't in Firestorm's Necromunda range), NM-016 Promethium Tanks
Refuelling Station, NM-023 Thatos Pattern: Hab Module (only the
"Extended" and "Fortified" variants are carried), NM-065 Zone Mortalis:
Underhive Market.

Small RRP/msrp_gbp mismatches (matched anyway, price used is still the
Firestorm sale price): NM-048 Ashwing Helamites (RRP £31.50 vs msrp
£32.50), NM-049 Palanite Enforcer Captains & Sergeants (RRP £31.50 vs
msrp £32.50). NM-010/011/012 (Escher/Goliath/Van Saar Gang) have
msrp_gbp=None in the DB (not yet synced by games-workshop-uk) -- matched
on name/price consistency with sibling Cawdor/Delaque/Orlock Gang
listings (all £32.50 RRP).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

_PRICES = [
    ('NM-004', "Enforcer 'Sanctioner' Pattern Automata", Decimal('30.88'),
     'https://www.firestormgames.co.uk/necromunda:-enforcer-sanctioner-pattern-automata?aff=6a4ab07d1c6f9'),
    ('NM-006', 'Cawdor Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda-house-cawdor-gang?aff=6a4ab07d1c6f9'),
    ('NM-007', 'Delaque Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-delaque-gang?aff=6a4ab07d1c6f9'),
    ('NM-008', 'Orlock Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda-orlock-gang?aff=6a4ab07d1c6f9'),
    ('NM-010', 'Necromunda Escher Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda-escher-gang?aff=6a4ab07d1c6f9'),
    ('NM-011', 'Necromunda Goliath Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda-goliath-gang?aff=6a4ab07d1c6f9'),
    ('NM-012', 'Necromunda Van Saar Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda-van-saar-gang?aff=6a4ab07d1c6f9'),
    ('NM-013', 'Palanite Enforcer Patrol', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-palanite-enforcer-patrol?aff=6a4ab07d1c6f9'),
    ('NM-014', 'Cawdor Ridge Walkers', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-cawdor-ridge-walkers?aff=6a4ab07d1c6f9'),
    ('NM-015', 'Promethium Tanks on Cargo-8 Ridgehauler Trailer', Decimal('35.20'),
     'https://www.firestormgames.co.uk/necromunda---promethium-tanks-on-cargo-8-trailer?aff=6a4ab07d1c6f9'),
    ('NM-017', 'Escher Cutters', Decimal('28.60'),
     'https://www.firestormgames.co.uk/escher-cutters?aff=6a4ab07d1c6f9'),
    ('NM-018', 'Cargo-8 Ridgehauler Gunner Frames', Decimal('17.57'),
     'https://www.firestormgames.co.uk/cargo-8-ridgehauler-gunner-frames?aff=6a4ab07d1c6f9'),
    ('NM-019', 'Cargo-8 Ridgehauler Trailer', Decimal('35.20'),
     'https://www.firestormgames.co.uk/necromunda---cargo-8-ridgehauler-trailer?aff=6a4ab07d1c6f9'),
    ('NM-020', 'Cargo-8 Ridgehauler', Decimal('56.76'),
     'https://www.firestormgames.co.uk/necromunda---cargo-8-ridgehauler?aff=6a4ab07d1c6f9'),
    ('NM-021', 'Thatos Pattern: Extended Hab Module', Decimal('59.40'),
     'https://www.firestormgames.co.uk/thatos-pattern---extended-hab-module?aff=6a4ab07d1c6f9'),
    ('NM-022', 'Thatos Pattern: Platforms & Walkways', Decimal('43.56'),
     'https://www.firestormgames.co.uk/thatos-pattern---platforms--walkways?aff=6a4ab07d1c6f9'),
    ('NM-024', 'Orlock Outrider Quads', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-orlock-outrider-quads?aff=6a4ab07d1c6f9'),
    ('NM-025', 'Ash Waste Nomads Dustback Helamites', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-ash-wastes-nomads-dustback-helamites?aff=6a4ab07d1c6f9'),
    ('NM-026', 'Ash Waste Nomads War Party', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-ash-wastes-nomads-war-party?aff=6a4ab07d1c6f9'),
    ('NM-027', 'Delaque Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/necromunda:-delaque-weapons?aff=6a4ab07d1c6f9'),
    ('NM-028', 'Hive Scum', Decimal('12.32'),
     'https://www.firestormgames.co.uk/necromunda:-hive-scum?aff=6a4ab07d1c6f9'),
    ('NM-029', 'Van Saar Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/necromunda:-van-saar-weapons-and-upgrades?aff=6a4ab07d1c6f9'),
    ('NM-030', 'Orlock Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/necromunda:-orlock-weapons-upgrades?aff=6a4ab07d1c6f9'),
    ('NM-031', 'Delaque Nacht-Ghul, Psy-Gheists and Piscean Spektor', Decimal('28.60'),
     'https://www.firestormgames.co.uk/delaque-nacht-ghul-and-psy-gheists?aff=6a4ab07d1c6f9'),
    ('NM-032', 'Cawdor Redemptionists', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-cawdor-redemptionists?aff=6a4ab07d1c6f9'),
    ('NM-033', 'Goliath Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/necromunda:-goliath-weapons--upgrades?aff=6a4ab07d1c6f9'),
    ('NM-034', 'Escher Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/necromunda:-escher-weapons--upgrades?aff=6a4ab07d1c6f9'),
    ('NM-035', 'Van Saar Archeoteks & Grav-cutters', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-van-saar-archeoteks--grav-cutters?aff=6a4ab07d1c6f9'),
    ('NM-036', 'Orlock Arms Masters and Wreckers', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-orlock-arms-masters-and-wreckers?aff=6a4ab07d1c6f9'),
    ('NM-037', "'Jotunn' H-Grade Industrial Servitor Ogryns", Decimal('26.40'),
     'https://www.firestormgames.co.uk/necromunda:-jotunn-h-grade-servitor-ogryns?aff=6a4ab07d1c6f9'),
    ('NM-038', 'Escher Death-maidens and Wyld Runners', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-escher-death-maidens-and-wyld-runners?aff=6a4ab07d1c6f9'),
    ('NM-039', 'Goliath Stimmers and Forge-born', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-goliath-stimmers--forgeborn?aff=6a4ab07d1c6f9'),
    ('NM-040', 'Palanite Subjugator Patrol', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-palanite-subjugator-patrol?aff=6a4ab07d1c6f9'),
    ('NM-041', 'Luther Pattern Excavation Automata "Ambot"', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-ambot-automata?aff=6a4ab07d1c6f9'),
    ('NM-042', 'Necromunda Barricades and Objectives', Decimal('28.50'),
     'https://www.firestormgames.co.uk/necromunda:-barricades-and-objectives?aff=6a4ab07d1c6f9'),
    ('NM-043', 'Underhive Hangers-on', Decimal('23.76'),
     'https://www.firestormgames.co.uk/necromunda:-underhive-hangers-on?aff=6a4ab07d1c6f9'),
    ('NM-044', 'Palanite Enforcer Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/necromunda:-enforcer-weapons--upgrades?aff=6a4ab07d1c6f9'),
    ('NM-045', 'Ironhead Squat Charter Masters and Drill Masters', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-ironhead-squat-charter--drill-masters?aff=6a4ab07d1c6f9'),
    ('NM-046', 'Palanite Justicars', Decimal('23.76'),
     'https://www.firestormgames.co.uk/necromunda:-palanite-justicars?aff=6a4ab07d1c6f9'),
    ('NM-047', 'Ozostium Aranthus, the Divine Prince', Decimal('22.00'),
     'https://www.firestormgames.co.uk/necromunda:-ozostium-aranthus-the-divine-prince?aff=6a4ab07d1c6f9'),
    ('NM-048', 'Ashwing Helamites', Decimal('27.72'),
     'https://www.firestormgames.co.uk/necromunda:-nomads-ashwing-helamites?aff=6a4ab07d1c6f9'),
    ('NM-049', 'Palanite Enforcer Captains & Sergeants', Decimal('27.72'),
     'https://www.firestormgames.co.uk/necromunda:-palanite-enforcer-captains--sergeants?aff=6a4ab07d1c6f9'),
    ('NM-050', 'Zone Mortalis: Ruined Underhive Sector', Decimal('100.22'),
     'https://www.firestormgames.co.uk/zone-mortalis:-ruined-underhive-sector?aff=6a4ab07d1c6f9'),
    ('NM-051', 'Thatos Pattern Fortified Hab Module', Decimal('66.03'),
     'https://www.firestormgames.co.uk/necromunda:-thatos-pattern-fortified-hab-module?aff=6a4ab07d1c6f9'),
    ('NM-052', 'Ash Waste Nomads: Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/ash-waste-nomads-weapons--upgrades?aff=6a4ab07d1c6f9'),
    ('NM-053', "Sha'dar Hunters and Arthromite Spinewyrms", Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda-shadar-hunters--arthromite-spinewyrms?aff=6a4ab07d1c6f9'),
    ('NM-054', 'Ironhead Squat Svenotar Scout Trikes', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-ironhead-squat-svenotar-scout-trikes?aff=6a4ab07d1c6f9'),
    ('NM-055', 'Ironhead Squat Prospectors Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/necromunda:-squat-propectors-weapons-and-upgrades?aff=6a4ab07d1c6f9'),
    ('NM-056', 'Ironhead Squat Prospectors Exo-kyn', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-squat-prospectors-exo-kyn?aff=6a4ab07d1c6f9'),
    ('NM-057', 'Van Saar Tek-hunters', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-van-saar-tek-hunters?aff=6a4ab07d1c6f9'),
    ('NM-058', 'Malcadon, Yeld, and Jakara Spyre Hunters', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-malcadon-yeld--jakara-spyre-hunter?aff=6a4ab07d1c6f9'),
    ('NM-059', 'Orrus Spyre Hunters', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-orrus-spyre-hunters?aff=6a4ab07d1c6f9'),
    ('NM-060', 'Ruined Zone Mortalis', Decimal('47.96'),
     'https://www.firestormgames.co.uk/necromunda:-ruined-zone-mortalis?aff=6a4ab07d1c6f9'),
    ('NM-061', 'Hive Data Stack Cluster', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-hive-data-stack-cluster?aff=6a4ab07d1c6f9'),
    ('NM-062', 'Palanite Enforcer Tauros Venator', Decimal('33.44'),
     'https://www.firestormgames.co.uk/necromunda:-palanite-enforcer-taurus-venator?aff=6a4ab07d1c6f9'),
    ('NM-063', 'Van Saar Ash Wastes Arachni-rig', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-van-saar-ash-wastes-arachnirig?aff=6a4ab07d1c6f9'),
    ('NM-064', 'Goliath Maulters', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda---goliath-maulers?aff=6a4ab07d1c6f9'),
    ('NM-066', 'Cawdor Weapons & Upgrades', Decimal('16.28'),
     'https://www.firestormgames.co.uk/necromunda:-cawdor-weapons--upgrades?aff=6a4ab07d1c6f9'),
    ('NM-067', 'Zone Mortalis: Gang Stronghold', Decimal('56.76'),
     'https://www.firestormgames.co.uk/necromunda:-zone-mortalis-gang-stronghold?aff=6a4ab07d1c6f9'),
    ('NM-068', 'Necromunda Zone Mortalis Platforms and Stairs', Decimal('43.56'),
     'https://www.firestormgames.co.uk/necromunda:-zone-mortalis-platforms-and-stairs?aff=6a4ab07d1c6f9'),
    ('NM-069', 'Necromunda Zone Mortalis Columns and Walls', Decimal('54.56'),
     'https://www.firestormgames.co.uk/necromunda:-zone-mortalis-columns-and-walls?aff=6a4ab07d1c6f9'),
    ('NM-070', 'Zone Mortalis: Floor Tile Set', Decimal('45.76'),
     'https://www.firestormgames.co.uk/necromunda:-zone-mortalis-floor-tile-set?aff=6a4ab07d1c6f9'),
    ('NM-071', 'Kal Jericho and Scabs', Decimal('23.75'),
     'https://www.firestormgames.co.uk/necromunda:-kal-jericho-and-scabs?aff=6a4ab07d1c6f9'),
    ('NM-072', 'Trazior Pattern Sentry Guns', Decimal('23.76'),
     'https://www.firestormgames.co.uk/necromunda:-trazior-pattern-sentry-guns?aff=6a4ab07d1c6f9'),
    ('NM-073', 'Malstrain Genestealer Abomination Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-malstrain-genestealer-abomination-gang?aff=6a4ab07d1c6f9'),
    ('NM-074', 'Corpse Grinder Cult Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda:-corpse-grinder-cult?aff=6a4ab07d1c6f9'),
    ('NM-075', 'Ironhead Squat Prospectors Gang', Decimal('28.60'),
     'https://www.firestormgames.co.uk/necromunda---ironhead-squat-prospectors-?aff=6a4ab07d1c6f9'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Necromunda. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': 'https://www.firestormgames.co.uk/?aff=6a4ab07d1c6f9',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for sku, label, gbp_price, url in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
                skipped += 1
                continue

            for product in products:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'currency': 'GBP',
                        'url': url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Firestorm Games Necromunda prices. Skipped: {skipped}.'
            )
        )
