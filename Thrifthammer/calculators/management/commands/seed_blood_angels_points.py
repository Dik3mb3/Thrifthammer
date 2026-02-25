"""
Management command: seed_blood_angels_points

Sets the points_cost on UnitType records for all Blood Angels units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_blood_angels_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Blood Angels UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Some values differ from Space Marines (e.g. Chaplain 60pts vs 75pts SM).
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Blood Angels 10th Edition list.
# Includes BA-exclusive units (41-xx) and shared SM kits (48-xx).
# ---------------------------------------------------------------------------
BLOOD_ANGELS_POINTS = [
    # ── BA-exclusive characters & units ──────────────────────────────────────
    ('41-03',  95, 'Astorath'),
    ('41-02', 120, 'Chief Librarian Mephiston'),
    ('41-04', 120, 'Commander Dante'),
    ('41-05', 100, 'Lemartes'),
    ('41-08', 130, 'The Sanguinor'),
    ('41-09',  75, 'Sanguinary Priest'),
    ('41-07',  85, 'Death Company Marines'),
    ('41-12', 120, 'Death Company Marines with Jump Packs'),
    ('41-06', 125, 'Sanguinary Guard'),
    ('41-10', 125, 'Baal Predator'),
    ('41-11', 160, 'Death Company Dreadnought'),
    ('41-15', 160, 'Librarian Dreadnought'),
    # ── Shared SM characters — BA-specific costs ──────────────────────────────
    ('48-34',  50, 'Ancient'),
    ('48-33',  50, 'Apothecary'),
    ('48-32',  60, 'Chaplain'),          # 60pts BA | 75pts Space Marines
    ('48-36',  70, 'Judiciar'),
    ('48-30',  65, 'Librarian'),
    ('48-61',  55, 'Lieutenant'),
    ('48-62',  80, 'Captain'),
    ('48-37', 105, 'Company Heroes'),
    # ── Battleline ────────────────────────────────────────────────────────────
    ('48-75',  80, 'Intercessor Squad'),
    ('48-76',  75, 'Assault Intercessor Squad'),
    ('48-29',  70, 'Scout Squad'),
    ('48-45',  90, 'Infernus Squad'),
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('48-06', 170, 'Terminator Squad'),
    ('48-92',  95, 'Aggressor Squad'),
    ('48-38',  80, 'Bladeguard Veteran Squad'),
    ('48-15', 120, 'Devastator Squad'),
    ('48-98',  85, 'Eliminator Squad'),
    ('48-39',  90, 'Eradicator Squad'),
    ('48-96',  80, 'Incursor Squad'),
    ('48-41', 100, 'Infiltrator Squad'),
    ('48-43', 100, 'Sternguard Veteran Squad'),
    ('48-08', 100, 'Vanguard Veteran Squad'),
    # ── Mounted / Fast Attack ──────────────────────────────────────────────────
    ('48-40',  80, 'Outrider Squad'),
    ('48-42',  60, 'Invader ATV'),
    ('48-97', 120, 'Inceptor Squad'),
    ('48-99',  75, 'Suppressor Squad'),
    # ── Vehicles / Dreadnoughts ────────────────────────────────────────────────
    ('48-46', 150, 'Ballistus Dreadnought'),
    ('48-44', 160, 'Brutalis Dreadnought'),
    ('48-93', 195, 'Redemptor Dreadnought'),
    ('48-23', 140, 'Predator Destructor'),
    ('48-25', 190, 'Whirlwind'),
    ('48-26', 185, 'Vindicator'),
    ('48-95', 220, 'Repulsor Executioner'),
    # ── Transports ────────────────────────────────────────────────────────────
    ('48-94',  80, 'Impulsor'),
    ('48-85', 180, 'Repulsor'),
    ('48-21', 220, 'Land Raider'),
    ('48-22', 220, 'Land Raider Crusader'),
    # ── Fortifications ────────────────────────────────────────────────────────
    ('48-27', 175, 'Hammerfall Bunker'),
    ('48-28',  75, 'Firestrike Servo-Turrets'),
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Blood Angels units.

    Looks up each product by GW SKU, then filters for the Blood Angels
    UnitType specifically and updates only that row's points_cost. This
    ensures Space Marines UnitType rows for the same product are untouched.
    Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Blood Angels units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Blood Angels points…\n')

        ba_faction = Faction.objects.filter(name='Blood Angels').first()
        if not ba_faction:
            self.stdout.write(self.style.ERROR(
                'Blood Angels faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in BLOOD_ANGELS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=ba_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — BA UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
