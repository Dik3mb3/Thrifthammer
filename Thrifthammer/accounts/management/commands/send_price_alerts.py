"""
Management command: send_price_alerts

Checks every WatchlistItem that has email_alerts=True and a non-none alert_type.
When the alert condition is met and the user has an email address, sends a
notification — but only if the current price has moved since the last alert
(tracked via last_alerted_price) to prevent spam.

Usage:
    python manage.py send_price_alerts          # production run
    python manage.py send_price_alerts --dry-run # log matches, send nothing
"""

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from accounts.models import WatchlistItem


class Command(BaseCommand):
    """Sends email alerts for watchlist items whose price condition is now met."""

    help = 'Send price-alert emails for watchlist items where the alert condition is met.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Log matches without sending emails or updating last_alerted_price.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        sent = skipped = errors = 0

        candidates = (
            WatchlistItem.objects
            .exclude(alert_type=WatchlistItem.ALERT_NONE)
            .filter(email_alerts=True)
            .select_related('user', 'product', 'product__category')
            .prefetch_related('product__current_prices__retailer')
        )

        for item in candidates:
            if not item.user.email:
                self.stdout.write(f'  [skip] {item} — no email on account')
                skipped += 1
                continue

            best = item.product.get_cheapest_price()
            if not item.alert_condition_met(best):
                skipped += 1
                continue

            current_price = best.price
            # Only alert if the price has improved since we last alerted
            if item.last_alerted_price is not None and current_price >= item.last_alerted_price:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    f'  [dry-run] Would alert {item.user.email} — '
                    f'{item.product.name} @ £{current_price}'
                )
                sent += 1
                continue

            try:
                self._send_alert(item, best)
                item.last_alerted_price = current_price
                item.save(update_fields=['last_alerted_price'])
                sent += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  [sent] {item.user.email} — {item.product.name} @ £{current_price}')
                )
            except Exception as exc:
                self.stderr.write(f'  [error] {item} — {exc}')
                errors += 1

        self.stdout.write(
            f'\nDone — sent: {sent} | skipped: {skipped} | errors: {errors}'
            + (' (dry run)' if dry_run else '')
        )

    def _send_alert(self, item: WatchlistItem, best_price) -> None:
        """Compose and send the alert email for one watchlist item."""
        product = item.product
        retailer = best_price.retailer if best_price else None
        alert_label = dict(WatchlistItem.ALERT_TYPE_CHOICES).get(item.alert_type, item.alert_type)

        subject = f'ThriftHammer Price Alert — {product.name}'

        body_lines = [
            f'Hi {item.user.username},',
            '',
            f'Good news! A price alert has triggered for a product on your ThriftHammer watchlist.',
            '',
            f'  Product : {product.name}',
            f'  Price   : £{best_price.price}' + (f' at {retailer.name}' if retailer else ''),
        ]
        if item.alert_type == WatchlistItem.ALERT_PRICE and item.target_price:
            body_lines.append(f'  Target  : £{item.target_price}')
        elif item.alert_type == WatchlistItem.ALERT_PCT_OFF and item.alert_percent:
            body_lines.append(f'  Alert   : {item.alert_percent}% off MSRP')
        elif item.alert_type == WatchlistItem.ALERT_SITE_LOW:
            body_lines.append(f'  Alert   : Website low price reached')

        body_lines += [
            '',
            f'  View product: https://www.thrifthammer.com/products/{product.slug}/',
            '',
            'You can manage your watchlist alerts at:',
            '  https://www.thrifthammer.com/accounts/watchlist/',
            '',
            '— ThriftHammer',
            'Stop overpaying for plastic.',
        ]

        send_mail(
            subject=subject,
            message='\n'.join(body_lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[item.user.email],
            fail_silently=False,
        )
