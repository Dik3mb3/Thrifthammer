"""
Seed Miniature Market US prices and the USD MSRP for Infinity: Yu Jing.

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
status of each listing checked on 2026-10-02 (YUJ-005, 006, 008, 014 and 017
were in stock, the rest out of stock, which keeps their real price with
in_stock=False and not_available=False). The scraper corrects stock on its
next run.

Every match was made by reading, not by script, every URL was fetched live and
its page title and price confirmed against the sheet, and the picks and the
missing list were confirmed with the user (2026-10-02).

30 of 37 Yu Jing SKUs written here. Not written:
- Not in the sheet (confirmed by searching it): YUJ-001 Gui Feng Spec-Ops
  Bundle, YUJ-002 Gui Feng Spec-Ops, YUJ-025 White Banner Action Pack, YUJ-031
  Mowang Troops, YUJ-035 Guijia Squadron.
- Deliberately unmatched (confirmed with the user): YUJ-003 Ninjas (MM's only
  listing is the old two-model "Yu-Jing - Ninjas (2)", $23.99, against a UK MSRP
  of 33.90) and YUJ-036 Yan Huo Invincible (MM's "(HMC) (1)" is $24.99, against
  a UK MSRP of 31.70).

Notes on individual picks (all confirmed with the user):
- YUJ-017 Invincible Army Expansion Pack is MM's "Invincible Army Expansion
  Pack" ($44.49 / $40.99), chosen by the user over MM's "Invincible Army
  Action Pack" ($107.99 / $97.99). NOTE: the UK side mapped this SKU to
  Firestorm's Action Pack (GBP 89.25), so the UK and US data for it differ.
- YUJ-004 Sun Tze is MM's "Sun Tze (Boarding Shotgun)" (our SKU is the
  Thunderbolt Light Shotgun version; same treatment as the UK Vulkan Shotgun).
- YUJ-005 Kuang Shi is the new box (2 chain rifles + 2 boarding shotguns,
  new sculpt), not the old "Kuang Shi (4)".
- YUJ-009, 010 and 012 are the "Essentials" (Booster Pack Alpha, Blue Wolf TAG
  Pack) and plain (Support Pack) listings, not the "CodeOne" or older ones.
- YUJ-014 is the newer "Yu Jing - Yu Jing Action Pack" (99.99 retail).
- YUJ-015 is MM's "White Banner Pack Alpha"; YUJ-020 is MM's "Yu Jing - Pack
  Alpha" (our "Reinforcements: Yu Jing Pack Alpha").
- YUJ-030 Libertos is "NA2 - Libertos Freedom Fighters (1)" (its page names the
  Light Shotgun); the "NA2 - Libertos" listing is the Submachine Gun variant.
- Miniature Market files YUJ-008 under "JSA" and YUJ-030 under "NA2" in its
  own titles.

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
    ('YUJ-004', Decimal('17.99'), Decimal('16.99'), 'https://www.miniaturemarket.com/cvb280316-0076.html', False),
    ('YUJ-005', Decimal('62.50'), Decimal('39.99'), 'https://www.miniaturemarket.com/Infinity-Yu-Jing-Kuang-Shi/CVB281361-1203', True),
    ('YUJ-006', Decimal('63.50'), Decimal('57.99'), 'https://www.miniaturemarket.com/Infinity-Yu-Jing-Feiquan-Imperial-Tactical-Wing/CVB281359-1193', True),
    ('YUJ-007', Decimal('22.99'), Decimal('20.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-lei-gong-invincibles-lord-of-thunder-cvb281331-0968.html', False),
    ('YUJ-008', Decimal('24.00'), Decimal('19.99'), 'https://www.miniaturemarket.com/infinity-jsa-essentials-hero-shinobu-kitsune-monofilament-ccw-cvb281714-1170.html', True),
    ('YUJ-009', Decimal('36.00'), Decimal('28.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-yu-jing-essentials-booster-pack-alpha-cvb281355-1168.html', False),
    ('YUJ-010', Decimal('48.00'), Decimal('38.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-essentials-blue-wolf-mongol-cavalry-tag-pack-cvb281353-1158.html', False),
    ('YUJ-011', Decimal('50.50'), Decimal('39.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-longwang-imperial-tag-police-cvb281350-1145.html', False),
    ('YUJ-012', Decimal('36.00'), Decimal('24.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-support-pack-cvb281349-1141.html', False),
    ('YUJ-013', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-white-banner-expansion-pack-beta-cvb2813511152.html', False),
    ('YUJ-014', Decimal('99.99'), Decimal('89.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-yu-jing-action-pack-cvb281346-1127.html', True),
    ('YUJ-015', Decimal('47.99'), Decimal('34.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-white-banner-pack-alpha-cvb281345-1105.html', False),
    ('YUJ-016', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-yaoxie-remotes-lu-duan-rui-shi-cvb281343-1088.html', False),
    ('YUJ-017', Decimal('44.49'), Decimal('40.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-invincible-army-expansion-pack-cvb281342-1085.html', True),
    ('YUJ-018', Decimal('21.49'), Decimal('19.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-guilang-hacker-cvb281340-1064.html', False),
    ('YUJ-019', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-zuyong-invincibles-cvb281339-1048.html', False),
    ('YUJ-020', Decimal('88.49'), Decimal('80.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-pack-alpha-cvb281335-1021.html', False),
    ('YUJ-021', Decimal('16.49'), Decimal('14.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-bixie-the-jade-champion-cvb281334-1015.html', False),
    ('YUJ-022', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-shaolin-warrior-monks-cvb281337-1042.html', False),
    ('YUJ-023', Decimal('20.49'), Decimal('18.99'), 'https://www.miniaturemarket.com/infinity-yu-jing-hulang-shocktroopers-submachine-gun-cvb281333.html', False),
    ('YUJ-024', Decimal('41.99'), Decimal('37.99'), 'https://www.miniaturemarket.com/cvb281330-0951.html', False),
    ('YUJ-026', Decimal('49.99'), Decimal('45.99'), 'https://www.miniaturemarket.com/cvb281326-0918.html', False),
    ('YUJ-027', Decimal('49.99'), Decimal('44.99'), 'https://www.miniaturemarket.com/cvb281322-0897.html', False),
    ('YUJ-028', Decimal('59.99'), Decimal('54.99'), 'https://www.miniaturemarket.com/cvb281321-0885.html', False),
    ('YUJ-029', Decimal('65.49'), Decimal('58.99'), 'https://www.miniaturemarket.com/cvb280034-0837.html', False),
    ('YUJ-030', Decimal('15.49'), Decimal('13.99'), 'https://www.miniaturemarket.com/cvb280743-0802.html', False),
    ('YUJ-032', Decimal('23.99'), Decimal('21.99'), 'https://www.miniaturemarket.com/cvb280396-0641.html', False),
    ('YUJ-033', Decimal('16.99'), Decimal('14.99'), 'https://www.miniaturemarket.com/cvb280383-0576.html', False),
    ('YUJ-034', Decimal('53.99'), Decimal('48.99'), 'https://www.miniaturemarket.com/cvb280381-0568.html', False),
    ('YUJ-037', Decimal('47.99'), Decimal('43.99'), 'https://www.miniaturemarket.com/cvb280354-0339.html', False),
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
    help = 'Seed Miniature Market US prices and USD MSRPs (sheet Retail Price) for Infinity: Yu Jing. Idempotent.'

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
                f'Seeded {seeded} Infinity Yu Jing Miniature Market prices and USD MSRPs. Skipped: {skipped}.'
            )
        )
