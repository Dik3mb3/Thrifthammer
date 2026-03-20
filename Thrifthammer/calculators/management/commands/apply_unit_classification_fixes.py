"""
Management command: apply_unit_classification_fixes

Corrects UnitType.category values and deactivates confirmed duplicate units
so that the Army Calculator shows the right battlefield roles.

Changes applied (10th Edition):
  Adeptus Mechanicus
    - Ironstrider Ballistarii: infantry -> vehicle
    - Kataphron Destroyers: mounted -> infantry

  Astra Militarum
    - Commissar: infantry -> character
    - Sentinel: mounted -> vehicle

  Space Marines (base faction)
    - Company Heroes: character -> infantry
    - Inceptors: mounted -> infantry
    - Hammerfall Bunker: transport -> fortification
    - Firestrike Servo-Turrets: fortification -> vehicle

  Black Templars
    - Emperor's Champion: infantry -> character
    - High Marshal Helbrecht: infantry -> epic_hero
    - Company Heroes: character -> infantry
    - Inceptor Squad: mounted -> infantry
    - Hammerfall Bunker: transport -> fortification
    - Firestrike Servo-Turrets: fortification -> vehicle
    - Tactical Squad: infantry -> battleline

  Blood Angels
    - Company Heroes: character -> infantry
    - Infernus Squad: battleline -> infantry
    - Tactical Squad: infantry -> battleline
    - Inceptor Squad: mounted -> infantry
    - Firestrike Servo-Turrets: fortification -> vehicle

  Dark Angels -- shared SM fixes
    - Company Heroes: character -> infantry
    - Infernus Squad: battleline -> infantry
    - Tactical Squad: infantry -> battleline
    - Inceptor Squad: mounted -> infantry
    - Firestrike Servo-Turrets: fortification -> vehicle
  Dark Angels -- unique unit fixes
    - Azrael: infantry -> epic_hero
    - Lion El'Jonson: infantry -> epic_hero
    - Asmodai/Belial/Ezekiel/Lazarus/Sammael/Ravenwing Command Squad: infantry -> character
    - Nephilim Jetfighter/Ravenwing Dark Talon/Ravenwing Darkshroud: infantry -> vehicle
    - Deathwing Knights: vehicle -> infantry
    - Ravenwing Black Knights: vehicle -> mounted

  Death Guard
    - Blightlord Terminators: character -> infantry
    - Poxwalkers: vehicle -> infantry
    - Foetid Bloat-drone: infantry -> vehicle

  Deathwatch -- shared SM fixes
    - Company Heroes: character -> infantry
    - Infernus Squad: battleline -> infantry
    - Tactical Squad: infantry -> battleline
    - Inceptor Squad: mounted -> infantry
    - Firestrike Servo-Turrets: fortification -> vehicle
    - Watch Master: infantry -> character

  Drukhari
    - Archon: epic_hero -> character

  Genestealer Cults
    - Patriarch: epic_hero -> character

  Grey Knights
    - Strike Squad: vehicle -> battleline
    - Terminators: vehicle -> infantry
    - Grand Master Voldus: character -> epic_hero
    - Chaplain (GK-specific UnitType): created if missing
    - Librarian (GK-specific UnitType): created if missing
    - parent_faction cleared (GK uses own datasheets only)

  Aeldari (formerly Craftworlds)
    - Dire Avengers: battleline -> infantry
    - Guardians: infantry -> battleline
  Craftworlds -> Aeldari rename (faction, products, units)

  Leagues of Votann
    - Hernkyn Pioneers: infantry -> mounted
    - Kahl: infantry -> character

  Necrons
    - C'tan Shard of the Void Dragon: infantry -> epic_hero
    - Canoptek Spyder: infantry -> vehicle
    - Doom Scythe: infantry -> vehicle
    - Immortals: infantry -> battleline
    - Psychomancer: infantry -> character
    - Royal Warden: infantry -> character

  Orks
    - Warboss in Mega Armour: epic_hero -> character

  Sisters of Battle (Adepta Sororitas)
    - Morvenn Vahl: infantry -> epic_hero

  Space Marines (base)
    - Infernus Squad: battleline -> infantry
    - Repulsor Executioner: transport -> vehicle

  Space Wolves
    - Ragnar Blackmane: infantry -> epic_hero
    - Wolf Guard Terminators: infantry -> infantry (already correct, kept for dedup check)

  T'au Empire
    - Riptide Battlesuit: character -> vehicle
    - Pathfinders: battleline -> infantry
    - Broadside Battlesuit: infantry -> vehicle
    - Crisis Battlesuits: infantry -> vehicle
    - Hammerhead Gunship: infantry -> vehicle
    - Stealth Battlesuits: infantry -> infantry (already correct)

  Tyranids
    - Hive Tyrant: epic_hero -> character
    - Carnifex: infantry -> monster

  Ultramarines
    - Marneus Calgar: infantry -> epic_hero

  World Eaters
    - Eightbound: battleline -> infantry

Deactivations (confirmed duplicates -- same product as parent SM unit):
  Black Templars, Blood Angels, Dark Angels, Deathwatch:
    - Aggressor Squad, Eradicator Squad, Terminator Squad (48-06),
      Assault Intercessor Squad
  NOTE: DA Terminator Squad deactivation targets SKU 48-06 only --
        Deathwing Terminator Squad (44-11) is preserved.

Usage:
    python manage.py apply_unit_classification_fixes

This command is fully idempotent -- safe to re-run at any time.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product


# ---------------------------------------------------------------------------
# Category reclassifications -- each entry:
#   (faction_name, unit_name_icontains, new_category)
# ---------------------------------------------------------------------------
RECLASSIFICATIONS = [
    # -- Adeptus Mechanicus --------------------------------------------------
    ('Adeptus Mechanicus', 'Ironstrider Ballistarii', 'vehicle'),
    ('Adeptus Mechanicus', 'Kataphron Destroyers',    'infantry'),

    # -- Astra Militarum -----------------------------------------------------
    ('Astra Militarum', 'Commissar', 'character'),
    ('Astra Militarum', 'Sentinel',  'vehicle'),

    # -- Space Marines (base faction) ----------------------------------------
    ('Space Marines', 'Company Heroes',           'infantry'),
    ('Space Marines', 'Inceptors',                'infantry'),
    ('Space Marines', 'Hammerfall Bunker',         'fortification'),
    ('Space Marines', 'Firestrike Servo-Turrets',  'vehicle'),

    # -- Black Templars ------------------------------------------------------
    ('Black Templars', "Emperor's Champion",      'character'),
    ('Black Templars', 'High Marshal Helbrecht',  'epic_hero'),
    ('Black Templars', 'Company Heroes',          'infantry'),
    ('Black Templars', 'Inceptor Squad',          'infantry'),
    ('Black Templars', 'Hammerfall Bunker',        'fortification'),
    ('Black Templars', 'Firestrike Servo-Turrets', 'vehicle'),
    ('Black Templars', 'Tactical Squad',           'battleline'),

    # -- Blood Angels -- shared SM fixes -------------------------------------
    ('Blood Angels', 'Company Heroes',           'infantry'),
    ('Blood Angels', 'Infernus Squad',           'infantry'),
    ('Blood Angels', 'Tactical Squad',           'battleline'),
    ('Blood Angels', 'Inceptor Squad',           'infantry'),
    ('Blood Angels', 'Firestrike Servo-Turrets', 'vehicle'),

    # -- Dark Angels -- shared SM fixes --------------------------------------
    ('Dark Angels', 'Company Heroes',           'infantry'),
    ('Dark Angels', 'Infernus Squad',           'infantry'),
    ('Dark Angels', 'Tactical Squad',           'battleline'),
    ('Dark Angels', 'Inceptor Squad',           'infantry'),
    ('Dark Angels', 'Firestrike Servo-Turrets', 'vehicle'),

    # -- Dark Angels -- unique named characters ------------------------------
    ('Dark Angels', 'Dark Angels Azrael',                  'epic_hero'),
    ("Dark Angels", "Dark Angels Lion El'Jonson",          'epic_hero'),
    ('Dark Angels', 'Dark Angels Ezekiel',                 'epic_hero'),
    ('Dark Angels', 'Dark Angels Asmodai',                 'character'),
    ('Dark Angels', 'Dark Angels Belial',                  'character'),
    ('Dark Angels', 'Dark Angels Lazarus',                 'character'),
    ('Dark Angels', 'Dark Angels Sammael',                 'character'),
    ('Dark Angels', 'Dark Angels Ravenwing Command Squad', 'character'),

    # -- Dark Angels -- unique vehicles / flyers -----------------------------
    ('Dark Angels', 'Dark Angels Nephilim Jetfighter',     'vehicle'),
    ('Dark Angels', 'Dark Angels Ravenwing Dark Talon',    'vehicle'),
    ('Dark Angels', 'Dark Angels Ravenwing Darkshroud',    'vehicle'),

    # -- Dark Angels -- unique infantry / cavalry ----------------------------
    ('Dark Angels', 'Dark Angels Deathwing Knights',       'infantry'),
    ('Dark Angels', 'Dark Angels Ravenwing Black Knights', 'mounted'),

    # -- Death Guard ---------------------------------------------------------
    ('Death Guard', 'Blightlord Terminators', 'infantry'),
    ('Death Guard', 'Poxwalkers',             'infantry'),
    ('Death Guard', 'Bloat-drone',            'vehicle'),

    # -- Deathwatch -- shared SM fixes ---------------------------------------
    ('Deathwatch', 'Company Heroes',           'infantry'),
    ('Deathwatch', 'Infernus Squad',           'infantry'),
    ('Deathwatch', 'Tactical Squad',           'battleline'),
    ('Deathwatch', 'Inceptor Squad',           'infantry'),
    ('Deathwatch', 'Firestrike Servo-Turrets', 'vehicle'),
    ('Deathwatch', 'Watch Master',             'character'),

    # -- Drukhari ------------------------------------------------------------
    ('Drukhari', 'Archon', 'character'),

    # -- Genestealer Cults ---------------------------------------------------
    ('Genestealer Cults', 'Patriarch', 'character'),

    # -- Grey Knights --------------------------------------------------------
    ('Grey Knights', 'Strike Squad',        'battleline'),
    ('Grey Knights', 'Terminators',         'infantry'),
    ('Grey Knights', 'Grand Master Voldus', 'epic_hero'),

    # -- Craftworlds (Aeldari) -----------------------------------------------
    ('Craftworlds', 'Dire Avengers', 'infantry'),
    ('Craftworlds', 'Guardians',     'battleline'),

    # -- Leagues of Votann ---------------------------------------------------
    ('Leagues of Votann', 'Hernkyn Pioneers', 'mounted'),
    ('Leagues of Votann', 'Kahl',             'character'),

    # -- Necrons -------------------------------------------------------------
    ('Necrons', 'Void Dragon',                    'epic_hero'),  # C'tan Shard of the Void Dragon
    ('Necrons', 'Canoptek Spyder',                'vehicle'),
    ('Necrons', 'Doom Scythe',                    'vehicle'),
    ('Necrons', 'Immortals',                      'battleline'),
    ('Necrons', 'Psychomancer',                   'character'),
    ('Necrons', 'Royal Warden',                   'character'),

    # -- Orks ----------------------------------------------------------------
    ('Orks', 'Warboss in Mega Armour', 'character'),

    # -- Sisters of Battle (units stored under this faction name) ------------
    ('Sisters of Battle', 'Morvenn Vahl', 'epic_hero'),

    # -- Space Marines (base) ------------------------------------------------
    ('Space Marines', 'Infernus Squad',          'infantry'),
    ('Space Marines', 'Repulsor Executioner',     'vehicle'),

    # -- Space Marines sub-factions: Infernus Squad + Repulsor Executioner --
    ('Black Templars',  'Infernus Squad',          'infantry'),
    ('Blood Angels',    'Repulsor Executioner',    'vehicle'),
    ('Dark Angels',     'Infernus Squad',          'infantry'),
    ('Dark Angels',     'Repulsor Executioner',    'vehicle'),
    ('Deathwatch',      'Repulsor Executioner',    'vehicle'),
    ('Space Wolves',    'Infernus Squad',          'infantry'),
    ('Space Wolves',    'Repulsor Executioner',    'vehicle'),
    ('Ultramarines',    'Infernus Squad',          'infantry'),
    ('Ultramarines',    'Repulsor Executioner',    'vehicle'),

    # -- Space Wolves unique characters --------------------------------------
    ('Space Wolves', 'Ragnar Blackmane', 'epic_hero'),

    # -- T'au Empire ---------------------------------------------------------
    ("T'au Empire", 'Riptide Battlesuit',    'vehicle'),
    ("T'au Empire", 'Pathfinders',           'infantry'),
    ("T'au Empire", 'Broadside Battlesuit',  'vehicle'),
    ("T'au Empire", 'Crisis Battlesuits',    'vehicle'),
    ("T'au Empire", 'Hammerhead Gunship',    'vehicle'),
    ("T'au Empire", 'Stealth Battlesuits',   'infantry'),

    # -- Tyranids ------------------------------------------------------------
    ('Tyranids', 'Hive Tyrant', 'character'),
    ('Tyranids', 'Carnifex',    'monster'),

    # -- Ultramarines --------------------------------------------------------
    ('Ultramarines', 'Marneus Calgar', 'epic_hero'),

    # -- World Eaters --------------------------------------------------------
    ('World Eaters', 'Eightbound', 'infantry'),
]


# ---------------------------------------------------------------------------
# Duplicate deactivations -- units that share the same product as the
# equivalent Space Marines parent unit.
# ---------------------------------------------------------------------------
SM_FACTION_DUPLICATES = [
    'Aggressor Squad',
    'Eradicator Squad',
    'Terminator Squad',   # 48-06 SM kit only — faction-unique terminator units are kept
    'Assault Intercessor Squad',
]

DUPLICATES_TO_DEACTIVATE = {
    'Black Templars': SM_FACTION_DUPLICATES,
    'Blood Angels':   SM_FACTION_DUPLICATES,
    'Dark Angels':    SM_FACTION_DUPLICATES,
    'Deathwatch':     SM_FACTION_DUPLICATES,
    'Space Wolves':   SM_FACTION_DUPLICATES,
    'Ultramarines':   SM_FACTION_DUPLICATES,
}

# Generic SM Terminator Squad SKU -- used to target only the SM-kit duplicate,
# not faction-specific terminator units (Deathwing 44-11, Deathwatch 39-xx).
SM_TERMINATOR_SKU = '48-06'

# SM Chaplain and Librarian SKUs used as stand-ins for GK until GK-specific
# products (57-09 Brotherhood Chaplain, 57-10 Brotherhood Librarian) are added.
GK_CHAPLAIN_SM_SKU = '48-32'
GK_LIBRARIAN_SM_SKU = '48-30'


class Command(BaseCommand):
    """Apply 10th Edition unit classification and deduplication fixes."""

    help = (
        'Fix UnitType categories, deactivate confirmed duplicate units, '
        'rename Craftworlds to Aeldari, set up Grey Knights standalone.'
    )

    def handle(self, *args, **options):
        """Apply all reclassifications, deactivations, and structural fixes."""
        self.stdout.write('Applying unit classification fixes...\n')
        reclass_updated = 0
        reclass_skipped = 0

        # ---- 1. Category reclassifications ----------------------------------
        self.stdout.write('\n-- Category reclassifications --')
        for faction_name, name_fragment, new_category in RECLASSIFICATIONS:
            # Support both old 'Craftworlds' and already-renamed 'Aeldari'
            if faction_name == 'Craftworlds':
                faction = (
                    Faction.objects.filter(name='Craftworlds').first()
                    or Faction.objects.filter(name='Aeldari').first()
                )
            else:
                faction = Faction.objects.filter(name=faction_name).first()

            if not faction:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] Faction "{faction_name}" not found'
                ))
                reclass_skipped += 1
                continue

            qs = UnitType.objects.filter(faction=faction, name__icontains=name_fragment)
            changed = qs.exclude(category=new_category).update(category=new_category)
            already_ok = qs.filter(category=new_category).count()

            if changed:
                self.stdout.write(
                    f'  [set]  {faction_name} / {name_fragment} -> {new_category}'
                    f' ({changed} row(s))'
                )
                reclass_updated += changed
            else:
                self.stdout.write(
                    f'  [ok]   {faction_name} / {name_fragment} -> {new_category}'
                    f' (already correct, {already_ok} row(s))'
                )
                reclass_skipped += 1

        # ---- 2. Duplicate deactivations -------------------------------------
        self.stdout.write('\n-- Duplicate deactivations --')
        deact_updated = 0
        deact_skipped = 0

        for faction_name, unit_names in DUPLICATES_TO_DEACTIVATE.items():
            faction = Faction.objects.filter(name=faction_name).first()
            if not faction:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] {faction_name} faction not found'
                ))
                continue

            for unit_name in unit_names:
                # Terminator Squad: match only the generic SM kit (48-06) to
                # avoid deactivating faction-unique terminator units.
                if unit_name == 'Terminator Squad':
                    sm_product = Product.objects.filter(gw_sku=SM_TERMINATOR_SKU).first()
                    if not sm_product:
                        self.stdout.write(self.style.WARNING(
                            f'  [skip] {faction_name} Terminator Squad -- '
                            f'SKU {SM_TERMINATOR_SKU} not found'
                        ))
                        deact_skipped += 1
                        continue
                    qs = UnitType.objects.filter(
                        faction=faction,
                        name__icontains='Terminator Squad',
                        product=sm_product,
                    )
                else:
                    qs = UnitType.objects.filter(
                        faction=faction,
                        name__icontains=unit_name,
                    )

                changed = qs.filter(is_active=True).update(is_active=False)
                label = f'{faction_name} / {unit_name}'
                if changed:
                    self.stdout.write(f'  [deactivated] {label} ({changed} row(s))')
                    deact_updated += changed
                else:
                    self.stdout.write(f'  [ok]          {label} (already inactive or not found)')
                    deact_skipped += 1

        # ---- 3. Grey Knights: remove SM parent, add Chaplain + Librarian ---
        self.stdout.write('\n-- Grey Knights standalone setup --')
        gk_updated = 0
        gk_faction = Faction.objects.filter(name='Grey Knights').first()

        if not gk_faction:
            self.stdout.write(self.style.WARNING('  [skip] Grey Knights faction not found'))
        else:
            # Remove Space Marines parent so GK doesn't inherit all SM units
            if gk_faction.parent_faction_id:
                gk_faction.parent_faction = None
                gk_faction.save(update_fields=['parent_faction'])
                self.stdout.write('  [cleared] Grey Knights parent_faction (was Space Marines)')
                gk_updated += 1
            else:
                self.stdout.write('  [ok] Grey Knights parent_faction already clear')

            # Add GK-specific Chaplain using SM product as stand-in (48-32)
            # until GK product 57-09 Brotherhood Chaplain is added to catalog.
            chaplain_product = Product.objects.filter(gw_sku=GK_CHAPLAIN_SM_SKU).first()
            if chaplain_product:
                _, created = UnitType.objects.get_or_create(
                    faction=gk_faction,
                    product=chaplain_product,
                    defaults={
                        'name': 'Brotherhood Chaplain',
                        'category': 'character',
                        'points_cost': 65,
                        'is_active': True,
                    },
                )
                if created:
                    self.stdout.write('  [created] GK Brotherhood Chaplain (using SM product 48-32)')
                    gk_updated += 1
                else:
                    self.stdout.write('  [ok] GK Brotherhood Chaplain already exists')
            else:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] SM Chaplain product {GK_CHAPLAIN_SM_SKU} not found'
                ))

            # Add GK-specific Librarian using SM product as stand-in (48-30)
            # until GK product 57-10 Brotherhood Librarian is added to catalog.
            librarian_product = Product.objects.filter(gw_sku=GK_LIBRARIAN_SM_SKU).first()
            if librarian_product:
                _, created = UnitType.objects.get_or_create(
                    faction=gk_faction,
                    product=librarian_product,
                    defaults={
                        'name': 'Brotherhood Librarian',
                        'category': 'character',
                        'points_cost': 80,
                        'is_active': True,
                    },
                )
                if created:
                    self.stdout.write('  [created] GK Brotherhood Librarian (using SM product 48-30)')
                    gk_updated += 1
                else:
                    self.stdout.write('  [ok] GK Brotherhood Librarian already exists')
            else:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] SM Librarian product {GK_LIBRARIAN_SM_SKU} not found'
                ))

        # ---- 4. Craftworlds -> Aeldari rename -------------------------------
        self.stdout.write('\n-- Craftworlds -> Aeldari rename --')
        rename_updated = 0

        craftworlds = Faction.objects.filter(name='Craftworlds').first()
        if craftworlds:
            craftworlds.name = 'Aeldari'
            craftworlds.slug = 'aeldari'
            craftworlds.save(update_fields=['name', 'slug'])
            self.stdout.write('  [renamed] Faction: Craftworlds -> Aeldari')
            rename_updated += 1

            for product in Product.objects.filter(faction=craftworlds, name__startswith='Craftworlds'):
                new_name = product.name.replace('Craftworlds', 'Aeldari', 1)
                product.name = new_name
                product.save(update_fields=['name'])
                self.stdout.write(f'  [renamed] Product: {new_name}')
                rename_updated += 1

            for unit in UnitType.objects.filter(faction=craftworlds, name__startswith='Craftworlds'):
                new_name = unit.name.replace('Craftworlds', 'Aeldari', 1)
                unit.name = new_name
                unit.save(update_fields=['name'])
                self.stdout.write(f'  [renamed] UnitType: {new_name}')
                rename_updated += 1
        else:
            aeldari = Faction.objects.filter(name='Aeldari').first()
            if aeldari:
                self.stdout.write('  [ok] Faction already named Aeldari')
            else:
                self.stdout.write(self.style.WARNING('  [skip] Craftworlds faction not found'))

        # ---- Summary --------------------------------------------------------
        self.stdout.write(self.style.SUCCESS(
            f'\nDone!'
            f'  Reclassified: {reclass_updated}'
            f'  |  Already correct: {reclass_skipped}'
            f'  |  Deactivated: {deact_updated}'
            f'  |  GK setup: {gk_updated}'
            f'  |  Renamed: {rename_updated}'
        ))
