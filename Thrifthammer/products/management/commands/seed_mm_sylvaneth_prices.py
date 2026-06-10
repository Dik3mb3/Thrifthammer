"""
Management command: seed_mm_sylvaneth_prices

Seeds Miniature Market prices for Sylvaneth products (SYL-001 to SYL-025).

Source: AOS Sylvaneth - GW, NK, MM.xlsx (2026-06-03)

MM MATCHES (15 products):
  SYL-002, SYL-003, SYL-004, SYL-006, SYL-007, SYL-008, SYL-010,
  SYL-011, SYL-014, SYL-015, SYL-016, SYL-017, SYL-018, SYL-021, SYL-025

NO MM LISTING (10 products):
  SYL-001, SYL-005, SYL-009, SYL-012, SYL-013,
  SYL-019, SYL-020, SYL-022, SYL-023, SYL-024

Shared kit notes:
  SYL-016 / SYL-017  — Revenant Seekers / Spiterider Lancers share MM listing

Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)

    # ── Spearhead ─────────────────────────────────────────────────────────────
    (
        'spearhead-sylvaneth-spitewing-flight',
        'Spearhead: Sylvaneth – Spitewing Flight',
        None,
        'https://www.miniaturemarket.com/Warhammer-Age-of-Sigmar-Spearhead-Sylvaneth-Spitewing-Flight/GW-70-922-2026',
        False,
        False,
    ),

    # ── Regiments of Renown / Warcry ─────────────────────────────────────────
    (
        'the-twisted-branch',
        'Sylvaneth: The Twisted Branch',
        None,
        'https://www.miniaturemarket.com/Warhammer-Age-of-Sigmar-Sylvaneth-The-Twisted-Branch/GW-92-53-2026',
        False,
        False,
    ),
    (
        'twistweald',
        'Warcry: Twistweald',
        None,
        'https://www.miniaturemarket.com/warcry-twistweald-gw-112-21.html',
        False,
        False,
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'gossamid-archers',
        'Gossamid Archers',
        None,
        'https://www.miniaturemarket.com/gw-92-27.html',
        False,
        False,
    ),
    (
        'arch-revenant',
        'Arch-Revenant',
        None,
        'https://www.miniaturemarket.com/gw-92-19.html',
        False,
        False,
    ),

    # ── Terrain ───────────────────────────────────────────────────────────────
    (
        'awakened-wyldwood',
        'Awakened Wyldwood',
        None,
        'https://www.miniaturemarket.com/gw-92-21.html',
        False,
        False,
    ),

    # ── Core units ────────────────────────────────────────────────────────────
    (
        'kurnoth-hunters',
        'Kurnoth Hunters',
        None,
        'https://www.miniaturemarket.com/gw-92-13.html',
        False,
        False,
    ),

    # ── Centrepiece ───────────────────────────────────────────────────────────
    (
        'alarielle-the-everqueen',
        'Alarielle the Everqueen',
        None,
        'https://www.miniaturemarket.com/gw-92-12.html',
        False,
        False,
    ),

    # ── Heroes (2026 releases) ────────────────────────────────────────────────
    (
        'grove-guardian',
        'Sylvaneth: Grove Guardian',
        None,
        'https://www.miniaturemarket.com/Warhammer-Age-of-Sigmar-Sylvaneth-Grove-Guardian/GW-92-54-2026',
        False,
        False,
    ),

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'order-battletome-sylvaneth',
        'Order Battletome: Sylvaneth (2026)',
        None,
        'https://www.miniaturemarket.com/Warhammer-Age-of-Sigmar-Order-Battletome-Sylvaneth-2026/GW-92-01-2026',
        False,
        False,
    ),

    # ── Cavalry (shared kit) ─────────────────────────────────────────────────
    # ⚠ Shared kit: Revenant Seekers / Spiterider Lancers share MM listing
    (
        'revenant-seekers',
        'Revenant Seekers / Spiterider Lancers',
        None,
        'https://www.miniaturemarket.com/gw-92-26.html',
        False,
        False,
    ),
    (
        'spiterider-lancers',
        'Revenant Seekers / Spiterider Lancers',
        None,
        'https://www.miniaturemarket.com/gw-92-26.html',
        False,
        False,
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'warsong-revenant',
        'Warsong Revenant',
        None,
        'https://www.miniaturemarket.com/gw-92-24.html',
        False,
        False,
    ),

    # ── Infantry ─────────────────────────────────────────────────────────────
    (
        'tree-revenants',
        'Tree-Revenants',
        None,
        'https://www.miniaturemarket.com/gw-92-14.html',
        False,
        False,
    ),

    # ── Named character ───────────────────────────────────────────────────────
    (
        'belthanos-first-thorn-of-kurnoth',
        'Belthanos - First Thorn of Kurnoth',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-sylvaneth-belthanos-first-thorn-kurnoth-gw-92-29.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Sylvaneth products."""

    help = 'Seeds Miniature Market listing URLs and prices for Sylvaneth. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stdout.write(self.style.ERROR('Miniature Market retailer not found'))
            return

        seeded = 0
        missing = 0

        for slug, title, price, url, in_stock, not_available in MM_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  [missing] {slug}'))
                missing += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
                defaults={
                    'url': url,
                    'listing_title': title,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {product.name}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Seeded={seeded}, Missing={missing}'
        ))
