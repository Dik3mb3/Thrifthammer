"""
Management command: seed_mm_phase2_prices

Seeds Miniature Market CurrentPrice entries for phase-2 Emperor's Children
products scraped from miniaturemarket.com.

Prices and stock status sourced from Octoparse scrape — 2026-04-03.
Only seeds products that exist in our catalog (keyed on slug).
Products not in our catalog (Battleforce, Dice, Paint, Datasheet Cards) are skipped.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_mm_phase2_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ── Miniature Market phase-2 price data ──────────────────────────────────────
# (slug, listing_title, price, url, in_stock)
MM_PRICES = [
    (
        'fulgrim-daemon-primarch-of-slaanesh',
        "Warhammer 40K: Emperor's Children - Fulgrim",
        144.99,
        'https://www.miniaturemarket.com/warhammer-40k-emperors-children-fulgrim-gw-37-06.html',
        True,
    ),
    (
        'emperors-children-tormentors',
        "Warhammer 40K: Emperor's Children - Tormentors",
        59.99,
        'https://www.miniaturemarket.com/warhammer-40k-emperors-children-tormentors-gw-37-11.html',
        False,
    ),
    (
        'codex-emperors-children',
        "Warhammer 40K: Codex - Emperor's Children",
        51.00,
        'https://www.miniaturemarket.com/warhammer-40k-codex-emperors-children-gw-37-02.html',
        True,
    ),
    (
        'emperors-children-flawless-blades',
        "Warhammer 40K: Emperor's Children - Flawless Blades",
        51.00,
        'https://www.miniaturemarket.com/warhammer-40k-emperors-children-flawless-blades-gw-37-07.html',
        False,
    ),
    (
        'emperors-children-noise-marines',
        "Warhammer 40K: Emperor's Children - Noise Marines",
        55.99,
        'https://www.miniaturemarket.com/warhammer-40k-emperors-children-noise-marines-gw-37-10.html',
        False,
    ),
    (
        'lucius-the-eternal',
        "Warhammer 40K: Emperor's Children - Lucius the Eternal",
        38.99,
        'https://www.miniaturemarket.com/warhammer-40k-emperors-children-lucius-eternal-gw-37-08.html',
        False,
    ),
    (
        'emperors-children-lord-kakophonist',
        "Warhammer 40K: Emperor's Children - Lord Kakophonist",
        34.00,
        'https://www.miniaturemarket.com/warhammer-40k-emperors-children-lord-kakophonist-gw-37-05.html',
        False,
    ),
    (
        'emperors-children-lord-exultant',
        "Warhammer 40K: Emperor's Children - Lord Exultant",
        35.99,
        'https://www.miniaturemarket.com/warhammer-40k-emperors-children-lord-exultant-gw-37-09.html',
        True,
    ),
    (
        'combat-patrol-emperors-children',
        "Warhammer 40k: Combat Patrol - Emperor's Children",
        144.99,
        'https://www.miniaturemarket.com/warhammer-40k-combat-patrol-emperors-children-gw-73-371.html',
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for phase-2 Emperor's Children products."""

    help = (
        'Seeds Miniature Market CurrentPrice entries for phase-2 EC products. '
        'Sourced from Octoparse scrape 2026-04-03. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stderr.write(self.style.ERROR(
                'Miniature Market retailer not found — run populate_products first.'
            ))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for (slug, listing_title, price, url, in_stock) in MM_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  Skipped (product not found): {slug}'
                ))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
                defaults={
                    'price': price,
                    'url': url,
                    'listing_title': listing_title,
                    'in_stock': in_stock,
                    'not_available': False,
                },
            )
            status = 'Created' if created else 'Updated'
            stock_label = 'In Stock' if in_stock else 'Out of Stock'
            self.stdout.write(
                self.style.SUCCESS(
                    f'  {status}: {product.name} — ${price:.2f} ({stock_label})'
                )
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nseed_mm_phase2_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
