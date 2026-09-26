"""
Seed Firestorm Games UK prices for Halo: Flashpoint.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; Mantic Games UK already holds that
role for this category (see seed_mantic_uk_halo_flashpoint_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/halo-flashpoint
Every one of the 32 rows below was opened and verified individually
(title, price, stock) on 2026-09-26, not scraped in bulk.

32 of 42 catalog SKUs matched. Not matched, by design or confirmed gap:
- 8 "New Player Bundle"/"Faction Bundle" SKUs -- Firestorm doesn't carry
  these standalone, same as Mantic's own site.
- 4 SKUs not in our catalog at all (Zeta Halo/New Mombasa/UNSC Firebase/
  Banished Garrison deluxe gaming mats) -- user confirmed 2026-09-25:
  ignore, do not add.
- HALO-012 (1 Player Token Set), HALO-023 (Paint Set - including Master
  Chief) -- genuine gaps, not listed on Firestorm at all.
- 3 real Mantic products found on Firestorm with no DB counterpart --
  confirmed distinct via their own Mantic product codes, not duplicates
  of anything we carry: "War Games Expansion Pack" (MGHA110), "Banished
  Garrison Terrain" (MGHAB103, distinct from our Banished Garrison
  Scenery Set / MGHAB104), "Banished Dice Booster" (MGHAB102, distinct
  from our generic Dice Booster / MGHA104). Flagged for the user as
  candidates for a future catalog addition -- out of scope here.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('HALO-001', Decimal('17.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---atriox-warmaster-of-the-banished-?aff=6a4ab07d1c6f9', False),
    ('HALO-002', Decimal('18.75'), 'https://www.firestormgames.co.uk/halo:-flashpoint---banished-garrison-scenery-set?aff=6a4ab07d1c6f9', True),
    ('HALO-003', Decimal('25.50'), 'https://www.firestormgames.co.uk/halo:-flashpoint---jiralhanae-pack?aff=6a4ab07d1c6f9', True),
    ('HALO-004', Decimal('21.25'), 'https://www.firestormgames.co.uk/halo:-flashpoint---sangheili-mercenaries?aff=6a4ab07d1c6f9', True),
    ('HALO-006', Decimal('34.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---defiance-expansion-pack?aff=6a4ab07d1c6f9', True),
    ('HALO-007', Decimal('36.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---desperate-measures-expansion-pack?aff=6a4ab07d1c6f9', True),
    ('HALO-008', Decimal('85.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---feet-first-into-hell?aff=6a4ab07d1c6f9', True),
    ('HALO-009', Decimal('25.50'), 'https://www.firestormgames.co.uk/halo:-flashpoint---field-outpost-deluxe-gaming-mat?aff=6a4ab07d1c6f9', False),
    ('HALO-010', Decimal('21.25'), 'https://www.firestormgames.co.uk/halo:-flashpoint---fireteam-cerberus?aff=6a4ab07d1c6f9', False),
    ('HALO-011', Decimal('21.25'), 'https://www.firestormgames.co.uk/halo:-flashpoint---fireteam-hydra?aff=6a4ab07d1c6f9', True),
    ('HALO-014', Decimal('45.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---banished-reinforcements?aff=6a4ab07d1c6f9', True),
    ('HALO-015', Decimal('53.10'), 'https://www.firestormgames.co.uk/halo:-flashpoint---spartan-killers?aff=6a4ab07d1c6f9', True),
    ('HALO-016', Decimal('22.50'), 'https://www.firestormgames.co.uk/halo:-flashpoint---buck-and-dare?aff=6a4ab07d1c6f9', True),
    ('HALO-017', Decimal('68.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---deluxe-buildable-3d-terrain-set?aff=6a4ab07d1c6f9', False),
    ('HALO-018', Decimal('12.75'), 'https://www.firestormgames.co.uk/halo:-flashpoint---dice-booster?aff=6a4ab07d1c6f9', True),
    ('HALO-019', Decimal('22.50'), 'https://www.firestormgames.co.uk/halo:-flashpoint---fireteam-grizzly?aff=6a4ab07d1c6f9', True),
    ('HALO-020', Decimal('40.50'), 'https://www.firestormgames.co.uk/halo:-flashpoint---fireteam-phoenix?aff=6a4ab07d1c6f9', True),
    ('HALO-021', Decimal('40.50'), 'https://www.firestormgames.co.uk/halo:-flashpoint---fireteam-wolf?aff=6a4ab07d1c6f9', True),
    ('HALO-022', Decimal('17.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---force-organiser-pack?aff=6a4ab07d1c6f9', False),
    ('HALO-024', Decimal('18.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---game-rulebook-pack?aff=6a4ab07d1c6f9', False),
    ('HALO-025', Decimal('90.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---spartan-edition-starter-set-?aff=6a4ab07d1c6f9', True),
    ('HALO-026', Decimal('9.00'), 'https://www.firestormgames.co.uk/halo-flashpoint-unit-card-update-pack?aff=6a4ab07d1c6f9', False),
    ('HALO-028', Decimal('45.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---unsc-marines-?aff=6a4ab07d1c6f9', True),
    ('HALO-030', Decimal('24.75'), 'https://www.firestormgames.co.uk/halo:-flashpoint---new-mombasa-terrain-set?aff=6a4ab07d1c6f9', True),
    ('HALO-031', Decimal('62.10'), 'https://www.firestormgames.co.uk/halo:-flashpoint---noble-team?aff=6a4ab07d1c6f9', False),
    ('HALO-033', Decimal('22.50'), 'https://www.firestormgames.co.uk/halo:-flashpoint---odst-scenery-set?aff=6a4ab07d1c6f9', True),
    ('HALO-035', Decimal('34.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---outpost-buildable-terrain-set?aff=6a4ab07d1c6f9', True),
    ('HALO-036', Decimal('44.10'), 'https://www.firestormgames.co.uk/halo:-flashpoint---reach-deluxe-gaming-mat?aff=6a4ab07d1c6f9', True),
    ('HALO-037', Decimal('85.00'), 'https://www.firestormgames.co.uk/halo:-flashpoint---rise-of-the-banished?aff=6a4ab07d1c6f9', True),
    ('HALO-040', Decimal('11.25'), 'https://www.firestormgames.co.uk/halo:-flashpoint---the-master-chief-humanitys-greatest-hero?aff=6a4ab07d1c6f9', True),
    ('HALO-041', Decimal('21.25'), 'https://www.firestormgames.co.uk/halo:-flashpoint---unsc-base-terrain-set?aff=6a4ab07d1c6f9', False),
    ('HALO-042', Decimal('21.25'), 'https://www.firestormgames.co.uk/halo:-flashpoint---unsc-scenery-set?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Halo: Flashpoint. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': 'https://www.firestormgames.co.uk/?aff=6a4ab07d1c6f9',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, gbp_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

            cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'GBP'}
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults=cp_defaults,
                create_defaults={**cp_defaults, 'price': gbp_price},
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Halo: Flashpoint Firestorm Games prices. Skipped: {skipped}.'
            )
        )
