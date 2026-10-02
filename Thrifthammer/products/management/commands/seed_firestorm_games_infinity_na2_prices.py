"""
Seed Firestorm Games UK prices for Infinity: NA2, and the GBP MSRP.

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

16 of 26 NA2 SKUs matched. 10 SKUs not on Firestorm (page and site search,
including alternate spellings): NA2-001 Rumbler Spec-Ops Preorder Exclusive
Miniature, NA2-016 Valerya Gromoz, NA2-017 Karakuri Special Project,
NA2-018 Soldiers Of Fortune, NA2-019 Saito Togan, NA2-022 CSU Corporate
Security Unit, NA2-023 Tanko Zensenbutai, NA2-024 Miyamoto Mushashi
Aristeia! outfit, NA2-025 Avicenna Mercenary Doctor, NA2-026 Yojimbo
Mercenary Sword.

Notes on individual picks:
- NA2-004 Anaconda is Firestorm's "Mercenaries - Anaconda, Mercenary TAG
  Squadron" (RRP 55.50, in stock), not the backordered "Infinity - Anaconda"
  listing (RRP 55.00) (confirmed with the user).
- NA2-009 JSA Support Pack is Firestorm's "Infinity - JSA Support Pack" (RRP
  29.70), not "JSA - Support Pack" (RRP 27.50). Firestorm has no Essentials
  version (confirmed with the user).
- NA2-002 is the Viral Pistol loadout, not Firestorm's "Yu Jing - Taowu
  Mastermind" listing.
- NA2-008 is "JSA O-Yoroi Kidobutai TAG Pack", not "NA2 - O-Yoroi Kidobutai".
- NA2-005, 007, 012, 013 and 015 are filed by Firestorm under its Nomads,
  Yu Jing, Mercenaries, PanOceania and Mercenaries sections, not NA2.
- NA2-002, 003, 010, 013 and 015 show "0 in Stock - Backorder" on Firestorm
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
    ('NA2-002', Decimal('15.75'), Decimal('14.18'), '/infinity-yu-jing-taowu-mastermind-and-schemer-viral-pistol', False),
    ('NA2-003', Decimal('25.00'), Decimal('22.50'), '/infinity---jsa-oban-expansion-pack-alpha', False),
    ('NA2-004', Decimal('55.50'), Decimal('49.95'), '/anaconda-mercenary-tag-squadron', True),
    ('NA2-005', Decimal('54.40'), Decimal('48.96'), '/infinity---iguana-squadron', True),
    ('NA2-006', Decimal('36.00'), Decimal('32.40'), '/infinity---jsa-booster-pack-alpha', True),
    ('NA2-007', Decimal('58.80'), Decimal('52.92'), '/infinity---imperial-service-expansion-pack-alpha', True),
    ('NA2-008', Decimal('41.14'), Decimal('37.03'), '/infinity---jsa-o-yoroi-kidobutai-tag-pack', True),
    ('NA2-009', Decimal('29.70'), Decimal('26.73'), '/infinity---jsa-support-pack', True),
    ('NA2-010', Decimal('18.00'), Decimal('16.20'), '/infinity---jsa---reinforcements-domaru-takeshi-neko-oyama', False),
    ('NA2-011', Decimal('34.50'), Decimal('31.05'), '/jsa---mechazoid-sokorentai', True),
    ('NA2-012', Decimal('49.59'), Decimal('44.63'), '/mercenaries---druze-shock-teams-', True),
    ('NA2-013', Decimal('17.85'), Decimal('16.07'), '/infinity---father-lucien-sforza-authorized-bounty-hunter', False),
    ('NA2-014', Decimal('46.59'), Decimal('41.93'), '/infinity---jsa-expansion-pack-alpha', True),
    ('NA2-015', Decimal('27.50'), Decimal('24.75'), '/infinity---mcmurrough-mercenary-dog-warrior', False),
    ('NA2-020', Decimal('38.65'), Decimal('34.79'), '/na2---brawlers-mercenary-enforcers', True),
    ('NA2-021', Decimal('36.69'), Decimal('33.02'), '/jsa---aragoto-senkenbutai', True),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices and Corvus Belli GBP MSRP (Firestorm RRP) for Infinity: NA2. Idempotent.'

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
                f'Seeded {seeded} Infinity NA2 Firestorm Games prices '
                f'and Corvus Belli MSRPs. Skipped: {skipped}.'
            )
        )
