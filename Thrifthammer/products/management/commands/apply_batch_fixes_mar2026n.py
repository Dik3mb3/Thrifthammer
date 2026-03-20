"""
Management command: apply_batch_fixes_mar2026n

Fourteenth wave of March 2026 batch corrections for ThriftHammer.
Run after apply_batch_fixes_mar2026m.

Changes covered:
  Fix 1 -- Grey Knights Strike Squad (57-06): Correct Amazon URL
            Old: https://www.amazon.com/dp/B08QJ4FCSL
            New: https://www.amazon.com/dp/B00MYGOM3Y

  Fix 2 -- Grey Knights Terminators (57-08): Add Amazon URL (was blank)
            New: https://www.amazon.com/dp/B09C3NTQSP

  Fix 3 -- Horus Heresy: Age of Darkness (HH-001): Deactivate (is_active=False)

  Fix 4 -- Horus Heresy Cataphractii Terminators (HA-030): Add Amazon URL (was blank)
            New: https://www.amazon.com/dp/B0GJTJPKMV

  Fix 5 -- Horus Heresy Chaplain in Terminator Armour (HA-051):
            - Rename  -> "Space Marine Chaplain in Terminator Armour"
            - Faction -> Space Marines (id=597)  [was None]
            - Slug    -> "space-marine-chaplain-in-terminator-armour"
            - ebay_search_name -> "Space Marines Chaplain Terminator Armour"
            - eBay URL -> https://www.ebay.com/itm/175928493136  (was blank)

  Fix 6 -- Horus Heresy Leviathan Dreadnought (HA-021): Correct GW URL
            New: https://www.warhammer.com/en-WW/shop/
                 leviathan-siege-dreadnought-with-claw-and-drill-weapons-2022

Usage:
    python manage.py apply_batch_fixes_mar2026n
    python manage.py apply_batch_fixes_mar2026n --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice
from products.models import Faction, Product, Retailer


class Command(BaseCommand):
    """Fourteenth wave of March 2026 ThriftHammer DB corrections."""

    help = (
        'Apply Wave N batch corrections (March 2026) -- '
        'GK/HH Amazon URLs, Age of Darkness deactivate, Chaplain rename.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag to preview changes without saving."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print planned changes without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute all Wave N corrections in order."""
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN -- no changes will be saved.\n'))

        self._fix_1_gk_strike_squad_amazon(dry)
        self._fix_2_gk_terminators_amazon(dry)
        self._fix_3_age_of_darkness_deactivate(dry)
        self._fix_4_cataphractii_amazon(dry)
        self._fix_5_chaplain_rename_reclassify(dry)
        self._fix_6_leviathan_gw_url(dry)

        if dry:
            self.stdout.write(self.style.WARNING('\nDRY RUN complete -- nothing was saved.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nWave N complete.'))

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _get_product(self, gw_sku):
        """Fetch a product by gw_sku, writing an error and returning None if missing."""
        try:
            return Product.objects.get(gw_sku=gw_sku)
        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'  ERROR: Product {gw_sku} not found.'))
            return None

    def _set_url(self, product, retailer_name, new_url, dry):
        """
        Update a CurrentPrice URL for a given retailer.

        Creates the row if it does not exist; skips if URL already matches.
        """
        try:
            retailer = Retailer.objects.get(name=retailer_name)
        except Retailer.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f'  ERROR: Retailer "{retailer_name}" not found.')
            )
            return

        cp, created = CurrentPrice.objects.get_or_create(
            product=product,
            retailer=retailer,
            defaults={'price': None, 'in_stock': False, 'url': new_url},
        )
        if created:
            self.stdout.write(f'  [ok] Created {retailer_name} entry: {new_url[:70]}')
            return

        if cp.url == new_url:
            self.stdout.write(f'  [skip] {retailer_name}: URL already correct')
            return

        old_url = cp.url or '(blank)'
        if dry:
            self.stdout.write(
                f'  [dry] {retailer_name}: {old_url[:60]}\n'
                f'             -> {new_url[:60]}'
            )
            return

        cp.url = new_url
        cp.save(update_fields=['url'])
        self.stdout.write(
            f'  [ok] {retailer_name}: {old_url[:50]} -> {new_url[:60]}'
        )

    # -----------------------------------------------------------------------
    # Fixes
    # -----------------------------------------------------------------------

    def _fix_1_gk_strike_squad_amazon(self, dry):
        """Fix 1: Correct Amazon URL for Grey Knights Strike Squad (57-06)."""
        self.stdout.write('\nFix 1: Grey Knights Strike Squad -- Amazon URL')
        p = self._get_product('57-06')
        if p:
            self._set_url(p, 'Amazon', 'https://www.amazon.com/dp/B00MYGOM3Y', dry)

    def _fix_2_gk_terminators_amazon(self, dry):
        """Fix 2: Add Amazon URL for Grey Knights Terminators (57-08)."""
        self.stdout.write('\nFix 2: Grey Knights Terminators -- Amazon URL')
        p = self._get_product('57-08')
        if p:
            self._set_url(p, 'Amazon', 'https://www.amazon.com/dp/B09C3NTQSP', dry)

    def _fix_3_age_of_darkness_deactivate(self, dry):
        """Fix 3: Deactivate Horus Heresy: Age of Darkness (HH-001)."""
        self.stdout.write('\nFix 3: Horus Heresy: Age of Darkness -- deactivate')
        p = self._get_product('HH-001')
        if p is None:
            return
        if not p.is_active:
            self.stdout.write('  [skip] Already inactive')
            return
        if dry:
            self.stdout.write(f'  [dry] "{p.name}" -- is_active: True -> False')
            return
        p.is_active = False
        p.save(update_fields=['is_active'])
        self.stdout.write(self.style.SUCCESS(f'  [ok] "{p.name}" deactivated'))

    def _fix_4_cataphractii_amazon(self, dry):
        """Fix 4: Add Amazon URL for Horus Heresy Cataphractii Terminators (HA-030)."""
        self.stdout.write('\nFix 4: Horus Heresy Cataphractii Terminators -- Amazon URL')
        p = self._get_product('HA-030')
        if p:
            self._set_url(p, 'Amazon', 'https://www.amazon.com/dp/B0GJTJPKMV', dry)

    def _fix_5_chaplain_rename_reclassify(self, dry):
        """
        Fix 5: Rename HA-051 and reclassify to Space Marines.

        Changes:
          - name: "Horus Heresy Chaplain in Terminator Armour"
               -> "Space Marine Chaplain in Terminator Armour"
          - slug: regenerated from new name
          - faction: None -> Space Marines
          - ebay_search_name: '' -> 'Space Marines Chaplain Terminator Armour'
          - eBay URL: blank -> https://www.ebay.com/itm/175928493136
        """
        self.stdout.write('\nFix 5: Chaplain in Terminator Armour -- rename + reclassify')
        p = self._get_product('HA-051')
        if p is None:
            return

        try:
            sm_faction = Faction.objects.get(name='Space Marines')
        except Faction.DoesNotExist:
            self.stderr.write(
                self.style.ERROR('  ERROR: Faction "Space Marines" not found.')
            )
            return

        new_name = 'Space Marine Chaplain in Terminator Armour'
        new_slug = slugify(new_name)
        new_search = 'Space Marines Chaplain Terminator Armour'
        fields = []

        if p.name != new_name:
            if dry:
                self.stdout.write(f'  [dry] name: "{p.name}" -> "{new_name}"')
                self.stdout.write(f'  [dry] slug: "{p.slug}" -> "{new_slug}"')
            else:
                p.name = new_name
                p.slug = new_slug
                fields += ['name', 'slug']
                self.stdout.write(f'  [ok] name -> "{new_name}"')
                self.stdout.write(f'  [ok] slug -> "{new_slug}"')
        else:
            self.stdout.write('  [skip] name already correct')

        if p.faction != sm_faction:
            if dry:
                self.stdout.write(
                    f'  [dry] faction: {p.faction} -> Space Marines'
                )
            else:
                p.faction = sm_faction
                fields.append('faction')
                self.stdout.write('  [ok] faction -> Space Marines')
        else:
            self.stdout.write('  [skip] faction already Space Marines')

        if p.ebay_search_name != new_search:
            if dry:
                self.stdout.write(
                    f'  [dry] ebay_search_name: "{p.ebay_search_name}" -> "{new_search}"'
                )
            else:
                p.ebay_search_name = new_search
                fields.append('ebay_search_name')
                self.stdout.write(f'  [ok] ebay_search_name -> "{new_search}"')
        else:
            self.stdout.write('  [skip] ebay_search_name already correct')

        if not dry and fields:
            p.save(update_fields=fields)

        self._set_url(p, 'eBay', 'https://www.ebay.com/itm/175928493136', dry)

    def _fix_6_leviathan_gw_url(self, dry):
        """Fix 6: Correct GW URL for Horus Heresy Leviathan Dreadnought (HA-021)."""
        self.stdout.write('\nFix 6: Horus Heresy Leviathan Dreadnought -- GW URL')
        p = self._get_product('HA-021')
        if p:
            gw_url = (
                'https://www.warhammer.com/en-WW/shop/'
                'leviathan-siege-dreadnought-with-claw-and-drill-weapons-2022'
            )
            self._set_url(p, 'Games Workshop', gw_url, dry)
