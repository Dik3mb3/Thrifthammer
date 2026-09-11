"""
Management command: populate_the_old_world_books

Creates the The Old World Books batch (Category: Warhammer, under Books and
Novels; Faction: The Old World Books -- both already created directly
against production, not by this command -- Faction created via one-off
shell command 2026-09-09, sibling to Horus Heresy Series, Warhammer 40,000
Books, and Age of Sigmar Books under the same Category) and seeds their
Softback / Hardback BookFormatPrice rows from Games Workshop.

Only 2 novels exist under Warhammer: The Old World on GW's storefront, so no
spreadsheet was used -- both titles' name/price/format/URL/image were
extracted directly from GW's live category page via a real browser session
(https://www.warhammer.com/en-US/plp?series=Warhammer:%20The%20Old%20World),
working around GW's bot-detection that blocks plain WebFetch.

Authors and ISBNs were cross-verified via WebSearch. "The Rise of Nagash"
(Mike Lee, ISBN 9781836092001) is a brand-new 2025 printing -- confirmed via
Amazon, Simon & Schuster's official publisher page, and Walmart, all citing
this exact ISBN for the 2025 edition specifically. "Grudge Bearer" (Gav
Thorpe) is a 2026 reprint of the original 2005 novel; its ISBN could not be
confirmed via GW or Amazon search directly, but two independent specialty
retailers (Your Hobby Place and Hobby Rising) both list this specific 2026
"Warhammer: The Old World Novel" printing (item numbers GW-60100299077 and
GWBL3283 respectively) under UPC 9781844161973 -- the same ISBN as the 2005
original printing, indicating Black Library reused the original ISBN for
this reprint rather than issuing a new one. Cross-verified via 2 independent
retailer sources for the current product before use.

Amazon / eBay / Noble Knight / Miniature Market sourcing for these books is
out of scope for this batch -- GW only, US only, matching the rollout order
of every prior book batch.

Safe to run repeatedly (idempotent via update_or_create keyed on gw_sku).

Usage:
    python manage.py populate_the_old_world_books
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
        'sku': 'BOOK-TOW-001', 'title': 'Grudge Bearer', 'author': 'Gav Thorpe',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781844161973',
             'url': 'https://www.warhammer.com/en-US/shop/grudge-bearer-pb-eng-2026',
             'listing_title': 'Grudge Bearer (Paperback)',
             'image': '60100299077_BLGrudeBearer2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-TOW-002', 'title': 'The Rise of Nagash', 'author': 'Mike Lee',
        'formats': [
            {'format': SOFTBACK, 'price': 25.00, 'in_stock': True, 'isbn': '9781836092001',
             'url': 'https://www.warhammer.com/en-US/shop/pb-the-rise-of-nagash-eng-2025',
             'listing_title': 'The Rise of Nagash (Paperback)',
             'image': '60102781005_BLRiseOfNagash2025.jpg'},
        ],
    },
]


class Command(BaseCommand):
    """Create the The Old World Books batch and seed GW format prices."""

    help = (
        'Populates the The Old World Books product batch under the '
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
            faction = Faction.objects.get(slug='the-old-world-books')
        except Faction.DoesNotExist:
            raise CommandError(
                "Faction 'The Old World Books' not found. "
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
                    'batch_tag': 'the-old-world-books',
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
