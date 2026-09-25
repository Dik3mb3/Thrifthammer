"""
Seed Mantic Games UK prices for Halo: Flashpoint.

Creates the `mantic-games-uk` Retailer if it does not exist, and
creates/updates a CurrentPrice record pointing at the Mantic Games
product page. Source: user-supplied "Halo Flashpoint UK - Mantic.xlsx"
export of manticgames.com, cross-referenced against the existing
HALO-* catalog by Mantic SKU (2026-09-25).

Halo: Flashpoint is published by Mantic Games, not Games Workshop.
There is no games-workshop-uk listing for this category at all, so
product_detail's gw_ref_price (the "MSRP" reference line / discount
badge) falls through to product.msrp_gbp -- which is None for every
HALO-* product unless set here. Mantic UK is this category's own
publisher-official price, so (create-only, same guard as GW UK) this
command sets msrp_gbp from the Mantic price the first time it seeds a
product. It never overwrites an already-set msrp_gbp.

8 catalog SKUs (all "New Player Bundle" / "Faction Bundle" products)
have no matching row in the Mantic export and are intentionally
omitted -- Mantic doesn't sell them as standalone bundles.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MANTIC_UK_SLUG = 'mantic-games-uk'

# (gw_sku, gbp_price, mantic_url, in_stock)
_PRICES = [
    ('HALO-025', Decimal('100.00'), 'https://www.manticgames.com/halo-flashpoint/getting-started/spartan-edition-updated/', True),
    ('HALO-024', Decimal('20.00'), 'https://www.manticgames.com/halo-flashpoint/getting-started/game-rulebook-pack/', True),
    ('HALO-026', Decimal('10.00'), 'https://www.manticgames.com/halo-flashpoint/accessories-terrain/unit-card-update-pack-v15/', True),
    ('HALO-023', Decimal('37.50'), 'https://www.manticgames.com/halo-flashpoint/paint-set/', True),
    ('HALO-008', Decimal('100.00'), 'https://www.manticgames.com/halo-flashpoint/unsc/feet-first-into-hell/', True),
    ('HALO-031', Decimal('69.00'), 'https://www.manticgames.com/halo-flashpoint/unsc/noble-team/', False),
    ('HALO-028', Decimal('50.00'), 'https://www.manticgames.com/halo-flashpoint/unsc/marines/', True),
    ('HALO-019', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/unsc/fireteam-grizzly/', True),
    ('HALO-007', Decimal('40.00'), 'https://www.manticgames.com/halo-flashpoint/unsc/desperate-measures-expansion/', True),
    ('HALO-016', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/unsc/gunnery-sergeant-buck-captain-dare/', True),
    ('HALO-040', Decimal('12.50'), 'https://www.manticgames.com/halo-flashpoint/master-chief-humanitys-greatest-weapon/', True),
    ('HALO-010', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/fireteam-cerberus-spartan-pack/', True),
    ('HALO-011', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/fireteam-hydra-spartans-pack/', True),
    ('HALO-021', Decimal('45.00'), 'https://www.manticgames.com/halo-flashpoint/unsc/fireteam-wolf/', True),
    ('HALO-020', Decimal('45.00'), 'https://www.manticgames.com/halo-flashpoint/fireteam-phoenix-show-special-spartans-pack/', True),
    ('HALO-042', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/unsc-plastic-scenery-set/', True),
    ('HALO-033', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/accessories-terrain/odst-scenery-set/', True),
    ('HALO-041', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/unsc-base-terrain-set/', True),
    ('HALO-030', Decimal('27.50'), 'https://www.manticgames.com/halo-flashpoint/accessories-terrain/new-mombasa-terrain-set/', True),
    ('HALO-036', Decimal('50.00'), 'https://www.manticgames.com/halo-flashpoint/accessories-terrain/reach-deluxe-gaming-mat/', True),
    ('HALO-009', Decimal('30.00'), 'https://www.manticgames.com/halo-flashpoint/field-outpost-deluxe-gaming-mat/', True),
    ('HALO-037', Decimal('100.00'), 'https://www.manticgames.com/halo-flashpoint/rise-of-the-banished-boxed-set/', True),
    ('HALO-015', Decimal('59.00'), 'https://www.manticgames.com/halo-flashpoint/banished/spartan-killers/', False),
    ('HALO-014', Decimal('50.00'), 'https://www.manticgames.com/halo-flashpoint/banished/reinforcements/', True),
    ('HALO-001', Decimal('20.00'), 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-banished/atriox-warmaster-of-the-banished-retail-version/', True),
    ('HALO-006', Decimal('40.00'), 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-banished/defiance/', True),
    ('HALO-003', Decimal('30.00'), 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-banished/jiralhanae-fireteam/', True),
    ('HALO-004', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-banished/sangheili-mercenaries/', True),
    ('HALO-002', Decimal('25.00'), 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-accessories-terrain/banished-garrison-scenery-set/', True),
    ('HALO-035', Decimal('40.00'), 'https://www.manticgames.com/halo-flashpoint/outpost-3d-plastic-terrain-set/', True),
    ('HALO-017', Decimal('80.00'), 'https://www.manticgames.com/halo-flashpoint/deluxe-3d-terrain-set/', True),
    ('HALO-022', Decimal('20.00'), 'https://www.manticgames.com/halo-flashpoint/force-organizer-tray-pack/', True),
    ('HALO-018', Decimal('15.00'), 'https://www.manticgames.com/halo-flashpoint/dice-booster/', True),
    ('HALO-012', Decimal('12.50'), 'https://www.manticgames.com/halo-flashpoint/token-set/', True),
]


class Command(BaseCommand):
    help = 'Seed Mantic Games UK prices and URLs for Halo: Flashpoint. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_MANTIC_UK_SLUG,
            defaults={
                'name': 'Mantic Games UK',
                'website': 'https://www.manticgames.com',
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

            # Create-only: Mantic UK is this category's own publisher price,
            # so it's an acceptable msrp_gbp source here -- but never reset
            # a value some future update already set.
            if product.msrp_gbp is None:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

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
                f'Seeded {seeded} Halo: Flashpoint Mantic UK prices. Skipped: {skipped}.'
            )
        )
