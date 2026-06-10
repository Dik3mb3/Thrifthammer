"""
Management command: add_fec_secondary_faction

Tags Nagash, Supreme Lord of the Undead (SG-016) with the Flesh-Eater Courts
secondary faction so it appears on the FEC faction page without creating a
duplicate product record.

The product's primary faction FK is NOT changed — it remains Soulblight
Gravelords. The M2M secondary_factions field powers the dual-display.

This command MUST run after populate_flesh_eater_courts_products (which ensures
the Flesh-Eater Courts faction exists). In the Procfile it is placed immediately
after that command.

Idempotent — safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product


class Command(BaseCommand):
    """Tag Nagash (SG-016) with the Flesh-Eater Courts secondary faction."""

    help = 'Add Flesh-Eater Courts secondary faction tag to Nagash (SG-016).'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            fec_faction = Faction.objects.get(slug='flesh-eater-courts')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Flesh-Eater Courts faction not found in DB. '
                'Run populate_flesh_eater_courts_products first.'
            ))
            return

        try:
            nagash = Product.objects.get(gw_sku='SG-016')
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Nagash (SG-016) not found in DB. '
                'Run populate_soulblight_gravelords_products first.'
            ))
            return

        nagash.secondary_factions.add(fec_faction)
        self.stdout.write(f'  tagged: {nagash.name} ({nagash.gw_sku})')

        self.stdout.write(self.style.SUCCESS(
            'add_fec_secondary_faction complete. Tagged 1 product.'
        ))
