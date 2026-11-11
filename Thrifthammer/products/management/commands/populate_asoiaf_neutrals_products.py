"""
Management command: populate_asoiaf_neutrals_products

Creates the "Neutrals" Faction under the "A Song of Ice and Fire (ASOIAF)"
Category and its 18 NEW products, SKUs NEUTRALS-001..NEUTRALS-018 (the numbers
follow CMON's own code order: SIF005 first, then SIF501..SIF513 and
SIF515..SIF519; the codes are read from CMON's image file names and shown in the
trailing comment on every row; this collection has no SIF506, SIF514 or SIF520).

MSRP/images/URLs come from CMON's own store (cmon-play-us.com), read from the
public collection page https://cmon-play-us.com/collections/sif-neutrals on
2026-11-11 (the store's products.json answered HTTP 429 to scripted requests that
day, so the page was read in a normal browser session instead and checked twice,
identical both times). Like populate_asoiaf_free_folk_products: product.msrp is
CMON's price, the CMON CurrentPrice row carries the same price plus CMON's real
in-stock flag, and product.gw_url holds the CMON product URL (it drives the
"View Official Listing" button). Out-of-stock items keep their real CMON price
with in_stock=False. No affiliate code is used on CMON links. Product names are
CMON's own "SIF: ..." titles, word for word.

The collection lists 19 products. 18 are created here. The 19th, SIF521 Stone
Crows, already exists as LANNISTER-019 (House Lannister); it is NOT created again
and is dual-tagged to Neutrals by adding this faction to its secondary_factions
(done by hand after this command, not in code). Five of the 18 are Bolton house
units (Starter Set, Cutthroats, Bastard's Girls, Flayed Men, Dreadfort
Blackguards): CMON lists them on this page first, so they belong to Neutrals
here and the future House Bolton build dual-tags them.

eBay: every product carries its approved eBay matching text from day one,
because the scheduled eBay runs pick up every active product within hours:
  * ebay_search_name -- the CMON unit name where sellers use it; where sellers
    use a shorter name the shorter one is used ("Bolton Blackguards", because
    sellers never write "Dreadfort" and eBay requires every query word;
    "Zorse Riders"); "Stormcrow" is one word (the two-word spelling finds
    nothing); the three Neutral Heroes boxes share "Ice Fire Neutral Heroes" and
    Hedge Knights gets an "Ice Fire " prefix because its bare words match books
    and T-shirts. Apostrophes are kept ("Bolton Bastard's Girls").
  * ebay_allowed_title_words -- "&" lets the official "A Song of Ice & Fire"
    spelling through the matcher's bundle rule; the numbered Heroes also allow
    their own digit (which keeps the other digits rejected).
  * ebay_negative_keywords -- only the sibling numerals for the three Heroes
    boxes, plus the phrase "Heroes Box Set" on Heroes 2 and 3 as insurance
    against generic unnumbered listings (the picks are identical without it
    today).

Run this ONCE, by hand. It is not in the Procfile. Re-running it would reset
every in-stock flag to the snapshot baked in below; later price/stock changes
are applied by hand from the CMON collection link, never by re-running this.

Slug collision check run against the full Product table before writing --
none of the 18 slugs used here already exist, and no faction or product name
clashes.

Usage:
    python manage.py populate_asoiaf_neutrals_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

CATEGORY_SLUG = 'asoiaf'
RETAILER_SLUG = 'cmon'
FACTION_NAME = 'Neutrals'
FACTION_SLUG = 'asoiaf-neutrals'
BATCH_TAG = 'asoiaf-neutrals'

# (slug, gw_sku, name, msrp, image_url, product_url, in_stock,
#  ebay_search_name, ebay_allowed_title_words, ebay_negative_keywords)
PRODUCTS = [
    ('sif-bolton-starter-set', 'NEUTRALS-001', 'SIF: Bolton Starter Set', decimal.Decimal('129.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF005-StarterSet-3DBOX-STANDINGL.png?v=1774883244', 'https://cmon-play-us.com/products/sif-bolton-starter-set', True, 'Bolton Starter Set', '&', ''),  # CMON SIF005
    ('sif-bolton-cutthroats', 'NEUTRALS-002', 'SIF: Bolton Cutthroats', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF501-BOLTONCUTTHROATS-LUPRIGHTBOX.png?v=1774276323', 'https://cmon-play-us.com/products/sif-bolton-cutthroats', True, 'Bolton Cutthroats', '&', ''),  # CMON SIF501
    ('sif-bolton-bastards-girls', 'NEUTRALS-003', "SIF: Bolton Bastard's Girls", decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF502-BoltonBastardGirls-LUPRIGHTBOX.png?v=1774288107', 'https://cmon-play-us.com/products/sif-bolton-bastards-girls', True, "Bolton Bastard's Girls", '&', ''),  # CMON SIF502
    ('sif-bolton-flayed-men', 'NEUTRALS-004', 'SIF: Bolton Flayed Men', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF503-BOLTONFLAYEDMEN-LUPRIGHTBOX.png?v=1774288409', 'https://cmon-play-us.com/products/sif-bolton-flayed-men', True, 'Bolton Flayed Men', '&', ''),  # CMON SIF503
    ('sif-bolton-dreadfort-blackguards', 'NEUTRALS-005', 'SIF: Bolton Dreadfort Blackguards', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF504-BOLTONBlackguards-LUPRIGHTBOX.png?v=1774289032', 'https://cmon-play-us.com/products/sif-bolton-dreadfort-blackguards', True, 'Bolton Blackguards', '&', ''),  # CMON SIF504
    ('sif-neutral-heroes-1', 'NEUTRALS-006', 'SIF: Neutral Heroes 1', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF505-NeutralHeroes1-LUPRIGHTBOX.png?v=1774289459', 'https://cmon-play-us.com/products/sif-neutral-heroes-1', True, 'Ice Fire Neutral Heroes', '& 1', 'II III 2 3'),  # CMON SIF505
    ('sif-hedge-knights', 'NEUTRALS-007', 'SIF: Hedge Knights', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF507-HedgeKnights-LUPRIGHTBOX.png?v=1774293128', 'https://cmon-play-us.com/products/sif-hedge-knights', True, 'Ice Fire Hedge Knights', '&', ''),  # CMON SIF507
    ('sif-bloody-mummer-skirmishers', 'NEUTRALS-008', 'SIF: Bloody Mummer Skirmishers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF508-BloodyMummer-LUPRIGHTBOX.png?v=1774293460', 'https://cmon-play-us.com/products/sif-bloody-mummer-skirmishers', True, 'Bloody Mummer Skirmishers', '&', ''),  # CMON SIF508
    ('sif-bloody-mummer-zorse-riders', 'NEUTRALS-009', 'SIF: Bloody Mummer Zorse Riders', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF509-ZorseRiders-LUPRIGHTBOX.png?v=1774293827', 'https://cmon-play-us.com/products/sif-bloody-mummer-zorse-riders', True, 'Zorse Riders', '&', ''),  # CMON SIF509
    ('sif-neutral-heroes-2', 'NEUTRALS-010', 'SIF: Neutral Heroes 2', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF510-NeutralHeroes2-LUPRIGHTBOX.png?v=1774294384', 'https://cmon-play-us.com/products/sif-neutral-heroes-2', False, 'Ice Fire Neutral Heroes', '& 2', 'I III 1 3 "Heroes Box Set"'),  # CMON SIF510
    ('sif-stormcrow-mercenaries', 'NEUTRALS-011', 'SIF: Stormcrow Mercenaries', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF511-StormCrowMercenaries-LUPRIGHTBOX.png?v=1774294838', 'https://cmon-play-us.com/products/sif-stormcrow-mercenaries', False, 'Stormcrow Mercenaries', '&', ''),  # CMON SIF511
    ('sif-stormcrow-archers', 'NEUTRALS-012', 'SIF: Stormcrow Archers', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF512-StormCrowArcher-LUPRIGHTBOX.png?v=1774295254', 'https://cmon-play-us.com/products/sif-stormcrow-archers', False, 'Stormcrow Archers', '&', ''),  # CMON SIF512
    ('sif-stormcrow-dervishes', 'NEUTRALS-013', 'SIF: Stormcrow Dervishes', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF513-StormCrowDervishes-LUPRIGHTBOX.png?v=1774295607', 'https://cmon-play-us.com/products/sif-stormcrow-dervishes', True, 'Stormcrow Dervishes', '&', ''),  # CMON SIF513
    ('sif-neutral-heroes-3', 'NEUTRALS-014', 'SIF: Neutral Heroes 3', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF515-Heroes3-LUPRIGHTBOX.png?v=1774295955', 'https://cmon-play-us.com/products/sif-neutral-heroes-3', True, 'Ice Fire Neutral Heroes', '& 3', 'I II 1 2 "Heroes Box Set"'),  # CMON SIF515
    ('sif-golden-company-swordsmen', 'NEUTRALS-015', 'SIF: Golden Company Swordsmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF516-GoldenCompanySwordsmen-LUPRIGHTBOXFLAT.png?v=1774296338', 'https://cmon-play-us.com/products/sif-golden-company-swordsmen', False, 'Golden Company Swordsmen', '&', ''),  # CMON SIF516
    ('sif-golden-company-crossbowmen', 'NEUTRALS-016', 'SIF: Golden Company Crossbowmen', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF517-GoldenCompanyCrossbowmen-LUPRIGHTBOXFLAT.png?v=1774296669', 'https://cmon-play-us.com/products/sif-golden-company-crossbowmen', False, 'Golden Company Crossbowmen', '&', ''),  # CMON SIF517
    ('sif-golden-company-elephants', 'NEUTRALS-017', 'SIF: Golden Company Elephants', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF518-GoldenCompanyElephants-LUPRIGHTBOXFLAT.png?v=1774296995', 'https://cmon-play-us.com/products/sif-golden-company-elephants', True, 'Golden Company Elephants', '&', ''),  # CMON SIF518
    ('sif-lysene-sellswords', 'NEUTRALS-018', 'SIF: Lysene Sellswords', decimal.Decimal('44.99'), 'https://cdn.shopify.com/s/files/1/0899/3895/2508/files/SIF519-LyseneSellswords-LUPRIGHTBOX.png?v=1774297393', 'https://cmon-play-us.com/products/sif-lysene-sellswords', True, 'Lysene Sellswords', '&', ''),  # CMON SIF519
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
    """Create the Neutrals faction and its 18 products with CMON prices."""

    help = 'Populates A Song of Ice and Fire: Neutrals (NEUTRALS-001 to NEUTRALS-018).'

    def handle(self, *args, **options):
        """Create the faction, the 18 products and their CMON price rows."""
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
