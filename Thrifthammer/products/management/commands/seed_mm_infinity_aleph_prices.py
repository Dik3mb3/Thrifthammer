"""
Seed Miniature Market US prices and the USD MSRP for Infinity: ALEPH.

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
status of each listing checked on 2026-10-02 (ALE-001, 002, 004 and 006 were
in stock, the rest out of stock, which keeps their real price with
in_stock=False and not_available=False). The scraper corrects stock on its
next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing list were confirmed with the user (2026-10-02).

18 of 22 ALEPH SKUs written here. Not written:
- Not in the sheet (confirmed by searching it): ALE-003 ALEPH Army Pack, ALE-014
  Rebot Remotes Pack, ALE-015 Dactyls.
- Deliberately unmatched (confirmed with the user): ALE-016 Marut. MM's "ALEPH -
  Marut" is $46.99 retail against a UK MSRP of 93.99 (about half the UK scale,
  so likely the older single-model release).

Notes on individual picks (all confirmed with the user):
- ALE-002 ALEPH Support Pack is "ALEPH - Essentials Support Pack (New Arrival)"
  (36.00 retail), not the older "CodeOne: ALEPH - Support Pack" (38.49).
- ALE-012 ALEPH Expansion Pack Beta is MM's "CodeOne: ALEPH - Booster Pack Beta"
  (the same renamed pack the UK side used).
- ALE-005 Posthumans is the main "ALEPH - Posthumans" box (59.99 retail), not
  the older "Posthumans Unit Box" (39.49) or the 2G Proxies pack.
- ALE-011 Phoenix and ALE-013 Agamemnon are MM's only listings for those
  products and carry "CodeOne" in their titles.

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
    ('ALE-001', Decimal('75.00'), Decimal('55.99'), 'https://www.miniaturemarket.com/Infinity-ALEPH-Tarkshyas-Interception-Wing-New-Arrival/CVB280897-1253', True),
    ('ALE-002', Decimal('36.00'), Decimal('27.99'), 'https://www.miniaturemarket.com/Infinity-ALEPH-Essentials-Support-Pack-New-Arrival/CVB280891-1209', True),
    ('ALE-004', Decimal('38.50'), Decimal('23.99'), 'https://www.miniaturemarket.com/Infinity-ALEPH-K2-Auxiliars/CVB280889-1201', True),
    ('ALE-005', Decimal('59.99'), Decimal('53.99'), 'https://www.miniaturemarket.com/infinity-aleph-posthumans-cvb280887.html', False),
    ('ALE-006', Decimal('39.50'), Decimal('35.99'), 'https://www.miniaturemarket.com/infinity-aleph-ajax-great-cvb280885-1086.html', True),
    ('ALE-007', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/infinity-aleph-atalanta-agemas-nco-spotbot-cvb280883-1074.html', False),
    ('ALE-008', Decimal('83.99'), Decimal('75.99'), 'https://www.miniaturemarket.com/infinity-aleph-reinforcements-pack-alpha-cvb280879-1036.html', False),
    ('ALE-009', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/infinity-aleph-myrmidons-cvb280881-1060.html', False),
    ('ALE-010', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/infinity-aleph-steel-phalanx-expansion-pack-alpha-cvb280876.html', False),
    ('ALE-011', Decimal('20.49'), Decimal('18.99'), 'https://www.miniaturemarket.com/infinity-codeone-aleph-phoenix-heavy-rocket-launcher-cvb280875-1011.html', False),
    ('ALE-012', Decimal('43.99'), Decimal('39.99'), 'https://www.miniaturemarket.com/infinity-codeone-aleph-booster-pack-beta-cvb280874.html', False),
    ('ALE-013', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/infinity-codeone-aleph-agamemnon-the-atreides-cvb280872-0983-289579.html', False),
    ('ALE-017', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/cvb280868-0931.html', False),
    ('ALE-018', Decimal('39.49'), Decimal('35.99'), 'https://www.miniaturemarket.com/cvb280864-0762.html', False),
    ('ALE-019', Decimal('16.99'), Decimal('14.99'), 'https://www.miniaturemarket.com/cvb280863-0756.html', False),
    ('ALE-020', Decimal('28.99'), Decimal('25.99'), 'https://www.miniaturemarket.com/cvb280857-0678.html', False),
    ('ALE-021', Decimal('24.99'), Decimal('22.99'), 'https://www.miniaturemarket.com/cvb280848-0571.html', False),
    ('ALE-022', Decimal('23.99'), Decimal('21.99'), 'https://www.miniaturemarket.com/cvb280842-0513.html', False),
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
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: ALEPH. Idempotent.'

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
                f'Seeded {seeded} Infinity ALEPH Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
