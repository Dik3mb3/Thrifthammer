"""
Management command: seed_nk_wood_elf_realms_prices

Seeds Noble Knight URLs and initial prices for Wood Elf Realms products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_wood_elf_realms_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-wood-elf-realms', 'Arcane Journal - Wood Elf Realms', None, f'{_NK}/P/2148328867/Arcane-Journal---Wood-Elf-Realms{_AFF}', True, False),
    ('wood-elf-realms-battalion', 'Wood Elf Realms Battalion', None, f'{_NK}/P/2148457924/Wood-Elf-Realms-Battalion{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Wood Elf Realms. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Wood Elf Realms.')
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
            f'seed_nk_wood_elf_realms_prices complete. {created} created, {updated} updated.'
        ))
