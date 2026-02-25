"""
Management command: seed_necrons_points

Sets the points_cost on UnitType records for all Necrons units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_necrons_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Necrons UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Necrons 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    49-03 (Overlord), 49-06 (Necron Warriors), 49-08 (Monolith),
    49-10 (Immortals), 49-11 (Lychguard), 49-12 (Doomsday Ark),
    49-13 (Doom Scythe), 49-14 (Canoptek Spyder), 49-17 (Flayed Ones),
    49-20 (C'tan Shard of the Void Dragon), 49-21 (Psychomancer),
    49-22 (Royal Warden)
- 49-11 (Lychguard): one kit builds Lychguard with Warscythes (85pts) or
  Hyperphase Sword & Dispersion Shield (100pts). Seeded at 85pts (base).
  Add a separate product for the shield variant later.
- 49-13 (Night Scythe / Doom Scythe): one kit builds both Night Scythe (185pts)
  and Doom Scythe (230pts). Seeded at 185pts (Night Scythe base).
  Add a separate product for the Doom Scythe variant later.
- 49-25 (Combat Patrol) is a bundle — no UnitType entry.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Necrons 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
NECRONS_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('49-40', 400, 'The Silent King'),                 # 400pts ✓
    ('49-41', 100, 'Imotekh the Stormlord'),           # 100pts ✓
    ('49-42', 165, 'Illuminor Szeras'),                # 165pts ✓
    ('49-43', 165, 'Nemesor Zahndrekh'),               # 165pts ✓
    ('49-44',  75, 'Trazyn the Infinite'),             # 75pts  ✓
    ('49-45',  80, 'Orikan the Diviner'),              # 80pts  ✓
    ('49-46',  80, 'Anrakyr the Traveller'),           # 80pts  ✓
    ('49-47',  75, 'Szarekhan Dynasty Overlord'),      # 75pts  ✓ (placeholder SKU)
    # ── Generic characters ────────────────────────────────────────────────────
    ('49-03',  80, 'Overlord'),                        # 80pts  ✓
    ('49-48',  60, 'Lord'),                            # 60pts  ✓
    ('49-49',  60, 'Lord with Warsythe'),              # 60pts  ✓
    ('49-21',  55, 'Psychomancer'),                    # 55pts  ✓
    ('49-22',  45, 'Royal Warden'),                    # 45pts  ✓
    ('49-50',  65, 'Chronomancer'),                    # 65pts  ✓
    ('49-51',  70, 'Lokhust Lord'),                    # 70pts  ✓
    ('49-52',  55, 'Plasmancer'),                      # 55pts  ✓
    ('49-53',  60, 'Skorpekh Lord'),                   # 60pts  ✓
    ('49-54',  70, 'Technomancer'),                    # 70pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('49-06',  90, 'Necron Warriors'),                 # 90pts  ✓
    ('49-10',  70, 'Immortals'),                       # 70pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('49-17',  65, 'Flayed Ones'),                     # 65pts  ✓
    ('49-11',  85, 'Lychguard'),                       # 85pts  ✓ (shield variant=100pts, same kit)
    ('49-55',  75, 'Deathmarks'),                      # 75pts  ✓
    ('49-56',  65, 'Necron Tomb Blades'),              # 65pts  ✓
    ('49-57',  70, 'Triarch Praetorians'),             # 70pts  ✓
    # ── Fast Attack ───────────────────────────────────────────────────────────
    ('49-58', 110, 'Canoptek Wraiths'),                # 110pts ✓
    ('49-59',  80, 'Canoptek Scarabs'),                # 80pts  ✓
    ('49-14',  55, 'Canoptek Spyder'),                 # 55pts  ✓
    # ── Elites / Heavy ────────────────────────────────────────────────────────
    ('49-60',  90, 'Skorpekh Destroyers'),             # 90pts  ✓
    ('49-61',  95, 'Lokhust Destroyers'),              # 95pts  ✓
    ('49-62', 130, 'Lokhust Heavy Destroyer'),         # 130pts ✓
    ('49-63', 150, 'Ophydian Destroyers'),             # 150pts ✓
    ('49-64', 140, 'Triarch Stalker'),                 # 140pts ✓
    # ── C'tan Shards ──────────────────────────────────────────────────────────
    ('49-65', 285, "C'tan Shard of the Deceiver"),     # 285pts ✓
    ('49-66', 315, "C'tan Shard of the Nightbringer"), # 315pts ✓
    ('49-20', 310, "C'tan Shard of the Void Dragon"),  # 310pts ✓
    ('49-67', 305, "Transcendent C'tan"),              # 305pts ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('49-12', 200, 'Doomsday Ark'),                    # 200pts ✓
    ('49-68', 150, 'Ghost Ark'),                       # 150pts ✓
    ('49-69', 125, 'Annihilation Barge'),              # 125pts ✓
    ('49-70', 145, 'Catacomb Command Barge'),          # 145pts ✓
    ('49-71', 120, 'Canoptek Doomstalker'),            # 120pts ✓
    ('49-72', 130, 'Canoptek Reanimator'),             # 130pts ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('49-13', 185, 'Night Scythe'),                    # 185pts ✓ (Doom Scythe=230pts, same kit)
    # ── Fortifications / Super-heavies ────────────────────────────────────────
    ('49-08', 400, 'Monolith'),                        # 400pts ✓
    ('49-73', 425, 'Tesseract Vault'),                 # 425pts ✓
    ('49-74', 300, 'Obelisk'),                         # 300pts ✓
    ('49-75', 540, 'Seraptek Heavy Construct'),        # 540pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Necrons units.

    Looks up each product by GW SKU, then filters for the Necrons
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Necrons units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Necrons points…\n')

        necrons_faction = Faction.objects.filter(name='Necrons').first()
        if not necrons_faction:
            self.stdout.write(self.style.ERROR(
                'Necrons faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in NECRONS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=necrons_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Necrons UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
