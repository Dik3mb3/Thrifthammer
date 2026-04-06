"""
Management command: apply_batch_fixes_apr2026h

Fixes image_url for Rotigus and Great Unclean One -- images were empty
during populate_deathguard_phase3_products because the GW CAPTCHA blocked
product page fetches. Images retrieved via authenticated session fetch.

Also updates gw_sku with correct internal IDs retrieved at same time.

Idempotent -- safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

GW_IMG_BASE = 'https://www.warhammer.com/app/resources/catalog/product/920x950/'

FIXES = [
    (
        'nurgle-rotigus',
        '99129915063_NURMoNRotigusLead.jpg',
        'prod3700271-99129915063',
    ),
    (
        'nurgle-great-unclean-one',
        '99129915063_NURMoNGreatUncleanOneLead.jpg',
        'prod3700247-99129915063',
    ),
]


class Command(BaseCommand):
    """Fix missing image_url values for Rotigus and Great Unclean One."""

    help = 'Patches image_url and gw_sku for Rotigus and Great Unclean One. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        for slug, img_file, gw_sku in FIXES:
            product = Product.objects.filter(slug=slug).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  [skip] {slug} -- not found'))
                continue
            product.image_url = GW_IMG_BASE + img_file
            product.gw_sku = gw_sku
            product.save(update_fields=['image_url', 'gw_sku'])
            self.stdout.write(self.style.SUCCESS(f'  Fixed: {product.name} -> {img_file}'))

        self.stdout.write(self.style.SUCCESS('\napply_batch_fixes_apr2026h complete.'))
