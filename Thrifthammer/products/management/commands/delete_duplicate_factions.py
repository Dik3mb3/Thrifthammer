"""
One-time cleanup: delete the empty duplicate factions 'Adepta Sororitas'
(id=54) and 'Adeptus Custodes' (id=55) that were erroneously created as
duplicates of 'Sisters of Battle' and 'Custodes' respectively.

Safe to re-run — exits cleanly if neither faction exists.
"""
from django.core.management.base import BaseCommand

from products.models import Faction, Product


class Command(BaseCommand):
    """Delete empty duplicate factions created in error."""

    help = 'Delete empty duplicate Adepta Sororitas / Adeptus Custodes factions'

    def handle(self, *args, **options):
        """Delete the two duplicate factions if they exist and have no products."""
        targets = Faction.objects.filter(slug__in=['adepta-sororitas', 'adeptus-custodes'])

        if not targets.exists():
            self.stdout.write(self.style.SUCCESS('No duplicate factions found — nothing to do.'))
            return

        for faction in targets:
            product_count = Product.objects.filter(faction=faction).count()
            if product_count > 0:
                self.stderr.write(self.style.ERROR(
                    f'SKIPPED: {faction.name} has {product_count} products — will not delete.'
                ))
                continue
            self.stdout.write(f'Deleting: {faction.name} (slug={faction.slug})')
            faction.delete()

        self.stdout.write(self.style.SUCCESS('Done.'))
