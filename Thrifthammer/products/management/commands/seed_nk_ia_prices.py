"""
Management command: seed_nk_ia_prices

Seeds Noble Knight prices for Agents of the Imperium products.

Source: Agents - GW, MM, NK.xlsx (2026-05-29)

NK MATCHES (13 products):
  IA-001, IA-002, IA-003, IA-004, IA-005, IA-006, IA-007,
  IA-008, IA-009, IA-010, IA-011, IA-013, IA-014

NO NK LISTING (1 product):
  IA-012  Rogue Trader Entourage and Voidsmen-at-Arms

Note: IA-011 Lord Inquisitor Kyria Draxus — NK URL slug reads "Inquisitor-Draxis"
(typo on NK side); confirmed correct listing, use as-is.

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

    # ── Combat Patrol ─────────────────────────────────────────────────────────
    (
        'combat-patrol-imperial-agents',
        'Combat Patrol - Imperial Agents',
        None,
        f'{_NK}/P/2148183372/Combat-Patrol---Imperial-Agents?awid=1576',
        False,
        False,
    ),

    # ── Inquisitors ───────────────────────────────────────────────────────────
    (
        'inquisitor-kroyle',
        'Inquisitor Kroyle',
        None,
        f'{_NK}/P/2148457461/Inquisitor-Kroyle?awid=1576',
        False,
        False,
    ),
    (
        'eisenhorn',
        'Eisenhorn - Webstore Edition',
        None,
        f'{_NK}/P/2148196085/Eisenhorn-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'inquisitor-coteaz',
        'Inquisitor Coteaz',
        None,
        f'{_NK}/P/2148213942/Inquisitor-Coteaz?awid=1576',
        False,
        False,
    ),
    (
        'inquisitor-greyfax',
        'Inquisitor Greyfax',
        None,
        f'{_NK}/P/2148183395/Inquisitor-Greyfax?awid=1576',
        False,
        False,
    ),
    (
        'lord-inquisitor-kyria-draxus',
        'Inquisitor Draxis',
        None,
        f'{_NK}/P/2148183433/Inquisitor-Draxis?awid=1576',
        False,
        False,
    ),

    # ── Navigator ─────────────────────────────────────────────────────────────
    (
        'navigator',
        'Navigator',
        None,
        f'{_NK}/P/2148183391/Navigator?awid=1576',
        False,
        False,
    ),

    # ── Assassins ─────────────────────────────────────────────────────────────
    (
        'callidus-assassin',
        'Callidus Assassin',
        None,
        f'{_NK}/P/2148183413/Callidus-Assassin?awid=1576',
        False,
        False,
    ),
    (
        'vindicare-assassin',
        'Vindicare Assassin',
        None,
        f'{_NK}/P/2148183409/Vindicare-Assassin?awid=1576',
        False,
        False,
    ),
    (
        'culexus-assassin',
        'Culexus Assassin',
        None,
        f'{_NK}/P/2148183421/Culexus-Assassin?awid=1576',
        False,
        False,
    ),
    (
        'eversor-assassin',
        'Eversor Assassin',
        None,
        f'{_NK}/P/2148183388/Eversor-Assassin?awid=1576',
        False,
        False,
    ),

    # IA-012 Rogue Trader Entourage and Voidsmen-at-Arms — no NK listing

    # ── Units ─────────────────────────────────────────────────────────────────
    (
        'inquisitorial-agents',
        'Inquisitorial Agents',
        None,
        f'{_NK}/P/2148183357/Inquisitorial-Agents?awid=1576',
        False,
        False,
    ),

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-imperial-agents',
        'Codex - Imperial Agents',
        None,
        f'{_NK}/P/2148183339/Codex---Imperial-Agents?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Agents of the Imperium products."""

    help = 'Seeds Noble Knight listing URLs and prices for Agents of the Imperium. Idempotent.'

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
