"""
Management command: populate_asoiaf_free_folk_products

Creates the "Free Folk" Faction under the "A Song of Ice and Fire (ASOIAF)"
Category and its 19 products, SKUs FREEFOLK-001..FREEFOLK-019 (the numbers
follow CMON's own SKU order, SIF003 first and then SIF401, SIF403..SIF419,
shown in the trailing comment on every row; CMON has no SIF402).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection feed https://cmon-play-us.com/collections/sif-free-folk
(products.json) on 2026-11-09, exactly like populate_asoiaf_nights_watch_products:
product.msrp is CMON's price, the CMON CurrentPrice row carries the same price
plus CMON's real in-stock flag, and product.gw_url holds the CMON product URL
(it drives the "View Official Listing" button). Out-of-stock items keep their
real CMON price with in_stock=False. No affiliate code is used on CMON links.
Product names are CMON's own "SIF: ..." titles, word for word.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * ebay_search_name -- distinctive units use the bare unit name; generic
    common-word units (Savage Giants, War Mammoths, Giant Spear Throwers) get an
    "Ice Fire " prefix as insurance against other games' listings (the picks are
    identical bare or prefixed today); the three Heroes boxes share
    "Ice Fire Free Folk Heroes". Apostrophes are kept ("Harma's Vanguard").
  * ebay_allowed_title_words -- "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule; the numbered Heroes and the
    Attachments also allow their own digit (which keeps the other digits
    rejected).
  * ebay_negative_keywords -- only where a sibling product could be confused:
    Roman/Arabic numerals for the three Heroes boxes, plus the phrase
    "Heroes Box Set" on Heroes 2 and 3: a generic listing titled "Free Folk
    Heroes Box Set CMON" is really Heroes I and would otherwise be picked for
    Heroes 2.
  * Heroes 2 uses the plural "Free Folks": the only real Heroes 2 listing on
    eBay (2026-11-10) is titled "Free Folks Heroes 2 ( II )", and eBay does not
    treat "Folks" as "Folk". No singular-spelled Heroes 2 listing exists today,
    so the plural name costs nothing now. It was applied to prod on 2026-11-11
    at the owner's approval; if that listing sells and a singular-spelled one
    appears, switch the name back to "Ice Fire Free Folk Heroes".

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 19 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_free_folk_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'Free Folk'
FACTION_SLUG = 'asoiaf-free-folk'
BATCH_TAG = 'asoiaf-free-folk'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-free-folk-starter-set', 'FREEFOLK-001', 'SIF: Free Folk Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF003-STARTERSET3-3DBOX-VertL.png?v=1774898350', 'https://cmon-play-us.com/products/sif-free-folk-starter-set', True, 'Free Folk Starter Set', '&', ''),  # CMON SIF003
    ('sif-free-folk-raiders', 'FREEFOLK-002', 'SIF: Free Folk Raiders', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF401-FreefolkRaiders-LUPRIGHTBOX.png?v=1774025186', 'https://cmon-play-us.com/products/sif-free-folk-raiders', True, 'Free Folk Raiders', '&', ''),  # CMON SIF401
    ('sif-free-folk-trappers', 'FREEFOLK-003', 'SIF: Free Folk Trappers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF403-FreefolkTrappers-LUPRIGHTBOX.png?v=1774030773', 'https://cmon-play-us.com/products/sif-free-folk-trappers', False, 'Free Folk Trappers', '&', ''),  # CMON SIF403
    ('sif-thenn-warriors', 'FREEFOLK-004', 'SIF: Thenn Warriors', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF404-ThennWarriors-LUPRIGHTBOX.png?v=1774031476', 'https://cmon-play-us.com/products/sif-thenn-warriors', True, 'Thenn Warriors', '&', ''),  # CMON SIF404
    ('sif-spearwives', 'FREEFOLK-005', 'SIF: Spearwives', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF405-Spearwives-LUPRIGHTBOX.png?v=1774031957', 'https://cmon-play-us.com/products/sif-spearwives', True, 'Spearwives', '&', ''),  # CMON SIF405
    ('sif-savage-giants', 'FREEFOLK-006', 'SIF: Savage Giants', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF406-SavageGiants-LUPRIGHTBOX.png?v=1774033164', 'https://cmon-play-us.com/products/sif-savage-giants', True, 'Ice Fire Savage Giants', '&', ''),  # CMON SIF406
    ('sif-followers-of-bone', 'FREEFOLK-007', 'SIF: Followers of Bone', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF407-FollowersBone-LUPRIGHTBOX.png?v=1774033438', 'https://cmon-play-us.com/products/sif-followers-of-bone', False, 'Followers of Bone', '&', ''),  # CMON SIF407
    ('sif-cave-dweller-savages', 'FREEFOLK-008', 'SIF: Cave Dweller Savages', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF408-CavedwellerSavages-LUPRIGHTBOX.png?v=1774033722', 'https://cmon-play-us.com/products/sif-cave-dweller-savages', False, 'Cave Dweller Savages', '&', ''),  # CMON SIF408
    ('sif-free-folk-heroes-1', 'FREEFOLK-009', 'SIF: Free Folk Heroes 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF409-FreeFolksHeroes1-LUPRIGHTBOX.png?v=1774034097', 'https://cmon-play-us.com/products/sif-free-folk-heroes-1', True, 'Ice Fire Free Folk Heroes', '& 1', 'II III 2 3'),  # CMON SIF409
    ('sif-free-folk-heroes-2', 'FREEFOLK-010', 'SIF: Free Folk Heroes 2', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF410-FreefolkHeroes2-LUPRIGHTBOX.png?v=1774034472', 'https://cmon-play-us.com/products/sif-free-folk-heroes-2', False, 'Ice Fire Free Folks Heroes', '& 2', 'I III 1 3 "Heroes Box Set"'),  # CMON SIF410 (plural "Folks", see the docstring)
    ('sif-frozen-shore-chariots', 'FREEFOLK-011', 'SIF: Frozen Shore Chariots', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF411-FrozenShoreChariots-LUPRIGHTBOX.png?v=1774035775', 'https://cmon-play-us.com/products/sif-frozen-shore-chariots', False, 'Frozen Shore Chariots', '&', ''),  # CMON SIF411
    ('sif-war-mammoths', 'FREEFOLK-012', 'SIF: War Mammoths', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF412-WarMammoths-Box-LUPRIGHTBOX.png?v=1774036040', 'https://cmon-play-us.com/products/sif-war-mammoths', True, 'Ice Fire War Mammoths', '&', ''),  # CMON SIF412
    ('sif-frozen-shore-hunters', 'FREEFOLK-013', 'SIF: Frozen Shore Hunters', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF413-ShoreHunters-LUPRIGHTBOX.png?v=1774036400', 'https://cmon-play-us.com/products/sif-frozen-shore-hunters', True, 'Frozen Shore Hunters', '&', ''),  # CMON SIF413
    ('sif-frozen-shore-bear-riders', 'FREEFOLK-014', 'SIF: Frozen Shore Bear Riders', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF414-FrozenShoreBear-LUPRIGHTBOX.png?v=1774036758', 'https://cmon-play-us.com/products/sif-frozen-shore-bear-riders', True, 'Frozen Shore Bear Riders', '&', ''),  # CMON SIF414
    ('sif-free-folk-heroes-3', 'FREEFOLK-015', 'SIF: Free Folk Heroes 3', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF415-FreefolkHeroes3-LUPRIGHTBOXFLAT.png?v=1774037175', 'https://cmon-play-us.com/products/sif-free-folk-heroes-3', True, 'Ice Fire Free Folk Heroes', '& 3', 'I II 1 2 "Heroes Box Set"'),  # CMON SIF415
    ('sif-free-folk-attachments', 'FREEFOLK-016', 'SIF: Free Folk Attachments', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF416-FreeFolksAttachments1-LUPRIGHTBOX.png?v=1774037484', 'https://cmon-play-us.com/products/sif-free-folk-attachments', True, 'Free Folk Attachments', '& 1', ''),  # CMON SIF416
    ('sif-varamyr-sixskins', 'FREEFOLK-017', 'SIF: Varamyr Sixskins', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF417-VarymyrSixskins-LUPRIGHTBOX.png?v=1774037836', 'https://cmon-play-us.com/products/sif-varamyr-sixskins', True, 'Varamyr Sixskins', '&', ''),  # CMON SIF417
    ('sif-giant-spear-throwers', 'FREEFOLK-018', 'SIF: Giant Spear Throwers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF418-SpearGiant-LUPRIGHTBOX.png?v=1774038167', 'https://cmon-play-us.com/products/sif-giant-spear-throwers', True, 'Ice Fire Giant Spear Throwers', '&', ''),  # CMON SIF418
    ('sif-harmas-vanguard', 'FREEFOLK-019', "SIF: Harma's Vanguard", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF419-HarmasVanguard-LUPRIGHTBOX.png?v=1774038661', 'https://cmon-play-us.com/products/sif-harmas-vanguard', True, "Harma's Vanguard", '&', ''),  # CMON SIF419
]


def _upsert_product(row, category, faction):
    """Create or update one product from a PRODUCTS row; return (product, created)."""
    (slug, gw_sku, name, msrp, image_url, product_url, _in_stock,
     ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords) = row
    return Product.objects.update_or_create(
        slug=slug,
        defaults={
            'gw_sku': gw_sku,
            'name': name,
            'category': category,
            'faction': faction,
            'msrp': msrp,
            'image_url': image_url,
            'gw_url': product_url,
            'ebay_search_name': ebay_search_name,
            'ebay_allowed_title_words': ebay_allowed_title_words,
            'ebay_negative_keywords': ebay_negative_keywords,
            'batch_tag': BATCH_TAG,
            'is_active': True,
        },
    )


def _upsert_cmon_price(product, retailer, row):
    """Create or update the CMON price row for a product; return True if created."""
    msrp, product_url, in_stock = row[3], row[5], row[6]
    _, created = CurrentPrice.objects.update_or_create(
        product=product,
        retailer=retailer,
        defaults={
            'price': msrp,
            'url': product_url,
            'in_stock': in_stock,
            'not_available': False,
        },
    )
    return created


class Command(BaseCommand):
    """Create the Free Folk faction and its 19 products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: Free Folk (FREEFOLK-001 to FREEFOLK-019).'

    def handle(self, *args, **options):
        """Create the faction, the 19 products and their CMON price rows."""
        category = Category.objects.get(slug=CATEGORY_SLUG)
        retailer = Retailer.objects.get(slug=RETAILER_SLUG)

        faction, faction_created = Faction.objects.get_or_create(
            name=FACTION_NAME,
            defaults={'slug': FACTION_SLUG, 'category': category},
        )
        if faction_created:
            self.stdout.write(self.style.SUCCESS(f'Created faction: {FACTION_NAME}'))
        else:
            self.stdout.write(f'Found faction: {FACTION_NAME} (pk={faction.pk})')

        products_created = prices_created = 0
        for row in PRODUCTS:
            product, created = _upsert_product(row, category, faction)
            price_created = _upsert_cmon_price(product, retailer, row)
            products_created += int(created)
            prices_created += int(price_created)
            self.stdout.write(f"  {'Created' if created else 'Updated'}: {row[2]} ({row[1]})")

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Products: {products_created} created, '
            f'{len(PRODUCTS) - products_created} updated. '
            f'CMON prices: {prices_created} created, '
            f'{len(PRODUCTS) - prices_created} updated.'
        ))
