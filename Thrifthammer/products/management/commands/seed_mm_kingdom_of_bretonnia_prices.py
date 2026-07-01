"""
Management command: seed_mm_kingdom_of_bretonnia_prices

Seeds Miniature Market URLs and initial prices for Kingdom of Bretonnia products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_kingdom_of_bretonnia_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-kingdom-of-bretonnia', 'Warhammer The Old World: Arcane Journal - Kingdom of Bretonnia', None, 'https://www.miniaturemarket.com/warhammer-old-world-arcane-journal-kingdom-bretonnia-gw-06-17.html', True, False),
    ('battle-standard-bearer-on-royal-pegasus', 'Warhammer The Old World: Kingdom of Bretonnia - Battle Standard on Royal Pegasus', None, 'https://www.miniaturemarket.com/warhammer-old-world-kingdom-bretonnia-battle-standard-on-royal-pegasus-gw-06-07.html', True, False),
    ('knights-of-the-realm-knights-errant', 'Warhammer The Old World: Kingdom of Bretonnia - Knights of the Realm', None, 'https://www.miniaturemarket.com/warhammer-old-world-kingdom-bretonnia-knights-realm-gw-06-11.html', True, False),
    ('knights-of-the-realm-on-foot', 'Warhammer The Old World: Kingdom of Bretonnia - Knights of the Realm on Foot', None, 'https://www.miniaturemarket.com/warhammer-old-world-kingdom-bretonnia-knights-realm-foot-gw-06-08.html', True, False),
    ('lord-on-royal-pegasus', 'Warhammer The Old World: Kingdom of Bretonnia - Lord on Royal Pegasus', None, 'https://www.miniaturemarket.com/warhammer-old-world-kingdom-bretonnia-lord-on-royal-pegasus-gw-06-10.html', True, False),
    ('men-at-arms', 'Warhammer The Old World: Kingdom of Bretonnia - Men-At-Arms', None, 'https://www.miniaturemarket.com/warhammer-old-world-kingdom-bretonnia-men-at-arms-gw-06-12.html', True, False),
    ('peasant-bowmen', 'Warhammer The Old World: Kingdom of Bretonnia - Peasant Bowmen', None, 'https://www.miniaturemarket.com/warhammer-old-world-kingdom-bretonnia-peasant-bowmen-gw-06-13.html', True, False),
    ('pegasus-knights', 'Warhammer The Old World: Kingdom of Bretonnia - Pegasus Knights', None, 'https://www.miniaturemarket.com/warhammer-old-world-kingdom-bretonnia-pegasus-knights-gw-06-09.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Kingdom of Bretonnia. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Kingdom of Bretonnia.')
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
            f'seed_mm_kingdom_of_bretonnia_prices complete. {created} created, {updated} updated.'
        ))
