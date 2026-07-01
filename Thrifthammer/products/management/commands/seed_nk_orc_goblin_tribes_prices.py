"""
Management command: seed_nk_orc_goblin_tribes_prices

Seeds Noble Knight URLs and initial prices for Orc & Goblin Tribes products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_orc_goblin_tribes_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('black-orc-mob', 'Black Orc Mob', None, f'{_NK}/P/2148137856/Black-Orc-Mob{_AFF}', True, False),
    ('goblin-mob', 'Goblin Mob', None, f'{_NK}/P/2148142020/Goblin-Mob{_AFF}', True, False),
    ('goblin-shaman', 'Goblin Shaman', None, f'{_NK}/P/2148141946/Goblin-Shaman{_AFF}', True, False),
    ('goblin-wolf-rider-mob', 'Goblin Wolf Rider Mob', None, f'{_NK}/P/2148137855/Goblin-Wolf-Rider-Mob{_AFF}', True, False),
    ('night-goblin-mob', 'Night Goblin Mob', None, f'{_NK}/P/2148142023/Night-Goblin-Mob{_AFF}', True, False),
    ('orc-boar-boyz-mob', 'Orc Boar Boyz Mob', None, f'{_NK}/P/2148137848/Orc-Boar-Boyz-Mob{_AFF}', True, False),
    ('orc-boar-chariots', 'Orc Boar Chariots', None, f'{_NK}/P/2148137865/Orc-Boar-Chariots{_AFF}', True, False),
    ('orc-bosses', 'Orc Bosses', None, f'{_NK}/P/2148137868/Orc-Bosses{_AFF}', True, False),
    ('orc-boyz-mob', 'Orc Boyz Mob', None, f'{_NK}/P/2148137853/Orc-Boyz-Mob{_AFF}', True, False),
    ('orc-boyz-orc-arrer-boyz-mob', 'Orc Boyz & Orc Arrer Boyz Mobs', None, f'{_NK}/P/2148137852/Orc-Boyz-and-Orc-Arrer-Boyz-Mobs{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Orc & Goblin Tribes. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Orc & Goblin Tribes.')
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
            f'seed_nk_orc_goblin_tribes_prices complete. {created} created, {updated} updated.'
        ))
