"""
Seed Steamforged Games UK prices for Warmachine: Khador.

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

Source: Khador is split across two Steamforged sub-collections --
https://warmachine.gg/collections/khador-old-umbrey (30 products, 2 pages)
and https://warmachine.gg/collections/khador-winter-korps (30 products, 2
pages) -- mirroring our own catalog's "Old Umbrey" / "Winter Korps" naming
split. GB/GBP localization confirmed selected. Each match verified by
pairing product title text with its href directly via JS (not list
position) -- caught two more misleading legacy slugs this way: "Khador
Winter Korps Command Starter" (WMH-289) lives at
.../warmachine-khador-annihilators-command-cadre, and "Behemoth, Spirit of
Imperial Khador" (WMH-043) lives at .../warmachine-behemoth-ii.

All 51 of 51 catalog SKUs matched -- full coverage, no gaps in the
existing catalog.

**New genuine gap found, NOT added**: "Drago, the Beast Unchained" (GBP
74.99, .../warmachine-drago-the-beast-unchained) is a real, CURRENTLY
AVAILABLE (not pre-order) Khador Old Umbrey super-heavy warbeast with no
matching Product row in our catalog at all -- unlike the Cryx/Dusk
"PRE-ORDER wave" gaps, this one is live and purchasable right now.
Flagged for the user, not created.

3 cross-listed Mercenaries characters correctly excluded (appear on the
Old Umbrey and/or Winter Korps pages at the same price): Magnus the
Unstoppable and Invictus (WMH-060), Emperor Carver Ultimus Esquire III &
War Boar MMD47 (WMH-061), Zacchaeus Winter's Chill (WMH-193). Gorman di
Wolfe (Mercenaries, WMH-015) also cross-listed, excluded. The "Two Player
Starter Set" cross-listed on both Khador sub-collections is the same
Khador-vs-Cygnar box already matched to WMH-261 under the Cygnar seed
command -- not duplicated here.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-253', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-khador-old-umbrey-command-starter', True),
    ('WMH-237', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-khador-old-umbrey-battlegroup-box', True),
    ('WMH-325', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-khador-old-umbrey-core-expansion', True),
    ('WMH-328', Decimal('139.99'), 'https://warmachine.gg/products/warmachine-khador-old-umbrey-auxiliary-expansion', True),
    ('WMH-014', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-gorger', True),
    ('WMH-011', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-lord-of-the-hunt', True),
    ('WMH-335', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-kapitan-kazimir-morozov', True),
    ('WMH-091', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-defenses', True),
    ('WMH-329', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-liegemen-hunters', True),
    ('WMH-330', Decimal('54.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-liegemen-ursans', True),
    ('WMH-089', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-liegemen-ursan-champion', True),
    ('WMH-331', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-ursine-shifted', True),
    ('WMH-332', Decimal('29.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-ursine-apex', True),
    ('WMH-333', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-ursine-shifted-variant', True),
    ('WMH-085', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-liegemen-wardens', True),
    ('WMH-326', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-shearlings', True),
    ('WMH-086', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-lupine-shifted', True),
    ('WMH-039', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-lupine-shifted-variant', True),
    ('WMH-087', Decimal('27.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-lupine-apex', True),
    ('WMH-327', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-liegemen-primalist', True),
    ('WMH-088', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-animist', True),
    ('WMH-315', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-primeval-warbeast', True),
    ('WMH-316', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-old-umbrey-feral-warbeast', True),
    ('WMH-075', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-kapitan-yana-kovoskiy', True),
    ('WMH-072', Decimal('64.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-sks-6-command-cadre', True),
    ('WMH-289', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-khador-annihilators-command-cadre', True),
    ('WMH-176', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-battlegroup-box', True),
    ('WMH-174', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-core-expansion', True),
    ('WMH-175', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-auxiliary-expansion', True),
    ('WMH-043', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-behemoth-ii', True),
    ('WMH-186', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-mastodon', True),
    ('WMH-058', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-ac-2-bison', True),
    ('WMH-055', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-great-bear-chassis-variant', True),
    ('WMH-179', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-infantry-standard-bearer', True),
    ('WMH-292', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-avalanche', True),
    ('WMH-056', Decimal('29.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-snipers-and-hunting-dog', True),
    ('WMH-182', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-officer', True),
    ('WMH-180', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-shock-trooper-gunners', True),
    ('WMH-057', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-battle-mechanik', True),
    ('WMH-185', Decimal('44.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-man-o-war-suppressors', True),
    ('WMH-183', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-shock-trooper-pikemen', True),
    ('WMH-262', Decimal('44.99'), 'https://warmachine.gg/products/warmachine-man-o-war-wrecking-crew', True),
    ('WMH-184', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-mortar-team', True),
    ('WMH-177', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-great-bear-heavy-warjack', True),
    ('WMH-247', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-winter-korp-infantry-b', True),
    ('WMH-181', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-arkanists', True),
    ('WMH-027', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-kontroller', True),
    ('WMH-246', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-winter-korp-infantry-a', True),
    ('WMH-178', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-dire-wolf-heavy-warjack', True),
    ('WMH-282', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-winter-korps-standard-bearer', True),
    ('WMH-307', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-khador-winter-korps-infantry-support-weapon-troopers', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Khador. Idempotent.'

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
                f'Seeded {seeded} Khador Steamforged UK prices. Skipped: {skipped}.'
            )
        )
