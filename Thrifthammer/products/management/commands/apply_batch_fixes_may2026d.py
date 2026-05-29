"""
Management command: apply_batch_fixes_may2026d

Sets ebay_negative_keywords and ebay_search_name on specific products using
targeted SQL UPDATE — never update_or_create, never touches any other field.

Products covered:
  55-23  Black Templars Sword Brethren   ebay_negative_keywords  x1
  50-09  Ork Nobz                        ebay_negative_keywords  Nob Bosspole Eavy Choppa Grenades Space
  CSM-025 Traitor Guardsmen Squad        ebay_negative_keywords  [new]
  47-12  Astra Militarum Sentinel        ebay_negative_keywords  h /
  53-21  Arjac Rockfist                  ebay_negative_keywords  NIB
  TY-011 Tyranid Hive Guard             ebay_search_name        Tyranids Hive Guard

Notes:
  - 55-23, 50-09, CSM-025, 47-12 are seeded by populate_products.py which does
    not run on Railway — these fields were empty in production before this fix.
  - 47-12 "/" was previously in populate_products.py _EBAY_NEGATIVE_KEYWORDS
    but never reached Railway. Included here alongside the new "h" keyword.
  - 53-21 (Arjac) and TY-011 (Hive Guard) have faction-specific populate
    commands in the Procfile but those commands do not set these fields.
  - "Eavy Choppa" is stored as two separate space-separated exclusion words
    since ebay_negative_keywords uses single-word -term eBay syntax.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

# ebay_negative_keywords: complete desired keyword string per SKU.
# Space-separated; each word is prepended with - in the eBay query.
_NEGATIVE_KEYWORDS = {
    # 55-23 "Black Templars Sword Brethren" — exclude x1 single-model listings.
    '55-23': 'x1',
    # 50-09 "Ork Nobz" — exclude accessory/bitz/single-model/cross-faction listings.
    # "Eavy" and "Choppa" stored as separate words (field uses single-word syntax).
    '50-09': 'Nob Bosspole Eavy Choppa Grenades Space',
    # CSM-025 "Traitor Guardsmen Squad" — exclude listings tagged [new] condition.
    'CSM-025': '[new]',
    # 47-12 "Astra Militarum Sentinel" — exclude multi-kit bundle listings that
    # use "/" as a separator (e.g. "Sentinel / Chimera") and single-letter spam.
    '47-12': 'h /',
    # 53-21 "Arjac Rockfist" — exclude NIB (New In Box) premium-priced resale.
    '53-21': 'NIB',
}

# ebay_search_name: replaces the product name in the eBay search query.
_SEARCH_NAMES = {
    # TY-011 "Tyranid Hive Guard" — eBay sellers consistently use plural prefix
    # "Tyranids Hive Guard". Previously in populate_products.py _EBAY_SEARCH_OVERRIDES
    # but that command does not run on Railway.
    'TY-011': 'Tyranids Hive Guard',
}


class Command(BaseCommand):
    """Apply May 2026 batch-d eBay keyword and search name fixes."""

    help = (
        'Sets ebay_negative_keywords and ebay_search_name on 6 products via '
        'targeted .update(). Does not create products or touch any other fields.'
    )

    def handle(self, *args, **options):
        """Apply all keyword and search name fixes."""
        kw_ok = kw_skip = 0
        sn_ok = sn_skip = 0

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\napply_batch_fixes_may2026d — ebay_negative_keywords'
        ))
        for sku, keywords in _NEGATIVE_KEYWORDS.items():
            updated = Product.objects.filter(gw_sku=sku).update(
                ebay_negative_keywords=keywords,
            )
            if updated:
                self.stdout.write(
                    self.style.SUCCESS(f'  [ok]   {sku} → "{keywords}"')
                )
                kw_ok += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'  [skip] {sku} — not found in DB')
                )
                kw_skip += 1

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\napply_batch_fixes_may2026d — ebay_search_name'
        ))
        for sku, name in _SEARCH_NAMES.items():
            updated = Product.objects.filter(gw_sku=sku).update(
                ebay_search_name=name,
            )
            if updated:
                self.stdout.write(
                    self.style.SUCCESS(f'  [ok]   {sku} → "{name}"')
                )
                sn_ok += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'  [skip] {sku} — not found in DB')
                )
                sn_skip += 1

        self.stdout.write(
            f'\nDone — ebay_negative_keywords: {kw_ok} updated, {kw_skip} skipped'
            f' | ebay_search_name: {sn_ok} updated, {sn_skip} skipped.'
        )
