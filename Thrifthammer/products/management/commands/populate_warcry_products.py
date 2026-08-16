"""
Management command: populate_warcry_products

Creates the Warcry category and faction, and its 6 genuinely-new products
(warbands that don't already exist elsewhere in the catalog under an Age
of Sigmar faction), seeds GW CurrentPrice records at MSRP.

Warcry is its own top-level Category (like Kill Team), not filed under
Age of Sigmar, even though its 6 new products are physically AoS-scale
miniatures -- user confirmed 2026-08-09. The Warcry Faction also belongs
to this Category (so it's the only faction listed when browsing the
Warcry category page).

The other 18 Warcry warbands in the source spreadsheet are the same
physical kits as existing Age of Sigmar faction products (e.g. Mindstealer
Sphiranx already exists as S2D-020 under Slaves to Darkness). Those 18
keep their own original category (Age of Sigmar) and primary faction
unchanged -- they're surfaced on the Warcry category page via a
secondary_factions cross-inclusion in products/views.py's product_list()
(category_slug == 'warcry' special case), not by moving their category.
add_warcry_secondary_faction.py tags those existing rows with Warcry as
a secondary faction rather than creating duplicates. This mirrors the
existing Forces of the Emperor pattern (see
add_forces_of_the_emperor_secondary_faction.py), extended with the extra
category-level inclusion Warcry specifically needs.

Product names match Games Workshop's official website titles exactly.
GW URLs come from the en-US storefront. Images come from the source
spreadsheet's Image URL column, stored once via the shared filename
template and never changed automatically.

ebay_negative_keywords are set directly on each DB row (not part of the
PRODUCTS tuple below, which has no slot for them) -- all 6 have "Dice"
(each warband has a same-named companion Dice Pack accessory that would
otherwise get matched instead of the actual box); WC-004 Pyregheists
also has "Jade" (was matching the unrelated Jade Obelisk listing);
WC-003 Questor Soulsworn also has "Bone" and "Briar" (was matching the
larger "Warcry: Briar and Bone" box set, not this specific warband).

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_warcry_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

# ── Image URL base ────────────────────────────────────────────────────────────
_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# Each tuple:
#   (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'ydrilan-riverblades',
        'WC-001',
        'Ydrilan Riverblades',
        60.00,
        '60120299005_EngWCPyreAndFlood02.jpg',
        'https://www.warhammer.com/en-US/shop/lumineth-realm-lords-ydrilan-riverblades-2025',
        'Warcry Ydrilan Riverblades Warhammer',
    ),
    (
        'jade-obelisk',
        'WC-002',
        'Jade Obelisk',
        60.00,
        '60010299038_WCSunderedFateJadeObeliskLead.jpg',
        'https://www.warhammer.com/en-US/shop/disciples-of-tzeentch-the-jade-obelisk-2025',
        'Warcry Jade Obelisk Warhammer',
    ),
    (
        'questor-soulsworn',
        'WC-003',
        'Questor Soulsworn',
        58.00,
        '60010299040_ENGWCNMQuest3.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-questor-soulsworn-2025',
        'Warcry Questor Soulsworn Warhammer',
    ),
    (
        'pyregheists',
        'WC-004',
        'Pyregheists',
        60.00,
        '60120299005_EngWCPyreAndFlood03.jpg',
        'https://www.warhammer.com/en-US/shop/nighthaunt-pyregheists-2025',
        'Warcry Pyregheists Warhammer',
    ),
    (
        # ebay_negative_keywords='Dice' is set directly on the DB row (not
        # part of this tuple) -- without it, the matcher picks up the
        # companion "Dice Pack" accessory instead of the warband box.
        'hunters-of-huanchi',
        'WC-005',
        'Hunters of Huanchi',
        60.00,
        '60010299038_WCSunderedFateHuntersOfHuanchiLead.jpg',
        'https://www.warhammer.com/en-US/shop/seraphon-hunters-of-huanchi-2025',
        'Warcry Hunters of Huanchi Warhammer',
    ),
    (
        'warcry-chaos-legionnaires',
        'WC-006',
        'Warcry: Chaos Legionnaires',
        65.00,
        '99120201138_WCLegionsLeadnew.jpg',
        'https://www.warhammer.com/en-US/shop/warcry-chaos-legionaires-2022',
        'Warcry Chaos Legionnaires Warhammer',
    ),
]


class Command(BaseCommand):
    """Create Warcry faction and its genuinely-new products, with GW prices."""

    help = (
        'Populates the Warcry faction and its 6 new-to-catalog products with GW '
        'prices. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        category_warcry, cat_created = Category.objects.get_or_create(
            name='Warcry', defaults={'slug': 'warcry'},
        )
        if cat_created:
            self.stdout.write(self.style.SUCCESS('Created category: Warcry'))

        warcry_faction, wc_created = Faction.objects.get_or_create(
            name='Warcry',
            defaults={'category': category_warcry},
        )
        if wc_created:
            self.stdout.write(self.style.SUCCESS('Created faction: Warcry'))
        else:
            if warcry_faction.category_id != category_warcry.id:
                warcry_faction.category = category_warcry
                warcry_faction.save(update_fields=['category'])
            self.stdout.write(f'Found faction: Warcry (pk={warcry_faction.pk})')

        gw_retailer = Retailer.objects.filter(slug='games-workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded. '
                'Run populate_products first.'
            ))

        product_created = 0
        product_updated = 0
        price_created = 0
        price_updated = 0

        for (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_name) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename) if img_filename else ''

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_name,
                    'category': category_warcry,
                    'faction': warcry_faction,
                    'is_active': True,
                    'batch_tag': 'warcry',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {name} [{gw_sku}]')
            if created:
                product_created += 1
            else:
                product_updated += 1

            # ── Seed GW CurrentPrice at MSRP ──────────────────────────────────
            if gw_retailer and gw_url:
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                        'listing_title': name,
                    },
                )
                if p_created:
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_warcry_products complete.\n'
            f'  {len(PRODUCTS)} products processed '
            f'({product_created} created, {product_updated} updated).\n'
            f'  GW prices: {price_created} created, {price_updated} updated.'
        ))
