"""
Management command: seed_nk_admech_prices

Seeds Noble Knight prices for Adeptus Mechanicus products.

Source: Admech - GW,NK,MM, AMAZON.xlsx (2026-05-19)

NK MATCHES (25 products — all have NK listings):
  MC-001 to MC-025

Dual-kit / shared NK listings:
  MC-001 / MC-002 / MC-003 — Archaeopter (same NK listing)
  MC-010 / MC-011          — Pteraxii (same NK listing)
  MC-012 / MC-013          — Serberys (same NK listing)
  MC-014 / MC-015          — Sicarians (same NK listing)
  MC-017 / MC-018          — Skorpius (same NK listing)

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

    # ── Archaeopter triple kit ────────────────────────────────────────────────
    (
        'adeptus-mechanicus-archaeopter-fusilave',
        'Archaeopter',
        None,
        f'{_NK_BASE}/P/2147936598/Archaeopter?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-archaeopter-stratoraptor',
        'Archaeopter',
        None,
        f'{_NK_BASE}/P/2147936598/Archaeopter?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-archaeopter-transvector',
        'Archaeopter',
        None,
        f'{_NK_BASE}/P/2147936598/Archaeopter?awid=1576',
        False,
        False,
    ),

    # ── Kill Team ─────────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-battleclade',
        'Battleclade',
        None,
        f'{_NK_BASE}/P/2148344136/Battleclade?awid=1576',
        False,
        False,
    ),

    # ── Named characters ──────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-belisarius-cawl',
        'Belisarius Cawl',
        None,
        f'{_NK_BASE}/P/2147994151/Belisarius-Cawl?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-thulia-ghuld',
        'Thulia Ghuld',
        None,
        f'{_NK_BASE}/P/2148448267/Thulia-Ghuld?awid=1576',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-fulgurite-electro-priests',
        'Electro-Priests',
        None,
        f'{_NK_BASE}/P/2147924593/Electro-Priests?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-hastarii',
        'Hastarii',
        None,
        f'{_NK_BASE}/P/2148448264/Hastarii?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Pteraxii Skystalkers / Sterylizors share same NK listing
    (
        'adeptus-mechanicus-pteraxii-skystalkers',
        'Pteraxii',
        None,
        f'{_NK_BASE}/P/2148411297/Pteraxii?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-pteraxii-sterylizors',
        'Pteraxii',
        None,
        f'{_NK_BASE}/P/2148411297/Pteraxii?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Serberys Raiders / Sulphurhounds share same NK listing
    (
        'adeptus-mechanicus-serberys-raiders',
        'Serberys Raiders',
        None,
        f'{_NK_BASE}/P/2148232979/Serberys-Raiders?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-serberys-sulphurhounds',
        'Serberys Raiders',
        None,
        f'{_NK_BASE}/P/2148232979/Serberys-Raiders?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Sicarian Infiltrators / Ruststalkers share same NK listing
    (
        'adeptus-mechanicus-sicarian-infiltrators',
        'Sicarians 2021 Edition',
        None,
        f'{_NK_BASE}/P/2147924596/Sicarians-2021-Edition?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-sicarian-ruststalkers',
        'Sicarians 2021 Edition',
        None,
        f'{_NK_BASE}/P/2147924596/Sicarians-2021-Edition?awid=1576',
        False,
        False,
    ),

    # ── Vehicles / Walkers ────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-kastelan-robots',
        'Kastelan Robots 2021 Edition',
        None,
        f'{_NK_BASE}/P/2148232973/Kastelan-Robots-2021-Edition?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-kataphron-breachers',
        'Kataphron Battle Servitors',
        None,
        f'{_NK_BASE}/P/2148084192/Kataphron-Battle-Servitors?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Skorpius Disintegrator / Dunerider share same NK listing
    (
        'adeptus-mechanicus-skorpius-disintegrator',
        'Skorpius Disintegrator',
        None,
        f'{_NK_BASE}/P/2147909511/Skorpius-Disintegrator?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-skorpius-dunerider',
        'Skorpius Disintegrator',
        None,
        f'{_NK_BASE}/P/2147909511/Skorpius-Disintegrator?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-sydonian-dragoon',
        'Ironstrider 2021 Edition',
        None,
        f'{_NK_BASE}/P/2147911818/Ironstrider-2021-Edition?awid=1576',
        False,
        False,
    ),

    # ── Leaders / HQ ─────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-skitarii-marshal',
        'Skitarii Marshall',
        None,
        f'{_NK_BASE}/P/2147889361/Skitarii-Marshall?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-sydonian-skatros',
        'Sydonian Skatros',
        None,
        f'{_NK_BASE}/P/2148098544/Sydonian-Skatros?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-technoarcheologist',
        'Technoarcheologist',
        None,
        f'{_NK_BASE}/P/2148084228/Technoarcheologist?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-tech-priest-enginseer',
        'Tech-Priest Enginseer',
        None,
        f'{_NK_BASE}/P/2147971403/Tech-Priest-Enginseer?awid=1576',
        False,
        False,
    ),
    (
        'adeptus-mechanicus-tech-priest-manipulus',
        'Tech-Priest Manipulus',
        None,
        f'{_NK_BASE}/P/2147936479/Tech-Priest-Manipulus?awid=1576',
        False,
        False,
    ),

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-adeptus-mechanicus',
        'Codex - Adeptus Mechanicus',
        None,
        f'{_NK_BASE}/P/2148098533/Codex---Adeptus-Mechanicus?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Adeptus Mechanicus products."""

    help = "Seeds Noble Knight listing URLs and prices for Adeptus Mechanicus. Idempotent."

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
