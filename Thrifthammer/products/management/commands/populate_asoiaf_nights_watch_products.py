"""
Management command: populate_asoiaf_nights_watch_products

Creates the "Night's Watch" Faction under the "A Song of Ice and Fire
(ASOIAF)" Category and its 15 products, SKUs NIGHTSWATCH-001..NIGHTSWATCH-015
(the numbers follow CMON's own SKU order, SIF002 first and then SIF301..SIF313,
SIF315 and SIF316, shown in the trailing comment on every row; CMON has no
SIF311 or SIF314).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection feed https://cmon-play-us.com/collections/sif-nights-watch
(products.json) on 2026-11-09, exactly like populate_asoiaf_house_lannister_products:
product.msrp is CMON's price, the CMON CurrentPrice row carries the same price
plus CMON's real in-stock flag, and product.gw_url holds the CMON product URL
(it drives the "View Official Listing" button). Out-of-stock items keep their
real CMON price with in_stock=False. No affiliate code is used on CMON links.
Product names are CMON's own "SIF: ..." titles, word for word.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * ebay_search_name -- distinctive units use the bare unit name; generic
    common-word units get a prefix so other products' listings cannot match:
    "Ice Fire " for Sworn Brothers (bare matches a manga) and the Heroes, and
    "Night's Watch " for Ranger Hunters (bare matches elk calls), Conscripts
    (bare matches a book) and Ranger Vanguard (bare matches a military crest).
    Ranger Vanguard is singular because the matcher tests each search word as a
    substring of the title, so the singular form matches "Vanguard" and
    "Vanguards" titles alike. Apostrophes are kept.
  * ebay_allowed_title_words -- "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule; the numbered Heroes and the
    Attachments also allow their own digit (which keeps the other digits
    rejected).
  * ebay_negative_keywords -- only where a sibling product could be confused:
    Roman/Arabic numerals for the three Heroes boxes, plus the phrase
    "Heroes Box Set" on Heroes 2 and 3: generic listings titled "Night's Watch
    Heroes Box Set ... Multilingual Edition" are really Heroes I and would
    otherwise be picked for Heroes 2.

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 15 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_nights_watch_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = "Night's Watch"
FACTION_SLUG = 'asoiaf-nights-watch'
BATCH_TAG = 'asoiaf-nights-watch'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-nights-watch-starter-set', 'NIGHTSWATCH-001', "SIF: Night's Watch Starter Set", decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF002-STARTERSET2-3DBOX-VertL.png?v=1774894542', 'https://cmon-play-us.com/products/sif-nights-watch-starter-set', False, "Night's Watch Starter Set", '&', ''),  # CMON SIF002
    ('sif-sworn-brothers', 'NIGHTSWATCH-002', 'SIF: Sworn Brothers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF301-NightWatchBlackBrothers-LUPRIGHTBOX.png?v=1773950645', 'https://cmon-play-us.com/products/sif-sworn-brothers', False, 'Ice Fire Sworn Brothers', '&', ''),  # CMON SIF301
    ('sif-ranger-trackers', 'NIGHTSWATCH-003', 'SIF: Ranger Trackers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF302-RangerTrackers-LUPRIGHTBOX.png?v=1773951705', 'https://cmon-play-us.com/products/sif-ranger-trackers', True, 'Ranger Trackers', '&', ''),  # CMON SIF302
    ('sif-veterans-of-the-watch', 'NIGHTSWATCH-004', 'SIF: Veterans of the Watch', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF303-VeteransWatch-LUPRIGHTBOX.png?v=1773952151', 'https://cmon-play-us.com/products/sif-veterans-of-the-watch', True, 'Veterans of the Watch', '&', ''),  # CMON SIF303
    ('sif-builder-crossbowmen', 'NIGHTSWATCH-005', 'SIF: Builder Crossbowmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF304-BuilderCrossbowmen-LUPRIGHTBOX.png?v=1773954090', 'https://cmon-play-us.com/products/sif-304-builder-crossbowmen', True, 'Builder Crossbowmen', '&', ''),  # CMON SIF304
    ('sif-ranger-hunters', 'NIGHTSWATCH-006', 'SIF: Ranger Hunters', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF305-RangerHunters-LUPRIGHTBOX.png?v=1773956127', 'https://cmon-play-us.com/products/sif-ranger-hunters', True, "Night's Watch Ranger Hunters", '&', ''),  # CMON SIF305
    ('sif-builder-scorpion-crew', 'NIGHTSWATCH-007', 'SIF: Builder Scorpion Crew', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF306-BuilderScorpionCrew-LUPRIGHTBOX.png?v=1773956435', 'https://cmon-play-us.com/products/sif-builder-scorpion-crew', True, 'Builder Scorpion Crew', '&', ''),  # CMON SIF306
    ('sif-builder-stone-thrower', 'NIGHTSWATCH-008', 'SIF: Builder Stone Thrower', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF307-BuilderStoneThrower-LUPRIGHTBOX.png?v=1773956794', 'https://cmon-play-us.com/products/sif-builder-stone-thrower', False, 'Builder Stone Thrower', '&', ''),  # CMON SIF307
    ('sif-conscripts', 'NIGHTSWATCH-009', 'SIF: Conscripts', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF308-Conscripts-LUPRIGHTBOX.png?v=1773957157', 'https://cmon-play-us.com/products/sif-conscripts', True, "Night's Watch Conscripts", '&', ''),  # CMON SIF308
    ('sif-nights-watch-heroes-1', 'NIGHTSWATCH-010', "SIF: Night's Watch Heroes 1", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF309-NightWatchHeroes1-LUPRIGHTBOX.png?v=1774021755', 'https://cmon-play-us.com/products/sif-nights-watch-heroes-1', True, "Ice Fire Night's Watch Heroes", '& 1', 'II III 2 3'),  # CMON SIF309
    ('sif-nights-watch-heroes-2', 'NIGHTSWATCH-011', "SIF: Night's Watch Heroes 2", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF310-Night_sWatchHeroes2-LUPRIGHTBOX.png?v=1774022289', 'https://cmon-play-us.com/products/sif-nights-watch-heroes-2', True, "Ice Fire Night's Watch Heroes", '& 2', 'I III 1 3 "Heroes Box Set"'),  # CMON SIF310
    ('sif-ranger-vanguards', 'NIGHTSWATCH-012', 'SIF: Ranger Vanguards', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF312-RangerVanguards-LUPRIGHTBOX.png?v=1774023031', 'https://cmon-play-us.com/products/sif-ranger-vanguards', False, "Night's Watch Ranger Vanguard", '&', ''),  # CMON SIF312
    ('sif-shadow-tower-spearmen', 'NIGHTSWATCH-013', 'SIF: Shadow Tower Spearmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF313-ShadowTower-LUPRIGHTBOX.png?v=1774023422', 'https://cmon-play-us.com/products/sif-shadow-tower-spearmen', False, 'Shadow Tower Spearmen', '&', ''),  # CMON SIF313
    ('sif-nights-watch-heroes-3', 'NIGHTSWATCH-014', "SIF: Night's Watch Heroes 3", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF315-Night_sWatchHeroes3-UPRIGHTBOXFLAT.png?v=1774024280', 'https://cmon-play-us.com/products/sif-nights-watch-heroes-3', True, "Ice Fire Night's Watch Heroes", '& 3', 'I II 1 2 "Heroes Box Set"'),  # CMON SIF315
    ('sif-nights-watch-attachments', 'NIGHTSWATCH-015', "SIF: Night's Watch Attachments", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF316-Attachments1-LUPRIGHTBOX.png?v=1774024687', 'https://cmon-play-us.com/products/sif-nights-watch-attachments', True, "Night's Watch Attachments", '& 1', ''),  # CMON SIF316
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
    """Create the Night's Watch faction and its 15 products with CMON prices."""

    help = "Populates A Song of Ice and Fire: Night's Watch (NIGHTSWATCH-001 to NIGHTSWATCH-015)."

    def handle(self, *args, **options):
        """Create the faction, the 15 products and their CMON price rows."""
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
