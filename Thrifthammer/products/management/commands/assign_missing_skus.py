"""
Management command: assign_missing_skus

Assigns internal SKU codes to Products that have an empty gw_sku field.
Codes follow the existing XX-YY format and are used purely for internal
matching and price-scraping — they are NOT necessarily real GW product codes.

Idempotent: products that already have a gw_sku are never touched.

Usage:
    python manage.py assign_missing_skus           # dry-run (default)
    python manage.py assign_missing_skus --execute  # write to DB
"""

import re

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Product

# Faction name → SKU prefix integer.
# Existing prefixes match what is already established in the DB.
# New prefixes (Black Templars, etc.) use unused ranges.
FACTION_PREFIX = {
    # ── Existing prefixes ─────────────────────────────────────────────────────
    'Space Marines (Warhammer 40,000)': 48,
    'Space Marines':                    48,
    'Blood Angels':                     41,
    'Dark Angels':                      44,
    'Grey Knights':                     57,
    'Space Wolves':                     53,
    'Ultramarines':                     55,
    'Orks':                             50,
    'Aeldari':                          46,
    'Necrons':                          49,
    # ── New prefixes for factions not yet in the DB ───────────────────────────
    'Black Templars':                   58,
    "Emperor's Children":               65,
    'Imperial Fists':                   60,
    'Iron Hands':                       61,
    'Raven Guard':                      62,
    'Salamanders':                      63,
    'White Scars':                      64,
    # Fallback for products with no faction assigned
    None:                               80,
}


class Command(BaseCommand):
    """Assign internal SKU codes to products that have an empty gw_sku."""

    help = 'Assign internal SKU codes to products missing a gw_sku value.'

    def add_arguments(self, parser):
        """Register CLI arguments."""
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Write SKUs to the database (default is dry-run, no writes).',
        )

    def handle(self, *args, **options):
        """Build next-available SKU map, assign codes, optionally save."""
        execute = options['execute']

        # ── Build map of used numbers per prefix ──────────────────────────────
        used: dict[int, set[int]] = {}
        for sku in Product.objects.exclude(gw_sku='').values_list('gw_sku', flat=True):
            m = re.match(r'^(\d+)-(\d+)$', sku)
            if m:
                prefix = int(m.group(1))
                num = int(m.group(2))
                used.setdefault(prefix, set()).add(num)

        # ── Helper: next available number for a prefix ────────────────────────
        def next_for(prefix: int) -> int:
            """Return the smallest unused number ≥ 1 for this prefix."""
            occupied = used.get(prefix, set())
            candidate = (max(occupied) + 1) if occupied else 1
            while candidate in occupied:
                candidate += 1
            return candidate

        # ── Process missing products ──────────────────────────────────────────
        missing_qs = (
            Product.objects
            .filter(gw_sku='')
            .select_related('faction')
            .order_by('faction__name', 'name')
        )

        if not missing_qs.exists():
            self.stdout.write(self.style.SUCCESS('No products are missing a gw_sku — nothing to do.'))
            return

        assignments: list[tuple[Product, str]] = []

        for product in missing_qs:
            faction_name = product.faction.name if product.faction else None
            prefix = FACTION_PREFIX.get(faction_name, 80)

            num = next_for(prefix)
            sku = f'{prefix:02d}-{num:02d}'

            # Reserve this number so the next product in the same prefix gets a
            # different one (we haven't written to the DB yet in dry-run mode).
            used.setdefault(prefix, set()).add(num)

            assignments.append((product, sku))

            mode = 'ASSIGN' if execute else 'DRY-RUN'
            faction_label = faction_name or '(no faction)'
            self.stdout.write(
                f'  [{mode}] {product.name!r:55} [{faction_label}]  ->  {sku}'
            )

        # ── Write if --execute ────────────────────────────────────────────────
        if execute:
            with transaction.atomic():
                for product, sku in assignments:
                    product.gw_sku = sku
                    product.save(update_fields=['gw_sku', 'updated_at'])
            self.stdout.write(
                self.style.SUCCESS(f'\nDone — assigned {len(assignments)} SKUs.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDry-run complete — {len(assignments)} SKUs would be assigned. '
                    f'Pass --execute to write to the database.'
                )
            )
