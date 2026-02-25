"""
Management command: seed_ultramarines_points

Sets the points_cost on UnitType records for all Space Marines / Ultramarines
products, using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_ultramarines_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku) and updates the linked UnitType's points_cost.
Products not found in the database are skipped with a warning.

Notes:
- This command should be run manually after the initial deploy (or after running
  populate_products / populate_units for the first time).
- Do NOT add to the Procfile unless all army points seeds are complete, because
  populate_units resets points_cost to 0 on a fresh seed (without --skip-if-current).
- Points values are for standard unit sizes as listed in New Recruit.
- SKUs not yet in the DB are skipped gracefully — add products later, re-run.
- 48-07 collision: Tactical Squad (140pts) and Terminator Assault Squad (180pts)
  share the same GW SKU. Handled via SM_SKU_COLLISIONS below with name filtering.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Space Marines / Ultramarines 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# SKUs not yet in the DB are included here so they are seeded automatically
# when the corresponding products are added later.
# Note: 48-07 is EXCLUDED from this list — handled via SM_SKU_COLLISIONS below.
# ---------------------------------------------------------------------------
SPACE_MARINES_POINTS = [
    # ── Characters ──────────────────────────────────────────────────────────
    ('48-34',  50, 'Ancient'),                            # 50pts ✓
    ('48-09',  75, 'Ancient in Terminator Armour'),       # 75pts ✓
    ('48-10',  45, 'Bladeguard Ancient'),                 # 45pts ✓
    ('48-33',  50, 'Apothecary'),                         # 50pts ✓
    ('48-11',  70, 'Apothecary Biologis'),                # 70pts ✓
    ('48-62',  80, 'Captain'),                            # 80pts ✓
    ('48-12',  80, 'Captain in Gravis Armour'),           # 80pts ✓
    ('48-13',  70, 'Captain in Phobos Armour'),           # 70pts ✓
    ('48-14',  95, 'Captain in Terminator Armour'),       # 95pts ✓
    ('48-16',  75, 'Captain with Jump Pack'),             # 75pts ✓
    ('48-32',  60, 'Chaplain'),                           # 60pts ✓ (NOT 75 — that is Chap in TDA)
    ('48-17',  75, 'Chaplain in Terminator Armour'),      # 75pts ✓
    ('48-18',  75, 'Chaplain on Bike'),                   # 75pts ✓
    ('48-19',  75, 'Chaplain with Jump Pack'),            # 75pts ✓
    ('48-36',  70, 'Judiciar'),                           # 70pts ✓
    ('48-30',  65, 'Librarian'),                          # 65pts ✓
    ('48-20',  70, 'Librarian in Phobos Armour'),         # 70pts ✓
    ('48-24',  75, 'Librarian in Terminator Armour'),     # 75pts ✓
    ('48-61',  55, 'Lieutenant'),                         # 55pts ✓
    ('48-31',  55, 'Lieutenant in Phobos Armour'),        # 55pts ✓
    ('48-35',  55, 'Lieutenant in Reiver Armour'),        # 55pts ✓
    ('48-47',  70, 'Lieutenant with Combi-weapon'),       # 70pts ✓
    ('48-48',  55, 'Techmarine'),                         # 55pts ✓
    ('48-37', 105, 'Company Heroes'),                     # 105pts ✓
    # ── Ultramarines named characters ───────────────────────────────────────
    ('55-12', 140, 'Marneus Calgar'),                     # 140pts ✓
    ('55-02', 340, 'Roboute Guilliman'),                  # 340pts ✓
    ('55-16', 110, 'Victrix Honour Guard'),               # 110pts ✓
    # ── Battleline ───────────────────────────────────────────────────────────
    ('48-76',  75, 'Assault Intercessor Squad'),          # 75pts ✓
    ('48-49', 100, 'Heavy Intercessor Squad'),            # 100pts ✓
    ('48-75',  80, 'Intercessor Squad'),                  # 80pts ✓
    ('48-29',  70, 'Scout Squad'),                        # 70pts ✓
    ('48-45',  90, 'Infernus Squad'),                     # 90pts ✓
    # ── Infantry ─────────────────────────────────────────────────────────────
    ('48-06', 170, 'Terminator Squad'),                   # 170pts ✓
    ('48-92',  95, 'Aggressor Squad'),                    # 95pts ✓
    ('48-50',  90, 'Assault Intercessors with Jump Packs'), # 90pts ✓
    ('48-51', 115, 'Assault Squad with Jump Packs'),      # 115pts ✓ (Legends)
    ('48-38',  80, 'Bladeguard Veteran Squad'),           # 80pts ✓
    ('48-55', 150, 'Centurion Assault Squad'),            # 150pts ✓
    ('48-56', 175, 'Centurion Devastator Squad'),         # 175pts ✓
    ('48-54', 200, 'Desolation Squad'),                   # 200pts ✓
    ('48-15', 120, 'Devastator Squad'),                   # 120pts ✓
    ('48-98',  85, 'Eliminator Squad'),                   # 85pts ✓
    ('48-39',  90, 'Eradicator Squad'),                   # 90pts ✓
    ('48-52', 110, 'Hellblaster Squad'),                  # 110pts ✓
    ('48-96',  80, 'Incursor Squad'),                     # 80pts ✓
    ('48-41', 100, 'Infiltrator Squad'),                  # 100pts ✓
    ('48-53',  80, 'Reiver Squad'),                       # 80pts ✓
    ('48-43', 100, 'Sternguard Veteran Squad'),           # 100pts ✓
    ('48-08', 100, 'Vanguard Veteran Squad'),             # 100pts ✓
    # ── Fast Attack / Mounted ────────────────────────────────────────────────
    ('48-97', 120, 'Inceptor Squad'),                     # 120pts ✓
    ('48-40',  80, 'Outrider Squad'),                     # 80pts ✓
    ('48-42',  60, 'Invader ATV'),                        # 60pts ✓
    ('48-99',  75, 'Suppressor Squad'),                   # 75pts ✓
    # ── Walkers / Dreadnoughts ───────────────────────────────────────────────
    ('48-46', 150, 'Ballistus Dreadnought'),              # 150pts ✓
    ('48-44', 160, 'Brutalis Dreadnought'),               # 160pts ✓
    ('48-60', 135, 'Dreadnought'),                        # 135pts ✓
    ('48-93', 195, 'Redemptor Dreadnought'),              # 195pts ✓
    ('48-57', 125, 'Invictor Tactical Warsuit'),          # 125pts ✓
    # ── Transports ───────────────────────────────────────────────────────────
    ('48-63',  70, 'Drop Pod'),                           # 70pts ✓
    ('48-94',  80, 'Impulsor'),                           # 80pts ✓
    ('48-58',  95, 'Razorback'),                          # 95pts ✓
    ('48-85', 180, 'Repulsor'),                           # 180pts ✓
    ('48-95', 220, 'Repulsor Executioner'),               # 220pts ✓
    ('48-59',  75, 'Rhino'),                              # 75pts ✓
    # ── Heavy Vehicles ────────────────────────────────────────────────────────
    ('48-65', 160, 'Gladiator Lancer'),                   # 160pts ✓
    ('48-66', 160, 'Gladiator Reaper'),                   # 160pts ✓
    ('48-67', 150, 'Gladiator Valiant'),                  # 150pts ✓
    ('48-21', 220, 'Land Raider'),                        # 220pts ✓
    ('48-22', 220, 'Land Raider Crusader'),               # 220pts ✓
    ('48-68', 270, 'Land Raider Redeemer'),               # 270pts ✓
    ('48-64', 135, 'Predator Annihilator'),               # 135pts ✓
    ('48-23', 140, 'Predator Destructor'),                # 140pts ✓
    ('48-25', 190, 'Whirlwind'),                          # 190pts ✓
    ('48-26', 185, 'Vindicator'),                         # 185pts ✓
    # ── Aircraft ─────────────────────────────────────────────────────────────
    ('48-69', 115, 'Storm Speeder Hailstrike'),           # 115pts ✓
    ('48-70', 125, 'Storm Speeder Hammerstrike'),         # 125pts ✓
    ('48-71', 135, 'Storm Speeder Thunderstrike'),        # 135pts ✓
    ('48-73', 155, 'Stormhawk Interceptor'),              # 155pts ✓
    ('48-74', 280, 'Stormraven Gunship'),                 # 280pts ✓
    ('48-72', 165, 'Stormtalon Gunship'),                 # 165pts ✓
    ('48-77', 525, 'Astraeus'),                           # 525pts ✓
    ('48-78', 840, 'Thunderhawk Gunship'),                # 840pts ✓
    # ── Fortifications ────────────────────────────────────────────────────────
    ('48-27', 175, 'Hammerfall Bunker'),                  # 175pts ✓
    ('48-28',  75, 'Firestrike Servo-Turrets'),           # 75pts ✓
]

# ---------------------------------------------------------------------------
# SKU collision handling — 48-07 is shared by TWO different products:
#   • Space Marine Tactical Squad        → 140 pts
#   • Space Marine Terminator Assault Squad → 180 pts
# The main loop uses .first() which only finds one; these are handled below
# using name-filtered queries identical to the cross-faction collision pattern.
# (gw_sku, name_fragment, points_cost, display_name)
# ---------------------------------------------------------------------------
SM_SKU_COLLISIONS = [
    ('48-07', 'Tactical',   140, 'Tactical Squad'),           # 140pts ✓
    ('48-07', 'Terminator', 180, 'Terminator Assault Squad'), # 180pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Space Marines / Ultramarines units.

    Looks up each product by GW SKU and updates the linked UnitType's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products later
    and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Space Marines / Ultramarines units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Space Marines / Ultramarines points…\n')

        # Filter by faction so we only update the Space Marines UnitType row —
        # not any Black Templars or other cross-faction rows for the same product.
        sm_faction = Faction.objects.filter(name='Space Marines').first()
        if not sm_faction:
            self.stdout.write(self.style.ERROR(
                'Space Marines faction not found. Run populate_products first.'
            ))
            return

        # Also fetch Ultramarines faction for UM-exclusive products (55-xx SKUs)
        um_faction = Faction.objects.filter(name='Ultramarines').first()

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in SPACE_MARINES_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            # Ultramarines-exclusive products (Calgar, Guilliman, Honour Guard) sit
            # under the Ultramarines faction; all generic SM kits use Space Marines.
            faction = um_faction if product.faction == um_faction else sm_faction

            updated = UnitType.objects.filter(
                product=product,
                faction=faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(
                    f'  [updated] {product.name} > {points} pts'
                )
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {product.name} (SKU {gw_sku}) — product exists '
                        f'but no UnitType found. Run populate_units first.'
                    )
                )
                skipped_count += 1

        # Handle the 48-07 SKU collision (Tactical Squad + Terminator Assault Squad)
        # Must use name-filtered queries since .first() returns only one of the two.
        for gw_sku, name_filter, points, label in SM_SKU_COLLISIONS:
            product = Product.objects.filter(
                gw_sku=gw_sku, name__icontains=name_filter
            ).first()
            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            faction = um_faction if product.faction == um_faction else sm_faction
            updated = UnitType.objects.filter(
                product=product,
                faction=faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {product.name} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {product.name} (SKU {gw_sku}) — product exists '
                        f'but no UnitType found. Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
