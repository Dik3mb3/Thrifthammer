"""
Management command: review_sunday_faction_deals

Read-only reporting tool -- NOT part of the real Sunday send and never
touches real subscribers. Loops through every confirmed sunday_faction
subscriber exactly as the real send does, computes each one's personalized
deal list using the same deal-selection logic the real send uses, and
merges the results into a single deduplicated union: every unique product
that would appear in ANY subscriber's digest this week, with how many
subscribers would see it and which faction it belongs to.

That consolidated list is emailed to the admin only, so the full real-world
content can be reviewed before deciding to trigger the real send
(python manage.py send_sunday_faction_deals).

Reuses send_sunday_faction_deals.Command._get_faction_deals() by importing
the real command and calling its method directly, rather than duplicating
the query -- this review can never drift from what the real send actually
computes.

The admin recipient is intentionally hardcoded below, with no --recipient
argument or other override. This command must never be able to email
anyone but the admin, by construction, not just by default.

Usage:
    python manage.py review_sunday_faction_deals
    python manage.py review_sunday_faction_deals --limit 15
"""

import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from products.management.commands.send_sunday_faction_deals import (
    Command as SundayFactionDealsCommand,
)
from products.models import NewsletterSignup

# Intentionally hardcoded -- see module docstring. Never add a --recipient
# argument to this command; it must only ever be able to email the admin.
_ADMIN_EMAIL = 'alexanderalonso1996@gmail.com'


class Command(BaseCommand):
    """Email the admin a deduplicated union of every Sunday subscriber's deals."""

    help = (
        "Read-only: email the admin a deduplicated union of every unique "
        "deal that would appear in ANY confirmed Sunday-faction subscriber's "
        "personalized digest this week. Sends nothing to real subscribers."
    )

    def add_arguments(self, parser):
        """Add --limit, matching the real send's per-subscriber deal cap."""
        parser.add_argument(
            '--limit', type=int, default=10,
            help='Deals per subscriber to consider, same default as the real send (default: 10).',
        )

    def handle(self, *args, **options):
        """Build the union across all real subscribers and email it to the admin."""
        limit = options['limit']
        today = datetime.date.today()

        subscribers = list(
            NewsletterSignup.objects
            .filter(
                is_confirmed=True,
                sunday_faction=True,
                region=NewsletterSignup.REGION_US,
            )
            .prefetch_related('factions')
        )
        if not subscribers:
            self.stdout.write(self.style.WARNING(
                'No confirmed Sunday faction subscribers -- nothing to review.'
            ))
            return

        self.stdout.write(f'{len(subscribers)} confirmed Sunday subscriber(s) to check.\n')

        # Reuse the real send command's own deal-selection method so this
        # review can never compute something different from the real send.
        deal_source = SundayFactionDealsCommand()

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

        self.stdout.write(
            f'Subscribers checked: {len(subscribers)} | '
            f'skipped (no factions selected): {skipped_no_factions} | '
            f'skipped (no deals found): {skipped_no_deals}\n'
        )

        if not union:
            self.stdout.write(self.style.WARNING(
                'No deals found across any subscriber -- nothing to send.'
            ))
            return

        deals_list = sorted(union.values(), key=lambda d: d['pct_off'], reverse=True)

        self.stdout.write(f'{len(deals_list)} unique deal(s) across all Sunday subscribers:')
        for i, d in enumerate(deals_list, 1):
            self.stdout.write(
                f'  {i:>3}. {d["name"]:45.45s} {d["group_label"]:22.22s} '
                f'${d["price"]:.2f} (save {d["pct_off"]:.0f}%) '
                f'-- {d["subscriber_count"]} subscriber(s)'
            )

        subject = (
            f"[ADMIN REVIEW] Sunday Faction Digest -- {len(deals_list)} Unique Deals "
            f"Across {len(subscribers)} Subscriber(s) ({today.strftime('%b')} {today.day})"
        )
        context = {
            'deals': deals_list,
            'today': today,
            'subscriber_count': len(subscribers),
            'digest_label': 'Sunday Faction',
        }
        html_body = render_to_string('emails/review_personalized_digest.html', context)
        text_body = self._build_text_body(deals_list, today, len(subscribers))

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
            'THRIFTHAMMER -- ADMIN REVIEW: SUNDAY FACTION DIGEST',
            '(Not sent to subscribers -- admin review only)',
            f'{today.strftime("%B")} {today.day}, {today.year}',
            f'{len(deals)} unique deal(s) across {subscriber_count} confirmed subscriber(s)',
            '',
        ]
        for i, d in enumerate(deals, 1):
            lines.append(f'{i:>3}. {d["name"]}  [{d["group_label"]}]')
            lines.append(
                f'      ${d["price"]:.2f}  (save {d["pct_off"]:.0f}% off ${d["msrp"]:.2f} MSRP '
                f'at {d["retailer"]}) -- shown to {d["subscriber_count"]} subscriber(s)'
            )
            lines.append(f'      {d["url"]}')
            lines.append('')
        lines += [
            '-' * 60,
            'This is internal admin tooling. Trigger the real send separately',
            'with: python manage.py send_sunday_faction_deals',
        ]
        return '\n'.join(lines)
