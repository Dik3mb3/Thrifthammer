"""
Management command: apply_batch_fixes_may2026u

Changes:
  ALL products
    ebay_negative_keywords: append 'Proxies'
    (DB-level Concat — preserves existing keywords, skips products
     that already contain 'Proxies' so the command is idempotent)

  48-76  Space Marine Assault Intercessors
    ebay_negative_keywords: add 'firstborn' (SKU-specific, on top of global Proxies)
    Old: 'legions imperialis Resin 04-113'
    New: 'legions imperialis Resin 04-113 Proxies firstborn'

  50-10  Ork Boyz
    ebay_negative_keywords: add 'Bosspole knives Eavy' (SKU-specific, on top of global Proxies)
    Old: 'lootas legions imperialis Resin 04-113'
    New: 'lootas legions imperialis Resin 04-113 Proxies Bosspole knives Eavy'
"""

from django.core.management.base import BaseCommand
from django.db.models import F, Value
from django.db.models.functions import Concat

from products.models import Product


class Command(BaseCommand):
    help = (
        'Appends Proxies to all products\' ebay_negative_keywords; '
        'adds firstborn to 48-76 (Space Marine Assault Intercessors). Idempotent.'
    )

    def handle(self, *args, **options):
        # Step 1: Add Proxies globally.
        # Products with no existing keywords.
        empty_updated = Product.objects.filter(ebay_negative_keywords='').update(
            ebay_negative_keywords='Proxies'
        )
        # Products with existing keywords that don't already contain Proxies.
        concat_updated = (
            Product.objects
            .exclude(ebay_negative_keywords='')
            .exclude(ebay_negative_keywords__icontains='Proxies')
            .update(ebay_negative_keywords=Concat(F('ebay_negative_keywords'), Value(' Proxies')))
        )
        total_proxies = empty_updated + concat_updated
        self.stdout.write(f'  Added Proxies to {total_proxies} product(s) globally.')

        # Step 2: Add firstborn to 48-76 (Space Marine Assault Intercessors).
        # Complete desired string after the global Proxies update above.
        updated = Product.objects.filter(gw_sku='48-76').update(
            ebay_negative_keywords='legions imperialis Resin 04-113 Proxies firstborn',
        )
        if updated:
            self.stdout.write(
                '  Updated ebay_negative_keywords: Space Marine Assault Intercessors (48-76)'
            )
        else:
            self.stdout.write(self.style.WARNING(
                '  Not found: Space Marine Assault Intercessors (48-76) -- skipped.'
            ))

        # Step 3: Add Bosspole, knives, Eavy to 50-10 (Ork Boyz).
        updated = Product.objects.filter(gw_sku='50-10').update(
            ebay_negative_keywords='lootas legions imperialis Resin 04-113 Proxies Bosspole knives Eavy',
        )
        if updated:
            self.stdout.write(
                '  Updated ebay_negative_keywords: Ork Boyz (50-10)'
            )
        else:
            self.stdout.write(self.style.WARNING(
                '  Not found: Ork Boyz (50-10) -- skipped.'
            ))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_may2026u complete.'))
