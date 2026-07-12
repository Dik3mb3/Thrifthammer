"""
Management command: send_aos_apology

One-off corrected AoS deal digest sent to friday_other subscribers as an
apology for incorrect prices in the earlier Friday email.

Filters to Age of Sigmar products only (not all non-40K).
Passes apology_note context to friday_deals.html via the {% if apology_note %}
block — no new template needed.

Usage:
    python manage.py send_aos_apology            # production run
    python manage.py send_aos_apology --dry-run  # log recipients, send nothing
    python manage.py send_aos_apology --recipient test@example.com
    python manage.py send_aos_apology --limit 5
"""

import datetime
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.db.models import F, Min, Q
from django.template.loader import render_to_string
from django.utils import timezone

from blog.models import Post
from prices.models import CurrentPrice
from products.models import NewsletterSignup, Product

_APOLOGY_NOTE = (
    "Hi all,\n\n"
    "This morning you received an email with incorrect prices for some Age of "
    "Sigmar products. The website prices are fine, but there was a bug on the "
    "backend that came from a new update I was working on for the future. You "
    "can find the corrected deals below.\n\n"
    "Sorry for the confusion, I apologize for any inconvenience.\n\n"
    "ThriftHammer"
)


class Command(BaseCommand):
    """Send a corrected AoS deal digest with apology note to friday_other subscribers."""

    help = 'Email a corrected top-N AoS deal digest with apology to friday_other subscribers.'

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
            help='Number of top deals to include (default: 10).',
        )
        parser.add_argument(
            '--recipient',
            type=str,
            default=None,
            help='Send only to this address instead of all subscribers (for testing).',
        )

    def handle(self, *args, **options):
        """Find top AoS deals, build apology email, send to friday_other subscribers."""
        dry_run = options['dry_run']
        limit = options['limit']
        recipient_override = options['recipient']
        today = datetime.date.today()

        # ── 1. Find top AoS deals ─────────────────────────────────────────────
        deals = self._get_top_deals(limit)

        if not deals:
            self.stdout.write(self.style.WARNING('No AoS deals found — nothing to send.'))
            return

        self.stdout.write(f'Found {len(deals)} AoS deals for {today}:')
        for i, d in enumerate(deals, 1):
            self.stdout.write(
                f'  {i:>2}. {d["name"]:50s}  '
                f'${d["price"]:.2f}  '
                f'(save {d["pct_off"]:.0f}% off ${d["msrp"]:.2f})'
            )

        # ── 2. Gather subscribers ─────────────────────────────────────────────
        if recipient_override:
            class _Stub:
                email = recipient_override

                def get_unsubscribe_url(self):
                    return 'https://thrifthammer.com/products/newsletter/unsubscribe/test/'

            subscribers = [_Stub()]
            self.stdout.write(f'\nTEST MODE — sending only to: {recipient_override}')
        else:
            subscribers = list(
                NewsletterSignup.objects.filter(is_confirmed=True, friday_other=True)
            )
            if not subscribers:
                self.stdout.write(self.style.WARNING(
                    'No confirmed Friday subscribers — nothing to send.'
                ))
                return
            self.stdout.write(f'\n{len(subscribers)} confirmed Friday subscriber(s).')

        # ── 3. Fetch latest published blog post ───────────────────────────────
        latest_post = (
            Post.objects
            .filter(status=Post.STATUS_PUBLISHED, published_at__lte=timezone.now())
            .order_by('-published_at')
            .first()
        )

        if dry_run:
            for sub in subscribers:
                self.stdout.write(f'  [dry-run] Would send to: {sub.email}')
            self.stdout.write('\nDry run complete — no emails sent.')
            return

        top_saving = int(deals[0]['pct_off']) if deals else 0
        subject = (
            f"[Corrected] This Week's Top AoS Deals -- Save Up to {top_saving}% Off"
            f" ({today.strftime('%b')} {today.day})"
        )

        # ── 4. Send ───────────────────────────────────────────────────────────
        sent = errors = 0
        for sub in subscribers:
            try:
                context = {
                    'deals': deals,
                    'today': today,
                    'site_url': 'https://thrifthammer.com',
                    'browse_url': 'https://thrifthammer.com/products/',
                    'register_url': 'https://thrifthammer.com/accounts/register/',
                    'top_pct': top_saving,
                    'latest_post': latest_post,
                    'unsubscribe_url': sub.get_unsubscribe_url(),
                    'apology_note': _APOLOGY_NOTE,
                }
                html_body = render_to_string('emails/friday_deals.html', context)
                text_body = self._build_text_body(
                    deals, today, sub.get_unsubscribe_url(), latest_post
                )

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

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_top_deals(self, limit):
        """Return up to `limit` dicts for the best Age of Sigmar current deals."""
        _uk_slugs = frozenset({'ebay-uk', 'amazon-uk'})
        candidates = (
            Product.objects
            .filter(is_active=True, msrp__isnull=False, category__name='Age of Sigmar')
            # Temporary: hold Battletech and Paint & Supplies out of newsletters
            # while these newer catalog lines are being monitored.
            .exclude(category__slug__in=('battletech', 'paint-supplies'))
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
                'category': product.category.name if product.category else '',
            })

        return deals

    def _build_text_body(self, deals, today, unsubscribe_url, latest_post=None):
        """Build a clean plain-text fallback email body."""
        lines = [
            'THRIFTHAMMER -- CORRECTED AoS DEAL DIGEST',
            f'{today.strftime("%B")} {today.day}, {today.year}',
            'https://thrifthammer.com',
            '',
            _APOLOGY_NOTE,
            '',
            '-' * 60,
            "This week's corrected top Age of Sigmar discounts:",
            '',
        ]
        for i, d in enumerate(deals, 1):
            lines.append(f'{i:>2}. {d["name"]}')
            lines.append(
                f'    ${d["price"]:.2f}  '
                f'(save {d["pct_off"]:.0f}% off ${d["msrp"]:.2f} MSRP at {d["retailer"]})'
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
        ]

        if latest_post:
            lines += [
                '-' * 60,
                'LATEST FROM THE BLOG',
                latest_post.title,
            ]
            if latest_post.excerpt:
                lines.append(latest_post.excerpt)
            lines.append(f'https://thrifthammer.com/blog/{latest_post.slug}/')
            lines.append('')

        lines += [
            '-' * 60,
            "You're receiving this because you signed up at thrifthammer.com.",
            'Stop overpaying for plastic.',
            '-- ThriftHammer',
            '',
            f'Unsubscribe: {unsubscribe_url}',
        ]
        return '\n'.join(lines)
