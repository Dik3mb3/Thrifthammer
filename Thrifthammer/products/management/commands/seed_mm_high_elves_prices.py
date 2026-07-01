"""
Management command: seed_mm_high_elves_prices

Seeds Miniature Market URLs and initial prices for High Elves products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_high_elves_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-high-elf-realms', 'Warhammer Old World: Arcane Journal - High Elf Realms', None, 'https://www.miniaturemarket.com/warhammer-old-world-arcane-journal-high-elf-realms-gw-13-01.html', True, False),
    ('dragon-princes-of-caledor', 'Warhammer Old World: High Elf Realms - Dragon Princes of Caledor', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-dragon-princes-caledor-gw-13-17.html', True, False),
    ('eagle-claw-bolt-throwers', 'Warhammer Old World: High Elf Realms - Eagle Claw Bolt Throwers', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-eagle-claw-bolt-throwers-gw-13-05.html', True, False),
    ('elven-spearmen', 'Warhammer Old World: High Elf Realms - Elven Spearmen', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-elven-spearmen-gw-13-15.html', True, False),
    ('high-elf-lords', 'Warhammer Old World: High Elf Realms - Lords', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-lords-gw-13-07.html', True, False),
    ('high-elf-loremaster', 'Warhammer The Old World: High Elf Realms - High Elf Loremaster', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-high-elf-loremaster-gw-13-08.html', True, False),
    ('high-elf-mages', 'Warhammer Old World: High Elf Realms - Mages', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-mages-gw-13-04.html', True, False),
    ('lord-on-dragon', 'Warhammer Old World: High Elf Realms - Lord on Dragon', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-lord-on-dragon-gw-13-20.html', True, False),
    ('phoenix-guard', 'Warhammer Old World: High Elf Realms - Phoenix Guard', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-phoenix-guard-gw-13-12.html', True, False),
    ('silver-helms', 'Warhammer The Old World: High Elf Realms - Silver Helms', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-silver-helms-gw-13-10.html', True, False),
    ('sisters-of-avelorn', 'Warhammer Old World: High Elf Realms - Sisters of Avelorn', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-sisters-avelorn-gw-13-16.html', True, False),
    ('swordmasters-of-hoeth', 'Warhammer Old World: High Elf Realms - Swordmasters of Hoeth', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-swordmasters-hoeth-gw-13-19.html', True, False),
    ('white-lions-of-chrace', 'Warhammer Old World: High Elf Realms - White Lions of Chrace', None, 'https://www.miniaturemarket.com/warhammer-old-world-high-elf-realms-white-lions-chrace-gw-13-14.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for High Elves. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for High Elves.')
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
            f'seed_mm_high_elves_prices complete. {created} created, {updated} updated.'
        ))
