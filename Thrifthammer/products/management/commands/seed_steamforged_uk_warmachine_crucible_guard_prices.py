"""
Seed Steamforged Games UK prices for Warmachine: Crucible Guard.

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
2026-09-26, mirroring the Mantic UK precedent for Halo: Flashpoint. So
(create-only, same guard as every other UK retailer) this command sets
msrp_gbp from the Steamforged UK price the first time it seeds a product.
It never overwrites an already-set msrp_gbp.

Source: https://warmachine.gg/collections/crucible-guard, GB/GBP
localization selected via the site's own Shopify Markets localization form
(POST to /localization with country_code=GB) -- confirmed this is a
genuine regional price list, not a currency-converted estimate. All 22 of
22 catalog SKUs for this faction matched by exact product name, verified
2026-09-26. (A 23rd item on the page, "Gorman di Wolfe, Revolutionary
Agent", is tagged Mercenary on Steamforged's own site and correctly has no
Crucible Guard SKU in our catalog -- not included here.)

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-103', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-captain-eira-mackay', True),
    ('WMH-104', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-core-expansion', True),
    ('WMH-108', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-defenses', True),
    ('WMH-109', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-vulcan', True),
    ('WMH-110', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-auxiliary-expansion', True),
    ('WMH-124', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-toro-suppressor-vindicator-warjack', True),
    ('WMH-125', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-liberator-retaliator-vanguard-warjack', True),
    ('WMH-126', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-infantry-and-officer-standard-bearer', True),
    ('WMH-127', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-rocketman-stinger', True),
    ('WMH-128', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-mechaniks', True),
    ('WMH-129', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-rocketmen-gunners', True),
    ('WMH-130', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-rocketmen-rocketman-captain', True),
    ('WMH-131', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-rocketman-ace', True),
    ('WMH-132', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-combat-alchemists', True),
    ('WMH-133', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-dragons-breath-rocket', True),
    ('WMH-134', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-assault-troopers', True),
    ('WMH-135', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-storm-troopers', True),
    ('WMH-136', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-containment-operatives', True),
    ('WMH-137', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-failed-experiments', True),
    ('WMH-336', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-battlegroup-box', True),
    ('WMH-337', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-command-starter', True),
    ('WMH-346', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-crucible-guard-athanor-locke', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Crucible Guard. Idempotent.'

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
                f'Seeded {seeded} Crucible Guard Steamforged UK prices. Skipped: {skipped}.'
            )
        )
