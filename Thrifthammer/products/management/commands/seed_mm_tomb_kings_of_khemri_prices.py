"""
Management command: seed_mm_tomb_kings_of_khemri_prices

Seeds Miniature Market URLs and initial prices for Tomb Kings of Khemri products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_tomb_kings_of_khemri_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-the-war-of-settras-fury', 'Warhammer The Old World: Arcane Journal - The War of Settra\'s Fury', None, 'https://www.miniaturemarket.com/Warhammer-The-Old-World-Arcane-Journal-The-War-of-Settra-s-Fury/GW-07-15', True, False),
    ('arcane-journal-tomb-kings-of-khemri', 'Warhammer The Old World: Arcane Journal - Tomb Kings of Khemri', None, 'https://www.miniaturemarket.com/warhammer-old-world-arcane-journal-tomb-kings-khemri-gw-07-02.html', True, False),
    ('khemrian-warsphinx', 'Warhammer The Old World: Tomb Kings of Khemri - Necrosphinx', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-necrosphinx-gw-07-06.html', True, False),
    ('liche-priests', 'Warhammer The Old World: Tomb Kings of Khemri - Liche Priests', None, 'https://www.miniaturemarket.com/Warhammer-The-Old-World-Tomb-Kings-of-Khemri-Liche-Priests/GW-07-14', True, False),
    ('necropolis-knights', 'Warhammer The Old World: Tomb Kings of Khemri - Sepulchral Stalkers', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-sepulchral-stalkers-gw-07-04.html', True, False),
    ('necrosphinx', 'Warhammer The Old World: Tomb Kings of Khemri - Necrosphinx', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-necrosphinx-gw-07-06.html', True, False),
    ('royal-heralds', 'Warhammer The Old World: Tomb Kings of Khemri - Royal Heralds', None, 'https://www.miniaturemarket.com/Warhammer-The-Old-World-Tomb-Kings-of-Khemri-Royal-Heralds/GW-07-13', True, False),
    ('sepulchral-stalkers', 'Warhammer The Old World: Tomb Kings of Khemri - Sepulchral Stalkers', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-sepulchral-stalkers-gw-07-04.html', True, False),
    ('skeleton-chariots', 'Warhammer The Old World: Tomb Kings of Khemri - Skeleton Chariots', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-skeleton-chariots-gw-07-11.html', True, False),
    ('tomb-guard', 'Warhammer The Old World: Tomb Kings of Khemri - Tomb Guard', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-tomb-guard-gw-07-03.html', True, False),
    ('tomb-king-liche-priest-on-necrolith-bone-dragon', 'Warhammer The Old World: Tomb Kings of Khemri - Tomb King on Necrolith Bone Dragon', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-tomb-king-necrolith-bone-dragon-gw-07-08.html', True, False),
    ('tomb-kings-skeleton-horsemen-horse-archers', 'Warhammer The Old World: Tomb Kings of Khemri - Skeleton Horsemen', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-skeleton-horsemen-gw-07-10.html', True, False),
    ('tomb-kings-skeleton-warriors-archers', 'Warhammer The Old World: Tomb Kings of Khemri - Skeleton Warriors', None, 'https://www.miniaturemarket.com/warhammer-old-world-tomb-kings-khemri-skeleton-warriors-gw-07-09.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Tomb Kings of Khemri. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Tomb Kings of Khemri.')
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
            f'seed_mm_tomb_kings_of_khemri_prices complete. {created} created, {updated} updated.'
        ))
