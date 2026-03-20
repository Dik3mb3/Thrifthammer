"""
Management command: stamp_price_date
=====================================
Bulk-stamps all CurrentPrice.last_seen values to a target date and clears
the cached last-price-update value shown in the footer.

Useful when prices are updated manually (e.g. via an Excel import or
admin edits) and you want the footer timestamp to reflect that work.

Usage:
    python manage.py stamp_price_date 2026-03-17
    python manage.py stamp_price_date 2026-03-17 --dry-run
    python manage.py stamp_price_date 2026-03-17 --sku 48-75   # single product
"""

import datetime

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice


class Command(BaseCommand):
    """Stamp CurrentPrice.last_seen to a given date and clear the footer cache."""

    help = "Set all (or one) CurrentPrice.last_seen to a specified date."

    def add_arguments(self, parser):
        parser.add_argument(
            "date",
            type=str,
            help="Target date in YYYY-MM-DD format (e.g. 2026-03-17).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would happen without changing the database.",
        )
        parser.add_argument(
            "--sku",
            type=str,
            default="",
            help="Limit update to a single product by GW SKU.",
        )

    def handle(self, *args, **options):
        raw_date = options["date"]
        dry_run = options["dry_run"]
        sku_filter = options["sku"].strip()

        try:
            target_date = datetime.date.fromisoformat(raw_date)
        except ValueError:
            raise CommandError(f"Invalid date '{raw_date}'. Use YYYY-MM-DD.")

        target_dt = datetime.datetime(
            target_date.year, target_date.month, target_date.day,
            12, 0, 0,
            tzinfo=datetime.timezone.utc,
        )

        qs = CurrentPrice.objects.all()
        if sku_filter:
            qs = qs.filter(product__gw_sku=sku_filter)

        count = qs.count()

        if dry_run:
            self.stdout.write(
                f"[DRY-RUN] Would stamp {count} CurrentPrice row(s) "
                f"→ last_seen = {target_dt.date()}"
            )
            return

        # bulk update bypasses auto_now — intentional
        updated = qs.update(last_seen=target_dt)

        # Clear the 15-min footer cache so the new date shows immediately
        cache.delete("site_last_price_update")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — updated {updated} CurrentPrice row(s) "
                f"to last_seen = {target_dt.date()}.  Cache cleared."
            )
        )
