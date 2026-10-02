"""
Seed Miniature Market US prices and the USD MSRP for Infinity: Haqqislam.

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
status of each listing checked on 2026-10-02 (HQQ-002, 003, 004, 007, 012 and
015 were in stock, the rest out of stock, which keeps their real price with
in_stock=False and not_available=False). The scraper corrects stock on its
next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing list were confirmed with the user (2026-10-02).

22 of 28 Haqqislam SKUs matched. 6 SKUs not in the sheet (confirmed by
searching it): HQQ-001 Hassassin Expansion Pack Gamma, HQQ-006 Ramah Taskforce
Expansion Pack Alpha, HQQ-021 Khawarijs, HQQ-022 Hakims (Special Medical
Assistance Group), HQQ-024 Naffatun, HQQ-027 Kameel Remote.

Notes on individual picks (all confirmed with the user):
- HQQ-003 Yuan Yuan is MM's "NA2 - Yuan Yuan", a two-metal-miniature box (the
  box listing the UK side chose, not the single "(Chain Rifle)" blister).
- HQQ-004 Mukthar, Active Response Unit is the newer MM listing (Combi Rifle,
  retail 36.00), not the older 17.99 one.
- HQQ-019 Namurr's page names the Heavy Pistol and E/M CCW loadout.
- HQQ-014 and HQQ-015 are MM's only listings ("CodeOne" titles) for the
  Haqqislam Remotes Pack and Support Pack.
- Miniature Market files HQQ-003, 007 and 010 under "NA2" and HQQ-016 under
  "O-12/Haqqislam" in its own titles.

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
    ('HQQ-002', Decimal('63.50'), Decimal('40.99'), 'https://www.miniaturemarket.com/Infinity-Haqqislam-Haytham-Aero-Unit/CVB281432-1219', True),
    ('HQQ-003', Decimal('36.00'), Decimal('22.99'), 'https://www.miniaturemarket.com/Infinty-NA2-Yuan-Yuan/CVB280785-1217', True),
    ('HQQ-004', Decimal('36.00'), Decimal('22.99'), 'https://www.miniaturemarket.com/Infinity-Haqqislam-Mukthar-Active-Response-Unit/CVB281431-1215', True),
    ('HQQ-005', Decimal('75.00'), Decimal('67.99'), 'https://www.miniaturemarket.com/Infinity-Haqqislam-Zeybek-Aero-unit/CVB281430-1194', False),
    ('HQQ-007', Decimal('72.00'), Decimal('57.99'), 'https://www.miniaturemarket.com/infinity-na2-scarface-cordelia-mercenary-tag-team-cvb280782-1167.html', True),
    ('HQQ-008', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/infinity-haqqislam-hassassin-expansion-pack-alpha-cvb281419-1083.html', False),
    ('HQQ-009', Decimal('83.99'), Decimal('56.99'), 'https://www.miniaturemarket.com/infinity-haqqislam-reinforcements-pack-alpha-cvb281422-1035.html', False),
    ('HQQ-010', Decimal('23.99'), Decimal('21.99'), 'https://www.miniaturemarket.com/infinity-na2-fiddler-aristeias-ex-toymaker-cvb280770-1037.html', False),
    ('HQQ-011', Decimal('53.99'), Decimal('48.99'), 'https://www.miniaturemarket.com/infinity-haqqislam-hassassin-fireteam-pack-alpha-cvb281418-1017.html', False),
    ('HQQ-012', Decimal('17.50'), Decimal('15.99'), 'https://www.miniaturemarket.com/infinity-codeone-haqqislam-yara-haddad-ap-marksman-rifle-cvb281417-1010.html', True),
    ('HQQ-013', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-codeone-haqqislam-shakush-light-armored-unit-cvb281414-0982-289581.html', False),
    ('HQQ-014', Decimal('43.99'), Decimal('39.99'), 'https://www.miniaturemarket.com/infinity-codeone-haqqislam-remote-pack-cvb281413-0970-288860.html', False),
    ('HQQ-015', Decimal('39.49'), Decimal('35.99'), 'https://www.miniaturemarket.com/cvb281412-0964.html', True),
    ('HQQ-016', Decimal('17.99'), Decimal('16.99'), 'https://www.miniaturemarket.com/cvb281411-0905.html', False),
    ('HQQ-017', Decimal('23.99'), Decimal('21.99'), 'https://www.miniaturemarket.com/cvb281409-0876.html', False),
    ('HQQ-018', Decimal('107.99'), Decimal('96.99'), 'https://www.miniaturemarket.com/cvb281408-0844.html', False),
    ('HQQ-019', Decimal('15.49'), Decimal('13.99'), 'https://www.miniaturemarket.com/cvb281403-0777.html', False),
    ('HQQ-020', Decimal('43.99'), Decimal('39.99'), 'https://www.miniaturemarket.com/cvb281402-0770.html', False),
    ('HQQ-023', Decimal('89.49'), Decimal('80.99'), 'https://www.miniaturemarket.com/cvb280481-0584.html', False),
    ('HQQ-025', Decimal('53.49'), Decimal('48.99'), 'https://www.miniaturemarket.com/cvb280472-0518.html', False),
    ('HQQ-026', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/cvb280467-0477.html', False),
    ('HQQ-028', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb280431-0176.html', False),
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
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: Haqqislam. Idempotent.'

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
                f'Seeded {seeded} Infinity Haqqislam Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
