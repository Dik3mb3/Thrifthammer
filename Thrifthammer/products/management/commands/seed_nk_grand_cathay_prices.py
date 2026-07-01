"""
Management command: seed_nk_grand_cathay_prices

Seeds Noble Knight URLs and initial prices for Grand Cathay products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_grand_cathay_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('arcane-journal-armies-of-grand-cathay', 'Arcane Journal - Armies of Grand Cathay', None, f'{_NK}/P/2148426641/Arcane-Journal---Armies-of-Grand-Cathay{_AFF}', True, False),
    ('arcane-journal-dawn-of-the-storm-dragon', 'Arcane Journal - Dawn of the Storm Dragon', None, f'{_NK}/P/2148341962/Arcane-Journal---Dawn-of-the-Storm-Dragon{_AFF}', True, False),
    ('arcane-journal-the-breaching-of-the-great-bastion', 'Arcane Journal - The Breaching of the Great Bastion', None, f'{_NK}/P/2148421614/Arcane-Journal---The-Breaching-of-the-Great-Bastion{_AFF}', True, False),
    ('cathayan-sentinel', 'Cathayan Sentinel', None, f'{_NK}/P/2148361251/Cathayan-Sentinel{_AFF}', True, False),
    ('gate-masters-of-the-celestial-cities', 'Gate Masters of the Celestial Cities', None, f'{_NK}/P/2148361245/Gate-Masters-of-the-Celestial-Cities{_AFF}', True, False),
    ('iron-hail-gunners-crane-gunner-teams', 'Iron Hail Gunners & Crane Gunner Teams', None, f'{_NK}/P/2148460467/Iron-Hail-Gunners-and-Crane-Gunner-Teams{_AFF}', True, False),
    ('jade-lancers', 'Jade Lancers', None, f'{_NK}/P/2148341925/Jade-Lancers{_AFF}', True, False),
    ('jade-warriors', 'Jade Warriors', None, f'{_NK}/P/2148341934/Jade-Warriors{_AFF}', True, False),
    ('miao-ying-the-storm-dragon', 'Miao Ying - The Storm Dragon', None, f'{_NK}/P/2148341952/Miao-Ying---The-Storm-Dragon{_AFF}', True, False),
    ('peasant-levy', 'Peasant Levy', None, f'{_NK}/P/2148460476/Peasant-Levy{_AFF}', True, False),
    ('shugengan-lord-on-great-spirit-longma', 'Shugengan Lord on Great Spirit Longma', None, f'{_NK}/P/2148457339/Shugengan-Lord-on-Great-Spirit-Longma{_AFF}', True, False),
    ('sky-lantern', 'Sky Lantern', None, f'{_NK}/P/2148457340/Sky-Lantern{_AFF}', True, False),
    ('the-northern-provinces-of-grand-cathay-transfer-sheet', 'Northern Provinces of Grand Cathay Transfer Sheet, The', None, f'{_NK}/P/2148460247/Northern-Provinces-of-Grand-Cathay-Transfer-Sheet-The{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Grand Cathay. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Grand Cathay.')
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
            f'seed_nk_grand_cathay_prices complete. {created} created, {updated} updated.'
        ))
