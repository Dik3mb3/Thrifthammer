"""
Management command: seed_mm_grand_cathay_prices

Seeds Miniature Market URLs and initial prices for Grand Cathay products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_grand_cathay_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-armies-of-grand-cathay', 'Warhammer The Old World: Arcane Journal - Armies of Grand Cathay', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-arcane-journal-armies-grand-cathay-gw-06-200.html', True, False),
    ('arcane-journal-dawn-of-the-storm-dragon', 'Warhammer The Old World: Arcane Journal - Dawn of the Storm Dragon', None, 'https://www.miniaturemarket.com/warhammer-old-world-arcane-journal-dawn-storm-dragon-gw-06-211.html', True, False),
    ('arcane-journal-the-breaching-of-the-great-bastion', 'Warhammer the Old World: Arcane Journal - Breaching of the Great Bastion', None, 'https://www.miniaturemarket.com/Warhammer-the-Old-World-Arcane-Journal-Breaching-of-the-Great-Bastion/GW-06-216-2026', True, False),
    ('cathayan-sentinel', 'Warhammer The Old World: Grand Cathay - Cathayan Sentinel', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-grand-cathay-cathayan-sentinel-gw-06-206.html', True, False),
    ('gate-masters-of-the-celestial-cities', 'Warhammer The Old World: Grand Cathay - Gate Masters of the Celestial Cities', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-grand-cathay-gate-masters-celestial-cities-gw-06-204.html', True, False),
    ('iron-hail-gunners-crane-gunner-teams', 'Warhammer The Old World: Grand Cathay - Iron Hail & Crane Gunners', None, 'https://www.miniaturemarket.com/Warhammer-The-Old-World-Grand-Cathay-Iron-Hail-Crane-Gunners/GW-06-215-2026', True, False),
    ('jade-lancers', 'Warhammer The Old World: Grand Cathay - Jade Lancers', None, 'https://www.miniaturemarket.com/warhammer-old-world-grand-cathay-jade-lancers-gw-06-208.html', True, False),
    ('jade-warriors', 'Warhammer The Old World: Grand Cathay - Jade Warriors', None, 'https://www.miniaturemarket.com/warhammer-old-world-grand-cathay-jade-warriors-gw-06-209.html', True, False),
    ('miao-ying-the-storm-dragon', 'Warhammer The Old World: Grand Cathay - Miao Ying The Storm Dragon', None, 'https://www.miniaturemarket.com/warhammer-old-world-grand-cathay-miao-ying-storm-dragon-gw-06-210.html', True, False),
    ('peasant-levy', 'Warhammer The Old World: Grand Cathay - Peasant Levy', None, 'https://www.miniaturemarket.com/Warhammer-The-Old-World-Grand-Cathay-Peasant-Levy/GW-06-214-2026', True, False),
    ('shugengan-lord-on-great-spirit-longma', 'Warhammer The Old World: Grand Cathay - Shugengan Lord on Great Spirit Longma', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-grand-cathay-shugengan-lord-on-great-spirit-longma-gw-06-207.html', True, False),
    ('sky-lantern', 'Warhammer The Old World: Grand Cathay - Sky Lantern', None, 'https://www.miniaturemarket.com/warhammer-the-old-world-grand-cathay-sky-lantern-gw-06-205.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Grand Cathay. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Grand Cathay.')
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
            f'seed_mm_grand_cathay_prices complete. {created} created, {updated} updated.'
        ))
