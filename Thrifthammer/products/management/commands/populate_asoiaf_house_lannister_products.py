"""
Management command: populate_asoiaf_house_lannister_products

Creates the "House Lannister" Faction under the "A Song of Ice and Fire
(ASOIAF)" Category and its 19 products, SKUs LANNISTER-001..LANNISTER-019 (the
numbers follow CMON's own SKU order, SIF001B first and then SIF201..SIF217 and
SIF521, shown in the trailing comment on every row).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection feed https://cmon-play-us.com/collections/sif-house-lannister
(products.json) on 2026-11-08, exactly like populate_asoiaf_house_stark_products:
product.msrp is CMON's price, the CMON CurrentPrice row carries the same price
plus CMON's real in-stock flag, and product.gw_url holds the CMON product URL
(it drives the "View Official Listing" button). Out-of-stock items keep their
real CMON price with in_stock=False. No affiliate code is used on CMON links.
Product names are CMON's own "SIF: ..." titles, word for word.

"SIF: Stone Crows" (SIF521) is a Neutral unit that CMON lists on the House
Lannister page; it is included with the rest of the page and can be dual-tagged
to other houses later through Product.secondary_factions.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * ebay_search_name -- distinctive units use the bare unit name; generic
    common-word units (Pyromancers, Poor Fellows, Redcloaks, Gold Cloaks, Stone
    Crows, The Mountain's Men, Warrior's Sons) get an "Ice Fire " prefix so other
    games' listings cannot match; apostrophes are kept; the numbered units
    (Heroes 1/2/3, Attachments 1) use "Ice Fire Lannister Heroes/Attachments".
    No game words are used on the distinctive names because sellers write the
    game as "Ice and Fire", "Ice & Fire" or "ASOIAF" about equally often.
  * ebay_allowed_title_words -- "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule; numbered units also allow their
    own digit (which keeps the other digits rejected).
  * ebay_negative_keywords -- only where a sibling product could be confused:
    Roman/Arabic numerals for the numbered units, "Stark" for the Starter Set
    (the two-player Stark vs Lannister box is a different product).

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 19 slugs used here already exist.

Usage:
    python manage.py populate_asoiaf_house_lannister_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'House Lannister'
FACTION_SLUG = 'asoiaf-house-lannister'
BATCH_TAG = 'asoiaf-house-lannister'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-lannister-starter-set', 'LANNISTER-001', 'SIF: Lannister Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF001B-StarterSet-3DBOX-STANDINGL.png?v=1774893693', 'https://cmon-play-us.com/products/sif-lannister-starter-set', False, 'Lannister Starter Set', '&', 'Stark'),  # CMON SIF001B
    ('sif-lannister-guardsmen', 'LANNISTER-002', 'SIF: Lannister Guardsmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF201-LannisterGuardsmen-LUPRIGHTBOX.png?v=1773855950', 'https://cmon-play-us.com/products/sif-lannister-guardsmen', True, 'Lannister Guardsmen', '&', ''),  # CMON SIF201
    ('sif-lannister-halberdiers', 'LANNISTER-003', 'SIF: Lannister Halberdiers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF202-LannisterHalberdiers-LUPRIGHTBOX.png?v=1773856442', 'https://cmon-play-us.com/products/sif-lannister-halberdiers', True, 'Lannister Halberdiers', '&', ''),  # CMON SIF202
    ('sif-the-mountains-men', 'LANNISTER-004', "SIF: The Mountain's Men", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF203-TheMountain_sMen-LUPRIGHTBOX.png?v=1773856826', 'https://cmon-play-us.com/products/sif-the-mountains-men', True, "Ice Fire Mountain's Men", '&', ''),  # CMON SIF203
    ('sif-pyromancers', 'LANNISTER-005', 'SIF: Pyromancers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF204-Pyramonancers-LUPRIGHTBOX.png?v=1773857572', 'https://cmon-play-us.com/products/sif-pyromancers', False, 'Ice Fire Pyromancers', '&', ''),  # CMON SIF204
    ('sif-knights-of-casterly-rock', 'LANNISTER-006', 'SIF: Knights of Casterly Rock', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF205-KnightsofCasterlyRock-LUPRIGHTBOX.png?v=1773858623', 'https://cmon-play-us.com/products/sif-knights-of-casterly-rock', True, 'Knights of Casterly Rock', '&', ''),  # CMON SIF205
    ('sif-lannister-crossbowmen', 'LANNISTER-007', 'SIF: Lannister Crossbowmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF206-LannisterCrossbowmen-LUPRIGHTBOX.png?v=1773858994', 'https://cmon-play-us.com/products/sif-lannister-crossbowmen', False, 'Lannister Crossbowmen', '&', ''),  # CMON SIF206
    ('sif-warriors-sons', 'LANNISTER-008', "SIF: Warrior's Sons", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF207-TheWarriorsSons-LUPRIGHTBOX.png?v=1773860661', 'https://cmon-play-us.com/products/sif-warriors-sons', False, "Ice Fire Warrior's Sons", '&', ''),  # CMON SIF207
    ('sif-poor-fellows', 'LANNISTER-009', 'SIF: Poor Fellows', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF208-PoorFellows-LUPRIGHTBOX.png?v=1773861388', 'https://cmon-play-us.com/products/sif-poor-fellows', False, 'Ice Fire Poor Fellows', '&', ''),  # CMON SIF208
    ('sif-lannister-heroes-1', 'LANNISTER-010', 'SIF: Lannister Heroes 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF209-LannisterHeroes1-LUPRIGHTBOX.png?v=1773862902', 'https://cmon-play-us.com/products/sif-lannister-heroes', True, 'Ice Fire Lannister Heroes', '& 1', 'II III 2 3'),  # CMON SIF209
    ('sif-lannister-heroes-2', 'LANNISTER-011', 'SIF: Lannister Heroes 2', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF210-LannisterHeroes2-LUPRIGHTBOX.png?v=1773940726', 'https://cmon-play-us.com/products/sif-lannister-heroes-2', True, 'Ice Fire Lannister Heroes', '& 2', 'I III 1 3'),  # CMON SIF210
    ('sif-redcloaks', 'LANNISTER-012', 'SIF: Redcloaks', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF211-RedCloaks-LUPRIGHTBOX.png?v=1773941162', 'https://cmon-play-us.com/products/sif-redcloaks', True, 'Ice Fire Redcloaks', '&', ''),  # CMON SIF211
    ('sif-lannisport-city-watch', 'LANNISTER-013', 'SIF: Lannisport City Watch', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF212-LannissportCity-LUPRIGHTBOX.png?v=1773942084', 'https://cmon-play-us.com/products/sif-lannisport-city-watch', False, 'Lannisport City Watch', '&', ''),  # CMON SIF212
    ('sif-casterly-rock-honor-guard', 'LANNISTER-014', 'SIF: Casterly Rock Honor Guard', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF213-CasterlyRockHonorGuard-LUPRIGHTBOXFLAT.png?v=1773943200', 'https://cmon-play-us.com/products/sif-casterly-rock-honor-guard', False, 'Casterly Rock Honor Guard', '&', ''),  # CMON SIF213
    ('sif-clegane-brigands', 'LANNISTER-015', 'SIF: Clegane Brigands', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF214-CleganeBrigands-LUPRIGHTBOX.png?v=1773943591', 'https://cmon-play-us.com/products/sif-clegane-brigands', False, 'Clegane Brigands', '&', ''),  # CMON SIF214
    ('sif-lannister-heroes-3', 'LANNISTER-016', 'SIF: Lannister Heroes 3', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF215_LannisterHeroes3-LUPRIGHTBOXFLAT.png?v=1773944003', 'https://cmon-play-us.com/products/sif-lannister-heroes-3', True, 'Ice Fire Lannister Heroes', '& 3', 'I II 1 2'),  # CMON SIF215
    ('sif-lannister-attachments-1', 'LANNISTER-017', 'SIF: Lannister Attachments 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF216-LannisterAttachments1-LUPRIGHTBOX.png?v=1773944523', 'https://cmon-play-us.com/products/sif-lannister-attachments-1', False, 'Ice Fire Lannister Attachments', '& 1', 'II III 2 3'),  # CMON SIF216
    ('sif-gold-cloaks', 'LANNISTER-018', 'SIF: Gold Cloaks', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF217-GoldCloaks-LUPRIGHTBOX.png?v=1773944828', 'https://cmon-play-us.com/products/sif-gold-cloaks', True, 'Ice Fire Gold Cloaks', '&', ''),  # CMON SIF217
    ('sif-stone-crows', 'LANNISTER-019', 'SIF: Stone Crows', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF521-StoneCrows-LUPRIGHTBOX.png?v=1774297980', 'https://cmon-play-us.com/products/sif-stone-crows', True, 'Ice Fire Stone Crows', '&', ''),  # CMON SIF521
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
    """Create the House Lannister faction and its 19 products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: House Lannister (LANNISTER-001 to LANNISTER-019).'

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
