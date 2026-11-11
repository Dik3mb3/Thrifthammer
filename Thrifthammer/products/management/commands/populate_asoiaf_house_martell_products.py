"""
Management command: populate_asoiaf_house_martell_products

Creates the "House Martell" Faction under the "A Song of Ice and Fire
(ASOIAF)" Category and its 12 NEW products, SKUs MARTELL-001..MARTELL-012
(the numbers follow CMON's own code order: SIF007 first, then SIF701..SIF711,
shown in the trailing comment on every row).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection page https://cmon-play-us.com/collections/sif-house-martell
on 2026-11-11 (the store's products.json answers HTTP 429 to scripted requests,
so the page was read in a normal browser session and checked twice, identical
both times; the collection lists 12 products and its page 2 is empty). Like
populate_asoiaf_house_bolton_products: product.msrp is CMON's price, the CMON
CurrentPrice row carries the same price plus CMON's real in-stock flag, and
product.gw_url holds the CMON product URL (it drives the "View Official Listing"
button). Out-of-stock items (Dune Vipers, Starfall Knights) keep their real CMON
price with in_stock=False. No affiliate code is used on CMON links. Product names
are CMON's own "SIF: ..." titles, word for word. Every image is the CMON store's
own box picture (all 12 answer HTTP 200 and each file name matches its unit).

The collection lists 12 products and none of them exists under another faction,
so no dual tags are needed.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * "Martell Spearmen" carries the house word (bare "Spearmen" matches historical
    wargame spearmen). The other unit names are distinctive and stay bare.
  * The two Martell Heroes boxes share "Martell Heroes", each with its own allowed
    digit and sibling-numeral negatives; Heroes 1 also rejects the phrase "Starter
    Set" (a "Starter Set & Martell Heroes Box 1" bundle exists) and Heroes 2 also
    rejects the phrase "Heroes Box Set" (generic unnumbered listings).
  * The Starter Set rejects "CCG" (a Game of Thrones card game starter deck) and
    "Assorted" (an "Assorted ice and fire models ... random boxes" loose lot).
  * Nine products match a US listing today: Starter Set, Spearmen, Sand
    Skirmishers, Sunspear Dervishes, Sunspear Royal Guard, Darkstar Retinue, Heroes
    1, Heroes 2 and Skyreach Bowmen. The other three have NO usable US listing today
    (verified by direct eBay searches by name, by UPC and over every New US listing
    in the game's categories): Dune Vipers only has calculated-shipping listings
    priced above the matcher's calculated-shipping ceiling of 125% of msrp (a code
    rule), Starfall Outriders only exists in Germany, Starfall Knights has none. No
    name or negative changes that.
  * ebay_allowed_title_words "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule.

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 12 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_house_martell_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'House Martell'
FACTION_SLUG = 'asoiaf-house-martell'
BATCH_TAG = 'asoiaf-house-martell'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-martell-starter-set', 'MARTELL-001', 'SIF: Martell Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF007-StarterSet-3DBOX-STANDINGL.png?v=1774888722', 'https://cmon-play-us.com/products/sif-martell-starter-set', True, 'Martell Starter Set', '&', 'CCG Assorted'),  # CMON SIF007
    ('sif-martell-spearmen', 'MARTELL-002', 'SIF: Martell Spearmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF701-Spearmen-LUPRIGHTBOX.png?v=1774385678', 'https://cmon-play-us.com/products/sif-martell-spearmen', True, 'Martell Spearmen', '&', ''),  # CMON SIF701
    ('sif-sand-skirmishers', 'MARTELL-003', 'SIF: Sand Skirmishers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF702-SandSkirmishers-LUPRIGHTBOX.png?v=1774386384', 'https://cmon-play-us.com/products/sif-sand-skirmishers', True, 'Sand Skirmishers', '&', ''),  # CMON SIF702
    ('sif-sunspear-dervishes', 'MARTELL-004', 'SIF: Sunspear Dervishes', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF703-SunspearDervishes-LUPRIGHTBOX.png?v=1774387263', 'https://cmon-play-us.com/products/sif-sunspear-dervishes', True, 'Sunspear Dervishes', '&', ''),  # CMON SIF703
    ('sif-sunspear-royal-guard', 'MARTELL-005', 'SIF: Sunspear Royal Guard', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF704-SunspearRoyalGuard-LUPRIGHTBOX.png?v=1774388111', 'https://cmon-play-us.com/products/sif-sunspear-royal-guard', True, 'Sunspear Royal Guard', '&', ''),  # CMON SIF704
    ('sif-dune-vipers', 'MARTELL-006', 'SIF: Dune Vipers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF705-DuneVipers-LUPRIGHTBOX.png?v=1774460582', 'https://cmon-play-us.com/products/sif-dune-vipers', False, 'Dune Vipers', '&', ''),  # CMON SIF705
    ('sif-starfall-outriders', 'MARTELL-007', 'SIF: Starfall Outriders', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF706-StarfallOutriders-LUPRIGHTBOX.png?v=1774461176', 'https://cmon-play-us.com/products/sif-starfall-outriders', True, 'Starfall Outriders', '&', ''),  # CMON SIF706
    ('sif-starfall-knights', 'MARTELL-008', 'SIF: Starfall Knights', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF707-Starfallknights-LUPRIGHTBOX.png?v=1774461632', 'https://cmon-play-us.com/products/sif-starfall-knights', False, 'Starfall Knights', '&', ''),  # CMON SIF707
    ('sif-darkstar-retinue', 'MARTELL-009', 'SIF: Darkstar Retinue', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF708-Darkstar-LUPRIGHTBOX-FLAT.png?v=1774461976', 'https://cmon-play-us.com/products/sif-darkstar-retinue', True, 'Darkstar Retinue', '&', ''),  # CMON SIF708
    ('sif-martell-heroes-1', 'MARTELL-010', 'SIF: Martell Heroes 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF709-MartellHeroes-LUPRIGHTBOX.png?v=1774462898', 'https://cmon-play-us.com/products/sif-martell-heroes-1', True, 'Martell Heroes', '& 1', 'II III 2 3 "Starter Set"'),  # CMON SIF709
    ('sif-martell-heroes-2', 'MARTELL-011', 'SIF: Martell Heroes 2', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF710-MartellHeroes2-LUPRIGHTBOX.png?v=1774464105', 'https://cmon-play-us.com/products/sif-martell-heroes-2', True, 'Martell Heroes', '& 2', 'I III 1 3 "Heroes Box Set"'),  # CMON SIF710
    ('sif-skyreach-bowmen', 'MARTELL-012', 'SIF: Skyreach Bowmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF711-SkyreachBowmen-LUPRIGHTBOX.png?v=1774465275', 'https://cmon-play-us.com/products/sif-skyreach-bowmen', True, 'Skyreach Bowmen', '&', ''),  # CMON SIF711
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
    """Create the House Martell faction and its 12 new products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: House Martell (MARTELL-001 to MARTELL-012).'

    def handle(self, *args, **options):
        """Create the faction, the 12 products and their CMON price rows."""
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
