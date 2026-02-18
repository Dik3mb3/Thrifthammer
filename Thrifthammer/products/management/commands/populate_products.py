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
        self._create_prices(products, retailers)

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created/updated:\n'
            f'  {len(categories)} categories\n'
            f'  {len(factions)} factions\n'
            f'  {len(retailers)} retailers\n'
            f'  {len(products)} products\n'
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
            ('Boxed Games', 'Two-player and starter box sets with everything to play.'),
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
            ('Space Marines', 'Warhammer 40,000'),
            ('Blood Angels', 'Warhammer 40,000'),
            ('Ultramarines', 'Warhammer 40,000'),
            ('Chaos Space Marines', 'Warhammer 40,000'),
            ('Tyranids', 'Warhammer 40,000'),
            ('Necrons', 'Warhammer 40,000'),
            ('Orks', 'Warhammer 40,000'),
            ('T\'au Empire', 'Warhammer 40,000'),
            ('Stormcast Eternals', 'Age of Sigmar'),
            ('Skaven', 'Age of Sigmar'),
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
                'name': 'Tower of Games',
                'website': 'https://www.towerofgames.com',
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
            # ---- Boxed Games ----
            (
                'Leviathan (10th Edition Starter Set)',
                'Boxed Games', None,
                '40-02', decimal.Decimal('145.00'),
                'The huge 10th Edition launch box. Contains Space Marine '
                'and Tyranid forces, a 376-page hardback rulebook, dice, '
                'and terrain. Superb value.',
            ),
            (
                'Warhammer 40,000 Starter Set',
                'Boxed Games', None,
                '40-03', decimal.Decimal('50.00'),
                'A compact starter with push-fit Space Marines and Tyranids, '
                'a small rulebook, and all you need to play your first game.',
            ),
            (
                'Combat Patrol: Space Marines',
                'Boxed Games', 'Space Marines',
                '71-02', decimal.Decimal('105.00'),
                'A ready-to-play Combat Patrol force of Space Marines: '
                'Captain, Redemptor Dreadnought, Intercessors, and Outriders.',
            ),
            (
                'Age of Sigmar Warrior Starter Set',
                'Boxed Games', None,
                '80-15', decimal.Decimal('35.00'),
                'The perfect introduction to Age of Sigmar: Stormcast Eternals '
                'vs Kruleboyz Orks, with a Getting Started guide.',
            ),
            (
                'Horus Heresy: Age of Darkness',
                'Boxed Games', None,
                'HH-001', decimal.Decimal('180.00'),
                'The massive Horus Heresy launch box. 54 plastic Mk VI Space '
                'Marines, vehicles, and the complete rulebook.',
            ),
            (
                'Warcry: Red Harvest',
                'Boxed Games', None,
                'WC-001', decimal.Decimal('105.00'),
                'A two-player Warcry skirmish set with two rival warbands, '
                'modular terrain, and complete rules.',
            ),
            (
                'Necromunda: Hive War',
                'Boxed Games', None,
                'NM-001', decimal.Decimal('80.00'),
                'The Necromunda two-player gang warfare set with Escher and '
                'Delaque gangs, plus terrain and rules.',
            ),
            (
                'Kill Team: Nightmare',
                'Boxed Games', None,
                'KT-001', decimal.Decimal('130.00'),
                'A Kill Team box with Chaos Legionaries vs Wyrmblade Genestealer '
                'Cult operatives, terrain, and full Kill Team rules.',
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
    # Price seed data
    # -------------------------------------------------------------------------

    def _create_prices(self, products, retailers):
        """
        Create realistic current prices for each product across retailers.

        Rules:
        - Games Workshop always charges the full MSRP
        - Miniature Market discounts 15–25% (best US deals)
        - Noble Knight Games discounts 10–18%
        - Tower of Games discounts 10–20%
        - Amazon may be cheaper or more expensive (small random variance)
        - Some products are out of stock at random retailers
        """
        self.stdout.write('Creating prices…')
        gw = retailers.get('Games Workshop')
        mm = retailers.get('Miniature Market')
        nk = retailers.get('Noble Knight Games')
        tower = retailers.get('Tower of Games')
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

            # Tower of Games: 10–20% off, good stock
            if tower:
                discount = decimal.Decimal(str(round(random.uniform(0.10, 0.20), 2)))
                tower_price = self._apply_discount(msrp, discount)
                in_stock = random.random() > 0.2
                self._upsert_price(
                    product=product,
                    retailer=tower,
                    price=tower_price,
                    in_stock=in_stock,
                    url=f'https://www.towerofgames.com/search?q={product.name}',
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
