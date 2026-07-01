"""
Management command: seed_nk_warriors_of_chaos_prices

Seeds Noble Knight URLs and initial prices for Warriors of Chaos (TOW) products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_warriors_of_chaos_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-the-razing-of-westerland', 'Arcane Journal - The Razing of Westerland', None, f'{_NK}/P/2148378725/Arcane-Journal---The-Razing-of-Westerland{_AFF}', True, False),
    ('arcane-journal-warriors-of-chaos', 'Arcane Journal - Warriors of Chaos', None, f'{_NK}/P/2148192595/Arcane-Journal---Warriors-of-Chaos{_AFF}', True, False),
    ('chaos-chariots', 'Chaos Chariots', None, f'{_NK}/P/2147485169/Chaos-Chariot-Gorebeast-Chariot{_AFF}', True, False),
    ('chaos-lord-on-manticore', 'Chaos Lord on Manticore', None, f'{_NK}/P/2148192391/Chaos-Lord-on-Manticore{_AFF}', True, False),
    ('chaos-marauder-horsemen', 'Chaos Marauder Horsemen', None, f'{_NK}/P/2148407505/Chaos-Marauder-Horsemen{_AFF}', True, False),
    ('chaos-marauders', 'Chaos Marauders', None, f'{_NK}/P/2148407502/Chaos-Marauders{_AFF}', True, False),
    ('chaos-warhounds', 'Chaos Warhounds', None, f'{_NK}/P/2148286608/Chaos-Warhounds{_AFF}', True, False),
    ('chimera', 'Chimera', None, f'{_NK}/P/2148286617/Chimera{_AFF}', True, False),
    ('dragon-ogres', 'Dragon Ogres', None, f'{_NK}/P/2148242185/Dragon-Ogres-2024-Edition{_AFF}', True, False),
    ('sorcerer-of-chaos', 'Sorcerer of Chaos', None, f'{_NK}/P/2148194425/Sorcerer-of-Chaos{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Warriors of Chaos (TOW). Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Warriors of Chaos.')
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
            f'seed_nk_warriors_of_chaos_prices complete. {created} created, {updated} updated.'
        ))
