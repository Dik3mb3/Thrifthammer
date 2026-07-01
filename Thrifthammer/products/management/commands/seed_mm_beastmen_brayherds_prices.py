"""
Management command: seed_mm_beastmen_brayherds_prices

Seeds Miniature Market URLs and initial prices for Beastmen Brayherds products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_beastmen_brayherds_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('beastman-shaman', 'Warhammer The Old World: Beastmen Brayherds - Beastman Shaman', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-beastmen-brayherds-beastman-shaman-gw-08-111.html', True, False),
    ('bestigor-herd', 'Warhammer The Old World: Beastmen Brayherds - Bestigor Herd', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-beastmen-brayherds-bestigor-herd-gw-08-104.html', True, False),
    ('gor-herd', 'Warhammer The Old World: Beastmen Brayherds - Gor Herd', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-beastmen-brayherds-gor-herd-gw-08-106.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Beastmen Brayherds. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Beastmen Brayherds.')
            return

        from decimal import Decimal
        from products.models import Product, Retailer
        from prices.models import CurrentPrice

        mm = Retailer.objects.get(name='Miniature Market')
        created = updated = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(slug=slug)
            _, was_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
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
            f'seed_mm_beastmen_brayherds_prices complete. {created} created, {updated} updated.'
        ))
