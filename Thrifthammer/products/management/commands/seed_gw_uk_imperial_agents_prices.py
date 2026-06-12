"""
Seed Games Workshop UK prices for Agents of the Imperium.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('IA-001', 'Combat Patrol: Imperial Agents',              Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-imperial-agents-2024',                          True),
    ('IA-002', 'Inquisitor Kroyle',                           Decimal('37.50'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-inquisitor-kroyle-2026',                       True),
    ('IA-004', 'Inquisitor Coteaz',                           Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/inquisitor-coteaz-and-the-glodovan-eagle-2024',                True),
    ('IA-005', 'Navigator',                                   Decimal('23.00'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-navigator-2024',                              True),
    ('IA-006', 'Callidus Assassin',                           Decimal('23.50'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-callidus-assassin-2024',                      True),
    ('IA-007', 'Vindicare Assassin',                          Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-vindicare-assassin-2024',                     True),
    ('IA-008', 'Culexus Assassin',                            Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-culexus-assassin-2024',                       True),
    ('IA-009', 'Eversor Assassin',                            Decimal('26.00'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-eversor-assassin-2024',                       True),
    ('IA-010', 'Inquisitor Greyfax',                          Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-inquisitor-greyfax-2024',                     True),
    ('IA-011', 'Lord Inquisitor Kyria Draxus',                Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-inquisitor-draxus-2024',                      True),
    ('IA-012', 'Rogue Trader Entourage and Voidsmen-at-Arms', Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-rogue-trader-entourage-and-voidsmen-at-arm-2024', True),
    ('IA-013', 'Inquisitorial Agents',                        Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/imperial-agents-inquisitorial-agents-2024',                   True),
    ('IA-014', 'Codex: Imperial Agents',                      Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-imperial-agents-2024-eng',                             True),
    # Temporarily out of stock — price and URL recorded, in_stock=False
    ('IA-003', 'Eisenhorn',                                   Decimal('24.00'),  'https://www.warhammer.com/en-GB/shop/Eisenhorn-2018',                                             False),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Agents of the Imperium. Idempotent.'

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

        for sku, label, gbp_price, url, in_stock in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
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

        self.stdout.write(f'Seeded {seeded} Imperial Agents GW UK prices. Skipped: {skipped}.')
