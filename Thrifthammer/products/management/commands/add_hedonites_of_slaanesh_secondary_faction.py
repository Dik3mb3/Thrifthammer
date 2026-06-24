"""
Management command: add_hedonites_of_slaanesh_secondary_faction

Tags existing products from Chaos Daemons and 40K Slaanesh daemon factions
with the Hedonites of Slaanesh secondary faction so they appear on the
Hedonites of Slaanesh browse page without creating duplicate records.

The products' primary faction FK is NOT changed. The M2M secondary_factions
field powers the dual-display.

This command MUST run after populate_hedonites_of_slaanesh_products. In the
Procfile it is placed immediately after the three populate/seed commands.

Idempotent -- safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.

Usage:
    python manage.py add_hedonites_of_slaanesh_secondary_faction
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

# (gw_sku, display name for logging)
_DUAL_TAG_SKUS = [
    ('CD-002',          "Syll'Esske: The Vengeful Allegiance"),
    ('CD-003',          'The Contorted Epitome'),
    ('CD-004',          'Infernal Enrapturess'),
    # CD-005 The Masque: slug collision -- already in DB as Chaos Daemons, so not in populate
    ('CD-005',          'The Masque'),
    ('99129915036',     'Daemonettes of Slaanesh'),
    ('99129915056',     'Keeper of Secrets / Shalaxi Helbane'),
    ('99129915052',     'Fiends'),
    ('99129915005',     'Seekers of Slaanesh'),
]


class Command(BaseCommand):
    """Tag existing products with the Hedonites of Slaanesh secondary faction."""

    help = 'Add Hedonites of Slaanesh secondary faction tag to cross-faction Slaanesh products.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            hos_faction = Faction.objects.get(slug='hedonites-of-slaanesh')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Hedonites of Slaanesh faction not found. '
                'Run populate_hedonites_of_slaanesh_products first.'
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
            product.secondary_factions.add(hos_faction)
            self.stdout.write(f'  tagged: {product.name} ({product.gw_sku})')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_hedonites_of_slaanesh_secondary_faction complete. Tagged {tagged} product(s).'
        ))
