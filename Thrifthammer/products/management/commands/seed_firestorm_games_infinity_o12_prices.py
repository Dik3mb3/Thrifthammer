"""
Seed Firestorm Games UK prices for Infinity: O-12, and the GBP MSRP.

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
the pick and the missing list were confirmed with the user (2026-10-02).

19 of 23 O-12 SKUs matched. 4 SKUs not on Firestorm (page and site search,
including alternate spellings): O12-012 Cyberghost, O12-016 O-12 Expansion
Pack Alpha, O12-019 Copperbot Remotes Pack, O12-021 O-12 Action Pack.

Notes on individual picks:
- O12-015 O-12 Expansion Pack Beta is Firestorm's "O-12 - Booster Pack Beta"
  (RRP 39.69, filed under Code One): the renamed pack, same pattern as
  ALE-012 and ARI-016 (confirmed with the user).
- O12-016 was deliberately NOT matched to Firestorm's "Torchlight Brig.
  Expansion Pack Alpha" (RRP 41.65): that is a Torchlight Brigade pack, and
  the catalog already has a separate Torchlight pack (O12-004).
- O12-017 Zeta Unit sits in Firestorm's Code One section.
- O12-014 shows "0 in Stock - Backorder" on Firestorm (checked 2026-10-02):
  real price kept, in_stock=False, not_available=False, per the
  sold-out-listing rule (never clear a real price to None just because a
  listing is temporarily unavailable).

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
    ('O12-001', Decimal('46.99'), Decimal('42.29'), '/infinity-o-12-paint-set-kappa-missile-launcher-exclusive-96761', True),
    ('O12-002', Decimal('26.85'), Decimal('24.16'), '/infinity---tinker-and-zetbot-remote', True),
    ('O12-003', Decimal('14.50'), Decimal('13.05'), '/infinity---jamie-arantes-netroid-rover', True),
    ('O12-004', Decimal('46.59'), Decimal('41.93'), '/infinity---torchlight-brig-expansion-pack-beta', True),
    ('O12-005', Decimal('13.05'), Decimal('11.75'), '/infinity---o-12---raveneye-officer-submachine-gun-emarat', True),
    ('O12-006', Decimal('39.69'), Decimal('35.72'), '/o-12---wreckers-fire-recon-armored-squad-tag-pack', True),
    ('O12-007', Decimal('109.05'), Decimal('98.14'), '/o-12-torchlight-brigade-action-pack', True),
    ('O12-008', Decimal('69.39'), Decimal('62.45'), '/reinforcements:-o-12-pack-alpha', True),
    ('O12-009', Decimal('31.70'), Decimal('28.53'), '/infinity---o-12---starmada-expansion-pack-alpha', True),
    ('O12-010', Decimal('44.60'), Decimal('40.14'), '/infinity---roadbots-highway-patrol', True),
    ('O12-011', Decimal('36.69'), Decimal('33.02'), '/o-12---fuzzbots', True),
    ('O12-013', Decimal('52.50'), Decimal('47.24'), '/o-12---raptor-boarding-squad', True),
    ('O12-014', Decimal('43.50'), Decimal('39.15'), '/infinity---nyoka-assault-troops', False),
    ('O12-015', Decimal('39.69'), Decimal('35.72'), '/o-12---booster-pack-beta', True),
    ('O12-017', Decimal('57.50'), Decimal('51.75'), '/code-one---zeta-unit-tag', True),
    ('O12-018', Decimal('89.25'), Decimal('80.33'), '/o-12---starmada-action-pack', True),
    ('O12-020', Decimal('34.70'), Decimal('31.23'), '/o-12---support-pack-specialized-support-unit-lambda', True),
    ('O12-022', Decimal('23.79'), Decimal('21.42'), '/o-12---alpha-unit-light-shotgun', True),
    ('O12-023', Decimal('31.70'), Decimal('28.53'), '/o-12--team-sirius-', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: O-12. Idempotent.'

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
                f'Seeded {seeded} Infinity O-12 Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
