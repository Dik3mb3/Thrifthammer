"""
Management command: add_kragnos_secondary_factions

Tags Kragnos, the End of Empires (GG-009) with the Ogor Mawtribes,
Sons of Behemat, and Orruk Warclans secondary factions so it appears on
all three faction pages without creating duplicate product records.

The product's primary faction FK is NOT changed -- it remains Gloomspite
Gitz. The M2M secondary_factions field powers the dual-display.

This command MUST run after populate_ogor_mawtribes_products,
populate_sons_of_behemat_products, and populate_orruk_warclans_products
(which ensure all three factions exist in the DB). In the Procfile it is
placed after all three populate commands.

Idempotent -- safe to re-run. ManyToManyField.add() is a no-op if the
relation already exists.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product


class Command(BaseCommand):
    """Tag Kragnos (GG-009) with Ogor Mawtribes, Sons of Behemat, and Orruk Warclans."""

    help = (
        'Add Ogor Mawtribes, Sons of Behemat, and Orruk Warclans secondary faction '
        'tags to Kragnos, the End of Empires (GG-009).'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            kragnos = Product.objects.get(gw_sku='GG-009')
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Kragnos (GG-009) not found in DB. '
                'Run populate_gloomspite_products first.'
            ))
            return

        factions_to_add = [
            ('ogor-mawtribes', 'Ogor Mawtribes', 'populate_ogor_mawtribes_products'),
            ('sons-of-behemat', 'Sons of Behemat', 'populate_sons_of_behemat_products'),
            ('orruk-warclans', 'Orruk Warclans', 'populate_orruk_warclans_products'),
        ]

        tagged = 0
        for slug, name, prereq in factions_to_add:
            try:
                faction = Faction.objects.get(slug=slug)
            except Faction.DoesNotExist:
                self.stderr.write(self.style.ERROR(
                    f'{name} faction not found -- run {prereq} first.'
                ))
                continue
            kragnos.secondary_factions.add(faction)
            self.stdout.write(f'  tagged: {kragnos.name} ({kragnos.gw_sku}) → {name}')
            tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'add_kragnos_secondary_factions complete. Tagged {tagged} faction(s).'
        ))
