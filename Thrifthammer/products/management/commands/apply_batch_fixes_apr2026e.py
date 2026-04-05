"""
Management command: apply_batch_fixes_apr2026e

Two fixes:

Fix 1 — Stormcast Eternals Liberators (stormcast-eternals-liberators)
  Add 'x5' to ebay_negative_keywords to prevent 5-model "x5" bulk
  listings from matching searches for the standard box.

Fix 2 — All Codex products (any product whose name starts with "Codex")
  Add old-edition edition markers as negative keywords:
  '3rd 4th 5th 6th 7th 8th 9th'
  This prevents outdated rulebook editions from appearing in eBay
  price results when searching for the current edition codex.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

OLD_EDITIONS = '3rd 4th 5th 6th 7th 8th 9th'


def _append_keywords(product, new_words):
    """
    Append new_words to product.ebay_negative_keywords, avoiding duplicates.

    Only adds words not already present (case-insensitive check).
    Returns True if the field was modified.
    """
    existing = (product.ebay_negative_keywords or '').strip()
    existing_lower = existing.lower()
    to_add = [w for w in new_words.split() if w.lower() not in existing_lower]
    if not to_add:
        return False
    addition = ' '.join(to_add)
    product.ebay_negative_keywords = f'{existing} {addition}'.strip() if existing else addition
    return True


class Command(BaseCommand):
    """Apply April 2026 wave-5 fixes: Liberators x5 + Codex old-edition negatives."""

    help = (
        'Adds "x5" to Stormcast Liberators negative keywords, and adds old-edition '
        'markers (3rd–9th) to all Codex products to block outdated rulebooks. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        self.stdout.write(self.style.MIGRATE_HEADING('\n  ── Fix 1: Liberators x5 ──'))
        liberators = Product.objects.filter(slug='stormcast-eternals-liberators').first()
        if not liberators:
            self.stdout.write(self.style.WARNING('  [skip] stormcast-eternals-liberators not found'))
        elif _append_keywords(liberators, 'x5'):
            liberators.save(update_fields=['ebay_negative_keywords'])
            self.stdout.write(self.style.SUCCESS(
                f'  Updated: {liberators.name} → "{liberators.ebay_negative_keywords}"'
            ))
        else:
            self.stdout.write(f'  [no-op] {liberators.name} — already has "x5"')

        self.stdout.write(self.style.MIGRATE_HEADING('\n  ── Fix 2: Codex old-edition negatives ──'))
        codex_products = Product.objects.filter(
            name__istartswith='codex', is_active=True
        )
        updated_count = 0
        skipped_count = 0
        for product in codex_products:
            if _append_keywords(product, OLD_EDITIONS):
                product.save(update_fields=['ebay_negative_keywords'])
                self.stdout.write(self.style.SUCCESS(
                    f'  Updated: {product.name} → "{product.ebay_negative_keywords}"'
                ))
                updated_count += 1
            else:
                self.stdout.write(f'  [no-op] {product.name} — already set')
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\napply_batch_fixes_apr2026e complete.\n'
            f'  Codex products updated: {updated_count}, skipped: {skipped_count}'
        ))
