"""
Management command: seed_mm_necromunda_prices

Seeds Miniature Market URLs for Necromunda products.

64 of 73 NM SKUs have confirmed MM listings. Omitted (not_available by
default): NM-004, NM-014, NM-018, NM-024, NM-042, NM-050, NM-051,
NM-064, NM-071.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.

Usage:
    python manage.py seed_mm_necromunda_prices
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    (
        'necromunda-hive-secundus',
        'Necromunda: Hive Secundus',
        Decimal('153.00'),
        'https://www.miniaturemarket.com/necromunda-hive-secundus-gw-301-34.html',
        True, False,
    ),
    (
        'necromunda-hive-war',
        'Necromunda: Hive War',
        Decimal('161.99'),
        'https://www.miniaturemarket.com/gw-300-08-2021.html',
        True, False,
    ),
    (
        'necromunda-core-rulebook',
        'Necromunda: Core Rulebook',
        Decimal('62.99'),
        'https://www.miniaturemarket.com/necromunda-core-rulebook-gw-300-25-2023.html',
        True, False,
    ),
    (
        'cawdor-gang',
        'Necromunda: Cawdor Gang',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-31.html',
        True, False,
    ),
    (
        'delaque-gang',
        'Necromunda: Delaque Gang',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-36.html',
        True, False,
    ),
    (
        'orlock-gang',
        'Necromunda: Orlock Gang',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-20.html',
        True, False,
    ),
    (
        'necromunda-escher-gang',
        'Necromunda: Escher Gang',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-11.html',
        True, False,
    ),
    (
        'necromunda-goliath-gang',
        'Necromunda: Goliath Gang',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-10.html',
        True, False,
    ),
    (
        'necromunda-van-saar-gang',
        'Necromunda: Van Saar Gang',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-29.html',
        True, False,
    ),
    (
        'palanite-enforcer-patrol',
        'Necromunda: Palanite Enforcer Patrol',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-45.html',
        True, False,
    ),
    (
        'promethium-tanks-on-cargo-8-ridgehauler-trailer',
        'Necromunda: Promethium Tanks on Cargo-8 Ridgehauler Trailer',
        Decimal('55.99'),
        'https://www.miniaturemarket.com/gw-301-12.html',
        True, False,
    ),
    (
        'promethium-tanks-refuelling-station',
        'Necromunda: Promethium Tanks Refuelling Station',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-301-13.html',
        True, False,
    ),
    (
        'escher-cutters',
        'Necromunda: Escher Cutters',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-301-10.html',
        True, False,
    ),
    (
        'cargo-8-ridgehauler-trailer',
        'Necromunda: Cargo-8 Ridgehauler Trailer',
        Decimal('55.99'),
        'https://www.miniaturemarket.com/gw-301-03.html',
        True, False,
    ),
    (
        'cargo-8-ridgehauler',
        'Necromunda: Cargo-8 Ridgehauler',
        Decimal('90.99'),
        'https://www.miniaturemarket.com/gw-301-02.html',
        True, False,
    ),
    # MM lists as "(Clearance)" — same product, URL is live
    (
        'thatos-pattern-extended-hab-module',
        'Necromunda: Thatos Pattern - Extended Hab Module (Clearance)',
        Decimal('95.99'),
        'https://www.miniaturemarket.com/gw-300-93.html',
        True, False,
    ),
    (
        'thatos-pattern-platforms-walkways',
        'Necromunda: Thatos Pattern - Platforms & Walkways',
        Decimal('69.99'),
        'https://www.miniaturemarket.com/gw-300-92.html',
        True, False,
    ),
    # MM lists as "(Clearance)" — same product, URL is live
    (
        'thatos-pattern-hab-module',
        'Necromunda: Thatos Pattern - Hab Module (Clearance)',
        Decimal('69.99'),
        'https://www.miniaturemarket.com/gw-300-91.html',
        True, False,
    ),
    (
        'ash-waste-nomads-dustback-helamites',
        'Necromunda: Ash Waste Nomads Dustback Helamites',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-97.html',
        True, False,
    ),
    # MM title uses "Ash Wastes" (plural) vs GW "Ash Waste" — same product
    (
        'ash-waste-nomads-war-party',
        'Necromunda: Ash Wastes Nomads War Party',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-96.html',
        True, False,
    ),
    (
        'delaque-weapons-upgrades',
        'Necromunda: Delaque Weapons & Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/gw-300-83.html',
        True, False,
    ),
    (
        'hive-scum',
        'Necromunda: Hive Scum',
        Decimal('18.99'),
        'https://www.miniaturemarket.com/gw-300-81.html',
        True, False,
    ),
    (
        'van-saar-weapons-upgrades',
        'Necromunda: Van Saar - Weapons & Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/gw-300-78.html',
        True, False,
    ),
    (
        'orlock-weapons-upgrades',
        'Necromunda: Orlock Weapons & Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/gw-300-73.html',
        True, False,
    ),
    (
        'delaque-nacht-ghul-psy-gheists-and-piscean-spektor',
        'Necromunda: Delaque Nacht-Ghul, Psy-Gheists, & Piscean Spektor',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-77.html',
        True, False,
    ),
    (
        'cawdor-redemptionists',
        'Warhammer 40K: Necromunda - Cawdor Redemptionists',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-76.html',
        True, False,
    ),
    (
        'goliath-weapons-upgrades',
        'Necromunda: Goliath Weapons & Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/gw-300-75.html',
        True, False,
    ),
    (
        'escher-weapons-upgrades',
        'Necromunda: Escher Weapons & Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/gw-300-74.html',
        True, False,
    ),
    # MM title uses "Sky-Cutters" vs GW "Grav-cutters" — same product
    (
        'van-saar-archeoteks-grav-cutters',
        'Necromunda: Van Saar Archeoteks & Sky-Cutters',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-71.html',
        True, False,
    ),
    (
        'orlock-arms-masters-and-wreckers',
        'Necromunda: Orlock Arms Masters & Wreckers',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-70.html',
        True, False,
    ),
    # MM title omits quotes and "Industrial" — same product
    (
        'jotunn-h-grade-industrial-servitor-ogryns',
        'Necromunda: Jotunn H-Grade Servitor Ogryns',
        Decimal('41.99'),
        'https://www.miniaturemarket.com/gw-300-64.html',
        True, False,
    ),
    (
        'escher-death-maidens-and-wyld-runners',
        'Necromunda: Escher Death-Maidens & Wyld Runners',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-66.html',
        True, False,
    ),
    (
        'goliath-stimmers-and-forge-born',
        'Necromunda: Goliath Stimmers & Forge-born',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-62.html',
        True, False,
    ),
    (
        'palanite-subjugator-patrol',
        'Necromunda: Palanite Subjugator Patrol',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-palanite-subjugator-patrol-gw-300-46.html',
        True, False,
    ),
    (
        'luther-pattern-excavation-automata-ambot',
        "Necromunda: Luther Pattern Excavation Automata 'Ambot'",
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-37.html',
        True, False,
    ),
    (
        'underhive-hangers-on',
        'Necromunda: Underhive Hangers-On',
        Decimal('36.99'),
        'https://www.miniaturemarket.com/Necromunda-Underhive-Hangers-On/GW-301-65-2025',
        True, False,
    ),
    (
        'palanite-enforcer-weapons-upgrades',
        'Necromunda: Palanite Enforcer Weapons and Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/Necromunda-Palanite-Enforcer-Weapons-and-Upgrades/GW-301-58-2025',
        True, False,
    ),
    # MM title uses "Charter and Drill Masters" vs GW "Charter Masters and Drill Masters"
    (
        'ironhead-squat-charter-masters-and-drill-masters',
        'Necromunda: Ironhead Squat Charter and Drill Masters',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/Necromunda-Ironhead-Squat-Charter-and-Drill-Masters/GW-301-62-2025',
        True, False,
    ),
    (
        'palanite-justicars',
        'Necromunda: Palanite Justicars',
        Decimal('36.99'),
        'https://www.miniaturemarket.com/Necromunda-Palanite-Justicars/GW-301-63-2025',
        True, False,
    ),
    (
        'ozostium-aranthus-the-divine-prince',
        'Necromunda: Ozostium Aranthus, the Divine Prince',
        Decimal('34.00'),
        'https://www.miniaturemarket.com/Necromunda-Ozostium-Aranthus-the-Divine-Prince/GW-301-61-2025',
        True, False,
    ),
    # MM title adds "Nomads" prefix — same product
    (
        'ashwing-helamites',
        'Necromunda: Nomads Ashwing Helamites',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/Necromunda-Nomads-Ashwing-Helamites/GW-301-60',
        True, False,
    ),
    (
        'palanite-enforcer-captains-sergeants',
        'Necromunda: Palanite Enforcer Captains & Sergeants',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/Necromunda-Palanite-Enforcer-Captains-Sergeants/GW-301-59',
        True, False,
    ),
    (
        'ash-waste-nomads-weapons-upgrades',
        'Necromunda: Ash Waste Nomads - Weapons & Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/necromunda-ash-waste-nomads-weapons-upgrades-gw-301-57.html',
        True, False,
    ),
    (
        'shadar-hunters-and-arthromite-spinewyrms',
        "Necromunda: Ash Waste Nomads - Sha'dar Hunters & Arthromite Spinewyrms",
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-ash-waste-nomads-shadar-hunters-arthromite-spinewyrms-gw-301-56.html',
        True, False,
    ),
    (
        'ironhead-squat-svenotar-scout-trikes',
        'Necromunda: Ironhead Squat Prospectors - Svenotar Scout Trikes',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-ironhead-squat-prospectors-svenotar-scout-trikes-gw-301-54.html',
        True, False,
    ),
    (
        'ironhead-squat-prospectors-weapons-upgrades',
        'Necromunda: Ironhead Squat Prospectors - Weapons & Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/necromunda-ironhead-squat-prospectors-weapons-upgrades-gw-301-53.html',
        True, False,
    ),
    (
        'ironhead-squat-prospectors-exo-kyn',
        'Necromunda: Ironhead Squat Prospectors - Exo-Kyn',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-ironhead-squat-prospectors-exo-kyn-gw-301-52.html',
        True, False,
    ),
    (
        'van-saar-tek-hunters',
        'Necromunda: Van Saar Tek-Hunters',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-van-saar-tek-hunters-gw-301-33.html',
        True, False,
    ),
    # MM title uses singular "Spyre Hunter" — same product
    (
        'malcadon-yeld-and-jakara-spyre-hunters',
        'Necromunda: Malcadon Yeld & Jakara Spyre Hunter',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-malcadon-yeld-jakara-spyre-hunter-gw-301-44.html',
        True, False,
    ),
    (
        'orrus-spyre-hunters',
        'Necromunda: Orrus Spyre Hunters',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-orrus-spyre-hunters-gw-301-32.html',
        True, False,
    ),
    (
        'ruined-zone-mortalis',
        'Necromunda: Ruined Zone Mortalis',
        Decimal('76.99'),
        'https://www.miniaturemarket.com/necromunda-ruined-zone-mortalis-gw-301-43.html',
        True, False,
    ),
    (
        'hive-data-stack-cluster',
        'Necromunda: Hive Data Stack Cluster',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-hive-data-stack-cluster-gw-301-36.html',
        True, False,
    ),
    # MM title spells "Taurus" vs GW "Tauros" — same product
    (
        'palanite-enforcer-tauros-venator',
        'Necromunda: Palanite Enforcer Taurus Venator',
        Decimal('51.00'),
        'https://www.miniaturemarket.com/necromunda-palanite-enforcer-taurus-venator-gw-301-27.html',
        True, False,
    ),
    (
        'van-saar-ash-wastes-arachni-rig',
        'Necromunda: Van Saar - Ash Wastes Arachni-rig',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-van-saar-ash-wastes-arachni-rig-gw-301-22.html',
        True, False,
    ),
    (
        'zone-mortalis-underhive-market',
        'Necromunda: Zone Mortalis - Underhive Market',
        Decimal('51.00'),
        'https://www.miniaturemarket.com/gw-300-85.html',
        True, False,
    ),
    (
        'cawdor-weapons-upgrades',
        'Necromunda: Cawdor - Weapons & Upgrades',
        Decimal('27.99'),
        'https://www.miniaturemarket.com/gw-300-72.html',
        True, False,
    ),
    (
        'zone-mortalis-gang-stronghold',
        'Necromunda: Zone Mortalis - Gang Stronghold',
        Decimal('90.99'),
        'https://www.miniaturemarket.com/gw-300-69.html',
        True, False,
    ),
    (
        'necromunda-zone-mortalis-platforms-and-stairs',
        'Necromunda: Zone Mortalis - Platforms & Stairs',
        Decimal('69.99'),
        'https://www.miniaturemarket.com/necromunda-zone-mortalis-platforms-stairs-gw-300-49.html',
        True, False,
    ),
    (
        'necromunda-zone-mortalis-columns-and-walls',
        'Necromunda: Zone Mortalis - Columns & Walls',
        Decimal('86.99'),
        'https://www.miniaturemarket.com/necromunda-zone-mortalis-columns-walls-gw-300-48.html',
        True, False,
    ),
    (
        'zone-mortalis-floor-tile-set',
        'Necromunda: Zone Mortalis - Floor Tile Set',
        Decimal('72.99'),
        'https://www.miniaturemarket.com/gw-300-59.html',
        True, False,
    ),
    (
        'trazior-pattern-sentry-guns',
        'Necromunda: Trazior Pattern Sentry Guns',
        Decimal('36.99'),
        'https://www.miniaturemarket.com/necromunda-trazior-pattern-sentry-guns-gw-301-35.html',
        True, False,
    ),
    (
        'malstrain-genestealer-abomination-gang',
        'Necromunda: Malstrain Genestealer Abomination Gang',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/necromunda-malstrain-genestealer-abomination-gang-gw-301-31.html',
        True, False,
    ),
    (
        'corpse-grinder-cult-gang',
        'Necromunda: Corpse Grinder Cult Gang',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-300-47.html',
        True, False,
    ),
    (
        'ironhead-squat-prospectors-gang',
        'Necromunda: Ironhead Squat Prospectors',
        Decimal('45.99'),
        'https://www.miniaturemarket.com/gw-301-01.html',
        True, False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Necromunda products."""

    help = 'seed_mm_necromunda_prices — Miniature Market URLs for Necromunda (64 of 73 SKUs)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        mm_retailer = Retailer.objects.get(slug='miniature-market')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(slug=slug)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm_retailer,
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
            self.stdout.write(f'  seeded MM: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_necromunda_prices complete. {seeded} record(s) seeded.'
        ))
