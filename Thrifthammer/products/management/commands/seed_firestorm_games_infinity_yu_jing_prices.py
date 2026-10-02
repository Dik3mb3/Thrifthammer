"""
Seed Firestorm Games UK prices for Infinity: Yu Jing, and the GBP MSRP.

Firestorm shows two numbers per listing: a struck-through RRP and a lower
sale price. For Infinity (and ONLY Infinity -- explicit user instruction,
see the msrp exception notes in project memory) each matched SKU gets both:

- the sale price becomes the `firestorm-games` CurrentPrice, and
- the RRP becomes the GBP MSRP: the `corvus-belli-uk` CurrentPrice price and
  Product.msrp_gbp. Corvus Belli's own store only shows EUR, so Firestorm's
  RRP is the closest real UK list price available.

Both writes are create-only (price is only written while it is still None),
so a redeploy never resets a price a manual correction or a future live
updater has since changed. The Corvus Belli row keeps its own official
listing URL (Product.gw_url), never Firestorm's.

Source: https://www.firestormgames.co.uk/wargames-miniatures/infinity (one
long page; units are filed under sections that differ from Corvus Belli's
factions, so the WHOLE page was read) plus Firestorm's site search for the
SKUs not on that page. Every match was made by reading, not by script, and
the ambiguous ones were confirmed with the user (2026-10-02).

24 of 37 Yu Jing SKUs matched. Not matched:
- YUJ-001 Gui Feng Spec-Ops Bundle: skipped on the user's instruction (a
  bundle SKU with no listing of its own, same as PAN-001).
- 12 SKUs Firestorm does not list anywhere on the site (page and search,
  including alternate spellings): YUJ-021, 023, 025, 026, 028, 029, 031,
  032, 034, 035, 036, 037.

Notes on individual picks (all confirmed with the user):
- YUJ-004 Sun Tze (Thunderbolt Light Shotgun) is the same kit as Firestorm's
  "Sun Tze (Vulkan Shotgun)" listing (user, 2026-10-02).
- YUJ-009: the Infinity-prefixed Booster Pack Alpha (RRP 30.35, in stock) is
  used, not the sold-out "Yu Jing Booster Pack Alpha OLD" (RRP 39.00).
- YUJ-017 Invincible Army Expansion Pack is Firestorm's "Invincible Army
  Action Pack" (same product, different name).
- YUJ-022 is the Shaolin Warrior Monks box ("... Monks 2023"), not the two
  single-miniature Shaolin Warrior Monk listings.
- YUJ-030 Libertos is the Light Shotgun listing (Firestorm's other Libertos
  listing is the Submachine Gun variant).
- YUJ-003 and YUJ-008 sit in Firestorm's JSA section, not Yu Jing.
- YUJ-002 is a Firestorm PRE ORDER (dispatch expected 30/10/2026), recorded
  in_stock=True like every other live-purchasable pre-order in the catalog.
- YUJ-004 and YUJ-013 show "0 in Stock - Backorder" and YUJ-033 shows
  "0 in Stock - Unavailable" on Firestorm (checked 2026-10-02): real price
  kept, in_stock=False, not_available=False, per the sold-out-listing rule
  (never clear a real price to None just because a listing is temporarily
  unavailable). Sold-out cards carry an RRP too; only the category page's
  button data-price is missing, so the struck-through price was read.

Every URL carries Firestorm's affiliate code (?aff=6a4ab07d1c6f9) per
standing site policy -- never break this on any Firestorm URL.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'
_CORVUS_BELLI_SLUG = 'corvus-belli-uk'
_FIRESTORM_BASE = 'https://www.firestormgames.co.uk'
_AFFILIATE = '?aff=6a4ab07d1c6f9'

# (gw_sku, rrp, sale_price, firestorm_path, in_stock)
_PRICES = [
    ('YUJ-002', Decimal('34.00'), Decimal('30.60'), '/yu-jing-gui-feng-spec-ops', True),
    ('YUJ-003', Decimal('33.90'), Decimal('30.51'), '/infinity---jsa-ninjas-multi-sniperhacker', True),
    ('YUJ-004', Decimal('23.35'), Decimal('21.02'), '/yu-jing---sun-tze-vulkan-shotgun', False),
    ('YUJ-005', Decimal('54.04'), Decimal('48.64'), '/infinity---kuang-shi', True),
    ('YUJ-006', Decimal('66.30'), Decimal('59.67'), '/infinity---feiquan-imperial-tactical-wing', True),
    ('YUJ-007', Decimal('17.40'), Decimal('15.66'), '/infinity---yu-jing-hero-lei-gong-invincibles-lord-of-thunder', True),
    ('YUJ-008', Decimal('20.25'), Decimal('18.23'), '/jsa-hero-shinobu-kitsune-monofilament-ccw', True),
    ('YUJ-009', Decimal('30.35'), Decimal('27.32'), '/infinity---yu-jing-booster-pack-alpha', True),
    ('YUJ-010', Decimal('48.00'), Decimal('43.20'), '/infinity---yu-jing-blue-wolf-mongol-cavalry-tag-pack', True),
    ('YUJ-011', Decimal('42.05'), Decimal('37.84'), '/infinity---longwang-imperial-tag-police', True),
    ('YUJ-012', Decimal('29.79'), Decimal('26.81'), '/infinity---yu-jing-support-pack', True),
    ('YUJ-013', Decimal('34.75'), Decimal('31.27'), '/infinity---white-banner-expansion-pack-beta', False),
    ('YUJ-014', Decimal('84.25'), Decimal('75.83'), '/infinity---yu-jing-action-pack', True),
    ('YUJ-015', Decimal('39.69'), Decimal('35.72'), '/infinity---yu-jing---white-banner-expansion-pack-alpha', True),
    ('YUJ-016', Decimal('39.69'), Decimal('35.72'), '/yu-jing---yaoxie-remotes-lu-duanrui-shi', True),
    ('YUJ-017', Decimal('89.25'), Decimal('80.33'), '/yu-jing---invincible-army-action-pack', True),
    ('YUJ-018', Decimal('17.85'), Decimal('16.07'), '/infinity---yu-jing---guilang-hacker', True),
    ('YUJ-019', Decimal('46.59'), Decimal('41.93'), '/infinity---zuyong-invincibles', True),
    ('YUJ-020', Decimal('73.35'), Decimal('66.00'), '/reinforcements:-yu-jing-pack-alpha', True),
    ('YUJ-022', Decimal('41.65'), Decimal('37.48'), '/yu-jing---shaolin-warrior-monks-2023', True),
    ('YUJ-024', Decimal('36.69'), Decimal('33.02'), '/yu-jing---tian-gou-orbital-activity-squad', True),
    ('YUJ-027', Decimal('44.60'), Decimal('40.14'), '/yu-jing---jujak-regiment-korean-shock-infantry', True),
    ('YUJ-030', Decimal('13.89'), Decimal('12.49'), '/na2---libertos-freedom-fighters-light-shotgun', True),
    ('YUJ-033', Decimal('13.89'), Decimal('12.50'), '/infinity-dragon-lady-imperial-service-judge', False),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: Yu Jing. Idempotent.'

    def handle(self, *args, **options):
        firestorm, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': f'{_FIRESTORM_BASE}/{_AFFILIATE}',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {firestorm.name}')
        corvus_belli, created = Retailer.objects.get_or_create(
            slug=_CORVUS_BELLI_SLUG,
            defaults={
                'name': 'Corvus Belli',
                'website': 'https://store.corvusbelli.com',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {corvus_belli.name}')

        seeded = 0
        skipped = 0
        for gw_sku, rrp, sale_price, path, in_stock in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue

            firestorm_defaults = {
                'url': f'{_FIRESTORM_BASE}{path}{_AFFILIATE}',
                'in_stock': in_stock,
                'not_available': False,
                'currency': 'GBP',
            }
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=firestorm,
                defaults=firestorm_defaults,
                create_defaults={**firestorm_defaults, 'price': sale_price},
            )

            if product.msrp_gbp is None:
                product.msrp_gbp = rrp
                product.save(update_fields=['msrp_gbp'])

            corvus_row, _ = CurrentPrice.objects.get_or_create(
                product=product,
                retailer=corvus_belli,
                defaults={
                    'url': product.gw_url,
                    'price': None,
                    'currency': 'GBP',
                    'in_stock': False,
                    'not_available': True,
                },
            )
            if corvus_row.price is None:
                corvus_row.price = rrp
                corvus_row.currency = 'GBP'
                corvus_row.in_stock = True
                corvus_row.not_available = False
                corvus_row.save(update_fields=['price', 'currency', 'in_stock', 'not_available'])
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Infinity Yu Jing Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
