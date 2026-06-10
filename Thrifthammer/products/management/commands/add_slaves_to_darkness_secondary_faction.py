"""
Management command: add_slaves_to_darkness_secondary_faction

Tags 4 existing 40K products with the Slaves to Darkness AoS secondary faction
so they appear on the Slaves to Darkness faction page without creating duplicate
records.

The products' primary faction FK is NOT changed. The M2M secondary_factions
field (migration 0061) powers the dual-display.

Dual-tagged products:
  99120201130  Daemon Prince            (primary: Chaos Space Marines 40K)
  CD-001       Be'lakor, the Dark Master (primary: Chaos Daemons 40K)
  99120201050  Chaos Spawn              (primary: Chaos Space Marines 40K)
  P-MUTALITH-VB Mutalith Vortex Beast  (primary: Thousand Sons 40K)

This command MUST run after populate_slaves_to_darkness_products (which creates
the Slaves to Darkness faction). In the Procfile it is placed immediately after
the three seed commands.

Idempotent -- ManyToManyField.add() is a no-op if the relation already exists.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('99120201130', 'Daemon Prince'),
    ('CD-001',      "Be'lakor, the Dark Master"),
    ('99120201050', 'Chaos Spawn'),
    ('P-MUTALITH-VB', 'Mutalith Vortex Beast'),
]


class Command(BaseCommand):
    """Tag existing 40K products with the Slaves to Darkness secondary faction."""

    help = 'Add Slaves to Darkness secondary faction tag to cross-faction products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            std_faction = Faction.objects.get(slug='slaves-to-darkness')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Slaves to Darkness faction not found in DB. '
                'Run populate_slaves_to_darkness_products first.'
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
            product.secondary_factions.add(std_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_slaves_to_darkness_secondary_faction complete. Tagged {tagged} product(s).'
        ))
