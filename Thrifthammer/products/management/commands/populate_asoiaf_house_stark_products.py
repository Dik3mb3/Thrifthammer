"""
Management command: populate_asoiaf_house_stark_products

Creates the "House Stark" Faction under the "A Song of Ice and Fire (ASOIAF)"
Category and its 20 products, SKUs STARK-001..STARK-020 (STARK = this house's
own SKU prefix; the numbers follow CMON's own SKU order, SIF001A first and
then SIF101..SIF119, shown in the trailing comment on every row).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection feed https://cmon-play-us.com/collections/sif-house-stark
(products.json) on 2026-11-08. CMON is this category's MSRP retailer, the same
role Steamforged Games plays for Warmachine: product.msrp is CMON's price, the
CMON CurrentPrice row carries the same price plus CMON's real in-stock flag,
and product.gw_url holds the CMON product URL (it drives the "View Official
Listing" button). Out-of-stock items keep their real CMON price with
in_stock=False. No affiliate code is used on CMON links. Product names are
CMON's own "SIF: ..." titles, word for word.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours of
it being created:
  * ebay_search_name -- the unit name as sellers write it (no game words; sellers
    write the game as "Ice and Fire", "Ice & Fire" or "ASOIAF" about equally
    often). The generic/numbered units (Stark Heroes 1/2/3, Stark Attachments 1)
    use "Ice Fire ..." so Marvel/LEGO "Tony Stark" results cannot match.
  * ebay_allowed_title_words -- "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule; numbered units also allow their
    own digit (which keeps the other digits rejected).
  * ebay_negative_keywords -- only where a sibling product could be confused:
    Roman/Arabic numerals for the numbered units, "Lannister" for the Starter
    Set (the two-player Stark vs Lannister box is a different product).

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 20 slugs used here already exist.

Usage:
    python manage.py populate_asoiaf_house_stark_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'House Stark'
FACTION_SLUG = 'asoiaf-house-stark'
BATCH_TAG = 'asoiaf-house-stark'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-stark-starter-set', 'STARK-001', 'SIF: Stark Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF001A-StarterSet-3DBOX-STANDINGL_ee790641-6ed2-4968-932f-e690cd95f2b1.png?v=1774893145', 'https://cmon-play-us.com/products/sif-stark-starter-set', False, 'Stark Starter Set', '&', 'Lannister'),  # CMON SIF001A
    ('sif-stark-sworn-swords', 'STARK-002', 'SIF: Stark Sworn Swords', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF101-StarkSwornSwords-LUPRIGHTBOX.png?v=1774904078', 'https://cmon-play-us.com/products/sif-stark-sworn-swords', True, 'Stark Sworn Swords', '&', ''),  # CMON SIF101
    ('sif-stark-outriders', 'STARK-003', 'SIF: Stark Outriders', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF102-StarkOutriders-LUPRIGHTBOX.png?v=1774904287', 'https://cmon-play-us.com/products/stark-outriders', True, 'Stark Outriders', '&', ''),  # CMON SIF102
    ('sif-umber-berserkers', 'STARK-004', 'SIF: Umber Berserkers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF103-UmberBerserkers-LUPRIGHTBOX.png?v=1774904448', 'https://cmon-play-us.com/products/sif-umber-berserkers', True, 'Umber Berserkers', '&', ''),  # CMON SIF103
    ('sif-umber-greataxes', 'STARK-005', 'SIF: Umber Greataxes', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF104-UmberGreataxes-LUPRIGHTBOX.png?v=1774904881', 'https://cmon-play-us.com/products/sif-umber-greataxes', False, 'Umber Greataxes', '&', ''),  # CMON SIF104
    ('sif-tully-sworn-shields', 'STARK-006', 'SIF: Tully Sworn Shields', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF105-TullySwornShields-LUPRIGHTBOX.png?v=1774905148', 'https://cmon-play-us.com/products/sif-tully-sworn-shields', True, 'Tully Sworn Shields', '&', ''),  # CMON SIF105
    ('sif-stark-bowmen', 'STARK-007', 'SIF: Stark Bowmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF106-StarkLongbowmen-LUPRIGHTBOX.png?v=1774905262', 'https://cmon-play-us.com/products/sif-stark-bowmen', True, 'Stark Bowmen', '&', ''),  # CMON SIF106
    ('sif-crannogman-trackers', 'STARK-008', 'SIF: Crannogman Trackers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF107-CrannogmanTrackers-LUPRIGHTBOX.png?v=1774905381', 'https://cmon-play-us.com/products/sif-crannogman-trackers', False, 'Crannogman Trackers', '&', ''),  # CMON SIF107
    ('sif-tully-cavaliers', 'STARK-009', 'SIF: Tully Cavaliers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF108-TullySwornShields-LUPRIGHTBOX.png?v=1774905629', 'https://cmon-play-us.com/products/sif-tully-cavaliers', False, 'Tully Cavaliers', '&', ''),  # CMON SIF108 (image file name says SwornShields, the picture is the Cavaliers box)
    ('sif-stark-heroes-1', 'STARK-010', 'SIF: Stark Heroes 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF109-StarkHeroes1-LUPRIGHTBOX.png?v=1774905511', 'https://cmon-play-us.com/products/sif-stark-heroes-1', True, 'Ice Fire Stark Heroes', '& 1', 'II III 2 3'),  # CMON SIF109
    ('sif-stark-heroes-2', 'STARK-011', 'SIF: Stark Heroes 2', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF110-StarkHeroes2-LUPRIGHTBOX.png?v=1774905852', 'https://cmon-play-us.com/products/sif-stark-heroes-2', True, 'Ice Fire Stark Heroes', '& 2', 'I III 1 3'),  # CMON SIF110
    ('sif-mormont-she-bears', 'STARK-012', 'SIF: Mormont She-Bears', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF111-MormontSheBears-LUPRIGHTBOX.png?v=1774906045', 'https://cmon-play-us.com/products/sif-mormont-she-bears', True, 'Mormont She-Bears', '&', ''),  # CMON SIF111
    ('sif-mormont-bruisers', 'STARK-013', 'SIF: Mormont Bruisers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF112-MormmontBruisers-LUPRIGHTBOX.png?v=1774906287', 'https://cmon-play-us.com/products/sif-mormont-bruisers', False, 'Mormont Bruisers', '&', ''),  # CMON SIF112
    ('sif-karstark-loyalists', 'STARK-014', 'SIF: Karstark Loyalists', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF113-KarstarkLoyalists-LUPRIGHTBOXFLAT.png?v=1774906481', 'https://cmon-play-us.com/products/sif-karstark-loyalists', True, 'Karstark Loyalists', '&', ''),  # CMON SIF113
    ('sif-karstark-spearmen', 'STARK-015', 'SIF: Karstark Spearmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF114-HouseKarstarkSpearmen-LUPRIGHTBOX.png?v=1774906704', 'https://cmon-play-us.com/products/sif-karstark-spearmen', False, 'Karstark Spearmen', '&', ''),  # CMON SIF114
    ('sif-stark-heroes-3', 'STARK-016', 'SIF: Stark Heroes 3', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF115-StarkHeroes3-LUPRIGHTBOXFLAT.png?v=1774906827', 'https://cmon-play-us.com/products/sif-stark-heroes-3', True, 'Ice Fire Stark Heroes', '& 3', 'I II 1 2'),  # CMON SIF115
    ('sif-stark-attachments-1', 'STARK-017', 'SIF: Stark Attachments 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF116-StarkAttachments1-LUPRIGHTBOX.png?v=1774906988', 'https://cmon-play-us.com/products/sif-stark-attachments-1', True, 'Ice Fire Stark Attachments', '& 1', 'II III 2 3'),  # CMON SIF116
    ('sif-crannogman-bog-devils', 'STARK-018', 'SIF: Crannogman Bog Devils', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF117-BogDevils-LUPRIGHTBOX.png?v=1774907143', 'https://cmon-play-us.com/products/sif-crannogman-bog-devils', True, 'Crannogman Bog Devils', '&', ''),  # CMON SIF117
    ('sif-house-umber-ravagers', 'STARK-019', 'SIF: House Umber Ravagers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF118-UmberRavagers-LUPRIGHTBOX.png?v=1774907247', 'https://cmon-play-us.com/products/sif-house-umber-ravagers', True, 'Umber Ravagers', '&', ''),  # CMON SIF118
    ('sif-winterfell-guards', 'STARK-020', 'SIF: Winterfell Guards', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF119-WinterfellGuards--LUPRIGHTBOX.png?v=1774907560', 'https://cmon-play-us.com/products/sif-winterfell-guards', True, 'Winterfell Guards', '&', ''),  # CMON SIF119
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
    """Create the House Stark faction and its 20 products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: House Stark (STARK-001 to STARK-020).'

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
