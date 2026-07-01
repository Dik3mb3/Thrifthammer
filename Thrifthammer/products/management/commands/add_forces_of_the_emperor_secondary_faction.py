"""
Management command: add_forces_of_the_emperor_secondary_faction

Tags 7 existing products with the Forces of the Emperor secondary faction
so they appear on the Forces of the Emperor (Horus Heresy) faction page
without creating duplicate records.

The products' primary faction FK is NOT changed — they remain in their
current faction (Custodes). The M2M secondary_factions field powers the
dual-display.

This command MUST run after populate_forces_of_the_emperor_products (which
creates the Forces of the Emperor faction). In the Procfile it is placed
immediately after populate_forces_of_the_emperor_products.

Idempotent — safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('AC-004', 'Custodes Caladius Annihilator Grav-tank'),
    ('AC-005', 'Custodes Caladius Grav-tank'),
    ('AC-007', 'Custodes Coronus Grav-carrier'),
    ('AC-008', 'Custodes Custodian Dreadnought'),
    ('AC-023', 'Legio Custodes Shield Captain'),
    ('01-08', 'Adeptus Custodes Custodian Guard'),
    ('01-10', 'Adeptus Custodes Custodian Wardens'),
]


class Command(BaseCommand):
    """Tag existing products with the Forces of the Emperor secondary faction."""

    help = 'Add Forces of the Emperor secondary faction tag to cross-system products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            foe_faction = Faction.objects.get(slug='forces-of-the-emperor')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Forces of the Emperor faction not found in DB. '
                'Run populate_forces_of_the_emperor_products first.'
            ))
            return

        sku_list = [sku for sku, _ in _DUAL_TAG_SKUS]
        products = list(
            Product.objects.filter(gw_sku__in=sku_list).order_by('gw_sku', 'name')
        )

        if not products:
            self.stdout.write(self.style.WARNING('No matching products found.'))
            return

        tagged = 0
        for product in products:
            product.secondary_factions.add(foe_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_forces_of_the_emperor_secondary_faction complete. Tagged {tagged} product(s).'
        ))
