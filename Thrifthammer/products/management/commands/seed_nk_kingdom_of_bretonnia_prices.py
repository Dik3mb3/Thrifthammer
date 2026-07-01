"""
Management command: seed_nk_kingdom_of_bretonnia_prices

Seeds Noble Knight URLs and initial prices for Kingdom of Bretonnia products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_kingdom_of_bretonnia_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-kingdom-of-bretonnia', 'Arcane Journal - Kingdom of Bretonnia', None, f'{_NK}/P/2148110792/Arcane-Journal---Kingdom-of-Bretonnia{_AFF}', True, False),
    ('battle-standard-bearer-on-royal-pegasus', 'Battle Standard Bearer on Royal Pegasus', None, f'{_NK}/P/2148320516/Battle-Standard-Bearer-on-Royal-Pegasus{_AFF}', True, False),
    ('knights-of-the-realm-knights-errant', 'Knights of the Realm', None, f'{_NK}/P/2148123272/Knights-of-the-Realm{_AFF}', True, False),
    ('knights-of-the-realm-on-foot', 'Knights of the Realm on Foot', None, f'{_NK}/P/2148124737/Knights-of-the-Realm-on-Foot{_AFF}', True, False),
    ('lord-on-royal-pegasus', 'Lord on Royal Pegasus #1', None, f'{_NK}/P/2148425431/Lord-on-Royal-Pegasus-1{_AFF}', True, False),
    ('men-at-arms', 'Men-at-arms', None, f'{_NK}/P/2148137862/Men-At-Arms{_AFF}', True, False),
    ('peasant-bowmen', 'Peasant Bowmen', None, f'{_NK}/P/2148137860/Peasant-Bowmen{_AFF}', True, False),
    ('pegasus-knights', 'Pegasus Knight', None, f'{_NK}/P/2148110844/Pegasus-Knights{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Kingdom of Bretonnia. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Kingdom of Bretonnia.')
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
            f'seed_nk_kingdom_of_bretonnia_prices complete. {created} created, {updated} updated.'
        ))
