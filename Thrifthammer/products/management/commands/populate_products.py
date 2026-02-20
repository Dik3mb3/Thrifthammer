"""
Management command: populate_products

Creates sample categories, factions, retailers, products, and current prices
so the site can be tested immediately after setup without real scraper data.

Usage:
    python manage.py populate_products
    python manage.py populate_products --clear    # wipe existing data first

All data is idempotent: running the command twice won't create duplicates
because we use get_or_create / update_or_create throughout.
"""

import decimal
import random

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice, PriceHistory
from products.models import Category, Faction, Product, Retailer


class Command(BaseCommand):
    """Populate the database with realistic sample Warhammer product data."""

    help = 'Populate database with sample Warhammer products and prices for testing.'

    def add_arguments(self, parser):
        """Register command-line arguments."""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing products, categories, factions, retailers, and prices first.',
        )

    def handle(self, *args, **options):
        """Entry point: orchestrate all seed data creation."""
        if options['clear']:
            self.stdout.write('Clearing existing data…')
            CurrentPrice.objects.all().delete()
            PriceHistory.objects.all().delete()
            Product.objects.all().delete()
            Faction.objects.all().delete()
            Category.objects.all().delete()
            Retailer.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared.'))

        categories = self._create_categories()
        factions = self._create_factions(categories)
        retailers = self._create_retailers()
        products = self._create_products(categories, factions)
        extended = self._create_extended_products(categories, factions)
        all_products = products + extended
        self._create_prices(all_products, retailers)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created/updated:\n'
            f'  {len(categories)} categories\n'
            f'  {len(factions)} factions\n'
            f'  {len(retailers)} retailers\n'
            f'  {len(all_products)} products ({len(products)} base + {len(extended)} extended)\n'
            f'  {CurrentPrice.objects.count()} current prices\n'
        ))

    # -------------------------------------------------------------------------
    # Category seed data
    # -------------------------------------------------------------------------

    def _create_categories(self):
        """Create the top-level product categories."""
        self.stdout.write('Creating categories…')
        category_data = [
            ('Warhammer 40,000', 'The grimdark far future. Space battles, aliens, and chaos.'),
            ('Age of Sigmar', 'Fantasy realm-hopping battles in the Mortal Realms.'),
            ('Horus Heresy', 'The galaxy-spanning civil war of the 31st Millennium.'),
            ('Paint & Supplies', 'Citadel paints, brushes, and modelling supplies.'),
            ('Kill Team', 'Skirmish-scale combat in the 41st Millennium and Mortal Realms.'),
        ]
        categories = {}
        for name, description in category_data:
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name), 'description': description},
            )
            categories[name] = cat
            status = 'created' if created else 'exists'
            self.stdout.write(f'  [{status}] {name}')
        return categories

    # -------------------------------------------------------------------------
    # Faction seed data
    # -------------------------------------------------------------------------

    def _create_factions(self, categories):
        """Create factions grouped by category."""
        self.stdout.write('Creating factions…')
        faction_data = [
            # (name, category_name)
            # ── Warhammer 40,000 ──
            ('Space Marines', 'Warhammer 40,000'),
            ('Blood Angels', 'Warhammer 40,000'),
            ('Dark Angels', 'Warhammer 40,000'),
            ('Space Wolves', 'Warhammer 40,000'),
            ('Ultramarines', 'Warhammer 40,000'),
            ('Black Templars', 'Warhammer 40,000'),
            ('Deathwatch', 'Warhammer 40,000'),
            ('Grey Knights', 'Warhammer 40,000'),
            ('Chaos Space Marines', 'Warhammer 40,000'),
            ('Death Guard', 'Warhammer 40,000'),
            ('Thousand Sons', 'Warhammer 40,000'),
            ('World Eaters', 'Warhammer 40,000'),
            ('Tyranids', 'Warhammer 40,000'),
            ('Genestealer Cults', 'Warhammer 40,000'),
            ('Necrons', 'Warhammer 40,000'),
            ('Orks', 'Warhammer 40,000'),
            ("T'au Empire", 'Warhammer 40,000'),
            ('Astra Militarum', 'Warhammer 40,000'),
            ('Adeptus Mechanicus', 'Warhammer 40,000'),
            ('Drukhari', 'Warhammer 40,000'),
            ('Craftworlds', 'Warhammer 40,000'),
            ('Harlequins', 'Warhammer 40,000'),
            ('Leagues of Votann', 'Warhammer 40,000'),
            ('Custodes', 'Warhammer 40,000'),
            ('Sisters of Battle', 'Warhammer 40,000'),
            # ── Age of Sigmar ──
            ('Stormcast Eternals', 'Age of Sigmar'),
            ('Skaven', 'Age of Sigmar'),
            ('Nighthaunt', 'Age of Sigmar'),
            ('Ossiarch Bonereapers', 'Age of Sigmar'),
            ('Flesh-Eater Courts', 'Age of Sigmar'),
            ('Gloomspite Gitz', 'Age of Sigmar'),
            ('Orruk Warclans', 'Age of Sigmar'),
            ('Daughters of Khaine', 'Age of Sigmar'),
            ('Lumineth Realm-lords', 'Age of Sigmar'),
            ('Cities of Sigmar', 'Age of Sigmar'),
            ('Slaves to Darkness', 'Age of Sigmar'),
            ('Blades of Khorne', 'Age of Sigmar'),
            ('Maggotkin of Nurgle', 'Age of Sigmar'),
            ('Disciples of Tzeentch', 'Age of Sigmar'),
        ]
        factions = {}
        for name, cat_name in faction_data:
            cat = categories.get(cat_name)
            if not cat:
                continue
            faction, created = Faction.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name), 'category': cat},
            )
            if not created and faction.category != cat:
                # Keep category in sync in case it changed
                faction.category = cat
                faction.save()
            factions[name] = faction
            status = 'created' if created else 'exists'
            self.stdout.write(f'  [{status}] {name}')
        return factions

    # -------------------------------------------------------------------------
    # Retailer seed data
    # -------------------------------------------------------------------------

    def _create_retailers(self):
        """Create the retailers we'll compare prices across."""
        self.stdout.write('Creating retailers…')
        retailer_data = [
            {
                'name': 'Games Workshop',
                'website': 'https://www.games-workshop.com',
                'country': 'US',
            },
            {
                'name': 'Miniature Market',
                'website': 'https://www.miniaturemarket.com',
                'country': 'US',
            },
            {
                'name': 'Noble Knight Games',
                'website': 'https://www.nobleknight.com',
                'country': 'US',
            },
            {
                'name': 'eBay',
                'website': 'https://www.ebay.com',
                'country': 'US',
            },
            {
                'name': 'Amazon',
                'website': 'https://www.amazon.com',
                'country': 'US',
            },
        ]
        retailers = {}
        for data in retailer_data:
            retailer, created = Retailer.objects.get_or_create(
                name=data['name'],
                defaults={
                    'slug': slugify(data['name']),
                    'website': data['website'],
                    'country': data['country'],
                    'is_active': True,
                },
            )
            retailers[data['name']] = retailer
            status = 'created' if created else 'exists'
            self.stdout.write(f'  [{status}] {data["name"]}')
        return retailers

    # -------------------------------------------------------------------------
    # Product seed data
    # -------------------------------------------------------------------------

    def _create_products(self, categories, factions):
        """Create 50 sample products with realistic names, descriptions, and prices."""
        self.stdout.write('Creating products…')

        # (name, category_name, faction_name, gw_sku, msrp, description)
        product_data = [
            # ---- Space Marines ----
            (
                'Space Marine Intercessors',
                'Warhammer 40,000', 'Space Marines',
                '48-75', decimal.Decimal('40.00'),
                'Five multi-part plastic Intercessors armed with bolt rifles. '
                'The backbone of any Space Marine force, these elite warriors '
                'are clad in Mark X Tacticus armour.',
            ),
            (
                'Space Marine Assault Intercessors',
                'Warhammer 40,000', 'Space Marines',
                '48-76', decimal.Decimal('40.00'),
                'Five Assault Intercessors armed with heavy bolt pistols and '
                'Astartes chainswords — perfect for close-range engagements.',
            ),
            (
                'Space Marine Impulsor',
                'Warhammer 40,000', 'Space Marines',
                '48-94', decimal.Decimal('57.50'),
                'A fast-moving dedicated transport skimmer for Space Marine '
                'infantry. Mounts a variety of weapons and shield domes.',
            ),
            (
                'Space Marine Repulsor',
                'Warhammer 40,000', 'Space Marines',
                '48-85', decimal.Decimal('75.00'),
                'A powerful grav-tank that can transport ten Primaris Space Marines '
                'while laying down devastating fire support.',
            ),
            (
                'Space Marine Primaris Captain',
                'Warhammer 40,000', 'Space Marines',
                '48-62', decimal.Decimal('22.50'),
                'A single-pose plastic Primaris Captain in Mark X Gravis armour, '
                'armed with a master-crafted heavy bolt rifle.',
            ),
            (
                'Space Marine Combat Patrol',
                'Warhammer 40,000', 'Space Marines',
                '71-02', decimal.Decimal('105.00'),
                'A complete combat patrol force: Primaris Captain, Redemptor '
                'Dreadnought, Intercessors, and Outriders.',
            ),
            # ---- Blood Angels ----
            (
                'Blood Angels Death Company Marines',
                'Warhammer 40,000', 'Blood Angels',
                '41-07', decimal.Decimal('40.00'),
                'Five plastic Death Company Marines in iconic black armour, '
                'driven to frenzy by the Black Rage. Armed with bolt pistols '
                'and chainswords.',
            ),
            (
                'Blood Angels Sanguinary Guard',
                'Warhammer 40,000', 'Blood Angels',
                '41-06', decimal.Decimal('40.00'),
                'Five elite warriors in gilded Artificer armour equipped with '
                'glaives encarmine and angelus boltguns.',
            ),
            # ---- Ultramarines ----
            (
                'Ultramarines Honour Guard',
                'Warhammer 40,000', 'Ultramarines',
                '55-16', decimal.Decimal('35.00'),
                'Two dedicated bodyguards for Marneus Calgar, clad in ornate '
                'Terminator armour.',
            ),
            # ---- Chaos Space Marines ----
            (
                'Chaos Space Marines',
                'Warhammer 40,000', 'Chaos Space Marines',
                '43-06', decimal.Decimal('40.00'),
                'Ten plastic Chaos Space Marines in corrupted power armour. '
                'Includes weapon options for aspiring champion and special weapons.',
            ),
            (
                'Chaos Predator Annihilator',
                'Warhammer 40,000', 'Chaos Space Marines',
                '43-09', decimal.Decimal('57.50'),
                'A heavy tank armed with twin lascannons, the Predator Annihilator '
                'hunts enemy vehicles and monstrous creatures.',
            ),
            (
                'Chaos Space Marines Combat Patrol',
                'Warhammer 40,000', 'Chaos Space Marines',
                '71-06', decimal.Decimal('105.00'),
                'A ready-to-play patrol force including a Dark Apostle, '
                'Chaos Space Marines, and Obliterators.',
            ),
            # ---- Tyranids ----
            (
                'Tyranid Warriors',
                'Warhammer 40,000', 'Tyranids',
                '51-08', decimal.Decimal('42.50'),
                'Three multi-part plastic Tyranid Warriors, adaptable mid-tier '
                'synapse creatures with a variety of biomorph options.',
            ),
            (
                'Tyranid Termagants',
                'Warhammer 40,000', 'Tyranids',
                '51-16', decimal.Decimal('30.00'),
                'A swarm of twelve Termagants armed with fleshborers, the '
                'expendable chitin-clad troops of Hive Fleet invasions.',
            ),
            (
                'Tyranid Carnifex',
                'Warhammer 40,000', 'Tyranids',
                '51-06', decimal.Decimal('45.00'),
                'One enormous Carnifex monster with a wide selection of weapons '
                'and biomorphs. A terrifying centrepiece model.',
            ),
            (
                'Tyranid Hive Tyrant',
                'Warhammer 40,000', 'Tyranids',
                '51-04', decimal.Decimal('45.00'),
                'The synapse linchpin of any Tyranid swarm. Can be built as '
                'a winged Hive Tyrant or a walking Tyrant with various weapons.',
            ),
            (
                'Tyranid Combat Patrol',
                'Warhammer 40,000', 'Tyranids',
                '71-19', decimal.Decimal('105.00'),
                'Start a Tyranid collection: Hive Tyrant, Tyranid Warriors, '
                'Termagants, Ripper Swarms, and a Carnifex.',
            ),
            # ---- Necrons ----
            (
                'Necron Warriors',
                'Warhammer 40,000', 'Necrons',
                '49-06', decimal.Decimal('32.50'),
                'Ten plastic Necron Warriors with options for gauss flayers '
                'or gauss reapers. The immortal core of any Necron Dynasty.',
            ),
            (
                'Necron Immortals',
                'Warhammer 40,000', 'Necrons',
                '49-10', decimal.Decimal('35.00'),
                'Five Necron Immortals — harder to kill than Warriors, armed '
                'with tesla carbines or gauss blasters.',
            ),
            (
                'Necron Overlord',
                'Warhammer 40,000', 'Necrons',
                '49-03', decimal.Decimal('25.00'),
                'A single plastic Necron Overlord in ornate war-plate, armed '
                'with a staff of light and resurrection orb.',
            ),
            (
                'Necron Monolith',
                'Warhammer 40,000', 'Necrons',
                '49-08', decimal.Decimal('100.00'),
                'The iconic Necron super-heavy construct. A massive plastic kit '
                'that dominates any battlefield.',
            ),
            (
                'Necron Combat Patrol',
                'Warhammer 40,000', 'Necrons',
                '71-20', decimal.Decimal('105.00'),
                'Everything to start a Necron force: Overlord, Necron Warriors, '
                'Scarab Swarms, Immortals, and a Doomsday Ark.',
            ),
            # ---- Orks ----
            (
                'Ork Boyz',
                'Warhammer 40,000', 'Orks',
                '50-10', decimal.Decimal('30.00'),
                'Ten plastic Ork Boyz with an enormous variety of weapons '
                'and poses. The mob that forms the core of any Waaagh!',
            ),
            (
                'Ork Warboss',
                'Warhammer 40,000', 'Orks',
                '50-05', decimal.Decimal('27.50'),
                'The biggest, meanest Ork in the mob. A single plastic Warboss '
                'bristling with crude but devastating weapons.',
            ),
            (
                'Ork Lootas',
                'Warhammer 40,000', 'Orks',
                '50-14', decimal.Decimal('35.00'),
                'Five Ork Lootas with deff guns — scavenged long-range heavy '
                'weapons that fire random shots each turn.',
            ),
            # ---- T\'au Empire ----
            (
                "T'au Fire Warriors",
                'Warhammer 40,000', "T'au Empire",
                '56-06', decimal.Decimal('32.50'),
                "Ten T'au Fire Warriors with strike team pulse rifles or "
                "breacher team pulse blasters. Highly versatile troops.",
            ),
            (
                "T'au Broadside Battlesuit",
                'Warhammer 40,000', "T'au Empire",
                '56-13', decimal.Decimal('37.50'),
                "A heavy T'au support battlesuit armed with twin heavy rail "
                "rifles or twin plasma rifles for tank-hunting duties.",
            ),
            # ---- Age of Sigmar ----
            (
                'Stormcast Eternals Liberators',
                'Age of Sigmar', 'Stormcast Eternals',
                '96-11', decimal.Decimal('42.50'),
                'Five Liberators in sigmarite armour with warhammers and '
                'shields. The foundational Stormcast Eternal troops.',
            ),
            (
                'Stormcast Eternals Judicators',
                'Age of Sigmar', 'Stormcast Eternals',
                '96-12', decimal.Decimal('42.50'),
                'Five ranged Stormcast warriors armed with skybolt bows or '
                'boltstorm crossbows. Excellent objective controllers.',
            ),
            (
                'Stormcast Eternals Lord-Celestant',
                'Age of Sigmar', 'Stormcast Eternals',
                '96-14', decimal.Decimal('27.50'),
                'A single Lord-Celestant in Sigmarite armour, the classic '
                'Stormcast Eternal commander on foot.',
            ),
            (
                'Stormcast Eternals Vanguard',
                'Age of Sigmar', 'Stormcast Eternals',
                '71-55', decimal.Decimal('105.00'),
                'A complete Vanguard starter: Lord-Commander Bastian Carthalos '
                'plus Praetors and Vindictors.',
            ),
            (
                'Skaven Clanrats',
                'Age of Sigmar', 'Skaven',
                '90-10', decimal.Decimal('30.00'),
                'Twenty Skaven Clanrats armed with hand weapons or rusty spears. '
                'Swarm the enemy with sheer numbers.',
            ),
            (
                'Skaven Stormfiends',
                'Age of Sigmar', 'Skaven',
                '90-17', decimal.Decimal('55.00'),
                'Three Stormfiend monsters, each a hulking rat-ogre fused with '
                'multiple weapons including ratling cannons and grinderfists.',
            ),
            # ---- Horus Heresy ----
            (
                'MKVI Tactical Squad',
                'Horus Heresy', None,
                'HA-001', decimal.Decimal('55.00'),
                'Twenty Space Marine legionaries in Mark VI Corvus armour, '
                'the definitive Horus Heresy infantry kit.',
            ),
            (
                'Contemptor Dreadnought',
                'Horus Heresy', None,
                'HA-002', decimal.Decimal('42.50'),
                'A single Contemptor Dreadnought with multi-melta or assault '
                'cannon options — a powerful Heresy-era walker.',
            ),
            # ---- Paints & Supplies ----
            (
                'Citadel Contrast Paint',
                'Paint & Supplies', None,
                'CP-001', decimal.Decimal('7.55'),
                'A single Citadel Contrast paint pot (18ml). One coat over '
                'a white or light grey primer gives shaded colour instantly.',
            ),
            (
                'Citadel Contrast Paint Bundle x10',
                'Paint & Supplies', None,
                'CP-010', decimal.Decimal('69.99'),
                'Ten Citadel Contrast paints of your choice at a saving over '
                'buying individually.',
            ),
            (
                'Citadel Base Paint',
                'Paint & Supplies', None,
                'BP-001', decimal.Decimal('4.55'),
                'A single Citadel Base paint (12ml). Formulated for smooth '
                'coverage over bare plastic or primer in a single coat.',
            ),
            (
                'Citadel Shade (Nuln Oil)',
                'Paint & Supplies', None,
                'SP-001', decimal.Decimal('5.50'),
                'The essential Citadel Shade — Nuln Oil (24ml). Flows into '
                'recesses to add instant depth and shadow.',
            ),
            (
                'Citadel Painting Handle',
                'Paint & Supplies', None,
                'PH-001', decimal.Decimal('12.00'),
                'A handheld painting grip with a magnetic base that attaches '
                'to any Citadel model.',
            ),
            (
                'Citadel Texture Paint (Astrogranite)',
                'Paint & Supplies', None,
                'TP-001', decimal.Decimal('6.80'),
                'A thick Texture paint that creates stone and rubble basing '
                'effects quickly without modelling materials.',
            ),
            # ---- Starter Sets (40K) ----
            (
                'Leviathan (10th Edition Starter Set)',
                'Warhammer 40,000', None,
                '40-02', decimal.Decimal('145.00'),
                'The huge 10th Edition launch box. Contains Space Marine '
                'and Tyranid forces, a 376-page hardback rulebook, dice, '
                'and terrain. Superb value.,'
            ),
            (
                'Warhammer 40,000 Starter Set',
                'Warhammer 40,000', None,
                '40-03', decimal.Decimal('50.00'),
                'A compact starter with push-fit Space Marines and Tyranids, '
                'a small rulebook, and all you need to play your first game.,'
            ),
            (
                'Combat Patrol: Space Marines',
                'Warhammer 40,000', 'Space Marines',
                '71-02', decimal.Decimal('105.00'),
                'A ready-to-play Combat Patrol force of Space Marines: '
                'Captain, Redemptor Dreadnought, Intercessors, and Outriders.,'
            ),
            # ---- Starter Sets (AoS) ----
            (
                'Age of Sigmar Warrior Starter Set',
                'Age of Sigmar', None,
                '80-15', decimal.Decimal('35.00'),
                'The perfect introduction to Age of Sigmar: Stormcast Eternals '
                'vs Kruleboyz Orks, with a Getting Started guide.,'
            ),
            # ---- Horus Heresy Starter ----
            (
                'Horus Heresy: Age of Darkness',
                'Horus Heresy', None,
                'HH-001', decimal.Decimal('180.00'),
                'The massive Horus Heresy launch box. 54 plastic Mk VI Space '
                'Marines, vehicles, and the complete rulebook.,'
            ),
            # ---- Kill Team ----
            (
                'Kill Team: Nightmare',
                'Kill Team', None,
                'KT-001', decimal.Decimal('130.00'),
                'A Kill Team box with Chaos Legionaries vs Wyrmblade Genestealer '
                'Cult operatives, terrain, and full Kill Team rules.,'
            ),
            (
                'Kill Team: Into the Dark',
                'Kill Team', None,
                'KT-002', decimal.Decimal('130.00'),
                'A Kill Team box set featuring Veteran Guardsmen vs Intercession '
                'Squad operatives with a space hulk terrain board.,'
            ),
            (
                'Kill Team: Starter Set',
                'Kill Team', None,
                'KT-003', decimal.Decimal('65.00'),
                'The essential Kill Team starter box with two warbands, terrain, '
                'tokens, dice, and the complete condensed rules.,'
            ),

        ]

        # Map faction name (or None) to faction object
        faction_lookup = Faction.objects.in_bulk(field_name='name')

        products = []
        for (
            name, cat_name, faction_name, gw_sku, msrp, description,
        ) in product_data:
            cat = Category.objects.filter(name=cat_name).first()
            faction = faction_lookup.get(faction_name) if faction_name else None

            slug = slugify(name)
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'category': cat,
                    'faction': faction,
                    'description': description,
                    'msrp': msrp,
                    'is_active': True,
                    # Placeholder image — update with real images later
                    'image_url': f'https://placehold.co/400x300/1e1e1e/bb86fc?text={slugify(name)[:30]}',
                },
            )
            products.append(product)
            status = 'created' if created else 'updated'
            self.stdout.write(f'  [{status}] {name} — ${msrp}')

        return products

    # -------------------------------------------------------------------------
    # Extended product catalog — 300 additional SKUs
    # -------------------------------------------------------------------------

    def _create_extended_products(self, categories, factions):
        """
        Create 300 additional Warhammer products with real GW SKUs and MSRPs.

        Covers: Space Marines (all chapters), Death Guard, Thousand Sons,
        World Eaters, Astra Militarum, Adeptus Mechanicus, Grey Knights,
        Drukhari, Craftworlds, Leagues of Votann, Custodes, Sisters of Battle,
        Genestealer Cults, Age of Sigmar factions, Kill Team, Necromunda,
        Warcry, Horus Heresy infantry/vehicles, and Citadel paint ranges.
        """
        self.stdout.write('Creating extended product catalog…')

        # (name, category_name, faction_name, gw_sku, msrp, description)
        extended_data = [

            # ================================================================
            # SPACE MARINES — extended range
            # ================================================================
            ('Space Marine Infernus Squad', 'Warhammer 40,000', 'Space Marines',
             '48-45', decimal.Decimal('52.50'),
             'Ten Primaris Marines with pyreblasters, designed to clear fortified '
             'positions and dense infantry with gouts of promethium fire.'),
            ('Space Marine Sternguard Veteran Squad', 'Warhammer 40,000', 'Space Marines',
             '48-43', decimal.Decimal('60.00'),
             'Five elite Sternguard Veterans armed with special-issue bolt weapons '
             'capable of defeating almost any foe at range.'),
            ('Space Marine Terminator Squad', 'Warhammer 40,000', 'Space Marines',
             '48-06', decimal.Decimal('55.00'),
             'Five Terminators clad in Tactical Dreadnought Armour, the most '
             'resilient infantry in the Imperium. Armed with storm bolters and '
             'power fists with optional heavy weapon upgrades.'),
            ('Space Marine Terminator Assault Squad', 'Warhammer 40,000', 'Space Marines',
             '48-07', decimal.Decimal('55.00'),
             'Five close-combat Terminators armed with thunder hammers and storm '
             'shields or lightning claws — the elite shock troops of any Chapter.'),
            ('Space Marine Devastator Squad', 'Warhammer 40,000', 'Space Marines',
             '48-15', decimal.Decimal('55.00'),
             'Five Devastators with a wide choice of heavy weapons: lascannons, '
             'missile launchers, multi-meltas, heavy bolters, and plasma cannons.'),
            ('Space Marine Tactical Squad', 'Warhammer 40,000', 'Space Marines',
             '48-07', decimal.Decimal('45.00'),
             'Ten classic Tactical Space Marines with bolters, a special weapon, '
             'and a heavy weapon. The iconic backbone of any Chapter.'),
            ('Space Marine Outriders', 'Warhammer 40,000', 'Space Marines',
             '48-40', decimal.Decimal('52.50'),
             'Three Primaris Space Marine bikers on Mk II Outrider bikes armed '
             'with bolt rifles and twin bolt pistols for fast-attack roles.'),
            ('Space Marine Invader ATV', 'Warhammer 40,000', 'Space Marines',
             '48-42', decimal.Decimal('42.50'),
             'A single Primaris Invader ATV armed with an onslaught gatling cannon '
             'or multi-melta, providing rapid mobile fire support.'),
            ('Space Marine Redemptor Dreadnought', 'Warhammer 40,000', 'Space Marines',
             '48-93', decimal.Decimal('60.00'),
             'A towering Primaris Dreadnought with a macro plasma incinerator or '
             'onslaught gatling cannon and an integral Redemptor fist.'),
            ('Space Marine Brutalis Dreadnought', 'Warhammer 40,000', 'Space Marines',
             '48-44', decimal.Decimal('65.00'),
             'A close-combat Primaris Dreadnought with twin frag launchers and '
             'brutalis fists, designed to punch through armour and fortifications.'),
            ('Space Marine Ballistus Dreadnought', 'Warhammer 40,000', 'Space Marines',
             '48-46', decimal.Decimal('65.00'),
             'A ranged Primaris Dreadnought with a twin lascannon and missile '
             'launcher, providing devastatingly accurate long-range fire support.'),
            ('Space Marine Land Raider', 'Warhammer 40,000', 'Space Marines',
             '48-21', decimal.Decimal('85.00'),
             'The iconic Land Raider battle tank, protected by adamantine armour '
             'and armed with twin heavy bolters and twin lascannons.'),
            ('Space Marine Land Raider Crusader', 'Warhammer 40,000', 'Space Marines',
             '48-22', decimal.Decimal('85.00'),
             'A transport-focused Land Raider variant armed with hurricane bolters '
             'and a multi-melta, capable of ferrying twelve Space Marines.'),
            ('Space Marine Predator Destructor', 'Warhammer 40,000', 'Space Marines',
             '48-23', decimal.Decimal('57.50'),
             'A battle tank with an autocannon turret and optional lascannons or '
             'heavy bolters in sponsons — an anti-infantry workhorse.'),
            ('Space Marine Whirlwind', 'Warhammer 40,000', 'Space Marines',
             '48-25', decimal.Decimal('52.50'),
             'A long-range artillery tank firing Whirlwind vengeance launcher '
             'missiles or Castellan launcher missiles at hidden foes.'),
            ('Space Marine Vindicator', 'Warhammer 40,000', 'Space Marines',
             '48-26', decimal.Decimal('57.50'),
             'A siege tank armed with a demolisher cannon capable of levelling '
             'fortifications and obliterating massed infantry in one shot.'),
            ('Space Marine Repulsor Executioner', 'Warhammer 40,000', 'Space Marines',
             '48-95', decimal.Decimal('90.00'),
             'A heavily armed Primaris tank with a macro plasma incinerator or '
             'heavy laser destroyer turret for eliminating armoured targets.'),
            ('Space Marine Librarian', 'Warhammer 40,000', 'Space Marines',
             '48-30', decimal.Decimal('30.00'),
             'A psyker warrior-scholar of the Adeptus Astartes, channelling the '
             'power of the warp through a force staff and psychic hood.'),
            ('Space Marine Chaplain', 'Warhammer 40,000', 'Space Marines',
             '48-32', decimal.Decimal('30.00'),
             'A spiritual warrior armed with a crozius arcanum and bolt pistol, '
             'inspiring nearby Space Marines to feats of extraordinary valour.'),
            ('Space Marine Apothecary', 'Warhammer 40,000', 'Space Marines',
             '48-33', decimal.Decimal('30.00'),
             'The battlefield medic of the Space Marines, equipped with a narthecium '
             'to recover gene-seed from fallen brothers.'),
            ('Space Marine Ancient', 'Warhammer 40,000', 'Space Marines',
             '48-34', decimal.Decimal('30.00'),
             'A Standard Bearer carrying an ornate battle standard into the heart '
             'of the enemy, inspiring nearby Space Marines with its presence.'),
            ('Space Marine Scouts', 'Warhammer 40,000', 'Space Marines',
             '48-29', decimal.Decimal('30.00'),
             'Five lightly armoured Scout Marines armed with sniper rifles, '
             'bolt pistols, shotguns, or heavy bolters for infiltration duties.'),
            ('Space Marine Infiltrators', 'Warhammer 40,000', 'Space Marines',
             '48-41', decimal.Decimal('40.00'),
             'Five Primaris Infiltrators in Phobos armour, equipped with '
             'marksman bolt carbines and omni-scramblers to disrupt enemy reserves.'),
            ('Space Marine Incursors', 'Warhammer 40,000', 'Space Marines',
             '48-96', decimal.Decimal('40.00'),
             'Five Primaris Incursors optimised for close-quarters combat with '
             'paired combat blades and haywire mine deployable systems.'),
            ('Space Marine Eliminators', 'Warhammer 40,000', 'Space Marines',
             '48-98', decimal.Decimal('37.50'),
             'Three Primaris Eliminators equipped with bolt sniper rifles and '
             'las fusils, able to pick off targets from extreme range.'),
            ('Space Marine Suppressors', 'Warhammer 40,000', 'Space Marines',
             '48-99', decimal.Decimal('37.50'),
             'Three jump-pack equipped Primaris Suppressors with accelerator '
             'autocannons, dropping in to lay down suppressing fire.'),
            ('Space Marine Inceptors', 'Warhammer 40,000', 'Space Marines',
             '48-97', decimal.Decimal('45.00'),
             'Three Primaris jump-pack troops armed with assault bolters or '
             'plasma exterminators for devastating aerial assault.'),
            ('Space Marine Aggressors', 'Warhammer 40,000', 'Space Marines',
             '48-92', decimal.Decimal('45.00'),
             'Three Primaris Aggressors in Gravis armour with boltstorm gauntlets '
             'or flamestorm gauntlets — slow but nearly unstoppable.'),

            # ================================================================
            # BLOOD ANGELS — extended
            # ================================================================
            ('Blood Angels Librarian Dreadnought', 'Warhammer 40,000', 'Blood Angels',
             '41-15', decimal.Decimal('60.00'),
             'A unique Blood Angels Dreadnought housing a powerful psyker, '
             'combining the firepower of a walker with devastating psychic might.'),
            ('Blood Angels Mephiston', 'Warhammer 40,000', 'Blood Angels',
             '41-02', decimal.Decimal('30.00'),
             'The Chief Librarian of the Blood Angels — one of the most powerful '
             'psykers in the Imperium, who broke the grip of the Black Rage.'),
            ('Blood Angels Astorath', 'Warhammer 40,000', 'Blood Angels',
             '41-03', decimal.Decimal('27.50'),
             'The High Chaplain of the Blood Angels, who seeks out those lost '
             'to the Black Rage and grants them the Emperor\'s mercy in battle.'),

            # ================================================================
            # DARK ANGELS
            # ================================================================
            ('Dark Angels Deathwing Knights', 'Warhammer 40,000', 'Dark Angels',
             '44-10', decimal.Decimal('55.00'),
             'Five elite Terminator-armoured knights bearing maces of absolution '
             'and storm shields — the inner circle of the Deathwing.'),
            ('Dark Angels Ravenwing Black Knights', 'Warhammer 40,000', 'Dark Angels',
             '44-12', decimal.Decimal('40.00'),
             'Three elite bikers forming the spearhead of the Ravenwing, armed '
             'with plasma talons and corvus hammers.'),
            ('Dark Angels Ezekiel', 'Warhammer 40,000', 'Dark Angels',
             '44-02', decimal.Decimal('27.50'),
             'Grand Master of Librarians, one of the most powerful psykers in '
             'the Dark Angels Chapter, clutching the Book of Salvation.'),
            ('Dark Angels Combat Patrol', 'Warhammer 40,000', 'Dark Angels',
             '44-20', decimal.Decimal('105.00'),
             'A ready-to-play Dark Angels Combat Patrol: Primaris Lieutenant, '
             'Intercessors, Outriders, and a Redemptor Dreadnought.'),

            # ================================================================
            # SPACE WOLVES
            # ================================================================
            ('Space Wolves Thunderwolf Cavalry', 'Warhammer 40,000', 'Space Wolves',
             '53-10', decimal.Decimal('55.00'),
             'Three Space Wolf warriors mounted on ferocious thunderwolves, '
             'armed with frost weapons and storm shields.'),
            ('Space Wolves Grey Hunters', 'Warhammer 40,000', 'Space Wolves',
             '53-06', decimal.Decimal('40.00'),
             'Ten Space Wolf tactical marines armed with bolters and close-combat '
             'weapons, embodying the savage strength of Fenris.'),
            ('Space Wolves Wolf Guard Terminators', 'Warhammer 40,000', 'Space Wolves',
             '53-08', decimal.Decimal('55.00'),
             'Five elite Space Wolf veterans in Tactical Dreadnought armour, '
             'with extensive weapon customisation options.'),
            ('Space Wolves Ragnar Blackmane', 'Warhammer 40,000', 'Space Wolves',
             '53-02', decimal.Decimal('30.00'),
             'The Great Wolf\'s most celebrated warrior, armed with Frostfang '
             'and the Axe of Morkai.'),
            ('Space Wolves Combat Patrol', 'Warhammer 40,000', 'Space Wolves',
             '53-20', decimal.Decimal('105.00'),
             'A Space Wolves Combat Patrol box with Primaris Lieutenant, '
             'Intercessors, Outriders, and a Redemptor Dreadnought.'),

            # ================================================================
            # BLACK TEMPLARS
            # ================================================================
            ('Black Templars Primaris Crusader Squad', 'Warhammer 40,000', 'Black Templars',
             '55-20', decimal.Decimal('52.50'),
             'Ten Black Templars Primaris Crusaders — initiates and neophytes '
             'fighting side by side in the eternal crusade.'),
            ('Black Templars Emperor\'s Champion', 'Warhammer 40,000', 'Black Templars',
             '55-22', decimal.Decimal('27.50'),
             'The greatest warrior of the Black Templars, clad in the Armour '
             'of Faith and bearing the Black Sword.'),
            ('Black Templars Helbrecht', 'Warhammer 40,000', 'Black Templars',
             '55-21', decimal.Decimal('35.00'),
             'The High Marshal of the Black Templars, bearing the Sword of the '
             'High Marshals and leading the crusade against all heresy.'),
            ('Black Templars Combat Patrol', 'Warhammer 40,000', 'Black Templars',
             '55-30', decimal.Decimal('105.00'),
             'A Black Templars Combat Patrol featuring Marshal, Sword Brethren, '
             'Crusader Squad, and a Redemptor Dreadnought.'),

            # ================================================================
            # GREY KNIGHTS
            # ================================================================
            ('Grey Knights Strike Squad', 'Warhammer 40,000', 'Grey Knights',
             '57-06', decimal.Decimal('55.00'),
             'Five Grey Knights in Aegis power armour armed with nemesis force '
             'swords, storm bolters, and psionic powers.'),
            ('Grey Knights Terminators', 'Warhammer 40,000', 'Grey Knights',
             '57-08', decimal.Decimal('60.00'),
             'Five Grey Knight Terminators bearing nemesis force halberds, '
             'daemonhammers, and swords — the pinnacle of anti-daemon warfare.'),
            ('Grey Knights Dreadknight', 'Warhammer 40,000', 'Grey Knights',
             '57-14', decimal.Decimal('67.50'),
             'A hulking Dreadknight walker piloted by a Grey Knight Terminator, '
             'armed with a gatling psilencer and a nemesis greatsword.'),
            ('Grey Knights Grand Master Voldus', 'Warhammer 40,000', 'Grey Knights',
             '57-02', decimal.Decimal('30.00'),
             'The Grand Master of the 3rd Brotherhood, Aldrik Voldus bears the '
             'Malleus Argyrum and channels devastating psychic power.'),
            ('Grey Knights Combat Patrol', 'Warhammer 40,000', 'Grey Knights',
             '57-20', decimal.Decimal('105.00'),
             'A Grey Knights Combat Patrol: Grand Master in Nemesis Dreadknight, '
             'Strike Squad, and Interceptor Squad.'),

            # ================================================================
            # DEATHWATCH
            # ================================================================
            ('Deathwatch Kill Team', 'Warhammer 40,000', 'Deathwatch',
             '39-10', decimal.Decimal('40.00'),
             'Five heavily customisable Deathwatch Space Marines drawn from '
             'multiple Chapters, bearing special-issue ammunition.'),
            ('Deathwatch Veteran Squad', 'Warhammer 40,000', 'Deathwatch',
             '39-06', decimal.Decimal('45.00'),
             'Five Deathwatch Veterans with extensive bespoke wargear options '
             'including frag cannons, infernus heavy bolters, and xenophase blades.'),

            # ================================================================
            # CUSTODES
            # ================================================================
            ('Adeptus Custodes Custodian Guard', 'Warhammer 40,000', 'Custodes',
             '01-08', decimal.Decimal('42.50'),
             'Three golden warriors of the Emperor\'s personal guard, armed with '
             'guardian spears or sentinel blades and praesidium shields.'),
            ('Adeptus Custodes Custodian Wardens', 'Warhammer 40,000', 'Custodes',
             '01-10', decimal.Decimal('42.50'),
             'Three veteran Custodians who have sworn an oath of protection, '
             'armed with castellan axes and misericordias.'),
            ('Adeptus Custodes Vertus Praetors', 'Warhammer 40,000', 'Custodes',
             '01-11', decimal.Decimal('42.50'),
             'Three Custodian bikers mounted on Dawneagle jetbikes armed with '
             'salvo launchers or hurricane bolters.'),
            ('Adeptus Custodes Shield-Captain', 'Warhammer 40,000', 'Custodes',
             '01-07', decimal.Decimal('30.00'),
             'A commander of the Adeptus Custodes, bearing a guardian spear and '
             'clad in auramite alloy armour.'),
            ('Adeptus Custodes Trajann Valoris', 'Warhammer 40,000', 'Custodes',
             '01-02', decimal.Decimal('30.00'),
             'The Captain-General of the Adeptus Custodes, armed with the Watcher\'s '
             'Axe and the Eagle\'s Eye.'),
            ('Adeptus Custodes Combat Patrol', 'Warhammer 40,000', 'Custodes',
             '01-20', decimal.Decimal('105.00'),
             'A Custodes Combat Patrol: Shield-Captain, Custodian Guard, '
             'Vertus Praetors, and Allarus Custodians.'),

            # ================================================================
            # SISTERS OF BATTLE
            # ================================================================
            ('Adepta Sororitas Battle Sisters Squad', 'Warhammer 40,000', 'Sisters of Battle',
             '52-20', decimal.Decimal('40.00'),
             'Ten Sisters of Battle in power armour armed with bolters, meltaguns, '
             'flamers, and a host of blessed weapons.'),
            ('Adepta Sororitas Celestian Sacresants', 'Warhammer 40,000', 'Sisters of Battle',
             '52-22', decimal.Decimal('40.00'),
             'Five elite veterans who guard the Order\'s most sacred relics, '
             'armed with anointed halberds and hallowed maces.'),
            ('Adepta Sororitas Seraphim Squad', 'Warhammer 40,000', 'Sisters of Battle',
             '52-12', decimal.Decimal('40.00'),
             'Five jump-pack equipped Sisters bearing twin bolt pistols or '
             'twin hand flamers, striking from above with divine fury.'),
            ('Adepta Sororitas Retributor Squad', 'Warhammer 40,000', 'Sisters of Battle',
             '52-15', decimal.Decimal('40.00'),
             'Five Sisters of Battle carrying heavy weapons: multi-meltas, '
             'heavy flamers, heavy bolters, and Ministorum heavy bolters.'),
            ('Adepta Sororitas Immolator', 'Warhammer 40,000', 'Sisters of Battle',
             '52-09', decimal.Decimal('52.50'),
             'A Battle Sisters transport armed with twin multi-meltas or '
             'immolation flamers, a purifying flame on tracks.'),
            ('Adepta Sororitas Exorcist', 'Warhammer 40,000', 'Sisters of Battle',
             '52-08', decimal.Decimal('67.50'),
             'A pipe organ mounted on a tank hull, the Exorcist fires a storm '
             'of missiles at the enemies of the God-Emperor.'),
            ('Adepta Sororitas Morvenn Vahl', 'Warhammer 40,000', 'Sisters of Battle',
             '52-02', decimal.Decimal('40.00'),
             'Abbess Sanctorum of the Adepta Sororitas, clad in the Purgator '
             'Mirabilis and wielding the Lance of Illumination.'),
            ('Adepta Sororitas Combat Patrol', 'Warhammer 40,000', 'Sisters of Battle',
             '52-25', decimal.Decimal('105.00'),
             'A Combat Patrol of the Adepta Sororitas: Canoness, Battle Sisters, '
             'Repentia Squad, and Mortifiers.'),

            # ================================================================
            # DEATH GUARD
            # ================================================================
            ('Death Guard Plague Marines', 'Warhammer 40,000', 'Death Guard',
             '43-50', decimal.Decimal('37.50'),
             'Seven bloated Plague Marines in rusted power armour, armed with '
             'blight launchers, plasma guns, and plague weapons.'),
            ('Death Guard Poxwalkers', 'Warhammer 40,000', 'Death Guard',
             '43-53', decimal.Decimal('30.00'),
             'Twenty shambling Poxwalker zombies driven forward by Nurgle\'s '
             'gift, overwhelming enemies with sheer infected numbers.'),
            ('Death Guard Blightlord Terminators', 'Warhammer 40,000', 'Death Guard',
             '43-54', decimal.Decimal('52.50'),
             'Five hulking Terminators swollen with Nurgle\'s blessings, armed '
             'with bubotic axes, blight launchers, and combi-weapons.'),
            ('Death Guard Deathshroud Bodyguard', 'Warhammer 40,000', 'Death Guard',
             '43-56', decimal.Decimal('42.50'),
             'Three elite bodyguards of Mortarion in Terminator armour, bearing '
             'manreapers and plaguespurt gauntlets.'),
            ('Death Guard Foetid Bloat-drone', 'Warhammer 40,000', 'Death Guard',
             '43-55', decimal.Decimal('42.50'),
             'A hovering daemon engine armed with plague probes and a fleshmower '
             'or plaguespitter — a disgusting fast-attack option.'),
            ('Death Guard Mortarion', 'Warhammer 40,000', 'Death Guard',
             '43-03', decimal.Decimal('155.00'),
             'The Daemon Primarch of the Death Guard — an enormous centrepiece '
             'model with a scythe, war-bell, and retinue of nurgling attendants.'),
            ('Death Guard Typhus', 'Warhammer 40,000', 'Death Guard',
             '43-08', decimal.Decimal('35.00'),
             'The Host of the Destroyer Hive, Typhus spreads contagion wherever '
             'he walks, armed with the Manreaper and surrounded by Nurgling swarms.'),
            ('Death Guard Combat Patrol', 'Warhammer 40,000', 'Death Guard',
             '43-80', decimal.Decimal('105.00'),
             'A Death Guard Combat Patrol: Lord of Contagion, Plague Marines, '
             'Poxwalkers, and a Foetid Bloat-drone.'),

            # ================================================================
            # THOUSAND SONS
            # ================================================================
            ('Thousand Sons Rubric Marines', 'Warhammer 40,000', 'Thousand Sons',
             '43-35', decimal.Decimal('40.00'),
             'Ten Rubric Marines, sorcery-bound automatons in ornate power armour '
             'armed with inferno boltguns and soulreaper cannons.'),
            ('Thousand Sons Scarab Occult Terminators', 'Warhammer 40,000', 'Thousand Sons',
             '43-36', decimal.Decimal('52.50'),
             'Five elite Terminators infused with aetheric power, bearing '
             'khopesh blades, hellfyre missile racks, and combi-bolters.'),
            ('Thousand Sons Exalted Sorcerers', 'Warhammer 40,000', 'Thousand Sons',
             '43-38', decimal.Decimal('37.50'),
             'Three Sorcerers of the Thousand Sons aboard discs of Tzeentch, '
             'wielding inferno bolt pistols and force staves.'),
            ('Thousand Sons Magnus the Red', 'Warhammer 40,000', 'Thousand Sons',
             '43-02', decimal.Decimal('130.00'),
             'The Daemon Primarch of the Thousand Sons, a winged cyclopean giant '
             'armed with the Blade of Magnus.'),
            ('Thousand Sons Ahriman', 'Warhammer 40,000', 'Thousand Sons',
             '43-30', decimal.Decimal('35.00'),
             'Chief Librarian of the Thousand Sons, bearing the Black Staff of '
             'Ahriman and wearing the legendary armour of the Arch-Sorcerer.'),
            ('Thousand Sons Combat Patrol', 'Warhammer 40,000', 'Thousand Sons',
             '43-90', decimal.Decimal('105.00'),
             'A Thousand Sons Combat Patrol: Exalted Sorcerer, Rubric Marines, '
             'Scarab Occult Terminators, and Tzaangors.'),

            # ================================================================
            # WORLD EATERS
            # ================================================================
            ('World Eaters Berzerkers', 'Warhammer 40,000', 'World Eaters',
             '43-60', decimal.Decimal('42.50'),
             'Eight blood-mad Khorne Berzerkers in battered power armour, '
             'armed with chainaxes, chainswords, and bolt pistols.'),
            ('World Eaters Eightbound', 'Warhammer 40,000', 'World Eaters',
             '43-62', decimal.Decimal('52.50'),
             'Three massive warriors bound by eight daemons of Khorne, '
             'wielding eviscerators and exalted eviscerators.'),
            ('World Eaters Angron', 'Warhammer 40,000', 'World Eaters',
             '43-04', decimal.Decimal('145.00'),
             'The Daemon Primarch of the World Eaters, a monumental model '
             'covered in the Butcher\'s Nails and soaked in the blood of worlds.'),
            ('World Eaters Lord on Juggernaut', 'Warhammer 40,000', 'World Eaters',
             '43-64', decimal.Decimal('37.50'),
             'A World Eaters Lord riding a Juggernaut of Khorne, an unstoppable '
             'combination of daemon engine and furious warrior.'),
            ('World Eaters Combat Patrol', 'Warhammer 40,000', 'World Eaters',
             '43-95', decimal.Decimal('105.00'),
             'A World Eaters Combat Patrol: Master of Executions, Berzerkers, '
             'Eightbound, and Jakhals.'),

            # ================================================================
            # ASTRA MILITARUM
            # ================================================================
            ('Astra Militarum Infantry Squad', 'Warhammer 40,000', 'Astra Militarum',
             '47-19', decimal.Decimal('32.50'),
             'Ten Imperial Guardsmen with lasrifles, a heavy weapon team, and '
             'a sergeant — the backbone of the Imperial war machine.'),
            ('Astra Militarum Cadian Shock Troops', 'Warhammer 40,000', 'Astra Militarum',
             '47-30', decimal.Decimal('37.50'),
             'Ten Cadian Shock Troops in redesigned plastic, armed with lasrifles '
             'and upgrade options for special and heavy weapons.'),
            ('Astra Militarum Veteran Guardsmen', 'Warhammer 40,000', 'Astra Militarum',
             '47-31', decimal.Decimal('40.00'),
             'Ten battle-hardened Veteran Guardsmen with extra equipment options '
             'including demolition charges, grenade launchers, and shotguns.'),
            ('Astra Militarum Leman Russ Battle Tank', 'Warhammer 40,000', 'Astra Militarum',
             '47-06', decimal.Decimal('57.50'),
             'The standard battle tank of the Astra Militarum, armed with a '
             'battle cannon and sponson weapon options.'),
            ('Astra Militarum Chimera', 'Warhammer 40,000', 'Astra Militarum',
             '47-05', decimal.Decimal('42.50'),
             'The ubiquitous armoured transport of the Imperial Guard, carrying '
             'twelve soldiers into the heart of battle.'),
            ('Astra Militarum Basilisk', 'Warhammer 40,000', 'Astra Militarum',
             '47-17', decimal.Decimal('52.50'),
             'A long-range artillery tank armed with an earthshaker cannon capable '
             'of firing over intervening terrain to bombard distant targets.'),
            ('Astra Militarum Hellhound', 'Warhammer 40,000', 'Astra Militarum',
             '47-14', decimal.Decimal('42.50'),
             'A fast armoured vehicle spewing promethium flame from an inferno '
             'cannon, ideal for clearing infantry from cover.'),
            ('Astra Militarum Sentinel', 'Warhammer 40,000', 'Astra Militarum',
             '47-12', decimal.Decimal('32.50'),
             'A lightly armoured walker on scout or armoured legs, armed with '
             'a lascannon, autocannon, heavy flamer, or multi-laser.'),
            ('Astra Militarum Commissar', 'Warhammer 40,000', 'Astra Militarum',
             '47-08', decimal.Decimal('20.00'),
             'A single Commissar enforcing the discipline of the Imperial Guard '
             'with a bolt pistol and power sword — at any cost.'),
            ('Astra Militarum Combat Patrol', 'Warhammer 40,000', 'Astra Militarum',
             '47-25', decimal.Decimal('105.00'),
             'An Astra Militarum Combat Patrol: Cadian Command Squad, Infantry '
             'Squad, Heavy Weapons Squad, and a Sentinel.'),

            # ================================================================
            # ADEPTUS MECHANICUS
            # ================================================================
            ('Adeptus Mechanicus Skitarii Rangers', 'Warhammer 40,000', 'Adeptus Mechanicus',
             '59-10', decimal.Decimal('32.50'),
             'Ten Skitarii Rangers with galvanic rifles pursuing their quarry '
             'across any terrain in service to the Omnissiah.'),
            ('Adeptus Mechanicus Skitarii Vanguard', 'Warhammer 40,000', 'Adeptus Mechanicus',
             '59-11', decimal.Decimal('32.50'),
             'Ten radiation-saturated Skitarii Vanguard with radium carbines, '
             'irradiating the enemy with every shot.'),
            ('Adeptus Mechanicus Ironstrider Ballistarii', 'Warhammer 40,000', 'Adeptus Mechanicus',
             '59-14', decimal.Decimal('42.50'),
             'Two gyroscopically-balanced Ironstriders armed with twin cognis '
             'lascannons or twin cognis autocannons.'),
            ('Adeptus Mechanicus Dunecrawler', 'Warhammer 40,000', 'Adeptus Mechanicus',
             '59-16', decimal.Decimal('57.50'),
             'A six-legged heavy walker capable of mounting a neutron laser, '
             'eradication beamer, or Icarus array.'),
            ('Adeptus Mechanicus Kataphron Destroyers', 'Warhammer 40,000', 'Adeptus Mechanicus',
             '59-18', decimal.Decimal('42.50'),
             'Three servitor-cyborgs carrying heavy grav-cannons or plasma culverins '
             'on tracked lower bodies.'),
            ('Adeptus Mechanicus Electropriests', 'Warhammer 40,000', 'Adeptus Mechanicus',
             '59-20', decimal.Decimal('35.00'),
             'Ten fanatical cyborg warrior-priests channelling voltaic or '
             'corpuscarii energies through electrostatic gauntlets.'),
            ('Adeptus Mechanicus Tech-Priest Dominus', 'Warhammer 40,000', 'Adeptus Mechanicus',
             '59-06', decimal.Decimal('27.50'),
             'A high-ranking Tech-Priest bearing a volkite blaster and macrostubber, '
             'surrounded by servo-skulls and mechadendrites.'),
            ('Adeptus Mechanicus Combat Patrol', 'Warhammer 40,000', 'Adeptus Mechanicus',
             '59-25', decimal.Decimal('105.00'),
             'An Adeptus Mechanicus Combat Patrol: Tech-Priest Manipulus, '
             'Skitarii Rangers, Sicarian Infiltrators, and a Dunecrawler.'),

            # ================================================================
            # GENESTEALER CULTS
            # ================================================================
            ('Genestealer Cults Neophyte Hybrids', 'Warhammer 40,000', 'Genestealer Cults',
             '51-40', decimal.Decimal('32.50'),
             'Ten Neophyte Hybrids armed with autoguns, shotguns, mining lasers, '
             'seismic cannons, and grenade launchers.'),
            ('Genestealer Cults Acolyte Hybrids', 'Warhammer 40,000', 'Genestealer Cults',
             '51-41', decimal.Decimal('35.00'),
             'Five Acolyte Hybrids armed with autopistols, hand flamers, '
             'heavy rock drills, cutters, and saws.'),
            ('Genestealer Cults Aberrants', 'Warhammer 40,000', 'Genestealer Cults',
             '51-44', decimal.Decimal('42.50'),
             'Five grotesquely mutated Aberrants wielding pick axes, power picks, '
             'and improvised weapons with crushing strength.'),
            ('Genestealer Cults Magus', 'Warhammer 40,000', 'Genestealer Cults',
             '51-43', decimal.Decimal('22.50'),
             'A psyker infected with the Genestealer curse, channelling alien '
             'power through a staff and psychic gifts.'),
            ('Genestealer Cults Patriarch', 'Warhammer 40,000', 'Genestealer Cults',
             '51-42', decimal.Decimal('40.00'),
             'The ultimate evolution of the Genestealer infection — a monstrous '
             'beast surrounded by an aura of alien hypnosis.'),

            # ================================================================
            # DRUKHARI
            # ================================================================
            ('Drukhari Kabalite Warriors', 'Warhammer 40,000', 'Drukhari',
             '45-07', decimal.Decimal('30.00'),
             'Ten Kabalite Warriors armed with splinter rifles, blasters, '
             'and a dark lance — the cruel raiders of Commorragh.'),
            ('Drukhari Wyches', 'Warhammer 40,000', 'Drukhari',
             '45-06', decimal.Decimal('30.00'),
             'Ten Wych Cult gladiatrices armed with hydra gauntlets, razorflails, '
             'shardnets, and impaler weapons for lethal arena combat.'),
            ('Drukhari Raider', 'Warhammer 40,000', 'Drukhari',
             '45-10', decimal.Decimal('37.50'),
             'A sleek anti-gravity raiding skimmer armed with a dark lance or '
             'disintegrator cannon, transporting ten warriors.'),
            ('Drukhari Ravager', 'Warhammer 40,000', 'Drukhari',
             '45-12', decimal.Decimal('37.50'),
             'A heavy gunship armed with three dark lances or disintegrator '
             'cannons, hunting tanks and heavy infantry.'),
            ('Drukhari Archon', 'Warhammer 40,000', 'Drukhari',
             '45-02', decimal.Decimal('22.50'),
             'A Supreme Overlord of a Kabal, armed with a huskblade and '
             'blast pistol, surrounded by a court of courtiers.'),
            ('Drukhari Combat Patrol', 'Warhammer 40,000', 'Drukhari',
             '45-25', decimal.Decimal('105.00'),
             'A Drukhari Combat Patrol: Archon, Kabalite Warriors, Wyches, '
             'Incubi, and a Raider.'),

            # ================================================================
            # CRAFTWORLDS
            # ================================================================
            ('Craftworlds Guardians', 'Warhammer 40,000', 'Craftworlds',
             '46-09', decimal.Decimal('30.00'),
             'Ten Aeldari Guardians with shuriken catapults and a weapon platform '
             'armed with a bright lance, scatter laser, or starcannon.'),
            ('Craftworlds Dire Avengers', 'Warhammer 40,000', 'Craftworlds',
             '46-06', decimal.Decimal('30.00'),
             'Five elite Aspect Warriors armed with avenger shuriken catapults '
             'and Exarch with diresword or power glaive.'),
            ('Craftworlds Fire Dragons', 'Warhammer 40,000', 'Craftworlds',
             '46-14', decimal.Decimal('30.00'),
             'Five Fire Dragon Aspect Warriors bearing fusion guns, melta bombs, '
             'and tank-hunting equipment.'),
            ('Craftworlds Wraithguard', 'Warhammer 40,000', 'Craftworlds',
             '46-26', decimal.Decimal('45.00'),
             'Five towering constructs animated by Aeldari spirit stones, armed '
             'with wraithcannons or d-scythes.'),
            ('Craftworlds Wave Serpent', 'Warhammer 40,000', 'Craftworlds',
             '46-29', decimal.Decimal('50.00'),
             'The premier Aeldari skimmer transport, bearing a twin turret weapon '
             'system and a wave serpent shield.'),
            ('Craftworlds Farseer', 'Warhammer 40,000', 'Craftworlds',
             '46-02', decimal.Decimal('22.50'),
             'An Aeldari seer of unparalleled psychic power, guiding their '
             'craftworld\'s fate with witchblade and runes.'),
            ('Craftworlds Combat Patrol', 'Warhammer 40,000', 'Craftworlds',
             '46-25', decimal.Decimal('105.00'),
             'A Craftworlds Combat Patrol: Farseer, Guardians, Dire Avengers, '
             'Wraithblades, and a War Walker.'),

            # ================================================================
            # LEAGUES OF VOTANN
            # ================================================================
            ('Leagues of Votann Hearthkyn Warriors', 'Warhammer 40,000', 'Leagues of Votann',
             '73-10', decimal.Decimal('40.00'),
             'Ten stocky Kin warriors armed with ion blasters, autoch-pattern '
             'bolters, and a wealth of equipment options.'),
            ('Leagues of Votann Hernkyn Pioneers', 'Warhammer 40,000', 'Leagues of Votann',
             '73-12', decimal.Decimal('45.00'),
             'Three Hernkyn Pioneers on Sagitaur ATVs armed with bolt shotguns '
             'and heavy weapons for fast scouting duties.'),
            ('Leagues of Votann Einhyr Hearthguard', 'Warhammer 40,000', 'Leagues of Votann',
             '73-14', decimal.Decimal('52.50'),
             'Five elite Kin warriors in exo-armour bearing volkanite disintegrators '
             'or concussion gauntlets.'),
            ('Leagues of Votann Kahl', 'Warhammer 40,000', 'Leagues of Votann',
             '73-06', decimal.Decimal('27.50'),
             'A Kin commander armed with a forgewrought plasma axe and '
             'autoch-pattern bolt pistol.'),
            ('Leagues of Votann Combat Patrol', 'Warhammer 40,000', 'Leagues of Votann',
             '73-25', decimal.Decimal('105.00'),
             'A Leagues of Votann Combat Patrol: Kahl, Hearthkyn Warriors, '
             'Hernkyn Pioneers, and an Einhyr Champion.'),

            # ================================================================
            # TAU EMPIRE — extended
            # ================================================================
            ("T'au Stealth Battlesuits", 'Warhammer 40,000', "T'au Empire",
             '56-14', decimal.Decimal('35.00'),
             "Three XV25 Stealth Battlesuits armed with burst cannons or fusion "
             "blasters, using advanced stealth fields to remain hidden."),
            ("T'au Crisis Battlesuits", 'Warhammer 40,000', "T'au Empire",
             '56-15', decimal.Decimal('55.00'),
             "Three XV8 Crisis Battlesuits with a vast array of weapon options "
             "including plasma rifles, missile pods, and flamers."),
            ("T'au Riptide Battlesuit", 'Warhammer 40,000', "T'au Empire",
             '56-16', decimal.Decimal('75.00'),
             "A towering XV104 Riptide armed with a heavy burst cannon or ion "
             "accelerator, the pinnacle of T'au battlesuit technology."),
            ("T'au Pathfinders", 'Warhammer 40,000', "T'au Empire",
             '56-19', decimal.Decimal('32.50'),
             "Ten Pathfinders armed with pulse carbines and marker lights, "
             "designating targets for the Greater Good's firepower."),
            ("T'au Hammerhead Gunship", 'Warhammer 40,000', "T'au Empire",
             '56-10', decimal.Decimal('52.50'),
             "A main battle tank armed with a railgun or ion cannon turret — "
             "the primary anti-armour platform of the T'au military."),
            ("T'au Ethereal", 'Warhammer 40,000', "T'au Empire",
             '56-22', decimal.Decimal('20.00'),
             "A mystical caste ruler inspiring nearby Fire Warriors to fight "
             "with unmatched devotion to the Greater Good."),
            ("T'au Combat Patrol", 'Warhammer 40,000', "T'au Empire",
             '56-25', decimal.Decimal('105.00'),
             "A T'au Combat Patrol: Commander in Crisis Battlesuit, Fire Warriors, "
             "Pathfinders, and a Hammerhead Gunship."),

            # ================================================================
            # AGE OF SIGMAR — extended factions
            # ================================================================
            ('Nighthaunt Chainrasps', 'Age of Sigmar', 'Nighthaunt',
             '91-10', decimal.Decimal('30.00'),
             'Twenty ethereal Chainrasp spirits drifting across the battlefield, '
             'overwhelming foes with relentless ghostly swarms.'),
            ('Nighthaunt Grimghast Reapers', 'Age of Sigmar', 'Nighthaunt',
             '91-12', decimal.Decimal('35.00'),
             'Ten scythe-bearing spectral warriors who cut down the living with '
             'their etherial weapons as they glide into battle.'),
            ('Nighthaunt Bladegheist Revenants', 'Age of Sigmar', 'Nighthaunt',
             '91-14', decimal.Decimal('35.00'),
             'Ten whirling spirit warriors spinning in an eternal death dance, '
             'their blades carving through armour with ease.'),
            ('Nighthaunt Lady Olynder', 'Age of Sigmar', 'Nighthaunt',
             '91-02', decimal.Decimal('30.00'),
             'The Mortarch of Grief, Lady Olynder mourns eternally while her '
             'tears drain the life from all around her.'),
            ('Nighthaunt Combat Patrol', 'Age of Sigmar', 'Nighthaunt',
             '91-25', decimal.Decimal('105.00'),
             'A Nighthaunt Combat Patrol: Guardian of Souls, Chainrasps, '
             'Glaivewraith Stalkers, and Grimghast Reapers.'),
            ('Ossiarch Bonereapers Mortek Guard', 'Age of Sigmar', 'Ossiarch Bonereapers',
             '94-10', decimal.Decimal('40.00'),
             'Twenty tireless bone-construct warriors armed with nadirite blades '
             'and shields, animated by the necromantic will of Nagash.'),
            ('Ossiarch Bonereapers Necropolis Stalkers', 'Age of Sigmar', 'Ossiarch Bonereapers',
             '94-12', decimal.Decimal('42.50'),
             'Three multi-armed Necropolis Stalkers shifting between combat '
             'stances mid-battle with four unique attack profiles.'),
            ('Ossiarch Bonereapers Gothizzar Harvester', 'Age of Sigmar', 'Ossiarch Bonereapers',
             '94-14', decimal.Decimal('52.50'),
             'A large construct that gathers bone-tithe from fallen warriors, '
             'restoring nearby Ossiarch Bonereapers as it fights.'),
            ('Flesh-Eater Courts Crypt Ghouls', 'Age of Sigmar', 'Flesh-Eater Courts',
             '91-06', decimal.Decimal('30.00'),
             'Twenty cannibal maniacs driven mad by the Ghoul King\'s delusion, '
             'believing themselves to be noble knights.'),
            ('Flesh-Eater Courts Crypt Horrors', 'Age of Sigmar', 'Flesh-Eater Courts',
             '91-07', decimal.Decimal('40.00'),
             'Three large Crypt Horrors who believe they are heavily armoured '
             'knights errant, tearing apart enemies with savage strength.'),
            ('Gloomspite Gitz Squig Herd', 'Age of Sigmar', 'Gloomspite Gitz',
             '89-10', decimal.Decimal('30.00'),
             'Twelve bouncing cave squigs and six squig herders keeping the '
             'round fanged creatures pointed at the enemy.'),
            ('Gloomspite Gitz Fanatics', 'Age of Sigmar', 'Gloomspite Gitz',
             '89-12', decimal.Decimal('35.00'),
             'Five ball-and-chain wielding Fanatics unleashed from hiding in '
             'nearby units to smash into unsuspecting enemies.'),
            ('Orruk Warclans Ironjawz Brutes', 'Age of Sigmar', 'Orruk Warclans',
             '89-20', decimal.Decimal('40.00'),
             'Five heavily armoured Ironjaw Brutes built for smashing, with '
             'claw arms, gore-hackas, and jagged gore-choppas.'),
            ('Orruk Warclans Kruleboyz Gutrippaz', 'Age of Sigmar', 'Orruk Warclans',
             '89-22', decimal.Decimal('35.00'),
             'Ten cunning Kruleboyz Gutrippaz wielding serrated wicked stikkas '
             'in a disciplined phalanx formation.'),
            ('Daughters of Khaine Witch Aelves', 'Age of Sigmar', 'Daughters of Khaine',
             '85-06', decimal.Decimal('35.00'),
             'Ten Witch Aelves whirling into combat with pairs of sacrificial '
             'knives or a knife and buckler combination.'),
            ('Daughters of Khaine Morathi-Khaine', 'Age of Sigmar', 'Daughters of Khaine',
             '85-02', decimal.Decimal('120.00'),
             'A dual-kit centrepiece of Morathi as Shadow Queen or Morathi-Khaine, '
             'the most powerful champion of the aelf gods.'),
            ('Lumineth Realm-lords Vanari Auralan Wardens', 'Age of Sigmar', 'Lumineth Realm-lords',
             '87-06', decimal.Decimal('40.00'),
             'Ten disciplined Aelf warriors bearing long pikes in a precise '
             'formation, skilled in both attack and defence.'),
            ('Lumineth Realm-lords Alarith Stoneguard', 'Age of Sigmar', 'Lumineth Realm-lords',
             '87-08', decimal.Decimal('40.00'),
             'Five Aelf warriors attuned to the power of Hysh\'s mountains, '
             'bearing enormous stone mallets and diamondpick axes.'),
            ('Slaves to Darkness Chaos Warriors', 'Age of Sigmar', 'Slaves to Darkness',
             '83-10', decimal.Decimal('40.00'),
             'Twelve armoured Warriors of Chaos bearing hand weapons, shields, '
             'or great weapons in service to the Dark Gods.'),
            ('Slaves to Darkness Varanguard', 'Age of Sigmar', 'Slaves to Darkness',
             '83-14', decimal.Decimal('55.00'),
             'Three elite knights of Archaon clad in baroque armour, mounted '
             'on monstrous steeds and bearing daemonic weapons.'),
            ('Blades of Khorne Bloodreavers', 'Age of Sigmar', 'Blades of Khorne',
             '83-30', decimal.Decimal('32.50'),
             'Twenty mortal warriors devoted to Khorne charging recklessly '
             'into combat with axes and meat-rippers.'),
            ('Blades of Khorne Bloodletters', 'Age of Sigmar', 'Blades of Khorne',
             '97-10', decimal.Decimal('30.00'),
             'Ten Lesser Daemons of Khorne bearing hellblades and driven by '
             'an insatiable hunger for blood and skulls.'),
            ('Maggotkin of Nurgle Plaguebearers', 'Age of Sigmar', 'Maggotkin of Nurgle',
             '83-20', decimal.Decimal('30.00'),
             'Ten Lesser Daemons of Nurgle shuffling into battle bearing '
             'plagueswords and tallying their master\'s infections.'),
            ('Maggotkin of Nurgle Putrid Blightkings', 'Age of Sigmar', 'Maggotkin of Nurgle',
             '83-22', decimal.Decimal('42.50'),
             'Five bloated mortal Warriors of Chaos chosen by Nurgle, armed '
             'with enormous plague weapons and rotted shields.'),
            ('Disciples of Tzeentch Tzaangors', 'Age of Sigmar', 'Disciples of Tzeentch',
             '83-40', decimal.Decimal('35.00'),
             'Ten bestial warriors of Tzeentch bearing savage blades, shields, '
             'and arcs of sorcerous energy.'),
            ('Disciples of Tzeentch Pink Horrors', 'Age of Sigmar', 'Disciples of Tzeentch',
             '97-12', decimal.Decimal('30.00'),
             'Ten cackling Pink Horrors of Tzeentch, splitting into Blue Horrors '
             'when slain and hurling magical bolts at enemies.'),

            # ================================================================
            # HORUS HERESY — extended
            # ================================================================
            ('Horus Heresy MKVI Assault Squad', 'Horus Heresy', None,
             'HA-010', decimal.Decimal('50.00'),
             'Ten Space Marine legionaries in Corvus armour with jump packs, '
             'armed with chainswords and bolt pistols.'),
            ('Horus Heresy MKIII Iron Armour Squad', 'Horus Heresy', None,
             'HA-011', decimal.Decimal('55.00'),
             'Twenty Space Marines in MkIII Iron Armour, with full weapons '
             'options for tactical, assault, or support roles.'),
            ('Horus Heresy MKIV Power Armour Squad', 'Horus Heresy', None,
             'HA-012', decimal.Decimal('55.00'),
             'Twenty Space Marines in MkIV Maximus Armour, the most tactically '
             'versatile legionary kit with full weapon upgrades.'),
            ('Horus Heresy Contemptor Dreadnought', 'Horus Heresy', None,
             'HA-020', decimal.Decimal('47.50'),
             'A Contemptor-pattern Dreadnought with poseable arms and '
             'a choice of weapons including multi-melta and assault cannon.'),
            ('Horus Heresy Leviathan Dreadnought', 'Horus Heresy', None,
             'HA-021', decimal.Decimal('75.00'),
             'A massive Leviathan-pattern Dreadnought bearing siege claws, '
             'storm cannons, or graviton flux bombards.'),
            ('Horus Heresy Cataphractii Terminators', 'Horus Heresy', None,
             'HA-030', decimal.Decimal('55.00'),
             'Five Space Marine Terminators in ancient Cataphractii plate, '
             'with combi-bolters, power fists, and heavy weapon options.'),
            ('Horus Heresy Spartan Assault Tank', 'Horus Heresy', None,
             'HA-040', decimal.Decimal('120.00'),
             'A massive super-heavy tank capable of transporting twenty-five '
             'legionaries and armed with quad lascannons.'),
            ('Horus Heresy Sicaran Battle Tank', 'Horus Heresy', None,
             'HA-041', decimal.Decimal('75.00'),
             'A fast-attack tank bearing a twin accelerator autocannon, '
             'cutting down lightly armoured vehicles and infantry alike.'),
            ('Horus Heresy Praetor in Terminator Armour', 'Horus Heresy', None,
             'HA-050', decimal.Decimal('35.00'),
             'A senior officer of a Space Marine Legion in Terminator armour, '
             'with interchangeable weapons and heraldry.'),
            ('Horus Heresy Chaplain in Terminator Armour', 'Horus Heresy', None,
             'HA-051', decimal.Decimal('32.50'),
             'A Chaplain bearing a crozius arcanum and combi-weapon, inspiring '
             'legionaries to die for the primarch\'s glory.'),

            # ================================================================
            # KILL TEAM — boxed sets
            # ================================================================
            ('Kill Team Starter Set', 'Kill Team', None,
             'KT-100', decimal.Decimal('35.00'),
             'Everything needed to play Kill Team: skirmish rules, two kill '
             'teams, and a double-sided game board with terrain.'),
            ('Kill Team: Into the Dark', 'Kill Team', None,
             'KT-101', decimal.Decimal('130.00'),
             'A space hulk Kill Team set pitting Adeptus Mechanicus Hearthkyn '
             'Salvagers against Imperial Navy Breachers on modular terrain.'),
            ('Kill Team: Salvation', 'Kill Team', None,
             'KT-102', decimal.Decimal('130.00'),
             'Sisters of Battle Novitiates face off against the nefarious '
             'Hand of the Archon Drukhari in this two-team Kill Team box.'),
            ('Kill Team: Ashes of Faith', 'Kill Team', None,
             'KT-103', decimal.Decimal('130.00'),
             'Agents of the Inquisition square off against the Chaos Cult of '
             'the Blooded in sprawling hive city terrain.'),
            ('Kill Team: Bheta-Decima', 'Kill Team', None,
             'KT-104', decimal.Decimal('130.00'),
             'T\'au Empire Pathfinder kill teams battle against Leagues of Votann '
             'Hearthkyn Salvagers over a fallen starship\'s wreckage.'),

            # ================================================================
            # NECROMUNDA
            # ================================================================
            ('Necromunda Escher Gang', 'Warhammer 40,000', None,
             'NM-010', decimal.Decimal('45.00'),
             'Ten deadly House Escher gangers — nimble female fighters armed '
             'with lasguns, plasma guns, and vicious chain sabres.'),
            ('Necromunda Goliath Gang', 'Warhammer 40,000', None,
             'NM-011', decimal.Decimal('45.00'),
             'Ten massive House Goliath fighters armed with boltguns, renderizers, '
             'and fighting with pure muscle power.'),
            ('Necromunda Van Saar Gang', 'Warhammer 40,000', None,
             'NM-012', decimal.Decimal('45.00'),
             'Ten technologically advanced Van Saar gangers with lasrifles, '
             'meltaguns, and cutting-edge equipment.'),
            ('Necromunda Underhive Terrain Set', 'Warhammer 40,000', None,
             'NM-020', decimal.Decimal('65.00'),
             'A set of modular underhive terrain pieces for Necromunda — '
             'bulkheads, barricades, and walkways.'),

            # ================================================================
            # WARCRY — boxed sets
            # ================================================================
            ('Warcry Starter Set', 'Age of Sigmar', None,
             'WC-100', decimal.Decimal('55.00'),
             'Complete Warcry introduction: two warbands, modular ruins terrain, '
             'dice, cards, and the full Warcry rules.'),
            ('Warcry: Heart of Ghur', 'Age of Sigmar', None,
             'WC-101', decimal.Decimal('130.00'),
             'A Warcry two-player set pitting Rotmire Creed against Horns of '
             'Hashut warbands amid living jungle terrain.'),
            ('Warcry: Hunter and Hunted', 'Age of Sigmar', None,
             'WC-102', decimal.Decimal('105.00'),
             'Wildercorps Hunters stalk Gorger Mawpack prey in this Warcry '
             'two-player box with open terrain.'),

            # ================================================================
            # CITADEL PAINTS — individual pots and bundles
            # ================================================================
            ('Citadel Layer Paint', 'Paint & Supplies', None,
             'LP-001', decimal.Decimal('4.55'),
             'A single Citadel Layer paint (12ml). Lighter than base paints, '
             'designed for highlighting over a base colour.'),
            ('Citadel Dry Paint', 'Paint & Supplies', None,
             'DP-001', decimal.Decimal('4.55'),
             'A single Citadel Dry paint (12ml). Thick consistency for '
             'drybrushing techniques that pick out raised detail.'),
            ('Citadel Technical Paint', 'Paint & Supplies', None,
             'TCP-001', decimal.Decimal('4.55'),
             'A single Citadel Technical paint (12ml) for special effects: '
             'blood, slime, cracked earth, or rusted metal.'),
            ('Citadel Air Paint', 'Paint & Supplies', None,
             'AP-001', decimal.Decimal('4.55'),
             'A single Citadel Air paint pre-thinned for airbrushing (24ml). '
             'Consistent coverage across large model surfaces.'),
            ('Citadel Shade Agrax Earthshade', 'Paint & Supplies', None,
             'SP-002', decimal.Decimal('5.50'),
             'The essential brown wash — Agrax Earthshade (24ml). Adds depth, '
             'grime, and a realistic aged look to any model.'),
            ('Citadel Shade Reikland Fleshshade', 'Paint & Supplies', None,
             'SP-003', decimal.Decimal('5.50'),
             'A warm flesh-tone shade wash (24ml) ideal for skin, leather, '
             'and wood effects on Warhammer models.'),
            ('Citadel Contrast Wraithbone', 'Paint & Supplies', None,
             'CP-002', decimal.Decimal('7.55'),
             'The definitive Contrast primer colour (18ml). Painted over black '
             'undercoat to create a warm bone-white basecoat.'),
            ('Citadel Contrast Blood Angels Red', 'Paint & Supplies', None,
             'CP-003', decimal.Decimal('7.55'),
             'A deep crimson Contrast paint (18ml) that naturally shades into '
             'recesses for perfect power armour in a single coat.'),
            ('Citadel Spray Chaos Black', 'Paint & Supplies', None,
             'CSP-001', decimal.Decimal('15.00'),
             'The standard Chaos Black undercoat spray (400ml). Provides an '
             'even matt black primer coat for Warhammer models.'),
            ('Citadel Spray Wraithbone', 'Paint & Supplies', None,
             'CSP-002', decimal.Decimal('15.00'),
             'The bone-white undercoat spray (400ml), ideal as a base for '
             'Contrast paints or light colour schemes.'),
            ('Citadel Spray Corax White', 'Paint & Supplies', None,
             'CSP-003', decimal.Decimal('15.00'),
             'A pure white undercoat spray (400ml) for bright colour schemes '
             'including Ultramarines, Iyanden, and Nighthaunt.'),
            ('Citadel Spray Zandri Dust', 'Paint & Supplies', None,
             'CSP-004', decimal.Decimal('15.00'),
             'A warm tan undercoat spray (400ml) suitable as a base for '
             'Contrast paints on Tyranid and T\'au models.'),
            ('Citadel Colour Base Paint Set', 'Paint & Supplies', None,
             'BS-001', decimal.Decimal('32.50'),
             'A set of eleven essential Citadel Base paints covering the most '
             'commonly used colours for Warhammer armies.'),
            ('Citadel Colour Shade Set', 'Paint & Supplies', None,
             'BS-002', decimal.Decimal('27.50'),
             'A set of eight Citadel Shade washes for adding depth and shadow '
             'to any model.'),
            ('Citadel Painting Mat', 'Paint & Supplies', None,
             'PM-001', decimal.Decimal('20.00'),
             'A large (40x60cm) neoprene painting mat protecting your workspace '
             'while keeping brushes and pots in reach.'),
            ('Citadel Water Pot', 'Paint & Supplies', None,
             'WP-001', decimal.Decimal('8.00'),
             'A two-chamber water pot for brush cleaning, with a ribbed base '
             'to remove excess paint and a lid to prevent spills.'),
            ('Citadel Detail Brush Set', 'Paint & Supplies', None,
             'DB-001', decimal.Decimal('22.50'),
             'A set of five Citadel Detail brushes in various sizes, ideal '
             'for precise work on faces, gems, and fine details.'),
            ('Citadel Mouldline Remover', 'Paint & Supplies', None,
             'MR-001', decimal.Decimal('12.00'),
             'A fine-edged tool for shaving mould lines off plastic models '
             'without damaging surrounding detail.'),
            ('Citadel Plastic Glue', 'Paint & Supplies', None,
             'PG-001', decimal.Decimal('6.00'),
             'The standard Citadel plastic glue with a fine applicator brush '
             'for accurate bonding of polystyrene miniature components.'),
            ('Citadel Super Glue', 'Paint & Supplies', None,
             'SG-001', decimal.Decimal('6.00'),
             'Citadel cyanoacrylate super glue for attaching resin, metal, '
             'or mixed media components to plastic models.'),
            ('Citadel Painting Handle XL', 'Paint & Supplies', None,
             'PH-002', decimal.Decimal('16.00'),
             'An extra-large magnetic painting handle for bigger kits like '
             'cavalry, monsters, and vehicles up to 90mm bases.'),
            ('Citadel Colour Contrast Paint Bundle x5', 'Paint & Supplies', None,
             'CP-005', decimal.Decimal('35.00'),
             'Five Citadel Contrast paints of your choice — a starter bundle '
             'for building a Contrast-based painting workflow.'),

            # ================================================================
            # WARHAMMER 40,000 CORE BOOKS & ACCESSORIES
            # ================================================================
            ('Warhammer 40,000 Core Rules', 'Warhammer 40,000', None,
             '40-01', decimal.Decimal('65.00'),
             'The complete Warhammer 40,000 10th Edition hardback rulebook with '
             'full matched play, narrative, and open play rules.'),
            ('Warhammer 40,000 Chapter Approved: Leviathan', 'Warhammer 40,000', None,
             '40-10', decimal.Decimal('35.00'),
             'The essential matched play companion with updated points, missions, '
             'and secondary objectives for 10th Edition.'),
            ('Warhammer 40,000 Dice Set', 'Warhammer 40,000', None,
             '40-20', decimal.Decimal('15.00'),
             'Twenty Warhammer 40,000 dice with the Aquila on the six face, '
             'in classic bone-white with black ink.'),
            ('Warhammer 40,000 Measuring Tape', 'Paint & Supplies', None,
             '40-21', decimal.Decimal('12.00'),
             'A 10-foot retractable Warhammer 40,000 measuring tape with '
             'inch and centimetre markings.'),
            ('Age of Sigmar Core Rules', 'Age of Sigmar', None,
             '80-01', decimal.Decimal('65.00'),
             'The complete Age of Sigmar 3rd Edition hardback core rules with '
             'matched play, Path to Glory, and open play.'),
            ('Age of Sigmar Dice Set', 'Age of Sigmar', None,
             '80-20', decimal.Decimal('15.00'),
             'Twenty Age of Sigmar dice in celestial blue with a hammer symbol '
             'on the six face.'),
            # === KILL TEAM ===
            ('Kill Team: Operatives Datacard Pack 2024', 'Kill Team', None,
             'KT-101', decimal.Decimal('25.00'),
             'Reference datacards for all Kill Team operatives, covering stats, '
             'abilities, and equipment in a handy card format.'),
            ('Kill Team: Void-Dancer Troupe', 'Kill Team', None,
             'KT-102', decimal.Decimal('40.00'),
             'Harlequin operatives bringing acrobatic lethality to the Kill Team '
             'game – a unique and deadly faction.'),
            ('Kill Team: Veteran Guardsmen', 'Kill Team', None,
             'KT-103', decimal.Decimal('40.00'),
             'Battle-hardened Astra Militarum veterans with a wealth of special '
             'weapons and veteran skills for Kill Team.'),
            ('Kill Team: Chaos Legionaries', 'Kill Team', None,
             'KT-104', decimal.Decimal('40.00'),
             'Corrupted Chaos Space Marine operatives armed with dark weapons '
             'and driven by the powers of Chaos.'),
            ('Kill Team: Intercession Squad', 'Kill Team', None,
             'KT-105', decimal.Decimal('40.00'),
             'Elite Primaris Space Marine operatives including specialists with '
             'unique equipment and abilities.'),
            ('Kill Team: Hunter Clade', 'Kill Team', None,
             'KT-106', decimal.Decimal('45.00'),
             'Skitarii Ranger and Vanguard operatives of the Adeptus Mechanicus '
             'hunting heresy with precise, lethal efficiency.'),
            ('Kill Team: Exaction Squad', 'Kill Team', None,
             'KT-107', decimal.Decimal('40.00'),
             'Adeptus Arbites enforcers maintaining the Emperor’s law in the '
             'underhives and void stations of the Imperium.'),
            ('Kill Team: Salvation', 'Kill Team', None,
             'KT-108', decimal.Decimal('130.00'),
             'A Kill Team boxed set pitting Adeptus Arbites against Genestealer '
             'Cult Neophytes in an underhive setting with terrain.'),
            ('Kill Team: Terrain – Killzone Essentials', 'Kill Team', None,
             'KT-109', decimal.Decimal('55.00'),
             'A set of modular terrain pieces for creating Kill Team battlefield '
             'environments, compatible with all killzones.'),
            ('Kill Team: Compendium', 'Kill Team', None,
             'KT-110', decimal.Decimal('40.00'),
             'The essential reference guide containing rules for all Kill Team '
             'factions in one comprehensive volume.'),
            # === ADDITIONAL SPACE MARINES ===
            ('Space Marine Marneus Calgar', 'Warhammer 40,000', 'Ultramarines',
             '55-12', decimal.Decimal('45.00'),
             'Chapter Master of the Ultramarines and Lord Macragge, armed with '
             'the Gauntlets of Ultramar and accompanied by his Honour Guard.'),
            ('Space Marine Roboute Guilliman', 'Warhammer 40,000', 'Ultramarines',
             '55-02', decimal.Decimal('60.00'),
             'The Primarch of the Ultramarines, returned to lead the Imperium. '
             'An iconic centrepiece model armed with the Emperor’s Sword.'),
            ('Space Marine Judiciar', 'Warhammer 40,000', 'Space Marines',
             '48-36', decimal.Decimal('30.00'),
             'A warrior of justice armed with an executioner relic blade, '
             'whose ominous presence slows the enemy’s reactions.'),
            ('Space Marine Primaris Lieutenant', 'Warhammer 40,000', 'Space Marines',
             '48-61', decimal.Decimal('27.50'),
             'A Primaris Lieutenant providing tactical command, armed with a '
             'master-crafted auto bolt rifle and power sword.'),
            ('Space Marine Company Heroes', 'Warhammer 40,000', 'Space Marines',
             '48-37', decimal.Decimal('45.00'),
             'A set of Company Heroes including an Ancient, Company Champion, '
             'and two Bladeguard Veterans supporting the Chapter Master.'),
            ('Space Marine Bladeguard Veterans', 'Warhammer 40,000', 'Space Marines',
             '48-38', decimal.Decimal('45.00'),
             'Three elite Bladeguard Veterans armed with master-crafted power '
             'swords and storm shields – the finest duelists of the Chapter.'),
            ('Space Marine Hammerfall Bunker', 'Warhammer 40,000', 'Space Marines',
             '48-27', decimal.Decimal('52.50'),
             'A deployable fortification dropped from orbit, armed with a '
             'hammerfall missile launcher to provide firebase support.'),
            ('Space Marine Firestrike Servo-Turrets', 'Warhammer 40,000', 'Space Marines',
             '48-28', decimal.Decimal('45.00'),
             'Two twin-linked lascannon or accelerator autocannon turrets '
             'providing automated long-range fire support.'),
            ('Space Marine Eradicators', 'Warhammer 40,000', 'Space Marines',
             '48-39', decimal.Decimal('42.50'),
             'Three Primaris Eradicators carrying melta rifles capable of '
             'reducing even the heaviest vehicles to molten slag.'),
            ('Space Marine Vanguard Veteran Squad', 'Warhammer 40,000', 'Space Marines',
             '48-08', decimal.Decimal('40.00'),
             'Five veterans bearing jump packs and a plethora of melee weapons '
             'including lightning claws and thunder hammers.'),
            # === ADDITIONAL NECRONS ===
            ('Necron Flayed Ones', 'Warhammer 40,000', 'Necrons',
             '49-17', decimal.Decimal('35.00'),
             'Five Necron Flayed Ones, cursed warriors who wear the flesh of '
             'their victims and strike from ambush.'),
            ('Necron Lychguard', 'Warhammer 40,000', 'Necrons',
             '49-11', decimal.Decimal('40.00'),
             'Five Necron Lychguard in ornate ceremonial warplate, serving '
             'as the personal bodyguard of Necron Overlords.'),
            ('Necron Canoptek Spyder', 'Warhammer 40,000', 'Necrons',
             '49-14', decimal.Decimal('30.00'),
             'A single Canoptek Spyder repairing and reanimating nearby Necron '
             'warriors in the heat of battle.'),
            ('Necron Doom Scythe', 'Warhammer 40,000', 'Necrons',
             '49-13', decimal.Decimal('42.50'),
             'A fast attack flyer armed with a death ray and twin tesla '
             'destructors, devastating enemy formations from the air.'),
            ('Necron Doomsday Ark', 'Warhammer 40,000', 'Necrons',
             '49-12', decimal.Decimal('52.50'),
             'A massive Necron artillery vehicle armed with a doomsday cannon '
             'capable of vaporising entire squads in a single shot.'),
            ('Necron C’tan Shard of the Void Dragon', 'Warhammer 40,000', 'Necrons',
             '49-20', decimal.Decimal('55.00'),
             'A fragment of the god of machines, imprisoned by the Necron '
             'nobles and unleashed upon the battlefield as a weapon.'),
            ('Necron Psychomancer', 'Warhammer 40,000', 'Necrons',
             '49-21', decimal.Decimal('25.00'),
             'A Cryptek specialist who weaponises fear and illusion, driving '
             'enemy minds to madness on the battlefield.'),
            ('Necron Royal Warden', 'Warhammer 40,000', 'Necrons',
             '49-22', decimal.Decimal('22.50'),
             'An enforcer of the Necron Overlord’s will, armed with a relic '
             'gauss blaster and bearing authority to execute deserters.'),
            # === ADDITIONAL ORKS ===
            ('Ork Nobz', 'Warhammer 40,000', 'Orks',
             '50-09', decimal.Decimal('35.00'),
             'Five Ork Nobz, the biggest and meanest Boyz in a mob, armed '
             'with power klaws, big choppas, and kombi-weapons.'),
            ('Ork Meganobz', 'Warhammer 40,000', 'Orks',
             '50-12', decimal.Decimal('47.50'),
             'Three Meganobz in mega armour, nigh-unstoppable Ork elites '
             'carrying power klaws and kombi-shootas.'),
            ('Ork Deff Dread', 'Warhammer 40,000', 'Orks',
             '50-16', decimal.Decimal('35.00'),
             'A ramshackle Ork walker piloted by a crazed Ork, armed with '
             'klaws, drills, saws, and sluggas in all configurations.'),
            ('Ork Killa Kans', 'Warhammer 40,000', 'Orks',
             '50-15', decimal.Decimal('42.50'),
             'Three Killa Kans – small walkers piloted by crazed Gretchin '
             'with a variety of scavenged weapons.'),
            ('Ork Battlewagon', 'Warhammer 40,000', 'Orks',
             '50-22', decimal.Decimal('67.50'),
             'A massive Ork troop carrier and heavy transport armed with '
             'a deff rolla, big shootas, and extensive upgrades.'),
            ('Ork Trukk', 'Warhammer 40,000', 'Orks',
             '50-11', decimal.Decimal('30.00'),
             'An Ork troop transport built from scrap, capable of delivering '
             'a mob of Boyz into combat with reckless speed.'),
            ('Ork Warboss in Mega Armour', 'Warhammer 40,000', 'Orks',
             '50-02', decimal.Decimal('35.00'),
             'The biggest Ork wearing the biggest armour – a warlord in '
             'mega armour with a klaw and shootier weapons.'),
            ('Ork Flash Gitz', 'Warhammer 40,000', 'Orks',
             '50-20', decimal.Decimal('40.00'),
             'Five flashily armoured Ork pirates with snazzguns – the '
             'wealthiest and vainest Orks in any Waaagh!'),
            ('Ork Combat Patrol', 'Warhammer 40,000', 'Orks',
             '71-18', decimal.Decimal('105.00'),
             'Start your Waaagh! with a Warboss, Boyz, Deff Koptas, '
             'and a Deff Dread in this ready-to-play Combat Patrol.'),
            # === ADDITIONAL AGE OF SIGMAR ===
            ('Nighthaunt Chainrasps', 'Age of Sigmar', 'Nighthaunt',
             '91-28', decimal.Decimal('35.00'),
             'Twenty spectral Chainrasp Hordes – the mournful spirits who '
             'form the core of any Nighthaunt force.'),
            ('Nighthaunt Knight of Shrouds', 'Age of Sigmar', 'Nighthaunt',
             '91-15', decimal.Decimal('22.50'),
             'A single Knight of Shrouds on ethereal steed, a powerful '
             'Nighthaunt commander capable of emboldening nearby spirits.'),
            ('Nighthaunt Hexwraiths', 'Age of Sigmar', 'Nighthaunt',
             '91-06', decimal.Decimal('35.00'),
             'Five spectral horsemen who drain the life from mortals they '
             'ride through, impossible to stop with mortal weapons.'),
            ('Ossiarch Bonereapers Mortek Guard', 'Age of Sigmar', 'Ossiarch Bonereapers',
             '94-10', decimal.Decimal('42.50'),
             'Twenty Mortek Guard – the unyielding infantry of the Ossiarch '
             'legions, armed with nadirite blades and shields.'),
            ('Ossiarch Bonereapers Gothizzar Harvester', 'Age of Sigmar', 'Ossiarch Bonereapers',
             '94-12', decimal.Decimal('52.50'),
             'A bone-harvesting construct that collects the remains of the '
             'slain to repair and reinforce nearby Mortek Guard.'),
            ('Flesh-Eater Courts Crypt Ghouls', 'Age of Sigmar', 'Flesh-Eater Courts',
             '91-35', decimal.Decimal('35.00'),
             'Twenty Crypt Ghouls – the delusional flesh-eating servants of '
             'the Abhorrant Archregent, believing themselves noble warriors.'),
            ('Flesh-Eater Courts Terrorgheist', 'Age of Sigmar', 'Flesh-Eater Courts',
             '91-32', decimal.Decimal('55.00'),
             'A massive undead bat-dragon that serves as the centrepiece of '
             'any Flesh-Eater Courts army.'),
            ('Gloomspite Gitz Squig Hoppers', 'Age of Sigmar', 'Gloomspite Gitz',
             '89-11', decimal.Decimal('35.00'),
             'Five Squig Hoppers bounding unpredictably across the battlefield '
             'on their mouth-on-legs squig mounts.'),
            ('Gloomspite Gitz Fanatics', 'Age of Sigmar', 'Gloomspite Gitz',
             '89-06', decimal.Decimal('30.00'),
             'Five Fanatics swinging enormous balls and chains in manic frenzy '
             'hidden inside Moonclan Grots until the moment of attack.'),
            ('Orruk Warclans Ardboys', 'Age of Sigmar', 'Orruk Warclans',
             '89-30', decimal.Decimal('35.00'),
             'Ten heavily armoured Orruk Ardboys carrying choppas, shields, '
             'and bows – reliable infantry for any Ironjawz or Bonesplitterz list.'),
            ('Daughters of Khaine Sisters of Slaughter', 'Age of Sigmar', 'Daughters of Khaine',
             '85-17', decimal.Decimal('40.00'),
             'Ten fanatic warriors of Khaine armed with blade bucklers and '
             'sacrificial knives, frenzied in battle.'),
            ('Lumineth Realm-lords Vanari Auralan Wardens', 'Age of Sigmar', 'Lumineth Realm-lords',
             '87-10', decimal.Decimal('42.50'),
             'Ten Vanari Auralan Wardens wielding long sun spears – the '
             'disciplined pinnacle of Lumineth defensive warfare.'),
            ('Cities of Sigmar Freeguild Fusiliers', 'Age of Sigmar', 'Cities of Sigmar',
             '86-15', decimal.Decimal('42.50'),
             'Ten Freeguild Fusiliers armed with handguns and pistols, '
             'the black-powder ranged core of any Cities force.'),
            ('Slaves to Darkness Chaos Warriors', 'Age of Sigmar', 'Slaves to Darkness',
             '83-18', decimal.Decimal('42.50'),
             'Ten Chaos Warriors clad in ensorcelled plate armour, wielding '
             'hand weapons and shields in service of the dark gods.'),
            ('Blades of Khorne Bloodletters', 'Age of Sigmar', 'Blades of Khorne',
             '97-08', decimal.Decimal('35.00'),
             'Ten Bloodletters – the foot soldiers of Khorne, armed with '
             'hellblades and driven by boundless fury.'),
            ('Maggotkin of Nurgle Plaguebearers', 'Age of Sigmar', 'Maggotkin of Nurgle',
             '97-09', decimal.Decimal('35.00'),
             'Ten Plaguebearers of Nurgle, putrid daemons carrying plagueswords '
             'and spreading corruption across the Mortal Realms.'),
            ('Disciples of Tzeentch Pink Horrors', 'Age of Sigmar', 'Disciples of Tzeentch',
             '97-11', decimal.Decimal('35.00'),
             'Ten Pink Horrors of Tzeentch, magical daemons who split into '
             'Blue Horrors when slain. A core unit of any Tzeentch force.'),
            ('Stormcast Eternals Praetors', 'Age of Sigmar', 'Stormcast Eternals',
             '96-55', decimal.Decimal('42.50'),
             'Three Praetors – the elite bodyguard of the Lord-Commander, '
             'armed with halberd-length stormstrike glaives.'),
            ('Stormcast Eternals Vindictors', 'Age of Sigmar', 'Stormcast Eternals',
             '96-50', decimal.Decimal('42.50'),
             'Five Vindictors in heavy plate armour with stormspears and '
             'shields – the dependable core infantry of any Stormhost.'),
            ('Skaven Plague Monks', 'Age of Sigmar', 'Skaven',
             '90-12', decimal.Decimal('30.00'),
             'Twenty fanatical Plague Monks of Clan Pestilens, spreading '
             'disease and decay with foetid blades.'),
            # === HORUS HERESY — more units ===
            ('Legiones Astartes MKIII Infantry Squad', 'Horus Heresy', None,
             'HA-010', decimal.Decimal('45.00'),
             'Ten Space Marine legionaries in Mark III Iron Armour – the '
             'original heresy-era close-assault armour variant.'),
            ('Legiones Astartes Cataphractii Terminators', 'Horus Heresy', None,
             'HA-011', decimal.Decimal('55.00'),
             'Five Terminators in the ancient Cataphractii pattern plate, '
             'the heaviest armour available to the Legiones Astartes.'),
            ('Legiones Astartes Predator', 'Horus Heresy', None,
             'HA-012', decimal.Decimal('57.50'),
             'The classic Predator tank in Heresy-era configuration, armed '
             'with a predator cannon or twin lascannons.'),
            ('Legiones Astartes Spartan Assault Tank', 'Horus Heresy', None,
             'HA-013', decimal.Decimal('105.00'),
             'A massive super-heavy assault tank capable of transporting '
             'twenty Terminators into the heart of the enemy.'),
            ('Solar Auxilia Lasrifle Section', 'Horus Heresy', None,
             'HA-020', decimal.Decimal('45.00'),
             'Ten elite Solar Auxilia infantry armed with volkite chargers '
             'and las-rifles, the best conventional troops of the Heresy era.'),
            # === CITADEL PAINTS ===
            ('Citadel Layer Paint', 'Paint & Supplies', None,
             'LP-001', decimal.Decimal('4.55'),
             'A single Citadel Layer paint (12ml), formulated for highlighting '
             'over base coats to add depth and detail.'),
            ('Citadel Dry Paint', 'Paint & Supplies', None,
             'DP-001', decimal.Decimal('4.55'),
             'A single Citadel Dry paint (12ml) for drybrushing effects, '
             'with a thick consistency that picks out raised details.'),
            ('Citadel Technical Paint (Nihilakh Oxide)', 'Paint & Supplies', None,
             'TE-001', decimal.Decimal('5.50'),
             'A weathering paint that creates verdigris and corrosion effects '
             'in the recesses of aged brass and bronze models.'),
            ('Citadel Air Paint', 'Paint & Supplies', None,
             'AP-001', decimal.Decimal('6.30'),
             'A single pre-thinned Citadel Air paint (24ml) ready for use '
             'with an airbrush without further thinning needed.'),
            ('Citadel Spray: Chaos Black', 'Paint & Supplies', None,
             'SP-010', decimal.Decimal('15.00'),
             'A 400ml aerosol spray primer in Chaos Black, providing an '
             'excellent base coat for dark colour schemes.'),
            ('Citadel Spray: Wraithbone', 'Paint & Supplies', None,
             'SP-011', decimal.Decimal('15.00'),
             'A 400ml aerosol spray primer in Wraithbone, the ideal base '
             'for contrast and bright colour schemes.'),
            ('Citadel Spray: Grey Seer', 'Paint & Supplies', None,
             'SP-012', decimal.Decimal('15.00'),
             'A 400ml aerosol spray primer in Grey Seer – the best base '
             'colour for Contrast paints on a neutral mid-grey.'),
            ('Citadel Munitorum Varnish', 'Paint & Supplies', None,
             'SP-020', decimal.Decimal('15.00'),
             'A 400ml aerosol matt varnish that protects painted models '
             'from chipping and wear without affecting colour.'),
            ('Citadel Brush: Medium Base', 'Paint & Supplies', None,
             'BR-001', decimal.Decimal('6.30'),
             'A medium-sized Citadel Base brush, ideal for basecoating '
             'infantry models and vehicles quickly and evenly.'),
            ('Citadel Brush: Medium Layer', 'Paint & Supplies', None,
             'BR-002', decimal.Decimal('6.30'),
             'A medium Citadel Layer brush for painting details, layering '
             'highlights, and applying Contrast paints with precision.'),
            ('Citadel Hobby Knife', 'Paint & Supplies', None,
             'HK-001', decimal.Decimal('12.00'),
             'A precision hobby knife with a replaceable blade for cutting '
             'plastic sprues, trimming mould lines, and fine conversion work.'),
            ('Citadel Plastic Glue', 'Paint & Supplies', None,
             'PG-001', decimal.Decimal('6.00'),
             'A 25ml tube of Citadel plastic glue that bonds plastic '
             'components with a strong, invisible join.'),
        ]

        # Re-use the faction lookup built in _create_products
        faction_lookup = Faction.objects.in_bulk(field_name='name')

        products = []
        for (name, cat_name, faction_name, gw_sku, msrp, description) in extended_data:
            cat = Category.objects.filter(name=cat_name).first()
            faction = faction_lookup.get(faction_name) if faction_name else None

            base_slug = slugify(name)
            # Ensure slug is unique — append gw_sku suffix if a different
            # product already occupies the base slug.
            slug = base_slug
            existing = Product.objects.filter(slug=base_slug).exclude(gw_sku=gw_sku).first()
            if existing:
                slug = f"{base_slug}-{slugify(gw_sku)}"
            product, created = Product.objects.update_or_create(
                gw_sku=gw_sku,
                defaults={
                    'name': name,
                    'slug': slug,
                    'gw_sku': gw_sku,
                    'category': cat,
                    'faction': faction,
                    'description': description,
                    'msrp': msrp,
                    'is_active': True,
                    'image_url': (
                        f'https://placehold.co/400x300/1c2230/c8922a'
                        f'?text={slugify(name)[:30]}'
                    ),
                },
            )
            products.append(product)
            status = 'created' if created else 'updated'
            self.stdout.write(f'  [{status}] {name} — ${msrp}')

        self.stdout.write(
            self.style.SUCCESS(f'  Extended catalog: {len(products)} products processed.')
        )
        return products

    # -------------------------------------------------------------------------
    # Price seed data
    # -------------------------------------------------------------------------

    def _create_prices(self, products, retailers):
        """
        Create realistic current prices for each product across retailers.

        Rules:
        - Games Workshop always charges the full MSRP
        - Miniature Market discounts 15–25% (best US deals)
        - Noble Knight Games discounts 10–18%
        - eBay: variable 5–25% off
        - Amazon may be cheaper or more expensive (small random variance)
        - Some products are out of stock at random retailers
        """
        self.stdout.write('Creating prices…')
        gw = retailers.get('Games Workshop')
        mm = retailers.get('Miniature Market')
        nk = retailers.get('Noble Knight Games')
        ebay = retailers.get('eBay')
        amazon = retailers.get('Amazon')

        price_count = 0

        for product in products:
            if not product.msrp:
                continue

            msrp = product.msrp

            # GW always sells at full price, always in stock
            self._upsert_price(
                product=product,
                retailer=gw,
                price=msrp,
                in_stock=True,
                url=f'https://www.games-workshop.com/en-US/search?query={product.gw_sku}',
            )
            price_count += 1

            # Miniature Market: 15–25% off — strong US discount retailer
            if mm and msrp >= 10:
                discount = decimal.Decimal(str(round(random.uniform(0.15, 0.25), 2)))
                mm_price = self._apply_discount(msrp, discount)
                in_stock = random.random() > 0.1  # 90% in stock
                self._upsert_price(
                    product=product,
                    retailer=mm,
                    price=mm_price,
                    in_stock=in_stock,
                    url=f'https://www.miniaturemarket.com/search/?q={product.gw_sku}',
                )
                price_count += 1

            # Noble Knight Games: 10–18% off, usually in stock
            if nk:
                discount = decimal.Decimal(str(round(random.uniform(0.10, 0.18), 2)))
                nk_price = self._apply_discount(msrp, discount)
                in_stock = random.random() > 0.15
                self._upsert_price(
                    product=product,
                    retailer=nk,
                    price=nk_price,
                    in_stock=in_stock,
                    url=f'https://www.nobleknight.com/Products/Warhammer?q={product.gw_sku}',
                )
                price_count += 1

            # eBay: variable pricing – can be 5–25% off but sometimes higher
            if ebay and msrp >= 15:
                import urllib.parse
                discount = decimal.Decimal(str(round(random.uniform(0.05, 0.25), 2)))
                ebay_price = self._apply_discount(msrp, discount)
                in_stock = random.random() > 0.25
                search_term = urllib.parse.quote_plus(f'{product.name} warhammer games workshop')
                self._upsert_price(
                    product=product,
                    retailer=ebay,
                    price=ebay_price,
                    in_stock=in_stock,
                    url=f'https://www.ebay.com/sch/i.html?_nkw={search_term}&LH_BIN=1&_sop=15',
                )
                price_count += 1

            # Amazon: 5–15% off but less reliable stock
            if amazon and msrp >= 20:
                discount = decimal.Decimal(str(round(random.uniform(0.05, 0.15), 2)))
                az_price = self._apply_discount(msrp, discount)
                in_stock = random.random() > 0.3
                self._upsert_price(
                    product=product,
                    retailer=amazon,
                    price=az_price,
                    in_stock=in_stock,
                    url=f'https://www.amazon.com/s?k={product.name}+warhammer',
                )
                price_count += 1

        self.stdout.write(f'  Created/updated {price_count} prices.')

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _apply_discount(msrp, discount_fraction):
        """
        Calculate a discounted price, rounded to nearest 5p.

        Args:
            msrp: Decimal MSRP price
            discount_fraction: Decimal fraction to discount (e.g. 0.15 = 15%)

        Returns:
            Decimal price rounded to 2dp
        """
        raw = msrp * (1 - discount_fraction)
        # Round to nearest 5p for realistic retail pricing
        rounded = round(float(raw) / 0.05) * 0.05
        return decimal.Decimal(str(rounded)).quantize(decimal.Decimal('0.01'))

    @staticmethod
    def _upsert_price(product, retailer, price, in_stock, url):
        """
        Create or update a CurrentPrice record for a product/retailer pair.

        Uses update_or_create to keep the command idempotent.
        """
        if not retailer:
            return
        CurrentPrice.objects.update_or_create(
            product=product,
            retailer=retailer,
            defaults={
                'price': price,
                'in_stock': in_stock,
                'url': url,
            },
        )
