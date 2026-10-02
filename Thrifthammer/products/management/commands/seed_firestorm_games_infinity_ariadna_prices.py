"""
Seed Firestorm Games UK prices for Infinity: Ariadna, and the GBP MSRP.

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
the missing list was confirmed with the user (2026-10-02).

20 of 33 Ariadna SKUs matched. 13 SKUs Firestorm does not list anywhere on
the site (page and search, including alternate spellings): ARI-009, 018,
020, 021, 022, 023, 024, 027, 029, 030, 031, 032, 033.

Notes on individual picks:
- ARI-007 Ariadna Action Pack is Firestorm's "Ariadna Action Pack (CodeOne)"
  (RRP 76.50). Firestorm's separate "USAriadna Action Pack" (RRP 89.25) is
  believed to be the US sectorial pack, which is not in the catalog.
- ARI-016 Ariadna Expansion Pack Alpha is Firestorm's "Ariadna - Booster
  Pack Alpha" (Corvus Belli's own image file for this SKU is named
  ariadna-booster-pack-alpha, i.e. the renamed Booster Pack).
- ARI-028 Kazak Spetsnazs is Firestorm's "Kazak Spetsnaz" (same product).
- ARI-001, ARI-004, ARI-011, ARI-013 and ARI-015 are filed by Firestorm under
  its JSA, Nomads, Combined Army, Mercenaries and Code One sections
  respectively, not under Ariadna.
- ARI-001, ARI-004 and ARI-013 show "0 in Stock - Backorder" on Firestorm
  (checked 2026-10-02): real price kept, in_stock=False, not_available=False,
  per the sold-out-listing rule (never clear a real price to None just
  because a listing is temporarily unavailable).

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
    ('ARI-001', Decimal('36.55'), Decimal('32.89'), '/infinity-jsa-ioann-bann-varangian-dog-warrior', False),
    ('ARI-002', Decimal('14.60'), Decimal('13.14'), '/infinity---1st-highlander-sas-chain-rifle', True),
    ('ARI-003', Decimal('54.40'), Decimal('48.96'), '/infinity---ariadna-support-pack', True),
    ('ARI-004', Decimal('38.40'), Decimal('34.56'), '/infinity---vystrel-mobile-artillery-regiment', False),
    ('ARI-005', Decimal('51.60'), Decimal('46.44'), '/infinity---tak-expansion-pack-alpha', True),
    ('ARI-006', Decimal('54.50'), Decimal('49.05'), '/infinity---kibervolk-patrol', True),
    ('ARI-007', Decimal('76.50'), Decimal('68.85'), '/ariadna-action-pack-codeone', True),
    ('ARI-008', Decimal('79.29'), Decimal('71.36'), '/infinity---reinforcements:-ariadna-pack-alpha', True),
    ('ARI-010', Decimal('47.60'), Decimal('42.84'), '/infinity---kosmoflot-support-pack', True),
    ('ARI-011', Decimal('41.65'), Decimal('37.48'), '/infinity---combined-army---patchers-structural-response-team', True),
    ('ARI-012', Decimal('36.69'), Decimal('33.03'), '/infinity---ariadna:-kosmoflot-expansion-pack-alpha', True),
    ('ARI-013', Decimal('30.00'), Decimal('27.01'), '/infinity---scots-guard', False),
    ('ARI-014', Decimal('46.59'), Decimal('41.93'), '/infinity---chernobog-armored-detachment', True),
    ('ARI-015', Decimal('14.90'), Decimal('13.41'), '/code-one---uxa-mcneill-boarding-shotgun-', True),
    ('ARI-016', Decimal('36.69'), Decimal('33.02'), '/ariadna---booster-pack-alpha', True),
    ('ARI-017', Decimal('36.69'), Decimal('33.02'), '/ariadna---polaris-team-beast-pack', True),
    ('ARI-019', Decimal('13.89'), Decimal('11.46'), '/ariadna---tankhunters-autocannon', True),
    ('ARI-025', Decimal('44.60'), Decimal('40.14'), '/ariadna---dynamo-reg-of-kazak-light-cavalry', True),
    ('ARI-026', Decimal('36.69'), Decimal('33.02'), '/ariadna---frontoviks-assault-separated-bat', True),
    ('ARI-028', Decimal('31.70'), Decimal('28.53'), '/ariadna---kazak-spetsnaz', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: Ariadna. Idempotent.'

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
                f'Seeded {seeded} Infinity Ariadna Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
