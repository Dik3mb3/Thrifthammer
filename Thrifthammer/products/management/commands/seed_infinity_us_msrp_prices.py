"""
Seed the USD MSRP for the 50 Infinity SKUs that no Miniature Market sheet row
covered.

Research (2026-10-04/05), made by reading real US retailer product pages, never
by search-engine summaries or by script, then confirmed with the user:

- Warsenal (warsen.al) prints an explicit "MSRP(USD)" on each product page, and
  Game Nerdz (gamenerdz.com) tags a recommended-retail price (RRP) on each
  listing. The two agreed to the cent on all 46 products both carry.
  Interstellar Gamez (interstellargamez.com, struck-through "Regular price")
  agreed on all 40 it carries, and is the second source for PAN-046 Miranda
  Ashcroft, which Game Nerdz does not list.
- Each SKU was matched through the Corvus Belli product code on its own
  store.corvusbelli.com page (REF), which equalled the code every retailer used.
  Corvus Belli's euro price x 1.2, rounded to $0.50, matches these USD figures,
  as a sanity check.
- Noble Knight's "MSRP old price" was deliberately not used: it is 10-48% above
  these figures on 38 of 40 pages. Miniature Market's struck list price was also
  not used for these SKUs (it is lower and older than the figures below, and
  Miniature Market carries only 8 of the 50).

The three Hyperthermal faction bundles (PAN-001, YUJ-001, CA-001) are
EUR 98.00 at Corvus Belli (EUR 120.50 struck through, including the free Rumbler
exclusive). Warsenal's MSRP label and Interstellar Gamez's struck price are
$144.60 (= EUR 120.50 x 1.2), while both sell it at $94.08, which is 80% of
$117.60. The user chose $144.60 (2026-10-05).

As in the Miniature Market seeds, the MSRP is written to Product.msrp AND to the
price of the Corvus Belli US row (retailer `corvus-belli`), the MSRP shown to
users. Both writes are create-only (a value is only written while it is still
None), so a redeploy never overwrites an MSRP or a scraper-refreshed price.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_CORVUS_BELLI_US_SLUG = 'corvus-belli'

# (gw_sku, usd_msrp)
_MSRPS = [
    # PanOceania
    ('PAN-001', Decimal('144.60')),  # Indigo Spec-Ops Bundle (user-chosen, see above)
    ('PAN-002', Decimal('48.00')),
    ('PAN-003', Decimal('36.00')),
    ('PAN-028', Decimal('45.50')),
    ('PAN-029', Decimal('51.50')),
    ('PAN-031', Decimal('111.00')),
    ('PAN-033', Decimal('22.00')),
    ('PAN-035', Decimal('26.00')),
    ('PAN-043', Decimal('43.00')),
    ('PAN-046', Decimal('17.50')),  # Warsenal + Interstellar Gamez (not on Game Nerdz)
    ('PAN-048', Decimal('48.00')),
    # Yu Jing
    ('YUJ-001', Decimal('144.60')),  # Gui Feng Spec-Ops Bundle (user-chosen)
    ('YUJ-002', Decimal('48.00')),
    ('YUJ-003', Decimal('48.00')),
    ('YUJ-025', Decimal('111.00')),
    ('YUJ-031', Decimal('39.50')),
    ('YUJ-035', Decimal('69.00')),
    ('YUJ-036', Decimal('26.00')),
    # Ariadna
    ('ARI-032', Decimal('78.00')),
    ('ARI-033', Decimal('78.00')),
    # Haqqislam
    ('HQQ-001', Decimal('43.00')),
    ('HQQ-006', Decimal('49.00')),
    ('HQQ-021', Decimal('56.00')),
    ('HQQ-022', Decimal('43.00')),
    ('HQQ-024', Decimal('56.00')),
    ('HQQ-027', Decimal('49.00')),
    # Nomads
    ('NOM-002', Decimal('78.00')),
    ('NOM-004', Decimal('49.00')),
    ('NOM-005', Decimal('24.00')),
    ('NOM-015', Decimal('45.50')),
    ('NOM-018', Decimal('65.50')),
    ('NOM-022', Decimal('43.00')),
    ('NOM-024', Decimal('51.50')),
    ('NOM-035', Decimal('45.50')),
    # ALEPH
    ('ALE-003', Decimal('78.00')),
    ('ALE-014', Decimal('39.00')),  # current Essentials pack, Corvus REF 280892-1210
    ('ALE-015', Decimal('39.50')),
    ('ALE-016', Decimal('48.00')),
    # Combined Army
    ('CA-001', Decimal('144.60')),  # Nexus-7 Spec-Ops Bundle (user-chosen)
    ('CA-002', Decimal('48.00')),
    ('CA-004', Decimal('36.00')),
    ('CA-005', Decimal('56.00')),
    ('CA-014', Decimal('43.00')),
    ('CA-017', Decimal('59.50')),
    ('CA-023', Decimal('65.50')),
    ('CA-028', Decimal('58.00')),
    ('CA-029', Decimal('51.50')),
    # O-12
    ('O12-011', Decimal('45.50')),
    # NA2
    ('NA2-001', Decimal('27.00')),
    ('NA2-015', Decimal('39.50')),
]


def _apply_msrp(product, corvus_belli, usd_msrp):
    """Write the create-only USD MSRP and the Corvus Belli US row price.

    Returns True when Product.msrp was written, False when it was already set.
    """
    written = False
    if product.msrp is None:
        product.msrp = usd_msrp
        product.save(update_fields=['msrp'])
        written = True

    corvus_row, _ = CurrentPrice.objects.get_or_create(
        product=product,
        retailer=corvus_belli,
        defaults={
            'url': product.gw_url,
            'price': None,
            'currency': 'USD',
            'in_stock': False,
            'not_available': True,
        },
    )
    if corvus_row.price is None:
        corvus_row.price = usd_msrp
        corvus_row.currency = 'USD'
        corvus_row.in_stock = True
        corvus_row.not_available = False
        corvus_row.save(update_fields=['price', 'currency', 'in_stock', 'not_available'])
    return written


class Command(BaseCommand):
    help = 'Seed USD MSRPs (and the Corvus Belli US row price) for 50 Infinity SKUs. Idempotent, create-only.'

    def handle(self, *args, **options):
        corvus_belli = Retailer.objects.get(slug=_CORVUS_BELLI_US_SLUG)

        written = 0
        already_set = 0
        skipped = 0
        for gw_sku, usd_msrp in _MSRPS:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} not in DB')
                skipped += 1
                continue
            if _apply_msrp(product, corvus_belli, usd_msrp):
                written += 1
            else:
                already_set += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Infinity USD MSRPs: {written} written, {already_set} already set, {skipped} skipped.'
            )
        )
