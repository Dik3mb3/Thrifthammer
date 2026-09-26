"""
Seed Firestorm Games UK prices for Warmachine: Dusk.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(DUSK sub-category) plus a full-site search for "Dusk" and each of the 36
other individual DB product names in this faction (Nymara, Blood Sirens,
Fane Stalkers, Sythyss Overseer/Prophet, Scyrafael, Imperatus, Mage Hunter
Rangers/Commander/Sniper Team/Assassins/Variant Commander, Fane Knights,
Strygon Rider, Strygon/Vordak "Options" variants, Eidolon + Chassis
Variant, Ghast, Soulless Guardians/Hunters/Blademasters, Dreadguard
Slayers/Cavalry/Archers/Scyir, Seeker Adepts/Warden/Warden Variant, Void
Engine and Wights, Void Shaper, Phantasm, Specter, Dusk House Kallyss
Command Starter) -- none returned a genuine match, confirmed 2026-09-26.

10 of 46 catalog SKUs matched, each opened and verified individually.
WMH-334 "Frozen & Forgotten" is a combined two-cadre bundle box (Dusk's
Final Hunt cadre + Orgoth's Graveborn cadre together) on Firestorm's own
listing, but our catalog only has one Product row for it (Dusk-scoped, no
Orgoth-faction sibling row exists yet) -- recorded against that single row
as-is; revisit if an Orgoth-scoped WMH-334 row is ever added later.

NOT matched to any SKU, and NOT a catalog gap to add here (see project rule
against creating products in a seed command) -- flagged to the user
instead: "Warmachine: Dusk Ghosts of Ios Cadre" (£85.49) is a genuine,
current, separate 4th-edition Command Cadre bundle (Morayne warcaster +
Mage Hunter Assassins/Rangers/Sniper Team/Commander + Vaelyss character
solo + Specter light warjack) that Firestorm carries but that has no
corresponding Product row in our catalog -- its component units (Mage
Hunter Rangers/Commander/Sniper Team/Assassins, Specter) DO exist as their
own individual SKUs, but the bundle itself as a single retail SKU does not.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-005', Decimal('130.50'), 'https://www.firestormgames.co.uk/warmachine-dusk-fane-of-nyrro-court-of-shadows?aff=6a4ab07d1c6f9', True),
    ('WMH-022', Decimal('134.99'), 'https://www.firestormgames.co.uk/warmachine:-dusk-fane-of-nyrro---deaths-whisper?aff=6a4ab07d1c6f9', True),
    ('WMH-041', Decimal('32.39'), 'https://www.firestormgames.co.uk/warmachine:-dusk---fane-of-nyrro-strygon-light-warbeast?aff=6a4ab07d1c6f9', True),
    ('WMH-040', Decimal('35.99'), 'https://www.firestormgames.co.uk/warmachine:-dusk---fane-of-nyrro-vordak-heavy-warbeast?aff=6a4ab07d1c6f9', True),
    ('WMH-020', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-dusk---fane-of-nyrro-executioners-toll?aff=6a4ab07d1c6f9', True),
    ('WMH-100', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-dusk-final-hunt-?aff=6a4ab07d1c6f9', True),
    ('WMH-334', Decimal('94.49'), 'https://www.firestormgames.co.uk/warmachine:-frozen--forgotten?aff=6a4ab07d1c6f9', True),
    ('WMH-063', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine:-dusk-house-kallyss-battlegroup-box?aff=6a4ab07d1c6f9', True),
    ('WMH-198', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine:-dusk-house-kallyss-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-197', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-dusk-house-kallyss-core-expansion?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Dusk. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': 'https://www.firestormgames.co.uk/?aff=6a4ab07d1c6f9',
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
                f'Seeded {seeded} Warmachine: Dusk Firestorm Games prices. Skipped: {skipped}.'
            )
        )
