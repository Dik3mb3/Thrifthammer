"""
Seed Miniature Market US prices and the USD MSRP for Infinity: PanOceania.

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
status of each listing checked on 2026-10-02 (four listings were in stock,
the rest out of stock, which keeps their real price with in_stock=False and
not_available=False). The scraper corrects stock on its next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing list were confirmed with the user (2026-10-02).

37 of 48 PanOceania SKUs matched. 11 SKUs not in the sheet: PAN-001 Indigo
Spec-Ops Bundle, PAN-002 Indigo Spec-Ops, PAN-003 Optimate Agent Maximus,
PAN-028 Karhu Special Team, PAN-029 PanOceania Headquarters Pack, PAN-031
WinterFor Action Pack, PAN-033 Knight of Santiago, PAN-035 Motorized Bounty
Hunters, PAN-043 Orc Troops, PAN-046 Miranda Ashcroft, PAN-048 Mulebots.

Notes on individual picks (all confirmed with the user):
- PAN-005 is "Essentials Hero, Jeanne d'Arc 2.0" (our catalog name is "PanOceania
  Hero, Jeanne d'Arc 2.0"), not the plain "Jeanne d'Arc 2.0" listing.
- PAN-006 is "Essentials Booster Pack Alpha" (retail 36.00, parallel to the
  confirmed UK 36.00 listing), not the older "Booster Pack Alpha" (retail 49.99).
- PAN-011 is the plain "Infinity: PanOceania - Dronbot Remotes Pack", not the
  "CodeOne" duplicate listing.
- PAN-023 is Miniature Market's "PanOceania - Pack Alpha" (our "Reinforcements:
  PanOceania Pack Alpha").
- PAN-035 is deliberately NOT matched to "NA2 - Motorized Bounty Hunter"
  (singular, 23.99): that is the single-model release, while our SKU is the
  multi-model box.
- Miniature Market files PAN-016, 017, 020, 022, 036, 040 and 041 under "NA2",
  PAN-018 under "O-12" and PAN-021 under "ALEPH" in its own titles.

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
    ('PAN-004', Decimal('54.00'), Decimal('33.99'), 'https://www.miniaturemarket.com/Infinity-PanOceania-Kestrel-Expansion-Pack-Delta/CVB281252-1218', True),
    ('PAN-005', Decimal('24.00'), Decimal('19.99'), 'https://www.miniaturemarket.com/infinity-panoceania-essentials-hero-jeanne-darc-20-mobility-armor-cvb281250-1169.html', False),
    ('PAN-006', Decimal('36.00'), Decimal('28.99'), 'https://www.miniaturemarket.com/infinity-panoceania-essentials-booster-pack-alpha-cvb281248-1160.html', False),
    ('PAN-007', Decimal('49.00'), Decimal('39.99'), 'https://www.miniaturemarket.com/infinity-panoceania-drummers-mobile-support-section-cvb281247-1151.html', True),
    ('PAN-008', Decimal('56.00'), Decimal('50.99'), 'https://www.miniaturemarket.com/infinity-panoceania-cutters-tag-pack-cvb281246-1142.html', True),
    ('PAN-009', Decimal('54.00'), Decimal('48.99'), 'https://www.miniaturemarket.com/infinity-panoceania-paint-set-with-fusilier-paramedic-cvb281249-1162.html', False),
    ('PAN-010', Decimal('55.00'), Decimal('49.99'), 'https://www.miniaturemarket.com/infinity-panoceania-kestrel-expansion-pack-gamma-cvb281243-1131.html', False),
    ('PAN-011', Decimal('39.50'), Decimal('35.99'), 'https://www.miniaturemarket.com/infinity-panoceania-dronbot-remotes-pack-cvb281243-1128.html', False),
    ('PAN-012', Decimal('35.99'), Decimal('32.99'), 'https://www.miniaturemarket.com/infinity-panoceania-panoceania-support-pack-cvb281245-1137.html', False),
    ('PAN-013', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/infinity-panoceania-kestrel-expansion-pack-beta-cbv2812421125.html', False),
    ('PAN-014', Decimal('18.99'), Decimal('17.99'), 'https://www.miniaturemarket.com/infinity-panoceania-dr-priya-harper-archeo-raider-cvb281244.html', True),
    ('PAN-015', Decimal('78.99'), Decimal('71.99'), 'https://www.miniaturemarket.com/infinity-panoceania-army-pack-cvb281242.html', False),
    ('PAN-016', Decimal('21.49'), Decimal('19.99'), 'https://www.miniaturemarket.com/infinity-na2-beasthunters-free-guild-tactical-bow-cvb280780.html', False),
    ('PAN-017', Decimal('55.99'), Decimal('50.99'), 'https://www.miniaturemarket.com/infinity-na2-triphammers-repurposed-industrial-tags-cvb280778-1095.html', False),
    ('PAN-018', Decimal('21.49'), Decimal('11.99'), 'https://www.miniaturemarket.com/infinity-o-12-freelance-operator-samsa-plasma-rifle-cvb280779-1103.html', False),
    ('PAN-019', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-panoceania-tikbalangs-armored-chasseurs-acontecimento-cvb281239-1093.html', False),
    ('PAN-020', Decimal('17.99'), Decimal('16.99'), 'https://www.miniaturemarket.com/infinity-na2-warcors-war-correspondents-cvb280776-1076.html', False),
    ('PAN-021', Decimal('41.90'), Decimal('37.99'), 'https://www.miniaturemarket.com/infinity-aleph-maximus-optimate-hexadome-legend-cvb280882-1067.html', False),
    ('PAN-022', Decimal('24.99'), Decimal('22.99'), 'https://www.miniaturemarket.com/infinity-na2-diggers-armed-prospectors-chain-rifle-cvb280772-1059.html', False),
    ('PAN-023', Decimal('71.49'), Decimal('64.99'), 'https://www.miniaturemarket.com/infinity-panoceania-pack-alpha-cvb281235-1020.html', False),
    ('PAN-024', Decimal('53.99'), Decimal('48.99'), 'https://www.miniaturemarket.com/infinity-panoceania-military-orders-expansion-pack-alpha-cvb281237-1041.html', False),
    ('PAN-025', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/infinity-panoceania-armbots-cvb281234-1013.html', False),
    ('PAN-026', Decimal('49.99'), Decimal('45.99'), 'https://www.miniaturemarket.com/infinity-dire-foes-mission-pack-12-troubled-theft-cvb280048-0994.html', False),
    ('PAN-027', Decimal('107.99'), Decimal('96.99'), 'https://www.miniaturemarket.com/infinity-panoceania-military-order-hospitaller-action-pack-cvb281233-0991.html', False),
    ('PAN-030', Decimal('16.99'), Decimal('14.99'), 'https://www.miniaturemarket.com/cvb281230-0943.html', False),
    ('PAN-032', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb281228-0923.html', False),
    ('PAN-034', Decimal('49.99'), Decimal('45.99'), 'https://www.miniaturemarket.com/cvb281223-0895.html', False),
    ('PAN-036', Decimal('15.49'), Decimal('13.99'), 'https://www.miniaturemarket.com/cvb280757-0894.html', False),
    ('PAN-037', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb281222-0883.html', False),
    ('PAN-038', Decimal('69.49'), Decimal('62.99'), 'https://www.miniaturemarket.com/cvb281220-0878.html', False),
    ('PAN-039', Decimal('119.99'), Decimal('107.99'), 'https://www.miniaturemarket.com/cvb281220-0870.html', False),
    ('PAN-040', Decimal('18.99'), Decimal('17.99'), 'https://www.miniaturemarket.com/cvb280752-0869.html', False),
    ('PAN-041', Decimal('18.99'), Decimal('17.99'), 'https://www.miniaturemarket.com/cvb280751-0861.html', False),
    ('PAN-042', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb-281012-0801.html', False),
    ('PAN-044', Decimal('16.99'), Decimal('15.99'), 'https://www.miniaturemarket.com/cvb281209-0769.html', False),
    ('PAN-045', Decimal('28.99'), Decimal('25.99'), 'https://www.miniaturemarket.com/cvb280290-0631.html', False),
    ('PAN-047', Decimal('66.99'), Decimal('60.99'), 'https://www.miniaturemarket.com/cvb280281-0550.html', False),
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
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: PanOceania. Idempotent.'

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
                f'Seeded {seeded} Infinity PanOceania Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
