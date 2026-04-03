"""
Management command: seed_mm_ork_prices

Seeds Miniature Market CurrentPrice entries for Ork products (phase-1 and phase-2)
scraped from miniaturemarket.com.

Prices and stock status sourced from Octoparse scrape — 2026-04-03.
Only seeds products that exist in our catalog (keyed on slug).

SKIPPED (not in catalog):
  - Kill Team: Ork Kommandos         → Kill Team product, not in Ork faction catalog
  - Ork Gorkanaut                    → not in catalog
  - Ork Warbiker Mob                 → not in catalog
  - Orks Boyz (2022 kit, gw-50-57)  → user confirmed skip (duplicate of Ork Boyz)
  - Orks Kommandos                   → not in catalog
  - Datacards: Orks                  → accessory, not seeded
  - Necron Ghost Ark                 → wrong faction
  - Arks of Omen products            → not Ork products

AIRCRAFT (gw-50-32.html):
  MM lists Wazbom Blastajet/Dakkajet/Burna-Bommer/Blitza-Bommer as one listing at $72.99.
  All four products share the same MM URL and price (they are the same physical dual-build kit).

UNCERTAIN (included with best match):
  - 'Orks - Big Mek' (gw-50-68) at $44.99 → matched to ork-big-mek-shokk-attack-gun.
    MM title omits "Shokk Attack Gun" but it is the same GW product.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_mm_ork_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ── Miniature Market Ork price data ──────────────────────────────────────────
# (slug, listing_title, price, url, in_stock)
# Sourced from Octoparse scrape 2026-04-03.
# Out of Stock items retain their listed price (price is shown on MM page).
# Zodgrod is In Stock (clearance); all others are Out of Stock.
MM_PRICES = [
    # ── Phase-1 products ──────────────────────────────────────────────────────
    (
        'ork-warboss-in-mega-armour',
        'Warhammer 40K: Orks - Ork Warboss In Mega Armour',
        35.99,
        'https://www.miniaturemarket.com/gw-50-56.html',
        False,
    ),
    (
        'ork-stormboyz',
        'Warhammer 40K: Ork Stormboyz',
        33.99,
        'https://www.miniaturemarket.com/gw-50-13.html',
        False,
    ),
    (
        'ork-meganobz',
        'Warhammer 40K: Ork Meganobz',
        59.99,
        'https://www.miniaturemarket.com/gw-50-08.html',
        False,
    ),
    (
        'ork-boyz',
        'Warhammer 40K: Ork Boyz',
        38.99,
        'https://www.miniaturemarket.com/gw-50-10.html',
        False,
    ),
    (
        'ork-nobz',
        'Warhammer 40K: Ork Nobz',
        33.99,
        'https://www.miniaturemarket.com/gw-50-12.html',
        False,
    ),
    (
        'ork-gretchin',
        'Warhammer 40K: Ork Gretchin',
        22.99,
        'https://www.miniaturemarket.com/gw-50-16.html',
        False,
    ),
    (
        'ork-lootas',
        'Warhammer 40K: Ork Lootas/Burnas',
        33.99,
        'https://www.miniaturemarket.com/gw-50-22.html',
        False,
    ),
    (
        'ork-painboy',
        'Warhammer 40K: Ork Painboy',
        29.99,
        'https://www.miniaturemarket.com/gw-50-25.html',
        False,
    ),
    (
        'ork-trukk',
        'Warhammer 40K: Orks - Trukk',
        50.99,
        'https://www.miniaturemarket.com/gw-50-09.html',
        False,
    ),
    (
        'ork-killa-kans',
        'Warhammer 40K: Ork Killa Kans',
        53.99,
        'https://www.miniaturemarket.com/gw-50-17.html',
        False,
    ),
    (
        'ork-flash-gitz',
        'Warhammer 40K: Ork Flash Gitz',
        53.99,
        'https://www.miniaturemarket.com/gw-50-24.html',
        False,
    ),
    (
        'ork-battlewagon',
        'Warhammer 40K: Orks - Battlewagon',
        106.99,
        'https://www.miniaturemarket.com/gw-50-20-2021.html',
        False,
    ),
    # ── Phase-2 products ──────────────────────────────────────────────────────
    (
        'ork-beastboss',
        'Warhammer 40K: Orks - Beastboss',
        35.99,
        'https://www.miniaturemarket.com/gw-50-53.html',
        False,
    ),
    (
        'ork-painboss',
        'Warhammer 40K: Orks - Painboss',
        35.99,
        'https://www.miniaturemarket.com/gw-50-49.html',
        False,
    ),
    (
        'ork-deffkoptas',
        'Warhammer 40K: Orks - Deffkoptas',
        55.99,
        'https://www.miniaturemarket.com/gw-50-58.html',
        False,
    ),
    (
        'ork-boomdakka-snazzwagon',
        'Warhammer 40K: Orks - Boomdakka Snazzwagon',
        51.00,
        'https://www.miniaturemarket.com/gw-50-39.html',
        False,
    ),
    (
        'ork-deffkilla-wartrike',
        'Warhammer 40K: Orks - Deffkilla Wartrike',
        51.00,
        'https://www.miniaturemarket.com/gw-50-38.html',
        False,
    ),
    (
        'ork-megatrakk-scrapjet',
        'Warhammer 40K: Orks - Megatrakk Scrapjet',
        51.00,
        'https://www.miniaturemarket.com/gw-50-36.html',
        False,
    ),
    (
        'ork-rukkatrukk-squigbuggy',
        'Warhammer 40K: Orks - Rukkatrukk Squigbuggy',
        51.00,
        'https://www.miniaturemarket.com/gw-50-35.html',
        False,
    ),
    (
        'ork-shokkjump-dragsta',
        'Warhammer 40K: Orks - Shokkjump Dragsta',
        51.00,
        'https://www.miniaturemarket.com/gw-50-34.html',
        False,
    ),
    (
        'ork-kustom-boosta-blasta',
        'Warhammer 40K: Orks - Kustom Boosta-Blasta',
        51.00,
        'https://www.miniaturemarket.com/gw-50-37.html',
        False,
    ),
    (
        'ork-boss-snikrot',
        'Warhammer 40K: Orks - Boss Snikrot',
        35.99,
        'https://www.miniaturemarket.com/warhammer-40k-orks-boss-snikrot-gw-50-42-2023.html',
        False,
    ),
    (
        'ork-ghazghkull-thraka',
        'Warhammer 40K: Orks - Ghazghkull Thraka',
        67.99,
        'https://www.miniaturemarket.com/gw-50-29.html',
        False,
    ),
    (
        'ork-squighog-boyz',
        'Warhammer 40K: Orks - Squighog Boyz',
        55.99,
        'https://www.miniaturemarket.com/gw-50-54.html',
        False,
    ),
    (
        'ork-kill-rig',
        'Warhammer 40K: Orks - Kill Rig',
        123.99,
        'https://www.miniaturemarket.com/gw-50-46.html',
        False,
    ),
    (
        'ork-mozrog-skragbad',
        'Warhammer 40K: Orks - Mozrog Skragbad',
        51.00,
        'https://www.miniaturemarket.com/gw-50-55.html',
        False,
    ),
    (
        'ork-zodgrod-wortsnagga',
        'Warhammer 40K: Orks - Zodgrod Wortsnagga (Clearance)',
        38.99,
        'https://www.miniaturemarket.com/gw-50-50.html',
        True,
    ),
    (
        'codex-orks',
        'Warhammer 40K: Codex - Orks (10th Edition)',
        51.00,
        'https://www.miniaturemarket.com/warhammer-40k-codex-orks-10th-edition-gw-50-01-2024.html',
        False,
    ),
    (
        'ork-beast-snagga-boyz',
        'Warhammer 40K: Orks - Beast Snagga Boyz',
        51.00,
        'https://www.miniaturemarket.com/gw-50-51.html',
        False,
    ),
    # ── Big Mek (matched to ork-big-mek-shokk-attack-gun) ────────────────────
    (
        'ork-big-mek-shokk-attack-gun',
        'Warhammer 40K: Orks - Big Mek',
        44.99,
        'https://www.miniaturemarket.com/warhammer-40k-orks-big-mek-gw-50-68.html',
        False,
    ),
    # ── Aircraft — one MM listing covers all four build options ───────────────
    # MM SKU gw-50-32 lists all four aircraft variants at $72.99.
    (
        'ork-wazbom-blastajet',
        'Warhammer 40K: Ork Wazbom Blastajet/Dakkajet/Burna-Bommer/Blitza-Bommer',
        72.99,
        'https://www.miniaturemarket.com/gw-50-32.html',
        False,
    ),
    (
        'ork-dakkajet',
        'Warhammer 40K: Ork Wazbom Blastajet/Dakkajet/Burna-Bommer/Blitza-Bommer',
        72.99,
        'https://www.miniaturemarket.com/gw-50-32.html',
        False,
    ),
    (
        'ork-burna-bommer',
        'Warhammer 40K: Ork Wazbom Blastajet/Dakkajet/Burna-Bommer/Blitza-Bommer',
        72.99,
        'https://www.miniaturemarket.com/gw-50-32.html',
        False,
    ),
    (
        'ork-blitza-bommer',
        'Warhammer 40K: Ork Wazbom Blastajet/Dakkajet/Burna-Bommer/Blitza-Bommer',
        72.99,
        'https://www.miniaturemarket.com/gw-50-32.html',
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Ork products (phase-1 and phase-2)."""

    help = (
        'Seeds Miniature Market CurrentPrice entries for Ork products. '
        'Sourced from Octoparse scrape 2026-04-03. '
        'Zodgrod Wortsnagga is in stock (clearance); all others are out of stock. '
        'Aircraft variants (Wazbom/Dakkajet/Burna-Bommer/Blitza-Bommer) share one MM listing. '
        'Idempotent.'
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
            f'\nseed_mm_ork_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
