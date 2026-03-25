"""
Management command: apply_batch_fixes_mar2026ad

Twenty-ninth wave of March 2026 batch corrections for ThriftHammer.

Changes covered:
  Fix 1  -- Force-set Product.gw_url for 13 SKUs, one transaction per product.
             Wave AB Fix 15 sets these inside a single large transaction; if
             any earlier fix in that transaction raises an exception the whole
             block rolls back and gw_url is never written.  This wave writes
             each product independently so a failure on one SKU cannot block
             the others.  Prints the before/after value for every SKU so the
             Railway log confirms exactly what happened.
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand

from products.models import Product

# Canonical Product.gw_url values — kept in sync with wave AB _GW_URLS.
_GW_URLS = {
    '54-21': 'https://www.warhammer.com/en-US/shop/imperial-knights-knight-dominus-knight-valiant-2022',
    'HA-021': 'https://www.warhammer.com/en-US/shop/Night-Lords-Leviathan-Dreadnought-2019',
    'NM-010': 'https://www.warhammer.com/en-US/shop/Necromunda-Escher-Gang-2017',
    'NM-011': 'https://www.warhammer.com/en-US/shop/Necromunda-Goliath-Gang-2017',
    'NM-012': 'https://www.warhammer.com/en-US/shop/Necromunda-Van-Saar-Gang-2018',
    '56-14':  'https://www.warhammer.com/en-US/shop/kill-team-xv26-stealth-battlesuits-2026',
    '48-29':  'https://www.warhammer.com/en-US/shop/kill-team-scout-squad-2024',
    '96-12':  'https://www.warhammer.com/en-US/shop/stormcast-eternals-knight-judicator-with-gryph-hounds-2021',
    '48-61':  'https://www.warhammer.com/en-US/shop/Space-Marine-Primaris-Lieutenant-With-Power-Sword-2020',
    '43-56':  'https://www.warhammer.com/en-US/shop/Death-Guard-Deathshroud-Bodyguard-2020',
    '51-42':  'https://www.warhammer.com/en-US/shop/Genestealer-Cults-Broodcoven',
    '59-20':  'https://www.warhammer.com/en-US/shop/Ad-Mec-Corpuscarii-Electro-Priests',
    '44-09':  'https://www.warhammer.com/en-US/shop/Ravenwing-Command-Squad-2020',
}


class Command(BaseCommand):
    """Apply wave-AD March 2026 batch corrections to products."""

    help = 'Apply wave-AD March 2026 batch corrections.'

    def handle(self, *args, **options):
        """Apply all fixes."""
        self.stdout.write('\napply_batch_fixes_mar2026ad')
        self.stdout.write('=' * 50)
        self._fix_1_force_gw_urls()
        self.stdout.write(self.style.SUCCESS('\nAll wave-AD fixes applied successfully.'))

    # -------------------------------------------------------------------------
    # Individual fixes
    # -------------------------------------------------------------------------

    def _fix_1_force_gw_urls(self):
        """
        Force-set Product.gw_url for 13 SKUs, one save per product.

        Each product is saved independently — not inside a shared transaction —
        so a failure on one SKU cannot roll back the others.  The before/after
        value is logged for every SKU so the Railway deploy log shows exactly
        what happened.
        """
        updated = 0
        already_ok = 0
        not_found = 0

        for gw_sku, target_url in _GW_URLS.items():
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  Fix 1: {gw_sku} -- NOT FOUND in DB'
                ))
                not_found += 1
                continue

            before = product.gw_url or '(blank)'
            if product.gw_url == target_url:
                self.stdout.write(
                    f'  Fix 1: {gw_sku} [{product.name[:40]}] -- already correct'
                )
                already_ok += 1
                # Still bust the cache in case the stale entry pre-dates the correct DB value.
                if product.slug:
                    cache.delete(f'product_detail|{product.slug}')
                continue

            product.gw_url = target_url
            product.save(update_fields=['gw_url'])

            self.stdout.write(self.style.SUCCESS(
                f'  Fix 1: {gw_sku} [{product.name[:40]}]'
                f' gw_url: {before[:60]} -> {target_url[:60]}'
            ))
            updated += 1

        self.stdout.write(
            f'  Fix 1 summary: {updated} updated, {already_ok} already correct,'
            f' {not_found} not found.'
        )
