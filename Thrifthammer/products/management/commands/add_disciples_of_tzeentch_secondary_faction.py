"""
Management command: add_disciples_of_tzeentch_secondary_faction

Tags existing products from Chaos Daemons, 40K daemon factions, and
Slaves to Darkness with the Disciples of Tzeentch secondary faction so
they appear on the Disciples of Tzeentch browse page without creating
duplicate records.

The products' primary faction FK is NOT changed. The M2M secondary_factions
field powers the dual-display.

This command MUST run after populate_disciples_of_tzeentch_products. In the
Procfile it is placed immediately after the three populate/seed commands.

Idempotent -- safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.

Usage:
    python manage.py add_disciples_of_tzeentch_secondary_faction
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('CD-010',                  'Changecaster'),
    ('CD-015',                  'The Changeling'),
    ('CD-016',                  'Burning Chariot of Tzeentch'),
    ('CD-017',                  'Exalted Flamer of Tzeentch'),
    ('CD-018',                  'Fateskimmer, Herald of Tzeentch on Burning Chariot'),
    ('P-TZEENTCH-SCREAMERS',    'Screamers of Tzeentch'),
    ('P-TZEENTCH-FLAMERS',      'Flamers of Tzeentch'),
    ('P-TZEENTCH-BLUEHORRORS',  'Blue Horrors and Brimstone Horrors'),
    ('P-TZEENTCH-KAIROS',       'Kairos Fateweaver'),
    ('P-TZEENTCH-LOC',          'Lord of Change'),
    ('S2D-009',                 'Gaunt Summoner'),
    ('99120201050',             'Chaos Spawn'),
]


class Command(BaseCommand):
    """Tag existing products with the Disciples of Tzeentch secondary faction."""

    help = 'Add Disciples of Tzeentch secondary faction tag to cross-faction Tzeentch products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            dot_faction = Faction.objects.get(slug='disciples-of-tzeentch')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Disciples of Tzeentch faction not found. '
                'Run populate_disciples_of_tzeentch_products first.'
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
            product.secondary_factions.add(dot_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_disciples_of_tzeentch_secondary_faction complete. Tagged {tagged} product(s).'
        ))
