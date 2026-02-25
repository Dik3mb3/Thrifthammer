"""
Management command: seed_black_templars_points

Sets the points_cost on UnitType records for all Black Templars units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_black_templars_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Black Templars UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units — those commands create the
  products and UnitType rows respectively.
- Do NOT add to the Procfile yet (same rule as seed_ultramarines_points).
- Points values are for standard unit sizes as listed in New Recruit.
- Some values DIFFER from the Space Marines equivalents (e.g. Chaplain 60pts
  here vs 75pts for Space Marines, Repulsor Executioner 235pts vs 220pts).
  The faction filter on the update call ensures these remain independent.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Black Templars 10th Edition list.
# Includes both BT-exclusive units (55-xx SKUs) and shared SM kits (48-xx).
# ---------------------------------------------------------------------------
BLACK_TEMPLARS_POINTS = [
    # ── BT-exclusive characters & units ─────────────────────────────────────
    ('55-22', 100, "Emperor's Champion"),
    ('55-21', 120, 'High Marshal Helbrecht'),
    ('55-20', 150, 'Primaris Crusader Squad'),
    ('55-23', 105, 'Sword Brethren'),
    ('55-24', 110, 'Chaplain Grimaldus'),
    ('55-25',  70, 'Castellan'),
    ('55-26',  60, 'Execrator'),
    ('55-27',  55, 'Crusade Ancient'),
    ('55-28',  80, 'Marshal'),
    # ── Shared SM characters — BT-specific costs ─────────────────────────────
    ('48-34',  50, 'Ancient'),
    ('48-33',  50, 'Apothecary'),
    ('48-32',  60, 'Chaplain'),          # 60pts BT | 75pts Space Marines
    ('48-36',  70, 'Judiciar'),
    ('48-61',  55, 'Lieutenant'),
    ('48-62',  80, 'Captain'),
    ('48-37', 105, 'Company Heroes'),
    # ── Battleline ───────────────────────────────────────────────────────────
    ('48-75',  80, 'Intercessor Squad'),
    ('48-76',  75, 'Assault Intercessor Squad'),
    ('48-29',  70, 'Scout Squad'),
    ('48-45',  90, 'Infernus Squad'),
    # ── Infantry ─────────────────────────────────────────────────────────────
    ('48-06', 175, 'Terminator Squad'),  # 175pts BT | 170pts Space Marines
    ('48-92',  95, 'Aggressor Squad'),
    ('48-38',  80, 'Bladeguard Veteran Squad'),
    ('48-15', 120, 'Devastator Squad'),
    ('48-98',  85, 'Eliminator Squad'),
    ('48-39',  90, 'Eradicator Squad'),
    ('48-96',  80, 'Incursor Squad'),
    ('48-41', 100, 'Infiltrator Squad'),
    ('48-43',  85, 'Sternguard Veteran Squad'),  # 85pts BT | 100pts Space Marines
    ('48-08', 100, 'Vanguard Veteran Squad'),
    # ── Mounted / Fast Attack ─────────────────────────────────────────────────
    ('48-40',  80, 'Outrider Squad'),
    ('48-42',  60, 'Invader ATV'),
    ('48-97', 120, 'Inceptor Squad'),
    ('48-99',  75, 'Suppressor Squad'),
    # ── Vehicles / Dreadnoughts ───────────────────────────────────────────────
    ('48-46', 150, 'Ballistus Dreadnought'),
    ('48-44', 160, 'Brutalis Dreadnought'),
    ('48-93', 195, 'Redemptor Dreadnought'),
    ('48-23', 140, 'Predator Destructor'),
    ('48-25', 190, 'Whirlwind'),
    ('48-26', 185, 'Vindicator'),
    ('48-95', 235, 'Repulsor Executioner'),  # 235pts BT | 220pts Space Marines
    # ── Transports ───────────────────────────────────────────────────────────
    ('48-94',  85, 'Impulsor'),              # 85pts BT | 80pts Space Marines
    ('48-85', 180, 'Repulsor'),
    ('48-21', 220, 'Land Raider'),
    ('48-22', 220, 'Land Raider Crusader'),
    # ── Fortifications ────────────────────────────────────────────────────────
    ('48-27', 175, 'Hammerfall Bunker'),
    ('48-28',  75, 'Firestrike Servo-Turrets'),
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Black Templars units.

    Looks up each product by GW SKU, then filters for the Black Templars
    UnitType specifically and updates only that row's points_cost. This
    ensures Space Marines UnitType rows for the same product are untouched.
    Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Black Templars units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Black Templars points…\n')

        # Filter by faction so we only update Black Templars UnitType rows —
        # not Space Marines or other cross-faction rows for the same product.
        bt_faction = Faction.objects.filter(name='Black Templars').first()
        if not bt_faction:
            self.stdout.write(self.style.ERROR(
                'Black Templars faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in BLACK_TEMPLARS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            # Filter by BOTH product AND faction — critical for multi-faction safety
            updated = UnitType.objects.filter(
                product=product,
                faction=bt_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — BT UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        # ── 48-07 SKU collision (Tactical Squad + Terminator Assault Squad) ──────
        # Both products share gw_sku 48-07; must use name filtering to distinguish.
        BT_SKU_COLLISIONS = [
            ('48-07', 'Tactical',   140, 'Tactical Squad'),            # 140pts ✓
            ('48-07', 'Terminator', 180, 'Terminator Assault Squad'),  # 180pts ✓
        ]
        for gw_sku, name_filter, points, label in BT_SKU_COLLISIONS:
            product = Product.objects.filter(
                gw_sku=gw_sku, name__icontains=name_filter
            ).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  [skip]    {label} (SKU {gw_sku} not found in DB)'
                ))
                skipped_count += 1
                continue
            updated = UnitType.objects.filter(
                product=product,
                faction=bt_faction,
            ).update(points_cost=points)
            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(self.style.WARNING(
                    f'  [no unit] {label} (SKU {gw_sku}) — BT UnitType not found. '
                    f'Run populate_units first.'
                ))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
