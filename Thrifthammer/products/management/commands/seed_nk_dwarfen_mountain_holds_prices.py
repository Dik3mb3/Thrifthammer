"""
Management command: seed_nk_dwarfen_mountain_holds_prices

Seeds Noble Knight URLs and initial prices for Dwarfen Mountain Holds products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_dwarfen_mountain_holds_prices
"""

from django.core.management.base import BaseCommand

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('dwarf-cannon-organ-gun', 'Dwarf Cannon & Organ Gun', None, f'{_NK}/P/2148261829/Dwarf-Cannon-and-Organ-Gun{_AFF}', True, False),
    ('dwarfen-mountain-holds-battalion', 'Dwarfen Mountain Holds Battalion', None, f'{_NK}/P/2148177559/Dwarfen-Mountain-Holds-Battalion{_AFF}', True, False),
    ('dwarf-gyrocopters', 'Dwarf Gyrocopters', None, f'{_NK}/P/2148419981/Dwarf-Gyrocopters{_AFF}', True, False),
    ('dwarf-hammerers', 'Dwarf Hammerers', None, f'{_NK}/P/2148177624/Dwarf-Hammerers{_AFF}', True, False),
    ('dwarf-ironbreakers', 'Dwarf Ironbreakers', None, f'{_NK}/P/2148177629/Dwarf-Ironbreakers{_AFF}', True, False),
    ('dwarf-lords-with-shieldbearers', 'Dwarf Lords w/Shieldbearers', None, f'{_NK}/P/2148177620/Dwarf-Lords-w-Shieldbearers{_AFF}', True, False),
    ('dwarf-miners', 'Dwarf Miners', None, f'{_NK}/P/2148336403/Dwarf-Miners{_AFF}', True, False),
    ('dwarf-quarrelers', 'Dwarf Quarrelers', None, f'{_NK}/P/2148177613/Dwarf-Quarrelers{_AFF}', True, False),
    ('dwarf-runesmith', 'Dwarf Runesmith', None, f'{_NK}/P/2148177634/Dwarf-Runesmith{_AFF}', True, False),
    ('dwarf-slayer-of-legend', 'Dwarf Slayer of Legend', None, f'{_NK}/P/2148419957/Dwarf-Slayer-of-Legend{_AFF}', True, False),
    ('dwarf-warriors', 'Dwarf Warriors', None, f'{_NK}/P/2148177604/Dwarf-Warriors{_AFF}', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Noble Knight prices for Dwarfen Mountain Holds. Idempotent.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write('No NK prices to seed for Dwarfen Mountain Holds.')
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
            f'seed_nk_dwarfen_mountain_holds_prices complete. {created} created, {updated} updated.'
        ))
