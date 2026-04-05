"""
Management command: apply_batch_fixes_apr2026c

Third wave of April 2026 batch corrections for ThriftHammer.

Changes covered:
  Fix 1  -- Space Marine Whirlwind (space-marine-whirlwind)
             Add 'legions imperialis scorpus' to ebay_negative_keywords.

             Root cause: eBay search 'whirlwind 40k' was returning the
             Legions Imperialis 'Whirlwind and Scorpus Missile Tank' set
             at $45.25 (Epic/8mm scale miniatures) instead of the correct
             28mm Space Marine Whirlwind kit (~$66.60).
             The LI set passes all existing title-keyword checks because
             it contains '40k' in the listing title. Adding 'legions',
             'imperialis', and 'scorpus' as negative keywords blocks the
             LI set and allows the correct listing to be returned on the
             next update_ebay_prices cron run.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

# (slug, new_ebay_negative_keywords)  — full replacement value, not append
NEGATIVE_KEYWORD_FIXES = [
    (
        'space-marine-whirlwind',
        '1999 vintage legions imperialis scorpus',
    ),
]


class Command(BaseCommand):
    """Apply April 2026 wave-3 fix: block Legions Imperialis from Whirlwind eBay search."""

    help = (
        'Adds "legions imperialis scorpus" to Whirlwind ebay_negative_keywords to prevent '
        'the Legions Imperialis Whirlwind/Scorpus set from matching the 28mm kit search. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Apply all fixes in this wave."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n  ── eBay negative keyword fixes ──'))

        for slug, new_keywords in NEGATIVE_KEYWORD_FIXES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  [skip] Not found: {slug}'))
                continue

            if product.ebay_negative_keywords == new_keywords:
                self.stdout.write(f'  [no-op] {product.name} — already set')
                continue

            old = product.ebay_negative_keywords or '(empty)'
            product.ebay_negative_keywords = new_keywords
            product.save(update_fields=['ebay_negative_keywords'])
            self.stdout.write(self.style.SUCCESS(
                f'  Updated: {product.name}\n'
                f'    old: "{old}"\n'
                f'    new: "{new_keywords}"'
            ))

        self.stdout.write(self.style.SUCCESS('\napply_batch_fixes_apr2026c complete.'))
