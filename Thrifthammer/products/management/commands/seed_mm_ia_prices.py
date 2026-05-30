"""
Management command: seed_mm_ia_prices

Seeds Miniature Market prices for Agents of the Imperium products.

Source: Agents - GW, MM, NK.xlsx (2026-05-29)

MM MATCHES (10 products):
  IA-002, IA-004, IA-005, IA-006, IA-007, IA-008, IA-009, IA-010, IA-013, IA-014

NO MM LISTING (4 products):
  IA-001  Combat Patrol: Imperial Agents
  IA-003  Eisenhorn
  IA-011  Lord Inquisitor Kyria Draxus
  IA-012  Rogue Trader Entourage and Voidsmen-at-Arms

Note: IA-002 Inquisitor Kroyle MM URL uses a non-standard path format (no .html extension).

Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com/'

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)

    # ── Inquisitors ───────────────────────────────────────────────────────────
    # IA-001 Combat Patrol: Imperial Agents — no MM listing
    (
        'inquisitor-kroyle',
        '',
        None,
        f'{_MM}Warhammer-40K-Imperial-Agents-Inquisitor-Kroyle-New-Arrival/GW-68-14-2026',
        False,
        False,
    ),
    # IA-003 Eisenhorn — no MM listing
    (
        'inquisitor-coteaz',
        '',
        None,
        f'{_MM}warhammer-40k-imperial-agents-inquisitor-coteaz-gw-57-50.html',
        False,
        False,
    ),
    (
        'inquisitor-greyfax',
        '',
        None,
        f'{_MM}warhammer-40k-imperial-agents-inquisitor-greyfax-gw-52-45-24.html',
        False,
        False,
    ),
    # IA-011 Lord Inquisitor Kyria Draxus — no MM listing

    # ── Navigator ─────────────────────────────────────────────────────────────
    (
        'navigator',
        '',
        None,
        f'{_MM}warhammer-40k-imperial-agents-navigator-gw-57-52.html',
        False,
        False,
    ),

    # ── Assassins ─────────────────────────────────────────────────────────────
    (
        'callidus-assassin',
        '',
        None,
        f'{_MM}warhammer-40k-imperial-agents-callidus-assassin-gw-52-12-24.html',
        False,
        False,
    ),
    (
        'vindicare-assassin',
        '',
        None,
        f'{_MM}warhammer-40k-imperial-agents-vindicare-assassin-gw-52-10-24.html',
        False,
        False,
    ),
    (
        'culexus-assassin',
        '',
        None,
        f'{_MM}warhammer-40k-imperial-agents-culexus-assassin-gw-52-11-24.html',
        False,
        False,
    ),
    (
        'eversor-assassin',
        '',
        None,
        f'{_MM}warhammer-40k-imperial-agents-eversor-assassin-gw-52-13-24.html',
        False,
        False,
    ),

    # IA-012 Rogue Trader Entourage and Voidsmen-at-Arms — no MM listing

    # ── Units ─────────────────────────────────────────────────────────────────
    (
        'inquisitorial-agents',
        '',
        None,
        f'{_MM}warhammer-40k-imperial-agents-inquisitorial-agents-gw-68-13.html',
        False,
        False,
    ),

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-imperial-agents',
        '',
        None,
        f'{_MM}warhammer-40k-codex-imperial-agents-gw-68-28.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Agents of the Imperium products."""

    help = 'Seeds Miniature Market listing URLs and prices for Agents of the Imperium. Idempotent.'

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
