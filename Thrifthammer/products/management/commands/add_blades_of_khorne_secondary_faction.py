"""
Management command: add_blades_of_khorne_secondary_faction

Tags existing products from Chaos Daemons and 40K daemon factions with the
Blades of Khorne secondary faction so they appear on the Blades of Khorne
faction browse page without creating duplicate records.

The products' primary faction FK is NOT changed. The M2M secondary_factions
field powers the dual-display.

This command MUST run after populate_blades_of_khorne_products (which creates
the Blades of Khorne faction). In the Procfile it is placed immediately after
the three populate/seed commands for this faction.

Idempotent -- safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.

Usage:
    python manage.py add_blades_of_khorne_secondary_faction
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('CD-006',                  'Skulltaker'),
    ('CD-007',                  'Skull Altar'),
    ('CD-011',                  'Karanak'),
    ('CD-012',                  'Bloodmaster, Herald of Khorne'),
    ('CD-019',                  'Skull Cannon'),
    ('CD-020',                  'Rendmaster, Herald of Khorne on Blood Throne'),
    ('P-KHORNE-FLESHHOUNDS',    'Flesh Hounds'),
    ('P-KHORNE-BLOODTHIRSTER',  'Bloodthirster'),
    ('P-KHORNE-BLOODCRUSHERS',  'Bloodcrushers'),
    ('P-KHORNE-SKARBRAND',      'Skarbrand'),
]


class Command(BaseCommand):
    """Tag existing products with the Blades of Khorne secondary faction."""

    help = 'Add Blades of Khorne secondary faction tag to cross-faction Khorne products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            bok_faction = Faction.objects.get(slug='blades-of-khorne')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Blades of Khorne faction not found. '
                'Run populate_blades_of_khorne_products first.'
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
            product.secondary_factions.add(bok_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_blades_of_khorne_secondary_faction complete. Tagged {tagged} product(s).'
        ))
