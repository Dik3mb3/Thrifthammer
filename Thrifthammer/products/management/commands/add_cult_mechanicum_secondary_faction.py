"""
Management command: add_cult_mechanicum_secondary_faction

Tags 2 existing products with the Cult Mechanicum secondary faction so they
appear on the Cult Mechanicum (Horus Heresy) faction page without creating
duplicate records.

The products' primary faction FK is NOT changed — they remain in their
current faction (Imperial Knights). The M2M secondary_factions field
powers the dual-display.

This command MUST run after populate_cult_mechanicum_products (which
creates the Cult Mechanicum faction). In the Procfile it is placed
immediately after populate_cult_mechanicum_products.

Idempotent — safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('31-67', 'Cerastus Knight Acheron'),
    ('31-66', 'Cerastus Knight Castigator'),
]


class Command(BaseCommand):
    """Tag existing products with the Cult Mechanicum secondary faction."""

    help = 'Add Cult Mechanicum secondary faction tag to cross-system products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            cm_faction = Faction.objects.get(slug='cult-mechanicum')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Cult Mechanicum faction not found in DB. '
                'Run populate_cult_mechanicum_products first.'
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
            product.secondary_factions.add(cm_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_cult_mechanicum_secondary_faction complete. Tagged {tagged} product(s).'
        ))
