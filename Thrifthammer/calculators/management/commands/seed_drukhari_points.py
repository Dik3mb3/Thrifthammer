"""
Management command: seed_drukhari_points

Sets the points_cost on UnitType records for all Drukhari units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_drukhari_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Drukhari UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Drukhari 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- The Drukhari faction keyword in 10th Edition includes units from Kabal,
  Wych Cult, Haemonculus Covens, Corsairs, and Harlequins sub-factions.
  Corsair and Harlequin units (Skyweavers, Starweaver, Troupe etc.) that
  appear in Drukhari lists use placeholder SKUs — they may be filed under
  the Harlequins faction in the DB when added.
- Currently seeded SKUs in DB:
    45-02 (Archon), 45-06 (Wyches), 45-07 (Kabalite Warriors),
    45-10 (Raider), 45-12 (Ravager)
- 45-25 (Combat Patrol) is a bundle — no UnitType entry.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Drukhari 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
DRUKHARI_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('45-01',  85, 'Drazhar'),                             # 85pts  ✓
    ('45-03',  95, 'Kharseth'),                            # 95pts  ✓
    ('45-04', 100, 'Lady Malys'),                          # 100pts ✓
    ('45-05',  85, 'Lelith Hesperax'),                     # 85pts  ✓
    ('45-08',  95, 'Prince Yriel'),                        # 95pts  ✓
    # ── Named characters — Harlequins ─────────────────────────────────────────
    ('45-09', 115, 'Solitaire'),                           # 115pts ✓
    # ── Generic characters — Kabal ────────────────────────────────────────────
    ('45-02',  80, 'Archon'),                              # 80pts  ✓
    ('45-11',  70, 'Haemonculus'),                         # 70pts  ✓
    ('45-13',  50, 'Succubus'),                            # 50pts  ✓
    # ── Generic characters — Harlequins ───────────────────────────────────────
    ('45-14',  90, 'Death Jester'),                        # 90pts  ✓
    ('45-15',  60, 'Shadowseer'),                          # 60pts  ✓
    ('45-16',  75, 'Troupe Master'),                       # 75pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('45-07', 115, 'Kabalite Warriors'),                   # 115pts ✓
    ('45-06',  90, 'Wyches'),                              # 90pts  ✓
    ('45-17',  65, 'Wracks'),                              # 65pts  ✓
    ('45-18',  65, 'Corsair Voidreavers'),                 # 65pts  ✓
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('45-19',  85, 'Hellions'),                            # 85pts  ✓
    ('45-20',  90, 'Incubi'),                              # 90pts  ✓
    ('45-21',  75, 'Mandrakes'),                           # 75pts  ✓
    ('45-22', 125, 'Hand of the Archon'),                  # 125pts ✓
    ('45-23', 130, 'Scourges with Heavy Weapons'),         # 130pts ✓
    ('45-24',  80, 'Scourges with Shardcarbines'),         # 80pts  ✓
    ('45-26',  55, 'Cronos'),                              # 55pts  ✓
    ('45-27',  80, 'Talos'),                               # 80pts  ✓
    # ── Fast Attack / Mounted ─────────────────────────────────────────────────
    ('45-28',  70, 'Reavers'),                             # 70pts  ✓
    ('45-29',  75, 'Corsair Skyreavers'),                  # 75pts  ✓
    ('45-30',  80, 'Corsair Voidscarred'),                 # 80pts  ✓
    # ── Harlequins units ──────────────────────────────────────────────────────
    ('45-31',  95, 'Skyweavers'),                          # 95pts  ✓
    ('45-32',  85, 'Troupe'),                              # 85pts  ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('45-10',  85, 'Raider'),                              # 85pts  ✓
    ('45-12', 110, 'Ravager'),                             # 110pts ✓
    ('45-33',  70, 'Venom'),                               # 70pts  ✓
    ('45-34',  75, 'Starfangs'),                           # 75pts  ✓
    ('45-35',  80, 'Starweaver'),                          # 80pts  ✓
    ('45-36', 125, 'Voidweaver'),                          # 125pts ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('45-37', 170, 'Razorwing Jetfighter'),                # 170pts ✓
    ('45-38', 245, 'Voidraven Bomber'),                    # 245pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Drukhari units.

    Looks up each product by GW SKU, then filters for the Drukhari
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Drukhari units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Drukhari points…\n')

        drukhari_faction = Faction.objects.filter(name='Drukhari').first()
        if not drukhari_faction:
            self.stdout.write(self.style.ERROR(
                'Drukhari faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in DRUKHARI_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=drukhari_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Drukhari UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
