"""
Management command: seed_nk_sylvaneth_prices

Seeds Noble Knight prices for Sylvaneth products (SYL-001 to SYL-025).

Source: AOS Sylvaneth - GW, NK, MM.xlsx (2026-06-03)

NK MATCHES (22 products):
  SYL-001, SYL-002, SYL-003, SYL-004, SYL-005, SYL-006, SYL-007,
  SYL-008, SYL-009, SYL-010, SYL-011, SYL-014, SYL-015, SYL-016,
  SYL-017, SYL-018, SYL-020, SYL-021, SYL-022, SYL-023, SYL-024, SYL-025

NO NK LISTING (3 products):
  SYL-012  Dryads
  SYL-013  Branchwych
  SYL-019  Spite-Revenants

Shared kit notes:
  SYL-016 / SYL-017  — Revenant Seekers / Spiterider Lancers share NK listing
  SYL-022 / SYL-023 / SYL-024  — Spirit of Durthu / Treelord Ancient / Treelord
                                   share NK listing

Affiliate tag ?awid=1576 appended to all URLs.
Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)

    # ── Battleforce / Spearhead ───────────────────────────────────────────────
    (
        'battleforce-sylvaneth-strongroot-grove',
        'Battleforce - Strongroot Grove',
        None,
        f'{_NK}/P/2148434540/Battleforce---Strongroot-Grove?awid=1576',
        False,
        False,
    ),
    (
        'spearhead-sylvaneth-spitewing-flight',
        'Spearhead - Spitewing Flight',
        None,
        f'{_NK}/P/2148434578/Spearhead---Spitewing-Flight?awid=1576',
        False,
        False,
    ),

    # ── Regiments of Renown / Warcry ─────────────────────────────────────────
    (
        'the-twisted-branch',
        'Regiments of Renown - The Twisted Branch',
        None,
        f'{_NK}/P/2148434583/Regiments-of-Renown---The-Twisted-Branch?awid=1576',
        False,
        False,
    ),
    (
        'twistweald',
        'Twistweald',
        None,
        f'{_NK}/P/2148200847/Twistweald?awid=1576',
        False,
        False,
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'the-lady-of-vines',
        'Lady of Vines, The',
        None,
        f'{_NK}/P/2147997378/Lady-of-Vines-The?awid=1576',
        False,
        False,
    ),
    (
        'gossamid-archers',
        'Gossamid Archers',
        None,
        f'{_NK}/P/2147986339/Gossamid-Archers?awid=1576',
        False,
        False,
    ),
    (
        'arch-revenant',
        'Arch-Revenant',
        None,
        f'{_NK}/P/2148004880/Arch-Revenant?awid=1576',
        False,
        False,
    ),

    # ── Terrain / Endless Spells ─────────────────────────────────────────────
    (
        'awakened-wyldwood',
        'Awakened Wyldwood',
        None,
        f'{_NK}/P/2147758676/Awakened-Wyldwood?awid=1576',
        False,
        False,
    ),
    (
        'endless-spells-sylvaneth',
        'Endless Spells - Sylvaneth',
        None,
        f'{_NK}/P/2147758678/Endless-Spells---Sylvaneth?awid=1576',
        False,
        False,
    ),

    # ── Core units ────────────────────────────────────────────────────────────
    (
        'kurnoth-hunters',
        'Kurnoth Hunters',
        None,
        f'{_NK}/P/2148009776/Kurnoth-Hunters?awid=1576',
        False,
        False,
    ),

    # ── Centrepiece ───────────────────────────────────────────────────────────
    (
        'alarielle-the-everqueen',
        'Alarielle the Everqueen',
        None,
        f'{_NK}/P/2148009796/Alarielle-the-Everqueen?awid=1576',
        False,
        False,
    ),

    # SYL-012 Dryads        — no NK listing
    # SYL-013 Branchwych    — no NK listing

    # ── Heroes (2026 releases) ────────────────────────────────────────────────
    (
        'grove-guardian',
        'Grove Guardian',
        None,
        f'{_NK}/P/2148434582/Grove-Guardian?awid=1576',
        False,
        False,
    ),

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'order-battletome-sylvaneth',
        'Battletome - Sylvaneth',
        None,
        f'{_NK}/P/2148434580/Battletome---Sylvaneth?awid=1576',
        False,
        False,
    ),

    # ── Cavalry (shared kit) ─────────────────────────────────────────────────
    # ⚠ Shared kit: Revenant Seekers / Spiterider Lancers share NK listing
    (
        'revenant-seekers',
        'Revenant Seekers / Spiterider Lancers',
        None,
        f'{_NK}/P/2147986338/Spiterider-Lancers?awid=1576',
        False,
        False,
    ),
    (
        'spiterider-lancers',
        'Revenant Seekers / Spiterider Lancers',
        None,
        f'{_NK}/P/2147986338/Spiterider-Lancers?awid=1576',
        False,
        False,
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'warsong-revenant',
        'Warsong Revenant',
        None,
        f'{_NK}/P/2148067728/Warsong-Revenant?awid=1576',
        False,
        False,
    ),

    # SYL-019 Spite-Revenants — no NK listing

    # ── Named heroes ──────────────────────────────────────────────────────────
    (
        'drycha-hamadreth',
        'Drycha Hamadreth',
        None,
        f'{_NK}/P/2148005052/Drycha-Hamadreth?awid=1576',
        False,
        False,
    ),

    # ── Infantry ─────────────────────────────────────────────────────────────
    (
        'tree-revenants',
        'Tree-Revenants',
        None,
        f'{_NK}/P/2147632525/Tree-Revenants?awid=1576',
        False,
        False,
    ),

    # ── Treelord variants (triple kit — share NK listing) ────────────────────
    # ⚠ Triple kit: Spirit of Durthu / Treelord Ancient / Treelord share NK listing
    (
        'spirit-of-durthu',
        'Sylvaneth Treelord Ancient / Durthu Webstore Edition',
        None,
        f'{_NK}/P/2148217290/Sylvaneth-Treelord-Ancient-Durthu-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'treelord-ancient',
        'Sylvaneth Treelord Ancient / Durthu Webstore Edition',
        None,
        f'{_NK}/P/2148217290/Sylvaneth-Treelord-Ancient-Durthu-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'treelord',
        'Sylvaneth Treelord Ancient / Durthu Webstore Edition',
        None,
        f'{_NK}/P/2148217290/Sylvaneth-Treelord-Ancient-Durthu-Webstore-Edition?awid=1576',
        False,
        False,
    ),

    # ── Named character ───────────────────────────────────────────────────────
    (
        'belthanos-first-thorn-of-kurnoth',
        'Belthanos - First Thorn of Kurnoth',
        None,
        f'{_NK}/P/2148112908/Belthanos---First-Thorn-of-Kurnoth?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Sylvaneth products."""

    help = 'Seeds Noble Knight listing URLs and prices for Sylvaneth. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        nk = Retailer.objects.filter(name='Noble Knight Games').first()
        if not nk:
            self.stdout.write(self.style.ERROR('Noble Knight Games retailer not found'))
            return

        seeded = 0
        missing = 0

        for slug, title, price, url, in_stock, not_available in NK_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  [missing] {slug}'))
                missing += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
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
