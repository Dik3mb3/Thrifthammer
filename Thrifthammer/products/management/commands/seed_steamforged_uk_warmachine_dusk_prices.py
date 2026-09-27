"""
Seed Steamforged Games UK prices for Warmachine: Dusk.

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

Source: Dusk is split across two Steamforged sub-collections --
https://warmachine.gg/collections/dusk-fane-of-nyrro (24 products, 1 page)
and https://warmachine.gg/collections/dusk-house-kallyss (31 products, 2
pages) -- mirroring our own catalog's "Fane of Nyrro" / "House Kallyss"
naming split. GB/GBP localization confirmed selected. Each match verified
by pairing product title text with its href directly via JS (not list
position).

All 46 of 46 catalog SKUs matched -- full coverage, no gaps.

**Important correction to an earlier finding**: WMH-288 "Dusk House
Kallyss Command Starter" lives at .../warmachine-dusk-ghosts-of-ios-command-cadre
-- its own page text confirms "Previously known as 'Warmachine: Dusk Ghost
of Ios Command Cadre', this set was updated in May 2025". This means the
"Dusk Ghosts of Ios Cadre" listing found on Firestorm Games during the
earlier Firestorm UK audit (flagged then as an unmatched catalog gap,
since its contents -- Morayne, Mage Hunter Assassins/Rangers/Sniper Team,
Vaelyss, Specter -- didn't obviously read as WMH-288) is actually the SAME
product under its old name -- Firestorm just hasn't updated their listing
title. Confirmed via this product's own official page text, not assumed.
Flagged for the user to decide whether to backfill that Firestorm price
onto WMH-288; not done here.

Excluded from this command (not individual catalog SKUs): two Steamforged
bundle listings ("Dusk Fane of Nyrro Mercenaries Bundle" GBP 75.96, "Dusk
Fane of Nyrro Army Bundle" GBP 599.94, made-to-order) and a new
"PRE-ORDER" wave of 5 items with no catalog match ("The Gathering
Darkness" GBP 149.99, "Styrge Hounds" GBP 44.99, "Riven" GBP 19.99,
"Razorbat Alpha" GBP 24.99, "Hollowed" GBP 24.99) -- same pattern as the
Cryx wave-2 refresh found earlier, flagged not created. Gorman di Wolfe
(cross-listed on the House Kallyss page) is WMH-015, Mercenaries, excluded.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_STEAMFORGED_UK_SLUG = 'steamforged-games-uk'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-003', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-nymara-the-shadowblade', True),
    ('WMH-020', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-executioner-s-toll', True),
    ('WMH-022', Decimal('149.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-deaths-whisper', True),
    ('WMH-005', Decimal('149.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-army-box-court-of-shadows', True),
    ('WMH-100', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-the-final-hunt-command-cadre-hips', True),
    ('WMH-040', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-heavy-warbeast-vordak', True),
    ('WMH-041', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-light-warbeast-strygon', True),
    ('WMH-019', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-the-merciless', True),
    ('WMH-012', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-the-devoted', True),
    ('WMH-007', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-blood-sirens', True),
    ('WMH-013', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-sythyss-overseer', True),
    ('WMH-009', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-fane-stalkers', True),
    ('WMH-093', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-fane-knights', True),
    ('WMH-094', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-strygon-rider', True),
    ('WMH-024', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-sythyss-prophet', True),
    ('WMH-096', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-strygon-light-warbeast-options', True),
    ('WMH-097', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-dusk-fane-of-nyrro-vordak-heavy-warbeast-options', True),
    ('WMH-048', Decimal('74.99'), 'https://warmachine.gg/products/warmachine-imperatus-ashen-phoenix', True),
    ('WMH-334', Decimal('104.99'), 'https://warmachine.gg/products/warmachine-frozen-forgotten-hips', True),
    ('WMH-251', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-phantasm', True),
    ('WMH-288', Decimal('94.99'), 'https://warmachine.gg/products/warmachine-dusk-ghosts-of-ios-command-cadre', True),
    ('WMH-063', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-battlegroup-box', True),
    ('WMH-197', Decimal('144.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-core-expansion', True),
    ('WMH-198', Decimal('134.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-auxiliary-expansion', True),
    ('WMH-319', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-dreadguard-scyir', True),
    ('WMH-026', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-scyrafael-nis-issyr-of-desolation', True),
    ('WMH-206', Decimal('69.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-void-engine-and-wights', True),
    ('WMH-285', Decimal('32.99'), 'https://warmachine.gg/products/warmachine-specter', True),
    ('WMH-208', Decimal('47.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-dreadguard-cavalry', True),
    ('WMH-207', Decimal('19.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-void-shaper', True),
    ('WMH-205', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-seeker-adepts', True),
    ('WMH-204', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-dreadguard-slayers', True),
    ('WMH-203', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-soulless-hunters', True),
    ('WMH-210', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-soulless-blademasters', True),
    ('WMH-202', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-soulless-guardians', True),
    ('WMH-200', Decimal('34.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-ghast', True),
    ('WMH-199', Decimal('39.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-eidolon', True),
    ('WMH-263', Decimal('30.99'), 'https://warmachine.gg/products/warmachine-dreadguard-archers', True),
    ('WMH-265', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-mage-hunter-sniper-team', True),
    ('WMH-266', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-mage-hunter-assassins', True),
    ('WMH-076', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-mage-hunter-rangers', True),
    ('WMH-268', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-seeker-warden-variant', True),
    ('WMH-211', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-variant-mage-hunter-commander', True),
    ('WMH-209', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-seeker-warden', True),
    ('WMH-264', Decimal('15.99'), 'https://warmachine.gg/products/warmachine-mage-hunter-commander', True),
    ('WMH-201', Decimal('24.99'), 'https://warmachine.gg/products/warmachine-dusk-house-kallyss-eidolon-chassis-variant', True),
]


class Command(BaseCommand):
    help = 'Seed Steamforged Games UK prices and URLs for Warmachine: Dusk. Idempotent.'

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
                f'Seeded {seeded} Dusk Steamforged UK prices. Skipped: {skipped}.'
            )
        )
