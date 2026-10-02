"""
Seed Miniature Market US prices and the USD MSRP for Infinity: Nomads.

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
status of each listing checked on 2026-10-02 (NOM-001, 003, 008, 010 and 029
were in stock, the rest out of stock, which keeps their real price with
in_stock=False and not_available=False). The scraper corrects stock on its
next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing list were confirmed with the user (2026-10-02).

28 of 36 Nomads SKUs written here. Not written:
- Not in the sheet (confirmed by searching it): NOM-002 Nomads Army Pack,
  NOM-004 Switchers Gruppa, NOM-015 Bakunin Expansion Pack Beta, NOM-018
  Sputniks, NOM-022 Tomcats, NOM-024 Gator Squadron, NOM-035 Tunguska
  Interventors.
- Deliberately unmatched (confirmed with the user): NOM-005 Nomads Hero,
  Wolfgang Amadeus Wolff. MM's only listing is "CodeOne: Wolfgang Amadeus Wolff,
  Wulver Bounty Hunter", the same earlier release the UK side did not treat as
  our Hero.

Notes on individual picks (all confirmed with the user):
- NOM-006 is "Essentials Booster Pack Alpha" (36.00 retail), not the "CodeOne"
  Booster Pack Alpha (47.99).
- NOM-008 is "Essentials Szalamandra Squadron TAG Pack" (66.00 retail), not the
  "CodeOne: Szalamandra Squadron" listing (71.49).
- NOM-009 is the plain "Zonds Remotes Pack", not the "CodeOne" Remotes Pack.
- NOM-007 Go-Pods is MM's singular "Go-Pod"; its page describes a two-miniature
  box.
- NOM-033 Mobile Brigada is MM's "Mobile Brigadas (4)".
- NOM-017 (35.99) and NOM-020 (23.99) have US retail prices below the UK MSRPs
  supplied for them (41.65 and 31.70); matched on identical names.

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
    ('NOM-001', Decimal('57.00'), Decimal('41.99'), 'https://www.miniaturemarket.com/Infinity-Nomads-Gecko-Squadron-New-Arrival/CVB281553-1249', True),
    ('NOM-003', Decimal('36.00'), Decimal('32.99'), 'https://www.miniaturemarket.com/Infinity-Nomads-Tunguska-Triggermen/CVB281541-1146', True),
    ('NOM-006', Decimal('36.00'), Decimal('28.99'), 'https://www.miniaturemarket.com/infinity-nomads-essentials-booster-pack-alpha-cvb281544-1171.html', False),
    ('NOM-007', Decimal('68.00'), Decimal('54.99'), 'https://www.miniaturemarket.com/infinity-nomads-go-pod-cvb281543-1166.html', False),
    ('NOM-008', Decimal('66.00'), Decimal('52.99'), 'https://www.miniaturemarket.com/infinity-nomads-essentials-szalamandra-squadron-tag-pack-cvb281542-1159.html', True),
    ('NOM-009', Decimal('39.50'), Decimal('35.99'), 'https://www.miniaturemarket.com/infinity-nomads-zonds-remotes-pack-cvb281539-1139.html', False),
    ('NOM-010', Decimal('36.00'), Decimal('32.99'), 'https://www.miniaturemarket.com/infinity-nomads-support-pack-cvb281540-1144.html', True),
    ('NOM-011', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/infinity-nomads-moran-maasai-hunters-cvb281537-1097.html', False),
    ('NOM-012', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-nomads-zeros-cvb281534-1069.html', False),
    ('NOM-013', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/infinity-nomads-reinforcements-lizard-squadron-cvb281532-1058.html', False),
    ('NOM-014', Decimal('81.49'), Decimal('73.99'), 'https://www.miniaturemarket.com/infinity-nomads-reinforcements-pack-alpha-cvb281530-1055.html', False),
    ('NOM-016', Decimal('49.99'), Decimal('45.99'), 'https://www.miniaturemarket.com/infinity-nomads-bakunin-uberfallkommando-cvb281529-1050.html', False),
    ('NOM-017', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/infinity-nomads-bakunin-expansion-pack-alpha-cvb281525-1012.html', False),
    ('NOM-019', Decimal('43.99'), Decimal('39.99'), 'https://www.miniaturemarket.com/infinity-nomads-stigmata-cvb281524-1007.html', False),
    ('NOM-020', Decimal('23.99'), Decimal('21.99'), 'https://www.miniaturemarket.com/infinity-nomads-meteor-zond-boarding-shotgun-cvb281523.html', False),
    ('NOM-021', Decimal('71.49'), Decimal('64.99'), 'https://www.miniaturemarket.com/infinity-nomads-corregidor-fireteam-pack-beta-cvb281521-0992.html', False),
    ('NOM-023', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/infinity-nomads-corregidor-fireteam-pack-alpha-cvb281519-0985.html', False),
    ('NOM-025', Decimal('17.99'), Decimal('16.99'), 'https://www.miniaturemarket.com/cvb281508-0865.html', False),
    ('NOM-026', Decimal('53.99'), Decimal('48.99'), 'https://www.miniaturemarket.com/cvb281507-0853.html', False),
    ('NOM-027', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb281503-0792.html', False),
    ('NOM-028', Decimal('71.49'), Decimal('64.99'), 'https://www.miniaturemarket.com/cvb281502-0781.html', False),
    ('NOM-029', Decimal('23.99'), Decimal('21.99'), 'https://www.miniaturemarket.com/cvb280599-0752.html', True),
    ('NOM-030', Decimal('55.99'), Decimal('50.99'), 'https://www.miniaturemarket.com/cvb280597-0733.html', False),
    ('NOM-031', Decimal('20.49'), Decimal('18.99'), 'https://www.miniaturemarket.com/cvb280596-0724.html', False),
    ('NOM-032', Decimal('23.99'), Decimal('21.99'), 'https://www.miniaturemarket.com/cvb280594-0715.html', False),
    ('NOM-033', Decimal('55.99'), Decimal('50.99'), 'https://www.miniaturemarket.com/cvb280576-0552.html', False),
    ('NOM-034', Decimal('43.99'), Decimal('39.99'), 'https://www.miniaturemarket.com/cvb280574-0524.html', False),
    ('NOM-036', Decimal('46.99'), Decimal('42.99'), 'https://www.miniaturemarket.com/cvb280538-0231.html', False),
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
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: Nomads. Idempotent.'

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
                f'Seeded {seeded} Infinity Nomads Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
