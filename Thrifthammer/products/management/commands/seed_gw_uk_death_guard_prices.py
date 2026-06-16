"""
Seed Games Workshop UK prices for Death Guard.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.

Note: gw_sku 43-56 covers both Deathshroud Bodyguard and Myphitic Blight-hauler.
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
    ('43-03',                      'Death Guard Mortarion',                                       Decimal('105.50'), 'https://www.warhammer.com/en-GB/shop/Death-Guard-Daemon-Primarch-Mortarion-2020',          True),
    ('43-08',                      'Death Guard Typhus',                                          Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Typhus-2020',                             True),
    ('43-24',                      'Death Guard Biologus Putrifier',                              Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Biologus-Putrifier-2020',                 True),
    ('43-29',                      'Death Guard Plague Surgeon',                                  Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Nauseous-Rotbone-2020',                   True),
    ('43-45',                      'Death Guard Tallyman',                                        Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Scribbus-Wretch-2020',                    True),
    ('43-46',                      'Death Guard Foul Blightspawn',                                Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Foul-Blightspawn-2020',                   True),
    ('43-47',                      'Death Guard Plague Marine Icon Bearer',                       Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Plague-Marine-Icon-Bearer-2020',           True),
    ('43-48',                      'Death Guard Plague Marine Champion',                          Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Plague-Marine-Champion-2020',              True),
    ('43-50',                      'Death Guard Plague Marines',                                  Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Plague-Marines-2020',                     True),
    ('43-52',                      'Death Guard Plagueburst Crawler',                             Decimal('50.00'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Plagueburst-Crawler-2020',                True),
    ('43-53',                      'Death Guard Poxwalkers',                                      Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Poxwalkers-2021',                         True),
    ('43-54',                      'Death Guard Blightlord Terminators',                          Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Blightlord-Terminators-2020',             True),
    ('43-55',                      'Death Guard Foetid Bloat-drone',                              Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Foetid-Bloat-drone-2020',                 True),
    ('43-56',                      'Death Guard Deathshroud Bodyguard',                           Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Deathshroud-Bodyguard-2020',              True, 'Deathshroud'),
    ('43-56',                      'Death Guard Myphitic Blight-hauler',                          Decimal('18.50'),  'https://www.warhammer.com/en-GB/shop/Etb-Death-Guard-Myphitic-Blight-hauler-2020',         True, 'Myphitic'),
    ('43-77',                      'Death Guard Lord of Virulence',                               Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Lord-of-Virulence-2020',                  True),
    ('43-78',                      'Death Guard Miasmic Malignifier',                             Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Miasmic-Malignifier-2020',                True),
    ('43-80',                      'Death Guard Combat Patrol',                                   Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-death-guard-2025',                      True),
    ('P-213409-60030102032',       'Codex: Death Guard',                                         Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-death-guard-hb-2025-eng',                       True),
    ('P-223010-99120102198',       'Death Guard Lord of Poxes',                                  Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/death-guard-lord-of-poxes-2025',                      True),
    ('P-NURGLE-PLAGUEBEARERS-40K', 'Plaguebearers of Nurgle',                                    Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Daemons-Plaguebearers-of-Nurgle-2018',          True),
    ('prod3550127-99129915060',    'Nurglings',                                                   Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Nurglings-2017',                                      True),
    ('prod3610130-99129915038',    'Plague Drones of Nurgle',                                    Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/plague-drones-of-nurgle-2017',                        True),
    ('prod3700246-99129915062',    'Beast of Nurgle',                                             Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Beast-Of-Nurgle-2018',                                True),
    ('prod3700247-99129915063',    'Great Unclean One',                                           Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/Great-Unclean-One-2018',                              True),
    ('prod3700271-99129915063',    'Rotigus',                                                     Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/Rotigus-Rainmaker',                                   True),
    ('prod4570149-99120102114',    'Death Guard Chosen of Mortarion',                            Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/Death-Guard-Chosen-Of-Mortarion-2020',               True),
    ('prod4650190-99120102150',    'Death Guard Lord of Contagion and Blightlord Terminators',   Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Lord-Felthius-And-The-Tainted-Cohort-2021',           True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Death Guard. Idempotent.'

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

        self.stdout.write(f'Seeded {seeded} Death Guard GW UK prices. Skipped: {skipped}.')
