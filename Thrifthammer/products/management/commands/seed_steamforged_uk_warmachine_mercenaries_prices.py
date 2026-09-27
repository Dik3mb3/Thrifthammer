"""
Seed Steamforged Games UK prices for Warmachine: Mercenaries.

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

Source: https://warmachine.gg/collections/mercenaries (22 listings, 1
page). GB/GBP localization confirmed selected. Each match verified by
pairing product title text with its href directly via JS (not list
position).

All 22 of 22 catalog SKUs matched -- full coverage, no gaps, no cross-listed
exclusions needed (cleanest batch of the rollout).

WMH-367 "Captain Barl 'Demolisher' Dunax" is PRE-ORDER (a brand-new SKU
created this session, no secondary-market footprint yet elsewhere) --
recorded with in_stock=True, same convention explicitly confirmed by the
user for Protectorate of Menoth's pre-order SKUs (a live, purchasable
pre-order is treated as available, not "out of stock").

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-367', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-captain-barl-demolisher-dunax-mercenary', True),
    ('WMH-001', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-constance-blaize-gallant', True),
    ('WMH-095', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-hellslinger-phantom', True),
    ('WMH-031', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-mind-thief', True),
    ('WMH-015', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-gorman-di-wolfe-revolutionary-agent', True),
    ('WMH-321', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-exulon-nostilla-and-aberration-hips', True),
    ('WMH-062', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-mercenary-krueger-wrath-of-blighterghast', True),
    ('WMH-059', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-mercenary-maulgreth-the-charnel-plague', True),
    ('WMH-187', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-mercenary-prisoner-102822', True),
    ('WMH-016', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-mercenary-eilish-garrity-the-dark-traitor', True),
    ('WMH-188', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-mercenary-koldun-lord-damien-korovnik', True),
    ('WMH-189', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-mercenary-eiryss-shadow-of-retribution', True),
    ('WMH-017', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-mercenary-alexia-queen-of-the-damned', True),
    ('WMH-060', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-mercenary-magnus-the-unstoppable-and-invictus', True),
    ('WMH-061', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-mercenary-emperor-carver-ultimus-esquire-iii-war-boar-mmd47', True),
    ('WMH-190', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-mercenary-nissak-totem-huntress-champion', True),
    ('WMH-191', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-mercenary-brineblood-marauders-madam-moriarty', True),
    ('WMH-192', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-mercenary-shadowflame-shard-bellighul-master-of-pain', True),
    ('WMH-193', Decimal('29.99'), 'https://warmachine.gg/products/warmachine-mercenary-shadowflame-shard-zacchaeus-winters-chill', True),
    ('WMH-194', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-mercenary-brineblood-marauders-greygore-boomhowler', True),
    ('WMH-195', Decimal('99.99'), 'https://warmachine.gg/products/warmachine-mercenary-sky-bomber', True),
    ('WMH-196', Decimal('99.99'), 'https://warmachine.gg/products/warmachine-mercenary-sky-raider', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Mercenaries. Idempotent.'

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
                f'Seeded {seeded} Mercenaries Steamforged UK prices. Skipped: {skipped}.'
            )
        )
