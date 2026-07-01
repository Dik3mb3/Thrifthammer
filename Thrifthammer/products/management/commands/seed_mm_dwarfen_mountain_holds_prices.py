"""
Management command: seed_mm_dwarfen_mountain_holds_prices

Seeds Miniature Market URLs and initial prices for Dwarfen Mountain Holds products.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_dwarfen_mountain_holds_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('dwarf-cannon-organ-gun', 'Warhammer The Old World: Dwarfen Mountain Holds - Cannon/Organ Gun', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-cannonorgan-gun-gw-10-14.html', True, False),
    ('dwarfen-mountain-holds-battalion', 'Warhammer The Old World: Dwarfen Mountain Holds - Battalion', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-battalion-gw-10-05.html', True, False),
    ('dwarf-gyrocopters', 'Warhammer The Old World: Dwarfen Mountain Holds - Gyrocopters', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-gyrocopters-gw-10-13.html', True, False),
    ('dwarf-hammerers', 'Warhammer The Old World: Dwarfen Mountain Holds - Dwarf Hammerers', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-dwarf-hammerers-gw-10-10.html', True, False),
    ('dwarf-ironbreakers', 'Warhammer The Old World: Dwarfen Mountain Holds - Dwarf Ironbreakers', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-dwarf-ironbreakers-gw-10-09.html', True, False),
    ('dwarf-king-with-oathstone', 'Warhammer The Old World: Dwarfen Mountain Holds - Dwarf King with Oathstone', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-dwarf-king-with-oathstone-gw-10-16.html', True, False),
    ('dwarf-lords-with-shieldbearers', 'Warhammer The Old World: Dwarfen Mountain Holds - Dwarf Lords w/ Shieldbearers', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-dwarf-lords-w-shieldbearers-gw-10-11.html', True, False),
    ('dwarf-miners', 'Warhammer The Old World: Dwarfen Mountain Holds - Dwarf Miners', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-dwarf-miners-gw-10-12.html', True, False),
    ('dwarf-quarrelers', 'Warhammer The Old World: Dwarfen Mountain Holds - Dwarf Quarrellers', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-dwarf-quarrellers-gw-10-08.html', True, False),
    ('dwarf-runesmith', 'Warhammer The Old World: Dwarfen Mountain Holds - Dwarf Runesmith', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-dwarf-runesmith-gw-10-06.html', True, False),
    ('dwarf-slayer-of-legend', 'Warhammer The Old World: Dwarfen Mountain Holds - Slayer of Legend', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-slayer-legend-gw-10-15.html', True, False),
    ('dwarf-warriors', 'Warhammer The Old World: Dwarfen Mountain Holds - Dwarf Warriors', None, 'https://www.miniaturemarket.com/warhammer-old-world-dwarfen-mountain-holds-dwarf-warriors-gw-10-07.html', True, False),
]


class Command(BaseCommand):
    help = 'Seeds Miniature Market prices for Dwarfen Mountain Holds. Idempotent.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write('No MM prices to seed for Dwarfen Mountain Holds.')
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
            f'seed_mm_dwarfen_mountain_holds_prices complete. {created} created, {updated} updated.'
        ))
