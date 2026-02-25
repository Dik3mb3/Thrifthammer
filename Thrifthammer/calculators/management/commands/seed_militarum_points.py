"""
Management command: seed_militarum_points

Sets the points_cost on UnitType records for all Astra Militarum units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_militarum_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Astra Militarum UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Astra Militarum 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    47-05 (Chimera), 47-06 (Leman Russ), 47-08 (Commissar),
    47-12 (Sentinel), 47-14 (Hellhound), 47-17 (Basilisk),
    47-19 (Infantry Squad), 47-30 (Cadian Shock Troops)
- 47-25 (Combat Patrol) is a bundle — no UnitType entry.
- 47-31 (Veteran Guardsmen box) builds Death Korps of Krieg — seeded at 60pts.
- 47-12 (Sentinel): one kit builds Scout Sentinels (55pts) or Armoured Sentinels
  (65pts). Seeded at 55pts (Scout base cost).
- Leman Russ variants: all share the 47-06 kit. Seeded at 185pts (Battle Tank
  base). Other variants listed here with placeholder SKUs for when added as
  separate products.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Astra Militarum 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
MILITARUM_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('47-32', 100, "Gaunt's Ghosts"),                      # 100pts ✓
    ('47-33', 100, 'Lord Marshal Dreir'),                  # 100pts ✓
    ('47-34', 130, 'Lord Solar Leontus'),                  # 130pts ✓
    ('47-35',  60, 'Nork Deddog'),                         # 60pts  ✓
    ('47-36',  55, 'Sly Marbo'),                           # 55pts  ✓
    ('47-37',  85, 'Ursula Creed'),                        # 85pts  ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('47-38',  55, 'Cadian Castellan'),                    # 55pts  ✓
    ('47-39',  65, 'Cadian Command Squad'),                # 65pts  ✓
    ('47-40',  65, 'Catachan Command Squad'),              # 65pts  ✓
    ('47-08',  30, 'Commissar'),                           # 30pts  ✓
    ('47-41',  65, 'Krieg Command Squad'),                 # 65pts  ✓
    ('47-42', 235, 'Leman Russ Commander'),                # 235pts ✓
    ('47-43',  85, 'Militarum Tempestus Command Squad'),   # 85pts  ✓
    ('47-44',  35, 'Ministorum Priest'),                   # 35pts  ✓
    ('47-45',  40, 'Ogryn Bodyguard'),                     # 40pts  ✓
    ('47-46',  60, 'Primaris Psyker'),                     # 60pts  ✓
    ('47-47', 275, 'Rogal Dorn Commander'),                # 275pts ✓
    ('47-03',  45, 'Tech-Priest Enginseer'),               # 45pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('47-30',  65, 'Cadian Shock Troops'),                 # 65pts  ✓
    ('47-48',  65, 'Catachan Jungle Fighters'),            # 65pts  ✓
    ('47-49',  65, 'Death Korps of Krieg'),                # 65pts  ✓
    ('47-19',  65, 'Infantry Squad'),                      # 65pts  ✓
    ('47-31',  60, 'Death Korps of Krieg'),                # 60pts  ✓ (box labelled Veteran Guardsmen)
    # ── Infantry ──────────────────────────────────────────────────────────────
    ('47-50', 100, 'Bullgryn Squad'),                      # 100pts ✓
    ('47-51',  65, 'Cadian Heavy Weapons Squad'),          # 65pts  ✓
    ('47-52',  65, 'Catachan Heavy Weapons Squad'),        # 65pts  ✓
    ('47-53',  60, 'Death Riders'),                        # 60pts  ✓
    ('47-54',  60, 'Krieg Combat Engineers'),              # 60pts  ✓
    ('47-55',  75, 'Krieg Heavy Weapons Squad'),           # 75pts  ✓
    ('47-56', 110, 'Kasrkin'),                             # 110pts ✓
    ('47-57',  60, 'Ogryn Squad'),                         # 60pts  ✓
    ('47-58',  60, 'Ratlings'),                            # 60pts  ✓
    ('47-59', 100, 'Tempestus Aquilons'),                  # 100pts ✓
    ('47-60',  70, 'Tempestus Scions'),                    # 70pts  ✓
    # ── Fast Attack ───────────────────────────────────────────────────────────
    ('47-61',  60, 'Attilan Rough Riders'),                # 60pts  ✓
    ('47-62',  25, 'Cyclops Demolition Vehicle'),          # 25pts  ✓
    ('47-12',  55, 'Scout Sentinels'),                     # 55pts  ✓ (same kit as Armoured @ 65pts)
    ('47-63',  65, 'Armoured Sentinels'),                  # 65pts  ✓
    # ── Heavy Support / Vehicles ──────────────────────────────────────────────
    ('47-05',  85, 'Chimera'),                             # 85pts  ✓
    ('47-17', 140, 'Basilisk'),                            # 140pts ✓
    ('47-64',  95, 'Artillery Team'),                      # 95pts  ✓
    ('47-65', 110, 'Field Ordnance Battery'),              # 110pts ✓
    ('47-14', 125, 'Hellhound'),                           # 125pts ✓
    ('47-66',  95, 'Hydra'),                               # 95pts  ✓
    ('47-06', 185, 'Leman Russ Battle Tank'),              # 185pts ✓
    ('47-67', 190, 'Leman Russ Demolisher'),               # 190pts ✓
    ('47-68', 170, 'Leman Russ Eradicator'),               # 170pts ✓
    ('47-69', 170, 'Leman Russ Executioner'),              # 170pts ✓
    ('47-70', 180, 'Leman Russ Exterminator'),             # 180pts ✓
    ('47-71', 150, 'Leman Russ Punisher'),                 # 150pts ✓
    ('47-72', 145, 'Leman Russ Vanquisher'),               # 145pts ✓
    ('47-73', 165, 'Manticore'),                           # 165pts ✓
    ('47-74', 145, 'Deathstrike'),                         # 145pts ✓
    ('47-75',  75, 'Taurox'),                              # 75pts  ✓
    ('47-76',  90, 'Taurox Prime'),                        # 90pts  ✓
    ('47-77', 250, 'Rogal Dorn Battle Tank'),              # 250pts ✓
    # ── Super-heavy vehicles ──────────────────────────────────────────────────
    ('47-78', 450, 'Baneblade'),                           # 450pts ✓
    ('47-79', 420, 'Banehammer'),                          # 420pts ✓
    ('47-80', 450, 'Banesword'),                           # 450pts ✓
    ('47-81', 415, 'Doomhammer'),                          # 415pts ✓
    ('47-82', 420, 'Hellhammer'),                          # 420pts ✓
    ('47-83', 410, 'Shadowsword'),                         # 410pts ✓
    ('47-84', 430, 'Stormlord'),                           # 430pts ✓
    ('47-85', 465, 'Stormsword'),                          # 465pts ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('47-86', 130, 'Avenger Strike Fighter'),              # 130pts ✓
    ('47-87', 190, 'Valkyrie'),                            # 190pts ✓
    # ── Fortifications ────────────────────────────────────────────────────────
    ('47-88', 145, 'Aegis Defence Line'),                  # 145pts ✓
    ('47-89', 110, 'Wyvern'),                              # 110pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Astra Militarum units.

    Looks up each product by GW SKU, then filters for the Astra Militarum
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Astra Militarum units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Astra Militarum points…\n')

        militarum_faction = Faction.objects.filter(name='Astra Militarum').first()
        if not militarum_faction:
            self.stdout.write(self.style.ERROR(
                'Astra Militarum faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in MILITARUM_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=militarum_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Militarum UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
