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
    - Emperor's Champion: infantry -> character  (standard named character, not epic)
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
    - Asmodai: infantry -> character
    - Belial: infantry -> character
    - Ezekiel: infantry -> character
    - Lazarus: infantry -> character
    - Sammael: infantry -> character
    - Ravenwing Command Squad: infantry -> character
    - Nephilim Jetfighter: infantry -> vehicle
    - Ravenwing Dark Talon: infantry -> vehicle
    - Ravenwing Darkshroud: infantry -> vehicle
    - Deathwing Knights: vehicle -> infantry
    - Ravenwing Black Knights: vehicle -> mounted

  Craftworlds (Aeldari)
    - Dire Avengers: battleline -> infantry
    - Guardians: infantry -> battleline

  Craftworlds -> Aeldari rename
    - Faction name + slug: Craftworlds -> Aeldari
    - All product names: "Craftworlds X" -> "Aeldari X"
    - All unit names: "Craftworlds X" -> "Aeldari X"

Deactivations (confirmed duplicates -- same product as parent SM unit):
  Black Templars
    - Aggressor Squad         (keep Space Marine Aggressors via parent faction)
    - Eradicator Squad        (keep Space Marine Eradicators via parent faction)
    - Terminator Squad        (keep Space Marine Terminator Squad via parent faction)
    - Assault Intercessor Squad
  Blood Angels
    - Aggressor Squad
    - Eradicator Squad
    - Terminator Squad
    - Assault Intercessor Squad
  Dark Angels
    - Aggressor Squad
    - Eradicator Squad
    - Terminator Squad        (48-06, NOT Deathwing Terminator Squad 44-11 -- that's unique)
    - Assault Intercessor Squad

NOTE: Units kept for both factions (Hammerfall Bunker, Firestrike Servo-Turrets,
      Company Heroes, Inceptor Squad, Tactical Squad) are handled by the
      deduplication logic in calculators/views.py which prefers the sub-faction
      unit over the parent SM unit when a parent_faction is set.

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
    ('Dark Angels', "Dark Angels Lion El'Jonson",          'epic_hero'),
    ('Dark Angels', 'Dark Angels Asmodai',                 'character'),
    ('Dark Angels', 'Dark Angels Belial',                  'character'),
    ('Dark Angels', 'Dark Angels Ezekiel',                 'character'),
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

    # -- Craftworlds (Aeldari) -----------------------------------------------
    ('Craftworlds', 'Dire Avengers', 'infantry'),
    ('Craftworlds', 'Guardians',     'battleline'),
]


# ---------------------------------------------------------------------------
# Duplicate deactivations -- units that share the same product as the
# equivalent Space Marines parent unit. The sub-faction copy is redundant
# because the SM unit already appears via the parent_faction union query.
# ---------------------------------------------------------------------------
DUPLICATES_TO_DEACTIVATE = {
    'Black Templars': [
        'Aggressor Squad',
        'Eradicator Squad',
        'Terminator Squad',
        'Assault Intercessor Squad',
    ],
    'Blood Angels': [
        'Aggressor Squad',
        'Eradicator Squad',
        'Terminator Squad',
        'Assault Intercessor Squad',
    ],
    'Dark Angels': [
        'Aggressor Squad',
        'Eradicator Squad',
        'Terminator Squad',        # 48-06 SM kit only -- Deathwing Terminator Squad (44-11) is kept
        'Assault Intercessor Squad',
    ],
}

# DA Terminator Squad must match the generic SM kit (48-06), not Deathwing (44-11).
DA_TERMINATOR_SM_SKU = '48-06'


class Command(BaseCommand):
    """Apply 10th Edition unit classification and deduplication fixes."""

    help = 'Fix UnitType categories, deactivate confirmed duplicate units, rename Craftworlds to Aeldari.'

    def handle(self, *args, **options):
        """Apply all reclassifications, deactivations, and the Craftworlds rename."""
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
                # DA Terminator Squad: match only the generic SM kit (48-06),
                # not the unique Deathwing Terminator Squad (44-11).
                if faction_name == 'Dark Angels' and unit_name == 'Terminator Squad':
                    sm_product = Product.objects.filter(gw_sku=DA_TERMINATOR_SM_SKU).first()
                    if not sm_product:
                        self.stdout.write(self.style.WARNING(
                            f'  [skip] DA Terminator Squad -- SKU {DA_TERMINATOR_SM_SKU} not found'
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

        # ---- 3. Craftworlds -> Aeldari rename -------------------------------
        self.stdout.write('\n-- Craftworlds -> Aeldari rename --')
        rename_updated = 0

        craftworlds = Faction.objects.filter(name='Craftworlds').first()
        if craftworlds:
            craftworlds.name = 'Aeldari'
            craftworlds.slug = 'aeldari'
            craftworlds.save(update_fields=['name', 'slug'])
            self.stdout.write('  [renamed] Faction: Craftworlds -> Aeldari')
            rename_updated += 1

            # Rename products: "Craftworlds X" -> "Aeldari X"
            for product in Product.objects.filter(faction=craftworlds, name__startswith='Craftworlds'):
                new_name = product.name.replace('Craftworlds', 'Aeldari', 1)
                product.name = new_name
                product.save(update_fields=['name'])
                self.stdout.write(f'  [renamed] Product: {new_name}')
                rename_updated += 1

            # Rename units: "Craftworlds X" -> "Aeldari X"
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
            f'  |  Renamed: {rename_updated}'
        ))
