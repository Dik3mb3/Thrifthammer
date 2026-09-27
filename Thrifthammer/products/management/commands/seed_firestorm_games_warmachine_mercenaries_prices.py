"""
Seed Firestorm Games UK prices for Warmachine: Mercenaries.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(MERCENARY sub-category, exactly 17 listings there -- confirmed by the
user 2026-09-26, all individually opened and verified). "Gorman di Wulfe"
on Firestorm vs "Gorman di Wolfe" in our catalog is the same character,
just a spelling variant between the two sites.

5 catalog SKUs have no Firestorm listing at all, confirmed via individual
site search: Alexia, Queen of the Damned (WMH-017); Bellighul, Master of
Pain (WMH-192); Sky Bomber (WMH-195); Sky Raider (WMH-196); Captain Barl
"Demolisher" Dunax (WMH-367).

17 of 22 catalog SKUs matched, each opened and verified individually.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-001', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-constance-blaize-and-gallant?aff=6a4ab07d1c6f9', True),
    ('WMH-095', Decimal('17.99'), 'https://www.firestormgames.co.uk/warmachine:-hellslinger-phantom?aff=6a4ab07d1c6f9', True),
    ('WMH-031', Decimal('17.99'), 'https://www.firestormgames.co.uk/warmachine:-the-mind-thief-mercenary?aff=6a4ab07d1c6f9', True),
    ('WMH-015', Decimal('17.99'), 'https://www.firestormgames.co.uk/warmachine:-gorman-di-wulfe-revolutionary-agent?aff=6a4ab07d1c6f9', True),
    ('WMH-321', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-exulon-nostilla-and-aberration-?aff=6a4ab07d1c6f9', True),
    ('WMH-062', Decimal('29.69'), 'https://www.firestormgames.co.uk/warmachine:-krueger-wrath-of-blighterghast?aff=6a4ab07d1c6f9', True),
    ('WMH-061', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-emperor-carver-ultimus-esquire-iii--war-boar-mmd47?aff=6a4ab07d1c6f9', True),
    ('WMH-194', Decimal('17.99'), 'https://www.firestormgames.co.uk/warmachine:-greygore-boomhowler?aff=6a4ab07d1c6f9', True),
    ('WMH-193', Decimal('26.99'), 'https://www.firestormgames.co.uk/warmachine:-zacchaeus-winters-chill?aff=6a4ab07d1c6f9', False),
    ('WMH-191', Decimal('17.99'), 'https://www.firestormgames.co.uk/warmachine:-madam-moriarty?aff=6a4ab07d1c6f9', True),
    ('WMH-190', Decimal('17.99'), 'https://www.firestormgames.co.uk/warmachine:-nissak-totem-huntress-champion?aff=6a4ab07d1c6f9', True),
    ('WMH-060', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-magnus-the-unstoppable-and-invictus?aff=6a4ab07d1c6f9', True),
    ('WMH-189', Decimal('14.39'), 'https://www.firestormgames.co.uk/warmachine:-eiryss-shadow-of-retribution?aff=6a4ab07d1c6f9', True),
    ('WMH-188', Decimal('14.39'), 'https://www.firestormgames.co.uk/warmachine:-koldun-lord-damien-korovnik?aff=6a4ab07d1c6f9', True),
    ('WMH-016', Decimal('14.39'), 'https://www.firestormgames.co.uk/warmachine:-eilish-garrity-the-dark-traitor?aff=6a4ab07d1c6f9', True),
    ('WMH-187', Decimal('14.39'), 'https://www.firestormgames.co.uk/warmachine:-prisoner-102822?aff=6a4ab07d1c6f9', True),
    ('WMH-059', Decimal('17.99'), 'https://www.firestormgames.co.uk/warmachine:-maulgreth-the-charnel-plague?aff=6a4ab07d1c6f9', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Mercenaries. Idempotent.'

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
                f'Seeded {seeded} Warmachine: Mercenaries Firestorm Games prices. Skipped: {skipped}.'
            )
        )
