"""
Management command: populate_horus_heresy_books

Creates the first 26 Horus Heresy Series book products (Category: Warhammer,
under Books and Novels; Faction: Horus Heresy Series -- both already created
directly against production, not by this command) and seeds their Softback /
Hardback BookFormatPrice rows from Games Workshop.

Unlike other products, books have no single Product.msrp / Product.gw_url --
price and buy-link vary by format (Softback vs Hardback), and even by which
retailer is the MSRP reference for a given format (GW here; Audible/Amazon
for E-Book/Audio Book once those are sourced). Product.msrp and gw_url are
left blank; each BookFormatPrice row marked is_msrp_source=True is the
reference price for that product+format instead.

Special editions and duplicate lower-priced paperback listings are
intentionally excluded from this batch (Raldoron: Revenant Special Edition
$75, and the old $9.99 False Gods paperback superseded by the $17.99 Horus
Heresy Saga edition).

ISBNs (one per format -- paperback and hardback editions of the same book
have different ISBNs) were cross-verified against 2+ independent sources
(Amazon, Simon & Schuster publisher pages, and specialty retailers) rather
than scraped from GW directly, since warhammer.com's bot-detection blocks
rapid automated access. They exist to drive precise Amazon lookups by ISBN
instead of ambiguous title search, and are shown on the product page.

Amazon / eBay / Noble Knight / Miniature Market sourcing for these books is
out of scope for this batch -- GW only, US only.

Safe to run repeatedly (idempotent via update_or_create keyed on gw_sku).

Usage:
    python manage.py populate_horus_heresy_books
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
        'sku': 'BOOK-HH-001', 'title': 'Echoes of Eternity', 'author': 'Aaron Dembski-Bowden',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781804073605',
             'url': 'https://www.warhammer.com/en-US/shop/siege-of-terra-echoes-of-eternity-pb-eng-2024',
             'listing_title': 'Echoes of Eternity (Paperback) The Horus Heresy: Siege of Terra Book 7',
             'image': '60100181144_BLEchoesOfEternity01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-002', 'title': 'False Gods', 'author': 'Graham McNeill',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093947',
             'url': 'https://www.warhammer.com/en-US/shop/horus-heresy-false-gods-pb-eng-2026',
             'listing_title': 'False Gods (Paperback)',
             'image': '60100181555_BLTHHFalseGods2026.jpg'},
            {'format': HARDBACK, 'price': 35.00, 'in_stock': True, 'isbn': '9781836093626',
             'url': 'https://www.warhammer.com/en-US/shop/the-horus-heresy-saga-false-gods-hb-eng-2026',
             'listing_title': 'False Gods (Hardback)',
             'image': '60040181453_HORUSHERESYSAGAFALSEGODSHBSlipcase.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-003', 'title': 'Flames of Betrayal', 'author': 'Various Authors',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': False, 'isbn': '9781836090212',
             'url': 'https://www.warhammer.com/en-US/shop/flames-of-betrayal-pb-eng-2026',
             'listing_title': 'Flames of Betrayal (Paperback)',
             'image': '60100181547_BLFlamesOfBetrayal2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-004', 'title': 'Fulgrim', 'author': 'Graham McNeill',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': False, 'isbn': '9781849708043',
             'url': 'https://www.warhammer.com/en-US/shop/The-Horus-Heresy-Fulgrim-Paperback-Platinum',
             'listing_title': 'Fulgrim (Paperback) The Horus Heresy Book 5',
             'image': '60100181290_FulgrimENGHB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-005', 'title': 'Galaxy in Flames', 'author': 'Ben Counter',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781849707534',
             'url': 'https://www.warhammer.com/en-US/shop/The-Horus-Heresy-Galaxy-in-Flames',
             'listing_title': 'Galaxy in Flames (Paperback) The Horus Heresy Book 3',
             'image': '60100181297_GalaxyinFlamesENGHB.jpg'},
            {'format': HARDBACK, 'price': 35.00, 'in_stock': True, 'isbn': '9781836094081',
             'url': 'https://www.warhammer.com/en-US/shop/the-horus-heresy-saga-galaxy-in-flames-hb-eng-2026',
             'listing_title': 'Galaxy in Flames (Hardback)',
             'image': '60040181465_BLTHHSagaGalaxyInFlamesENG2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-006', 'title': 'Horus Rising', 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093145',
             'url': 'https://www.warhammer.com/en-US/shop/the-horus-heresy-saga-horus-rising-pb-eng-2026',
             'listing_title': 'Horus Rising (Paperback)',
             'image': '60100181546_HORUSHERESYSAGAHORUSRISINGPB.jpg'},
            {'format': HARDBACK, 'price': 35.00, 'in_stock': True, 'isbn': '9781836092797',
             'url': 'https://www.warhammer.com/en-US/shop/the-horus-heresy-saga-horus-rising-hb-eng-2026',
             'listing_title': 'Horus Rising (Hardback)',
             'image': '60040181434_BlackLibraryHorusRisingENG2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-007', 'title': 'Know No Fear', 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781849701341',
             'url': 'https://www.warhammer.com/en-US/shop/Horus-Heresy-Know-No-Fear',
             'listing_title': 'Know No Fear (Paperback) The Horus Heresy Book 19',
             'image': '60100181166_BLKnownoFearNEW01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-008', 'title': 'Mortis', 'author': 'John French',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781800262461',
             'url': 'https://www.warhammer.com/en-US/shop/horus-heresy-siege-of-terra-mortis-pb-2023-eng',
             'listing_title': 'Mortis (Paperback) The Horus Heresy: Siege of Terra Book 5',
             'image': '60100181806_SoTMortisEngPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-009', 'title': 'Praetorian of Dorn', 'author': 'John French',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781784966423',
             'url': 'https://www.warhammer.com/en-US/shop/Horus-Heresy-Praetorian-Of-Dorn-pb-2018',
             'listing_title': 'Praetorian of Dorn (Paperback) The Horus Heresy Book 39',
             'image': '60100181470_HHPraetorianofDornPB01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-010', 'title': 'Raldoron: Revenant', 'author': 'Guy Haley',
        'formats': [
            {'format': HARDBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836093817',
             'url': 'https://www.warhammer.com/en-US/shop/raldoron-revenant-hb-eng-2026',
             'listing_title': 'Raldoron: Revenant (Hardback)',
             'image': '60040181456_BLRaldoronRevenantENG2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-011', 'title': 'Saturnine', 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781800261136',
             'url': 'https://www.warhammer.com/en-US/shop/siege-of-terra-saturnine-pb-eng-2022',
             'listing_title': 'Saturnine (Paperback) The Horus Heresy: Siege of Terra Book 4',
             'image': '60100181787_SaturnineHHSoTENGAPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-012', 'title': 'Siege of Terra: Era of Ruin', 'author': 'Various Authors',
        'formats': [
            {'format': HARDBACK, 'price': 35.00, 'in_stock': False, 'isbn': '9781800261808',
             'url': 'https://www.warhammer.com/en-US/shop/hb-siege-of-terra-era-of-ruin-eng-2025',
             'listing_title': 'Siege of Terra: Era of Ruin (Hardback)',
             'image': '60040181337_BLSiegeofTerraEraofRuin.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-013', 'title': 'Siege of Terra: The Shattered and the Soulless', 'author': 'Graham McNeill',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836090199',
             'url': 'https://www.warhammer.com/en-US/shop/pb-the-shattered-and-the-soulless-eng-2026',
             'listing_title': 'Siege of Terra: The Shattered and the Soulless (Paperback)',
             'image': '60100181537_BLSiegeOfTerraShatteredAndTheSoulless2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-014', 'title': 'Slaves to Darkness', 'author': 'John French',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781789990263',
             'url': 'https://www.warhammer.com/en-US/shop/Horus-Heresy-Slaves-To-Darkness-PB-2020',
             'listing_title': 'Slaves to Darkness (Paperback) The Horus Heresy Book 51',
             'image': '60100181735_ENGSlavestoDarknessHHAPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-015', 'title': 'Solar War', 'author': 'John French',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781789992908',
             'url': 'https://www.warhammer.com/en-US/shop/Horus-Heresy-The-Solar-War-pb-2020',
             'listing_title': 'Solar War (Paperback) The Horus Heresy: Siege of Terra Book 1',
             'image': '60100181764_ENGSolarWarAPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-016', 'title': 'The End and the Death Volume 1', 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781804076415',
             'url': 'https://www.warhammer.com/en-US/shop/the-end-and-the-death-volume-1-pb-eng-2024',
             'listing_title': 'The End and the Death Volume 1 (Paperback) The Horus Heresy: Siege of Terra Book 8',
             'image': '60100181357_BLTheEndAndTheDeathENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-017', 'title': 'The End and the Death Volume II', 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781804077351',
             'url': 'https://www.warhammer.com/en-US/shop/siege-of-terra-the-end-and-the-death-vol-2-pb-eng-2025',
             'listing_title': 'The End and the Death Volume II (Paperback) The Horus Heresy: Siege of Terra Book 8: Part 2',
             'image': '60100181517_BLEndAndTheDeathVolumeIIENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-018', 'title': 'The End and the Death: Volume III', 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781804074886',
             'url': 'https://www.warhammer.com/en-US/shop/the-end-and-the-death-volume-3-pb-eng-2025',
             'listing_title': 'The End and the Death: Volume III (Paperback) The Horus Heresy: Siege of Terra Book 8',
             'image': '60100181525_BLEndAndTheDeathVolumeIII2025.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-019', 'title': 'The First Heretic', 'author': 'Aaron Dembski-Bowden',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781844168842',
             'url': 'https://www.warhammer.com/en-US/shop/The-Horus-Heresy-The-First-Heretic',
             'listing_title': 'The First Heretic (Paperback) The Horus Heresy Book 14',
             'image': '60100181133_BLTheFirstHereticNEW01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-020', 'title': 'The First Wall', 'author': 'Gav Thorpe',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781800260245',
             'url': 'https://www.warhammer.com/en-US/shop/horus-heresy-sot-the-first-wall-pb-2021',
             'listing_title': 'The First Wall (Paperback) The Horus Heresy: Siege of Terra Book 3',
             'image': '60100181779_FirstWallSoTHHENGAFormat.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-021', 'title': 'The Flight of the Eisenstein', 'author': 'James Swallow',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': False, 'isbn': '9781849708036',
             'url': 'https://www.warhammer.com/en-US/shop/The-Horus-Heresy-Flight-Of-The-Eisenstein-Paperback-Platinum',
             'listing_title': 'The Flight of the Eisenstein (Paperback) The Horus Heresy Book 4',
             'image': '60100181294_TheFlightoftheEisensteinENGHB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-022', 'title': 'The Lost and the Damned', 'author': 'Guy Haley',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781789999341',
             'url': 'https://www.warhammer.com/en-US/shop/Siege-of-Terra-The-Lost-And-The-Damned-PB-2021',
             'listing_title': 'The Lost and the Damned (Paperback) The Horus Heresy: Siege of Terra Book 2',
             'image': '60100181771_LostandtheDamnedENGAPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-023', 'title': 'The Master of Mankind', 'author': 'Aaron Dembski-Bowden',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781784967116',
             'url': 'https://www.warhammer.com/en-US/shop/Horus-Heresy-The-Master-Of-Mankind-2018',
             'listing_title': 'The Master of Mankind (Paperback) The Horus Heresy Book 41',
             'image': '60100181599_MasterofMankindENGAFormatPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-024', 'title': 'Valdor: Birth of the Imperium', 'author': 'Chris Wraight',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781804075104',
             'url': 'https://www.warhammer.com/en-US/shop/valdor-birth-of-the-imperium-pb-eng-2023',
             'listing_title': 'Valdor: Birth of the Imperium (Paperback)',
             'image': '60100181505_BLValdorBirthOfTheImperiumENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-025', 'title': 'Warhawk', 'author': 'Chris Wraight',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781789993875',
             'url': 'https://www.warhammer.com/en-US/shop/siege-of-terra-warhawk-pb-eng-2023',
             'listing_title': 'Warhawk (Paperback) The Horus Heresy: Siege of Terra Book 6',
             'image': '60100181830_BLSoTWarhawkPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-HH-026', 'title': 'Zardu Layak: The Crimson Apostle', 'author': 'Rich McCormick',
        'formats': [
            {'format': HARDBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836093015',
             'url': 'https://www.warhammer.com/en-US/shop/zardu-layek-the-crimson-apostle-hb-eng-2026',
             'listing_title': 'Zardu Layak: The Crimson Apostle (Hardback)',
             'image': '60040181442_BLZarduLayakCrimsonApostole2026.jpg'},
        ],
    },
]


class Command(BaseCommand):
    """Create the first 26 Horus Heresy Series books and seed GW format prices."""

    help = (
        'Populates 26 Horus Heresy Series book products under the Warhammer '
        '(Books and Novels) category, with Softback/Hardback BookFormatPrice '
        'rows sourced from Games Workshop. Idempotent.'
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

        try:
            faction = Faction.objects.get(slug='horus-heresy-series')
        except Faction.DoesNotExist:
            raise CommandError(
                "Faction 'Horus Heresy Series' not found. "
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
                    'batch_tag': 'horus-heresy-books',
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
