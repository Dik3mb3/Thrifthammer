"""
Management command: seed_mm_ck_prices

Seeds Miniature Market prices for Chaos Knights products.

Source: Chaos Knights - GW, NK, MM.xlsx (2026-05-29)

MM MATCHES (11 products):
  CK-001, CK-002, CK-003, CK-004, CK-005, CK-006, CK-007,
  CK-008, CK-009, CK-010, CK-015

NO MM LISTING (7 products):
  CK-011, CK-012, CK-013, CK-014, CK-016, CK-017, CK-018

Shared MM URLs (same physical kit):
  CK-003 / CK-004         — War Dog Huntsmen / Executioners  (gw-54-20)
  CK-005 / CK-006 / CK-007 — War Dog Stalkers / Brigands / Karnivores  (gw-43-64-2022)
  CK-008 / CK-009         — Knight Tyrant / Despoiler  (gw-54-21)

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

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-chaos-knights',
        '',
        None,
        f'{_MM}warhammer-40k-codex-chaos-knights-gw-43-18.html',
        False,
        False,
    ),

    # ── Knights (large) ───────────────────────────────────────────────────────
    (
        'chaos-knight-ruinator',
        '',
        None,
        f'{_MM}warhammer-40k-chaos-knights-knight-ruinator-gw-43-102.html',
        False,
        False,
    ),
    # ⚠ Dual kit: Knight Tyrant / Despoiler share same MM URL
    (
        'chaos-knight-tyrant',
        '',
        None,
        f'{_MM}gw-54-21.html',
        False,
        False,
    ),
    (
        'chaos-knight-despoiler',
        '',
        None,
        f'{_MM}gw-54-21.html',
        False,
        False,
    ),
    (
        'chaos-knight-questoris',
        '',
        None,
        f'{_MM}Warhammer-40K-Imperial-Knights-Knight-Questoris/GW-54-22',
        False,
        False,
    ),

    # ── War Dogs ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Huntsmen / Executioners share same MM URL
    (
        'chaos-war-dog-huntsmen',
        '',
        None,
        f'{_MM}gw-54-20.html',
        False,
        False,
    ),
    (
        'chaos-war-dog-executioners',
        '',
        None,
        f'{_MM}gw-54-20.html',
        False,
        False,
    ),
    # ⚠ Triple kit: Stalkers / Brigands / Karnivores share same MM URL
    (
        'chaos-war-dog-stalkers',
        '',
        None,
        f'{_MM}gw-43-64-2022.html',
        False,
        False,
    ),
    (
        'chaos-war-dog-brigands',
        '',
        None,
        f'{_MM}gw-43-64-2022.html',
        False,
        False,
    ),
    (
        'chaos-war-dog-karnivores',
        '',
        None,
        f'{_MM}gw-43-64-2022.html',
        False,
        False,
    ),

    # ── Cerastus Knights ──────────────────────────────────────────────────────
    (
        'chaos-cerastus-knight-lancer',
        '',
        None,
        f'{_MM}warhammer-horus-heresy-cerastus-knight-lancer-gw-31-06.html',
        False,
        False,
    ),
    # CK-011 Chaos Cerastus Knight Acheron    — no MM listing
    # CK-012 Chaos Cerastus Knight Castigator — no MM listing
    # CK-013 Chaos Questoris Knight Magaera   — no MM listing
    # CK-014 Chaos Questoris Knight Styrix    — no MM listing
    # CK-016 Chaos Acastus Knight Asterius    — no MM listing
    # CK-017 Chaos Acastus Knight Porphyrion  — no MM listing
    # CK-018 Chaos Cerastus Knight Atrapos    — no MM listing
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Chaos Knights products."""

    help = 'Seeds Miniature Market listing URLs and prices for Chaos Knights. Idempotent.'

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
