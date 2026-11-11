"""
Management command: populate_asoiaf_house_greyjoy_products

Creates the "House Greyjoy" Faction under the "A Song of Ice and Fire
(ASOIAF)" Category and its 13 NEW products, SKUs GREYJOY-001..GREYJOY-013
(the numbers follow CMON's own code order: SIF009 first, then SIF901..SIF912,
shown in the trailing comment on every row).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection page https://cmon-play-us.com/collections/sif-house-greyjoy
on 2026-11-11 (the store's products.json answers HTTP 429 to scripted requests,
so the page was read in a normal browser session and checked twice, identical
both times; the collection lists 13 products and has no second page). Like
populate_asoiaf_house_bolton_products: product.msrp is CMON's price, the CMON
CurrentPrice row carries the same price plus CMON's real in-stock flag, and
product.gw_url holds the CMON product URL (it drives the "View Official Listing"
button). Only 4 of the 13 are in stock (Drowned Men, Silenced Men, Stony Shore
Pillagers, Iron Victory Crew); the other 9 keep their real CMON price with
in_stock=False. No affiliate code is used on CMON links. Product names are CMON's
own "SIF: ..." titles, word for word. Every image is the CMON store's own box
picture (all 13 answer HTTP 200, with 13 different file sizes).

The collection lists 13 products and none of them exists under another faction,
so no dual tags are needed.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * "Greyjoy Drowned Men" carries the house word (bare "Drowned Men" matches
    novels and T-shirts); "Greyjoy Ironmakers" and "Greyjoy Silenced Men" do the
    same as a precaution. The other unit names are distinctive and stay bare;
    "Harlaw Reapers" drops the word "House".
  * The two Greyjoy Heroes boxes share "Greyjoy Heroes", each with its own allowed
    digit and sibling-numeral negatives; Heroes 1 also rejects the phrase "Starter
    Set" (starter-set bundles exist) and Heroes 2 also rejects the phrase "Heroes
    Box Set" (generic unnumbered listings).
  * The Starter Set rejects "CCG" (a Game of Thrones card game Greyjoy starter
    deck exists).
  * Eleven products match a US listing today: Starter Set, Reavers, Bowmen,
    Trappers, Harlaw Reapers, Drowned Men, Silenced Men, Heroes 1, Heroes 2, Stony
    Shore Pillagers and Iron Victory Crew. Ironmakers and Blacktyde Chosen have NO
    usable US listing today (verified by direct eBay searches by name, by CMON
    code, by UPC and over every New US listing in the game's categories):
    Ironmakers only has a Noble Knight Games calculated-shipping listing priced
    above the matcher's calculated-shipping ceiling of 125% of msrp (a code rule),
    Blacktyde Chosen only has a used copy. No name or negative changes that.
  * ebay_allowed_title_words "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule.

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 13 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_house_greyjoy_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'House Greyjoy'
FACTION_SLUG = 'asoiaf-house-greyjoy'
BATCH_TAG = 'asoiaf-house-greyjoy'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-greyjoy-starter-set', 'GREYJOY-001', 'SIF: Greyjoy Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF009-StarterSet-3DBOX-STANDINGL.png?v=1774899885', 'https://cmon-play-us.com/products/sif-greyjoy-starter-set', False, 'Greyjoy Starter Set', '&', 'CCG'),  # CMON SIF009
    ('sif-ironborn-reavers', 'GREYJOY-002', 'SIF: Ironborn Reavers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF901-IronbornReavers-LUPRIGHTBOX.png?v=1774641678', 'https://cmon-play-us.com/products/sif-ironborn-reavers', False, 'Ironborn Reavers', '&', ''),  # CMON SIF901
    ('sif-ironborn-bowmen', 'GREYJOY-003', 'SIF: Ironborn Bowmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF902-IronbornBowmen-LUPRIGHTBOX.png?v=1774709987', 'https://cmon-play-us.com/products/sif-ironborn-bowmen', False, 'Ironborn Bowmen', '&', ''),  # CMON SIF902
    ('sif-ironmakers', 'GREYJOY-004', 'SIF: Ironmakers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF903-IronMakers-LUPRIGHTBOX.png?v=1774710349', 'https://cmon-play-us.com/products/sif-ironmakers', False, 'Greyjoy Ironmakers', '&', ''),  # CMON SIF903
    ('sif-ironborn-trappers', 'GREYJOY-005', 'SIF: Ironborn Trappers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF904-Trappers-LUPRIGHTBOX.png?v=1774710666', 'https://cmon-play-us.com/products/sif-ironborn-trappers', False, 'Ironborn Trappers', '&', ''),  # CMON SIF904
    ('sif-house-harlaw-reapers', 'GREYJOY-006', 'SIF: House Harlaw Reapers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF905-HarlawReapers-LUPRIGHTBOX.png?v=1774711026', 'https://cmon-play-us.com/products/sif-house-harlaw-reapers', False, 'Harlaw Reapers', '&', ''),  # CMON SIF905
    ('sif-blacktyde-chosen', 'GREYJOY-007', 'SIF: Blacktyde Chosen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF906-BlacktydeChosen-LUPRIGHTBOX.png?v=1774711850', 'https://cmon-play-us.com/products/sif-blacktyde-chosen', False, 'Blacktyde Chosen', '&', ''),  # CMON SIF906
    ('sif-drowned-men', 'GREYJOY-008', 'SIF: Drowned Men', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF907-DrownedMen-LUPRIGHTBOX.png?v=1774712207', 'https://cmon-play-us.com/products/sif-drowned-men', True, 'Greyjoy Drowned Men', '&', ''),  # CMON SIF907
    ('sif-silenced-men', 'GREYJOY-009', 'SIF: Silenced Men', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF908-SilencedMen-LUPRIGHTBOX.png?v=1774712528', 'https://cmon-play-us.com/products/sif-silenced-men', True, 'Greyjoy Silenced Men', '&', ''),  # CMON SIF908
    ('sif-greyjoy-heroes-1', 'GREYJOY-010', 'SIF: Greyjoy Heroes 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF909-Heroes1-LUPRIGHTBOX.png?v=1774713072', 'https://cmon-play-us.com/products/sif-greyjoy-heroes-1', False, 'Greyjoy Heroes', '& 1', 'II III 2 3 "Starter Set"'),  # CMON SIF909
    ('sif-greyjoy-heroes-2', 'GREYJOY-011', 'SIF: Greyjoy Heroes 2', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF910-GreyjoyHeroes2-LUPRIGHTBOX.png?v=1774713425', 'https://cmon-play-us.com/products/sif-greyjoy-heroes-2', False, 'Greyjoy Heroes', '& 2', 'I III 1 3 "Heroes Box Set"'),  # CMON SIF910
    ('sif-stony-shore-pillagers', 'GREYJOY-012', 'SIF: Stony Shore Pillagers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF911-ShorePillagers-LUPRIGHTBOX.png?v=1774716064', 'https://cmon-play-us.com/products/sif-stony-shore-pillagers', True, 'Stony Shore Pillagers', '&', ''),  # CMON SIF911
    ('sif-iron-victory-crew', 'GREYJOY-013', 'SIF: Iron Victory Crew', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF912-IronVictory-LUPRIGHTBOX.png?v=1774717646', 'https://cmon-play-us.com/products/sif-iron-victory-crew', True, 'Iron Victory Crew', '&', ''),  # CMON SIF912
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
    """Create the House Greyjoy faction and its 13 new products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: House Greyjoy (GREYJOY-001 to GREYJOY-013).'

    def handle(self, *args, **options):
        """Create the faction, the 13 products and their CMON price rows."""
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
