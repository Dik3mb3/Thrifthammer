"""
Management command: populate_asoiaf_brotherhood_products

Creates the "Brotherhood Without Banners" Faction under the "A Song of Ice and
Fire (ASOIAF)" Category and its 3 products, SKUs BROTHERHOOD-001..BROTHERHOOD-003
(the numbers follow CMON's own code order: SIF010, SIF014, SIF015, shown in the
trailing comment on every row).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection page
https://cmon-play-us.com/collections/sif-brotherhood-without-banners on
2026-11-11 (the store's products.json answers HTTP 429 to scripted requests, so
the page was read in a normal browser session and checked twice, identical both
times). Like populate_asoiaf_house_bolton_products: product.msrp is CMON's price,
the CMON CurrentPrice row carries the same price plus CMON's real in-stock flag,
and product.gw_url holds the CMON product URL (it drives the "View Official
Listing" button). No affiliate code is used on CMON links. Product names are
CMON's own "SIF: ..." titles, word for word.

None of the 3 products appears on any other CMON collection already built, so no
dual tagging is needed.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * Every name keeps the house words ("Brotherhood Without Banners" /
    "Brotherhood Sworn Knights"): shorter names match other games' products
    ("Brotherhood Starter Set" matched a Legend of the Five Rings box,
    "Brotherhood Heroes" a Rum & Bones game).
  * Starter Set has NO usable US listing today. The only real one is a
    German-language edition located in Germany. Two US New listings titled
    "Brotherhood Sworn Knights Starter Set" are really the Sworn Knights box
    (manufacturer part number SIF014) under a mislabelled title; they fail the
    matcher's 50%-of-msrp price floor. The negatives "Heroes" and "Sworn
    Knights" are sibling insurance so a sibling box can never be picked for it.
  * Heroes 1 allows its own digit ("& 1"), rejects the sibling numerals, and
    rejects "Starter" and "Sworn Knights" titles (sibling insurance; the pick is
    identical without them today).
  * ebay_allowed_title_words "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule.

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 3 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_brotherhood_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'Brotherhood Without Banners'
FACTION_SLUG = 'asoiaf-brotherhood-without-banners'
BATCH_TAG = 'asoiaf-brotherhood-without-banners'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-brotherhood-without-banners-starter-set', 'BROTHERHOOD-001', 'SIF: Brotherhood Without Banners Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF010-StarterSet-3DBOX-STANDINGL.png?v=1774900520', 'https://cmon-play-us.com/products/sif-brotherhood-without-banners-starter-set', True, 'Brotherhood Without Banners Starter Set', '&', 'Heroes "Sworn Knights"'),  # CMON SIF010
    ('sif-brotherhood-sworn-knights', 'BROTHERHOOD-002', 'SIF: Brotherhood Sworn Knights', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF014-BwBKnigts-LUPRIGHTBOX_1.png?v=1774717987', 'https://cmon-play-us.com/products/sif-brotherhood-sworn-knights', True, 'Brotherhood Sworn Knights', '&', ''),  # CMON SIF014
    ('sif-brotherhood-without-banners-heroes-1', 'BROTHERHOOD-003', 'SIF: Brotherhood Without Banners Heroes 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF015-BwBHeroes1-LUPRIGHTBOX.png?v=1774718696', 'https://cmon-play-us.com/products/sif-brotherhood-without-banners-heroes-1', True, 'Brotherhood Without Banners Heroes', '& 1', 'II III 2 3 Starter "Sworn Knights"'),  # CMON SIF015
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
    """Create the Brotherhood Without Banners faction and its 3 products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: Brotherhood Without Banners (BROTHERHOOD-001 to BROTHERHOOD-003).'

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
