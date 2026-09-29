"""
Management command: populate_starcraft_products

Creates the StarCraft product line as a new top-level Category (no Faction
subdivision -- standalone game system, same pattern as Halo: Flashpoint and
Star Wars: Legion).

StarCraft: The Tabletop Miniatures Game is published/manufactured by Archon
Studio under license from Blizzard Entertainment. This is a UK-first
category: all 25 products and their MSRP come from the user-supplied
"Starcraft - Archon UK prices.xlsx" sheet (Title/Title_URL/Image/pricing2
columns), sourced from Archon's own storefront (starcraft-tmg.com) with its
region switched to United Kingdom (GBP) -- spot-verified live (Hydralisk
GBP 35.00, Protoss Starter Set GBP 95.00, both matched the sheet exactly).

This category therefore has NO games-workshop-uk row (not a GW product) and
NO US pricing at all yet -- product.msrp is intentionally left blank for
every row here; only product.msrp_gbp is set (create-only guard, same rule
as every other UK retailer seed command -- never resets a value a live
updater may have since changed). The US-region product pages for this
category will show no MSRP/price until a US retailer source is added later;
that is expected, not a bug, per the "never use placeholder data" rule --
leave the field null rather than inventing a US price.

Name cleanup applied uniformly (cosmetic only, no facts changed):
  - The registered-trademark symbol (U+00AE) is stripped from every title
    for consistency with how every other category is displayed on this
    site (e.g. "Halo: Flashpoint", not "Halo(R): Flashpoint(TM)").
  - 9 of the 25 sheet rows (the "pre-orders" section: both Starter Sets,
    all 4 Expansion Sets, the Rulebook) were in ALL CAPS in the source --
    confirmed via the live site that this is just that page section's own
    CSS text-transform, not the actual underlying product name -- reflowed
    to Title Case to match the other 16 rows and the rest of the catalog.

Pre-order handling: all 9 "pre-orders" section items are confirmed live,
currently-purchasable listings ("Pre-order now" button present, not a
future/unavailable placeholder) -- recorded with in_stock=True, same
convention already established for Warmachine's Menoth/Cryx/Dusk pre-order
waves elsewhere in this catalog.

gw_sku scheme: SC-001 through SC-025 (prefix confirmed unused elsewhere in
the catalog before this command was written).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug, CurrentPrice keyed by product+retailer, msrp_gbp
and price both create-only).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

# (slug, gw_sku, name, gbp_price, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('starcraft-hydralisk', 'SC-001', 'StarCraft Hydralisk', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Hydralisk/Hydralisk%20-%201.jpg/300_300_crop.jpg?ts=1772804451&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-r-hydralisk', 'StarCraft Hydralisk'),
    ('starcraft-zergling', 'SC-002', 'StarCraft Zergling', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Zergling/Zergling%20-%201.jpg/300_300_crop.jpg?ts=1772805122&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-zergling', 'StarCraft Zergling'),
    ('starcraft-roach', 'SC-003', 'StarCraft Roach', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Roach/Roach%20-%201.jpg/300_300_crop.jpg?ts=1772806204&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-roach', 'StarCraft Roach'),
    ('starcraft-queen', 'SC-004', 'StarCraft Queen', Decimal('25.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Queen/Queen%20-%201.jpg/300_300_crop.jpg?ts=1772806613&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-queen', 'StarCraft Queen'),
    ('starcraft-kerrigan-omega-worm', 'SC-005', 'StarCraft Kerrigan & Omega Worm', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Kerrigan%20&%20Omega%20Worm/Kerrigan%20-%201.jpg/300_300_crop.jpg?ts=1772806885&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-kerrigan-omega-worm', 'StarCraft Kerrigan Omega Worm'),
    ('starcraft-marine', 'SC-006', 'StarCraft Marine', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Marine/Marine%20-%201.jpg/300_300_crop.jpg?ts=1773153486&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-marine', 'StarCraft Marine'),
    ('starcraft-marauder', 'SC-007', 'StarCraft Marauder', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Marauder/Marauder%20-%201.jpg/300_300_crop.jpg?ts=1772807668&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-marauder', 'StarCraft Marauder'),
    ('starcraft-medic', 'SC-008', 'StarCraft Medic', Decimal('22.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Medic/Medic%20-%201.jpg/300_300_crop.jpg?ts=1772808786&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-medic', 'StarCraft Medic'),
    ('starcraft-goliath', 'SC-009', 'StarCraft Goliath', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Goliath/Goliath%20-%201.jpg/300_300_crop.jpg?ts=1772809104&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-goliath', 'StarCraft Goliath'),
    ('starcraft-jim-raynor-point-defense-drone', 'SC-010', 'StarCraft Jim Raynor & Point Defense Drone', Decimal('29.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20%20Jim%20Raynor%20&%20Point%20Defense%20Drone/Terran%20Jim%20Raynor%20-%201.jpg/300_300_crop.jpg?ts=1772809389&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-jim-raynor-point-defense-drone', 'StarCraft Jim Raynor'),
    ('starcraft-zealot', 'SC-011', 'StarCraft Zealot', Decimal('29.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Zealot/Zealot%20-%201.jpg/300_300_crop.jpg?ts=1772810061&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-zealot', 'StarCraft Zealot'),
    ('starcraft-adept', 'SC-012', 'StarCraft Adept', Decimal('29.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Adept/Adept6.jpg/300_300_crop.jpg?ts=1772810347&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-adepts', 'StarCraft Adept'),
    ('starcraft-sentry', 'SC-013', 'StarCraft Sentry', Decimal('25.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Sentry/Sentry%20-%201.jpg/300_300_crop.jpg?ts=1772810862&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-sentry', 'StarCraft Sentry'),
    ('starcraft-stalker', 'SC-014', 'StarCraft Stalker', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Stalker/Stalker%20-%201.jpg/300_300_crop.jpg?ts=1772811252&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-stalker', 'StarCraft Stalker'),
    ('starcraft-artanis-pylon', 'SC-015', 'StarCraft Artanis & Pylon', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Artanis%20&%20Pylon/Artanis%20-%201.jpg/300_300_crop.jpg?ts=1772811442&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-artanis-pylon', 'StarCraft Artanis Pylon'),
    ('starcraft-lost-temple', 'SC-016', 'StarCraft Lost Temple', Decimal('35.00'), 'https://starcraft-tmg.com/files/thumbs/products/StarCraft%C2%AE%20Lost%20Temple/Lost%20Temple%20-%201.jpg/300_300_crop.jpg?ts=1772811697&pn=300x300', 'https://starcraft-tmg.com/shop/products/starcraft-lost-temple', 'StarCraft Lost Temple'),
    ('starcraft-protoss-starter-set', 'SC-017', 'StarCraft Protoss Starter Set', Decimal('95.00'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Protoss%20Starter%20Set/W2%20Protoss%20Starter%20Set%20-%201.jpg/300_300_crop.jpg?ts=1787228724&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-protoss-starter-set', 'StarCraft Protoss Starter Set'),
    ('starcraft-zerg-starter-set', 'SC-018', 'StarCraft Zerg Starter Set', Decimal('89.00'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Zerg%20Starter%20Set/W2%20Zerg%20Starter%20Set%20-%201.jpg/300_300_crop.jpg?ts=1787229077&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-zerg-starter-set', 'StarCraft Zerg Starter Set'),
    ('starcraft-terran-starter-set', 'SC-019', 'StarCraft Terran Starter Set', Decimal('89.00'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Terran%20Starter%20Set/W2%20Terran%20Starter%20Set%20-%201.jpg/300_300_crop.jpg?ts=1787229931&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-terran-starter-set', 'StarCraft Terran Starter Set'),
    ('starcraft-ravager-zerg-expansion-set', 'SC-020', 'StarCraft Ravager - Zerg - Expansion Set', Decimal('45.00'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Ravager/Ravager%20-%201.jpg/300_300_crop.jpg?ts=1787230216&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-ravager-zerg-expansion-set', 'StarCraft Ravager Zerg'),
    ('starcraft-immortal-protoss-expansion-set', 'SC-021', 'StarCraft Immortal - Protoss - Expansion Set', Decimal('49.00'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Immortal/Immortal%20-%201.jpg/300_300_crop.jpg?ts=1787231009&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-immortal-protoss-expansion-set', 'StarCraft Immortal Protoss'),
    ('starcraft-siege-tank-terran-expansion-set', 'SC-022', 'StarCraft Siege Tank - Terran - Expansion Set', Decimal('59.00'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Siege%20tank/Siege%20Tank%20-%201.jpg/300_300_crop.jpg?ts=1787231508&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-siege-tank-terran-expansion-set', 'StarCraft Siege Tank Terran'),
    ('starcraft-zeratul-protoss-hero-expansion-set', 'SC-023', 'StarCraft Zeratul - Protoss - Hero Expansion Set', Decimal('29.00'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Zeratul/Zeratul%20-%201.jpg/300_300_crop.jpg?ts=1787231683&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-zeratul-protoss-hero-expansion-set', 'StarCraft Zeratul'),
    ('starcraft-lost-temple-ramp-terrain-expansion-set', 'SC-024', 'StarCraft Lost Temple Ramp - Terrain Expansion Set', Decimal('29.00'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Lost%20temple%20ramp/Ramp%20-%201.jpg/300_300_crop.jpg?ts=1787233075&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-lost-temple-ramp-terrain-expansion-set', 'StarCraft Lost Temple Ramp'),
    ('starcraft-rulebook', 'SC-025', 'StarCraft Rulebook', Decimal('7.50'), 'https://starcraft-tmg.com/files/thumbs/products/W2%20Rulebook/W2%20Rulebook-%201.jpg/300_300_crop.jpg?ts=1787233305&pn=300x300', 'https://starcraft-tmg.com/shop/pre-orders/starcraft-rulebook', 'StarCraft Rulebook'),
]


class Command(BaseCommand):
    """Populate the StarCraft product line and its Archon Studio UK MSRP (idempotent)."""

    help = 'Populates StarCraft products (SC-001 to SC-025) with Archon Studio UK MSRP.'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='starcraft',
            defaults={'name': 'StarCraft'},
        )

        # 'archon-studio-uk' (not the bare 'archon-studio') -- the bare slug is
        # reserved for the US-side retailer, same is_uk split convention as
        # steamforged-games/steamforged-games-uk and mantic-games/mantic-games-uk.
        # See seed_archon_studio_starcraft_prices.py for the US counterpart.
        archon, created = Retailer.objects.get_or_create(
            slug='archon-studio-uk',
            defaults={
                'name': 'Archon Studio UK',
                'website': 'https://starcraft-tmg.com',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,          # REQUIRED -- prevents GBP prices leaking onto US pages.
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {archon.name}')

        products_created = 0
        products_updated = 0
        prices_created = 0
        prices_updated = 0

        for slug, gw_sku, name, gbp_price, image_url, product_url, ebay_search_name in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'image_url': image_url,
                    'gw_url': product_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'starcraft',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            # Create-only -- never resets a value a live price-verification
            # run or manual correction may have since changed.
            if product.msrp_gbp is None:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

            cp_defaults = {
                'url': product_url, 'in_stock': True, 'not_available': False, 'currency': 'GBP',
            }
            _, price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=archon,
                defaults=cp_defaults,
                create_defaults={**cp_defaults, 'price': gbp_price},
            )
            if price_created:
                prices_created += 1
            else:
                prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Archon Studio UK prices: {prices_created} created, {prices_updated} updated.'
        ))
