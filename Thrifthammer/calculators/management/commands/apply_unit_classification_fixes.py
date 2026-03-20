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

  Space Marines + all sub-factions sharing the same product_id
    - Company Heroes / Space Marine Company Heroes: character -> infantry
    - Inceptor Squad / Space Marine Inceptors: mounted -> infantry
    - Hammerfall Bunker / Space Marine Hammerfall Bunker: transport -> fortification
    - Firestrike Servo-Turrets (both factions): fortification -> vehicle
    - Tactical Squad (BT): infantry -> battleline

  Black Templars only
    - Emperor's Champion: infantry -> epic_hero
    - High Marshal Helbrecht: infantry -> epic_hero

Deactivations (confirmed duplicates — same product as parent SM unit):
    - Aggressor Squad (BT)          -> deactivate (keep Space Marine Aggressors)
    - Eradicator Squad (BT)         -> deactivate (keep Space Marine Eradicators)
    - Terminator Squad (BT)         -> deactivate (keep Space Marine Terminator Squad)
    - Assault Intercessor Squad (BT)-> deactivate (keep Space Marine Assault Intercessors)
  NOTE: Hammerfall Bunker, Firestrike Servo-Turrets, Company Heroes,
        Inceptor Squad, Tactical Squad are KEPT for both factions because
        the deduplication logic in calculators/views.py prefers the sub-faction
        unit when a parent_faction is set — so only one will be shown.

Usage:
    python manage.py apply_unit_classification_fixes

This command is fully idempotent — safe to re-run at any time.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction


# ---------------------------------------------------------------------------
# Category reclassifications — each entry:
#   (faction_name_or_None, unit_name_icontains, new_category)
# faction_name_or_None=None means "any faction"
# ---------------------------------------------------------------------------
RECLASSIFICATIONS = [
    # ── Adeptus Mechanicus ──────────────────────────────────────────────────
    ('Adeptus Mechanicus', 'Ironstrider Ballistarii', 'vehicle'),
    ('Adeptus Mechanicus', 'Kataphron Destroyers',    'infantry'),

    # ── Astra Militarum ─────────────────────────────────────────────────────
    ('Astra Militarum', 'Commissar', 'character'),
    ('Astra Militarum', 'Sentinel',  'vehicle'),

    # ── Space Marines (base faction) ────────────────────────────────────────
    ('Space Marines', 'Company Heroes',           'infantry'),
    ('Space Marines', 'Inceptors',                'infantry'),
    ('Space Marines', 'Hammerfall Bunker',         'fortification'),
    ('Space Marines', 'Firestrike Servo-Turrets',  'vehicle'),

    # ── Black Templars ──────────────────────────────────────────────────────
    ('Black Templars', "Emperor's Champion",      'epic_hero'),
    ('Black Templars', 'High Marshal Helbrecht',  'epic_hero'),
    ('Black Templars', 'Company Heroes',          'infantry'),
    ('Black Templars', 'Inceptor Squad',          'infantry'),
    ('Black Templars', 'Hammerfall Bunker',        'fortification'),
    ('Black Templars', 'Firestrike Servo-Turrets', 'vehicle'),
    ('Black Templars', 'Tactical Squad',           'battleline'),
]


# ---------------------------------------------------------------------------
# Duplicate deactivations — BT units that share the same product as the
# equivalent Space Marines unit. When a BT player selects the BT faction,
# the SM parent unit already appears via parent_faction union query, making
# the BT copy redundant. Deactivating removes it cleanly.
# ---------------------------------------------------------------------------
BT_DUPLICATES_TO_DEACTIVATE = [
    'Aggressor Squad',
    'Eradicator Squad',
    'Terminator Squad',
    'Assault Intercessor Squad',
]


class Command(BaseCommand):
    """Apply 10th Edition unit classification and deduplication fixes."""

    help = 'Fix UnitType categories and deactivate confirmed BT duplicate units.'

    def handle(self, *args, **options):
        """Apply all reclassifications and deactivations."""
        self.stdout.write('Applying unit classification fixes...\n')
        reclass_updated = 0
        reclass_skipped = 0

        # ── 1. Category reclassifications ───────────────────────────────────
        self.stdout.write('\n-- Category reclassifications --')
        for faction_name, name_fragment, new_category in RECLASSIFICATIONS:
            qs = UnitType.objects.filter(name__icontains=name_fragment)
            if faction_name:
                faction = Faction.objects.filter(name=faction_name).first()
                if not faction:
                    self.stdout.write(self.style.WARNING(
                        f'  [skip] Faction "{faction_name}" not found'
                    ))
                    reclass_skipped += 1
                    continue
                qs = qs.filter(faction=faction)

            # Only update rows that actually need changing
            changed = qs.exclude(category=new_category).update(category=new_category)
            already_ok = qs.filter(category=new_category).count()

            if changed:
                self.stdout.write(
                    f'  [set]  {faction_name or "all"} / {name_fragment} -> {new_category}'
                    f' ({changed} row(s))'
                )
                reclass_updated += changed
            else:
                self.stdout.write(
                    f'  [ok]   {faction_name or "all"} / {name_fragment} -> {new_category}'
                    f' (already correct, {already_ok} row(s))'
                )
                reclass_skipped += 1

        # ── 2. BT duplicate deactivations ───────────────────────────────────
        self.stdout.write('\n-- Black Templars duplicate deactivations --')
        bt_faction = Faction.objects.filter(name='Black Templars').first()
        deact_updated = 0
        deact_skipped = 0

        if not bt_faction:
            self.stdout.write(self.style.WARNING(
                '  [skip] Black Templars faction not found - skipping deactivations'
            ))
        else:
            for unit_name in BT_DUPLICATES_TO_DEACTIVATE:
                qs = UnitType.objects.filter(
                    faction=bt_faction,
                    name__icontains=unit_name,
                )
                changed = qs.filter(is_active=True).update(is_active=False)
                if changed:
                    self.stdout.write(
                        f'  [deactivated] {unit_name} ({changed} row(s))'
                    )
                    deact_updated += changed
                else:
                    self.stdout.write(
                        f'  [ok]          {unit_name} (already inactive or not found)'
                    )
                    deact_skipped += 1

        # ── Summary ─────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f'\nDone!'
            f'  Reclassified: {reclass_updated} unit(s)'
            f'  |  Already correct: {reclass_skipped}'
            f'  |  Deactivated duplicates: {deact_updated}'
        ))
