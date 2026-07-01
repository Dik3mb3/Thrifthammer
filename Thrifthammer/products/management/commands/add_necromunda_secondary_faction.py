"""
Management command: add_necromunda_secondary_faction

Tags 5 existing products with the Necromunda secondary faction so they
appear on the Necromunda faction page without creating duplicate records.

The products' primary faction FK is NOT changed — they remain in their
current faction (Genestealer Cults or Astra Militarum). The M2M
secondary_factions field powers the dual-display.

This command MUST run after populate_necromunda_products (which creates
the Necromunda faction). In the Procfile it is placed immediately after
the three Necromunda seed commands.

Idempotent — safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('GC-006', 'Genestealer Cults Atalan Jackals'),
    ('GC-010', 'Genestealer Cults Goliath Rockgrinder'),
    ('GC-011', 'Genestealer Cults Goliath Truck'),
    ('GC-016', 'Genestealer Cults Achilles Ridgerunner'),
    ('AM-044', 'Taurox'),
]


class Command(BaseCommand):
    """Tag existing products with the Necromunda secondary faction."""

    help = 'Add Necromunda secondary faction tag to cross-system products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            nm_faction = Faction.objects.get(slug='necromunda')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Necromunda faction not found in DB. '
                'Run populate_necromunda_products first.'
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
            product.secondary_factions.add(nm_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_necromunda_secondary_faction complete. Tagged {tagged} product(s).'
        ))
