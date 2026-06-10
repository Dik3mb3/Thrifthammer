"""
Management command: apply_batch_fixes_may2026r

Changes:
  59-11  Adeptus Mechanicus Skitarii Vanguard
    ebay_negative_keywords: add 'transuranic arquebus'
    Old: 'legions imperialis Resin 04-113 Arc Rifle'
    New: 'legions imperialis Resin 04-113 Arc Rifle transuranic arquebus'

  59-16  Adeptus Mechanicus Dunecrawler
    ebay_negative_keywords: add 'Search Light ray'
    Old: 'legions imperialis Resin 04-113 Neutron Laser'
    New: 'legions imperialis Resin 04-113 Neutron Laser Search Light ray'
"""

from django.core.management.base import BaseCommand

from products.models import Product


_FIXES = [
    (
        '59-11',
        'Adeptus Mechanicus Skitarii Vanguard',
        'legions imperialis Resin 04-113 Arc Rifle transuranic arquebus',
    ),
    (
        '59-16',
        'Adeptus Mechanicus Dunecrawler',
        'legions imperialis Resin 04-113 Neutron Laser Search Light ray',
    ),
]


class Command(BaseCommand):
    """Extend eBay negative keywords for Skitarii Vanguard and Dunecrawler."""

    help = (
        'Sets ebay_negative_keywords for 59-11 (add transuranic arquebus) '
        'and 59-16 (add Search Light ray). Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        updated_total = 0

        for gw_sku, name, keywords in _FIXES:
            updated = Product.objects.filter(gw_sku=gw_sku).update(
                ebay_negative_keywords=keywords,
            )
            if updated:
                self.stdout.write(
                    f'  Updated ebay_negative_keywords: {name} ({gw_sku})'
                )
                updated_total += updated
            else:
                self.stdout.write(self.style.WARNING(
                    f'  Not found: {name} ({gw_sku}) -- skipped.'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_may2026r complete. {updated_total} product(s) updated.'
        ))
