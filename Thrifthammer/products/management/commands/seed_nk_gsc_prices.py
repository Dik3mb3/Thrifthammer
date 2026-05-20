"""
Management command: seed_nk_gsc_prices

Seeds Noble Knight prices for Genestealer Cults products.

Source: GSC - GW, NK, MM, AMAZON.xlsx (2026-05-19)

NK MATCHES (18 products -- all have NK listings):
  GC-001 to GC-018

Dual-kit / shared NK listings:
  GC-010 / GC-011 — Goliath Rockgrinder / Goliath Truck (same NK listing)

Affiliate tag ?awid=1576 appended to all URLs.
Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_BASE = 'https://www.nobleknight.com'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-genestealer-cults',
        'Codex - Genestealer Cults',
        None,
        f'{_NK_BASE}/P/2148164142/Codex---Genestealer-Cults?awid=1576',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'genestealer-cults-reductus-saboteur',
        'Reductus Saboteur',
        None,
        f'{_NK_BASE}/P/2147979552/Reductus-Saboteur?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-kelermorph',
        'Kelermorph 2021 Edition',
        None,
        f'{_NK_BASE}/P/2148122832/Kelermorph-2021-Edition?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-abominant',
        'Abominant',
        None,
        f'{_NK_BASE}/P/2147956543/Abominant?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-biophagus',
        'Biophagus',
        None,
        f'{_NK_BASE}/P/2147961187/Biophagus?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-nexos',
        'Nexos',
        None,
        f'{_NK_BASE}/P/2147956514/Nexos?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-locus',
        'Locus',
        None,
        f'{_NK_BASE}/P/2148069871/Locus?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-sanctus',
        'Sanctus',
        None,
        f'{_NK_BASE}/P/2147956509/Sanctus?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-acolyte-iconward',
        'Acolyte Iconward',
        None,
        f'{_NK_BASE}/P/2147643549/Acolyte-Iconward?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-benefictus',
        'Benefictus',
        None,
        f'{_NK_BASE}/P/2148203639/Benefictus?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-jackal-alphus',
        'Jackal Alphus',
        None,
        f'{_NK_BASE}/P/2147744315/Jackal-Alphus?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-clamavus',
        'Clamavus',
        None,
        f'{_NK_BASE}/P/2148039067/Clamavus?awid=1576',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'genestealer-cults-atalan-jackals',
        'Atalan Jackals',
        None,
        f'{_NK_BASE}/P/2147744316/Atalan-Jackals?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-hybrid-metamorphs',
        'Neophyte Hybrids',
        None,
        f'{_NK_BASE}/P/2147974210/Neophyte-Hybrids?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-genestealers',
        'Genestealers',
        None,
        f'{_NK_BASE}/P/2148078728/Genestealers?awid=1576',
        False,
        False,
    ),

    # ── Vehicles ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Goliath Rockgrinder / Goliath Truck share same NK listing
    (
        'genestealer-cults-goliath-rockgrinder',
        'Goliath Rockgrinder / Truck',
        None,
        f'{_NK_BASE}/P/2147643547/Goliath-Rockgrinder-Truck?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-goliath-truck',
        'Goliath Rockgrinder / Truck',
        None,
        f'{_NK_BASE}/P/2147643547/Goliath-Rockgrinder-Truck?awid=1576',
        False,
        False,
    ),
    (
        'genestealer-cults-achilles-ridgerunner',
        'Achilles Ridgerunner',
        None,
        f'{_NK_BASE}/P/2147960556/Achilles-Ridgerunner?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Genestealer Cults products."""

    help = "Seeds Noble Knight listing URLs and prices for Genestealer Cults. Idempotent."

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
