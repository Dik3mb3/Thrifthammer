"""
Management command: send_admin_newsletter

Sends a one-off admin broadcast to all confirmed newsletter subscribers.

Usage:
    python manage.py send_admin_newsletter \\
        --subject "Big news from ThriftHammer" \\
        --body "We have just launched a new feature..."
    python manage.py send_admin_newsletter --dry-run --subject "Test" --body "Hello"
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from products.models import NewsletterSignup


class Command(BaseCommand):
    """Send a one-off admin broadcast to all confirmed newsletter subscribers."""

    help = 'Broadcast an admin message to all confirmed newsletter subscribers.'

    def add_arguments(self, parser):
        """Add --subject, --body, --dry-run, and --recipient flags."""
        parser.add_argument(
            '--subject',
            type=str,
            required=True,
            help='Email subject line.',
        )
        parser.add_argument(
            '--body',
            type=str,
            required=True,
            help='Plain-text body of the email. HTML will be auto-generated from this.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending emails.',
        )
        parser.add_argument(
            '--recipient',
            type=str,
            default=None,
            help='Send only to this address instead of all subscribers (for testing).',
        )

    def handle(self, *args, **options):
        """Main entry point — build and send the admin broadcast."""
        subject = options['subject']
        body = options['body']
        dry_run = options['dry_run']
        recipient_override = options['recipient']

        # ── 1. Gather subscribers ─────────────────────────────────────────────
        if recipient_override:
            class _Stub:
                email = recipient_override
                def get_unsubscribe_url(self):
                    return 'https://thrifthammer.com/products/newsletter/unsubscribe/test/'
            subscribers = [_Stub()]
            self.stdout.write(f'TEST MODE — sending only to: {recipient_override}')
        else:
            subscribers = list(NewsletterSignup.objects.filter(is_confirmed=True))
            if not subscribers:
                self.stdout.write(self.style.WARNING('No confirmed subscribers — nothing to send.'))
                return
            self.stdout.write(f'{len(subscribers)} confirmed subscriber(s).')

        self.stdout.write(f'Subject: {subject}')
        self.stdout.write(f'Body preview: {body[:80]}...' if len(body) > 80 else f'Body: {body}')

        if dry_run:
            for sub in subscribers:
                self.stdout.write(f'  [dry-run] Would send to: {sub.email}')
            self.stdout.write('\nDry run complete — no emails sent.')
            return

        # ── 2. Send ───────────────────────────────────────────────────────────
        sent = errors = 0
        for sub in subscribers:
            try:
                context = {
                    'subject': subject,
                    'body_text': body,
                    'site_url': 'https://thrifthammer.com',
                    'unsubscribe_url': sub.get_unsubscribe_url(),
                }
                html_body = render_to_string('emails/admin_newsletter.html', context)
                text_body = self._build_text_body(subject, body, sub.get_unsubscribe_url())

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[sub.email],
                )
                msg.attach_alternative(html_body, 'text/html')
                msg.send(fail_silently=False)
                sent += 1
                self.stdout.write(self.style.SUCCESS(f'  [sent] {sub.email}'))
            except Exception as exc:
                errors += 1
                self.stderr.write(f'  [error] {sub.email} — {exc}')

        self.stdout.write(f'\nDone -- sent: {sent} | errors: {errors}')

        if errors and not sent:
            raise Exception(
                f'All {errors} email(s) failed to send. '
                'Check EMAIL_HOST_USER / EMAIL_HOST_PASSWORD secrets.'
            )

    def _build_text_body(self, subject, body, unsubscribe_url):
        """Build a plain-text fallback email body."""
        lines = [
            'THRIFTHAMMER',
            'https://thrifthammer.com',
            '',
            subject,
            '=' * len(subject),
            '',
            body,
            '',
            '-' * 60,
            "You're receiving this because you signed up at thrifthammer.com.",
            '-- ThriftHammer',
            '',
            f'Unsubscribe: {unsubscribe_url}',
        ]
        return '\n'.join(lines)
