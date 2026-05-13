"""
Management command: seed_nk_phase2_prices

Seeds Noble Knight Games CurrentPrice entries for phase-2 Emperor's Children
products scraped from nobleknight.com.

Prices and stock status sourced from Octoparse scrape — 2026-04-03.
Affiliate parameter ?awid=1576 appended to all URLs per NK affiliate program.

Only seeds products that exist in our catalog (keyed on slug).
Products not in our catalog (Datasheet Cards, Collector's Edition,
Battleforces, Paint, Army Set) are skipped.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_nk_phase2_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ── Noble Knight phase-2 price data ──────────────────────────────────────────
# (slug, listing_title, price, url, in_stock)
# All URLs include ?awid=1576 affiliate parameter.
# Out of Stock entries use price=None.
NK_PRICES = [
    (
        'codex-emperors-children',
        "Codex - Emperor's Children",
        51.95,
        'https://www.nobleknight.com/P/2148298837/Codex---Emperors-Children?awid=1576',
        True,
    ),
    (
        'emperors-children-flawless-blades',
        'Flawless Blades',
        51.95,
        'https://www.nobleknight.com/P/2148298886/Flawless-Blades?awid=1576',
        True,
    ),
    (
        'emperors-children-lord-exultant',
        'Lord Exultant',
        37.95,
        'https://www.nobleknight.com/P/2148298910/Lord-Exultant?awid=1576',
        True,
    ),
    (
        'fulgrim-daemon-primarch-of-slaanesh',
        'Fulgrim - Demon Prince of Slaanesh',
        150.95,
        'https://www.nobleknight.com/P/2148298848/Fulgrim---Demon-Prince-of-Slaanesh?awid=1576',
        True,
    ),
    (
        'emperors-children-lord-kakophonist',
        'Lord Kakophonist',
        37.95,
        'https://www.nobleknight.com/P/2148394738/Lord-Kakophonist?awid=1576',
        True,
    ),
    (
        'combat-patrol-emperors-children',
        "Combat Patrol - Emperor's Children",
        None,
        'https://www.nobleknight.com/P/2148298716/Combat-Patrol---Emperors-Children?awid=1576',
        False,
    ),
    (
        'emperors-children-tormentors',
        'Tormentors',
        None,
        'https://www.nobleknight.com/P/2148384762/Tormentors?awid=1576',
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for phase-2 Emperor's Children products."""

    help = (
        'Seeds Noble Knight Games CurrentPrice entries for phase-2 EC products. '
        'Sourced from Octoparse scrape 2026-04-03. Affiliate links include ?awid=1576. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        nk = Retailer.objects.filter(name='Noble Knight Games').first()
        if not nk:
            self.stderr.write(self.style.ERROR(
                'Noble Knight Games retailer not found — run populate_products first.'
            ))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for (slug, listing_title, price, url, in_stock) in NK_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  Skipped (product not found): {slug}'
                ))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': False,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
            )
            status = 'Created' if created else 'Updated'
            stock_label = 'In Stock' if in_stock else 'Out of Stock'
            price_label = f'${price:.2f}' if price else 'N/A'
            self.stdout.write(
                self.style.SUCCESS(
                    f'  {status}: {product.name} — {price_label} ({stock_label})'
                )
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nseed_nk_phase2_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
