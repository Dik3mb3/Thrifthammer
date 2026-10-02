"""
Seed Miniature Market US prices and the USD MSRP for Infinity: O-12.

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
status of each listing checked on 2026-10-02 (O12-001 and O12-007 were in
stock, the rest out of stock, which keeps their real price with
in_stock=False and not_available=False). The scraper corrects stock on its
next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing SKU were confirmed with the user (2026-10-02).

22 of 23 O-12 SKUs matched. 1 SKU not in the sheet (confirmed by searching it):
O12-011 Fuzzbots.

Notes on individual picks (all confirmed with the user):
- O12-015 O-12 Expansion Pack Beta is MM's "CodeOne: O-12 - Booster Pack Beta"
  (the same renamed pack the UK side used).
- O12-016 O-12 Expansion Pack Alpha is MM's "CodeOne: O-12 - Booster Pack
  Alpha" (43.99 retail), not "O-12 - Torchlight Brigade Expansion Pack Alpha"
  (49.99): same renamed-booster pattern as ARI-016, ALE-012 and O12-015, and on
  the UK side the Torchlight Alpha was deliberately not used for this SKU.
- O12-005 is "O-12 - Raveneye Officer"; MM's separate "Raveneye" listing
  ($54.49 / $31.99) is a different product and is not used.
- O12-017, 019, 020 and 021 are MM's only listings for those products and
  carry "CodeOne" in their titles.

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
    ('O12-001', Decimal('54.00'), Decimal('48.99'), 'https://www.miniaturemarket.com/Infinity-O-12-Paint-Set-with-Kappa-Missile-Launcher-Exclusive-Miniature/CVB282036-1186', True),
    ('O12-002', Decimal('32.50'), Decimal('29.99'), 'https://www.miniaturemarket.com/infinity-o12-tinker-zetbot-remote-cvb282034-1133.html', False),
    ('O12-003', Decimal('22.00'), Decimal('20.99'), 'https://www.miniaturemarket.com/infinity-o12-jamie-arantes-netdroid-rover-cvb282033.html', False),
    ('O12-004', Decimal('55.99'), Decimal('35.99'), 'https://www.miniaturemarket.com/infinity-o-12-torchlight-brigade-expansion-pack-beta-cvb282032.html', False),
    ('O12-005', Decimal('17.99'), Decimal('16.99'), 'https://www.miniaturemarket.com/infinity-o-12-raveneye-officer-cvb282031-1108.html', False),
    ('O12-006', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-o-12-wreckers-fire-recon-armored-squad-cvb282029-1089.html', False),
    ('O12-007', Decimal('131.99'), Decimal('94.99'), 'https://www.miniaturemarket.com/infinity-o-12-torchlight-brigade-action-pack-cvb282027-1071.html', True),
    ('O12-008', Decimal('83.99'), Decimal('46.99'), 'https://www.miniaturemarket.com/infinity-o-12-reinforcement-pack-alpha-cvb282025-1052.html', False),
    ('O12-009', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/infinity-o-12-starmada-expansion-pack-alpha-cvb282024-1008.html', False),
    ('O12-010', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/infinity-o-12-roadbots-highway-patrol-cvb282023-0980.html', False),
    ('O12-012', Decimal('17.99'), Decimal('16.99'), 'https://www.miniaturemarket.com/cvb282014-0884.html', False),
    ('O12-013', Decimal('59.49'), Decimal('53.99'), 'https://www.miniaturemarket.com/cvb282012-0874.html', False),
    ('O12-014', Decimal('59.99'), Decimal('54.99'), 'https://www.miniaturemarket.com/cvb282011-0868.html', False),
    ('O12-015', Decimal('43.99'), Decimal('39.99'), 'https://www.miniaturemarket.com/cvb282010-0863.html', False),
    ('O12-016', Decimal('43.99'), Decimal('39.99'), 'https://www.miniaturemarket.com/cvb282009-0854.html', False),
    ('O12-017', Decimal('69.49'), Decimal('62.99'), 'https://www.miniaturemarket.com/cvb282008-0846.html', False),
    ('O12-018', Decimal('100.99'), Decimal('90.99'), 'https://www.miniaturemarket.com/cvb282007-0836.html', False),
    ('O12-019', Decimal('49.99'), Decimal('45.99'), 'https://www.miniaturemarket.com/cvb282004-0817.html', False),
    ('O12-020', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb282006-0832.html', False),
    ('O12-021', Decimal('100.99'), Decimal('90.99'), 'https://www.miniaturemarket.com/cvb282005-0826.html', False),
    ('O12-022', Decimal('28.99'), Decimal('25.99'), 'https://www.miniaturemarket.com/cvb282002-0809.html', False),
    ('O12-023', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/cvb282001-0803.html', False),
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
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: O-12. Idempotent.'

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
                f'Seeded {seeded} Infinity O-12 Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
