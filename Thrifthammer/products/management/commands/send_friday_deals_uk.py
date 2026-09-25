"""
Management command: send_friday_deals_uk

UK mirror of send_friday_deals. Finds the top 10 active "Rest of Warhammer"
products (everything in the Warhammer universe except 40K and Books and
Novels) with the biggest discount vs GBP MSRP, and sends a Friday deal
digest to confirmed UK subscribers with friday_other=True.

Covers Age of Sigmar, Horus Heresy, The Old World, Kill Team, Necromunda,
Warcry, and Blood Bowl -- same scope as the US command (WARHAMMER_CATEGORY_SLUGS
is a category concept, not a currency one, so it's reused unchanged).

This is a SEPARATE file from send_friday_deals.py on purpose, not a region
branch inside it -- see send_weekly_deals_uk.py's docstring for why. Every
retailer/price lookup below uses games-workshop-uk / is_uk=True; this
command never touches games-workshop / is_uk=False.

Usage:
    python manage.py send_friday_deals_uk            # production run
    python manage.py send_friday_deals_uk --dry-run  # log recipients, send nothing
    python manage.py send_friday_deals_uk --limit 5  # send top N deals instead of 10
"""

import datetime
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.db.models import DecimalField, F, Min, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from django.utils import timezone

from blog.models import Post
from prices.models import CurrentPrice
from products.models import NewsletterSignup, Product, WARHAMMER_CATEGORY_SLUGS

CURRENCY_SYMBOL = '£'


class Command(BaseCommand):
    """Send a Friday UK Rest-of-Warhammer deal digest to opted-in UK subscribers."""

    help = 'Email the top N GBP-discounted non-40K products to UK friday_other subscribers.'

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
        """Main entry point — find deals, build email, send to UK friday_other subscribers."""
        dry_run = options['dry_run']
        limit = options['limit']
        recipient_override = options['recipient']
        today = datetime.date.today()

        # ── 1. Find top non-40K UK deals ──────────────────────────────────────
        deals = self._get_top_deals(limit)

        if not deals:
            self.stdout.write(self.style.WARNING('No UK deals found — nothing to send.'))
            return

        self.stdout.write(f'Found {len(deals)} UK deals for {today}:')
        for i, d in enumerate(deals, 1):
            self.stdout.write(
                f'  {i:>2}. {d["name"]:50s}  '
                f'{CURRENCY_SYMBOL}{d["price"]:.2f}  '
                f'(save {d["pct_off"]:.0f}% off {CURRENCY_SYMBOL}{d["msrp"]:.2f})'
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
                NewsletterSignup.objects.filter(
                    is_confirmed=True,
                    friday_other=True,
                    region=NewsletterSignup.REGION_UK,
                )
            )
            if not subscribers:
                self.stdout.write(self.style.WARNING('No confirmed UK Friday subscribers — nothing to send.'))
                return
            self.stdout.write(f'\n{len(subscribers)} confirmed UK Friday subscriber(s).')

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
            f"This Week's Top 10 UK Rest of Warhammer Deals -- Save Up to {top_saving}% Off"
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
                    'browse_url': 'https://thrifthammer.com/products/?region=uk',
                    'register_url': 'https://thrifthammer.com/accounts/register/',
                    'top_pct': top_saving,
                    'latest_post': latest_post,
                    'unsubscribe_url': sub.get_unsubscribe_url(),
                    'currency_symbol': CURRENCY_SYMBOL,
                }
                html_body = render_to_string('emails/friday_deals.html', context)
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
                if hasattr(sub, 'record_send_success'):
                    sub.record_send_success()
            except Exception as exc:
                errors += 1
                self.stderr.write(f'  [error] {sub.email} — {exc}')
                if hasattr(sub, 'record_send_failure'):
                    sub.record_send_failure(exc)

        self.stdout.write(f'\nDone -- sent: {sent} | errors: {errors}')

        if errors and not sent:
            raise Exception(
                f'All {errors} email(s) failed to send. '
                'Check EMAIL_HOST_USER / EMAIL_HOST_PASSWORD secrets.'
            )

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_top_deals(self, limit):
        """
        Return up to `limit` dicts for the best UK "Rest of Warhammer" deals.

        Scoped to WARHAMMER_CATEGORY_SLUGS minus 40K (Wednesday's territory)
        and minus Books and Novels (no UK book pricing exists yet) -- the
        same INCLUDE list the US command uses, reused unchanged since this
        is a category question, not a currency one.

        MSRP reference price is Games Workshop UK's live tracked price
        (gw_ref_price, sourced from the games-workshop-uk retailer), falling
        back to the static product.msrp_gbp snapshot only when no live GW UK
        price is tracked at all.
        """
        gw_ref_price_sq = Subquery(
            CurrentPrice.objects
            .filter(
                product=OuterRef('pk'),
                retailer__slug='games-workshop-uk',
                not_available=False,
                price__isnull=False,
            )
            .order_by('price')
            .values('price')[:1]
        )
        candidates = (
            Product.objects
            .filter(is_active=True)
            .annotate(
                gw_ref_price=Coalesce(
                    gw_ref_price_sq, F('msrp_gbp'),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
            .filter(gw_ref_price__isnull=False)
            .filter(category__slug__in=WARHAMMER_CATEGORY_SLUGS - {'warhammer-40000', 'books-and-novels'})
            .annotate(
                min_price=Min(
                    'current_prices__price',
                    filter=Q(
                        current_prices__in_stock=True,
                        current_prices__not_available=False,
                        current_prices__retailer__is_uk=True,
                    ),
                )
            )
            .filter(min_price__isnull=False, min_price__gt=0)
            .filter(min_price__lt=F('gw_ref_price') * Decimal('0.95'))
            .select_related('category', 'faction')
        )

        def _pct(p):
            """Calculate % discount vs the live GW UK reference price."""
            return float(p.gw_ref_price - p.min_price) / float(p.gw_ref_price) * 100

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
                    retailer__is_uk=True,
                )
                .select_related('retailer')
                .first()
            )
            retailer_name = best_cp.retailer.name if best_cp and best_cp.retailer else 'a retailer'

            deals.append({
                'name': product.name,
                'slug': product.slug,
                'url': f'https://thrifthammer.com/products/{product.slug}/?region=uk',
                'price': float(product.min_price),
                'msrp': float(product.gw_ref_price),
                'pct_off': pct_off,
                'savings': float(product.gw_ref_price - product.min_price),
                'retailer': retailer_name,
                'image_url': product.image_url or '',
                'category': product.category.name if product.category else '',
            })

        return deals

    def _build_text_body(self, deals, today, unsubscribe_url, latest_post=None):
        """Build a clean plain-text fallback email body."""
        lines = [
            'THRIFTHAMMER -- FRIDAY UK REST OF WARHAMMER DEAL DIGEST',
            f'{today.strftime("%B")} {today.day}, {today.year}',
            'https://thrifthammer.com',
            '',
            "This week's top UK Age of Sigmar, Horus Heresy & more discounts:",
            '',
        ]
        for i, d in enumerate(deals, 1):
            lines.append(f'{i:>2}. {d["name"]}')
            lines.append(
                f'    {CURRENCY_SYMBOL}{d["price"]:.2f}  '
                f'(save {d["pct_off"]:.0f}% off {CURRENCY_SYMBOL}{d["msrp"]:.2f} MSRP at {d["retailer"]})'
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
