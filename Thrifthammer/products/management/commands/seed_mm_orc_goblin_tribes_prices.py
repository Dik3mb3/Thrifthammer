"""
Management command: seed_mm_orc_goblin_tribes_prices

Seeds Miniature Market URLs and initial prices for Orc & Goblin Tribes products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_orc_goblin_tribes_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('black-orc-mob', 'Warhammer The Old World: Orc & Goblin Tribes - Black Orc Mob', None, 'https://www.miniaturemarket.com/warhammer-old-world-orc-goblin-tribes-black-orc-mob-gw-09-13.html', True, False),
    ('goblin-mob', 'Warhammer The Old World: Orc & Goblin Tribes - Goblin Mob', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-orc-goblin-tribes-goblin-mob-gw-09-08.html', True, False),
    ('goblin-shaman', 'Warhammer The Old World: Orc & Goblin Tribes - Goblin Shaman', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-orc-goblin-tribes-goblin-shaman-gw-09-12.html', True, False),
    ('goblin-wolf-rider-mob', 'Warhammer The Old World: Orc & Goblin Tribes - Goblin Wolf Rider Mob', None, 'https://www.miniaturemarket.com/warhammer-old-world-orc-goblin-tribes-goblin-wolf-rider-mob-gw-09-09.html', True, False),
    ('night-goblin-mob', 'Warhammer The Old World: Orc & Goblin Tribes - Night Goblin Mob', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-orc-goblin-tribes-night-goblin-mob-gw-09-10.html', True, False),
    ('orc-boar-boyz-mob', 'Warhammer The Old World: Orc & Goblin Tribes - Orc Boar Boyz Mob', None, 'https://www.miniaturemarket.com/warhammer-old-world-orc-goblin-tribes-orc-boar-boyz-mob-gw-09-06.html', True, False),
    ('orc-boar-chariots', 'Warhammer The Old World: Orc & Goblin Tribes - Orc Boar Chariots', None, 'https://www.miniaturemarket.com/warhammer-old-world-orc-goblin-tribes-orc-boar-chariots-gw-09-07.html', True, False),
    ('orc-bosses', 'Warhammer The Old World: Orc & Goblin Tribes - Orc Bosses', None, 'https://www.miniaturemarket.com/warhammer-old-world-orc-goblin-tribes-orc-bosses-gw-09-01.html', True, False),
    ('orc-boyz-mob', 'Warhammer The Old World: Orc & Goblin Tribes - Orc Boyz Mob', None, 'https://www.miniaturemarket.com/warhammer-old-world-orc-goblin-tribes-orc-boyz-mob-gw-09-02.html', True, False),
    ('orc-boyz-orc-arrer-boyz-mob', 'Warhammer The Old World: Orc & Goblin Tribes - Orc Boyz & Orc Arrer Boyz Mobs', None, 'https://www.miniaturemarket.com/warhammer-old-world-orc-goblin-tribes-orc-boyz-orc-arrer-boyz-mobs-gw-09-03.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Orc & Goblin Tribes. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Orc & Goblin Tribes.')
            return

        from products.models import Product, Retailer
        from prices.models import CurrentPrice

        mm = Retailer.objects.get(name='Miniature Market')
        created = updated = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(slug=slug)
            _, was_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
                defaults={'url': url, 'listing_title': listing_title, 'not_available': not_available},
                create_defaults={'price': price, 'in_stock': in_stock},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_orc_goblin_tribes_prices complete. {created} created, {updated} updated.'
        ))
