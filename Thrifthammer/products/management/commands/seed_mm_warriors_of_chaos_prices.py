"""
Management command: seed_mm_warriors_of_chaos_prices

Seeds Miniature Market URLs and initial prices for Warriors of Chaos (TOW) products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_warriors_of_chaos_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-the-razing-of-westerland', 'Warhammer The Old World: Arcane Journal - The Razing of Westerland', None, 'https://www.miniaturemarket.com/Warhammer-The-Old-World-Arcane-Journal-The-Razing-of-Westerland/GW-08-17-2025', True, False),
    ('arcane-journal-warriors-of-chaos', 'Warhammer The Old World: Arcane Journal - Warriors of Chaos', None, 'https://www.miniaturemarket.com/warhammer-old-world-arcane-journal-warriors-chaos-gw-08-02.html', True, False),
    ('chaos-lord-on-manticore', 'Warhammer The Old World: Warriors of Chaos - Lord on Manticore', None, 'https://www.miniaturemarket.com/warhammer-old-world-warriors-chaos-lord-on-manticore-gw-08-05.html', True, False),
    ('chaos-marauder-horsemen', 'Warhammer The Old World: Warriors of Chaos - Chaos Marauders Horsemen', None, 'https://www.miniaturemarket.com/Warhammer-The-Old-World-Warriors-of-Chaos-Chaos-Marauders-Horsemen/GW-08-14-2026', True, False),
    ('chaos-marauders', 'Warhammer The Old World: Warriors of Chaos - Chaos Marauders', None, 'https://www.miniaturemarket.com/Warhammer-The-Old-World-Warriors-of-Chaos-Chaos-Marauders/GW-08-08-2026', True, False),
    ('sorcerer-of-chaos', 'Warhammer The Old World: Warriors of Chaos - Sorcerer of Chaos', None, 'https://www.miniaturemarket.com/warhammer-old-world-warriors-chaos-sorcerer-chaos-gw-08-15.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Warriors of Chaos (TOW). Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Warriors of Chaos.')
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
            f'seed_mm_warriors_of_chaos_prices complete. {created} created, {updated} updated.'
        ))
