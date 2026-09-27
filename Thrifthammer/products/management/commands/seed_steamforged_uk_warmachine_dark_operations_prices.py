"""
Seed Steamforged Games UK prices for Warmachine: Dark Operations.

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

Source: https://warmachine.gg/collections/dark-operations (22 products, one
page), GB/GBP localization confirmed selected. Each match verified by
pairing product title text with its href directly via JS (not list
position).

All 17 of 17 catalog SKUs matched -- no gaps, no new-wave surprises this
time. 5 of the 22 page listings are cross-listed characters/units that
belong to OTHER factions in our catalog and are correctly excluded here:
Hive Mind Cadre, Cryx Defenses Set, Criterions Unit (all Cryx -- WMH-006,
WMH-082, WMH-314), Emperor Carver Ultimus Esquire III & War Boar MMD47,
Magnus the Unstoppable and Invictus (both Mercenaries -- WMH-061, WMH-060).
These will be picked up when their own factions get their Steamforged UK
pass.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-340', Decimal('21.99'), 'https://warmachine.gg/products/warmachine-dark-operations-mind-slavers', True),
    ('WMH-338', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dark-operations-drudge-slayers-sculpts-a-e', True),
    ('WMH-339', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dark-operations-drudge-slayers-sculpts-f-j', True),
    ('WMH-008', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-wrecker', True),
    ('WMH-317', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-warden', True),
    ('WMH-318', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-subduer', True),
    ('WMH-341', Decimal('54.99'), 'https://warmachine.gg/products/warmachine-drudge-iconoclasts', True),
    ('WMH-342', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-exulon-thexus', True),
    ('WMH-343', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-overlords', True),
    ('WMH-344', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-stygius', True),
    ('WMH-345', Decimal('21.99'), 'https://warmachine.gg/products/warmachine-mind-benders', True),
    ('WMH-105', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-dominated-stormblades', True),
    ('WMH-106', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-dominated-winter-korps', True),
    ('WMH-107', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-dominated-strike-reavers', True),
    ('WMH-117', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-drudge-conduits', True),
    ('WMH-118', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-cognifex-cyphon', True),
    ('WMH-119', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-agitators', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Dark Operations. Idempotent.'

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
                f'Seeded {seeded} Dark Operations Steamforged UK prices. Skipped: {skipped}.'
            )
        )
