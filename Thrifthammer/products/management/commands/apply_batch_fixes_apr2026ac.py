"""
Management command: apply_batch_fixes_apr2026ac

Fixes three Aeldari UnitType SKU issues that left army-calculator entries
without a linked product (no SKU shown in the UI, no price data):

1. Delete the stale "Aeldari Wraithguard" UnitType (product=NULL).
   This entry was orphaned when apply_batch_fixes_apr2026j deleted the
   craftworlds-wraithguard product (ON DELETE SET_NULL).  The correct
   "Wraithguard" UnitType linked to the aeldari-wraithguard product
   already exists; the old entry is a duplicate with no product.

2. Link the correct product to the Yvraine, The Visarch, and The Yncarne
   UnitTypes.  populate_units created these entries with product=NULL
   (Ynnari characters were not part of the original product seed).
   populate_aeldari_phase3_products subsequently failed to update them
   because it keyed update_or_create on (product, faction) instead of
   (name, faction), so the NULL rows were never repaired.

Safe to run repeatedly (idempotent).

Usage:
    python manage.py apply_batch_fixes_apr2026ac
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from products.models import Faction, Product

_FACTION_NAME = 'Aeldari'

# Ynnari characters: (UnitType.name, Product.slug)
_YNNARI_FIXES = [
    ('Yvraine',      'aeldari-yvraine'),
    ('The Visarch',  'aeldari-the-visarch'),
    ('The Yncarne',  'aeldari-the-yncarne'),
]


class Command(BaseCommand):
    """Delete orphaned UnitType and link Ynnari products to their UnitTypes."""

    help = (
        'Deletes the stale "Aeldari Wraithguard" UnitType (product=NULL) and '
        'links the correct products to Yvraine, The Visarch, and The Yncarne '
        'UnitTypes. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        faction = Faction.objects.filter(name=_FACTION_NAME).first()
        if not faction:
            self.stderr.write(self.style.ERROR(
                f'{_FACTION_NAME} faction not found.'
            ))
            return

        # ── 1. Delete stale "Aeldari Wraithguard" UnitType ───────────────────
        stale_qs = UnitType.objects.filter(
            name='Aeldari Wraithguard',
            faction=faction,
            product__isnull=True,
        )
        count = stale_qs.count()
        if count:
            stale_qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f'  Deleted {count} stale "Aeldari Wraithguard" UnitType(s) '
                f'(product=NULL).'
            ))
        else:
            self.stdout.write(
                '  No stale "Aeldari Wraithguard" UnitType found (already clean).'
            )

        # ── 2. Link Ynnari character products to their UnitTypes ──────────────
        for unit_name, product_slug in _YNNARI_FIXES:
            product = Product.objects.filter(slug=product_slug).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  SKIP: product not found for slug {product_slug!r}.'
                ))
                continue

            unit = UnitType.objects.filter(name=unit_name, faction=faction).first()
            if not unit:
                self.stdout.write(self.style.WARNING(
                    f'  SKIP: UnitType not found for {unit_name!r}.'
                ))
                continue

            if unit.product_id == product.pk:
                self.stdout.write(
                    f'  Already linked: {unit_name!r} -> {product_slug}'
                )
                continue

            unit.product = product
            unit.save()
            self.stdout.write(self.style.SUCCESS(
                f'  Linked: {unit_name!r} -> {product_slug} (pk={product.pk})'
            ))

        self.stdout.write(self.style.SUCCESS(
            '\napply_batch_fixes_apr2026ac complete.'
        ))
