"""
Management command: review_sunday_faction_deals_uk

UK mirror of review_sunday_faction_deals. Read-only reporting tool -- NOT part
of the real UK Sunday send and never touches real subscribers. Loops through
every confirmed UK sunday_faction subscriber exactly as the real send does,
computes each one's personalized GBP deal list using the same deal-selection
logic the real send uses, and merges the results into a single deduplicated
union: every unique product that would appear in ANY UK subscriber's digest
this week, with how many subscribers would see it and which faction it
belongs to.

That consolidated list is emailed to the admin only, so the full real-world
content can be reviewed before deciding to trigger the real send
(python manage.py send_sunday_faction_deals_uk).

Reuses send_sunday_faction_deals_uk.Command._get_faction_deals() by importing
the real command and calling its method directly, rather than duplicating
the query -- this review can never drift from what the real send actually
computes.

The admin recipient is the single hardcoded address in
review_sunday_faction_deals, imported below, with no --recipient argument or
other override. This command must never be able to email anyone but the
admin, by construction, not just by default.

Usage:
    python manage.py review_sunday_faction_deals_uk
    python manage.py review_sunday_faction_deals_uk --limit 15
"""

import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from products.management.commands.review_sunday_faction_deals import _ADMIN_EMAIL
from products.management.commands.send_sunday_faction_deals_uk import (
    CURRENCY_SYMBOL,
    Command as SundayFactionDealsUKCommand,
)
from products.models import NewsletterSignup


class Command(BaseCommand):
    """Email the admin a deduplicated union of every UK Sunday subscriber's deals."""

    help = (
        "Read-only: email the admin a deduplicated union of every unique "
        "deal that would appear in ANY confirmed UK Sunday-faction "
        "subscriber's personalized digest this week. Sends nothing to real "
        "subscribers."
    )

    def add_arguments(self, parser):
        """Add --limit, matching the real send's per-subscriber deal cap."""
        parser.add_argument(
            '--limit', type=int, default=10,
            help='Deals per subscriber to consider, same default as the real send (default: 10).',
        )

    def handle(self, *args, **options):
        """Build the union across all real UK subscribers and email it to the admin."""
        limit = options['limit']
        today = datetime.date.today()

        subscribers = list(
            NewsletterSignup.objects
            .filter(
                is_confirmed=True,
                sunday_faction=True,
                region=NewsletterSignup.REGION_UK,
            )
            .prefetch_related('factions')
        )
        if not subscribers:
            self.stdout.write(self.style.WARNING(
                'No confirmed UK Sunday faction subscribers -- nothing to review.'
            ))
            return

        self.stdout.write(f'{len(subscribers)} confirmed UK Sunday subscriber(s) to check.\n')
        union, skipped_no_factions, skipped_no_deals = self._build_union(subscribers, limit)
        self.stdout.write(
            f'Subscribers checked: {len(subscribers)} | '
            f'skipped (no factions selected): {skipped_no_factions} | '
            f'skipped (no deals found): {skipped_no_deals}\n'
        )

        if not union:
            self.stdout.write(self.style.WARNING(
                'No deals found across any UK subscriber -- nothing to send.'
            ))
            return

        deals_list = sorted(union.values(), key=lambda d: d['pct_off'], reverse=True)
        self._print_deals(deals_list)
        self._email_admin(deals_list, len(subscribers), today)

    def _build_union(self, subscribers, limit):
        """Return (union, skipped_no_factions, skipped_no_deals) for the subscribers."""
        # Reuse the real send command's own deal-selection method so this
        # review can never compute something different from the real send.
        deal_source = SundayFactionDealsUKCommand()

        union = {}  # product slug -> deal dict (+ subscriber_count)
        skipped_no_factions = 0
        skipped_no_deals = 0

        for sub in subscribers:
            faction_list = list(sub.factions.all())
            if not faction_list:
                skipped_no_factions += 1
                continue

            deals = deal_source._get_faction_deals(faction_list, limit)
            if not deals:
                skipped_no_deals += 1
                continue

            for d in deals:
                slug = d['slug']
                if slug not in union:
                    union[slug] = dict(d)
                    union[slug]['group_label'] = d.get('faction', '')
                    union[slug]['subscriber_count'] = 0
                union[slug]['subscriber_count'] += 1

        return union, skipped_no_factions, skipped_no_deals

    def _print_deals(self, deals_list):
        """Write the unique deals to stdout, best discount first."""
        self.stdout.write(f'{len(deals_list)} unique deal(s) across all UK Sunday subscribers:')
        for i, d in enumerate(deals_list, 1):
            self.stdout.write(
                f'  {i:>3}. {d["name"]:45.45s} {d["group_label"]:22.22s} '
                f'{CURRENCY_SYMBOL}{d["price"]:.2f} (save {d["pct_off"]:.0f}%) '
                f'-- {d["subscriber_count"]} subscriber(s)'
            )

    def _email_admin(self, deals_list, subscriber_count, today):
        """Send the consolidated review email to the admin address only."""
        subject = (
            f"[ADMIN REVIEW] UK Sunday Faction Digest -- {len(deals_list)} Unique Deals "
            f"Across {subscriber_count} Subscriber(s) ({today.strftime('%b')} {today.day})"
        )
        context = {
            'deals': deals_list,
            'today': today,
            'subscriber_count': subscriber_count,
            'digest_label': 'UK Sunday Faction',
            'currency_symbol': CURRENCY_SYMBOL,
        }
        html_body = render_to_string('emails/review_personalized_digest.html', context)
        text_body = self._build_text_body(deals_list, today, subscriber_count)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[_ADMIN_EMAIL],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)

        self.stdout.write(self.style.SUCCESS(
            f'\n[sent] Review digest emailed to admin only: {_ADMIN_EMAIL}'
        ))

    def _build_text_body(self, deals, today, subscriber_count):
        """Build a clean plain-text fallback email body."""
        lines = [
            'THRIFTHAMMER -- ADMIN REVIEW: UK SUNDAY FACTION DIGEST',
            '(Not sent to subscribers -- admin review only)',
            f'{today.strftime("%B")} {today.day}, {today.year}',
            f'{len(deals)} unique deal(s) across {subscriber_count} confirmed UK subscriber(s)',
            '',
        ]
        for i, d in enumerate(deals, 1):
            lines.append(f'{i:>3}. {d["name"]}  [{d["group_label"]}]')
            lines.append(
                f'      {CURRENCY_SYMBOL}{d["price"]:.2f}  '
                f'(save {d["pct_off"]:.0f}% off {CURRENCY_SYMBOL}{d["msrp"]:.2f} MSRP '
                f'at {d["retailer"]}) -- shown to {d["subscriber_count"]} subscriber(s)'
            )
            lines.append(f'      {d["url"]}')
            lines.append('')
        lines += [
            '-' * 60,
            'This is internal admin tooling. Trigger the real send separately',
            'with: python manage.py send_sunday_faction_deals_uk',
        ]
        return '\n'.join(lines)
