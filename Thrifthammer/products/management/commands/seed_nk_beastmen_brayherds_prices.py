"""
Management command: seed_nk_beastmen_brayherds_prices

Seeds Noble Knight URLs and initial prices for Beastmen Brayherds products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_beastmen_brayherds_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('beastman-shaman', 'Beastman Shaman', None, f'{_NK}/P/2148312192/Beastman-Shaman{_AFF}', True, False),
    ('bestigor-herd', 'Bestigor Herd', None, f'{_NK}/P/2148312179/Bestigor-Herd{_AFF}', True, False),
    ('gor-herd', 'Gor Herd', None, f'{_NK}/P/2148312171/Gor-Herd{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Beastmen Brayherds. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Beastmen Brayherds.')
            return

        from decimal import Decimal
        from products.models import Product, Retailer
        from prices.models import CurrentPrice

        nk = Retailer.objects.get(name='Noble Knight Games')
        created = updated = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(slug=slug)
            _, was_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_beastmen_brayherds_prices complete. {created} created, {updated} updated.'
        ))
