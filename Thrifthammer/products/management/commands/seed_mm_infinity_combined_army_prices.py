"""
Seed Miniature Market US prices and the USD MSRP for Infinity: Combined Army.

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
status of each listing checked on 2026-10-02 (CA-003, 006, 007, 009, 010 and
011 were in stock, the rest out of stock, which keeps their real price with
in_stock=False and not_available=False). The scraper corrects stock on its
next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing list were confirmed with the user (2026-10-02).

28 of 37 Combined Army SKUs written here. Not written:
- Not in the sheet (confirmed by searching it): CA-001 Nexus-7 Spec-Ops Bundle,
  CA-002 Nexus-7 Spec-Ops, CA-005 Overdron Batroids TAG Pack, CA-014 The
  Anathematics, CA-017 Combined Army Expansion Pack Alpha, CA-023 Morat Fireteam
  Pack, CA-028 Shasvastii Expansion Pack Gamma, CA-029 Shasvastii Sphinx.
- Deliberately unmatched (confirmed with the user): CA-004 Combined Army Booster
  Pack Alpha. MM's only listing is "CodeOne: Combined Army - Booster Pack Alpha"
  ($53.49 retail) against a UK MSRP of 25.45 (about half the US scale, so likely
  a different, older pack).

Notes on individual picks (all confirmed with the user):
- CA-003 is "Essentials Hero, The Charontids" (27.00 retail), not the older
  plain "The Charontids (Plasma Rifle)" listing (28.99).
- CA-007 is the plain "Combined Army - Support Pack" (36.00 retail), not the
  "CodeOne" Support Pack (35.99).
- CA-033 Raicho (71.49), CA-034 Bit & KISS! (27.49) and CA-035 Avatar (75.49) are
  matched on identical names even though their retail prices sit on a different
  scale from the UK MSRPs supplied for them (93.99, 16.90 and 106.99).
- CA-031 Greif Operators is MM's singular "NA2 - Greif Operator"; its page names
  the Breaker Pistols loadout.
- CA-012 Krakot Renegades is filed by MM under "NA2". CA-030 is MM's only
  Shasvastii Action Pack ("CodeOne" in its title).

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
    ('CA-003', Decimal('27.00'), Decimal('20.99'), 'https://www.miniaturemarket.com/Infinity-Combined-Army-Essentials-Hero-The-Charontids-Plasma-Rifle-New-Arrival/CVB281653-1236', True),
    ('CA-006', Decimal('39.60'), Decimal('24.99'), 'https://www.miniaturemarket.com/Infinty-Combined-Army-Drone-Remotes-Pack/CVB281647-1213', True),
    ('CA-007', Decimal('36.00'), Decimal('22.99'), 'https://www.miniaturemarket.com/Infinity-Combined-Army-Support-Pack/CVB281646-1212', True),
    ('CA-008', Decimal('36.00'), Decimal('32.99'), 'https://www.miniaturemarket.com/Infinity-Combined-Army-Achilles/CVB281640-1198', False),
    ('CA-009', Decimal('54.00'), Decimal('33.99'), 'https://www.miniaturemarket.com/Infinity-Combined-Army-Paint-Set-with-Harbinger-Paramedic-Exclusive-Miniature/CVB281638-1189', True),
    ('CA-010', Decimal('66.00'), Decimal('59.99'), 'https://www.miniaturemarket.com/Infinity-Combined-Army-Juggernauts-Armored-Assault-Brigade-MULTI-HMG/CVB281637-1188', True),
    ('CA-011', Decimal('120.00'), Decimal('108.00'), 'https://www.miniaturemarket.com/Infinity-Combined-Army-Next-Wave-Action-Pack/CVB281636-1187', True),
    ('CA-012', Decimal('30.00'), Decimal('23.99'), 'https://www.miniaturemarket.com/infinity-na2-krakot-renegades-cvb280781-1157.html', False),
    ('CA-013', Decimal('47.99'), Decimal('29.99'), 'https://www.miniaturemarket.com/infinity-combined-army-shasvastii-expansion-pack-beta-cvb281635-1107.html', False),
    ('CA-015', Decimal('53.99'), Decimal('36.99'), 'https://www.miniaturemarket.com/infinity-combined-army-reinforcements-caskuda-cvb281632-1062.html', False),
    ('CA-016', Decimal('99.99'), Decimal('90.99'), 'https://www.miniaturemarket.com/infinity-combined-army-reinforcements-pack-alpha-cvb281630-1051.html', False),
    ('CA-018', Decimal('62.99'), Decimal('56.99'), 'https://www.miniaturemarket.com/infinity-combined-army-morat-expansion-pack-beta-cvb281628-1009.html', False),
    ('CA-019', Decimal('49.99'), Decimal('45.99'), 'https://www.miniaturemarket.com/infinity-combined-army-the-hungries-gakis-pretas-cvb281625-0986-289583.html', False),
    ('CA-020', Decimal('49.99'), Decimal('19.99'), 'https://www.miniaturemarket.com/infinity-combined-army-shasvastii-expansion-pack-alpha-cvb281624-0984.html', False),
    ('CA-021', Decimal('56.99'), Decimal('51.99'), 'https://www.miniaturemarket.com/cvb281623-0976.html', False),
    ('CA-022', Decimal('21.49'), Decimal('19.99'), 'https://www.miniaturemarket.com/cvb281622-0962.html', False),
    ('CA-024', Decimal('53.49'), Decimal('48.99'), 'https://www.miniaturemarket.com/cvb281620-0945.html', False),
    ('CA-025', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/cvb281617-0938.html', False),
    ('CA-026', Decimal('124.99'), Decimal('112.99'), 'https://www.miniaturemarket.com/cvb281616-0934.html', False),
    ('CA-027', Decimal('39.49'), Decimal('35.99'), 'https://www.miniaturemarket.com/cvb281613-0899.html', False),
    ('CA-030', Decimal('100.99'), Decimal('90.99'), 'https://www.miniaturemarket.com/cvb281603-0830.html', False),
    ('CA-031', Decimal('19.99'), Decimal('18.99'), 'https://www.miniaturemarket.com/cvb280747-0829.html', False),
    ('CA-032', Decimal('44.99'), Decimal('40.99'), 'https://www.miniaturemarket.com/cvb280699-0811.html', False),
    ('CA-033', Decimal('71.49'), Decimal('64.99'), 'https://www.miniaturemarket.com/cvb280692-0726.html', False),
    ('CA-034', Decimal('27.49'), Decimal('24.99'), 'https://www.miniaturemarket.com/cvb280689-0701.html', False),
    ('CA-035', Decimal('75.49'), Decimal('68.99'), 'https://www.miniaturemarket.com/cvb280686-0681.html', False),
    ('CA-036', Decimal('16.99'), Decimal('14.99'), 'https://www.miniaturemarket.com/cvb280685-0679.html', False),
    ('CA-037', Decimal('71.49'), Decimal('64.99'), 'https://www.miniaturemarket.com/cvb280677-0588.html', False),
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
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: Combined Army. Idempotent.'

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
                f'Seeded {seeded} Infinity Combined Army Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
