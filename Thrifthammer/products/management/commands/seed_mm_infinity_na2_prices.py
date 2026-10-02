"""
Seed Miniature Market US prices and the USD MSRP for Infinity: NA2.

Uses the existing `miniature-market` Retailer (US, is_uk=False) -- does not
create it, matching every other Miniature Market seed command.

Source: user-supplied "Infinity U.S Miniature Market.xlsx" (Title/Title_URL/
Keywords/Price columns). Each sheet row carries two numbers, used as follows
(explicit user instruction, 2026-10-02):

- "Retail Price" is the Corvus Belli US MSRP shown to users -> Product.msrp
  (USD; the MSRP and discount baseline on US pages when a product has no Games
  Workshop row) AND the price of the Corvus Belli US row (retailer
  `corvus-belli`, the same official URL as the UK `corvus-belli-uk` row,
  created by seed_corvus_belli_infinity_us_links).
- "Price" is Miniature Market's own, lower selling price -> the
  `miniature-market` CurrentPrice price, with the sheet's link as its url.

Both writes are create-only (a value is only written while it is still None /
the row does not exist yet), so a redeploy never resets an MSRP or a price
the Miniature Market scraper has since refreshed. in_stock is the live stock
status of each listing checked on 2026-10-02 (NA2-002, 004, 005 and 006 were
in stock, the rest out of stock, which keeps their real price with
in_stock=False and not_available=False). The scraper corrects stock on its
next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing list were confirmed with the user (2026-10-02).

24 of 26 NA2 SKUs matched. 2 SKUs not in the sheet (confirmed by searching it):
NA2-001 Rumbler Spec-Ops Preorder Exclusive Miniature, NA2-015 McMurrough,
Mercenary Dog-Warrior.

Notes on individual picks (all confirmed with the user):
- NA2-004 Anaconda is MM's "NA2 - Anaconda, Mercenary TAG Squadron" (75.00
  retail), not the older "Mercenaries - Anaconda TAG Squad" (66.99).
- NA2-005 "Iguana" Squadron is MM's "Nomads - Iguana Squadron" (75.00 retail),
  not the older "Iguana Squad" (75.49).
- NA2-002 is MM's Viral Pistol "Taowu, Mastermind & Schemer" listing (filed by
  MM under "Yu Jing"), not the plain "Taowu, Mastermind".
- NA2-008 is "JSA - O-Yoroi Kidobutai TAG Pack", not "NA2 - O-Yoroi Kidobutai".
- NA2-010 is the "JSA - Reinf. Domaru Takeshi 'Neko' Oyama" listing, not the
  older Yu Jing one.
- Miniature Market files NA2-002 and NA2-007 under "Yu Jing", NA2-005 under
  "Nomads", NA2-012 under "Haqqislam", NA2-022 and NA2-024 to NA2-026 under
  "Mercenaries" and NA2-006, 008, 009 and 010 under "JSA" in its own titles.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM_SLUG = 'miniature-market'
_CORVUS_BELLI_US_SLUG = 'corvus-belli'

# (gw_sku, usd_msrp (sheet "Retail Price"), usd_mm_price (sheet "Price"), url, in_stock)
_PRICES = [
    ('NA2-002', Decimal('22.00'), Decimal('15.99'), 'https://www.miniaturemarket.com/Infinity-Yu-Jing-Taowu-Mastermind-Schemer-Viral-Pistol-New-Arrival/CVB281364-1248', True),
    ('NA2-003', Decimal('49.00'), Decimal('30.99'), 'https://www.miniaturemarket.com/Infinity-NA2-JSA-Oban-Expansion-Pack-Alpha/CVB281715-1214', False),
    ('NA2-004', Decimal('75.00'), Decimal('47.99'), 'https://www.miniaturemarket.com/Infinity-NA2-Anaconda-Mercenary-TAG-Squadron/CVB280783-1181', True),
    ('NA2-005', Decimal('75.00'), Decimal('59.99'), 'https://www.miniaturemarket.com/infinity-nomads-iguana-squadron-cvb281547-1176.html', True),
    ('NA2-006', Decimal('36.00'), Decimal('28.99'), 'https://www.miniaturemarket.com/infinity-jsa-essentials-booster-pack-alpha-cvb281712-1161.html', True),
    ('NA2-007', Decimal('59.00'), Decimal('47.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-imperial-service-expansion-pack-alpha-cvb281352-1155.html', False),
    ('NA2-008', Decimal('48.00'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-jsa-o-yoroi-kidobutai-tag-pack-cvb281709-1143.html', False),
    ('NA2-009', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/infinity-jsa-jsa-support-pack-cvb281708-1138.html', False),
    ('NA2-010', Decimal('24.99'), Decimal('22.99'), 'https://www.miniaturemarket.com/infinity-jsa-reinf-domaru-takeshi-neko-oyama-cvb281703-1109.html', False),
    ('NA2-011', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-na2-jsa-mechazoid-sokorentai-cvb281701-1094.html', False),
    ('NA2-012', Decimal('59.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/infinity-haqqislam-druze-shock-teams-cvb280774-1063.html', False),
    ('NA2-013', Decimal('21.49'), Decimal('19.99'), 'https://www.miniaturemarket.com/infinity-na2-father-lucien-sforza-authorized-bounty-hunter-cvb280769-1016.html', False),
    ('NA2-014', Decimal('55.99'), Decimal('50.99'), 'https://www.miniaturemarket.com/infinity-na2-jsa-expansion-pack-alpha-cvb280771-1039.html', False),
    ('NA2-016', Decimal('17.99'), Decimal('16.99'), 'https://www.miniaturemarket.com/cvb280763-0933.html', False),
    ('NA2-017', Decimal('38.49'), Decimal('34.99'), 'https://www.miniaturemarket.com/cvb280754-0881.html', False),
    ('NA2-018', Decimal('53.99'), Decimal('48.99'), 'https://www.miniaturemarket.com/cvb280741-0794.html', False),
    ('NA2-019', Decimal('16.99'), Decimal('14.99'), 'https://www.miniaturemarket.com/cvb280738-0778.html', False),
    ('NA2-020', Decimal('46.99'), Decimal('42.99'), 'https://www.miniaturemarket.com/cvb280736-0766.html', False),
    ('NA2-021', Decimal('44.49'), Decimal('40.99'), 'https://www.miniaturemarket.com/cvb280733-0737.html', False),
    ('NA2-022', Decimal('15.49'), Decimal('13.99'), 'https://www.miniaturemarket.com/cvb280731-0723.html', False),
    ('NA2-023', Decimal('55.99'), Decimal('50.99'), 'https://www.miniaturemarket.com/cvb280729-0716.html', False),
    ('NA2-024', Decimal('28.99'), Decimal('25.99'), 'https://www.miniaturemarket.com/cvb280721-0589.html', False),
    ('NA2-025', Decimal('16.99'), Decimal('14.99'), 'https://www.miniaturemarket.com/cvb280719-0554.html', False),
    ('NA2-026', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb280716-0490.html', False),
]


def _apply_row(product, retailer, corvus_belli, usd_msrp, usd_price, url, in_stock):
    """Write the create-only USD MSRP, the Corvus Belli US row and the Miniature Market row."""
    if product.msrp is None:
        product.msrp = usd_msrp
        product.save(update_fields=['msrp'])

    corvus_row, _ = CurrentPrice.objects.get_or_create(
        product=product,
        retailer=corvus_belli,
        defaults={
            'url': product.gw_url,
            'price': None,
            'currency': 'USD',
            'in_stock': False,
            'not_available': True,
        },
    )
    if corvus_row.price is None:
        corvus_row.price = usd_msrp
        corvus_row.currency = 'USD'
        corvus_row.in_stock = True
        corvus_row.not_available = False
        corvus_row.save(update_fields=['price', 'currency', 'in_stock', 'not_available'])

    cp_defaults = {'url': url, 'in_stock': in_stock, 'not_available': False, 'currency': 'USD'}
    CurrentPrice.objects.update_or_create(
        product=product,
        retailer=retailer,
        defaults=cp_defaults,
        create_defaults={**cp_defaults, 'price': usd_price},
    )


class Command(BaseCommand):
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: NA2. Idempotent.'

    def handle(self, *args, **options):
        retailer = Retailer.objects.get(slug=_MM_SLUG)
        corvus_belli, created = Retailer.objects.get_or_create(
            slug=_CORVUS_BELLI_US_SLUG,
            defaults={
                'name': 'Corvus Belli US',
                'website': 'https://store.corvusbelli.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {corvus_belli.name}')

        seeded = 0
        skipped = 0
        for gw_sku, usd_msrp, usd_price, url, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue
            _apply_row(product, retailer, corvus_belli, usd_msrp, usd_price, url, in_stock)
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Infinity NA2 Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
