"""
Management command: apply_batch_fixes_apr2026f

Necron eBay search-name corrections + Seraptek deactivation.

Fix 1 — necron-trazyn-the-infinite
  Change ebay_search_name → 'trazyn the infinite necron'
  (previous name had extra words blocking the correct listing)

Fix 2 — necron-nekrosor-ammentar
  Change ebay_search_name → 'Nekrosor Ammentar'
  (simpler query matches the single known listing)

Fix 3 — necron-night-scythe
  Change ebay_search_name → 'night scythe necron'
  (doom-scythe variant already works; night scythe needs necron qualifier)

Fix 4 — necron-obelisk
  Change ebay_search_name → 'Obelisk Transcendent Ctan necron'
  (dual-kit listing titled "Obelisk & Transcendent C'tan")

Fix 5 — necron-tesseract-vault
  Change ebay_search_name → 'Obelisk Transcendent Ctan necron'
  (same dual-kit listing as the Obelisk — user confirmed shared search)

Fix 6 — necron-seraptek-heavy-construct
  Set is_active=False — product removed from GW line, no eBay listing exists.
  (user: "Please delete this SKU from our database")

Fix 7 — necron-ctan-shard-of-the-deceiver
  Change ebay_search_name → "C'tan Shard of The Deceiver Necron"
  (previous name was too abbreviated; full title matches the listing)

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Product

SEARCH_NAME_FIXES = [
    ('necron-trazyn-the-infinite',       'trazyn the infinite necron'),
    ('necron-nekrosor-ammentar',         'Nekrosor Ammentar'),
    ('necron-night-scythe',              'night scythe necron'),
    ('necron-obelisk',                   'Obelisk Transcendent Ctan necron'),
    ('necron-tesseract-vault',           'Obelisk Transcendent Ctan necron'),
    ('necron-ctan-shard-of-the-deceiver', "C'tan Shard of The Deceiver Necron"),
]

DEACTIVATE_SLUG = 'necron-seraptek-heavy-construct'


class Command(BaseCommand):
    """Fix Necron eBay search names and deactivate Seraptek Heavy Construct."""

    help = (
        'Corrects ebay_search_name on 6 Necron products so eBay Browse API finds '
        'the correct listings, and deactivates the Seraptek Heavy Construct '
        '(no longer available). Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n  ── Fix 1–6: Necron eBay search-name corrections ──'
        ))

        for slug, new_name in SEARCH_NAME_FIXES:
            product = Product.objects.filter(slug=slug).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  [skip] {slug} — not found'))
                continue
            if product.ebay_search_name == new_name:
                self.stdout.write(f'  [no-op] {product.name} — already set to "{new_name}"')
                continue
            old_name = product.ebay_search_name
            product.ebay_search_name = new_name
            product.save(update_fields=['ebay_search_name'])
            self.stdout.write(self.style.SUCCESS(
                f'  Updated: {product.name}\n'
                f'    "{old_name}" → "{new_name}"'
            ))

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n  ── Fix 7: Deactivate Seraptek Heavy Construct ──'
        ))
        seraptek = Product.objects.filter(slug=DEACTIVATE_SLUG).first()
        if not seraptek:
            self.stdout.write(self.style.WARNING(f'  [skip] {DEACTIVATE_SLUG} — not found'))
        elif not seraptek.is_active:
            self.stdout.write(f'  [no-op] {seraptek.name} — already inactive')
        else:
            seraptek.is_active = False
            seraptek.save(update_fields=['is_active'])
            self.stdout.write(self.style.SUCCESS(
                f'  Deactivated: {seraptek.name}'
            ))

        self.stdout.write(self.style.SUCCESS('\napply_batch_fixes_apr2026f complete.'))
