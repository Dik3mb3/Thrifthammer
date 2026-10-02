"""
Seed Firestorm Games UK prices for Infinity: PanOceania, and the GBP MSRP.

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
factions, so the WHOLE page was read, including Mercenaries, Infinity
Essentials, Code One and Dire Foes) plus Firestorm's site search for the
SKUs not on that page. Every match was made by reading, not by script, and
the ambiguous ones were confirmed with the user.

28 of 48 PanOceania SKUs matched. Not matched:
- PAN-001 Indigo Spec-Ops Bundle and PAN-013 Kestrel Expansion Pack Beta:
  skipped on the user's instruction.
- 18 SKUs Firestorm does not list anywhere on the site (page and search,
  including alternate spellings): PAN-019, 027, 028, 029, 030, 034, 035,
  036, 037, 038, 039, 040, 042, 044, 045, 046, 047, 048.

Notes on individual picks:
- PAN-009 and PAN-018 are the exact links the user supplied (PAN-018 sits in
  Firestorm's Mercenaries section, not PanOceania).
- PAN-006: Firestorm has two Booster Pack Alpha listings; the Infinity-
  prefixed one (RRP 36.00) is used, not the older "PanOceania - Booster Pack
  Alpha" (39.00).
- PAN-020: the Infinity-prefixed Warcors listing (RRP 13.00, in stock) is
  used, not the Mercenaries "Stun Pistol" one (RRP 12.00, sale 10.79, sold
  out). Sold-out Firestorm cards have an RRP too; only the category page's
  button data-price is missing, so read the struck-through price instead.
- PAN-021 is "Maximus, Optimate and HexaDome Legend"; PAN-003 is the
  separate "Aleph Optimate Agent Maximus" listing.
- PAN-031 WinterFor Action Pack is Firestorm's "PanOceania - Action Pack"
  (WinterFor is the renamed PanOceania Action Pack).
- PAN-002 is a Firestorm PRE ORDER (dispatch expected 30/10/2026), recorded
  in_stock=True like every other live-purchasable pre-order in the catalog.
- PAN-016, PAN-025 and PAN-032 show "0 in Stock - Backorder" on Firestorm
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
    ('PAN-002', Decimal('34.00'), Decimal('30.60'), '/panoceania-indigo-spec-ops', True),
    ('PAN-003', Decimal('25.45'), Decimal('22.91'), '/infinity---aleph-optimate-agent-maximus', True),
    ('PAN-004', Decimal('38.79'), Decimal('34.91'), '/infinity---kestrel-expansion-pack-delta', True),
    ('PAN-005', Decimal('20.25'), Decimal('18.23'), '/panoceania-hero-jeanne-darc-20-mobility-armor', True),
    ('PAN-006', Decimal('36.00'), Decimal('32.40'), '/infinity---panoceania-booster-pack-alpha', True),
    ('PAN-007', Decimal('49.20'), Decimal('44.28'), '/infinity---drummers-mobile-support-section', True),
    ('PAN-008', Decimal('48.35'), Decimal('43.52'), '/infinity---panoceania-cutters-tag-pack', True),
    ('PAN-009', Decimal('44.65'), Decimal('37.95'), '/infinity---panoceania-paint-set-fusilier-paramedic-exclusive', True),
    ('PAN-010', Decimal('45.69'), Decimal('41.12'), '/infinity---kestrel-expansion-pack-gamma', True),
    ('PAN-011', Decimal('32.79'), Decimal('29.51'), '/infinity---panoceania-dronbot-remotes-pack', True),
    ('PAN-012', Decimal('29.70'), Decimal('26.73'), '/infinity---panoceania-support-pack', True),
    ('PAN-014', Decimal('15.85'), Decimal('14.27'), '/infinity---dr-priya-harper---archeo-raider-plasma-carbine', True),
    ('PAN-015', Decimal('64.45'), Decimal('58.01'), '/infinity---panoceania-army-pack', True),
    ('PAN-016', Decimal('17.85'), Decimal('16.07'), '/infinity---beasthunters-free-guild-tactical-bow', False),
    ('PAN-017', Decimal('46.59'), Decimal('41.93'), '/infinity---triphammers-repurposed-industrial-tags', True),
    ('PAN-018', Decimal('17.85'), Decimal('16.07'), '/infinity---freelance-operator-samsa-plasma-rifle', True),
    ('PAN-020', Decimal('13.00'), Decimal('11.70'), '/infinity---warcors-war-correspondents', True),
    ('PAN-021', Decimal('34.70'), Decimal('31.23'), '/maximus-optimate-and-hexadome-legend', True),
    ('PAN-022', Decimal('16.50'), Decimal('14.85'), '/diggers-armed-prospectors-chain-rifle', True),
    ('PAN-023', Decimal('62.49'), Decimal('56.24'), '/reinforcements:-panoceania-pack-alpha', True),
    ('PAN-024', Decimal('44.60'), Decimal('40.14'), '/military-orders-expansion-pack-alpha', True),
    ('PAN-025', Decimal('30.00'), Decimal('27.00'), '/infinity---panoceania---armbots', False),
    ('PAN-026', Decimal('41.65'), Decimal('37.48'), '/infinity---dire-foes-mission-pack-12:-troubled-theft', True),
    ('PAN-031', Decimal('78.00'), Decimal('70.20'), '/panoceania---action-pack', True),
    ('PAN-032', Decimal('36.69'), Decimal('33.02'), '/panoceania---vargar-maximum-security-team', False),
    ('PAN-033', Decimal('17.85'), Decimal('16.07'), '/panoceania---knight-of-santiago-spitfire', True),
    ('PAN-041', Decimal('15.85'), Decimal('14.27'), '/na2---ada-swanson-submondo-smuggler-submachine-gun', True),
    ('PAN-043', Decimal('34.70'), Decimal('31.23'), '/panoceania---orc-troops', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: PanOceania. Idempotent.'

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
                f'Seeded {seeded} Infinity PanOceania Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
