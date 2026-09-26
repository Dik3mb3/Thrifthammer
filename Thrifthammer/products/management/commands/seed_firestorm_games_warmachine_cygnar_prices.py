"""
Seed Firestorm Games UK prices for Warmachine: Cygnar.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), price is create-only (see create_defaults below) so a
redeploy never resets a price a manual correction or future live updater
has since changed. NEVER writes msrp_gbp -- Firestorm is a discount
competitor here, not the MSRP source; steamforged-games-uk holds that role
for Warmachine (see seed_steamforged_uk_warmachine_crucible_guard_prices.py).

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.

Source: https://www.firestormgames.co.uk/wargames-miniatures/warmachine-4th-edition
(CYGNAR sub-category) plus a full-site search for "Cygnar" and each of the
39 other individual DB product names in this faction, to catch listings
outside that category page (the Cryx batch found one this way -- Hive Mind
Cadre). None of the 39 individual-unit searches (Bandit, Sharpshooter,
Captain Raef Huxley, Courser Light Warjack, Tempest Assailers, Weather
Station, Maelstrom, Heavy Field Gun, Thunderhead, Stryker Heavy Warjack,
Stormblade/Stormguard/Stormthrower Legionnaires, Tempest Thunderers, Arcane
Mechaniks, Storm Lance Legionnaires, Zephyr, Storm Callers, Storm Vanes,
Legionnaire Standard Bearer, Two Player Starter Set, Borealis, Gravediggers
Valiant/Patriot Warjack, Gravediggers Airdrops/Rangers/Commando, Captain
Connor 'Boom Boom' McCoy, Assault Strider, Gravediggers Heavy Machinegun
Crew/Trollkin Express Sniper/Gunmages/Armored Airdrop, Gravediggers Defenses
Set) returned a genuine hit for this faction -- confirmed 2026-09-26.

9 of 49 catalog SKUs matched, each opened and verified individually.
"Warmachine: Cygnar Gravediggers Auxiliar" (WMH-234) has a genuinely
truncated title AND URL slug on Firestorm's own site (their data entry
error, not ours) -- confirmed via its contents (Colonel Allison Jakes,
Gravedigger Commandos, Captain Argo Brock) that it is the real Auxiliary
Expansion box, same price tier as every other faction's Auxiliary Expansion.

NOT matched to any SKU, and NOT a catalog gap to add here (see project rule
against creating products in a seed command) -- flagged to the user
instead: "Warmachine: Cygnar Storm Forge Cadre" (£62.99) is a genuine,
current, separate 4th-edition Command Cadre product (Master Mechanik Adept
Figmund Sparkhammer + Storm Forge unit) that Firestorm carries but that has
no corresponding Product row in our catalog at all.

Storm Legion Core Expansion is 0-in-stock/backorder at Firestorm -- seeded
with the real price and in_stock=False, per the sold-out-listing rule
(never clear a real price just because a listing is temporarily
unavailable).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

# (gw_sku, gbp_price, url, in_stock)
_PRICES = [
    ('WMH-071', Decimal('58.49'), 'https://www.firestormgames.co.uk/warmachine:-cygnar-hellslingers-command-cadre-hips?aff=6a4ab07d1c6f9', True),
    ('WMH-286', Decimal('85.49'), 'https://www.firestormgames.co.uk/warmachine:-command-starter-for-cygnar-storm-legion?aff=6a4ab07d1c6f9', True),
    ('WMH-234', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine:-cygnar-gravediggers-auxiliar?aff=6a4ab07d1c6f9', True),
    ('WMH-255', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-cygnar-gravediggers-core-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-236', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine:-cygnar-gravediggers-battlegroup-box?aff=6a4ab07d1c6f9', True),
    ('WMH-074', Decimal('67.49'), 'https://www.firestormgames.co.uk/warmachine:-cygnar-gravediggers-command-starter?aff=6a4ab07d1c6f9', True),
    ('WMH-143', Decimal('62.99'), 'https://www.firestormgames.co.uk/warmachine:-cygnar-storm-legion-battlegroup-box?aff=6a4ab07d1c6f9', True),
    ('WMH-142', Decimal('121.49'), 'https://www.firestormgames.co.uk/warmachine:-cygnar-storm-legion-auxiliary-expansion?aff=6a4ab07d1c6f9', True),
    ('WMH-034', Decimal('130.49'), 'https://www.firestormgames.co.uk/warmachine:-cygnar-storm-legion-core-expansion?aff=6a4ab07d1c6f9', False),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and URLs for Warmachine: Cygnar. Idempotent.'

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
                f'Seeded {seeded} Warmachine: Cygnar Firestorm Games prices. Skipped: {skipped}.'
            )
        )
