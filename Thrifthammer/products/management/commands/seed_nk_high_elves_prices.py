"""
Management command: seed_nk_high_elves_prices

Seeds Noble Knight URLs and initial prices for High Elves products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_high_elves_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-high-elf-realms', 'Arcane Journal: High Elf Realms', None, f'{_NK}/P/2148304741/Arcane-Journal---High-Elf-Realms{_AFF}', True, False),
    ('dragon-princes-of-caledor', 'Dragon Princes of Caledor', None, f'{_NK}/P/2148296327/Dragon-Princes-of-Caledor{_AFF}', True, False),
    ('eagle-claw-bolt-throwers', 'Eagle-Claw Bolt Throwers', None, f'{_NK}/P/2148336380/Eagle-Claw-Bolt-Throwers{_AFF}', True, False),
    ('ellyrian-reavers', 'Ellyrian Reavers', None, f'{_NK}/P/2148336365/Ellyrian-Reavers{_AFF}', True, False),
    ('elven-spearmen', 'Elven Spearmen', None, f'{_NK}/P/2148296319/Elven-Spearmen{_AFF}', True, False),
    ('flamespyre-phoenix', 'Flamespyre Phoenix', None, f'{_NK}/P/2148336996/Flamespyre-Phoenix{_AFF}', True, False),
    ('great-eagle-of-the-elven-realms', 'Great Eagle of the Elven Realms', None, f'{_NK}/P/2148337026/Great-Eagles-of-the-Elven-Realms-Webstore-Edition{_AFF}', True, False),
    ('handmaiden-of-the-everqueen', 'Handmaiden of the Everqueen', None, f'{_NK}/P/2148336385/Handmaiden-of-the-Everqueen{_AFF}', True, False),
    ('high-elf-lords', 'High Elf Lords', None, f'{_NK}/P/2148291174/High-Elf-Lords{_AFF}', True, False),
    ('high-elf-mages', 'High Elf Mages', None, f'{_NK}/P/2148296329/High-Elf-Mages{_AFF}', True, False),
    ('lord-on-dragon', 'Lord on Dragon', None, f'{_NK}/P/2148299072/Lord-on-Dragon{_AFF}', True, False),
    ('lothern-sea-guard', 'Lothern Sea Guard', None, f'{_NK}/P/2148337014/Lothern-Sea-Guard{_AFF}', True, False),
    ('lothern-skycutter', 'Lothern Skycutter', None, f'{_NK}/P/2147524523/Lothern-Skycutter{_AFF}', True, False),
    ('phoenix-guard', 'Phoenix Guard', None, f'{_NK}/P/2148291162/Phoenix-Guard{_AFF}', True, False),
    ('silver-helms', 'Silver Helms', None, f'{_NK}/P/2148389471/Silver-Helms{_AFF}', True, False),
    ('sisters-of-avelorn', 'Sisters of Avelorn', None, f'{_NK}/P/2148291160/Sisters-of-Avelorn{_AFF}', True, False),
    ('swordmasters-of-hoeth', 'Swordmasters of Hoeth', None, f'{_NK}/P/2148336370/Swordmasters-of-Hoeth{_AFF}', True, False),
    ('white-lions-of-chrace', 'White Lions of Chrace', None, f'{_NK}/P/2148336404/White-Lions-of-Chrace{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for High Elves. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for High Elves.')
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
            f'seed_nk_high_elves_prices complete. {created} created, {updated} updated.'
        ))
