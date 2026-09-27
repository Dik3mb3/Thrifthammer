"""
Seed Firestorm Games UK prices for Warmachine: Protectorate of Menoth.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(PROTECTORATE OF MENOTH sub-category, exactly 6 listings there -- confirmed
by the user 2026-09-26).

**All 18 Menoth SKUs are new, not-yet-released products** (dispatch
27/10/2026-19/01/2027; see project_warmachine_faction_rollout memory) --
eBay/Amazon were deliberately deferred to November 2026 for this faction
since there's no secondary-market inventory yet for an unreleased line.
Firestorm is different: it's a real, current PRE ORDER direct from the
publisher's own release, not a secondary-market listing, so it was NOT
deferred. **Explicitly confirmed with the user 2026-09-26: record these 6
as in_stock=True** (a live, purchasable pre-order, not "out of stock") --
do not reuse the backorder in_stock=False convention here.

6 of 18 catalog SKUs matched, each opened and verified individually. The
other 12 (Revenger/Crusader "Options" variants, Flameguard Defenders,
Cleanser Sanctifiers/Skyhammers/Purifiers/Preceptor/Sunburst Crew, Vassals
of Menoth, Reclaimer, Flameguard Defender Standard, Cleanser Purifier
Officer) have not yet been checked against Firestorm's site -- only the 6
that were already visible on the category page were verified this round;
revisit alongside the eBay/Amazon November 2026 pass if Firestorm expands
its Menoth pre-order listing before then.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-353', Decimal('31.49'), 'https://www.firestormgames.co.uk/warmachine-protectorate-of-menoth-covenant-of-the-flame-revenger-light-warjack?aff=6a4ab07d1c6f9', True),
    ('WMH-354', Decimal('35.99'), 'https://www.firestormgames.co.uk/warmachine-protectorate-of-menoth-covenant-of-the-flame-crusader-heavy-warjack?aff=6a4ab07d1c6f9', True),
    ('WMH-352', Decimal('134.99'), 'https://www.firestormgames.co.uk/warmachine-protectorate-of-menoth-covenant-of-the-flame-heralds-of-perdition?aff=6a4ab07d1c6f9', True),
    ('WMH-351', Decimal('134.99'), 'https://www.firestormgames.co.uk/warmachine-protectorate-of-menoth-covenant-of-the-flame-bastions-of-faith?aff=6a4ab07d1c6f9', True),
    ('WMH-350', Decimal('134.99'), 'https://www.firestormgames.co.uk/warmachine-protectorate-of-menoth-covenant-of-the-flame-scourge-of-the-unbeliever?aff=6a4ab07d1c6f9', True),
    ('WMH-349', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine-protectorate-of-menoth-covenant-of-the-flame-defenders-of-the-flame?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Protectorate of Menoth. Idempotent.'

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
                f'Seeded {seeded} Warmachine: Protectorate of Menoth Firestorm Games prices. Skipped: {skipped}.'
            )
        )
