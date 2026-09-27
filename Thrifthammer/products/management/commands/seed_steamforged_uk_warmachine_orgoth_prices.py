"""
Seed Steamforged Games UK prices for Warmachine: Orgoth Sea Raiders.

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

Source: https://warmachine.gg/collections/orgoth-sea-raiders (30 listings,
2 pages). GB/GBP localization confirmed selected. Each match verified by
pairing product title text with its href directly via JS (not list
position).

All 28 of 28 catalog SKUs matched -- full coverage. Two items on the
collection pages were excluded, not gaps:

- "Frozen & Forgotten (HIPS)" (page 1, £104.99) is WMH-334, which belongs
  to Dusk in our catalog (confirmed faction=Dusk). Steamforged's own site
  cross-lists it here because it is a two-faction box (Dusk vs Orgoth). It
  is already priced under the Dusk Steamforged UK seed command.
- "Azdharak, Herald of Immolation" (page 2, £74.99,
  /products/warmachine-azdharak-orgoth-super-heavy-warjack) matches
  WMH-033, which currently sits in the catalog's UNASSIGNED pool
  (faction=None). This is a faction-reassignment question, not a pricing
  one -- flagged for the user, excluded from this command pending a
  decision on assigning WMH-033 to Orgoth Sea Raiders.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-157', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-core-expansion', True),
    ('WMH-290', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-orgoth-cursebound-command-cadre', True),
    ('WMH-037', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-orsus-the-betrayed', True),
    ('WMH-276', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-gnashers', True),
    ('WMH-275', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-grhotten-keeper', True),
    ('WMH-274', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-grhotten-champion', True),
    ('WMH-273', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-ravener', True),
    ('WMH-272', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-orgoth-reaver-commander', True),
    ('WMH-271', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-orgoth-standard-bearer', True),
    ('WMH-173', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-gharlghast', True),
    ('WMH-172', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-horruskh-the-thousand-faces', True),
    ('WMH-171', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-reaver-standard-variant', True),
    ('WMH-170', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-reaver-commander-variant', True),
    ('WMH-169', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-siege-tarask', True),
    ('WMH-054', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-vulcar-forge-master', True),
    ('WMH-168', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-rhok-harriers', True),
    ('WMH-167', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-ulkor-axers', True),
    ('WMH-166', Decimal('37.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-reaver-skirmishers', True),
    ('WMH-165', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-warwitch-coven', True),
    ('WMH-164', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-ulkor-barragers', True),
    ('WMH-163', Decimal('37.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-strike-reavers', True),
    ('WMH-162', Decimal('37.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-assault-reavers', True),
    ('WMH-053', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-tyrant-chassis-variant', True),
    ('WMH-161', Decimal('35.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-jackal-light-warjack', True),
    ('WMH-160', Decimal('42.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-tyrant-heavy-warjack', True),
    ('WMH-159', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-battlegroup-box', True),
    ('WMH-158', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-orgoth-sea-raiders-auxiliary-expansion', True),
    ('WMH-101', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-the-graveborn-command-cadre-hips', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Orgoth Sea Raiders. Idempotent.'

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
                f'Seeded {seeded} Orgoth Sea Raiders Steamforged UK prices. Skipped: {skipped}.'
            )
        )
