"""
Management command: seed_chaos_knights_points

Sets the points_cost on UnitType records for all Chaos Knights units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_chaos_knights_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Chaos Knights UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Chaos Knights 10th Edition list.
- As of initial creation, NO Chaos Knights products exist in the DB.
  All entries will [skip] until populate_products.py is updated with CK SKUs.

Kit → Variant mapping (for reference when adding products):
  55-10 (Chaos Knight Ruinator): builds Knight Ruinator, Knight Abominant,
      Knight Desecrator, Knight Despoiler, Knight Rampager — five variants.
  55-11 (Knight Tyrant): Dominus-class Chaos Knight — single variant.
  55-20 (War Dogs): builds 2x War Dog Executioner OR 2x War Dog Huntsman
      OR 2x War Dog Karnivore OR 2x War Dog Brigand OR 2x War Dog Stalker.
      War Dog Moirax is a separate Forge World resin kit.
  31-06 / 31-66 / 31-67: Cerastus plastic kits (HH range) — same kits used
      for both Imperial and Chaos Cerastus Knights. Already in DB under
      Imperial Knights; cross-faction CK UnitType rows needed in populate_units.
  Forge World resin only (not stocked): Atrapos, Moirax, Acastus
      Porphyrion/Asterius, Questoris Magaera/Styrix.

Multi-variant kits (55-10, 55-20) are seeded at their lowest-cost variant.
Cerastus kits (31-xx) already exist in DB — their CK UnitType rows will be
populated once populate_units creates cross-faction entries.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Chaos Knights 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
CHAOS_KNIGHTS_POINTS = [
    # ── Questoris-class Chaos Knights (55-10 builds all five variants) ────────
    # Seeded at Knight Ruinator / Abominant / Desecrator (355pts) — base cost.
    # Knight Rampager (365pts) and Knight Despoiler (390pts) are higher-cost builds.
    ('55-10', 355, 'Chaos Knight Ruinator'),               # Ruinator=355, Abominant=355, Desecrator=355, Rampager=365, Despoiler=390

    # ── Dominus-class Chaos Knight (55-11 — Knight Tyrant only) ──────────────
    ('55-11', 410, 'Knight Tyrant'),                       # 410pts ✓

    # ── War Dogs (55-20 builds 2 per box — all variants) ─────────────────────
    # Seeded at 130pts (War Dog Executioner — lowest cost variant).
    ('55-20', 130, 'War Dogs'),                            # Executioner=130, Brigand=140, Huntsman=140, Stalker=140, Karnivore=150

    # ── War Dog Moirax (Forge World resin — placeholder SKU) ─────────────────
    ('55-21', 150, 'War Dog Moirax'),                      # 150pts ✓ (FW resin, not yet in DB)

    # ── Cerastus-class Chaos Knights (shared HH plastic kits, already in DB
    #    under Imperial Knights — need cross-faction CK UnitType rows) ─────────
    ('31-67', 385, 'Chaos Cerastus Knight Acheron'),       # 385pts ✓
    ('31-06', 385, 'Chaos Cerastus Knight Lancer'),        # 385pts ✓
    ('31-66', 385, 'Chaos Cerastus Knight Castigator'),    # 385pts ✓

    # ── Cerastus Knight Atrapos (Forge World resin — placeholder SKU) ─────────
    ('55-22', 395, 'Chaos Cerastus Knight Atrapos'),       # 395pts ✓ (FW resin, not yet in DB)

    # ── Questoris Knight Magaera / Styrix Chaos variants (FW resin) ───────────
    ('55-23', 375, 'Chaos Questoris Knight Magaera'),      # 375pts ✓ (FW resin, not yet in DB)
    ('55-24', 375, 'Chaos Questoris Knight Styrix'),       # 375pts ✓ (FW resin, not yet in DB)

    # ── Acastus-class Chaos Knights (Forge World resin — placeholder SKUs) ────
    ('55-25', 700, 'Chaos Acastus Knight Porphyrion'),     # 700pts ✓ (FW resin, not yet in DB)
    ('55-26', 765, 'Chaos Acastus Knight Asterius'),       # 765pts ✓ (FW resin, not yet in DB)
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Chaos Knights units.

    Looks up each product by GW SKU, then filters for the Chaos Knights
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Chaos Knights units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Chaos Knights points…\n')

        ck_faction = Faction.objects.filter(name='Chaos Knights').first()
        if not ck_faction:
            self.stdout.write(self.style.ERROR(
                'Chaos Knights faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in CHAOS_KNIGHTS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=ck_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Chaos Knights UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
