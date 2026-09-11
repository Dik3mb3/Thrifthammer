"""
Management command: seed_nk_horus_heresy_books_prices

Seeds Noble Knight Games BookFormatPrice rows (Paperback/Hardback only,
matching the eBay/Amazon physical-format scope) for the Horus Heresy Series
book batch, sourced from a user-provided spreadsheet cross-referenced
against NK's live site, plus additional direct links the user found that
the spreadsheet and site search both missed.

Unlike eBay (automated matcher only, no manual URLs ever) and like Amazon,
Noble Knight accepts manually-curated URLs -- every URL below was opened
and verified directly (title, author, format, live price/stock) before
being included here, per project convention.

Rows intentionally excluded (no entry -- correctly renders as no NK price,
matching every other retailer's convention: a missing row means no data,
not a fabricated not_available placeholder):
  - Fulgrim, Slaves to Darkness, The First Heretic, The Flight of the
    Eisenstein: NK only has old/expensive collector printings ($48-175),
    not a comparable current retail copy.
  - Valdor: Birth of the Imperium, Warhawk (Paperback): NK's only current
    stock is a single USED copy (no MINT/New option) -- not a fair "new"
    price comparison against GW/Amazon/eBay.
  - Raldoron: Revenant, Siege of Terra: Era of Ruin, The End and the Death:
    Volume III, The First Wall: not carried by NK at all (checked directly).
  - Know No Fear / The End and the Death Vol 2/3 / Warhawk Hardback
    editions: real NK listings exist, but these books are Paperback-only
    in our catalog (GW doesn't sell a hardback edition) -- staying
    Paperback-only per explicit decision, not adding a new format with no
    GW/Amazon/eBay counterpart.

Rows included with in_stock=False, price=None (real listing, currently
unavailable -- kept per explicit instruction rather than treated as "not
carried", since NK does carry the edition, just not in stock right now):
  Echoes of Eternity, Praetorian of Dorn, Know No Fear, Galaxy in Flames
  (Hardback), The End and the Death Vol 2.

Every URL carries the ?awid=1576 affiliate tag (confirmed as the exact
parameter already used on every other Noble Knight CurrentPrice URL in
this codebase).

Not added to the Procfile -- run manually, on demand, same as the other
one-time seed commands introduced for the Books feature.

Usage:
    python manage.py seed_nk_horus_heresy_books_prices
"""

from django.core.management.base import BaseCommand, CommandError

from prices.models import BookFormatPrice
from products.models import Product, Retailer

NK_AWID = '1576'
SOFTBACK = BookFormatPrice.FORMAT_SOFTBACK
HARDBACK = BookFormatPrice.FORMAT_HARDBACK

