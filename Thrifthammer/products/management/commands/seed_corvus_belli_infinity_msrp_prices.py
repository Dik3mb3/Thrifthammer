"""
Seed the GBP MSRP for Infinity SKUs that Firestorm Games does not list.

Corvus Belli's own store only shows EUR, and Firestorm Games supplied the
GBP RRP for every SKU it lists (seed_firestorm_games_infinity_*_prices).
The SKUs below are not on Firestorm, so their GBP MSRPs were supplied by the
user on 2026-10-02 (taken from UK retailer listings).

Each price becomes the GBP MSRP in the same two places the Firestorm seeders
use: Product.msrp_gbp and the `corvus-belli-uk` CurrentPrice price (which
keeps its own official listing URL, Product.gw_url). There is no Firestorm
row for these SKUs.

Both writes are create-only (a value is only written while it is still
None), so a redeploy never resets an MSRP that was corrected afterwards.

YUJ-001 Gui Feng Spec-Ops Bundle, CA-001 Nexus-7 Spec-Ops Bundle and NA2-001
Rumbler Spec-Ops Preorder Exclusive Miniature were supplied separately later
the same day (they were left out of Firestorm matching as bundle/exclusive
SKUs with no listing of their own).

Notes on values as supplied: PAN-029 was typed "4165" and is read as 41.65;
PAN-027 is 89.26 as typed; YUJ-001 was typed "YU-001" and is read as YUJ-001.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_CORVUS_BELLI_SLUG = 'corvus-belli-uk'

# (gw_sku, gbp_msrp)
_MSRPS = [
    # PanOceania
    ('PAN-001', Decimal('112.58')),
    ('PAN-013', Decimal('41.65')),
    ('PAN-019', Decimal('33.99')),
    ('PAN-027', Decimal('89.26')),
    ('PAN-028', Decimal('32.00')),
    ('PAN-029', Decimal('41.65')),
    ('PAN-030', Decimal('13.90')),
    ('PAN-034', Decimal('41.65')),
    ('PAN-035', Decimal('46.60')),
    ('PAN-036', Decimal('12.00')),
    ('PAN-037', Decimal('36.70')),
    ('PAN-038', Decimal('57.50')),
    ('PAN-039', Decimal('99.15')),
    ('PAN-040', Decimal('16.90')),
    ('PAN-042', Decimal('34.70')),
    ('PAN-044', Decimal('14.90')),
    ('PAN-045', Decimal('14.99')),
    ('PAN-046', Decimal('12.99')),
    ('PAN-047', Decimal('93.99')),
    ('PAN-048', Decimal('38.65')),
    # Yu Jing
    ('YUJ-001', Decimal('112.58')),
    ('YUJ-021', Decimal('14.90')),
    ('YUJ-023', Decimal('16.90')),
    ('YUJ-025', Decimal('99.15')),
    ('YUJ-026', Decimal('41.65')),
    ('YUJ-028', Decimal('36.70')),
    ('YUJ-029', Decimal('46.60')),
    ('YUJ-031', Decimal('31.99')),
    ('YUJ-032', Decimal('16.90')),
    ('YUJ-034', Decimal('41.65')),
    ('YUJ-035', Decimal('93.99')),
    ('YUJ-036', Decimal('31.70')),
    ('YUJ-037', Decimal('38.65')),
    # Ariadna
    ('ARI-009', Decimal('17.85')),
    ('ARI-018', Decimal('14.90')),
    ('ARI-020', Decimal('14.90')),
    ('ARI-021', Decimal('46.60')),
    ('ARI-022', Decimal('99.15')),
    ('ARI-023', Decimal('12.99')),
    ('ARI-024', Decimal('14.90')),
    ('ARI-027', Decimal('36.70')),
    ('ARI-029', Decimal('17.85')),
    ('ARI-030', Decimal('14.90')),
    ('ARI-031', Decimal('38.65')),
    ('ARI-032', Decimal('39.95')),
    ('ARI-033', Decimal('38.65')),
    # Haqqislam
    ('HQQ-014', Decimal('38.65')),
    ('HQQ-017', Decimal('14.90')),
    ('HQQ-024', Decimal('34.70')),
    ('HQQ-025', Decimal('46.60')),
    ('HQQ-026', Decimal('34.70')),
    ('HQQ-027', Decimal('38.65')),
    ('HQQ-028', Decimal('34.70')),
    # Nomads
    ('NOM-017', Decimal('41.65')),
    ('NOM-020', Decimal('31.70')),
    ('NOM-024', Decimal('36.50')),
    ('NOM-031', Decimal('14.90')),
    ('NOM-032', Decimal('17.85')),
    ('NOM-033', Decimal('41.65')),
    ('NOM-035', Decimal('36.70')),
    # ALEPH
    ('ALE-014', Decimal('38.65')),
    ('ALE-015', Decimal('31.70')),
    ('ALE-016', Decimal('93.99')),
    # Combined Army
    ('CA-001', Decimal('112.58')),
    ('CA-024', Decimal('42.95')),
    ('CA-026', Decimal('99.15')),
    ('CA-028', Decimal('41.65')),
    ('CA-031', Decimal('14.90')),
    ('CA-033', Decimal('93.99')),
    ('CA-034', Decimal('16.90')),
    ('CA-035', Decimal('106.99')),
    # O-12
    ('O12-012', Decimal('14.90')),
    ('O12-016', Decimal('41.65')),
    ('O12-019', Decimal('38.65')),
    ('O12-021', Decimal('99.15')),
    # NA2
    ('NA2-001', Decimal('19.20')),
    ('NA2-016', Decimal('14.90')),
    ('NA2-017', Decimal('31.70')),
    ('NA2-018', Decimal('36.70')),
    ('NA2-019', Decimal('12.99')),
    ('NA2-022', Decimal('12.99')),
    ('NA2-023', Decimal('36.70')),
    ('NA2-024', Decimal('14.90')),
    ('NA2-025', Decimal('12.99')),
    ('NA2-026', Decimal('36.70')),
    # JSA
    ('JSA-002', Decimal('38.65')),
]


def _apply_msrp(product, msrp, corvus_belli):
    """Set the GBP MSRP on the product and its Corvus Belli row, create-only."""
    if product.msrp_gbp is None:
        product.msrp_gbp = msrp
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
        corvus_row.price = msrp
        corvus_row.currency = 'GBP'
        corvus_row.in_stock = True
        corvus_row.not_available = False
        corvus_row.save(update_fields=['price', 'currency', 'in_stock', 'not_available'])


class Command(BaseCommand):
    help = 'Seed user-supplied GBP MSRPs (Product.msrp_gbp + Corvus Belli row) for Infinity SKUs not on Firestorm. Idempotent.'

    def handle(self, *args, **options):
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
        for gw_sku, msrp in _MSRPS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue
            _apply_msrp(product, msrp, corvus_belli)
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Infinity GBP MSRPs (Corvus Belli). Skipped: {skipped}.'
            )
        )
