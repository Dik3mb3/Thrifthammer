"""
Seed Firestorm Games UK prices for Infinity: Combined Army, and the GBP MSRP.

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
the picks and the missing list were confirmed with the user (2026-10-02).

29 of 37 Combined Army SKUs matched. 8 SKUs not on Firestorm (page and site
search, including alternate spellings): CA-001 Nexus-7 Spec-Ops Bundle (a
bundle SKU, Firestorm lists only the single Spec-Ops box; same as PAN-001
and YUJ-001), CA-024 Bultrak Mobile Armored Regiment, CA-026 Morat
Aggression Forces Action Pack, CA-028 Shasvastii Expansion Pack Gamma,
CA-031 Greif Operators, CA-033 Raicho Armored Brigade, CA-034 Bit and
KISS!, CA-035 Avatar.

Notes on individual picks:
- CA-007 Combined Army Support Pack is Firestorm's "Infinity - Combined Army
  Support Pack" (RRP 31.20), not the "Combined Army - Support Pack OLD"
  (RRP 27.50). Firestorm has no Essentials version (confirmed with the user).
- CA-009 Combined Army Paint Set is Firestorm's "Combined Army Paint Set -
  Harbinger Paramedic Exclusive", the same pattern as PAN-009 (confirmed).
- CA-019 The Hungries is the "The Hungries: Gakis and Pretas" listing (RRP
  41.65). Firestorm's "Combined Army - The Hungries: Gakis & Pretas" listing
  shows no struck-through RRP, so it cannot supply an MSRP (confirmed).
- CA-002 Nexus-7 Spec-Ops is a Firestorm PRE ORDER (dispatch expected
  30/10/2026), recorded in_stock=True like every other live-purchasable
  pre-order in the catalog.
- CA-029 Shasvastii Sphinx is Firestorm's Code One "Shasvastii Special Armored
  Corp Sphinx (TAG)". CA-022 Kornak Gazarot and CA-025 Morat Tarlok Pack sit
  in Firestorm's Mercenaries section.
- CA-014 is the Hacker loadout, not the "(Plasma Rifle)" listing.
- CA-003, 004, 017, 021 and 030 show "0 in Stock - Backorder" on Firestorm
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
    ('CA-002', Decimal('34.00'), Decimal('30.60'), '/combined-army-nexus-7-spec-ops', True),
    ('CA-003', Decimal('19.15'), Decimal('17.23'), '/infinity-combined-army-hero-the-charontids-plasma-rifle', False),
    ('CA-004', Decimal('25.45'), Decimal('22.91'), '/infinity-combined-army-booster-pack-alpha', False),
    ('CA-005', Decimal('40.65'), Decimal('36.59'), '/combined-army---overdron-batroids-tag-pack', True),
    ('CA-006', Decimal('28.35'), Decimal('25.52'), '/infinity---combined-army-drone-remotes-pack', True),
    ('CA-007', Decimal('31.20'), Decimal('28.08'), '/infinity---combined-army-support-pack', True),
    ('CA-008', Decimal('26.00'), Decimal('23.40'), '/infinity---achilles', True),
    ('CA-009', Decimal('38.85'), Decimal('34.97'), '/infinity---combined-army-paint-set---harbinger-paramedic-exclusive', True),
    ('CA-010', Decimal('47.50'), Decimal('42.75'), '/infinity---juggernauts-armored-assault-brigade-multi-hmg', True),
    ('CA-011', Decimal('86.30'), Decimal('77.67'), '/infinity---next-wave-action-pack', True),
    ('CA-012', Decimal('30.00'), Decimal('27.00'), '/infinity---krakot-renegades-2-smg-chest-mine', True),
    ('CA-013', Decimal('39.69'), Decimal('35.72'), '/infinity---shasvastii-expansion-pack-beta', True),
    ('CA-014', Decimal('34.70'), Decimal('31.23'), '/the-anathematics-hacker', True),
    ('CA-015', Decimal('44.60'), Decimal('40.14'), '/reinf-caskuda-wcd-armored-jump-operator', True),
    ('CA-016', Decimal('83.30'), Decimal('74.97'), '/infinity---reinforcements:-combined-army-pack-alpha', True),
    ('CA-017', Decimal('41.50'), Decimal('37.35'), '/infinity---combined-army-expansion-pack-alpha', False),
    ('CA-018', Decimal('55.50'), Decimal('49.95'), '/combined-army:-morat-expansion-pack-beta', True),
    ('CA-019', Decimal('41.65'), Decimal('37.48'), '/infinity---the-hungries:-gakis-and-pretas', True),
    ('CA-020', Decimal('44.60'), Decimal('40.14'), '/infinity---shasvastii-expansion-pack-alpha', True),
    ('CA-021', Decimal('43.50'), Decimal('39.15'), '/infinity---morat-expansion-pack-alpha', False),
    ('CA-022', Decimal('17.85'), Decimal('16.07'), '/infinity---kornak-gazarot', True),
    ('CA-023', Decimal('52.50'), Decimal('47.24'), '/infinity---morat-fireteam-pack', True),
    ('CA-025', Decimal('41.65'), Decimal('37.48'), '/infinity---morat-tarlok-pack', True),
    ('CA-027', Decimal('34.70'), Decimal('31.23'), '/combined-army---taigha-creatures', True),
    ('CA-029', Decimal('41.65'), Decimal('37.48'), '/code-one---shasvastii-special-armored-corp-sphinx-tag', True),
    ('CA-030', Decimal('78.00'), Decimal('70.19'), '/combined-army---shasvastii-action-pack', False),
    ('CA-032', Decimal('36.69'), Decimal('33.02'), '/combined-army---shasvastii-nox-troops', True),
    ('CA-036', Decimal('13.89'), Decimal('12.49'), '/pneumarch-of-the-ur-hegemony-high-value-target', True),
    ('CA-037', Decimal('62.49'), Decimal('56.24'), '/xeodron-batroids-box-of-2', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: Combined Army. Idempotent.'

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
                f'Seeded {seeded} Infinity Combined Army Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
