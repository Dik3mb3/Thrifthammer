"""
Management command: seed_chaos_daemons_points

Sets the points_cost on UnitType records for all Chaos Daemons units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_chaos_daemons_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Chaos Daemons UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Chaos Daemons 10th Edition list.
- As of initial creation, NO Chaos Daemons products exist in the DB.
  All entries will [skip] until populate_products.py is updated with daemon SKUs.
- Many daemon kits are dual-use (40K Chaos Daemons AND AoS god factions).
  The 97-xx SKUs below are the expected catalogue numbers once added.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Chaos Daemons 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# All SKUs are placeholders — add products to populate_products.py first.
# ---------------------------------------------------------------------------
CHAOS_DAEMONS_POINTS = [
    # ── Named characters — cross-god ─────────────────────────────────────────
    ('97-01', 375, "Be'lakor"),                            # 375pts ✓
    # ── Named characters — Khorne ─────────────────────────────────────────────
    ('97-02',  75, 'Karanak'),                             # 75pts  ✓
    ('97-03', 305, 'Skarbrand'),                           # 305pts ✓
    ('97-04',  85, 'Skulltaker'),                          # 85pts  ✓
    # ── Named characters — Nurgle ─────────────────────────────────────────────
    ('97-05',  80, 'Epidemius'),                           # 80pts  ✓
    ('97-06', 120, 'Horticulous Slimux'),                  # 120pts ✓
    ('97-07', 265, 'Rotigus'),                             # 265pts ✓
    # ── Named characters — Slaanesh ───────────────────────────────────────────
    ('97-13', 340, 'Shalaxi Helbane'),                     # 340pts ✓
    ('97-14', 120, "Syll'esske"),                          # 120pts ✓
    ('97-15',  95, 'The Masque of Slaanesh'),              # 95pts  ✓
    # ── Named characters — Tzeentch ───────────────────────────────────────────
    ('97-16', 285, 'Kairos Fateweaver'),                   # 285pts ✓
    ('97-17',  75, 'The Blue Scribes'),                    # 75pts  ✓
    ('97-18',  90, 'The Changeling'),                      # 90pts  ✓
    # ── Generic characters — Khorne ───────────────────────────────────────────
    ('97-19',  65, 'Bloodmaster'),                         # 65pts  ✓
    ('97-20', 305, 'Bloodthirster'),                       # 305pts ✓
    ('97-21', 100, 'Skullmaster'),                         # 100pts ✓
    # ── Generic characters — Nurgle ───────────────────────────────────────────
    ('97-22', 250, 'Great Unclean One'),                   # 250pts ✓
    ('97-23',  55, 'Poxbringer'),                          # 55pts  ✓
    ('97-24',  55, 'Sloppity Bilepiper'),                  # 55pts  ✓
    ('97-25',  60, 'Spoilpox Scrivener'),                  # 60pts  ✓
    # ── Generic characters — Slaanesh ─────────────────────────────────────────
    ('97-26', 100, 'Contorted Epitome'),                   # 100pts ✓
    ('97-27',  60, 'Infernal Enrapturess'),                # 60pts  ✓
    ('97-28', 240, 'Keeper of Secrets'),                   # 240pts ✓
    ('97-29', 140, 'Tormentbringer'),                      # 140pts ✓
    ('97-30',  60, 'Tranceweaver'),                        # 60pts  ✓
    # ── Generic characters — Tzeentch ─────────────────────────────────────────
    ('97-31',  60, 'Changecaster'),                        # 60pts  ✓
    ('97-32',  65, 'Exalted Flamer'),                      # 65pts  ✓
    ('97-33',  95, 'Fateskimmer'),                         # 95pts  ✓
    ('97-34',  60, 'Fluxmaster'),                          # 60pts  ✓
    ('97-35', 270, 'Lord of Change'),                      # 270pts ✓
    # ── Generic characters — Undivided ────────────────────────────────────────
    ('97-36', 190, 'Daemon Prince of Chaos'),              # 190pts ✓
    ('97-37', 180, 'Daemon Prince of Chaos with Wings'),   # 180pts ✓
    ('97-38', 165, 'Rendmaster on Blood Throne'),          # 165pts ✓
    # ── Battleline — Khorne ───────────────────────────────────────────────────
    ('97-08', 110, 'Bloodletters'),                        # 110pts ✓
    # ── Battleline — Nurgle ───────────────────────────────────────────────────
    ('97-09', 110, 'Plaguebearers'),                       # 110pts ✓
    # ── Battleline — Slaanesh ─────────────────────────────────────────────────
    ('97-39', 100, 'Daemonettes'),                         # 100pts ✓
    # ── Battleline — Tzeentch ─────────────────────────────────────────────────
    ('97-11', 140, 'Pink Horrors'),                        # 140pts ✓
    ('97-40', 125, 'Blue Horrors'),                        # 125pts ✓
    # ── Infantry — Khorne ─────────────────────────────────────────────────────
    ('97-41',  75, 'Flesh Hounds'),                        # 75pts  ✓
    # ── Infantry — Nurgle ─────────────────────────────────────────────────────
    ('97-42',  40, 'Nurglings'),                           # 40pts  ✓
    ('97-43', 110, 'Plague Drones'),                       # 110pts ✓
    # ── Infantry — Slaanesh ───────────────────────────────────────────────────
    ('97-44',  95, 'Fiends'),                              # 95pts  ✓
    ('97-45',  80, 'Hellflayers'),                         # 80pts  ✓
    ('97-46',  80, 'Seekers'),                             # 80pts  ✓
    # ── Infantry — Tzeentch ───────────────────────────────────────────────────
    ('97-47',  65, 'Flamers'),                             # 65pts  ✓
    ('97-48',  80, 'Screamers'),                           # 80pts  ✓
    # ── Vehicles / Monsters — Khorne ─────────────────────────────────────────
    ('97-49', 110, 'Bloodcrushers'),                       # 110pts ✓
    ('97-50', 180, 'Khorne Soul Grinder'),                 # 180pts ✓
    ('97-51',  95, 'Skull Cannon'),                        # 95pts  ✓
    # ── Vehicles / Monsters — Tzeentch ───────────────────────────────────────
    ('97-52', 115, 'Burning Chariot'),                     # 115pts ✓
    # ── Monsters — Nurgle ─────────────────────────────────────────────────────
    ('97-53',  65, 'Beasts of Nurgle'),                    # 65pts  ✓
    # ── Fortifications ────────────────────────────────────────────────────────
    ('97-54', 100, 'Feculent Gnarlmaw'),                   # 100pts ✓
    ('97-55', 105, 'Skull Altar'),                         # 105pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Chaos Daemons units.

    Looks up each product by GW SKU, then filters for the Chaos Daemons
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Chaos Daemons units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Chaos Daemons points…\n')

        daemons_faction = Faction.objects.filter(name='Chaos Daemons').first()
        if not daemons_faction:
            self.stdout.write(self.style.ERROR(
                'Chaos Daemons faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in CHAOS_DAEMONS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=daemons_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Chaos Daemons UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
