"""
Management command: seed_mm_gsc_prices

Seeds Miniature Market prices for Genestealer Cults products.

Source: GSC - GW, NK, MM, AMAZON.xlsx (2026-05-19)

MM MATCHES (16 products with MM URLs):
  GC-001 to GC-011, GC-013 to GC-018

NO MM LISTING (2 products):
  GC-012 (Acolyte Iconward)
  GC-013 (Hybrid Metamorphs) -- source spreadsheet had a GW URL in the MM column

Dual-kit / shared MM URLs:
  GC-010 / GC-011 — Goliath Rockgrinder / Goliath Truck (gw-51-53)

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
        'codex-genestealer-cults',
        '',
        None,
        f'{_MM}warhammer-40k-codex-genestealer-cults-10th-edition-gw-38-01.html',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'genestealer-cults-reductus-saboteur',
        '',
        None,
        f'{_MM}gw-51-68.html',
        False,
        False,
    ),
    (
        'genestealer-cults-kelermorph',
        '',
        None,
        f'{_MM}gw-51-67.html',
        False,
        False,
    ),
    (
        'genestealer-cults-abominant',
        '',
        None,
        f'{_MM}gw-51-59.html',
        False,
        False,
    ),
    (
        'genestealer-cults-biophagus',
        '',
        None,
        f'{_MM}gw-51-44.html',
        False,
        False,
    ),
    (
        'genestealer-cults-nexos',
        '',
        None,
        f'{_MM}gw-51-48.html',
        False,
        False,
    ),
    (
        'genestealer-cults-locus',
        '',
        None,
        f'{_MM}gw-51-46.html',
        False,
        False,
    ),
    (
        'genestealer-cults-sanctus',
        '',
        None,
        f'{_MM}gw-51-49.html',
        False,
        False,
    ),
    # GC-012 Acolyte Iconward — no MM listing
    (
        'genestealer-cults-benefictus',
        '',
        None,
        f'{_MM}warhammer-40k-genestealer-cults-benefictus-gw-51-70.html',
        False,
        False,
    ),
    (
        'genestealer-cults-jackal-alphus',
        '',
        None,
        f'{_MM}gw-51-63.html',
        False,
        False,
    ),
    (
        'genestealer-cults-clamavus',
        '',
        None,
        f'{_MM}gw-51-45.html',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'genestealer-cults-atalan-jackals',
        '',
        None,
        f'{_MM}gw-51-62.html',
        False,
        False,
    ),
    # GC-013 Hybrid Metamorphs — spreadsheet MM column had a GW URL (data entry error); no MM URL
    (
        'genestealer-cults-genestealers',
        '',
        None,
        f'{_MM}warhammer-40k-tyranids-genestealers-gw-51-06-2023.html',
        False,
        False,
    ),

    # ── Vehicles ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Goliath Rockgrinder / Goliath Truck share same MM URL
    (
        'genestealer-cults-goliath-rockgrinder',
        '',
        None,
        f'{_MM}gw-51-53.html',
        False,
        False,
    ),
    (
        'genestealer-cults-goliath-truck',
        '',
        None,
        f'{_MM}gw-51-53.html',
        False,
        False,
    ),
    (
        'genestealer-cults-achilles-ridgerunner',
        '',
        None,
        f'{_MM}gw-51-61.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Genestealer Cults products."""

    help = "Seeds Miniature Market listing URLs and prices for Genestealer Cults. Idempotent."

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
