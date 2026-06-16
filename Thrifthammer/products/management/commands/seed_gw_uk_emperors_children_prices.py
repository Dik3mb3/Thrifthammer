"""
Seed Games Workshop UK prices for Emperor's Children.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.

Note: gw_sku 99129915056 covers both Keeper of Secrets and Shalaxi Helbane.
A 6th tuple element (name_filter) disambiguates them via icontains lookup.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
# Optional 6th element: name_filter (icontains) for shared-SKU products.
_PRICES = [
    ('65-01',         "Codex: Emperor's Children",             Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-emperors-children-2025-eng',              True),
    ('99120102200',   'Fulgrim, Daemon Primarch of Slaanesh',  Decimal('105.50'), 'https://www.warhammer.com/en-GB/shop/emperors-children-fulgrim-2025',                True),
    ('99120102201',   'Lucius the Eternal',                    Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/emperors-children-lucius-the-eternal-2025',     True),
    ('99120102202',   'Flawless Blades',                       Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/emperors-children-flawless-blades-2025',        True),
    ('99120102203',   'Tormentors',                            Decimal('44.00'),  'https://www.warhammer.com/en-GB/shop/emperors-children-tormentors-2025',             True),
    ('99120102204',   'Noise Marines',                         Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/emperors-children-noise-marines-2025',          True),
    ('99120102205',   'Lord Kakophonist',                      Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/emperors-children-lord-kakophonist-2025',       True),
    ('99120102206',   'Lord Exultant',                         Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/emperors-children-lord-exultant-2025',          True),
    ('99120102207',   "Combat Patrol: Emperor's Children",     Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-emperors-children-2025',          True),
    ('99129915005',   'Seekers of Slaanesh',                   Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/Seekers-of-Slaanesh',                           True),
    ('99129915036',   'Daemonettes of Slaanesh',               Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Daemonettes-of-Slaanesh-2021',                  True),
    ('99129915052',   'Fiends',                                Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Fiends-of-Slaanesh-2019',                       True),
    ('99129915056',   'Keeper of Secrets',                     Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/Keeper-of-Secrets-2019',                        True, 'Keeper'),
    ('99129915056',   'Shalaxi Helbane',                       Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/Shalaxi-Hellbane-2019',                         True, 'Shalaxi'),
]


class Command(BaseCommand):
    help = "Seed GW UK prices and URLs for Emperor's Children. Idempotent."

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_GW_UK_SLUG,
            defaults={
                'name': 'Games Workshop UK',
                'website': 'https://www.warhammer.com/en-GB/',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0

        for entry in _PRICES:
            sku, label, gbp_price, url, in_stock = entry[:5]
            name_filter = entry[5] if len(entry) > 5 else None

            qs = Product.objects.filter(gw_sku=sku)
            if name_filter:
                qs = qs.filter(name__icontains=name_filter)
            products = list(qs)

            if not products:
                self.stdout.write(f'  SKIP {sku} ({label}) — not found in DB')
                skipped += 1
                continue
            for product in products:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'url': url,
                        'in_stock': in_stock,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(f"Seeded {seeded} Emperor's Children GW UK prices. Skipped: {skipped}.")
