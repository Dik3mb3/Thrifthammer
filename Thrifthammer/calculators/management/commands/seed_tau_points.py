"""
Management command: seed_tau_points

Sets the points_cost on UnitType records for all T'au Empire units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_tau_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the T'au Empire UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit T'au Empire 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    56-06 (Fire Warriors), 56-10 (Hammerhead Gunship), 56-13 (Broadside),
    56-14 (Stealth Battlesuits), 56-15 (Crisis Battlesuits),
    56-16 (Riptide Battlesuit), 56-19 (Pathfinders), 56-22 (Ethereal)
- Kit collision — 56-06 (T'au Fire Warriors): one kit builds both Strike Team
  (70pts) and Breacher Team (90pts). Seeded at 70pts (Strike Team base).
  Add a separate product for the Breacher Team variant later.
- Kit collision — 56-15 (Crisis Battlesuits): one kit builds Fireknife (120pts),
  Starscythe (110pts), and Sunforge (140pts) variants. Seeded at 110pts
  (Starscythe, base/lowest cost). Add separate products for other variants later.
- 56-25 (Combat Patrol) is a bundle — no standalone UnitType entry.
- Forge World / Apocalypse products (Ta'unar, AX-1-0 Tiger Shark, Manta)
  use placeholder SKUs; skip gracefully until added to DB.
- Tidewall fortifications use placeholder SKUs.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — T'au Empire 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
TAU_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('56-40', 100, 'Commander Shadowsun'),             # 100pts ✓
    ('56-41',  85, 'Commander Farsight'),              # 85pts  ✓
    ('56-42',  60, 'Darkstrider'),                     # 60pts  ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('56-43',  95, 'Commander in Coldstar Battlesuit'), # 95pts ✓
    ('56-44',  80, 'Commander in Enforcer Battlesuit'), # 80pts  ✓
    ('56-22',  50, 'Ethereal'),                        # 50pts  ✓
    ('56-45',  50, 'Cadre Fireblade'),                 # 50pts  ✓
    ('56-46',  60, 'Firesight Team'),                  # 60pts  ✓
    # ── Kroot characters ──────────────────────────────────────────────────────
    ('56-47',  45, 'Kroot Flesh Shaper'),              # 45pts  ✓
    ('56-48',  80, 'Kroot Lone-spear'),                # 80pts  ✓
    ('56-49',  55, 'Kroot Trail Shaper'),              # 55pts  ✓
    ('56-50',  50, 'Kroot War Shaper'),                # 50pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('56-06',  70, 'Strike Team'),                     # 70pts  ✓ (Breacher Team=90pts, same kit)
    # ── Battlesuits ───────────────────────────────────────────────────────────
    ('56-15', 110, 'Crisis Battlesuits'),              # 110pts ✓ (Starscythe base; Fireknife=120, Sunforge=140, same kit)
    ('56-13',  80, 'Broadside Battlesuits'),           # 80pts  ✓
    ('56-14', 110, 'Stealth Battlesuits'),             # 110pts ✓
    ('56-16', 200, 'Riptide Battlesuit'),              # 200pts ✓
    ('56-51', 160, 'Ghostkeel Battlesuit'),            # 160pts ✓
    ('56-52', 360, 'Stormsurge'),                      # 360pts ✓
    # ── Kroot infantry ────────────────────────────────────────────────────────
    ('56-53',  65, 'Kroot Carnivores'),                # 65pts  ✓
    ('56-54',  85, 'Kroot Farstalkers'),               # 85pts  ✓
    ('56-55',  40, 'Kroot Hounds'),                    # 40pts  ✓
    ('56-56',  85, 'Krootox Rampagers'),               # 85pts  ✓
    ('56-57',  40, 'Krootox Riders'),                  # 40pts  ✓
    # ── Core infantry ─────────────────────────────────────────────────────────
    ('56-19',  90, 'Pathfinder Team'),                 # 90pts  ✓
    ('56-58',  65, 'Vespid Stingwings'),               # 65pts  ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('56-10', 145, 'Hammerhead Gunship'),              # 145pts ✓
    ('56-59', 150, 'Sky Ray Gunship'),                 # 150pts ✓
    ('56-60',  85, 'Devilfish'),                       # 85pts  ✓
    ('56-61',  60, 'Piranhas'),                        # 60pts  ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('56-62', 160, 'Sun Shark Bomber'),                # 160pts ✓
    # ── Fortifications ────────────────────────────────────────────────────────
    ('56-63',  85, 'Tidewall Droneport'),              # 85pts  ✓
    ('56-64',  90, 'Tidewall Gunrig'),                 # 90pts  ✓
    ('56-65',  85, 'Tidewall Shieldline'),             # 85pts  ✓
    # ── Forge World / Super-heavies ───────────────────────────────────────────
    ('56-66', 790, "Ta'unar Supremacy Armour"),        # 790pts ✓ (FW resin placeholder)
    ('56-67', 315, 'AX-1-0 Tiger Shark'),              # 315pts ✓ (FW placeholder)
    ('56-68', 325, 'Tiger Shark'),                     # 325pts ✓ (FW placeholder)
    ('56-69', 2100, 'Manta'),                          # 2100pts ✓ (FW super-heavy placeholder)
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for T'au Empire units.

    Looks up each product by GW SKU, then filters for the T'au Empire
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = "Seed 10th Edition points values for T'au Empire units."

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write("Seeding T'au Empire points…\n")

        tau_faction = Faction.objects.filter(name="T'au Empire").first()
        if not tau_faction:
            self.stdout.write(self.style.ERROR(
                "T'au Empire faction not found. Run populate_products first."
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in TAU_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=tau_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — T\'au Empire UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
