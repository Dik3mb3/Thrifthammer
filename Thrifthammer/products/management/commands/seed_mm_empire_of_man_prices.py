"""
Management command: seed_mm_empire_of_man_prices

Seeds Miniature Market URLs and initial prices for Empire of Man products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_empire_of_man_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-empire-of-man', 'Warhammer Old World: Arcane Journal - Empire of Man', None, 'https://www.miniaturemarket.com/warhammer-old-world-arcane-journal-empire-man-gw-06-101.html', True, False),
    ('cannons-mortars', 'Warhammer Old World: Empire of Man - Cannons & Mortars', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-cannons-mortars-gw-06-108.html', True, False),
    ('commanders-of-the-empire', 'Warhammer Old World: Empire of Man - Commanders of the Empire', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-commanders-empire-gw-06-118.html', True, False),
    ('demigryph-knights', 'Warhammer Old World: Empire of Man - Demigryph Knights', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-demigryph-knights-gw-06-107.html', True, False),
    ('empire-archers', 'Warhammer Old World: Empire of Man - Empire Archers', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-empire-archers-gw-06-113.html', True, False),
    ('empire-greatswords', 'Warhammer Old World: Empire of Man - Greatswords', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-greatswords-gw-06-112.html', True, False),
    ('empire-knights', 'Warhammer Old World: Empire of Man - Empire Knights', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-empire-knights-gw-06-105.html', True, False),
    ('empire-pistoliers', 'Warhammer Old World: Empire of Man - Empire Pistoliers', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-empire-pistoliers-gw-06-106.html', True, False),
    ('empire-state-troops', 'Warhammer Old World: Empire of Man - Empire State Troops', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-empire-state-troops-gw-06-109.html', True, False),
    ('flagellants', 'Warhammer Old World: Empire of Man - Flagellants', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-flagellants-gw-06-111.html', True, False),
    ('free-company-militia', 'Warhammer Old World: Empire of Man - Free Company Militia', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-free-company-militia-gw-06-104.html', True, False),
    ('general-of-the-empire-on-imperial-griffon', 'Warhammer Old World: Empire of Man - General of the Empire on Imperial Griffon', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-general-empire-imperial-griffon-gw-06-103.html', True, False),
    ('helblaster-volley-gun-helstorm-rocket-battery', 'Warhammer Old World: Empire of Man - Helblaster Volleygun & Helstorm Battery', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-helblaster-volleygun-helstorm-battery-gw-06-114.html', True, False),
    ('state-missile-troops', 'Warhammer Old World: Empire of Man - State Missile Troops', None, 'https://www.miniaturemarket.com/warhammer-old-world-empire-man-state-missile-troops-gw-06-110.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Empire of Man. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Empire of Man.')
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
            f'seed_mm_empire_of_man_prices complete. {created} created, {updated} updated.'
        ))
