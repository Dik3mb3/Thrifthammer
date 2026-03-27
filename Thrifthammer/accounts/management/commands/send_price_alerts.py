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

from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
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

        for item in candidates:
            # Must have an email address on the account
            if not item.user.email:
                self.stdout.write(f'  [skip] {item} — no email on account')
                skipped += 1
                continue

            # Check alert condition against live best price
            best = item.product.get_cheapest_price()
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
                item.save(update_fields=['last_alerted_at', 'last_alerted_price'])
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
