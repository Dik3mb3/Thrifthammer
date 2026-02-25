"""
Management command: seed_custodes_points

Sets the points_cost on UnitType records for all Adeptus Custodes units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_custodes_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Adeptus Custodes UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Adeptus Custodes 10th Edition list.
- SKUs not yet in the DB are included so they seed automatically when products are added.
- Currently seeded SKUs in DB: 01-02, 01-07, 01-08, 01-10, 01-11
- 01-20 (Combat Patrol) is a bundle — no UnitType entry.
- All other units will skip gracefully until products are added.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Adeptus Custodes 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
CUSTODES_POINTS = [
    # ── Named characters ─────────────────────────────────────────────────────
    ('01-01',  65, 'Aleya'),                                   # 65pts  ✓
    ('01-02', 140, 'Trajann Valoris'),                         # 140pts ✓
    ('01-03', 110, 'Valerian'),                                # 110pts ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('01-04', 120, 'Blade Champion'),                          # 120pts ✓
    ('01-05',  55, 'Knight-Centura'),                          # 55pts  ✓
    ('01-07', 120, 'Shield-Captain'),                          # 120pts ✓
    ('01-12', 130, 'Shield-Captain in Allarus Terminator Armour'),  # 130pts ✓
    ('01-13', 150, 'Shield-Captain on Dawneagle Jetbike'),     # 150pts ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('01-08', 150, 'Custodian Guard'),                         # 150pts ✓
    ('01-14', 250, 'Custodian Guard with Adrasite and Pyrithite Spears'),  # 250pts ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('01-15', 110, 'Allarus Custodians'),                      # 110pts ✓
    ('01-16', 195, 'Aquilon Custodians'),                      # 195pts ✓
    ('01-10', 210, 'Custodian Wardens'),                       # 210pts ✓
    ('01-17',  40, 'Prosecutors'),                             # 40pts  ✓
    ('01-18', 225, 'Sagittarum Custodians'),                   # 225pts ✓
    ('01-19',  45, 'Vigilators'),                              # 45pts  ✓
    ('01-21',  45, 'Witchseekers'),                            # 45pts  ✓
    # ── Fast Attack / Mounted ─────────────────────────────────────────────────
    ('01-11', 150, 'Vertus Praetors'),                         # 150pts ✓
    ('01-22', 225, 'Agamatus Custodians'),                     # 225pts ✓
    ('01-23', 165, 'Venatari Custodians'),                     # 165pts ✓
    ('01-24', 105, 'Pallas Grav-attack'),                      # 105pts ✓
    # ── Walkers / Dreadnoughts ────────────────────────────────────────────────
    ('01-25', 155, 'Contemptor-Achillus Dreadnought'),         # 155pts ✓
    ('01-26', 165, 'Contemptor-Galatus Dreadnought'),          # 165pts ✓
    ('01-27', 225, 'Telemon Heavy Dreadnought'),               # 225pts ✓
    ('01-28', 170, 'Venerable Contemptor Dreadnought'),        # 170pts ✓
    # ── Transports ────────────────────────────────────────────────────────────
    ('01-06',  75, 'Anathema Psykana Rhino'),                  # 75pts  ✓
    ('01-29', 200, 'Coronus Grav-carrier'),                    # 200pts ✓
    # ── Heavy Vehicles ────────────────────────────────────────────────────────
    ('01-30', 215, 'Caladius Grav-tank'),                      # 215pts ✓
    ('01-31', 220, 'Venerable Land Raider'),                   # 220pts ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('01-32', 580, 'Ares Gunship'),                            # 580pts ✓
    ('01-33', 690, 'Orion Assault Dropship'),                  # 690pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Adeptus Custodes units.

    Looks up each product by GW SKU, then filters for the Adeptus Custodes
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Adeptus Custodes units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Adeptus Custodes points…\n')

        custodes_faction = Faction.objects.filter(name='Adeptus Custodes').first()
        if not custodes_faction:
            self.stdout.write(self.style.ERROR(
                'Adeptus Custodes faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in CUSTODES_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=custodes_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Custodes UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
