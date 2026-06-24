"""
Management command: add_maggotkin_of_nurgle_secondary_faction

Tags existing products from Chaos Daemons and 40K Nurgle daemon factions
with the Maggotkin of Nurgle secondary faction so they appear on the
Maggotkin of Nurgle browse page without creating duplicate records.

The products' primary faction FK is NOT changed. The M2M secondary_factions
field powers the dual-display.

This command MUST run after populate_maggotkin_of_nurgle_products. In the
Procfile it is placed immediately after the three populate/seed commands.

Idempotent -- safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.

Usage:
    python manage.py add_maggotkin_of_nurgle_secondary_faction
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('CD-008',                    'Feculent Gnarlmaw'),
    ('CD-009',                    'Horticulous Slimux'),
    ('CD-013',                    'Sloppity Bilepiper'),
    ('CD-014',                    'Poxbringer, Herald of Nurgle'),
    ('prod3700271-99129915063',   'Rotigus'),
    ('prod3700247-99129915063',   'Great Unclean One'),
    ('prod3700246-99129915062',   'Beast of Nurgle'),
    ('prod3610130-99129915038',   'Plague Drones'),
    ('prod3550127-99129915060',   'Nurglings'),
]


class Command(BaseCommand):
    """Tag existing products with the Maggotkin of Nurgle secondary faction."""

    help = 'Add Maggotkin of Nurgle secondary faction tag to cross-faction Nurgle products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            mon_faction = Faction.objects.get(slug='maggotkin-of-nurgle')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Maggotkin of Nurgle faction not found. '
                'Run populate_maggotkin_of_nurgle_products first.'
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
            product.secondary_factions.add(mon_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_maggotkin_of_nurgle_secondary_faction complete. Tagged {tagged} product(s).'
        ))
