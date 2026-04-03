"""
Management command: list_batch_skus

Lists all products with a given batch_tag so you can quickly pull a
scraping target list without having to re-scrape the entire catalogue.

Usage:
    python manage.py list_batch_skus phase-2
    python manage.py list_batch_skus phase-3 --format csv
    python manage.py list_batch_skus phase-2 --format names

Output formats:
    table  (default) — aligned columns: name | gw_sku | faction | batch_tag
    csv              — name,gw_sku,faction,batch_tag  (paste into spreadsheet)
    names            — product names only, one per line
    skus             — gw_sku values only, one per line

List all tags currently in use:
    python manage.py list_batch_skus --list-tags
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Export a SKU list for a given batch_tag."""

    help = 'List products by batch_tag for targeted scraping.'

    def add_arguments(self, parser):
        parser.add_argument(
            'tag',
            nargs='?',
            help='The batch_tag to filter by (e.g. phase-2).',
        )
        parser.add_argument(
            '--format',
            choices=['table', 'csv', 'names', 'skus'],
            default='table',
            help='Output format (default: table).',
        )
        parser.add_argument(
            '--list-tags',
            action='store_true',
            help='Show all batch_tag values currently in use and exit.',
        )

    def handle(self, *args, **options):
        """Run the command."""
        if options['list_tags']:
            tags = (
                Product.objects
                .exclude(batch_tag='')
                .values_list('batch_tag', flat=True)
                .distinct()
                .order_by('batch_tag')
            )
            if not tags:
                self.stdout.write('No batch tags in use yet.')
                return
            self.stdout.write('Batch tags in use:')
            for tag in tags:
                count = Product.objects.filter(batch_tag=tag).count()
                self.stdout.write(f'  {tag}  ({count} products)')
            return

        tag = options.get('tag')
        if not tag:
            self.stderr.write(self.style.ERROR(
                'Provide a tag name or use --list-tags to see all tags.\n'
                'Usage: python manage.py list_batch_skus phase-2'
            ))
            return

        products = (
            Product.objects
            .filter(batch_tag=tag)
            .select_related('faction')
            .order_by('faction__name', 'name')
        )

        if not products.exists():
            self.stderr.write(self.style.WARNING(f'No products found with batch_tag="{tag}".'))
            return

        fmt = options['format']

        if fmt == 'skus':
            for p in products:
                self.stdout.write(p.gw_sku)

        elif fmt == 'names':
            for p in products:
                self.stdout.write(p.name)

        elif fmt == 'csv':
            self.stdout.write('name,gw_sku,faction,batch_tag')
            for p in products:
                faction = p.faction.name if p.faction else ''
                self.stdout.write(f'"{p.name}","{p.gw_sku}","{faction}","{p.batch_tag}"')

        else:  # table
            self.stdout.write(f'\nProducts tagged "{tag}":\n')
            row = f'  {"Name":<50} {"GW SKU":<15} {"Faction":<25}'
            self.stdout.write(row)
            self.stdout.write('  ' + '-' * 88)
            for p in products:
                faction = p.faction.name if p.faction else '-'
                self.stdout.write(
                    f'  {p.name:<50} {p.gw_sku:<15} {faction:<25}'
                )
            self.stdout.write(f'\n  Total: {products.count()} products')
