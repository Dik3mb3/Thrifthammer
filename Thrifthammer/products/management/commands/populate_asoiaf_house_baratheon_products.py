"""
Management command: populate_asoiaf_house_baratheon_products

Creates the "House Baratheon" Faction under the "A Song of Ice and Fire
(ASOIAF)" Category and its 20 NEW products, SKUs BARATHEON-001..BARATHEON-020
(the numbers follow CMON's own code order: SIF008 first, then SIF801..SIF818 and
SIF820, shown in the trailing comment on every row; the collection has no SIF819).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection page https://cmon-play-us.com/collections/sif-house-baratheon
on 2026-11-11 (the store's products.json answers HTTP 429 to scripted requests,
so the page was read in a normal browser session and checked twice, identical
both times). Like populate_asoiaf_house_bolton_products: product.msrp is CMON's
price, the CMON CurrentPrice row carries the same price plus CMON's real in-stock
flag, and product.gw_url holds the CMON product URL (it drives the "View Official
Listing" button). Out-of-stock items keep their real CMON price with
in_stock=False. No affiliate code is used on CMON links. Product names are CMON's
own "SIF: ..." titles, word for word.

Image exception: CMON's own featured picture for SIF809 Baratheon Heroes 1 is the
R'hllor Faithful box (a CMON error). The user supplied the real box art for that
one product, https://www.cmon.com/wp-content/uploads/2023/06/Baratheon-Heroes-I_Avatar.jpg
(read in the browser: it is the "Baratheon Heroes I" box, HTTP 200 image/jpeg).
Every other image is the CMON store's own box picture.

The collection lists 20 products and none of them exists under another faction,
so no dual tags are needed.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * Generic English names get the house word so other products' listings cannot
    match: "Baratheon Rose Knights" (bare matches a watch), "Baratheon Thorn
    Watch" (bare matches diver watches), "Baratheon King's Men" and "Baratheon
    Queen's Men" (bare match a leather wallet, books and DVDs), plus
    "Baratheon Wardens", "Baratheon Sentinels" and "Baratheon Halberdiers".
    Distinctive names stay bare: Stag Knights, Champions of the Stag, R'hllor
    Lightbringers, R'hllor Faithful, Riders of Highgarden, Highgarden Pikemen,
    Crownland Scouts.
  * The four Baratheon Heroes boxes share "Baratheon Heroes", each with its own
    allowed digit and sibling-numeral negatives; Heroes 2, 3 and 4 also reject the
    phrase "Heroes Box Set" (generic unnumbered listings).
  * The Starter Set rejects "CCG" (a Game of Thrones card game Baratheon starter
    deck exists; only the matcher's price floor kept it out).
  * Nine products match a US listing today: Starter Set, Wardens, Sentinels, Stag
    Knights, Heroes 1, Rose Knights, Heroes 3, Halberdiers, Crownland Scouts.
    The other eleven have NO usable US listing today (verified by direct eBay
    searches by name, by CMON code, by the units' own words, by UPC, by seller and
    over every New US "Baratheon" listing): the only listings are abroad, used,
    or Noble Knight Games calculated-shipping rows (Riders of Highgarden,
    Highgarden Pikemen, Attachments) priced above the matcher's calculated-shipping
    ceiling of 125% of msrp (a code rule). No name or negative changes that.
  * ebay_allowed_title_words "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule.

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 20 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_house_baratheon_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'House Baratheon'
FACTION_SLUG = 'asoiaf-house-baratheon'
BATCH_TAG = 'asoiaf-house-baratheon'

# Real box art supplied by the user for SIF809 (CMON's own featured image for
# that product is the R'hllor Faithful box).
HEROES_1_IMAGE = 'https://www.cmon.com/wp-content/uploads/2023/06/Baratheon-Heroes-I_Avatar.jpg'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-baratheon-starter-set', 'BARATHEON-001', 'SIF: Baratheon Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF008-StarterSet-3DBOX-STANDINGL.png?v=1774899001', 'https://cmon-play-us.com/products/sif-baratheon-starter-set', False, 'Baratheon Starter Set', '&', 'CCG'),  # CMON SIF008
    ('sif-baratheon-wardens', 'BARATHEON-002', 'SIF: Baratheon Wardens', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF801-Wardens-LUPRIGHTBOX.png?v=1774465842', 'https://cmon-play-us.com/products/sif-baratheon-wardens', True, 'Baratheon Wardens', '&', ''),  # CMON SIF801
    ('sif-baratheon-sentinels', 'BARATHEON-003', 'SIF: Baratheon Sentinels', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF802-Sentinels-LUPRIGHTBOX.png?v=1774466538', 'https://cmon-play-us.com/products/sif-baratheon-sentinels', True, 'Baratheon Sentinels', '&', ''),  # CMON SIF802
    ('sif-stag-knights', 'BARATHEON-004', 'SIF: Stag Knights', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF803-StagKnights-LUPRIGHTBOX.png?v=1774466962', 'https://cmon-play-us.com/products/sif-stag-knights', False, 'Stag Knights', '&', ''),  # CMON SIF803
    ('sif-champions-of-the-stag', 'BARATHEON-005', 'SIF: Champions of the Stag', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF804-ChampionStag-LUPRIGHTBOX.png?v=1774468077', 'https://cmon-play-us.com/products/sif-champions-of-the-stag', True, 'Champions of the Stag', '&', ''),  # CMON SIF804
    ('sif-kings-men', 'BARATHEON-006', "SIF: King's Men", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF805-KingsMen-LUPRIGHTBOX.png?v=1774468734', 'https://cmon-play-us.com/products/sif-kings-men', True, "Baratheon King's Men", '&', ''),  # CMON SIF805
    ('sif-queens-men', 'BARATHEON-007', "SIF: Queen's Men", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF806-QueensMen-LUPRIGHTBOX.png?v=1774473971', 'https://cmon-play-us.com/products/sif-queens-men', True, "Baratheon Queen's Men", '&', ''),  # CMON SIF806
    ('sif-rhllor-lightbringers', 'BARATHEON-008', "SIF: R'hllor Lightbringers", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF807-RhllorLightbringers-LUPRIGHTBOX.png?v=1774474431', 'https://cmon-play-us.com/products/sif-rhllor-lightbringers', True, "R'hllor Lightbringers", '&', ''),  # CMON SIF807
    ('sif-rhllor-faithful', 'BARATHEON-009', "SIF: R'hllor Faithful", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF808-RhllorFaithful-LUPRIGHTBOX.png?v=1774474794', 'https://cmon-play-us.com/products/sif-rhllor-faithful', False, "R'hllor Faithful", '&', ''),  # CMON SIF808
    ('sif-baratheon-heroes-1', 'BARATHEON-010', 'SIF: Baratheon Heroes 1', decimal.Decimal('44.99'), HEROES_1_IMAGE, 'https://cmon-play-us.com/products/sif-baratheon-heroes-1', True, 'Baratheon Heroes', '& 1', 'II III IV 2 3 4'),  # CMON SIF809
    ('sif-baratheon-heroes-2', 'BARATHEON-011', 'SIF: Baratheon Heroes 2', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF810-BaratheonHeroes2-LUPRIGHTBOX.png?v=1774538956', 'https://cmon-play-us.com/products/sif-baratheon-heroes-2', False, 'Baratheon Heroes', '& 2', 'I III IV 1 3 4 "Heroes Box Set"'),  # CMON SIF810
    ('sif-rose-knights', 'BARATHEON-012', 'SIF: Rose Knights', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF811-RoseKnights-LUPRIGHTBOX.png?v=1774539445', 'https://cmon-play-us.com/products/sif-rose-knights', True, 'Baratheon Rose Knights', '&', ''),  # CMON SIF811
    ('sif-thorn-watch', 'BARATHEON-013', 'SIF: Thorn Watch', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF812-ThornWatch-LUPRIGHTBOX.png?v=1774539978', 'https://cmon-play-us.com/products/sif-thorn-watch', True, 'Baratheon Thorn Watch', '&', ''),  # CMON SIF812
    ('sif-riders-of-highgarden', 'BARATHEON-014', 'SIF: Riders of Highgarden', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF813-RidersOfHighGarden-LUPRIGHTBOX.png?v=1774540391', 'https://cmon-play-us.com/products/sif-riders-of-highgarden', True, 'Riders of Highgarden', '&', ''),  # CMON SIF813
    ('sif-highgarden-pikemen', 'BARATHEON-015', 'SIF: Highgarden Pikemen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF814-Pikemen-LUPRIGHTBOX-Flat.png?v=1774540893', 'https://cmon-play-us.com/products/sif-highgarden-pikemen', False, 'Highgarden Pikemen', '&', ''),  # CMON SIF814
    ('sif-baratheon-heroes-3', 'BARATHEON-016', 'SIF: Baratheon Heroes 3', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF815-BaratheonHeroes3-LUPRIGHTBOX.png?v=1774626766', 'https://cmon-play-us.com/products/sif-baratheon-heroes-3', True, 'Baratheon Heroes', '& 3', 'I II IV 1 2 4 "Heroes Box Set"'),  # CMON SIF815
    ('sif-baratheon-attachments', 'BARATHEON-017', 'SIF: Baratheon Attachments', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF816-Attachments1-LUPRIGHTBOX.png?v=1774633284', 'https://cmon-play-us.com/products/sif-baratheon-attachments', False, 'Baratheon Attachments', '& 1', 'II III 2 3'),  # CMON SIF816
    ('sif-baratheon-halberdiers', 'BARATHEON-018', 'SIF: Baratheon Halberdiers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF817-Halbardiers-LUPRIGHTBOX.png?v=1774633604', 'https://cmon-play-us.com/products/sif-baratheon-halberdiers', True, 'Baratheon Halberdiers', '&', ''),  # CMON SIF817
    ('sif-crownland-scouts', 'BARATHEON-019', 'SIF: Crownland Scouts', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF818-Crownland-LUPRIGHTBOX.png?v=1774634020', 'https://cmon-play-us.com/products/sif-crownland-scouts', True, 'Crownland Scouts', '&', ''),  # CMON SIF818
    ('sif-baratheon-heroes-4', 'BARATHEON-020', 'SIF: Baratheon Heroes 4', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF820-BaratheonHeroes4-LUPRIGHTBOX.png?v=1774635104', 'https://cmon-play-us.com/products/sif-baratheon-heroes-4', True, 'Baratheon Heroes', '& 4', 'I II III 1 2 3 "Heroes Box Set"'),  # CMON SIF820
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
    """Create the House Baratheon faction and its 20 new products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: House Baratheon (BARATHEON-001 to BARATHEON-020).'

    def handle(self, *args, **options):
        """Create the faction, the 20 products and their CMON price rows."""
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
