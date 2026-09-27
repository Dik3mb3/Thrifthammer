"""
Seed Steamforged Games UK prices for Warmachine: Cygnar.

Creates the `steamforged-games-uk` Retailer if it does not exist -- distinct
from the existing US-only `steamforged-games` retailer (is_uk=False), same
split as mantic-games / mantic-games-uk for Halo: Flashpoint.

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

Source: Cygnar is split across two Steamforged sub-collections --
https://warmachine.gg/collections/cygnar-gravediggers (23 products) and
https://warmachine.gg/collections/cygnar-storm-legion (30 products, 2
pages) -- mirroring our own catalog's "Gravediggers" / "Storm Legion"
naming split. GB/GBP localization confirmed selected.

All 49 of 49 catalog SKUs matched, each verified by pairing product title
text with its href directly via JS (NOT by list position -- two of
Steamforged's own URL slugs are stale/misleading: "Cygnar Storm Legion
Command Starter" lives at .../warmachine-cygnar-storm-forge-command-cadre
(a leftover slug from before a rename, verified by title text -- NOT the
still-uncatalogued "Storm Forge Cadre" gap product flagged during the
Firestorm Cygnar batch), and "Rangers Unit A" lives at
.../warmachine-cygnar-gravediggers-core-expansion-copy (a duplicated-slug
artifact). Position-based matching would have silently mismatched both.

3 products are cross-listed on both sub-collection pages at the same price
(Cygnar Hellslingers Command Cadre, Two Player Starter Set, and Gorman di
Wolfe) -- Gorman di Wolfe is WMH-015, a Mercenaries-faction SKU in our
catalog, not Cygnar, so it's excluded here (will be picked up when the
Mercenaries faction gets its Steamforged UK pass).

WMH-261 Two Player Starter Set is sold out on Steamforged's site --
in_stock=False, real price kept per the sold-out-listing convention.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-030', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-bandit', True),
    ('WMH-071', Decimal('64.99'), 'https://warmachine.gg/products/warmachine-cygnar-hellslingers-command-cadre', True),
    ('WMH-074', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-command-starter', True),
    ('WMH-236', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-battlegroup-box', True),
    ('WMH-255', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-core-expansion', True),
    ('WMH-234', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-auxiliary-expansion', True),
    ('WMH-084', Decimal('59.99'), 'https://warmachine.gg/products/warmachine-heavy-field-gun', True),
    ('WMH-324', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-assault-strider', True),
    ('WMH-261', Decimal('79.99'), 'https://warmachine.gg/products/warmachine-khador-vs-cygnar-starter', False),
    ('WMH-081', Decimal('44.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-armored-airdrop', True),
    ('WMH-311', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-commando-unit', True),
    ('WMH-312', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-commando-officer', True),
    ('WMH-308', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-core-expansion-copy', True),
    ('WMH-309', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-rangers-unit-b', True),
    ('WMH-038', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-heavy-machinegun-crew', True),
    ('WMH-080', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-gunmages', True),
    ('WMH-079', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-trollkin-express-sniper', True),
    ('WMH-304', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-valiant-warjack', True),
    ('WMH-305', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-patriot-warjack', True),
    ('WMH-306', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-cygnar-gravediggers-airdrops', True),
    ('WMH-313', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-captain-connor-boom-boom-mccoy', True),
    ('WMH-083', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-defenses-set', True),
    ('WMH-286', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-forge-command-cadre', True),
    ('WMH-143', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-battlegroup-box', True),
    ('WMH-034', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-core-expanion', True),
    ('WMH-142', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-auxiliary-expansion', True),
    ('WMH-102', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-thunderhead-ii', True),
    ('WMH-073', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-maelstrom', True),
    ('WMH-291', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-borealis', True),
    ('WMH-152', Decimal('59.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-zephyr', True),
    ('WMH-144', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-stryker-heavy-warjack', True),
    ('WMH-049', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-courser-light-warjack', True),
    ('WMH-036', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-captain-raef-huxley', True),
    ('WMH-052', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-weather-station', True),
    ('WMH-050', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-tempest-assailers', True),
    ('WMH-035', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-sharpshooter', True),
    ('WMH-149', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-arcane-mechaniks', True),
    ('WMH-151', Decimal('49.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-storm-lance-legionnaires', True),
    ('WMH-148', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-tempest-thunderers', True),
    ('WMH-146', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-stormblade-legionnaires', True),
    ('WMH-267', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-storm-legion-legionnaire-standard-bearer', True),
    ('WMH-156', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-storm-vanes', True),
    ('WMH-155', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-storm-callers', True),
    ('WMH-150', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-stormthrower-legionnaires', True),
    ('WMH-147', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-stormguard-legionnaires', True),
    ('WMH-154', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-legionnaire-standard-bearer-variant', True),
    ('WMH-153', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-legionnaire-officer-variant', True),
    ('WMH-051', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-sharpshooter-variant', True),
    ('WMH-145', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-cygnar-storm-legion-stryker-chassis-variant', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Cygnar. Idempotent.'

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
                f'Seeded {seeded} Cygnar Steamforged UK prices. Skipped: {skipped}.'
            )
        )
