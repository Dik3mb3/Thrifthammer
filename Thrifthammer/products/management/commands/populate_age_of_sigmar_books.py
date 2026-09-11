"""
Management command: populate_age_of_sigmar_books

Creates the Age of Sigmar Books batch (Category: Warhammer, under Books and
Novels; Faction: Age of Sigmar Books -- both already created directly
against production, not by this command -- Faction created via one-off
shell command 2026-09-06, sibling to Horus Heresy Series and Warhammer
40,000 Books under the same Category) and seeds their Softback / Hardback
BookFormatPrice rows from Games Workshop.

Sourced from a user-provided "GW Age of Sigmar Books.xlsx" GW storefront
scrape (21 rows). No exclusions this batch -- no Special/Limited/Box Set
editions or art books present. No Paperback+Hardback pairs of the same
title either -- every title here is single-format only in GW's own
listing. Two titles carried no (Paperback)/(Hardback) tag in their own
title text ("Grombrindal: The Legend of the White Dwarf" was completely
untagged; "Yndrasta: The Celestial Spear" was tagged "(Hardcover)") --
format resolved from the GW CDN image-filename prefix (60040=Hardback,
60100=Paperback) and cross-checked against price (both are $30/$21,
matching this batch's other confirmed hardbacks at the same price points).
In-stock status taken directly from the spreadsheet's cart-button column
("Add to Cart" vs "Notify Me") rather than assumed.

Authors and ISBNs were cross-verified via WebSearch against Amazon, Simon &
Schuster (Black Library's US print distributor), Goodreads, and specialty
retailers -- never scraped from warhammer.com directly (bot-detection).
"Grombrindal: The Legend of the White Dwarf" and "War for the Mortal
Realms" are genuine multi-author anthologies/omnibuses -- shown as "Various
Authors" per the same convention used for prior book batches. Two title-
collision traps were caught and avoided during research: "Callis & Toll"
(2024, David Annandale) is a different book from the same-named-characters
"Callis & Toll: The Silver Shard" (2018, Nick Horth); "Grombrindal: The
Legend of the White Dwarf" (2026 anthology) is a different book from
"Grombrindal: Chronicles of the Wanderer" (2022, David Guymer).

Amazon / eBay / Noble Knight / Miniature Market sourcing for these books is
out of scope for this batch -- GW only, US only, matching the rollout order
of every prior book batch.

Safe to run repeatedly (idempotent via update_or_create keyed on gw_sku).

Usage:
    python manage.py populate_age_of_sigmar_books
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from prices.models import BookFormatPrice
from products.models import Category, Faction, Product, Retailer

_GW_CDN = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{}'

SOFTBACK = BookFormatPrice.FORMAT_SOFTBACK
HARDBACK = BookFormatPrice.FORMAT_HARDBACK

BOOKS = [
    {
        'sku': 'BOOK-AOS-001', 'title': 'Bad Loon Rising', 'author': 'Andy Clark',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804073414',
             'url': 'https://www.warhammer.com/en-US/shop/bad-loon-rising-pb-eng-2023',
             'listing_title': 'Bad Loon Rising (Paperback)',
             'image': '60040181874_BadLoonRisingENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-002', 'title': 'Blacktalon', 'author': 'Liane Merciel',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076422',
             'url': 'https://www.warhammer.com/en-US/shop/blacktalon-pb-2024-eng',
             'listing_title': 'Blacktalon (Paperback)',
             'image': '60100281077_BLBlacktalonENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-003', 'title': 'Callis & Toll', 'author': 'David Annandale',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076651',
             'url': 'https://www.warhammer.com/en-US/shop/callis-and-toll-pb-eng-2025',
             'listing_title': 'Callis & Toll (Paperback)',
             'image': '60100281133_BLCallisAndToll01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-004', 'title': 'Darkoath', 'author': 'Chris Thursten',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076811',
             'url': 'https://www.warhammer.com/en-US/shop/age-of-sigmar-darkoath-pb-eng-2025',
             'listing_title': 'Darkoath (Paperback)',
             'image': '60100281244_BLDarkoathENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-005', 'title': 'First Marshal', 'author': 'Evan Dicken',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836092445',
             'url': 'https://www.warhammer.com/en-US/shop/hb-first-marshal-eng-2026',
             'listing_title': 'First Marshal (Hardback)',
             'image': '60040281096_BLFirstMarshalENG2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-006', 'title': 'Gloomspite', 'author': 'Andy Clark',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': False, 'isbn': '9781836093572',
             'url': 'https://www.warhammer.com/en-US/shop/gloomspite-hb-eng-2026',
             'listing_title': 'Gloomspite (Hardback)',
             'image': '60040281230_BLGloomspiteENG2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-007', 'title': "Godeater's Son", 'author': 'Noah Van Nguyen',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781800262836',
             'url': 'https://www.warhammer.com/en-US/shop/godeaters-son-pb-eng-2023',
             'listing_title': "Godeater's Son (Paperback)",
             'image': '60100281322_GodeatersSonENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-008', 'title': 'Gotrek and Maleneth: The Omnibus', 'author': 'Darius Hinks',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781804079669',
             'url': 'https://www.warhammer.com/en-US/shop/pb-gotrek-and-maleneth-the-omnibus-eng-2025',
             'listing_title': 'Gotrek and Maleneth: The Omnibus (Paperback)',
             'image': '60100281199_BLGotrekAndMalenethTheOmnibus.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-009', 'title': "Grombrindal: Ancestor's Burden", 'author': 'Chris Thursten',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836091660',
             'url': 'https://www.warhammer.com/en-US/shop/pb-grombrindal-ancestors-burden-eng-2026',
             'listing_title': "Grombrindal: Ancestor's Burden (Paperback)",
             'image': '60100281247_BLGrombindalAncestorsBurden2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-010', 'title': 'Grombrindal: The Legend of the White Dwarf', 'author': 'Various Authors',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836092759',
             'url': 'https://www.warhammer.com/en-US/shop/grombrindal-legend-of-the-white-dwarf-hb-eng-2026',
             'listing_title': 'Grombrindal: The Legend of the White Dwarf (Hardback)',
             'image': '60040281097_BLGrombrindalTheLegendoftheWhiteDwarfENG2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-011', 'title': 'Lioness of the Parch', 'author': 'Evan Dicken',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': False, 'isbn': '9781804077306',
             'url': 'https://www.warhammer.com/en-US/shop/tahlia-vedra-lioness-of-the-parch-pb-eng-2025',
             'listing_title': 'Lioness of the Parch (Paperback)',
             'image': '60100281203_BLLionessOfTheParchENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-012', 'title': 'Queen of the Rose Throne', 'author': 'Gary Kloster',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836092957',
             'url': 'https://www.warhammer.com/en-US/shop/queen-of-the-rose-throne-pb-eng-2026',
             'listing_title': 'Queen of the Rose Throne (Paperback)',
             'image': '60100281333_BLQueenOfTheRoseThrone2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-013', 'title': 'Skaventide', 'author': 'Gary Kloster',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076934',
             'url': 'https://www.warhammer.com/en-US/shop/age-of-sigmar-skaventide-eng-pb-2024',
             'listing_title': 'Skaventide (Paperback)',
             'image': '60100281087_BLSkaventideEng.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-014', 'title': 'Soulblight Gravelords: Masters of Death', 'author': 'David Annandale',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836090045',
             'url': 'https://www.warhammer.com/en-US/shop/pb-soulblight-gravelords-masters-of-death-eng-2025',
             'listing_title': 'Soulblight Gravelords: Masters of Death (Paperback)',
             'image': '60100281202_BLSBGMastersOfDeath.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-015', 'title': "Starseer's Ruin", 'author': 'Adrian Tchaikovsky',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836094821',
             'url': 'https://www.warhammer.com/en-US/shop/starseers-ruin-pb-eng-2026',
             'listing_title': "Starseer's Ruin (Paperback)",
             'image': '60100281335_BLStarseersRuins2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-016', 'title': 'The Dead Kingdom', 'author': 'John French',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076705',
             'url': 'https://www.warhammer.com/en-US/shop/the-dead-kingdom-pb-eng-2025',
             'listing_title': 'The Dead Kingdom (Paperback)',
             'image': '60100281123_BLTheDeadKingdomENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-017', 'title': 'The Hollow King', 'author': 'John French',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781789996371',
             'url': 'https://www.warhammer.com/en-US/shop/the-hollow-king-pb-2023',
             'listing_title': 'The Hollow King (Paperback)',
             'image': '60100281317_TheHollowKingENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-018', 'title': 'Verminslayer', 'author': 'David Guymer',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804077016',
             'url': 'https://www.warhammer.com/en-US/shop/pb-gotrek-gurnisson-verminslayer-eng-2026',
             'listing_title': 'Verminslayer (Paperback)',
             'image': '60100281330_BLGotrekGurnissonVerminslayer2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-019', 'title': 'War for the Mortal Realms', 'author': 'Various Authors',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781804075524',
             'url': 'https://www.warhammer.com/en-US/shop/war-for-the-mortal-realms-pb-eng-2024',
             'listing_title': 'War for the Mortal Realms (Paperback)',
             'image': '60100281046_BLWarForTheMortalRealms01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-020', 'title': 'Witch Hunters: The Omnibus', 'author': 'Nick Horth & Richard Strachan',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836094005',
             'url': 'https://www.warhammer.com/en-US/shop/witch-hunters-the-omnibus-pb-eng-2026',
             'listing_title': 'Witch Hunters: The Omnibus (Paperback)',
             'image': '60100281334_BLWItchHuntersOmnibus2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-AOS-021', 'title': 'Yndrasta: The Celestial Spear', 'author': 'Noah Van Nguyen',
        'formats': [
            {'format': HARDBACK, 'price': 21.00, 'in_stock': False, 'isbn': '9781804070637',
             'url': 'https://www.warhammer.com/en-US/shop/yndrasta-the-celestial-spear-hb-2023',
             'listing_title': 'Yndrasta: The Celestial Spear (Hardback)',
             'image': '60040281300_BLYndrastaTheCelestialSpear01.jpg'},
        ],
    },
]


class Command(BaseCommand):
    """Create the Age of Sigmar Books batch and seed GW format prices."""

    help = (
        'Populates the Age of Sigmar Books product batch under the '
        'Warhammer (Books and Novels) category, with Softback/Hardback '
        'BookFormatPrice rows sourced from Games Workshop. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category = Category.objects.get(slug='warhammer', parent_category__slug='books-and-novels')
        except Category.DoesNotExist:
            raise CommandError(
                "Category 'Warhammer' (under 'Books and Novels') not found. "
                "It must already exist -- this command does not create categories."
            )

        try:
            faction = Faction.objects.get(slug='age-of-sigmar-books')
        except Faction.DoesNotExist:
            raise CommandError(
                "Faction 'Age of Sigmar Books' not found. "
                "It must already exist -- this command does not create factions."
            )

        gw_retailer = Retailer.objects.filter(name='Games Workshop').filter(is_uk=False).first()
        if not gw_retailer:
            raise CommandError('Games Workshop (US) retailer not found.')

        prod_created = prod_updated = 0
        price_created = price_updated = 0

        for book in BOOKS:
            slug = slugify(book['title'])
            primary_image = _GW_CDN.format(book['formats'][0]['image'])

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
                    'batch_tag': 'age-of-sigmar-books',
                },
            )
            if created:
                prod_created += 1
            else:
                prod_updated += 1

            for fmt in book['formats']:
                _, p_created = BookFormatPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    format=fmt['format'],
                    defaults={
                        'price': fmt['price'],
                        'currency': 'USD',
                        'url': fmt['url'],
                        'listing_title': fmt['listing_title'],
                        'in_stock': fmt['in_stock'],
                        'not_available': False,
                        'is_msrp_source': True,
                        'isbn': fmt['isbn'],
                    },
                )
                if p_created:
                    price_created += 1
                else:
                    price_updated += 1

            self.stdout.write(
                f"  {'Created' if created else 'Updated'}: {book['title']} [{book['sku']}] "
                f"({', '.join(f['format'] for f in book['formats'])})"
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Products: {prod_created} created, {prod_updated} updated. '
            f'BookFormatPrice rows: {price_created} created, {price_updated} updated.'
        ))
