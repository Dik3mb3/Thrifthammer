"""
Management command: send_weekly_deals

Finds the top 10 active Warhammer 40K products with the biggest discount vs
MSRP and sends a Wednesday deal digest to confirmed subscribers with monday_40k=True.

Usage:
    python manage.py send_weekly_deals            # production run
    python manage.py send_weekly_deals --dry-run  # log recipients, send nothing
    python manage.py send_weekly_deals --limit 5  # send top N deals instead of 10
"""

import datetime
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.management.base import BaseCommand
from django.db.models import DecimalField, F, Min, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from django.utils import timezone

from blog.models import Post
from prices.models import CurrentPrice
from products.models import NewsletterSignup, Product
from products.newsletter_deals import (
    DEAL_FOOTNOTE, build_deal, build_deal_tabs, build_text_sections,
    get_curated_deals, get_curated_label, order_candidates, pick_unique_deals, tab_log_lines,
)


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

        # ── 1. Find top 40K deals ────────────────────────────────────────────
        deals = self._get_top_deals(limit, category_name='Warhammer 40,000')

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

        # ── 1b. The Curated Picks and Most Saved tabs ──────
        saved_deals = self._get_top_deals(limit, category_name='Warhammer 40,000', by='saved')
        curated_deals, curated_status = get_curated_deals(
            self, 'wednesday', uk=False,
        )
        curated_label = get_curated_label('wednesday', uk=False)
        for line in tab_log_lines(curated_status, curated_deals, saved_deals, '$', curated_label):
            self.stdout.write(line)
        tabs = build_deal_tabs(curated_deals, deals, saved_deals, '$', curated_label)

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
            subscribers = list(
                NewsletterSignup.objects.filter(
                    is_confirmed=True,
                    monday_40k=True,
                    region=NewsletterSignup.REGION_US,
                )
            )
            if not subscribers:
                self.stdout.write(self.style.WARNING('No confirmed Wednesday 40K subscribers — nothing to send.'))
                return
            self.stdout.write(f'\n{len(subscribers)} confirmed Wednesday 40K subscriber(s).')

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
            f"This Week's Top 10 Warhammer 40K Deals -- Save Up to {top_saving}% Off"
            f" ({today.strftime('%b')} {today.day})"
        )

        # ── 4. Send (per-subscriber so each gets their own unsubscribe link) ─
        # Reuse a single SMTP connection across the whole batch -- opening a
        # fresh connection per subscriber (the old behavior) triggers Gmail's
        # abuse detection after ~85 rapid reconnects, which then drops every
        # subsequent connection with "Connection unexpectedly closed" and
        # silently fails the rest of the run.
        connection = get_connection()
        connection.open()
        sent = errors = 0
        for sub in subscribers:
            try:
                context = {
                    'deals': deals,
                    'today': today,
                    'site_url': 'https://thrifthammer.com',
                    'browse_url': 'https://thrifthammer.com/products/?region=us',
                    'register_url': 'https://thrifthammer.com/accounts/register/',
                    'top_pct': top_saving,
                    'tabs': tabs,
                    'deal_footnote': DEAL_FOOTNOTE,
                    'latest_post': latest_post,
                    'unsubscribe_url': sub.get_unsubscribe_url(),
                }
                html_body = render_to_string('emails/weekly_deals.html', context)
                text_body = self._build_text_body(tabs, today, sub.get_unsubscribe_url(), latest_post)

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[sub.email],
                    connection=connection,
                )
                msg.attach_alternative(html_body, 'text/html')
                try:
                    msg.send(fail_silently=False)
                except Exception:
                    # Connection may have dropped -- reopen once and retry
                    # this single message before giving up on it.
                    connection.close()
                    connection.open()
                    msg.send(fail_silently=False)
                sent += 1
                self.stdout.write(self.style.SUCCESS(f'  [sent] {sub.email}'))
                if hasattr(sub, 'record_send_success'):
                    sub.record_send_success()
            except Exception as exc:
                errors += 1
                self.stderr.write(f'  [error] {sub.email} — {exc}')
                if hasattr(sub, 'record_send_failure'):
                    sub.record_send_failure(exc)
        connection.close()

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

    def _annotated_products(self, require_ref=True):
        """
        Return active products annotated with gw_ref_price, the live US MSRP.

        The reference price is the live Games Workshop price, falling back to the
        static product.msrp snapshot. With require_ref=False products with no
        reference price are kept (a curated pick can be shown without a discount).
        """
        gw_ref_price_sq = Subquery(
            CurrentPrice.objects
            .filter(
                product=OuterRef('pk'),
                retailer__slug='games-workshop',
                not_available=False,
                price__isnull=False,
            )
            .order_by('price')
            .values('price')[:1]
        )
        qs = Product.objects.filter(is_active=True).annotate(
            gw_ref_price=Coalesce(
                gw_ref_price_sq, F('msrp'),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            )
        )
        if require_ref:
            qs = qs.filter(gw_ref_price__isnull=False)
        return qs

    @staticmethod
    def _with_cheapest_price(qs):
        """Annotate min_price, the cheapest in-stock US price, and keep only priced products."""
        return qs.annotate(
            min_price=Min(
                'current_prices__price',
                filter=Q(
                    current_prices__in_stock=True,
                    current_prices__not_available=False,
                ) & Q(current_prices__retailer__is_uk=False),
            )
        ).filter(min_price__isnull=False, min_price__gt=0)

    def _get_top_deals(self, limit, category_name=None, by='pct'):
        """
        Return up to `limit` dicts representing the best current deals.

        A deal is an active product with an MSRP where the cheapest in-stock
        CurrentPrice gives the largest percentage saving vs MSRP.

        Pass category_name to restrict to a single category (e.g. 'Warhammer 40,000').

        MSRP reference price is Games Workshop's live tracked price
        (gw_ref_price), falling back to the static product.msrp snapshot
        only when no live GW price is tracked at all. product.msrp only
        updates when someone manually runs sync_msrp_from_gw or re-imports
        a GW price list, so relying on it alone drifts stale after every
        GW price change -- that's what caused last week's newsletter to
        show duplicate/wrong prices. Same live-price pattern used for the
        "More Products" widget on product_detail.

        by='pct' (default) ranks by biggest % discount; by='saved' ranks by the
        biggest amount saved and keeps only products at least 20% below MSRP
        (the "Most Saved" tab). Both pick from the same >= 5% off candidates.
        """
        qs = self._annotated_products()
        if category_name:
            qs = qs.filter(category__name=category_name)
        # Temporary: hold Battletech and Paint & Supplies out of newsletters
        # while these newer catalog lines are being monitored.
        qs = qs.exclude(category__slug__in=('battletech', 'paint-supplies'))
        candidates = (
            self._with_cheapest_price(qs)
            # Only show products cheaper than MSRP by at least 5%
            .filter(min_price__lt=F('gw_ref_price') * Decimal('0.95'))
            .select_related('category', 'faction')
        )
        picked = pick_unique_deals(order_candidates(candidates, by), limit, uk=False)
        return [build_deal(product, uk=False) for product in picked]

    def _build_text_body(self, tabs, today, unsubscribe_url, latest_post=None):
        """Build a clean plain-text fallback email body."""
        lines = [
            'THRIFTHAMMER -- WEDNESDAY 40K DEAL DIGEST',
            f'{today.strftime("%B")} {today.day}, {today.year}',
            'https://thrifthammer.com',
            '',
            "This week's top Warhammer 40K discounts:",
            '',
        ]
        lines += build_text_sections(tabs, '$')

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
