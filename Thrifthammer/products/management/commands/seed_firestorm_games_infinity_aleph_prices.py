"""
Seed Firestorm Games UK prices for Infinity: ALEPH, and the GBP MSRP.

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

19 of 22 ALEPH SKUs matched. 3 SKUs not available on Firestorm (page and
site search): ALE-014 Rebot Remotes Pack (a pre-release product Firestorm
has not listed), ALE-015 Dactyls, ALE-016 Marut.

Notes on individual picks (both confirmed with the user):
- ALE-002 ALEPH Support Pack is Firestorm's "Essentials ALEPH Support Pack"
  (RRP 25.50): our Corvus Belli URL for this SKU sits in Essentials. Firestorm's
  "ALEPH - Support Pack" (RRP 31.70) and "ALEPH Support Pack Beta" (RRP 34.70)
  are other products.
- ALE-012 ALEPH Expansion Pack Beta is Firestorm's "Aleph Booster Pack Beta"
  (our Corvus Belli URL for this SKU is aleph-booster-pack-beta, i.e. the
  renamed pack).
- ALE-007, ALE-011 and ALE-013 are filed by Firestorm under its Mercenaries
  and Code One sections, not ALEPH.
- ALE-001, 002, 004, 006 and 017 show "0 in Stock - Backorder" on Firestorm
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
    ('ALE-001', Decimal('53.55'), Decimal('48.19'), '/infinity-aleph-tarkshyas-interception-wing', False),
    ('ALE-002', Decimal('25.50'), Decimal('22.95'), '/infinity-essentials-aleph-support-pack', False),
    ('ALE-003', Decimal('54.14'), Decimal('48.73'), '/infinity---aleph-army-pack', True),
    ('ALE-004', Decimal('28.15'), Decimal('25.33'), '/infinity---k2-auxiliars', False),
    ('ALE-005', Decimal('49.59'), Decimal('44.63'), '/infinity---posthumans', True),
    ('ALE-006', Decimal('31.70'), Decimal('28.53'), '/aleph---ajax-the-great', False),
    ('ALE-007', Decimal('20.85'), Decimal('18.77'), '/infinity---atalanta-agemas-nco--spotbot', True),
    ('ALE-008', Decimal('60.25'), Decimal('54.23'), '/infinity---reinforcements:-aleph-pack-alpha-', True),
    ('ALE-009', Decimal('41.65'), Decimal('37.48'), '/aleph---myrmidons', True),
    ('ALE-010', Decimal('36.69'), Decimal('33.02'), '/infinity---steel-phalanx-expansion-pack-alpha', True),
    ('ALE-011', Decimal('17.85'), Decimal('16.07'), '/infinity---code-one:-phoenix-heavy-rocket-launcher', True),
    ('ALE-012', Decimal('39.69'), Decimal('35.72'), '/infinity---aleph-booster-pack-beta', True),
    ('ALE-013', Decimal('30.00'), Decimal('27.00'), '/infinity---code-one:-agamemnon-the-atreides', True),
    ('ALE-017', Decimal('31.70'), Decimal('28.53'), '/aleph---probots', False),
    ('ALE-018', Decimal('34.70'), Decimal('31.23'), '/aleph---yadu-troops', True),
    ('ALE-019', Decimal('13.89'), Decimal('12.49'), '/aleph---dart-optimate-huntress-smg-grenades', True),
    ('ALE-020', Decimal('23.79'), Decimal('21.42'), '/andromeda-sophistes-of-the-steel-phalanx', True),
    ('ALE-021', Decimal('20.85'), Decimal('18.77'), '/hector-homerid-champion-heavy-pistol-exp-ccw', True),
    ('ALE-022', Decimal('20.85'), Decimal('18.77'), '/penthesilea-amazon-biker-special-edition', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: ALEPH. Idempotent.'

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
                f'Seeded {seeded} Infinity ALEPH Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
