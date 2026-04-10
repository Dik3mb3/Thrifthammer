"""
Management command: send_issue_reports

Emails a digest of unnotified issue reports to ISSUE_REPORT_EMAIL.
Marks each report as emailed so it is not included in future digests.

Runs daily via GitHub Actions at 08:00 UTC (after all scrapers finish).

Usage:
    python manage.py send_issue_reports          # production run
    python manage.py send_issue_reports --dry-run # log only, no email or DB update
"""

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from products.models import IssueReport


class Command(BaseCommand):
    """Email a digest of new issue reports, then mark them as sent."""

    help = 'Email a digest of unnotified issue reports to the site owner.'

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Log reports without sending email or updating emailed_at.',
        )

    def handle(self, *args, **options):
        """Fetch unsent reports, compose digest, send, mark as emailed."""
        dry_run = options['dry_run']

        reports = (
            IssueReport.objects
            .filter(emailed_at__isnull=True)
            .select_related('product')
            .order_by('created_at')
        )

        if not reports.exists():
            self.stdout.write('No new issue reports to send.')
            return

        count = reports.count()
        self.stdout.write(f'Found {count} new issue report(s).')

        lines = [f'You have {count} new issue report(s) on ThriftHammer:\n']
        for report in reports:
            lines.append(f'--- {report.created_at:%Y-%m-%d %H:%M UTC} ---')
            lines.append(f'Product : {report.product.name} (SKU: {report.product.gw_sku})')
            lines.append(
                f'Page    : https://www.thrifthammer.com/products/{report.product.slug}/'
            )
            lines.append(f'Issue   : {report.issue_type}')
            lines.append(f'Details : {report.description}')
            reporter = report.contact_email or 'Anonymous'
            lines.append(f'Reporter: {reporter}')
            lines.append('')

        body = '\n'.join(lines)

        if dry_run:
            self.stdout.write('\n--- DRY RUN: email not sent ---\n')
            self.stdout.write(body)
            return

        try:
            send_mail(
                subject=f'[ThriftHammer] {count} New Issue Report(s)',
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ISSUE_REPORT_EMAIL],
                fail_silently=False,
            )
            now = timezone.now()
            reports.update(emailed_at=now)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Digest sent — {count} report(s) marked as emailed.'
                )
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Failed to send digest: {exc}'))
            raise
