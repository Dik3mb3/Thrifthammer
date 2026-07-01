"""
Management command: seed_mm_wood_elf_realms_prices

Seeds Miniature Market URLs and initial prices for Wood Elf Realms products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_wood_elf_realms_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('araloth-lord-of-talsyn', 'Warhammer The Old World: Wood Elf Realms - Araloth, Lord of Talsyn', None, 'https://www.miniaturemarket.com/warhammer-old-world-wood-elf-realms-araloth-lord-talsyn-gw-13-108.html', True, False),
    ('arcane-journal-wood-elf-realms', 'Warhammer The Old World: Arcane Journal - Wood Elf Realms', None, 'https://www.miniaturemarket.com/warhammer-old-world-arcane-journal-wood-elf-realms-gw-13-101.html', True, False),
    ('eternal-guard', 'Warhammer The Old World: Wood Elf Realms - Eternal Guard', None, 'https://www.miniaturemarket.com/warhammer-old-world-wood-elf-realms-eternal-guard-gw-13-106.html', True, False),
    ('glade-guard', 'Warhammer The Old World: Wood Elf Realms - Glade Guard', None, 'https://www.miniaturemarket.com/warhammer-old-world-wood-elf-realms-glade-guard-gw-13-105.html', True, False),
    ('glade-riders', 'Warhammer The Old World: Wood Elf Realms - Glade Riders', None, 'https://www.miniaturemarket.com/warhammer-old-world-wood-elf-realms-glade-riders-gw-13-104.html', True, False),
    ('wood-elf-realms-battalion', 'Warhammer The Old World: Wood Elf Realms - Battalion', None, 'https://www.miniaturemarket.com/warhammer-old-world-wood-elf-realms-battalion-gw-13-109.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Wood Elf Realms. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Wood Elf Realms.')
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
            f'seed_mm_wood_elf_realms_prices complete. {created} created, {updated} updated.'
        ))
