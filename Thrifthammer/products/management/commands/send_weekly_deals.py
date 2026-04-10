"""
Management command: send_weekly_deals

Finds the top 10 active products with the biggest discount vs MSRP and sends
a weekly deal digest email to every NewsletterSignup subscriber.

Usage:
    python manage.py send_weekly_deals            # production run
    python manage.py send_weekly_deals --dry-run  # log recipients, send nothing
    python manage.py send_weekly_deals --limit 5  # send top N deals instead of 10
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


class Command(BaseCommand):
    """Send a weekly deal digest to all newsletter subscribers."""

    help = 'Email the top N discounted products to every newsletter subscriber.'

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
        """Main entry point — find deals, build email, send to all subscribers."""
        dry_run = options['dry_run']
        limit = options['limit']
        recipient_override = options['recipient']
        today = datetime.date.today()

        # ── 1. Find top deals ────────────────────────────────────────────────
        deals = self._get_top_deals(limit)

        if not deals:
            self.stdout.write(self.style.WARNING('No deals found — nothing to send.'))
            return

        self.stdout.write(f'Found {len(deals)} deals for {today}:')
        for i, d in enumerate(deals, 1):
            self.stdout.write(
                f'  {i:>2}. {d["name"]:50s}  '
                f'${d["price"]:.2f}  '
                f'(save {d["pct_off"]:.0f}% off ${d["msrp"]:.2f})'
            )

        # ── 2. Gather subscribers (or use override for testing) ──────────────
        if recipient_override:
            # Create a minimal stub — just needs .email and .get_unsubscribe_url()
            class _Stub:
                email = recipient_override
                def get_unsubscribe_url(self):
                    return 'https://thrifthammer.com/products/newsletter/unsubscribe/test/'
            subscribers = [_Stub()]
            self.stdout.write(f'\nTEST MODE — sending only to: {recipient_override}')
        else:
            subscribers = list(NewsletterSignup.objects.all())
            if not subscribers:
                self.stdout.write(self.style.WARNING('No newsletter subscribers — nothing to send.'))
                return
            self.stdout.write(f'\n{len(subscribers)} subscriber(s) found.')

        # ── 3. Fetch latest published blog post ──────────────────────────────
        latest_post = (
            Post.objects
            .filter(status=Post.STATUS_PUBLISHED, published_at__lte=timezone.now())
            .order_by('-published_at')
            .first()
        )
        if latest_post:
            self.stdout.write(f'Latest blog post: "{latest_post.title}"')
        else:
            self.stdout.write('No published blog post found — blog section will be hidden.')

        if dry_run:
            for sub in subscribers:
                self.stdout.write(f'  [dry-run] Would send to: {sub.email}')
            self.stdout.write('\nDry run complete — no emails sent.')
            return

        # Dynamic subject — mentions the top saving to hook the reader
        top_saving = int(deals[0]['pct_off']) if deals else 0
        subject = (
            f"This Week's Top 10 Warhammer Deals -- Save Up to {top_saving}% Off"
            f" ({today.strftime('%b')} {today.day})"
        )

        # ── 4. Send (per-subscriber so each gets their own unsubscribe link) ─
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
                }
                html_body = render_to_string('emails/weekly_deals.html', context)
                text_body = self._build_text_body(deals, today, sub.get_unsubscribe_url(), latest_post)

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

        self.stdout.write(
            f'\nDone -- sent: {sent} | errors: {errors}'
        )

        if errors and not sent:
            # Every send failed — raise so GitHub Actions marks the run red
            raise Exception(
                f'All {errors} email(s) failed to send. '
                'Check EMAIL_HOST_USER / EMAIL_HOST_PASSWORD secrets.'
            )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_top_deals(self, limit):
        """
        Return up to `limit` dicts representing the best current deals.

        A deal is an active product with an MSRP where the cheapest in-stock
        CurrentPrice gives the largest percentage saving vs MSRP.
        """
        # Annotate each active product with its cheapest in-stock price.
        # We calculate pct_saving in Python to avoid ORM type-inference
        # issues with mixed Decimal/Float arithmetic across DB backends.
        candidates = (
            Product.objects
            .filter(is_active=True, msrp__isnull=False)
            .annotate(
                min_price=Min(
                    'current_prices__price',
                    filter=Q(
                        current_prices__in_stock=True,
                        current_prices__not_available=False,
                    ),
                )
            )
            .filter(min_price__isnull=False, min_price__gt=0)
            # Only show products cheaper than MSRP by at least 5%
            .filter(min_price__lt=F('msrp') * Decimal('0.95'))
            .select_related('category', 'faction')
        )

        # Sort by % discount descending in Python, then take top N
        def _pct(p):
            """Calculate % discount vs MSRP."""
            return float(p.msrp - p.min_price) / float(p.msrp) * 100

        sorted_candidates = sorted(candidates, key=_pct, reverse=True)[:limit]

        deals = []
        for product in sorted_candidates:
            pct_off = _pct(product)
            # Fetch the cheapest retailer name for this product
            best_cp = (
                CurrentPrice.objects
                .filter(
                    product=product,
                    in_stock=True,
                    not_available=False,
                    price=product.min_price,
                )
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
            })

        return deals

    def _build_text_body(self, deals, today, unsubscribe_url, latest_post=None):
        """Build a clean plain-text fallback email body."""
        lines = [
            'THRIFTHAMMER -- WEEKLY DEAL DIGEST',
            f'{today.strftime("%B")} {today.day}, {today.year}',
            'https://thrifthammer.com',
            '',
            "This week's top Warhammer discounts:",
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
