"""
Management command: send_sunday_faction_deals

Sends a personalised Sunday deal digest to confirmed subscribers who have
opted in (sunday_faction=True) and selected at least one faction.

Each subscriber receives a tailored email showing deals only from their
chosen faction(s), ranked by % discount vs MSRP.

Usage:
    python manage.py send_sunday_faction_deals            # production run
    python manage.py send_sunday_faction_deals --dry-run
    python manage.py send_sunday_faction_deals --limit 10
"""

import datetime
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.db.models import F, Min, Q
from django.template.loader import render_to_string
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import NewsletterSignup, Product


class Command(BaseCommand):
    """Send a personalised Sunday faction deal digest to opted-in subscribers."""

    help = 'Email personalised faction deals to sunday_faction subscribers.'

    def add_arguments(self, parser):
        """Add --dry-run, --limit, and --recipient flags."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without actually sending emails.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of top deals per subscriber to include (default: 10).',
        )
        parser.add_argument(
            '--recipient',
            type=str,
            default=None,
            help='Send only to this address instead of all subscribers (for testing).',
        )

    def handle(self, *args, **options):
        """Main entry point — find subscribers, build personalised emails, send."""
        dry_run = options['dry_run']
        limit = options['limit']
        recipient_override = options['recipient']
        today = datetime.date.today()

        # ── 1. Gather subscribers ─────────────────────────────────────────────
        if recipient_override:
            # Test mode: use the recipient_override but still look up their prefs
            subscriber = NewsletterSignup.objects.filter(
                email__iexact=recipient_override,
            ).prefetch_related('factions').first()
            if subscriber:
                subscribers = [subscriber]
            else:
                # Fallback stub with no factions — useful for basic smoke test
                class _Stub:
                    email = recipient_override
                    factions = NewsletterSignup.objects.none()
                    def get_unsubscribe_url(self):
                        return 'https://thrifthammer.com/products/newsletter/unsubscribe/test/'
                subscribers = [_Stub()]
            self.stdout.write(f'\nTEST MODE — sending only to: {recipient_override}')
        else:
            subscribers = list(
                NewsletterSignup.objects
                .filter(is_confirmed=True, sunday_faction=True)
                .prefetch_related('factions')
            )
            if not subscribers:
                self.stdout.write(self.style.WARNING('No confirmed Sunday faction subscribers — nothing to send.'))
                return
            self.stdout.write(f'\n{len(subscribers)} confirmed Sunday subscriber(s).')

        if dry_run:
            for sub in subscribers:
                factions = getattr(sub.factions, 'all', lambda: [])()
                faction_names = ', '.join(f.name for f in factions) or '(none)'
                self.stdout.write(f'  [dry-run] Would send to: {sub.email} — factions: {faction_names}')
            self.stdout.write('\nDry run complete — no emails sent.')
            return

        # ── 2. Send per subscriber ────────────────────────────────────────────
        sent = errors = skipped = 0
        for sub in subscribers:
            try:
                faction_list = list(sub.factions.all())
                if not faction_list:
                    self.stdout.write(self.style.WARNING(f'  [skip] {sub.email} — no factions selected'))
                    skipped += 1
                    continue

                deals = self._get_faction_deals(faction_list, limit)
                if not deals:
                    self.stdout.write(self.style.WARNING(f'  [skip] {sub.email} — no deals found for their factions'))
                    skipped += 1
                    continue

                faction_names = ', '.join(f.name for f in faction_list)
                top_saving = int(deals[0]['pct_off']) if deals else 0
                subject = (
                    f"Your {faction_names} Deals — Save Up to {top_saving}% Off"
                    f" ({today.strftime('%b')} {today.day})"
                )

                context = {
                    'deals': deals,
                    'today': today,
                    'faction_names': faction_names,
                    'site_url': 'https://thrifthammer.com',
                    'browse_url': 'https://thrifthammer.com/products/',
                    'register_url': 'https://thrifthammer.com/accounts/register/',
                    'top_pct': top_saving,
                    'unsubscribe_url': sub.get_unsubscribe_url(),
                }
                html_body = render_to_string('emails/sunday_faction_deals.html', context)
                text_body = self._build_text_body(deals, today, faction_names, sub.get_unsubscribe_url())

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[sub.email],
                )
                msg.attach_alternative(html_body, 'text/html')
                msg.send(fail_silently=False)
                sent += 1
                self.stdout.write(self.style.SUCCESS(f'  [sent] {sub.email} ({faction_names})'))
            except Exception as exc:
                errors += 1
                self.stderr.write(f'  [error] {sub.email} — {exc}')

        self.stdout.write(f'\nDone -- sent: {sent} | skipped: {skipped} | errors: {errors}')

        if errors and not sent and not skipped:
            raise Exception(
                f'All {errors} email(s) failed to send. '
                'Check EMAIL_HOST_USER / EMAIL_HOST_PASSWORD secrets.'
            )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_faction_deals(self, factions, limit):
        """
        Return up to `limit` deal dicts for products belonging to the given factions.

        Ranked by % discount vs MSRP descending.
        """
        # Exclude UK retailers so GBP prices never appear as cheap USD deals.
        _uk_slugs = frozenset({'ebay-uk', 'amazon-uk'})
        faction_ids = [f.pk for f in factions]
        candidates = (
            Product.objects
            .filter(is_active=True, msrp__isnull=False, faction_id__in=faction_ids)
            .annotate(
                min_price=Min(
                    'current_prices__price',
                    filter=Q(
                        current_prices__in_stock=True,
                        current_prices__not_available=False,
                    ) & ~Q(current_prices__retailer__slug__in=_uk_slugs),
                )
            )
            .filter(min_price__isnull=False, min_price__gt=0)
            .filter(min_price__lt=F('msrp') * Decimal('0.95'))
            .select_related('category', 'faction')
        )

        def _pct(p):
            """Calculate % discount vs MSRP."""
            return float(p.msrp - p.min_price) / float(p.msrp) * 100

        sorted_candidates = sorted(candidates, key=_pct, reverse=True)[:limit]

        deals = []
        for product in sorted_candidates:
            pct_off = _pct(product)
            best_cp = (
                CurrentPrice.objects
                .filter(
                    product=product,
                    in_stock=True,
                    not_available=False,
                    price=product.min_price,
                )
                .exclude(retailer__slug__in=_uk_slugs)
                .select_related('retailer')
                .first()
            )
            retailer_name = best_cp.retailer.name if best_cp and best_cp.retailer else 'a retailer'

            deals.append({
                'name': product.name,
                'slug': product.slug,
                'url': f'https://thrifthammer.com/products/{product.slug}/',
                'price': float(product.min_price),
                'msrp': float(product.msrp),
                'pct_off': pct_off,
                'savings': float(product.msrp - product.min_price),
                'retailer': retailer_name,
                'image_url': product.image_url or '',
                'faction': product.faction.name if product.faction else '',
            })

        return deals

    def _build_text_body(self, deals, today, faction_names, unsubscribe_url):
        """Build a clean plain-text fallback email body."""
        lines = [
            f'THRIFTHAMMER -- YOUR {faction_names.upper()} DEALS',
            f'{today.strftime("%B")} {today.day}, {today.year}',
            'https://thrifthammer.com',
            '',
            f"This week's best deals for your faction(s): {faction_names}",
            '',
        ]
        for i, d in enumerate(deals, 1):
            lines.append(f'{i:>2}. {d["name"]}')
            lines.append(
                f'    ${d["price"]:.2f}  (save {d["pct_off"]:.0f}% off ${d["msrp"]:.2f} MSRP at {d["retailer"]})'
            )
            lines.append(f'    {d["url"]}')
            lines.append('')

        lines += [
            '-' * 60,
            'CREATE A FREE ACCOUNT',
            'Track prices, build wishlists, and get personal alerts',
            'when your target price drops.',
            'https://thrifthammer.com/accounts/register/',
            '',
            '-' * 60,
            "You're receiving this because you opted in to faction deal alerts.",
            'Stop overpaying for plastic.',
            '-- ThriftHammer',
            '',
            f'Unsubscribe: {unsubscribe_url}',
        ]
        return '\n'.join(lines)
