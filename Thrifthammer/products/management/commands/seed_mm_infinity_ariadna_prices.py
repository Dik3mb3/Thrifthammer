"""
Seed Miniature Market US prices and the USD MSRP for Infinity: Ariadna.

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
status of each listing checked on 2026-10-02 (ARI-001, 002, 003, 004 and 031
were in stock, the rest out of stock, which keeps their real price with
in_stock=False and not_available=False). The scraper corrects stock on its
next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing list were confirmed with the user (2026-10-02).

31 of 33 Ariadna SKUs matched. 2 SKUs not in the sheet (confirmed by searching
it): ARI-032 Antipode Assault Pack, ARI-033 Traktor Muls. Regiment of
Artillery and Support.

Notes on individual picks (all confirmed with the user):
- ARI-016 Ariadna Expansion Pack Alpha is MM's "CodeOne: Ariadna - Booster Pack
  Alpha" (the same renamed pack the UK side used).
- ARI-020 Uxia McNeill (Assault Pistol) is MM's "Ariadna - Uxia McNeill": its
  title does not name the weapon but its page names the Assault Pistol.
- ARI-031 Dog-Warriors is MM's "Dog-Warriors (4)" ($78.00 retail), which is
  about twice the UK MSRP scale (GBP 38.65); matched on the identical name.
- ARI-015 (Boarding Shotgun) and ARI-017 (Polaris Team Beast Pack) are MM's only
  listings for those products and carry "CodeOne" in their titles.
- ARI-007 is MM's "Ariadna - Action Pack" (the other Ariadna action pack in the
  sheet is the Tartary Army Corps one, ARI-022).
- Miniature Market files ARI-001 under "NA2" in its own title.

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
    ('ARI-001', Decimal('52.00'), Decimal('38.99'), 'https://www.miniaturemarket.com/Infinity-NA2-Ioann-Bann-Varangian-Dog-Warrior-New-Arrival/CVB280787-1231', True),
    ('ARI-002', Decimal('20.40'), Decimal('12.99'), 'https://www.miniaturemarket.com/Infinty-Ariadna-1st-Highlander-S.A.S.-Chain-Rifle/CVB281131-1038', True),
    ('ARI-003', Decimal('58.00'), Decimal('36.99'), 'https://www.miniaturemarket.com/Infinity-Ariadna-Support-Pack/CVB281141-1204', True),
    ('ARI-004', Decimal('45.50'), Decimal('36.99'), 'https://www.miniaturemarket.com/infinity-ariadna-vystrel-mobile-artillery-regiment-cvb281140-1165.html', True),
    ('ARI-005', Decimal('51.50'), Decimal('28.99'), 'https://www.miniaturemarket.com/infinity-ariadna-tak-expansion-pack-alpha-cvb281139-1156.html', False),
    ('ARI-006', Decimal('65.99'), Decimal('41.99'), 'https://www.miniaturemarket.com/infinity-ariadna-kibervolk-patrol-cvb281138.html', False),
    ('ARI-007', Decimal('107.99'), Decimal('77.99'), 'https://www.miniaturemarket.com/infinity-ariadna-action-pack-cvb281133-1066.html', False),
    ('ARI-008', Decimal('95.94'), Decimal('86.99'), 'https://www.miniaturemarket.com/infinity-ariadna-reinforcements-ariadna-pack-alpha-cvb281134-1072.html', False),
    ('ARI-009', Decimal('21.49'), Decimal('19.99'), 'https://www.miniaturemarket.com/infinity-ariadna-highlander-cateran-cvb281132-1057.html', False),
    ('ARI-010', Decimal('55.49'), Decimal('49.99'), 'https://www.miniaturemarket.com/infinity-ariadna-kosmoflot-support-pack-cvb281131-1018.html', False),
    ('ARI-011', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-ariadna-patchers-structural-response-team-cvb281130-1006.html', False),
    ('ARI-012', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/infinity-ariadna-kosmoflot-expansion-pack-alpha-cvb281128-0979-289580.html', False),
    ('ARI-013', Decimal('39.49'), Decimal('35.99'), 'https://www.miniaturemarket.com/cvb281125-0969.html', False),
    ('ARI-014', Decimal('55.99'), Decimal('50.99'), 'https://www.miniaturemarket.com/cvb281124-0961.html', False),
    ('ARI-015', Decimal('17.99'), Decimal('16.99'), 'https://www.miniaturemarket.com/cvb281123-0949.html', False),
    ('ARI-016', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb281121-0930.html', False),
    ('ARI-017', Decimal('44.49'), Decimal('39.99'), 'https://www.miniaturemarket.com/cvb281119-0908.html', False),
    ('ARI-018', Decimal('23.99'), Decimal('21.99'), 'https://www.miniaturemarket.com/cvb281117-0896.html', False),
    ('ARI-019', Decimal('16.99'), Decimal('14.99'), 'https://www.miniaturemarket.com/cvb281114-0872.html', False),
    ('ARI-020', Decimal('16.99'), Decimal('15.99'), 'https://www.miniaturemarket.com/cvb281113-0864.html', False),
    ('ARI-021', Decimal('55.99'), Decimal('50.99'), 'https://www.miniaturemarket.com/cvb281111-0842.html', False),
    ('ARI-022', Decimal('107.99'), Decimal('96.99'), 'https://www.miniaturemarket.com/cvb281112-0851.html', False),
    ('ARI-023', Decimal('18.99'), Decimal('17.99'), 'https://www.miniaturemarket.com/cvb281110-0814.html', False),
    ('ARI-024', Decimal('18.99'), Decimal('17.99'), 'https://www.miniaturemarket.com/cvb281109-0797.html', False),
    ('ARI-025', Decimal('53.99'), Decimal('48.99'), 'https://www.miniaturemarket.com/cvb281106-0776.html', False),
    ('ARI-026', Decimal('44.49'), Decimal('39.99'), 'https://www.miniaturemarket.com/cvb281105-0765.html', False),
    ('ARI-027', Decimal('39.49'), Decimal('35.99'), 'https://www.miniaturemarket.com/cvb281103-0744.html', False),
    ('ARI-028', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/cvb281101-0689.html', False),
    ('ARI-029', Decimal('28.99'), Decimal('25.99'), 'https://www.miniaturemarket.com/cvb280180-0574.html', False),
    ('ARI-030', Decimal('16.99'), Decimal('14.99'), 'https://www.miniaturemarket.com/cvb280177-0549.html', False),
    ('ARI-031', Decimal('78.00'), Decimal('70.99'), 'https://www.miniaturemarket.com/cvb280169-0497.html', True),
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
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: Ariadna. Idempotent.'

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
                f'Seeded {seeded} Infinity Ariadna Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
