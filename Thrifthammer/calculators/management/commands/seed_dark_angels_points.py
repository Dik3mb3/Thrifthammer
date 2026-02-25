"""
Management command: seed_dark_angels_points

Sets the points_cost on UnitType records for all Dark Angels units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_dark_angels_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Dark Angels UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Dark Angels 10th Edition list.
- Key difference vs Space Marines: Chaplain 60pts (SM=75pts).
- DA-exclusive units: Lion El'Jonson, Azrael, Belial, Asmodai, Lazarus,
  Sammael, Ezekiel, Deathwing Knights, Deathwing Terminators, Ravenwing
  Black Knights, Ravenwing Command Squad, Inner Circle Companions,
  Ravenwing Dark Talon, Ravenwing Darkshroud, Land Speeder Vengeance,
  Nephilim Jetfighter.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Dark Angels 10th Edition list.
# Every line with pts in the list has been checked individually.
# ---------------------------------------------------------------------------
DARK_ANGELS_POINTS = [
    # ── DA-exclusive named characters ────────────────────────────────────────
    ('44-02',  75, 'Ezekiel'),                     # 75pts ✓
    ('44-03',  70, 'Asmodai'),                     # 70pts ✓
    ('44-04', 125, 'Azrael'),                      # 125pts ✓
    ('44-05',  85, 'Belial'),                      # 85pts ✓
    ('44-06', 315, 'Lion El\'Jonson'),             # 315pts ✓
    ('44-07',  70, 'Lazarus'),                     # 70pts ✓
    ('44-08', 115, 'Sammael'),                     # 115pts ✓
    # ── DA-exclusive units ───────────────────────────────────────────────────
    ('44-09', 120, 'Ravenwing Command Squad'),     # 120pts ✓
    ('44-10', 250, 'Deathwing Knights'),           # 250pts ✓
    ('44-11', 180, 'Deathwing Terminator Squad'),  # 180pts ✓
    ('44-12',  80, 'Ravenwing Black Knights'),     # 80pts ✓
    ('44-13',  90, 'Inner Circle Companions'),     # 90pts ✓
    ('44-14', 210, 'Ravenwing Dark Talon'),        # 210pts ✓
    ('44-15', 100, 'Ravenwing Darkshroud'),        # 100pts ✓
    ('44-16', 120, 'Land Speeder Vengeance'),      # 120pts ✓
    ('44-17', 195, 'Nephilim Jetfighter'),         # 195pts ✓
    # ── Shared SM characters — DA-specific costs ──────────────────────────────
    ('48-34',  50, 'Ancient'),                     # 50pts ✓ same as SM
    ('48-33',  50, 'Apothecary'),                  # 50pts ✓ same as SM
    ('48-32',  60, 'Chaplain'),                    # 60pts ✓ DA | SM=75pts
    ('48-36',  70, 'Judiciar'),                    # 70pts ✓ same as SM
    ('48-30',  65, 'Librarian'),                   # 65pts ✓ same as SM
    ('48-61',  55, 'Lieutenant'),                  # 55pts ✓ same as SM
    ('48-62',  80, 'Captain'),                     # 80pts ✓ same as SM
    ('48-37', 105, 'Company Heroes'),              # 105pts ✓ same as SM
    # ── Battleline ────────────────────────────────────────────────────────────
    ('48-75',  80, 'Intercessor Squad'),           # 80pts ✓
    ('48-76',  75, 'Assault Intercessor Squad'),   # 75pts ✓
    ('48-29',  70, 'Scout Squad'),                 # 70pts ✓
    ('48-45',  90, 'Infernus Squad'),              # 90pts ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('48-06', 170, 'Terminator Squad'),            # 170pts ✓ same as SM
    ('48-92',  95, 'Aggressor Squad'),             # 95pts ✓
    ('48-38',  80, 'Bladeguard Veteran Squad'),    # 80pts ✓
    ('48-15', 120, 'Devastator Squad'),            # 120pts ✓
    ('48-98',  85, 'Eliminator Squad'),            # 85pts ✓
    ('48-39',  90, 'Eradicator Squad'),            # 90pts ✓
    ('48-96',  80, 'Incursor Squad'),              # 80pts ✓
    ('48-41', 100, 'Infiltrator Squad'),           # 100pts ✓
    ('48-43', 100, 'Sternguard Veteran Squad'),    # 100pts ✓ same as SM
    ('48-08', 100, 'Vanguard Veteran Squad'),      # 100pts ✓
    # ── Mounted / Fast Attack ──────────────────────────────────────────────────
    ('48-40',  80, 'Outrider Squad'),              # 80pts ✓
    ('48-42',  60, 'Invader ATV'),                 # 60pts ✓
    ('48-97', 120, 'Inceptor Squad'),              # 120pts ✓
    ('48-99',  75, 'Suppressor Squad'),            # 75pts ✓
    # ── Vehicles / Dreadnoughts ────────────────────────────────────────────────
    ('48-46', 150, 'Ballistus Dreadnought'),       # 150pts ✓
    ('48-44', 160, 'Brutalis Dreadnought'),        # 160pts ✓
    ('48-93', 195, 'Redemptor Dreadnought'),       # 195pts ✓
    ('48-23', 140, 'Predator Destructor'),         # 140pts ✓
    ('48-25', 190, 'Whirlwind'),                   # 190pts ✓
    ('48-26', 185, 'Vindicator'),                  # 185pts ✓
    ('48-95', 220, 'Repulsor Executioner'),        # 220pts ✓ same as SM
    # ── Transports ────────────────────────────────────────────────────────────
    ('48-94',  80, 'Impulsor'),                    # 80pts ✓ same as SM
    ('48-85', 180, 'Repulsor'),                    # 180pts ✓
    ('48-21', 220, 'Land Raider'),                 # 220pts ✓
    ('48-22', 220, 'Land Raider Crusader'),        # 220pts ✓
    # ── Fortifications ────────────────────────────────────────────────────────
    ('48-27', 175, 'Hammerfall Bunker'),           # 175pts ✓
    ('48-28',  75, 'Firestrike Servo-Turrets'),    # 75pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Dark Angels units.

    Looks up each product by GW SKU, then filters for the Dark Angels
    UnitType specifically. Points verified line-by-line from New Recruit.
    Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Dark Angels units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Dark Angels points…\n')

        da_faction = Faction.objects.filter(name='Dark Angels').first()
        if not da_faction:
            self.stdout.write(self.style.ERROR(
                'Dark Angels faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in DARK_ANGELS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=da_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — DA UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
