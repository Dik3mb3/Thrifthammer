"""
Seed Firestorm Games UK prices for Warmachine: Cryx.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(CRYX sub-category) plus a full-site search for "Cryx" and each individual
DB product name, to catch listings outside that category page -- this is
how WMH-006 (Hive Mind Cadre) was found; Firestorm's own site miscategorizes
it under a stale "Warmachine & Hordes 3rd Ed" breadcrumb despite it being a
current, in-print Steamforged Games product (brand + description confirmed
on the product page, 2026-09-26).

3 of 23 catalog SKUs are seeded here (5 matched on 2026-09-26, each opened and
verified individually; WMH-004 and WMH-254 were dropped later, see below). The
other 18 (Deathjack, Hellraker, Malefactor, Raptor Light
Warjack, Mechanithrall Swarm/Brutes, Necroharvester, Machine Wraith
Dominator, Necrosurgeon Initiates, Skarlock Lieutenant, Sludge Thralls,
Night Terrors, Iron Lich Commander, Mortenebra Perfected, Criterions Unit,
Cryx Defenses Set) returned zero results anywhere on Firestorm's site --
confirmed via direct site search per SKU/name, not just the category page.
Firestorm does carry several other legacy MK2/3 Cryx items (Bile Thralls,
Blood Gorgers, Warwitch Deneghra, Bloat Thrall, Epic Sturgis) but none of
those match a name in our catalog -- not force-matched.

Command Starter (WMH-004) and Core Expansion (WMH-254) were removed from this
seed on 2026-10-08: their Firestorm pages no longer exist under any address
(the old addresses return 404 and no renamed page was found), so the rows were
blanked (no price, no link). Leaving them here would put the dead links back on
every deploy.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-006', Decimal('71.99'), 'https://www.firestormgames.co.uk/warmachine---hive-mind-cadre?aff=6a4ab07d1c6f9', True),
    ('WMH-233', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine-cryx-necrofactorium-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-235', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine-cryx-necrofactorium-battlegroup-box?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Cryx. Idempotent.'

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
                f'Seeded {seeded} Warmachine: Cryx Firestorm Games prices. Skipped: {skipped}.'
            )
        )
