"""
Seed Firestorm Games UK prices for Infinity: Haqqislam, and the GBP MSRP.

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

21 of 28 Haqqislam SKUs matched. 7 SKUs Firestorm does not list anywhere on
the site (page and search, including alternate spellings): HQQ-014 Haqqislam
Remotes Pack, HQQ-017 Bashi Bazouks, HQQ-024 Naffatun, HQQ-025 The Nazarova
Twins, HQQ-026 Muttawi'ah, HQQ-027 Kameel Remote, HQQ-028 Odalisques.

Notes on individual picks:
- HQQ-003 Yuan Yuan is Firestorm's "Infinity - Yuan Yuan" (RRP 25.75, filed
  under NA2) and not the "Yuan Yuan (Chain Rifle)" listing (RRP 16.89), which
  is a different loadout (confirmed with the user).
- HQQ-007 Scarface & Cordelia. Mercenary Armored Team is Firestorm's
  "Scarface. Mercenary TAG Team" (confirmed with the user).
- HQQ-003, 010, 012 and 013 are filed by Firestorm under its NA2, Aristeia!
  and Code One sections, not Haqqislam. HQQ-007 sits in the Haqqislam
  section.
- HQQ-006, 012 and 022 show "0 in Stock - Backorder" on Firestorm (checked
  2026-10-02): real price kept, in_stock=False, not_available=False, per the
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
    ('HQQ-001', Decimal('31.15'), Decimal('28.03'), '/haqqislam---hassassin-expansion-pack-gamma', True),
    ('HQQ-002', Decimal('45.64'), Decimal('41.08'), '/infinity---haytham-aero-unit', True),
    ('HQQ-003', Decimal('25.75'), Decimal('23.18'), '/infinity---yuan-yuan', True),
    ('HQQ-004', Decimal('29.35'), Decimal('26.41'), '/infinity---mukthar-active-response-unit', True),
    ('HQQ-005', Decimal('55.00'), Decimal('49.50'), '/infinity---zeybek-aero-unit', True),
    ('HQQ-006', Decimal('35.65'), Decimal('32.09'), '/infinity---ramah-taskforce-expansion-pack-alpha', False),
    ('HQQ-007', Decimal('60.65'), Decimal('54.59'), '/infinity---scarface-mercenary-tag-team', True),
    ('HQQ-008', Decimal('41.65'), Decimal('37.48'), '/haqqislam---hassassin-expansion-pack-alpha', True),
    ('HQQ-009', Decimal('69.39'), Decimal('62.45'), '/infinity---reinforcements:-haqqislam-pack-alpha-', True),
    ('HQQ-010', Decimal('19.80'), Decimal('17.82'), '/infinity---fiddler-aristeias-ex-toymaker', True),
    ('HQQ-011', Decimal('44.60'), Decimal('40.14'), '/hassassin-fireteam-pack-alpha-', True),
    ('HQQ-012', Decimal('12.00'), Decimal('10.80'), '/codeone:-yara-haddad-ap-marksman-rifle', False),
    ('HQQ-013', Decimal('39.69'), Decimal('35.72'), '/infinity---code-one:-shakush-light-armored-unit', True),
    ('HQQ-015', Decimal('34.70'), Decimal('31.23'), '/infinity---haqqislam-support-pack', True),
    ('HQQ-016', Decimal('14.90'), Decimal('13.41'), '/haqqislam---saladin-o-12-liaison-officer-combi-rifle', True),
    ('HQQ-018', Decimal('89.25'), Decimal('80.33'), '/haqqislam---action-pack', True),
    ('HQQ-019', Decimal('13.89'), Decimal('12.50'), '/haqqislam---namurr-active-response-unit-heavy-pistol-em-ccw', True),
    ('HQQ-020', Decimal('38.65'), Decimal('34.79'), '/haqqislam---zhayedan-intervention-troops', True),
    ('HQQ-021', Decimal('44.60'), Decimal('40.14'), '/haqqislam---khawarijs', True),
    ('HQQ-022', Decimal('30.00'), Decimal('24.00'), '/haqqislam-hakims-special-medical-assistance-group-box-of-4', False),
    ('HQQ-023', Decimal('79.10'), Decimal('71.19'), '/maghariba-guard', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: Haqqislam. Idempotent.'

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
                f'Seeded {seeded} Infinity Haqqislam Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
