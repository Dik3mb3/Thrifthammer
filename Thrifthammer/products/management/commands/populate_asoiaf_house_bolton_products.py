"""
Management command: populate_asoiaf_house_bolton_products

Creates the "House Bolton" Faction under the "A Song of Ice and Fire (ASOIAF)"
Category and its 3 NEW products, SKUs BOLTON-001..BOLTON-003 (the numbers follow
CMON's own code order: SIF506, SIF522, SIF523, shown in the trailing comment on
every row).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection page https://cmon-play-us.com/collections/sif-house-bolton on
2026-11-11 (the store's products.json answers HTTP 429 to scripted requests, so
the page was read in a normal browser session and checked twice, identical both
times). Like populate_asoiaf_neutrals_products: product.msrp is CMON's price, the
CMON CurrentPrice row carries the same price plus CMON's real in-stock flag, and
product.gw_url holds the CMON product URL (it drives the "View Official Listing"
button). No affiliate code is used on CMON links. Product names are CMON's own
"SIF: ..." titles, word for word.

The collection lists 9 products. 3 are created here. The other 6 already exist
under the Neutrals faction (NEUTRALS-001 Bolton Starter Set, 002 Bolton
Cutthroats, 003 Bolton Bastard's Girls, 004 Bolton Flayed Men, 005 Bolton
Dreadfort Blackguards, 006 Neutral Heroes 1): the Neutrals build owns their SKUs
(first-built faction owns the SKU), and they are dual-tagged to House Bolton by
adding this faction to their secondary_factions (done by hand after this command,
not in code), so they show under BOTH factions. No second rows are created.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * Bolton Heroes: "Ice Fire Bolton Heroes", allowed "& 1" (sellers write
    "#1"/"I"/"1"), negatives "II III 2 3". It has NO usable US listing today:
    the only US New listing is Noble Knight's own eBay store item at $79.95 plus
    shipping (178% of msrp), which the matcher's calculated-shipping fallback
    rejects above 125% of msrp (a code rule). No name or negative changes that.
  * Dreadfort Spearmen / Dreadfort Archers: the bare CMON unit names.
  * ebay_allowed_title_words "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule.

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 3 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_house_bolton_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'House Bolton'
FACTION_SLUG = 'asoiaf-house-bolton'
BATCH_TAG = 'asoiaf-house-bolton'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-bolton-heroes', 'BOLTON-001', 'SIF: Bolton Heroes', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF506-BoltonHeroes1-LUPRIGHTBOX.png?v=1774290202', 'https://cmon-play-us.com/products/sif-bolton-heroes', True, 'Ice Fire Bolton Heroes', '& 1', 'II III 2 3'),  # CMON SIF506
    ('sif-dreadfort-spearmen', 'BOLTON-002', 'SIF: Dreadfort Spearmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF522-Spearmen-LUPRIGHTBOX.png?v=1774298566', 'https://cmon-play-us.com/products/sif-dreadfort-spearmen', True, 'Dreadfort Spearmen', '&', ''),  # CMON SIF522
    ('sif-dreadfort-archers', 'BOLTON-003', 'SIF: Dreadfort Archers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF523-Archers-LUPRIGHTBOX.png?v=1774298966', 'https://cmon-play-us.com/products/sif-dreadfort-archers', True, 'Dreadfort Archers', '&', ''),  # CMON SIF523
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
    """Create the House Bolton faction and its 3 new products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: House Bolton (BOLTON-001 to BOLTON-003).'

    def handle(self, *args, **options):
        """Create the faction, the 3 products and their CMON price rows."""
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
