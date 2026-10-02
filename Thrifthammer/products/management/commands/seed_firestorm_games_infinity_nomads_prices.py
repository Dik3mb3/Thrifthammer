"""
Seed Firestorm Games UK prices for Infinity: Nomads, and the GBP MSRP.

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

29 of 36 Nomads SKUs matched. 7 SKUs Firestorm does not list anywhere on the
site (page and search, including alternate spellings): NOM-017 Bakunin
Expansion Pack Alpha, NOM-020 Meteor Zond, NOM-024 Gator Squadron, NOM-031
Hecklers, NOM-032 Zoe and Pi-Well, NOM-033 Mobile Brigada, NOM-035 Tunguska
Interventors.

Notes on individual picks:
- NOM-007 Go-Pods is Firestorm's singular "Infinity - Go-Pod" (confirmed).
- NOM-010 Nomads Support Pack is Firestorm's "Infinity - Nomads Support Pack"
  (RRP 29.79). Firestorm has no "Essentials Nomads Support Pack", and its
  other "Nomads - Support Pack" (RRP 46.59) was judged a different product
  (confirmed with the user).
- NOM-011 Moran, Maasai Hunters is the current listing, not the "(OLD)" one
  at the same price (confirmed).
- NOM-005 is "Nomads Hero, Wolfgang Amadeus Wolff", not the separate
  "Wolfgang Amadeus Wolff, Vulver Bounty Hunter" listing.
- NOM-018 Sputniks is "Nomads - Sputniks", not "Tsyklon Sputniks".
- NOM-012 Zeros and NOM-013 Reinf. Lizard Squadron are filed by Firestorm
  under its Mercenaries and Combined Army sections, not Nomads.
- NOM-001, 002, 011 and 025 show "0 in Stock - Backorder" on Firestorm
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
    ('NOM-001', Decimal('39.94'), Decimal('35.95'), '/infinity-nomads-gecko-squadron', False),
    ('NOM-002', Decimal('56.14'), Decimal('50.53'), '/infinity-nomads-army-pack', False),
    ('NOM-003', Decimal('37.56'), Decimal('33.80'), '/infinity---tunguska-triggermen', True),
    ('NOM-004', Decimal('35.65'), Decimal('32.09'), '/infinity---switchers-gruppa', True),
    ('NOM-005', Decimal('17.40'), Decimal('15.66'), '/infinity---nomads-hero-wolfgang-amadeus-wolff', True),
    ('NOM-006', Decimal('30.35'), Decimal('27.32'), '/nomads-booster-pack-alpha', True),
    ('NOM-007', Decimal('56.60'), Decimal('50.94'), '/infinity---go-pod', True),
    ('NOM-008', Decimal('66.00'), Decimal('59.40'), '/infinity---nomads-szalamandra-squadron-tag-pack', True),
    ('NOM-009', Decimal('33.95'), Decimal('30.56'), '/infinity---nomads-zonds-remotes-pack', True),
    ('NOM-010', Decimal('29.79'), Decimal('26.81'), '/infinity---nomads-support-pack', True),
    ('NOM-011', Decimal('26.00'), Decimal('23.40'), '/infinity---moran-maasai-hunters', False),
    ('NOM-012', Decimal('39.69'), Decimal('35.72'), '/infinity---zeros', True),
    ('NOM-013', Decimal('41.65'), Decimal('37.48'), '/reinf-lizard-squadron', True),
    ('NOM-014', Decimal('67.40'), Decimal('60.67'), '/infinity---reinforcements:-nomads-pack-alpha', True),
    ('NOM-015', Decimal('32.00'), Decimal('28.80'), '/infinity---bakunin-expansion-pack-beta', True),
    ('NOM-016', Decimal('41.65'), Decimal('37.48'), '/infinity---bakunin-uberfallkommando', True),
    ('NOM-018', Decimal('52.50'), Decimal('47.25'), '/infinity---nomads---sputniks', True),
    ('NOM-019', Decimal('33.75'), Decimal('30.38'), '/infinity---nomads---stigmata', True),
    ('NOM-021', Decimal('62.49'), Decimal('56.24'), '/infinity---corregidor-fireteam-pack-beta', True),
    ('NOM-022', Decimal('34.70'), Decimal('31.23'), '/infinity---nomads---tomcats', True),
    ('NOM-023', Decimal('34.70'), Decimal('31.23'), '/infinity---corregidor-fireteam-pack-alpha', True),
    ('NOM-025', Decimal('13.00'), Decimal('11.70'), '/nomads---cassandra-kusanagi-spitfire', False),
    ('NOM-026', Decimal('39.00'), Decimal('35.10'), '/nomads---tunguska-cheerkillers', True),
    ('NOM-027', Decimal('30.00'), Decimal('27.00'), '/nomads---puppetactica-company', True),
    ('NOM-028', Decimal('54.50'), Decimal('49.05'), '/nomads---fast-offensive-unit-zondnautica', True),
    ('NOM-029', Decimal('20.85'), Decimal('18.77'), '/nomads---corregidor-bandits', True),
    ('NOM-030', Decimal('46.59'), Decimal('41.93'), '/nomads---the-hollow-men-4', True),
    ('NOM-034', Decimal('38.65'), Decimal('34.79'), '/corregidor-jaguars-box-of-4', True),
    ('NOM-036', Decimal('33.75'), Decimal('30.38'), '/salyut-zonds-evo-repeater-combi-rifle', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: Nomads. Idempotent.'

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
                f'Seeded {seeded} Infinity Nomads Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
