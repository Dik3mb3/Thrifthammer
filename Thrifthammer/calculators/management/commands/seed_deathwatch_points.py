"""
Management command: seed_deathwatch_points

Sets the points_cost on UnitType records for all Deathwatch units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_deathwatch_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Deathwatch UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Deathwatch 10th Edition list.
- Key difference vs Space Marines: Chaplain 60pts (SM=75pts).
- DW-exclusive units: Watch Captain Artemis, Watch Master, Deathwatch Veterans,
  Deathwatch Kill Team, Deathwatch Terminator Squad, Corvus Blackstar,
  Decimus Kill Team, Fortis Kill Team, Indomitor Kill Team,
  Spectrus Kill Team, Talonstrike Kill Team.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Deathwatch 10th Edition list.
# Every line with pts in the list has been checked individually.
# ---------------------------------------------------------------------------
DEATHWATCH_POINTS = [
    # ── DW-exclusive named characters ────────────────────────────────────────
    ('39-01',  65, 'Watch Captain Artemis'),       # 65pts ✓
    ('39-02',  95, 'Watch Master'),                # 95pts ✓
    # ── DW-exclusive units ────────────────────────────────────────────────────
    ('39-06', 100, 'Deathwatch Veterans'),         # 100pts ✓
    ('39-10', 100, 'Deathwatch Kill Team'),        # 100pts ✓
    ('39-03', 100, 'Decimus Kill Team'),           # 100pts ✓
    ('39-04', 180, 'Corvus Blackstar'),            # 180pts ✓
    ('39-05', 190, 'Deathwatch Terminator Squad'), # 190pts ✓
    ('39-07', 180, 'Fortis Kill Team'),            # 180pts ✓
    ('39-08', 265, 'Indomitor Kill Team'),         # 265pts ✓
    ('39-09', 180, 'Spectrus Kill Team'),          # 180pts ✓
    ('39-11', 275, 'Talonstrike Kill Team'),       # 275pts ✓
    # ── Shared SM characters — DW-specific costs ──────────────────────────────
    ('48-34',  50, 'Ancient'),                     # 50pts ✓ same as SM
    ('48-33',  50, 'Apothecary'),                  # 50pts ✓ same as SM
    ('48-32',  60, 'Chaplain'),                    # 60pts ✓ DW | SM=75pts
    ('48-36',  70, 'Judiciar'),                    # 70pts ✓ same as SM
    ('48-30',  65, 'Librarian'),                   # 65pts ✓ same as SM
    ('48-61',  55, 'Lieutenant'),                  # 55pts ✓ same as SM
    ('48-62',  80, 'Captain'),                     # 80pts ✓ same as SM
    ('48-37', 105, 'Company Heroes'),              # 105pts ✓ same as SM
    # ── Battleline ────────────────────────────────────────────────────────────
    ('48-75',  80, 'Intercessor Squad'),           # 80pts ✓ same as SM
    ('48-76',  75, 'Assault Intercessor Squad'),   # 75pts ✓ same as SM
    ('48-29',  70, 'Scout Squad'),                 # 70pts ✓ same as SM
    ('48-45',  90, 'Infernus Squad'),              # 90pts ✓ same as SM
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('48-06', 170, 'Terminator Squad'),            # 170pts ✓ same as SM
    ('48-92',  95, 'Aggressor Squad'),             # 95pts ✓ same as SM
    ('48-38',  80, 'Bladeguard Veteran Squad'),    # 80pts ✓ same as SM
    ('48-15', 120, 'Devastator Squad'),            # 120pts ✓ same as SM
    ('48-98',  85, 'Eliminator Squad'),            # 85pts ✓ same as SM
    ('48-39',  90, 'Eradicator Squad'),            # 90pts ✓ same as SM
    ('48-96',  80, 'Incursor Squad'),              # 80pts ✓ same as SM
    ('48-41', 100, 'Infiltrator Squad'),           # 100pts ✓ same as SM
    ('48-43', 100, 'Sternguard Veteran Squad'),    # 100pts ✓ same as SM
    ('48-08', 100, 'Vanguard Veteran Squad'),      # 100pts ✓ same as SM
    # ── Mounted / Fast Attack ──────────────────────────────────────────────────
    ('48-40',  80, 'Outrider Squad'),              # 80pts ✓ same as SM
    ('48-42',  60, 'Invader ATV'),                 # 60pts ✓ same as SM
    ('48-97', 120, 'Inceptor Squad'),              # 120pts ✓ same as SM
    ('48-99',  75, 'Suppressor Squad'),            # 75pts ✓ same as SM
    # ── Vehicles / Dreadnoughts ────────────────────────────────────────────────
    ('48-46', 150, 'Ballistus Dreadnought'),       # 150pts ✓ same as SM
    ('48-44', 160, 'Brutalis Dreadnought'),        # 160pts ✓ same as SM
    ('48-93', 195, 'Redemptor Dreadnought'),       # 195pts ✓ same as SM
    ('48-23', 140, 'Predator Destructor'),         # 140pts ✓ same as SM
    ('48-25', 190, 'Whirlwind'),                   # 190pts ✓ same as SM
    ('48-26', 185, 'Vindicator'),                  # 185pts ✓ same as SM
    ('48-95', 220, 'Repulsor Executioner'),        # 220pts ✓ same as SM
    # ── Transports ────────────────────────────────────────────────────────────
    ('48-94',  80, 'Impulsor'),                    # 80pts ✓ same as SM
    ('48-85', 180, 'Repulsor'),                    # 180pts ✓ same as SM
    ('48-21', 220, 'Land Raider'),                 # 220pts ✓ same as SM
    ('48-22', 220, 'Land Raider Crusader'),        # 220pts ✓ same as SM
    # ── Fortifications ────────────────────────────────────────────────────────
    ('48-27', 175, 'Hammerfall Bunker'),           # 175pts ✓ same as SM
    ('48-28',  75, 'Firestrike Servo-Turrets'),    # 75pts ✓ same as SM
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Deathwatch units.

    Looks up each product by GW SKU, then filters for the Deathwatch
    UnitType specifically and updates only that row's points_cost. This
    ensures Space Marines UnitType rows for the same product are untouched.
    Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Deathwatch units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Deathwatch points…\n')

        dw_faction = Faction.objects.filter(name='Deathwatch').first()
        if not dw_faction:
            self.stdout.write(self.style.ERROR(
                'Deathwatch faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in DEATHWATCH_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=dw_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — DW UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
