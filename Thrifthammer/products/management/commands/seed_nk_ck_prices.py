"""
Management command: seed_nk_ck_prices

Seeds Noble Knight prices for Chaos Knights products.

Source: Chaos Knights - GW, NK, MM.xlsx (2026-05-29)

NK MATCHES (13 products):
  CK-001, CK-002, CK-003, CK-004, CK-005, CK-006, CK-007,
  CK-008, CK-009, CK-010, CK-011, CK-012, CK-015

NO NK LISTING (5 products):
  CK-013, CK-014, CK-016, CK-017, CK-018

Shared NK listings (same physical kit):
  CK-003 / CK-004  — War Dog Huntsmen / Executioners  (Knight-Armigers-Warglaives)
  CK-005 / CK-006 / CK-007  — War Dog Stalkers / Brigands / Karnivores  (War-Dogs)

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

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-chaos-knights',
        'Codex - Chaos Knights',
        None,
        f'{_NK}/P/2148314680/Codex---Chaos-Knights?awid=1576',
        False,
        False,
    ),

    # ── Knights (large) ───────────────────────────────────────────────────────
    (
        'chaos-knight-ruinator',
        'Knight Ruinator',
        None,
        f'{_NK}/P/2148314697/Knight-Ruinator?awid=1576',
        False,
        False,
    ),
    (
        'chaos-knight-tyrant',
        'Knight Castellan',
        None,
        f'{_NK}/P/2147705956/Knight-Castellan?awid=1576',
        False,
        False,
    ),
    (
        'chaos-knight-despoiler',
        'Knight Valiant',
        None,
        f'{_NK}/P/2147705944/Knight-Valiant?awid=1576',
        False,
        False,
    ),
    (
        'chaos-knight-questoris',
        'Knight Questoris',
        None,
        f'{_NK}/P/2148347536/Knight-Questoris?awid=1576',
        False,
        False,
    ),

    # ── War Dogs ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Huntsmen / Executioners share same NK listing
    (
        'chaos-war-dog-huntsmen',
        'Knight Armigers Warglaives',
        None,
        f'{_NK}/P/2147975564/Knight-Armigers-Warglaives?awid=1576',
        False,
        False,
    ),
    (
        'chaos-war-dog-executioners',
        'Knight Armigers Warglaives',
        None,
        f'{_NK}/P/2147975564/Knight-Armigers-Warglaives?awid=1576',
        False,
        False,
    ),
    # ⚠ Triple kit: Stalkers / Brigands / Karnivores share same NK listing
    (
        'chaos-war-dog-stalkers',
        'War Dogs',
        None,
        f'{_NK}/P/2147980635/War-Dogs?awid=1576',
        False,
        False,
    ),
    (
        'chaos-war-dog-brigands',
        'War Dogs',
        None,
        f'{_NK}/P/2147980635/War-Dogs?awid=1576',
        False,
        False,
    ),
    (
        'chaos-war-dog-karnivores',
        'War Dogs',
        None,
        f'{_NK}/P/2147980635/War-Dogs?awid=1576',
        False,
        False,
    ),

    # ── Cerastus Knights ──────────────────────────────────────────────────────
    (
        'chaos-cerastus-knight-acheron',
        'Cerastus Knight Acheron',
        None,
        f'{_NK}/P/2148082536/Cerastus-Knight-Acheron?awid=1576',
        False,
        False,
    ),
    (
        'chaos-cerastus-knight-castigator',
        'Cerastus Knight Castigator',
        None,
        f'{_NK}/P/2148082533/Cerastus-Knight-Castigator?awid=1576',
        False,
        False,
    ),
    (
        'chaos-cerastus-knight-lancer',
        'Cerastus Knight Lancer',
        None,
        f'{_NK}/P/2148071962/Cerastus-Knight-Lancer?awid=1576',
        False,
        False,
    ),
    # CK-013 Chaos Questoris Knight Magaera  — no NK listing
    # CK-014 Chaos Questoris Knight Styrix   — no NK listing
    # CK-016 Chaos Acastus Knight Asterius   — no NK listing
    # CK-017 Chaos Acastus Knight Porphyrion — no NK listing
    # CK-018 Chaos Cerastus Knight Atrapos   — no NK listing
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Chaos Knights products."""

    help = 'Seeds Noble Knight listing URLs and prices for Chaos Knights. Idempotent.'

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
