"""
Management command: seed_nk_tomb_kings_of_khemri_prices

Seeds Noble Knight URLs and initial prices for Tomb Kings of Khemri products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_tomb_kings_of_khemri_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-the-war-of-settras-fury', 'Arcane Journal - The War of Settra\'s Fury', None, f'{_NK}/P/2148356761/Arcane-Journal---The-War-of-Settras-Fury{_AFF}', True, False),
    ('arcane-journal-tomb-kings-of-khemri', 'Arcane Journal - Tomb Kings of Khemri', None, f'{_NK}/P/2148110790/Arcane-Journal---Tomb-Kings-of-Khemri{_AFF}', True, False),
    ('khemrian-warsphinx', 'Necrosphinx', None, f'{_NK}/P/2148110824/Necrosphinx{_AFF}', True, False),
    ('liche-priests', 'Liche Priests', None, f'{_NK}/P/2148356768/Liche-Priests{_AFF}', True, False),
    ('necropolis-knights', 'Necropolis Knights & Sepulchral Stalkers', None, f'{_NK}/P/2148110841/Sepulchral-Stalkers{_AFF}', True, False),
    ('necrosphinx', 'Necrosphinx', None, f'{_NK}/P/2148110824/Necrosphinx{_AFF}', True, False),
    ('royal-heralds', 'Royal Heralds', None, f'{_NK}/P/2148356766/Royal-Heralds{_AFF}', True, False),
    ('sepulchral-stalkers', 'Necropolis Knights & Sepulchral Stalkers', None, f'{_NK}/P/2148110841/Sepulchral-Stalkers{_AFF}', True, False),
    ('skeleton-chariots', 'Skeleton Chariots', None, f'{_NK}/P/2148124752/Skeleton-Chariots{_AFF}', True, False),
    ('tomb-guard', 'Tomb Guard', None, f'{_NK}/P/2148110839/Tomb-Guard{_AFF}', True, False),
    ('tomb-king-liche-priest-on-necrolith-bone-dragon', 'Tomb King on Necrolith Bone Dragon', None, f'{_NK}/P/2148123266/Tomb-King-on-Necrolith-Bone-Dragon{_AFF}', True, False),
    ('tomb-kings-skeleton-horsemen-horse-archers', 'Skeleton Horsemen', None, f'{_NK}/P/2148124748/Skeleton-Horsemen{_AFF}', True, False),
    ('tomb-kings-skeleton-warriors-archers', 'Skeleton Warriors/Archers', None, f'{_NK}/P/2148123261/Skeleton-Warriors-Archers{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Tomb Kings of Khemri. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Tomb Kings of Khemri.')
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
            f'seed_nk_tomb_kings_of_khemri_prices complete. {created} created, {updated} updated.'
        ))
