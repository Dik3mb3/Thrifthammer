"""
Seed Games Workshop UK prices for Flesh-Eater Courts.

Creates the `games-workshop-uk` Retailer if it does not exist, sets
msrp_gbp on each matched Product, and creates/updates a CurrentPrice
record pointing at the GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url)
_PRICES = [
    ('70-915', 'Spearhead: Flesh-Eater Courts – Charnel Watch', Decimal('91.00'),
     'https://www.warhammer.com/en-GB/shop/spearhead-charnel-watch-2025'),
    ('91-07', 'Flesh-Eater Courts Crypt Horrors', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Flesh-Eater-Courts-Crypt-Horrors'),
    ('91-32', 'Flesh-Eater Courts Terrorgheist', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/Royal-Terrorgheist-2019'),
    ('91-35', 'Flesh-Eater Courts Crypt Ghouls', Decimal('29.00'),
     'https://www.warhammer.com/en-GB/shop/Flesh-Eater-Courts-Crypt-Ghouls'),
    ('FEC-001', 'Abhorrant Archregent', Decimal('20.50'),
     'https://www.warhammer.com/en-GB/shop/Flesh-Eater-Courts-Abhorrant-Archregent-2020'),
    ('FEC-002', 'Abhorrant Ghoul King on Royal Zombie Dragon', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/Abhorrant-Ghoul-King-on-Zombie-Dragon-2016'),
    ('FEC-003', 'Abhorrant Ghoul King on Royal Terrorgheist', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/Flesh-Eaters-Courts-Abhorrant-Ghoul-King-on-Terrorgheist'),
    ('FEC-004', 'Crypt Infernal Courtier', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Flesh-Eater-Courts-Crypt-Infernal-Courtier'),
    ('FEC-005', 'Crypt Haunter Courtier', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Flesh-Eater-Courts-Crypt-Haunter-Courtier'),
    ('FEC-006', 'High Falconer Felgryn', Decimal('26.00'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-high-falconer-felgryn-2025'),
    ('FEC-007', 'Marrowscroll Herald', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-marrowscroll-herald-2024'),
    ('FEC-008', 'Abhorrant Gorewarden', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-abhorrant-gorewarden-2024'),
    ('FEC-009', 'Abhorrant Cardinal', Decimal('26.00'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-abhorrant-cardinal-2024'),
    ('FEC-010', 'Grand Justice Gormayne', Decimal('27.00'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-grand-justice-gormayne-2024'),
    ('FEC-011', 'Royal Decapitator', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-royal-decapitator-2024'),
    ('FEC-012', 'Ushoran, Mortarch of Delusion', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-ushoran-mortarch-of-delusion-2024'),
    ('FEC-013', 'Varghulf Courtier', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-varghulf-courtier-2024'),
    ('FEC-014', 'Royal Zombie Dragon', Decimal('47.00'),
     'https://www.warhammer.com/en-GB/shop/Royal-Zombie-Dragon-2019'),
    ('FEC-015', 'Crypt Flayers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Flesh-Eater-Courts-Crypt-Flayers'),
    ('FEC-016', 'Morbheg Knights', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-morbheg-knights-2024'),
    ('FEC-017', 'Cryptguard', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/flesh-eater-courts-cryptguard-2024'),
    ('FEC-018', 'Royal Beastflayers', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/warcry-royal-beastflayers-warband-2023'),
    ('FEC-019', 'Charnel Throne', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Flesh-Eater-Courts-Charnel-Throne-2019'),
    ('FEC-020', 'Endless Spells: Flesh-eater Courts', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/Endless-Spells-Flesh-Eater-Courts-2019'),
    ('FEC-021', 'Death Battletome: Flesh-eater Courts', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/battletome-flesh-eater-courts-2025-eng'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Flesh-Eater Courts. Idempotent.'

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
        for gw_sku, label, gbp_price, url in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} ({label}) not in DB')
                skipped += 1
                continue

            if product.msrp_gbp != gbp_price:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': gbp_price,
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Flesh-Eater Courts GW UK prices. Skipped: {skipped}.'
            )
        )
