"""
Management command: apply_batch_fixes_may2026l

Noble Knight listings for Manticore and Deathstrike are dead (same kit,
one NK listing that no longer exists). Cleans up both records.

Changes:
  AM-033   Astra Militarum Manticore — Noble Knight
           url: 'https://www.nobleknight.com/P/2148431611/Manticore-5?awid=1576' → ''
           not_available: False → True

  AM-020   Astra Militarum Deathstrike — Noble Knight
           url: 'https://www.nobleknight.com/P/2148431611/Manticore-5?awid=1576' → ''
           price: 34.95 → None
           in_stock: True → False
           not_available: False → True

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice


class Command(BaseCommand):
    """Apply batch fixes may2026l — clean up dead Noble Knight records for Manticore and Deathstrike."""

    help = 'Clear dead Noble Knight URLs and prices for Manticore and Deathstrike.'

    def handle(self, *args, **options):
        """Run all fixes."""
        # ── Manticore — remove dead URL, mark not_available ───────────────────
        updated = CurrentPrice.objects.filter(
            product__gw_sku='AM-033',
            retailer__slug='noble-knight-games',
        ).update(
            url='',
            not_available=True,
        )
        self.stdout.write(f'Manticore NK: {updated} record(s) updated.')

        # ── Deathstrike — remove dead URL, clear stale price, mark not_available
        updated = CurrentPrice.objects.filter(
            product__gw_sku='AM-020',
            retailer__slug='noble-knight-games',
        ).update(
            url='',
            price=None,
            in_stock=False,
            not_available=True,
        )
        self.stdout.write(f'Deathstrike NK: {updated} record(s) updated.')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_may2026l complete.'))
