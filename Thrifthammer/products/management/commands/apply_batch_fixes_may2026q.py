"""
Management command: apply_batch_fixes_may2026q

Changes:
  59-10  Adeptus Mechanicus Skitarii Rangers
    ebay_negative_keywords: add 'transuranic Arquebus'
    Old: 'legions imperialis Resin 04-113'
    New: 'legions imperialis Resin 04-113 transuranic Arquebus'

  59-11  Adeptus Mechanicus Skitarii Vanguard
    ebay_negative_keywords: add 'Arc Rifle'
    Old: 'legions imperialis Resin 04-113'
    New: 'legions imperialis Resin 04-113 Arc Rifle'

  59-16  Adeptus Mechanicus Dunecrawler
    ebay_negative_keywords: add 'Neutron Laser'
    Old: 'legions imperialis Resin 04-113'
    New: 'legions imperialis Resin 04-113 Neutron Laser'

  59-18  Adeptus Mechanicus Kataphron Destroyers
    ebay_negative_keywords: add 'magazine issue'
    Old: 'legions imperialis Resin 04-113'
    New: 'legions imperialis Resin 04-113 magazine issue'

  MC-009 Adeptus Mechanicus Kataphron Breachers
    ebay_negative_keywords: add 'magazine issue'
    Old: '100th 1926 TShirt Plushie Plush legions imperialis Resin 04-113'
    New: '100th 1926 TShirt Plushie Plush legions imperialis Resin 04-113 magazine issue'

  MC-013 Adeptus Mechanicus Serberys Sulphurhounds
    ebay_negative_keywords: add 'Maul weapons'
    Old: '100th 1926 TShirt Plushie Plush legions imperialis Resin 04-113'
    New: '100th 1926 TShirt Plushie Plush legions imperialis Resin 04-113 Maul weapons'

  MC-016 Adeptus Mechanicus Skitarii Marshal
    ebay_allowed_title_words: set to 'new'
    Makes _allowed_words non-empty so the description-mirrors-title bot check is
    bypassed for this product. The £24.43 UK listing has a genuine description that
    happens to overlap heavily with the title keyword set; without this, it is
    incorrectly rejected as a bot storefront listing.
    Old: ''
    New: 'new'
"""

from django.core.management.base import BaseCommand

from products.models import Product


_KEYWORD_FIXES = [
    (
        '59-10',
        'Adeptus Mechanicus Skitarii Rangers',
        'legions imperialis Resin 04-113 transuranic Arquebus',
    ),
    (
        '59-11',
        'Adeptus Mechanicus Skitarii Vanguard',
        'legions imperialis Resin 04-113 Arc Rifle',
    ),
    (
        '59-16',
        'Adeptus Mechanicus Dunecrawler',
        'legions imperialis Resin 04-113 Neutron Laser',
    ),
    (
        '59-18',
        'Adeptus Mechanicus Kataphron Destroyers',
        'legions imperialis Resin 04-113 magazine issue',
    ),
    (
        'MC-009',
        'Adeptus Mechanicus Kataphron Breachers',
        '100th 1926 TShirt Plushie Plush legions imperialis Resin 04-113 magazine issue',
    ),
    (
        'MC-013',
        'Adeptus Mechanicus Serberys Sulphurhounds',
        '100th 1926 TShirt Plushie Plush legions imperialis Resin 04-113 Maul weapons',
    ),
]

_ALLOWED_TITLE_FIXES = [
    (
        'MC-016',
        'Adeptus Mechanicus Skitarii Marshal',
        'new',
    ),
]


class Command(BaseCommand):
    """Fix eBay keyword filters for six AdMech products; fix mirror-check for Skitarii Marshal."""

    help = (
        'Sets ebay_negative_keywords for 59-10/11/16/18, MC-009, MC-013 '
        'and ebay_allowed_title_words for MC-016. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        updated_total = 0

        for gw_sku, name, keywords in _KEYWORD_FIXES:
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

        for gw_sku, name, allowed_words in _ALLOWED_TITLE_FIXES:
            updated = Product.objects.filter(gw_sku=gw_sku).update(
                ebay_allowed_title_words=allowed_words,
            )
            if updated:
                self.stdout.write(
                    f'  Updated ebay_allowed_title_words: {name} ({gw_sku})'
                )
                updated_total += updated
            else:
                self.stdout.write(self.style.WARNING(
                    f'  Not found: {name} ({gw_sku}) -- skipped.'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'apply_batch_fixes_may2026q complete. {updated_total} product(s) updated.'
        ))
