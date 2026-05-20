"""
Management command: seed_mm_admech_prices

Seeds Miniature Market prices for Adeptus Mechanicus products.

Source: Admech - GW,NK,MM, AMAZON.xlsx (2026-05-19)

MM MATCHES (23 products with MM URLs):
  MC-001 to MC-020, MC-021, MC-023, MC-024

NO MM LISTING (2 products):
  MC-022 (Tech-Priest Enginseer), MC-025 (Codex: Adeptus Mechanicus)

Dual-kit / shared MM URLs:
  MC-001 / MC-002 / MC-003 — Archaeopter (gw-59-22)
  MC-010 / MC-011          — Pteraxii (gw-59-23)
  MC-012 / MC-013          — Serberys (gw-59-24)
  MC-014 / MC-015          — Sicarians (gw-59-11)
  MC-017 / MC-018          — Skorpius (gw-59-20)

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

    # ── Archaeopter triple kit (shared URL) ───────────────────────────────────
    (
        'adeptus-mechanicus-archaeopter-fusilave',
        '',
        None,
        f'{_MM}gw-59-22.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-archaeopter-stratoraptor',
        '',
        None,
        f'{_MM}gw-59-22.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-archaeopter-transvector',
        '',
        None,
        f'{_MM}gw-59-22.html',
        False,
        False,
    ),

    # ── Kill Team ─────────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-battleclade',
        '',
        None,
        f'{_MM}kill-team-battleclade-gw-103-97.html',
        False,
        False,
    ),

    # ── Named characters ──────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-belisarius-cawl',
        '',
        None,
        f'{_MM}gw-59-17.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-thulia-ghuld',
        '',
        None,
        f'{_MM}Warhammer-40K-Adeptus-Mechanicus-Thulia-Ghuld-New-Arrival/GW-59-33-2026',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-fulgurite-electro-priests',
        '',
        None,
        f'{_MM}gw-59-15.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-hastarii',
        '',
        None,
        f'{_MM}Warhammer-40K-Adeptus-Mechanicus-Hastarii-New-Arrival/GW-59-34-2026',
        False,
        False,
    ),
    # ⚠ Dual kit: Pteraxii Skystalkers / Sterylizors share same MM URL
    (
        'adeptus-mechanicus-pteraxii-skystalkers',
        '',
        None,
        f'{_MM}gw-59-23.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-pteraxii-sterylizors',
        '',
        None,
        f'{_MM}gw-59-23.html',
        False,
        False,
    ),
    # ⚠ Dual kit: Serberys Raiders / Sulphurhounds share same MM URL
    (
        'adeptus-mechanicus-serberys-raiders',
        '',
        None,
        f'{_MM}gw-59-24.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-serberys-sulphurhounds',
        '',
        None,
        f'{_MM}gw-59-24.html',
        False,
        False,
    ),
    # ⚠ Dual kit: Sicarian Infiltrators / Ruststalkers share same MM URL
    (
        'adeptus-mechanicus-sicarian-infiltrators',
        '',
        None,
        f'{_MM}gw-59-11.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-sicarian-ruststalkers',
        '',
        None,
        f'{_MM}gw-59-11.html',
        False,
        False,
    ),

    # ── Vehicles / Walkers ────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-kastelan-robots',
        '',
        None,
        f'{_MM}gw-59-16.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-kataphron-breachers',
        '',
        None,
        f'{_MM}gw-59-14.html',
        False,
        False,
    ),
    # ⚠ Dual kit: Skorpius Disintegrator / Dunerider share same MM URL
    (
        'adeptus-mechanicus-skorpius-disintegrator',
        '',
        None,
        f'{_MM}gw-59-20.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-skorpius-dunerider',
        '',
        None,
        f'{_MM}gw-59-20.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-sydonian-dragoon',
        '',
        None,
        f'{_MM}gw-59-12.html',
        False,
        False,
    ),

    # ── Leaders / HQ ─────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-skitarii-marshal',
        '',
        None,
        f'{_MM}gw-59-26.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-sydonian-skatros',
        '',
        None,
        f'{_MM}warhammer-40k-adeptus-mechanicus-sydonian-skatros-gw-59-31.html',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-technoarcheologist',
        '',
        None,
        f'{_MM}gw-59-30.html',
        False,
        False,
    ),
    # MC-022 Tech-Priest Enginseer — no MM listing
    (
        'adeptus-mechanicus-tech-priest-manipulus',
        '',
        None,
        f'{_MM}gw-59-21.html',
        False,
        False,
    ),
    # MC-025 Codex: Adeptus Mechanicus — no MM listing
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Adeptus Mechanicus products."""

    help = "Seeds Miniature Market listing URLs and prices for Adeptus Mechanicus. Idempotent."

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
