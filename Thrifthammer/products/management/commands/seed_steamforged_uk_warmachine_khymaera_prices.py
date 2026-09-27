"""
Seed Steamforged Games UK prices for Warmachine: Khymaera.

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

Source: https://warmachine.gg/collections/khymaera-shadowflame-shard (27
listings, 2 pages) -- unlike Cygnar/Dusk/Khador, Khymaera is not split
across sub-collections. GB/GBP localization confirmed selected. Each match
verified by pairing product title text with its href directly via JS (not
list position).

All 26 of 26 catalog SKUs matched -- full coverage, no gaps. The 27th page
listing, "Shadows & Scum" (sold out, GBP 104.99), is correctly excluded --
it's WMH-078, primary-faction Southern Kriels with a secondary Khymaera
tag (per project_warmachine_faction_rollout memory), so it belongs to the
Southern Kriels seed command, not here.

**Correction to an earlier Firestorm audit finding**: WMH-323 "Khymaera
Shadowflame Shard Command Starter (HIPS)" lives at Steamforged's own
.../warmachine-khymaera-shard-nocturnes-command-starter-hips slug, and its
official page confirms the exact same contents (Vallyx Fate's Eclipse
warlock, Aklyss, Pythia, Regulus, Shades) as the "Khymaera Shard Nocturnes
Command Starter" listing found on Firestorm Games during the earlier
Firestorm Khymaera audit -- which was incorrectly excluded at the time on
the assumption its component characters didn't map to any catalog SKU.
That was the wrong test: "Shard Nocturnes" is simply this Command
Starter's in-universe flavor name, the same pattern later confirmed for
Dusk's "Ghosts of Ios" naming Dusk House Kallyss Command Starter. Firestorm
had a real, correct match (GBP 67.49, 1 in stock) that was wrongly turned
away. Flagged for the user to decide whether to backfill that Firestorm
price onto WMH-323; not done here.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-028', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-shadow-seraph', True),
    ('WMH-323', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-khymaera-shard-nocturnes-command-starter-hips', True),
    ('WMH-229', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-khymaera-shadowflame-shard-incarnates-cadre', True),
    ('WMH-228', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-khymaera-shadowflame-shard-battlegroup-box', True),
    ('WMH-226', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-khymaera-shadowflame-shard-core-expansion', True),
    ('WMH-227', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-khymaera-shadowflame-shard-auxiliary-expansion', True),
    ('WMH-023', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-shadowflame-shard-gargantuan', True),
    ('WMH-303', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-lylyth-the-raven-vengeance', True),
    ('WMH-232', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-khymaera-shadowflame-shard-wyvern', True),
    ('WMH-231', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-khymaera-shadowflame-shard-vypex', True),
    ('WMH-293', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-incarnate-conjuror-variant', True),
    ('WMH-257', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-hydrix-variant', True),
    ('WMH-238', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-quick-fang-master', True),
    ('WMH-239', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-shadowmancer-scion', True),
    ('WMH-243', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-quick-fang-wind-strikers', True),
    ('WMH-230', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-khymaera-shadowflame-shard-hydrix', True),
    ('WMH-242', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-quick-fang-stalkers', True),
    ('WMH-241', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-spinner', True),
    ('WMH-244', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-talon-death-dealers', True),
    ('WMH-248', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-talon-lashers', True),
    ('WMH-240', Decimal('29.99'), 'https://warmachine.gg/products/warmachine-wraithwing-paragon', True),
    ('WMH-249', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-wyrmspine-cinderbacks', True),
    ('WMH-245', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-wyrmspine-shadowmancers', True),
    ('WMH-269', Decimal('29.99'), 'https://warmachine.gg/products/warmachine-incarnate-conjuror', True),
    ('WMH-270', Decimal('49.99'), 'https://warmachine.gg/products/warmachine-incarnate-knights', True),
    ('WMH-284', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-drakyon', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Khymaera. Idempotent.'

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
                f'Seeded {seeded} Khymaera Steamforged UK prices. Skipped: {skipped}.'
            )
        )
