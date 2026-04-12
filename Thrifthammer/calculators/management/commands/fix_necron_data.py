"""
Management command: fix_necron_data

One-off fixes for Necron data issues:
  1. Delete duplicate Seraptek Heavy Construct with Synaptic Obliterators
     UnitType entries — keeps the original (id=645), deletes the rest.
  2. Fix Night Scythe scraper config — it's the same dual kit as Doom Scythe:
     - Change ebay_search_name to 'doom scythe necron' (scraper auto-searches)
     - Copy Amazon and Noble Knight URLs from Doom Scythe with manual_url_override=True

Usage:
    python manage.py fix_necron_data
    python manage.py fix_necron_data --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from calculators.models import UnitType
from prices.models import CurrentPrice
from products.models import Product, Retailer


DOOM_SCYTHE_ID = 278
NIGHT_SCYTHE_ID = 610
SERAPTEK_KEEP_ID = 645

# Retailers whose URLs should be manually overridden on Night Scythe
MANUAL_URL_RETAILERS = ['Amazon', 'Noble Knight Games']


class Command(BaseCommand):
    """Fix Necron data: remove Seraptek dupes and align Night Scythe with Doom Scythe."""

    help = 'Fix Seraptek duplicates and Night Scythe scraper config.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Run both fixes atomically."""
        dry_run = options['dry_run']

        with transaction.atomic():
            self._fix_seraptek_dupes(dry_run)
            self._fix_night_scythe(dry_run)

            if dry_run:
                self.stdout.write(self.style.WARNING('\nDry run — no changes written.'))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS('\nAll fixes applied successfully.'))

    def _fix_seraptek_dupes(self, dry_run):
        """Delete all Seraptek UnitType entries except the canonical one (id=645)."""
        self.stdout.write('\n=== Fix 1: Seraptek duplicates ===')

        dupes = UnitType.objects.filter(
            name='Seraptek Heavy Construct with Synaptic Obliterators'
        ).exclude(pk=SERAPTEK_KEEP_ID)

        count = dupes.count()
        self.stdout.write(f'  Found {count} duplicates (keeping id={SERAPTEK_KEEP_ID})')

        if count == 0:
            self.stdout.write('  Nothing to do.')
            return

        for u in dupes.order_by('pk')[:5]:
            self.stdout.write(f'  {"DRY-RUN " if dry_run else ""}DELETE id={u.pk}')
        if count > 5:
            self.stdout.write(f'  ... and {count - 5} more')

        if not dry_run:
            dupes.delete()
            self.stdout.write(self.style.SUCCESS(f'  Deleted {count} duplicates.'))

    def _fix_night_scythe(self, dry_run):
        """Align Night Scythe eBay search and copy manual URLs from Doom Scythe."""
        self.stdout.write('\n=== Fix 2: Night Scythe scraper config ===')

        night_scythe = Product.objects.get(pk=NIGHT_SCYTHE_ID)
        doom_scythe = Product.objects.get(pk=DOOM_SCYTHE_ID)

        # 1. Update eBay search name
        old_ebay = night_scythe.ebay_search_name
        new_ebay = doom_scythe.ebay_negative_keywords and 'doom scythe necron' or 'doom scythe necron'
        self.stdout.write(
            f'  {"DRY-RUN " if dry_run else ""}ebay_search_name: '
            f'"{old_ebay}" -> "doom scythe necron"'
        )
        if not dry_run:
            night_scythe.ebay_search_name = 'doom scythe necron'
            night_scythe.save(update_fields=['ebay_search_name'])

        # 2. Copy Amazon and Noble Knight URLs with manual override
        for retailer_name in MANUAL_URL_RETAILERS:
            try:
                retailer = Retailer.objects.get(name=retailer_name)
                doom_cp = CurrentPrice.objects.get(product=doom_scythe, retailer=retailer)
                night_cp = CurrentPrice.objects.get(product=night_scythe, retailer=retailer)

                self.stdout.write(
                    f'  {"DRY-RUN " if dry_run else ""}Set {retailer_name} URL: '
                    f'{doom_cp.url[:70] if doom_cp.url else "None"}'
                )

                if not dry_run:
                    night_cp.url = doom_cp.url
                    night_cp.manual_url_override = True
                    night_cp.save(update_fields=['url', 'manual_url_override'])

            except (Retailer.DoesNotExist, CurrentPrice.DoesNotExist) as e:
                self.stdout.write(self.style.WARNING(f'  SKIP {retailer_name}: {e}'))
