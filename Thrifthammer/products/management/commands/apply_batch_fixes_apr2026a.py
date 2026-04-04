"""
Management command: apply_batch_fixes_apr2026a

First wave of April 2026 batch corrections for ThriftHammer.

Changes covered:
  Fix 1  -- Mek Gunz: Traktor Kannon (slug: ork-mek-gunz-traktor-kannon)
             Set ebay_search_name = 'Ork Mek Gunz' so the eBay updater finds
             the GW box listing instead of searching the variant-specific name.
             eBay sellers list all Mek Gunz variants under the generic box title.

  Fix 2  -- Mek Gunz: Kustom Mega-kannon (slug: ork-mek-gunz-kustom-mega-kannon)
             Same fix as Fix 1.

  Fix 3  -- Mek Gunz: Bubblechukka (slug: ork-mek-gunz-bubblechukka)
             Same fix as Fix 1.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

MEK_GUNZ_SLUGS = [
    'ork-mek-gunz-traktor-kannon',
    'ork-mek-gunz-kustom-mega-kannon',
    'ork-mek-gunz-bubblechukka',
]

EBAY_SEARCH_NAME = 'Ork Mek Gunz'


class Command(BaseCommand):
    """Set ebay_search_name override on Mek Gunz variant products."""

    help = (
        'Sets ebay_search_name="Ork Mek Gunz" on the three Mek Gunz variant '
        'products so the eBay price updater can find their shared GW box listing. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Apply the ebay_search_name fix to each Mek Gunz variant."""
        updated = 0
        skipped = 0

        for slug in MEK_GUNZ_SLUGS:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  [skip] Product not found: {slug}'
                ))
                skipped += 1
                continue

            if product.ebay_search_name == EBAY_SEARCH_NAME:
                self.stdout.write(
                    f'  [no-op] {product.name} — already set'
                )
                skipped += 1
                continue

            old = product.ebay_search_name or '(empty)'
            product.ebay_search_name = EBAY_SEARCH_NAME
            product.save(update_fields=['ebay_search_name'])

            self.stdout.write(self.style.SUCCESS(
                f'  Updated: {product.name}  "{old}" → "{EBAY_SEARCH_NAME}"'
            ))
            updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\napply_batch_fixes_apr2026a complete — '
            f'{updated} updated, {skipped} skipped.'
        ))
