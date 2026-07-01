"""
Management command: seed_nk_empire_of_man_prices

Seeds Noble Knight URLs and initial prices for Empire of Man products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_empire_of_man_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-empire-of-man', 'Arcane Journal - Empire of Man', None, f'{_NK}/P/2148250137/Arcane-Journal---Empire-of-Man{_AFF}', True, False),
    ('cannons-mortars', 'Cannons & Mortars', None, f'{_NK}/P/2148250108/Cannons-and-Mortars{_AFF}', True, False),
    ('commanders-of-the-empire', 'Commanders of the Empire', None, f'{_NK}/P/2148250135/Commanders-of-the-Empire{_AFF}', True, False),
    ('demigryph-knights', 'Demigryph Knights', None, f'{_NK}/P/2148250100/Demigryph-Knights{_AFF}', True, False),
    ('empire-knights', 'Empire Knights', None, f'{_NK}/P/2148250003/Empire-Knights{_AFF}', True, False),
    ('empire-pistoliers', 'Empire Pistoliers', None, f'{_NK}/P/2148250057/Empire-Pistoliers{_AFF}', True, False),
    ('free-company-militia', 'Free Company Militia', None, f'{_NK}/P/2148250033/Free-Company-Militia{_AFF}', True, False),
    ('general-of-the-empire-on-imperial-griffon', 'General of the Empire on Imperial Griffon', None, f'{_NK}/P/2148250090/General-of-the-Empire-on-Imperial-Griffon{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Empire of Man. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Empire of Man.')
            return

        from products.models import Product, Retailer
        from prices.models import CurrentPrice

        nk = Retailer.objects.get(name='Noble Knight Games')
        created = updated = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(slug=slug)
            _, was_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={'url': url, 'listing_title': listing_title, 'not_available': not_available},
                create_defaults={'price': price, 'in_stock': in_stock},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_empire_of_man_prices complete. {created} created, {updated} updated.'
        ))
