"""
Management command: apply_batch_fixes_apr2026b

Second wave of April 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_apr2026a.

Changes covered:
  Fix 1  -- Bjorn the Fell-handed (space-wolves-bjorn-fell-handed)
             Set ebay_search_name = 'Space Wolves Venerable Dreadnought'
             Bjorn is a dual-kit build of the Venerable Dreadnought — eBay
             sellers list it under the generic kit name, not "Bjorn".

  Fix 2  -- Wulfen Dreadnought (space-wolves-wulfen-dreadnought)
             Set ebay_search_name = 'Space Wolves Venerable Dreadnought'
             Same dual-kit situation as Bjorn.

  Fix 3  -- Iron Father Feirros (iron-hands-iron-father-feirros)
             Set ebay_search_name = 'Iron Father Feirros Warhammer'
             Adding "Warhammer" broadens the match to catch the listing
             without triggering false positives.

  Fix 4  -- Razorback (space-marine-razorback)
             Set ebay_search_name = 'Space Marine Razorback'
             The product was being searched as just "Razorback" which
             matched too many irrelevant listings. The faction qualifier
             narrows it to the correct kit.

  Fix 5  -- Captain in Gravis Armour with Master-crafted Heavy Bolt Rifle
             (space-marine-captain-gravis-heavy-bolt-rifle)
             Deactivate (is_active=False) — product discontinued / user
             requested removal.

  Fix 6  -- Ork Gargantuan Squiggoth (ork-gargantuan-squiggoth)
             Deactivate (is_active=False) — Forge World resin product,
             not stocked by mainstream retailers. User requested removal
             of all Forge World products.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Product

# (slug, ebay_search_name)
SEARCH_NAME_FIXES = [
    ('space-wolves-bjorn-fell-handed',       'Space Wolves Venerable Dreadnought'),
    ('space-wolves-wulfen-dreadnought',      'Space Wolves Venerable Dreadnought'),
    ('iron-hands-iron-father-feirros',       'Iron Father Feirros Warhammer'),
    ('space-marine-razorback',               'Space Marine Razorback'),
]

DEACTIVATE_SLUGS = [
    'space-marine-captain-gravis-heavy-bolt-rifle',  # discontinued
    'ork-gargantuan-squiggoth',                      # Forge World resin
]


class Command(BaseCommand):
    """Apply April 2026 wave-2 data fixes: eBay search overrides and product deactivations."""

    help = (
        'Sets ebay_search_name on Bjorn, Wulfen Dreadnought, Iron Father Feirros, '
        'and Razorback so the eBay price updater finds the correct listings. '
        'Deactivates Captain in Gravis Armour (Heavy Bolt Rifle) and Ork Gargantuan '
        'Squiggoth (Forge World). Idempotent.'
    )

    def handle(self, *args, **options):
        """Apply all fixes in this wave."""
        self._apply_search_name_fixes()
        self._deactivate_products()

    def _apply_search_name_fixes(self):
        """Set ebay_search_name overrides on products that return 'Not found' on eBay."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n  ── eBay search name overrides ──'))
        for slug, search_name in SEARCH_NAME_FIXES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  [skip] Not found: {slug}'))
                continue

            if product.ebay_search_name == search_name:
                self.stdout.write(f'  [no-op] {product.name} — already set')
                continue

            old = product.ebay_search_name or '(empty)'
            product.ebay_search_name = search_name
            product.save(update_fields=['ebay_search_name'])
            self.stdout.write(self.style.SUCCESS(
                f'  Updated: {product.name}  "{old}" → "{search_name}"'
            ))

    def _deactivate_products(self):
        """Deactivate products that should no longer appear on the site."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n  ── Product deactivations ──'))
        for slug in DEACTIVATE_SLUGS:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  [skip] Not found: {slug}'))
                continue

            if not product.is_active:
                self.stdout.write(f'  [no-op] {product.name} — already inactive')
                continue

            product.is_active = False
            product.save(update_fields=['is_active'])
            self.stdout.write(self.style.SUCCESS(
                f'  Deactivated: {product.name}'
            ))

            # Also deactivate the corresponding UnitType so it disappears
            # from the Army Cost Calculator immediately without a populate_units run.
            deactivated_units = UnitType.objects.filter(
                product=product, is_active=True
            ).update(is_active=False)
            if deactivated_units:
                self.stdout.write(self.style.SUCCESS(
                    f'    └─ deactivated {deactivated_units} UnitType entry'
                ))

        self.stdout.write(self.style.SUCCESS('\napply_batch_fixes_apr2026b complete.'))