# (gw_sku, format, listing_title, price, url, in_stock)
# not_available is always False here -- every row is a real, verified NK
# listing for the correct book (title + author confirmed on the live page).
NK_PRICES = [
    ('BOOK-HH-001', SOFTBACK, 'Siege of Terra - Echoes of Eternity',
     None, 'https://www.nobleknight.com/P/2148165880/Siege-of-Terra---Echoes-of-Eternity', False),
    ('BOOK-HH-002', SOFTBACK, 'False Gods',
     16.49, 'https://www.nobleknight.com/P/2148512541/False-Gods', True),
    ('BOOK-HH-003', SOFTBACK, 'Siege of Terra - Flames of Betrayal',
     16.49, 'https://www.nobleknight.com/P/2148493233/Siege-of-Terra---Flames-of-Betrayal', True),
    ('BOOK-HH-005', HARDBACK, 'Horus Heresy, The #3 - Galaxy in Flames',
     None, 'https://www.nobleknight.com/P/2148512550/Horus-Heresy-The-3---Galaxy-in-Flames', False),
    ('BOOK-HH-006', SOFTBACK, 'Horus Heresy, The #1 - Horus Rising',
     16.49, 'https://www.nobleknight.com/P/2148487730/Horus-Heresy-The-1---Horus-Rising', True),
    ('BOOK-HH-007', SOFTBACK, 'Horus Heresy, The #19 - Know No Fear (2019 Printing)',
     None, 'https://www.nobleknight.com/P/2147808871/Horus-Heresy-The-19---Know-No-Fear-2019-Printing', False),
    ('BOOK-HH-008', SOFTBACK, 'Siege of Terra - Mortis',
     9.99, 'https://www.nobleknight.com/P/2148029937/Siege-of-Terra---Mortis', True),
    ('BOOK-HH-009', SOFTBACK, 'Horus Heresy, The #39 - Praetorian of Dorn',
     None, 'https://www.nobleknight.com/P/2147691653/Horus-Heresy-The-39---Praetorian-of-Dorn', False),
    ('BOOK-HH-011', SOFTBACK, 'Siege of Terra - Saturnine (2022 Edition)',
     9.49, 'https://www.nobleknight.com/P/2147961111/Siege-of-Terra---Saturnine-2022-Edition', True),
    ('BOOK-HH-013', SOFTBACK, 'Siege of Terra - The Shattered and the Souless',
     16.49, 'https://www.nobleknight.com/P/2148397970/Siege-of-Terra---The-Shattered-and-the-Souless', True),
    ('BOOK-HH-015', SOFTBACK, 'Siege of Terra - The Solar War',
     9.99, 'https://www.nobleknight.com/P/2147854712/Siege-of-Terra---The-Solar-War', True),
    ('BOOK-HH-016', SOFTBACK, 'Siege of Terra - The End and the Death Vol. 1',
     14.49, 'https://www.nobleknight.com/P/2148192602/Siege-of-Terra---The-End-and-the-Death-Vol-1', True),
    ('BOOK-HH-017', SOFTBACK, 'Siege of Terra - The End and the Death Vol. 2',
     None, 'https://www.nobleknight.com/P/2148327779/Siege-of-Terra---The-End-and-the-Death-Vol-2', False),
    ('BOOK-HH-022', SOFTBACK, 'Siege of Terra - The Lost and the Damned (2021 Edition)',
     9.99, 'https://www.nobleknight.com/P/2147879542/Siege-of-Terra---The-Lost-and-the-Damned-2021-Edition', True),
    ('BOOK-HH-023', SOFTBACK, 'Master of Mankind, The',
     9.99, 'https://www.nobleknight.com/P/2147767642/Master-of-Mankind-The', True),
    ('BOOK-HH-026', HARDBACK, 'Zardu Layak - The Crimson Apostle',
     18.95, 'https://www.nobleknight.com/P/2148451423/Zardu-Layak---The-Crimson-Apostle', True),
]


class Command(BaseCommand):
    """Seed Noble Knight BookFormatPrice rows for the Horus Heresy Series batch."""

    help = 'Seeds verified Noble Knight Games prices for Horus Heresy Series books. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        nk_retailer = Retailer.objects.filter(slug='noble-knight-games').first()
        if not nk_retailer:
            raise CommandError('Noble Knight Games retailer not found.')

        created = updated = 0

        for gw_sku, fmt, listing_title, price, url, in_stock in NK_PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Product not found: {gw_sku}'))
                continue

            affiliate_url = f'{url}?awid={NK_AWID}'

            bfp, was_created = BookFormatPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                format=fmt,
                defaults={
                    'price': price,
                    'currency': 'USD',
                    'url': affiliate_url,
                    'listing_title': listing_title,
                    'in_stock': in_stock,
                    'not_available': False,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

            status = f'${price:.2f}' if price is not None else ('out of stock' if not in_stock else 'in stock, no price')
            self.stdout.write(
                f"  {'Created' if was_created else 'Updated'}: {product.name} ({bfp.get_format_display()}) — {status}"
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {created} created, {updated} updated.'
        ))
