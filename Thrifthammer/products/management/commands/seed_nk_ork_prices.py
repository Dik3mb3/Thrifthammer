"""
Management command: seed_nk_ork_prices

Seeds Noble Knight Games CurrentPrice entries for Ork products (phase-1,
phase-2, and phase-3) scraped from nobleknight.com.

Prices and stock status sourced from Octoparse scrape — 2026-04-03.
Affiliate parameter ?awid=1576 appended to all URLs per NK affiliate program.
All listed products are In Stock at NK.

SKIPPED (old/promo editions not in our catalog as separate products):
  - Stormboyz (2009 Edition)             → old edition
  - Ork Boyz (2012 Edition)              → old edition
  - Ork Meganobz (2014 Edition)          → old edition
  - Goff Rocker (2022 Xmas Promo)        → promo, not in catalog
  - Ork Gretchin (2008 Edition)          → old edition
  - Mek Gun (2013 Edition)               → old edition
  - Flash Gitz (2013 Edition)            → old edition
  - Boomdakka Snazzwagon (2018 Edition)  → use current 2022 listing instead
  - Ork Lootas (2018 Edition)            → use current 2021 listing instead
  - Ork Stormboyz (2019 Edition)         → use current 2021 listing instead
  - Da Red Gobbo (2019/2021 Edition)     → promo, not in catalog
  - Ork War Trukk (1998)                 → discontinued, not in catalog
  - Battleforce (2002 Edition)           → old bundle, not in catalog
  - Apocalypse Datasheets - Orks         → accessory, not seeded
  - Datacards - Orks (2021 Edition)      → accessory, not seeded
  - Beast Snagga Data Cards              → accessory, not seeded

SHARED KITS:
  - 'Mek Gun' (GAW50-26) covers all Mek Gunz build options. Applied to all
    four Mek Gunz slugs (Traktor Kannon, Kustom Mega-kannon, Smasha Gun,
    Bubblechukka) at the same URL and price.
  - 'Dakkajet' (GAW50-32) covers all four aircraft build options. Applied to
    all four aircraft slugs (Dakkajet, Burna-Bommer, Blitza-Bommer, Wazbom
    Blastajet) at the same URL and price.
  - 'Ork Morkanaut/Gorkanaut' (GAW50-19) applied to both ork-gorkanaut and
    ork-morkanaut at the same URL and price.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_nk_ork_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ── Noble Knight Ork price data ───────────────────────────────────────────────
# (slug, listing_title, price, url, in_stock)
# All URLs include ?awid=1576 affiliate parameter.
# All listed products are In Stock at NK.
NK_PRICES = [
    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-orks',
        'Codex - Orks',
        51.95,
        'https://www.nobleknight.com/P/2148137125/Codex---Orks?awid=1576',
        True,
    ),
    # ── Characters ────────────────────────────────────────────────────────────
    (
        'ork-ghazghkull-thraka',
        'Ghazghkull Thraka',
        73.95,
        'https://www.nobleknight.com/P/2147847067/Ghazghkull-Thraka?awid=1576',
        True,
    ),
    (
        'ork-boss-snikrot',
        'Boss Snikrot',
        37.95,
        'https://www.nobleknight.com/P/2148064050/Boss-Snikrot?awid=1576',
        True,
    ),
    (
        'ork-mozrog-skragbad',
        'Mozrog Skragbad',
        54.95,
        'https://www.nobleknight.com/P/2147930620/Mozrog-Skragbad?awid=1576',
        True,
    ),
    (
        'ork-zodgrod-wortsnagga',
        'Zodgrod Wortsnagga',
        43.95,
        'https://www.nobleknight.com/P/2147925490/Zodgrod-Wortsnagga?awid=1576',
        True,
    ),
    (
        'ork-warboss-in-mega-armour',
        'Ork Warboss in Mega Armour',
        39.95,
        'https://www.nobleknight.com/P/2147949801/Ork-Warboss-in-Mega-Armour?awid=1576',
        True,
    ),
    (
        'ork-painboss',
        'Painboss',
        39.95,
        'https://www.nobleknight.com/P/2147930624/Painboss?awid=1576',
        True,
    ),
    (
        'ork-painboy',
        'Ork Painboy',
        31.95,
        'https://www.nobleknight.com/P/2147956518/Ork-Painboy?awid=1576',
        True,
    ),
    (
        'ork-big-mek-2024',
        'Big Mek',
        47.95,
        'https://www.nobleknight.com/P/2148164234/Big-Mek?awid=1576',
        True,
    ),
    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'ork-gretchin',
        'Runtherd and Gretchin',
        24.95,
        'https://www.nobleknight.com/P/2147936756/Runtherd-and-Gretchin?awid=1576',
        True,
    ),
    (
        'ork-stormboyz',
        'Ork Stormboyz',
        37.95,
        'https://www.nobleknight.com/P/2147936759/Ork-Stormboyz?awid=1576',
        True,
    ),
    (
        'ork-meganobz',
        'Ork Meganobz',
        62.95,
        'https://www.nobleknight.com/P/2147936364/Ork-Meganobz?awid=1576',
        True,
    ),
    (
        'ork-killa-kans',
        'Killa Kans',
        58.95,
        'https://www.nobleknight.com/P/2147940227/Killa-Kans?awid=1576',
        True,
    ),
    (
        'ork-lootas',
        'Ork Lootas',
        37.95,
        'https://www.nobleknight.com/P/2147930711/Ork-Lootas?awid=1576',
        True,
    ),
    (
        'ork-flash-gitz',
        'Flash Gitz',
        58.95,
        'https://www.nobleknight.com/P/2147939378/Flash-Gitz?awid=1576',
        True,
    ),
    (
        'ork-squighog-boyz',
        'Squighog Boyz',
        59.95,
        'https://www.nobleknight.com/P/2147925489/Squighig-Boyz?awid=1576',
        True,
    ),
    # ── Cavalry / Bikes ───────────────────────────────────────────────────────
    (
        'ork-warbiker-mob',
        'Ork Warbiker Mob',
        51.95,
        'https://www.nobleknight.com/P/2147936778/Ork-Warbiker-Mob?awid=1576',
        True,
    ),
    # ── Vehicles ──────────────────────────────────────────────────────────────
    (
        'ork-trukk',
        'Trukk',
        45.95,
        'https://www.nobleknight.com/P/2147939405/Trukk?awid=1576',
        True,
    ),
    (
        'ork-kill-rig',
        'Kill Rig',
        130.95,
        'https://www.nobleknight.com/P/2147930619/Kill-Rig?awid=1576',
        True,
    ),
    (
        'ork-shokkjump-dragsta',
        'Shokkjump Dragsta',
        54.95,
        'https://www.nobleknight.com/P/2147746094/Shokkjump-Dragsta?awid=1576',
        True,
    ),
    (
        'ork-boomdakka-snazzwagon',
        'Boomdakka Snazzwagon',
        54.95,
        'https://www.nobleknight.com/P/2147966400/Boomdakka-Snazzwagon?awid=1576',
        True,
    ),
    (
        'ork-megatrakk-scrapjet',
        'Megatrakk Scrapjet',
        54.95,
        'https://www.nobleknight.com/P/2147936947/Megatrakk-Scrapjet?awid=1576',
        True,
    ),
    (
        'ork-deffkilla-wartrike',
        'Deffkilla Wartrike',
        54.95,
        'https://www.nobleknight.com/P/2147984601/Deffkilla-Wartrike?awid=1576',
        True,
    ),
    (
        'ork-rukkatrukk-squigbuggy',
        'Rukkatrukk Squigbuggy (2018 Edition)',
        59.95,
        'https://www.nobleknight.com/P/2147737035/Rukkatrukk-Squigbuggy?awid=1576',
        True,
    ),
    # ── Walkers ───────────────────────────────────────────────────────────────
    # NK lists Morkanaut/Gorkanaut as one listing — applied to both slugs
    (
        'ork-gorkanaut',
        'Ork Morkanaut/Gorkanaut',
        135.95,
        'https://www.nobleknight.com/P/2147970139/Ork-Morkanaut-Gorkanaut?awid=1576',
        True,
    ),
    (
        'ork-morkanaut',
        'Ork Morkanaut/Gorkanaut',
        135.95,
        'https://www.nobleknight.com/P/2147970139/Ork-Morkanaut-Gorkanaut?awid=1576',
        True,
    ),
    # ── Artillery — NK 'Mek Gun' (GAW50-26) covers all build options ──────────
    (
        'ork-mek-gunz-traktor-kannon',
        'Mek Gun',
        54.95,
        'https://www.nobleknight.com/P/2147936774/Mek-Gun?awid=1576',
        True,
    ),
    (
        'ork-mek-gunz-kustom-mega-kannon',
        'Mek Gun',
        54.95,
        'https://www.nobleknight.com/P/2147936774/Mek-Gun?awid=1576',
        True,
    ),
    (
        'ork-mek-gunz-smasha-gun',
        'Mek Gun',
        54.95,
        'https://www.nobleknight.com/P/2147936774/Mek-Gun?awid=1576',
        True,
    ),
    (
        'ork-mek-gunz-bubblechukka',
        'Mek Gun',
        54.95,
        'https://www.nobleknight.com/P/2147936774/Mek-Gun?awid=1576',
        True,
    ),
    # ── Aircraft — NK 'Dakkajet' (GAW50-32) covers all four build options ─────
    (
        'ork-dakkajet',
        'Dakkajet',
        81.95,
        'https://www.nobleknight.com/P/2147946038/Dakkajet?awid=1576',
        True,
    ),
    (
        'ork-burna-bommer',
        'Dakkajet',
        81.95,
        'https://www.nobleknight.com/P/2147946038/Dakkajet?awid=1576',
        True,
    ),
    (
        'ork-blitza-bommer',
        'Dakkajet',
        81.95,
        'https://www.nobleknight.com/P/2147946038/Dakkajet?awid=1576',
        True,
    ),
    (
        'ork-wazbom-blastajet',
        'Dakkajet',
        81.95,
        'https://www.nobleknight.com/P/2147946038/Dakkajet?awid=1576',
        True,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Ork products (all phases)."""

    help = (
        'Seeds Noble Knight Games CurrentPrice entries for Ork products. '
        'Sourced from Octoparse scrape 2026-04-03. Affiliate links include ?awid=1576. '
        'All listed products are In Stock at NK. '
        'Shared kits (Mek Gunz, aircraft, Gorkanaut/Morkanaut) seeded across all variant slugs. '
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
            f'\nseed_nk_ork_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
