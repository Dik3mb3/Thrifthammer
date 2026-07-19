"""
Management command: send_price_alerts

Checks every WatchlistItem that has email_alerts=True and a non-none alert_type.
Sends a styled HTML alert email when:
  - The alert condition is currently met, AND
  - The user has never been alerted for this item (last_alerted_at is None), OR
  - The last alert was sent 7+ days ago (weekly recurrence while condition remains)

This means:
  - First trigger → email sent immediately (within the next daily run)
  - Price stays at target for weeks → weekly reminder email
  - Price recovers then drops again → new immediate alert

Usage:
    python manage.py send_price_alerts          # production run
    python manage.py send_price_alerts --dry-run # log matches, send nothing
"""

import time
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.db import OperationalError, connection
from django.template.loader import render_to_string
from django.utils import timezone

from accounts.models import WatchlistItem

SITE_URL = 'https://thrifthammer.com'
ALERT_INTERVAL_DAYS = 7  # Re-alert weekly while condition remains met


class Command(BaseCommand):
    """Send HTML price-alert emails for watchlist items where the alert condition is met."""

    help = 'Send price-alert emails for watchlist items where the alert condition is met.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Log matches without sending emails or updating last_alerted_at.',
        )

    def _with_db_retry(self, operation):
        """
        Execute a single DB operation, recovering from a dropped connection.

        This command holds one DB connection open for its entire run and
        touches it on every watchlist item in the loop -- including the
        product price lookup, since the cache backend (DatabaseCache) is
        itself a Postgres table, so even a cache read is a DB query. That
        connection has been observed dying mid-run elsewhere in the same
        class of long-running command (psycopg2 "SSL SYSCALL error: EOF
        detected" / "server closed the connection unexpectedly") --
        without this, one dropped connection can crash the whole run or
        silently fail every remaining item. On OperationalError, close
        the stale connection so Django opens a fresh one, wait briefly,
        and retry once.

        Returns (result, True) on success, (None, False) if the retry
        also failed -- caller should skip and continue.
        """
        try:
            return operation(), True
        except OperationalError as exc:
            self.stderr.write(self.style.WARNING(
                f'  [db-retry] connection error, retrying: {exc}'
            ))
            connection.close()
            time.sleep(2)
            try:
                return operation(), True
            except OperationalError as exc2:
                self.stderr.write(self.style.ERROR(
                    f'  [db-error] failed after retry, skipping: {exc2}'
                ))
                return None, False

    def handle(self, *args, **options):
        """Main entry point — iterates candidates and dispatches alerts."""
        dry_run = options['dry_run']
        sent = skipped = errors = 0
        now = timezone.now()
        weekly_cutoff = now - timedelta(days=ALERT_INTERVAL_DAYS)

        candidates = (
            WatchlistItem.objects
            .exclude(alert_type=WatchlistItem.ALERT_NONE)
            .filter(email_alerts=True)
            .select_related('user', 'product', 'product__category')
            .prefetch_related('product__current_prices__retailer')
        )

        candidate_list, db_ok = self._with_db_retry(lambda: list(candidates))
        if not db_ok:
            self.stderr.write(self.style.ERROR('Could not load watchlist items — aborting.'))
            return

        for item in candidate_list:
            # Must have an email address on the account
            if not item.user.email:
                self.stdout.write(f'  [skip] {item} — no email on account')
                skipped += 1
                continue

            # Check alert condition against live best price
            best, db_ok = self._with_db_retry(item.product.get_cheapest_price)
            if not db_ok:
                errors += 1
                continue
            if not item.alert_condition_met(best):
                skipped += 1
                continue

            # Deduplication: skip if alerted within the last 7 days
            if item.last_alerted_at is not None and item.last_alerted_at >= weekly_cutoff:
                skipped += 1
                continue

            current_price = best.price

            if dry_run:
                self.stdout.write(
                    f'  [dry-run] Would alert {item.user.email} — '
                    f'{item.product.name} @ ${current_price}'
                )
                sent += 1
                continue

            try:
                self._send_alert(item, best, now)
                # Record timestamp so we don't re-alert for another 7 days
                item.last_alerted_at = now
                item.last_alerted_price = current_price  # keep for backwards compat
                _, db_ok = self._with_db_retry(
                    lambda: item.save(update_fields=['last_alerted_at', 'last_alerted_price'])
                )
                if not db_ok:
                    errors += 1
                    continue
                sent += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [sent] {item.user.email} — {item.product.name} @ ${current_price}'
                    )
                )
            except Exception as exc:
                self.stderr.write(f'  [error] {item} — {exc}')
                errors += 1

        self.stdout.write(
            f'\nDone — sent: {sent} | skipped: {skipped} | errors: {errors}'
            + (' (dry run)' if dry_run else '')
        )

    def _send_alert(self, item: WatchlistItem, best_price, now) -> None:
        """Compose and send the styled HTML alert email for one watchlist item."""
        product = item.product
        retailer = best_price.retailer if best_price else None
        price = best_price.price

        # Calculate % off for the email badge
        msrp = product.msrp
        pct_off = None
        if msrp and msrp > 0 and price is not None:
            raw_pct = float((msrp - price) / msrp * 100)
            pct_off = int(round(raw_pct)) if raw_pct > 0 else None

        # Unsubscribe URL via newsletter profile token
        unsubscribe_url = None
        try:
            from products.models import NewsletterSubscriber
            sub = NewsletterSubscriber.objects.filter(email=item.user.email).first()
            if sub:
                unsubscribe_url = sub.get_unsubscribe_url()
        except Exception:
            pass

        context = {
            'username': item.user.username,
            'product_name': product.name,
            'product_url': f'{SITE_URL}/products/{product.slug}/',
            'best_price': price,
            'msrp': msrp,
            'retailer_name': retailer.name if retailer else None,
            'pct_off': pct_off,
            'alert_type': item.alert_type,
            'target_price': item.target_price,
            'alert_percent': item.alert_percent,
            'site_url': SITE_URL,
            'browse_url': f'{SITE_URL}/products/',
            'watchlist_url': f'{SITE_URL}/accounts/watchlist/',
            'unsubscribe_url': unsubscribe_url,
            'now': now,
        }

        subject = f'ThriftHammer Alert — {product.name} hit your target'
        html_body = render_to_string('emails/price_alert.html', context)

        # Plain-text fallback
        lines = [
            f'Hi {item.user.username},',
            '',
            f'{product.name} just hit your watchlist target.',
            '',
            f'  Best Price : ${price}' + (f' at {retailer.name}' if retailer else ''),
        ]
        if msrp:
            lines.append(f'  GW MSRP   : ${msrp}')
        if pct_off:
            lines.append(f'  Savings   : {pct_off}% off MSRP')
        if item.alert_type == WatchlistItem.ALERT_PRICE and item.target_price:
            lines.append(f'  Your target: ${item.target_price}')
        elif item.alert_type == WatchlistItem.ALERT_PCT_OFF and item.alert_percent:
            lines.append(f'  Your target: {item.alert_percent}% off MSRP')
        lines += [
            '',
            f'  View product: {SITE_URL}/products/{product.slug}/',
            '',
            f'Manage your alerts: {SITE_URL}/accounts/watchlist/',
            '',
            'You will receive this alert weekly as long as the price stays at your target.',
            '',
            '— ThriftHammer',
        ]
        text_body = '\n'.join(lines)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[item.user.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
