"""
Management command: seed_orks_points

Sets the points_cost on UnitType records for all Orks units,
using official 10th Edition points values sourced from New Recruit.

Usage:
    python manage.py seed_orks_points

The command is fully idempotent — safe to re-run. It looks up each product by
its Games Workshop SKU (gw_sku), then filters for the Orks UnitType
specifically and updates only that row's points_cost.

Notes:
- Run AFTER populate_products and populate_units.
- Do NOT add to the Procfile yet.
- Line-by-line verified against the New Recruit Orks 10th Edition list.
- SKUs not yet in the DB skip gracefully — add products later and re-run.
- Currently seeded SKUs in DB:
    50-02 (Warboss in Mega Armour), 50-05 (Warboss), 50-09 (Nobz),
    50-10 (Boyz), 50-11 (Trukk), 50-12 (Meganobz), 50-14 (Lootas),
    50-15 (Killa Kans), 50-16 (Deff Dread), 50-20 (Flash Gitz),
    50-22 (Battlewagon)
- Kit collision — 50-15 (Killa Kans): 3 Killa Kans at 125pts. Seeded at 125pts.
- Kit collision — 50-12 (Meganobz): builds Meganobz (65pts per 2) and
  could serve as Grukk Face-Rippa base. Seeded at 65pts.
- 71-18 (Combat Patrol) is a bundle — no standalone UnitType entry.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

# ---------------------------------------------------------------------------
# Points data: (gw_sku, points_cost, display_name_for_logging)
#
# Sourced from New Recruit — Orks 10th Edition list.
# Verified line-by-line against the full New Recruit army list.
# ---------------------------------------------------------------------------
ORKS_POINTS = [
    # ── Named characters ──────────────────────────────────────────────────────
    ('50-30', 235, 'Ghazghkull Thraka'),               # 235pts ✓ (includes Makari)
    ('50-31',  75, 'Boss Snikrot'),                    # 75pts  ✓
    ('50-32', 145, 'Mozrog Skragbad'),                 # 145pts ✓
    ('50-33',  90, 'Zodgrod Wortsnagga'),              # 90pts  ✓
    # ── Generic characters ────────────────────────────────────────────────────
    ('50-05',  75, 'Warboss'),                         # 75pts  ✓
    ('50-02',  80, 'Warboss in Mega Armour'),          # 80pts  ✓
    ('50-34',  80, 'Beastboss'),                       # 80pts  ✓
    ('50-35', 110, 'Beastboss on Squigosaur'),         # 110pts ✓
    ('50-36',  70, 'Big Mek'),                         # 70pts  ✓
    ('50-37',  90, 'Big Mek in Mega Armour'),          # 90pts  ✓
    ('50-38',  80, 'Big Mek with Shokk Attack Gun'),   # 80pts  ✓
    ('50-39',  45, 'Mek'),                             # 45pts  ✓
    ('50-40',  70, 'Painboss'),                        # 70pts  ✓
    ('50-41',  80, 'Painboy'),                         # 80pts  ✓
    ('50-42',  65, 'Weirdboy'),                        # 65pts  ✓
    ('50-43',  60, 'Wurrboy'),                         # 60pts  ✓
    ('50-44',  80, 'Deffkilla Wartrike'),              # 80pts  ✓
    # ── Battleline ────────────────────────────────────────────────────────────
    ('50-10',  80, 'Boyz'),                            # 80pts  ✓
    ('50-45',  95, 'Beast Snagga Boyz'),               # 95pts  ✓
    # ── Infantry / Core ───────────────────────────────────────────────────────
    ('50-09', 105, 'Nobz'),                            # 105pts ✓
    ('50-12',  65, 'Meganobz'),                        # 65pts  ✓
    ('50-46',  40, 'Gretchin'),                        # 40pts  ✓
    ('50-47',  65, 'Stormboyz'),                       # 65pts  ✓
    ('50-48', 120, 'Kommandos'),                       # 120pts ✓
    ('50-49',  60, 'Burna Boyz'),                      # 60pts  ✓
    ('50-14',  50, 'Lootas'),                          # 50pts  ✓
    ('50-20',  80, 'Flash Gitz'),                      # 80pts  ✓
    ('50-50', 140, 'Tankbustas'),                      # 140pts ✓
    ('50-51', 140, 'Breaka Boyz'),                     # 140pts ✓
    # ── Cavalry / Bikes ───────────────────────────────────────────────────────
    ('50-52', 150, 'Squighog Boyz'),                   # 150pts ✓
    ('50-53',  65, 'Warbikers'),                       # 65pts  ✓
    ('50-54',  80, 'Deffkoptas'),                      # 80pts  ✓
    # ── Vehicles ──────────────────────────────────────────────────────────────
    ('50-11',  70, 'Trukk'),                           # 70pts  ✓
    ('50-22', 160, 'Battlewagon'),                     # 160pts ✓
    ('50-55',  70, 'Boomdakka Snazzwagon'),            # 70pts  ✓
    ('50-56',  70, 'Kustom Boosta-blasta'),            # 70pts  ✓
    ('50-57',  95, 'Rukkatrukk Squigbuggy'),           # 95pts  ✓
    ('50-58',  70, 'Shokkjump Dragsta'),               # 70pts  ✓
    ('50-59',  75, 'Megatrakk Scrapjet'),              # 75pts  ✓
    ('50-60',  50, 'Mek Gunz'),                        # 50pts  ✓ (Smasha gun variant)
    # ── Walkers ───────────────────────────────────────────────────────────────
    ('50-16', 120, 'Deff Dread'),                      # 120pts ✓
    ('50-15', 125, 'Killa Kans'),                      # 125pts ✓ (3 models)
    ('50-61', 265, 'Gorkanaut'),                       # 265pts ✓
    ('50-62', 280, 'Morkanaut'),                       # 280pts ✓
    # ── Beast / Cavalry vehicles ──────────────────────────────────────────────
    ('50-63', 135, 'Hunta Rig'),                       # 135pts ✓
    ('50-64', 155, 'Kill Rig'),                        # 155pts ✓
    # ── Aircraft ──────────────────────────────────────────────────────────────
    ('50-65', 135, 'Dakkajet'),                        # 135pts ✓
    ('50-66', 115, 'Blitza-bommer'),                   # 115pts ✓
    ('50-67', 125, 'Burna-bommer'),                    # 125pts ✓
    ('50-68', 175, 'Wazbom Blastajet'),                # 175pts ✓
    # ── Super-heavies ─────────────────────────────────────────────────────────
    ('50-69', 440, 'Gargantuan Squiggoth'),            # 440pts ✓
    ('50-70', 800, 'Stompa'),                          # 800pts ✓
]


class Command(BaseCommand):
    """
    Seed official 10th Edition points costs for Orks units.

    Looks up each product by GW SKU, then filters for the Orks
    UnitType specifically and updates only that row's points_cost.
    SKUs not found in the DB are skipped with a warning — add the products
    later and re-run. Idempotent — safe to re-run at any time.
    """

    help = 'Seed 10th Edition points values for Orks units.'

    def handle(self, *args, **options):
        """Entry point."""
        self.stdout.write('Seeding Orks points…\n')

        orks_faction = Faction.objects.filter(name='Orks').first()
        if not orks_faction:
            self.stdout.write(self.style.ERROR(
                'Orks faction not found. Run populate_products first.'
            ))
            return

        updated_count = 0
        skipped_count = 0

        for gw_sku, points, label in ORKS_POINTS:
            product = Product.objects.filter(gw_sku=gw_sku).first()

            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip]    {label} (SKU {gw_sku} not found in DB)')
                )
                skipped_count += 1
                continue

            updated = UnitType.objects.filter(
                product=product,
                faction=orks_faction,
            ).update(points_cost=points)

            if updated:
                self.stdout.write(f'  [updated] {label} > {points} pts')
                updated_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [no unit] {label} (SKU {gw_sku}) — Orks UnitType not found. '
                        f'Run populate_units first.'
                    )
                )
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated: {updated_count}  |  Skipped: {skipped_count}'
        ))
