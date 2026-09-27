"""
Seed Steamforged Games UK prices for Warmachine: Cryx.

Creates the `steamforged-games-uk` Retailer if it does not exist -- distinct
from the existing US-only `steamforged-games` retailer (is_uk=False), same
split as mantic-games / mantic-games-uk for Halo: Flashpoint. Never conflate
the two under one retailer record.

Warmachine is published by Steamforged Games, not Games Workshop -- there is
no games-workshop-uk listing for this category at all, so product_detail's
gw_ref_price (the "MSRP" reference line / discount badge) falls through to
product.msrp_gbp, which is None for every WMH-* product unless set here.
Steamforged Games UK (warmachine.gg with GB/GBP localization selected) is
this category's own publisher-official UK price -- confirmed with the user
2026-09-25 for Crucible Guard, applies to the whole Warmachine category (not
re-confirmed per faction). So (create-only, same guard as every other UK
retailer) this command sets msrp_gbp from the Steamforged UK price the
first time it seeds a product. It never overwrites an already-set msrp_gbp.

Source: https://warmachine.gg/collections/cryx-necrofactorium, GB/GBP
localization confirmed selected (top-right shows "GB"). All 23 of 23
catalog SKUs for this faction matched, verified 2026-09-27.

**IMPORTANT -- Steamforged is refreshing this faction's box lineup.** 6 of
the 23 SKUs (WMH-004, WMH-233, WMH-235, WMH-254, WMH-256, WMH-259) are
tagged "LEAVING SOON" on warmachine.gg -- still genuinely on sale at their
real regular price right now (which is what's recorded here), but
Steamforged is winding them down. A separate, brand-new "PRE-ORDER"/"NEW"
wave of 10 items was found on the same collection page that does NOT match
any existing catalog SKU: "Cryx Necrofactorium Command Set - Boneyard
Keeper" (GBP 74.99), three new Army Boxes -- "Legions of the Dead" (GBP
149.99), "Lord of Damnation" (GBP 149.99), "Wraithbinder's Host" (GBP
119.99) -- a restructured "Heavy Warjack - Malefactor" (GBP 39.99) and
"Light Warjack - Raptor" (GBP 29.99) plus a new "Light Warjack Variant -
Raptor" (GBP 29.99) and Options packs for both, and a genuinely new
"Mechanithrall Swarm C" (GBP 30.99). NOT added here -- flagged for the user,
same as the Storm Forge Cadre / Ghosts of Ios Cadre / Foulblood's Armada
gaps found in earlier factions. Revisit once the user decides whether/how
to catalog the new wave (likely once it moves from pre-order to release).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-004', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-cryx-necrofactorium-command-starter', True),
    ('WMH-006', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-hive-mind-cadre', True),
    ('WMH-025', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-mechanithrall-swarm-warden', True),
    ('WMH-082', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-cryx-defenses-set', True),
    ('WMH-090', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-deathjack', True),
    ('WMH-233', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-cryx-necrofactorium-auxiliary-expansion', True),
    ('WMH-235', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-cryx-necrofactorium-battlegroup-box', True),
    ('WMH-250', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-cryx-necrofactorium-hellraker-colossal', True),
    ('WMH-254', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-cryx-necrofactorium-core-expansion', True),
    ('WMH-256', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-malefactor-heavy-warjack', True),
    ('WMH-259', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-raptor-light-warjack', True),
    ('WMH-260', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-cryx-necroharvester-corpse-crawlers', True),
    ('WMH-294', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-machine-wraith-dominator', True),
    ('WMH-295', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-mechanithrall-swarm-a', True),
    ('WMH-296', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-mechanithrall-swarm-b', True),
    ('WMH-297', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-necrosurgeon-initiates', True),
    ('WMH-298', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-skarlock-lieutenant', True),
    ('WMH-299', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-mechanithrall-brutes', True),
    ('WMH-300', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-sludge-thralls', True),
    ('WMH-301', Decimal('44.99'), 'https://warmachine.gg/products/warmachine-night-terrors', True),
    ('WMH-302', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-iron-lich-commander', True),
    ('WMH-310', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-mortenebra-perfected', True),
    ('WMH-314', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-criterions-unit', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Cryx. Idempotent.'

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

            # Create-only: Steamforged UK is this category's own publisher price,
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
                f'Seeded {seeded} Cryx Steamforged UK prices. Skipped: {skipped}.'
            )
        )
