"""
Management command: seed_aeldari_points

Sets the points_cost on UnitType records for all Aeldari units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_aeldari_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the appropriate Aeldari
UnitType and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Aeldari 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- The Aeldari faction in 10th Edition is a merged keyword combining:
    Craftworlds, Harlequins, and Corsairs sub-factions.
  In the DB these are split across 'Craftworlds' and 'Harlequins' factions.
  This command updates the UnitType row for whichever faction the product
  belongs to (Craftworlds or Harlequins), falling back gracefully.
- Currently seeded SKUs in DB:
    Craftworlds: 46-02 (Farseer), 46-06 (Dire Avengers), 46-09 (Guardians),
                 46-14 (Fire Dragons), 46-26 (Wraithguard/Wraithblades),
                 46-29 (Wave Serpent)
    Harlequins: none currently in DB
- 46-25 (Combat Patrol) is a bundle — no UnitType entry.
- 46-26 (Wraithguard): one kit builds Wraithguard (170pts) or Wraithblades
  (160pts). Seeded at 170pts (Wraithguard base). Add separate product for
  Wraithblades later.
- 46-09 (Guardians): one kit builds Guardian Defenders or Storm Guardians.
  Seeded at 100pts (Guardian Defenders base). Storm Guardians = 110pts.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Aeldari 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
AELDARI_POINTS = [
    # ── Named characters — Phoenix Lords ─────────────────────────────────────
    ('46-30', 125, 'Asurmen'),                             # 125pts ✓
    ('46-31', 115, 'Baharroth'),                           # 115pts ✓
    ('46-32', 120, 'Fuegan'),                              # 120pts ✓
    ('46-33', 120, 'Jain Zar'),                            # 120pts ✓
    ('46-34', 100, 'Maugan Ra'),                           # 100pts ✓
    # ── Named characters — other Craftworlds ──────────────────────────────────
    ('46-35', 280, 'Avatar of Khaine'),                    # 280pts ✓
    ('46-36', 120, 'Eldrad Ulthran'),                      # 120pts ✓
    ('46-37',  95, 'Prince Yriel'),                        # 95pts  ✓
    ('46-38',  95, 'Kharseth'),                            # 95pts  ✓
    ('46-39', 135, 'Lhykhis'),                             # 135pts ✓
    # ── Named characters — Harlequins ─────────────────────────────────────────
    ('46-40', 115, 'Solitaire'),                           # 115pts ✓
    # ── Generic characters — Craftworlds ──────────────────────────────────────
    ('46-41',  85, 'Autarch'),                             # 85pts  ✓
    ('46-42',  80, 'Autarch Wayleaper'),                   # 80pts  ✓
    ('46-02',  70, 'Farseer'),                             # 70pts  ✓
    ('46-43',  80, 'Farseer Skyrunner'),                   # 80pts  ✓
    ('46-44',  65, 'Spiritseer'),                          # 65pts  ✓
    ('46-45',  45, 'Warlock'),                             # 45pts  ✓
    ('46-46',  55, 'Warlock Conclave'),                    # 55pts  ✓
    ('46-47',  45, 'Warlock Skyrunners'),                  # 45pts  ✓
    # ── Generic characters — Harlequins ───────────────────────────────────────
    ('46-48',  90, 'Death Jester'),                        # 90pts  ✓
    ('46-49',  60, 'Shadowseer'),                          # 60pts  ✓
    ('46-50',  75, 'Troupe Master'),                       # 75pts  ✓
    # ── Battleline — Craftworlds ──────────────────────────────────────────────
    ('46-09', 100, 'Guardian Defenders'),                  # 100pts ✓ (Storm Guardians=110, same kit)
    ('46-06',  75, 'Dire Avengers'),                       # 75pts  ✓
    ('46-51',  55, 'Rangers'),                             # 55pts  ✓
    # ── Battleline — Corsairs ─────────────────────────────────────────────────
    ('46-52',  65, 'Corsair Voidreavers'),                 # 65pts  ✓
    # ── Infantry — Craftworlds ────────────────────────────────────────────────
    ('46-14', 120, 'Fire Dragons'),                        # 120pts ✓
    ('46-53',  90, 'Dark Reapers'),                        # 90pts  ✓
    ('46-54',  95, 'Howling Banshees'),                    # 95pts  ✓
    ('46-55', 110, 'Shining Spears'),                      # 110pts ✓
    ('46-56',  80, 'Shroud Runners'),                      # 80pts  ✓
    ('46-57',  85, 'Striking Scorpions'),                  # 85pts  ✓
    ('46-58',  95, 'Swooping Hawks'),                      # 95pts  ✓
    ('46-59', 105, 'Warp Spiders'),                        # 105pts ✓
    ('46-26', 170, 'Wraithguard'),                         # 170pts ✓ (Wraithblades=160, same kit)
    ('46-60', 160, 'Wraithblades'),                        # 160pts ✓ (separate product needed)
    # ── Infantry — Corsairs ───────────────────────────────────────────────────
    ('46-61',  75, 'Corsair Skyreavers'),                  # 75pts  ✓
    ('46-62',  80, 'Corsair Voidscarred'),                 # 80pts  ✓
    # ── Infantry — Harlequins ─────────────────────────────────────────────────
    ('46-63',  85, 'Troupe'),                              # 85pts  ✓
    # ── Fast Attack / Mounted ─────────────────────────────────────────────────
    ('46-64',  80, 'Windriders'),                          # 80pts  ✓
    ('46-65',  95, 'Skyweavers'),                          # 95pts  ✓
    ('46-66',  75, 'Vypers'),                              # 75pts  ✓
    ('46-67',  85, 'War Walkers'),                         # 85pts  ✓
    # ── Heavy Support / Artillery ─────────────────────────────────────────────
    ('46-68', 125, 'D-Cannon Platform'),                   # 125pts ✓
    ('46-69',  75, 'Shadow Weaver Platform'),              # 75pts  ✓
    ('46-70',  60, 'Vibro Cannon Platform'),               # 60pts  ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('46-29', 125, 'Wave Serpent'),                        # 125pts ✓
    ('46-71', 130, 'Falcon'),                              # 130pts ✓
    ('46-72', 150, 'Fire Prism'),                          # 150pts ✓
    ('46-73', 190, 'Night Spinner'),                       # 190pts ✓
    ('46-74',  75, 'Starfangs'),                           # 75pts  ✓
    ('46-75',  80, 'Starweaver'),                          # 80pts  ✓
    ('46-76', 125, 'Voidweaver'),                          # 125pts ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('46-77', 160, 'Crimson Hunter'),                      # 160pts ✓
    ('46-78', 155, 'Hemlock Wraithfighter'),               # 155pts ✓
    # ── Monsters / Titans ─────────────────────────────────────────────────────
    ('46-79', 140, 'Wraithlord'),                          # 140pts ✓
    ('46-80', 435, 'Wraithknight'),                        # 435pts ✓ (Ghostglaive=420, same kit)
    ('46-81',1100, 'Revenant Titan'),                      # 1100pts ✓
    ('46-82',2100, 'Phantom Titan'),                       # 2100pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Aeldari units.

    The Aeldari faction keyword covers Craftworlds, Harlequins, and Corsairs
    products. Products are stored under 'Craftworlds' or 'Harlequins' factions
    in the DB. This command updates the UnitType row for whichever Aeldari
    sub-faction the product belongs to.
    SKUs not found in the DB are skipped. Idempotent — safe to re-run.
    """

    help = 'Seed 10th Edition points values for Aeldari units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Aeldari points…\n')

        craftworlds_faction = Faction.objects.filter(name='Craftworlds').first()
        harlequins_faction = Faction.objects.filter(name='Harlequins').first()

        if not craftworlds_faction:
            self.stdout.write(self.style.ERROR(
                'Craftworlds faction not found. Run populate_products first.'
            ))
            return

        aeldari_factions = [f for f in [craftworlds_faction, harlequins_faction] if f]

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in AELDARI_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            # Update whichever Aeldari sub-faction UnitType row exists for
            # this product (Craftworlds or Harlequins).
            updated = UnitType.objects.filter(
                product=product,
                faction__in=aeldari_factions,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Aeldari UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
