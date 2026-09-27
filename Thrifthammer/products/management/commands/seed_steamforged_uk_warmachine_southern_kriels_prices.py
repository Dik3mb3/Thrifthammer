"""
Seed Steamforged Games UK prices for Warmachine: Southern Kriels.

Creates the `steamforged-games-uk` Retailer if it does not exist -- distinct
from the existing US-only `steamforged-games` retailer (is_uk=False).

Warmachine is published by Steamforged Games, not Games Workshop -- there is
no games-workshop-uk listing for this category at all, so product_detail's
gw_ref_price (the "MSRP" reference line / discount badge) falls through to
product.msrp_gbp, which is None for every WMH-* product unless set here.
Steamforged Games UK (warmachine.gg with GB/GBP localization selected) is
this category's confirmed MSRP source (established with Crucible Guard,
applies to the whole Warmachine category). So (create-only, same guard as
every other UK retailer) this command sets msrp_gbp from the Steamforged UK
price the first time it seeds a product. It never overwrites an
already-set msrp_gbp.

Sources (two sub-army collections, this faction has none listed as a single
"southern-kriels" collection -- that slug 404s):
- https://warmachine.gg/collections/southern-kriels-kithguard (28 listings,
  2 pages)
- https://warmachine.gg/collections/southern-kriels-brinebloods (34
  listings, 2 pages)
GB/GBP localization confirmed selected. Each match verified by pairing
product title text with its href directly via JS (not list position).
Several units (trolls, Fire Tongue Warriors Command Cadre, etc.) are
cross-listed on both sub-collection pages -- verified as the same catalog
SKU/price in each case, priced once here.

All 54 of 54 catalog SKUs matched -- full coverage, no exclusions needed.

WMH-322 "Southern Kriels Brinebloods Command Starter (HIPS)" caught via a
misleading legacy URL slug (/products/warmachine-foulbloods-armada-command-
starter-hips -- an old in-universe/working name, "Foulbloods Armada",
predating the "Brinebloods" rename) -- confirmed correct only because of
the paired title+href JS extraction, never assumed from slug text or list
position.

WMH-078 "Shadows & Scum" is marked "Sold out" on Steamforged's site --
recorded with in_stock=False (its price/URL are still valid and captured).

One item on the Kithguard collection has NO matching catalog SKU and was
excluded, not a gap in our seed logic: "Dozer & Smigg" (PRE-ORDER, £74.99,
brand-new SKU with no catalog entry yet) -- flagged for the user, not
added.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-002', Decimal('174.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-fortress-king', True),
    ('WMH-010', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-command-starter', True),
    ('WMH-021', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-journeyman-ramhead', True),
    ('WMH-029', Decimal('84.99'), 'https://warmachine.gg/products/warmachine-ol-scuttlebutt', True),
    ('WMH-042', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-battlegroup-box', True),
    ('WMH-044', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-infantry', True),
    ('WMH-045', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-sergeant', True),
    ('WMH-046', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-steelbacks', True),
    ('WMH-047', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-sidewinder', True),
    ('WMH-064', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-quartermaster', True),
    ('WMH-065', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-bosun', True),
    ('WMH-066', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-tapper', True),
    ('WMH-067', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-pyg-boarding-party', True),
    ('WMH-068', Decimal('99.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-pyg-battle-brig', True),
    ('WMH-069', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-braghen-ragemonger', True),
    ('WMH-070', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-marauder-crew-a', True),
    ('WMH-077', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-vorogger-variant', True),
    ('WMH-078', Decimal('104.99'), 'https://warmachine.gg/products/warmachine-shadows-and-scum', False),
    ('WMH-092', Decimal('79.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-general-gunnbjorn', True),
    ('WMH-098', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-kithguard-defenses', True),
    ('WMH-120', Decimal('159.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-core-expansion', True),
    ('WMH-121', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-mortar-team', True),
    ('WMH-122', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-medics', True),
    ('WMH-123', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-tunnel-rats', True),
    ('WMH-138', Decimal('149.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-auxiliary-expansion', True),
    ('WMH-139', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-throat-cutters', True),
    ('WMH-140', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-hailer', True),
    ('WMH-141', Decimal('29.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-guard-post', True),
    ('WMH-212', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-core-expansion', True),
    ('WMH-213', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-auxiliary-expansion', True),
    ('WMH-214', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-battlegroup-box', True),
    ('WMH-215', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-deepborn-dire-troll', True),
    ('WMH-216', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-reef-troll', True),
    ('WMH-217', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-pyg-shockers', True),
    ('WMH-218', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-booty-boss', True),
    ('WMH-219', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-pyg-dirge', True),
    ('WMH-220', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-pyg-dirge-variant', True),
    ('WMH-221', Decimal('12.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-coxswain', True),
    ('WMH-222', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-surgeon', True),
    ('WMH-223', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-pyg-galley-crew', True),
    ('WMH-224', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-pyg-cannon-crew', True),
    ('WMH-225', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-brineblood-marauders-maruader-crew-b', True),
    ('WMH-252', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-abyssal-king', True),
    ('WMH-258', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-deepborn-dire-troll-variant', True),
    ('WMH-277', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-vorogger', True),
    ('WMH-278', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-fire-guardian', True),
    ('WMH-279', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-fugue-walker', True),
    ('WMH-280', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-fire-spitters', True),
    ('WMH-281', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-spirit-shamans', True),
    ('WMH-283', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-fire-guardians-variant', True),
    ('WMH-287', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-fire-tongue-warriors-command-cadre', True),
    ('WMH-322', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-foulbloods-armada-command-starter-hips', True),
    ('WMH-347', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-mistborn-dire-troll', True),
    ('WMH-348', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-southern-kriels-kithguard-jungle-troll', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Southern Kriels. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_STEAMFORGED_UK_SLUG,
            defaults={
                'name': 'Steamforged Games UK',
                'website': 'https://warmachine.gg',
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
                f'Seeded {seeded} Southern Kriels Steamforged UK prices. Skipped: {skipped}.'
            )
        )
