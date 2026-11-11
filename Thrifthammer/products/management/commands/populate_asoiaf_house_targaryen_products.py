"""
Management command: populate_asoiaf_house_targaryen_products

Creates the "House Targaryen" Faction under the "A Song of Ice and Fire
(ASOIAF)" Category and its 14 NEW products, SKUs TARGARYEN-001..TARGARYEN-014
(the numbers follow CMON's own code order: SIF006 first, then SIF601..SIF612 and
SIF615, shown in the trailing comment on every row; the collection has no SIF613
or SIF614).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection page https://cmon-play-us.com/collections/sif-house-targaryen
on 2026-11-11 (the store's products.json answers HTTP 429 to scripted requests,
so the page was read in a normal browser session and checked twice, identical
both times). Like populate_asoiaf_house_bolton_products: product.msrp is CMON's
price, the CMON CurrentPrice row carries the same price plus CMON's real in-stock
flag, and product.gw_url holds the CMON product URL (it drives the "View Official
Listing" button). Out-of-stock items keep their real CMON price with
in_stock=False. No affiliate code is used on CMON links. Product names are CMON's
own "SIF: ..." titles, word for word.

The collection lists 17 products. 14 are created here. The other 3 already exist
under the Neutrals faction (NEUTRALS-011 Stormcrow Mercenaries, 012 Stormcrow
Archers, 013 Stormcrow Dervishes): the Neutrals build owns their SKUs (the
first-built faction owns the SKU), and they are dual-tagged to House Targaryen by
adding this faction to their secondary_factions (done by hand after this command,
not in code), so they show under BOTH factions. No second rows are created.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * Generic English names get a prefix or the house word so other products'
    listings cannot match: "Targaryen Freedmen" (bare "Freedmen" matches a school
    photo), "Ice Fire Mother of Dragons" (bare matches a makeup highlighter),
    "Ice Fire Pit Fighters" (bare matches a novel). Distinctive names stay bare.
  * The three Targaryen Heroes boxes share "Ice Fire Targaryen Heroes", each with
    its own allowed digit and sibling-numeral negatives; Heroes 2 and 3 also
    reject the phrase "Heroes Box Set" (generic unnumbered listings).
  * Unsullied Pikemen, Targaryen Heroes 2 and Targaryen Heroes 3 have NO usable
    US listing today (verified by direct eBay searches): the only listings are
    abroad, used, Secondhand-Shop items sold as-is, or priced above the matcher's
    calculated-shipping ceiling of 125% of msrp (a code rule). No name or negative
    changes that.
  * ebay_allowed_title_words "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule.

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 14 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_house_targaryen_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'House Targaryen'
FACTION_SLUG = 'asoiaf-house-targaryen'
BATCH_TAG = 'asoiaf-house-targaryen'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-targaryen-starter-set', 'TARGARYEN-001', 'SIF: Targaryen Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF006-StarterSet-3DBOX-STANDINGL.png?v=1774898643', 'https://cmon-play-us.com/products/sif-targaryen-starter-set', True, 'Targaryen Starter Set', '&', ''),  # CMON SIF006
    ('sif-dothraki-screamers', 'TARGARYEN-002', 'SIF: Dothraki Screamers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF601-Screamers-LUPRIGHTBOX.png?v=1774365354', 'https://cmon-play-us.com/products/sif-dothraki-screamers', True, 'Dothraki Screamers', '&', ''),  # CMON SIF601
    ('sif-dothraki-veterans', 'TARGARYEN-003', 'SIF: Dothraki Veterans', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF602-Veterans-LUPRIGHTBOX.png?v=1774368231', 'https://cmon-play-us.com/products/sif-dothraki-veterans', True, 'Dothraki Veterans', '&', ''),  # CMON SIF602
    ('sif-dothraki-outriders', 'TARGARYEN-004', 'SIF: Dothraki Outriders', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF603-Outriders-LUPRIGHTBOX.png?v=1774365946', 'https://cmon-play-us.com/products/sif-dothraki-outriders', True, 'Dothraki Outriders', '&', ''),  # CMON SIF603
    ('sif-dothraki-hrakkars', 'TARGARYEN-005', 'SIF: Dothraki Hrakkars', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF604-DothrakiHrakkars-LUPRIGHTBOX.png?v=1774370677', 'https://cmon-play-us.com/products/sif-dothraki-hrakkars', True, 'Dothraki Hrakkars', '&', ''),  # CMON SIF604
    ('sif-freedmen', 'TARGARYEN-006', 'SIF: Freedmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF605-Freedmen-LUPRIGHTBOX.png?v=1774371199', 'https://cmon-play-us.com/products/sif-freedmen', True, 'Targaryen Freedmen', '&', ''),  # CMON SIF605
    ('sif-unsullied-pikemen', 'TARGARYEN-007', 'SIF: Unsullied Pikemen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF606-UnsulliedPikemen-LUPRIGHTBOX.png?v=1774371593', 'https://cmon-play-us.com/products/sif-unsullied-pikemen', True, 'Unsullied Pikemen', '&', ''),  # CMON SIF606
    ('sif-unsullied-swordmasters', 'TARGARYEN-008', 'SIF: Unsullied Swordmasters', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF607-UnsulliedSword-LUPRIGHTBOX.png?v=1774372583', 'https://cmon-play-us.com/products/sif-unsullied-swordmasters', False, 'Unsullied Swordmasters', '&', ''),  # CMON SIF607
    ('sif-mother-of-dragons', 'TARGARYEN-009', 'SIF: Mother of Dragons', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF608-MotherofDragons-LUPRIGHTBOX.png?v=1774373017', 'https://cmon-play-us.com/products/sif-mother-of-dragons', True, 'Ice Fire Mother of Dragons', '&', ''),  # CMON SIF608
    ('sif-targaryen-heroes-1', 'TARGARYEN-010', 'SIF: Targaryen Heroes 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF609-TargaryenHeroes1-LUPRIGHTBOX.png?v=1774378109', 'https://cmon-play-us.com/products/sif-targaryen-heroes-1', True, 'Ice Fire Targaryen Heroes', '& 1', 'II III 2 3'),  # CMON SIF609
    ('sif-targaryen-heroes-2', 'TARGARYEN-011', 'SIF: Targaryen Heroes 2', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF610-TargaryenHeroes2-LUPRIGHTBOX.png?v=1774378792', 'https://cmon-play-us.com/products/sif-targaryen-heroes-2', True, 'Ice Fire Targaryen Heroes', '& 2', 'I III 1 3 "Heroes Box Set"'),  # CMON SIF610
    ('sif-brazen-beasts', 'TARGARYEN-012', 'SIF: Brazen Beasts', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF611-BrazenBeasts-LUPRIGHTBOX.png?v=1774380659', 'https://cmon-play-us.com/products/sif-brazen-beasts', True, 'Brazen Beasts', '&', ''),  # CMON SIF611
    ('sif-pit-fighters', 'TARGARYEN-013', 'SIF: Pit Fighters', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF612-PitFighters-LUPRIGHTBOX.png?v=1774381298', 'https://cmon-play-us.com/products/sif-pit-fighters', False, 'Ice Fire Pit Fighters', '&', ''),  # CMON SIF612
    ('sif-targaryen-heroes-3', 'TARGARYEN-014', 'SIF: Targaryen Heroes 3', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF615-TargaryenHeroes3-LUPRIGHTBOX.png?v=1774381618', 'https://cmon-play-us.com/products/sif-targaryen-heroes-3', True, 'Ice Fire Targaryen Heroes', '& 3', 'I II 1 2 "Heroes Box Set"'),  # CMON SIF615
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
    """Create the House Targaryen faction and its 14 new products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: House Targaryen (TARGARYEN-001 to TARGARYEN-014).'

    def handle(self, *args, **options):
        """Create the faction, the 14 products and their CMON price rows."""
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
