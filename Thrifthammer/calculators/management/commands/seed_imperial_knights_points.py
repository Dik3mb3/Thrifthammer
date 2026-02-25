"""
Management command: seed_imperial_knights_points

Sets the points_cost on UnitType records for all Imperial Knights units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_imperial_knights_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Imperial Knights UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Imperial Knights 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.

Kit → Variant mapping:
  54-22 (Knight Questoris) builds:
      Knight Paladin (375pts), Knight Errant (365pts), Knight Gallant (365pts),
      Knight Warden (375pts), Knight Crusader (385pts), Knight Defender (415pts)
  54-15 (Knight Preceptor / Canis Rex) builds:
      Knight Preceptor (365pts), Canis Rex (415pts — named character)
  54-21 (Knight Dominus) builds:
      Knight Castellan (410pts), Knight Valiant (410pts)
  54-20 (Knight Armigers) builds:
      Armiger Warglaive (140pts) OR Armiger Helverin (140pts)
  31-06: Cerastus Knight Lancer (395pts) — single-variant kit
  31-66: Cerastus Knight Castigator (395pts) — single-variant kit
  31-67: Cerastus Knight Acheron (395pts) — single-variant kit

Multi-variant kits (54-22, 54-15, 54-21, 54-20): one product row covers all
variants built from that kit. Points seeded at the most common/base variant.
Forge World resin kits (Atrapos, Moirax, Acastus Porphyrion/Asterius,
Magaera, Styrix) are included with placeholder SKUs for future use.

Currently seeded SKUs in DB: 54-15, 54-20, 54-21, 54-22, 31-06, 31-66, 31-67
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Imperial Knights 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
#
# Multi-build kits are seeded at their lowest-cost variant as the base.
# All Questoris variants share 54-22; all Dominus variants share 54-21;
# both Armigers share 54-20.
# ---------------------------------------------------------------------------
IMPERIAL_KNIGHTS_POINTS = [
    # ── Named characters (unique single-variant kits) ─────────────────────────
    # Canis Rex is built from 54-15 (Knight Preceptor / Canis Rex kit).
    # Seeded as the Canis Rex points (415pts) since the product name reflects both.
    ('54-15', 365, 'Knight Preceptor / Canis Rex'),        # Preceptor=365, CRex=415 — base at Preceptor

    # ── Questoris-class Knights (54-22 builds all six variants) ──────────────
    # Seeded at Knight Errant (365pts) as the base/lowest-cost Questoris variant.
    # All six share the same physical kit — one UnitType row in the DB.
    ('54-22', 365, 'Knight Questoris'),                    # Errant=365, Gallant=365, Paladin=375, Warden=375, Crusader=385, Defender=415

    # ── Dominus-class Knights (54-21 builds Castellan or Valiant) ────────────
    # Both cost 410pts — seeded at 410pts.
    ('54-21', 410, 'Knight Dominus'),                      # Castellan=410, Valiant=410

    # ── Armiger-class Knights (54-20 builds Warglaive or Helverin) ───────────
    # Both cost 140pts — seeded at 140pts.
    ('54-20', 140, 'Knight Armigers'),                     # Warglaive=140, Helverin=140

    # ── Armiger Moirax (Forge World resin — placeholder SKU) ─────────────────
    ('54-23', 150, 'Armiger Moirax'),                      # 150pts ✓ (FW resin, not yet in DB)

    # ── Cerastus-class Knights (separate plastic kits, one variant each) ─────
    ('31-06', 395, 'Cerastus Knight Lancer'),              # 395pts ✓
    ('31-66', 395, 'Cerastus Knight Castigator'),          # 395pts ✓
    ('31-67', 395, 'Cerastus Knight Acheron'),             # 395pts ✓

    # ── Cerastus Knight Atrapos (Forge World resin — placeholder SKU) ─────────
    ('54-24', 405, 'Cerastus Knight Atrapos'),             # 405pts ✓ (FW resin, not yet in DB)

    # ── Questoris Knight Magaera / Styrix (Forge World resin) ────────────────
    ('54-25', 385, 'Questoris Knight Magaera'),            # 385pts ✓ (FW resin, not yet in DB)
    ('54-26', 385, 'Questoris Knight Styrix'),             # 385pts ✓ (FW resin, not yet in DB)

    # ── Acastus-class Knights (Forge World resin — placeholder SKUs) ──────────
    ('54-27', 700, 'Acastus Knight Porphyrion'),           # 700pts ✓ (FW resin, not yet in DB)
    ('54-28', 765, 'Acastus Knight Asterius'),             # 765pts ✓ (FW resin, not yet in DB)
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Imperial Knights units.

    Looks up each product by GW SKU, then filters for the Imperial Knights
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Imperial Knights units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Imperial Knights points…\n')

        knights_faction = Faction.objects.filter(name='Imperial Knights').first()
        if not knights_faction:
            self.stdout.write(self.style.ERROR(
                'Imperial Knights faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in IMPERIAL_KNIGHTS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=knights_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Imperial Knights UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
