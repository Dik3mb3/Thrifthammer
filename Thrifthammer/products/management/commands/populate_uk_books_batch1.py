"""
Management command: populate_uk_books_batch1

Creates UK-exclusive Black Library book products (titles found on the GW UK
storefront that have no equivalent product in the catalog yet -- cross-
referenced against the existing US-sourced Books and Novels catalog before
this batch was built) and seeds their Softback/Hardback BookFormatPrice rows
from Games Workshop UK. Spans four existing Faction series under the Books
and Novels category (Warhammer 40,000 Books, Horus Heresy Books, Age of
Sigmar Books, The Old World Books) -- all four already exist, created by
prior US batches; this command does not create factions.

Mirrors populate_horus_heresy_books.py's structure exactly, with two
differences: retailer is games-workshop-uk (not games-workshop), currency
is GBP, and is_msrp_source_uk is set (not is_msrp_source) -- a separate
field with its own database constraint, so this batch can never contend
with or overwrite the US is_msrp_source flag on any product.

Source data (title, price, format, GW UK url, image) is taken directly from
a GW UK storefront scrape the user supplied -- not re-verified via web
search, per the project's book-batch process (Step 3: trust the spreadsheet
for what it already gives you). Author names were researched and confirmed
against Black Library / Amazon / Simon & Schuster / Goodreads for every
title (see conversation), since the spreadsheet didn't include author.

Excluded from this batch, per the project's standing exclusion rule
(Special Edition / Limited Edition / Box Set / Illustrated & Annotated
Edition don't fit the site's format schema and are excluded by default):
    - Helbrecht: Sin of Hope (Special Edition) -- kept the standard Hardback,
      dropped the GBP45 Special Edition variant.
    - Mephiston: The Box Set (Limited Edition) -- no standard Hardback/
      Paperback edition exists for this title, so it has no place in this
      batch at all; dropped entirely rather than mis-mapped into the
      Hardback slot.
Also excluded (not novels, don't fit the Books and Novels author/series
model): "First Founding: Art and Background" and "Warhammer World:
Nottingham -- UK: Book of Dioramas -- Fifth Edition".

ISBNs are NOT yet sourced for this batch (left as '' -- a missing ISBN must
be '', never None, per BookFormatPrice.isbn's NOT NULL constraint). That's a
known, deliberate gap to close in a follow-up pass, not a placeholder value.

Amazon UK / eBay UK / Noble Knight UK sourcing for these books is out of
scope for this batch -- GW UK only.

Safe to run repeatedly (idempotent via update_or_create keyed on gw_sku).

Usage:
    python manage.py populate_uk_books_batch1
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from prices.models import BookFormatPrice
from products.models import Category, Faction, Product, Retailer

SOFTBACK = BookFormatPrice.FORMAT_SOFTBACK
HARDBACK = BookFormatPrice.FORMAT_HARDBACK

# faction_slug values must already exist under the Books and Novels category.
BOOKS = [
    # ── Warhammer 40,000 Books (alphabetical) ──────────────────────────────
    {
        'sku': 'BOOK-40K-073', 'title': 'Ahriman: Eternal', 'author': 'John French',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 8.99, 'in_stock': True, 'isbn': '9781789990812',
             'url': 'https://www.warhammer.com/en-GB/shop/ahriman-eternal-pb-eng-2023',
             'listing_title': 'Ahriman: Eternal (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181825_BLAhrimanEternalENG01.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-074', 'title': 'Carcharodons: Void Exile', 'author': 'Robbie MacNiven',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781836092704',
             'url': 'https://www.warhammer.com/en-GB/shop/carcharadons-void-exile-pb-eng-2026',
             'listing_title': 'Carcharodons: Void Exile (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181538_BLCarcharodonsVoidExile2026.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-075', 'title': 'Daemonhammer', 'author': 'Darius Hinks',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781804077023',
             'url': 'https://www.warhammer.com/en-GB/shop/pb-daemonhammer-eng-2025',
             'listing_title': 'Daemonhammer (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181514_BLDaemonhammerENG2025.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-076', 'title': 'Dawn of Fire: Crusade of Vengeance', 'author': 'Various Authors',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 17.00, 'in_stock': True, 'isbn': '9781804076552',
             'url': 'https://www.warhammer.com/en-GB/shop/dawn-of-fire-crusade-of-vengeance-eng-pb-2026',
             'listing_title': 'Dawn of Fire: Crusade of Vengeance (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181560_BLDawnOfFireCrusadeOfVengeance2026.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-077', 'title': 'Dawn of Fire: The Iron Kingdom Book 5', 'author': 'Nick Kyme',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 8.99, 'in_stock': True, 'isbn': '9781800261150',
             'url': 'https://www.warhammer.com/en-GB/shop/the-iron-kingdom-pb-eng-2023',
             'listing_title': 'Dawn of Fire: The Iron Kingdom Book 5 (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181819_BLIronKingdomENGPB.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-078', 'title': 'Double Eagle', 'author': 'Dan Abnett',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781836091950',
             'url': 'https://www.warhammer.com/en-GB/shop/pb-double-eagle-eng-2025',
             'listing_title': 'Double Eagle (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181530_BLDoubleEagle2025.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-079', 'title': 'Eisenhorn: The Omnibus', 'author': 'Dan Abnett',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 15.00, 'in_stock': True, 'isbn': '9781789990546',
             'url': 'https://www.warhammer.com/en-GB/shop/eisenhorn-the-omnibus-pb-eng-2022',
             'listing_title': 'Eisenhorn: The Omnibus (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181810_EisenhornOmnibusENGPB.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-080', 'title': 'Elemental Council', 'author': 'Noah Van Nguyen',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781836091899',
             'url': 'https://www.warhammer.com/en-GB/shop/pb-elemental-council-eng-2025',
             'listing_title': 'Elemental Council (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181529_BLElementalCouncil2025.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-081', 'title': 'Ghazghkull Thraka: Warlord of Warlords', 'author': 'Denny Flowers',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': HARDBACK, 'price': 22.00, 'in_stock': True, 'isbn': '9781836095460',
             'url': 'https://www.warhammer.com/en-GB/shop/ghazghkull-thraka-warlord-of-warlords-hb-eng-2026',
             'listing_title': 'Ghazghkull Thraka: Warlord of Warlords (Hardback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60040181438_BLGhazghkullThrakaWarlordOfWarlords2026.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        # Special Edition (GBP45) intentionally excluded -- see module docstring.
        'sku': 'BOOK-40K-082', 'title': 'Helbrecht: Sin of Hope', 'author': 'Mike Vincent',
        'faction_slug': 'warhammer-40000-books',
        # Only live eBay UK listing found for this title is the Special
        # Edition (already excluded from this catalog entry, see comment
        # above) -- user-directed negative keyword, confirmed 2026-09-24.
        'ebay_negative_keywords': 'special',
        'formats': [
            {'format': HARDBACK, 'price': 22.00, 'in_stock': True, 'isbn': '9781836094685',
             'url': 'https://www.warhammer.com/en-GB/shop/helbrecht-sin-of-hope-eng-hb-2026',
             'listing_title': 'Helbrecht: Sin of Hope (Hardback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60040181478_BLHelbrechtSinOfHope2026.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-083', 'title': "Hell's Last", 'author': 'Justin D Hill',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781836092025',
             'url': 'https://www.warhammer.com/en-GB/shop/minka-lesk-hells-last-pb-eng-2025',
             'listing_title': "Hell's Last (Paperback)",
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181848_BLHellsLast2025.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-084', 'title': "Inferno! Presents: The Emperor's Finest", 'author': 'Various Authors',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 8.99, 'in_stock': True, 'isbn': '9781800261402',
             'url': 'https://www.warhammer.com/en-GB/shop/inferno-presents-the-emperors-finest-pb-eng-2022',
             'listing_title': "Inferno! Presents: The Emperor's Finest (Paperback)",
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181807_EmperorsFinestInfernoENGPBP.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-085', 'title': 'Master of Rites', 'author': 'Rob Young',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781836093022',
             'url': 'https://www.warhammer.com/en-GB/shop/master-of-rites-eng-pb-2026',
             'listing_title': 'Master of Rites (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181544_BLMasterOfRites2026.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-086', 'title': 'Steel Tread', 'author': 'Andy Clark',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': HARDBACK, 'price': 20.00, 'in_stock': True, 'isbn': '9781836092254',
             'url': 'https://www.warhammer.com/en-GB/shop/steel-tread-hb-eng-2025',
             'listing_title': 'Steel Tread (Hardback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60040181417_BLSteelTread2025.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-40K-087', 'title': 'Word Bearers: The Omnibus', 'author': 'Anthony Reynolds',
        'faction_slug': 'warhammer-40000-books',
        'formats': [
            {'format': SOFTBACK, 'price': 15.00, 'in_stock': True, 'isbn': '9781804075371',
             'url': 'https://www.warhammer.com/en-GB/shop/word-bearers-omnibus-pb-2023',
             'listing_title': 'Word Bearers: The Omnibus (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181846_BLWordBearersENG01.jpg?fm=webp&w=320&h=330'},
        ],
    },
    # ── Horus Heresy Books ──────────────────────────────────────────────────
    {
        'sku': 'BOOK-HH-027', 'title': 'Betrayer', 'author': 'Aaron Dembski-Bowden',
        'faction_slug': 'horus-heresy-books',
        # Bare title "Betrayer" collides with Kharn the Betrayer miniatures
        # and an unrelated true-crime book on eBay UK -- author's surname
        # disambiguates to the one real listing. User-confirmed 2026-09-24.
        'ebay_search_name_uk': 'Betrayer Dembski-Bowden',
        'formats': [
            {'format': SOFTBACK, 'price': 7.99, 'in_stock': True, 'isbn': '9781849704960',
             'url': 'https://www.warhammer.com/en-GB/shop/Horus-Heresy-Betrayer-Legacy-Edition',
             'listing_title': 'Betrayer (Paperback) The Horus Heresy Book 24',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100181242_BLBetrayerNEW01.jpg?fm=webp&w=320&h=330'},
        ],
    },
    # ── Age of Sigmar Books (alphabetical) ──────────────────────────────────
    {
        'sku': 'BOOK-AOS-022', 'title': 'Anvils of the Heldenhammer: The Ancients', 'author': 'Dale Lucas',
        'faction_slug': 'age-of-sigmar-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781836091882',
             'url': 'https://www.warhammer.com/en-GB/shop/anvils-of-the-heldenhammer-the-ancients-pb-eng-2025',
             'listing_title': 'Anvils of the Heldenhammer: The Ancients (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100281329_BLAnvilsOfTheHeldenhammerTheAncientsENG2025.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-AOS-023', 'title': 'Blood of the Godeater', 'author': 'Noah Van Nguyen',
        'faction_slug': 'age-of-sigmar-books',
        'formats': [
            {'format': HARDBACK, 'price': 22.00, 'in_stock': True, 'isbn': '9781836094043',
             'url': 'https://www.warhammer.com/en-GB/shop/blood-of-the-godeater-hb-eng-2026',
             'listing_title': 'Blood of the Godeater (Hardback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60040281098_BLBloodOfTheGodeater2026.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-AOS-024', 'title': 'On the Shoulders of Giants And Other Stories', 'author': 'Various Authors',
        'faction_slug': 'age-of-sigmar-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781836091714',
             'url': 'https://www.warhammer.com/en-GB/shop/on-the-shoulders-of-giants-and-other-stories-pb-eng-2025',
             'listing_title': 'On the Shoulders of Giants And Other Stories (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100281328_BLOnTheShouldersOfGiantsAndOtherStories2025.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-AOS-025', 'title': 'Realmslayer: Legend of the Doomseeker', 'author': 'David Guymer',
        'faction_slug': 'age-of-sigmar-books',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781804076385',
             'url': 'https://www.warhammer.com/en-GB/shop/legend-of-the-doomseeker-pb-eng-2024',
             'listing_title': 'Realmslayer: Legend of the Doomseeker (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100281061_BLLegendOfDoomseekerENG01.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        # User-directed classification; sourced evidence points to The Old World
        # (classic C. L. Werner Mathias Thulmann series) -- kept as Age of
        # Sigmar per explicit instruction. See conversation.
        'sku': 'BOOK-AOS-026', 'title': 'Witch Hunter', 'author': 'C L Werner',
        'faction_slug': 'age-of-sigmar-books',
        'formats': [
            {'format': SOFTBACK, 'price': 7.99, 'in_stock': True, 'isbn': '9781844160716',
             'url': 'https://www.warhammer.com/en-GB/shop/witch-hunter-pb-eng-2022',
             'listing_title': 'Witch Hunter (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100299047_WitchHunterENGAPB.jpg?fm=webp&w=320&h=330'},
        ],
    },
    # ── The Old World Books (alphabetical) ──────────────────────────────────
    {
        'sku': 'BOOK-TOW-003', 'title': 'Gotrek and Felix: The First Omnibus', 'author': 'William King',
        'faction_slug': 'the-old-world-books',
        'formats': [
            {'format': SOFTBACK, 'price': 15.00, 'in_stock': True, 'isbn': '9781784967857',
             'url': 'https://www.warhammer.com/en-GB/shop/Whc-Gotrek-Felix-Volume-1-pb-2018',
             'listing_title': 'Gotrek and Felix: The First Omnibus (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60100281220_GotrekandFelixENGBformatPB.jpg?fm=webp&w=320&h=330'},
        ],
    },
    {
        'sku': 'BOOK-TOW-004', 'title': 'The Sundering', 'author': 'Gav Thorpe',
        'faction_slug': 'the-old-world-books',
        'formats': [
            {'format': SOFTBACK, 'price': 17.00, 'in_stock': True, 'isbn': '9781836094616',
             'url': 'https://www.warhammer.com/en-GB/shop/the-sundering-eng-pb-2026',
             'listing_title': 'The Sundering (Paperback)',
             'image': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60102781006_BLSundering2026.jpg?fm=webp&w=320&h=330'},
        ],
    },
]


class Command(BaseCommand):
    """Create UK-exclusive book products and seed GW UK format prices."""

    help = (
        'Populates UK-exclusive Black Library book products (23 titles across '
        'Warhammer 40,000/Horus Heresy/Age of Sigmar/The Old World Books) with '
        'Softback/Hardback BookFormatPrice rows sourced from Games Workshop UK. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category = Category.objects.get(slug='books-and-novels')
        except Category.DoesNotExist:
            raise CommandError(
                "Category 'Books and Novels' not found. "
                "It must already exist -- this command does not create categories."
            )

        faction_slugs = {b['faction_slug'] for b in BOOKS}
        factions = {}
        for slug in faction_slugs:
            try:
                factions[slug] = Faction.objects.get(slug=slug, category=category)
            except Faction.DoesNotExist:
                raise CommandError(
                    f"Faction '{slug}' not found under Books and Novels. "
                    "It must already exist -- this command does not create factions."
                )

        try:
            gw_uk_retailer = Retailer.objects.get(slug='games-workshop-uk')
        except Retailer.DoesNotExist:
            raise CommandError('Games Workshop UK retailer not found.')

        prod_created = prod_updated = 0
        price_created = price_updated = 0

        for book in BOOKS:
            slug = slugify(book['title'])
            faction = factions[book['faction_slug']]
            primary_image = book['formats'][0]['image']

            product, created = Product.objects.update_or_create(
                gw_sku=book['sku'],
                defaults={
                    'name': book['title'],
                    'slug': slug,
                    'author': book['author'],
                    'category': category,
                    'faction': faction,
                    'image_url': primary_image,
                    'is_active': True,
                    'batch_tag': 'uk-books-batch1',
                    'ebay_negative_keywords': book.get('ebay_negative_keywords', ''),
                    'ebay_search_name_uk': book.get('ebay_search_name_uk', ''),
                },
            )
            if created:
                prod_created += 1
            else:
                prod_updated += 1

            for fmt in book['formats']:
                _, p_created = BookFormatPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_uk_retailer,
                    format=fmt['format'],
                    defaults={
                        'price': fmt['price'],
                        'currency': 'GBP',
                        'url': fmt['url'],
                        'listing_title': fmt['listing_title'],
                        'in_stock': fmt['in_stock'],
                        'not_available': False,
                        'is_msrp_source_uk': True,
                        'isbn': fmt['isbn'],
                    },
                )
                if p_created:
                    price_created += 1
                else:
                    price_updated += 1

            self.stdout.write(
                f"  {'Created' if created else 'Updated'}: {book['title']} [{book['sku']}] "
                f"({', '.join(f['format'] for f in book['formats'])}) -> {faction.name}"
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Products: {prod_created} created, {prod_updated} updated. '
            f'BookFormatPrice rows: {price_created} created, {price_updated} updated.'
        ))
