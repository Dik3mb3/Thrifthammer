"""
Management command: seed_nk_seraphon_prices

Seeds Noble Knight prices for Seraphon products.

Source: AOS Seraphon - GW, NK, MM, AMAZON.xlsx (2026-05-19)

NK MATCHES (27 products -- SR-011 Ripperdactyl Riders has no NK listing):
  SR-001 to SR-010, SR-012 to SR-028

Dual/triple kit / shared NK listings:
  SR-003 / SR-025 / SR-026 — Engine of the Gods / Stegadon / Stegadon Chief (triple: same NK listing)
  SR-005 / SR-006 — Kroxigor / Kroxigor Warspawned (same NK listing)
  SR-008 / SR-009 — Raptadon Chargers / Raptadon Hunters (same NK listing)

Quad NK URL (webstore-edition listing):
  SR-014 / SR-015 / SR-017 / SR-019 — Saurus Oldblood / Oldblood on Carnosaur /
  Scar-Veteran on Carnosaur / Skink Oracle on Troglodon (same NK listing)

NO NK LISTING (1 product):
  SR-011 (Ripperdactyl Riders)

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

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-aggradon-lancers',
        'Aggradon Lancers',
        None,
        f'{_NK_BASE}/P/2148236809/Aggradon-Lancers?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-bastiladon',
        'Bastiladon',
        None,
        f'{_NK_BASE}/P/2147601577/Bastiladon?awid=1576',
        False,
        False,
    ),

    # ── Monsters / War Engines ────────────────────────────────────────────────
    # ⚠ Triple kit: SR-003 / SR-025 / SR-026 share same NK listing
    (
        'seraphon-engine-of-the-gods',
        'Seraphon Stegadon / Engine of the Gods',
        None,
        f'{_NK_BASE}/P/2147895549/Seraphon-Stegadon-Engine-of-the-Gods-Webstore-Edition?awid=1576',
        False,
        False,
    ),

    # ── Warband ───────────────────────────────────────────────────────────────
    (
        'seraphon-hunters-of-huanchi',
        'Hunters of Huanchi',
        None,
        f'{_NK_BASE}/P/2148036065/Hunters-of-Huanchi?awid=1576',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: SR-005 / SR-006 share same NK listing
    (
        'seraphon-kroxigor',
        'Kroxigor',
        None,
        f'{_NK_BASE}/P/2148056178/Kroxigor?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-kroxigor-warspawned',
        'Kroxigor',
        None,
        f'{_NK_BASE}/P/2148056178/Kroxigor?awid=1576',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-lord-kroak',
        'Lord Kroak',
        None,
        f'{_NK_BASE}/P/2148176356/Lord-Kroak?awid=1576',
        False,
        False,
    ),

    # ── Cavalry ───────────────────────────────────────────────────────────────
    # ⚠ Dual kit: SR-008 / SR-009 share same NK listing
    (
        'seraphon-raptadon-chargers',
        'Raptadon Hunters',
        None,
        f'{_NK_BASE}/P/2148056169/Raptadon-Hunters?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-raptadon-hunters',
        'Raptadon Hunters',
        None,
        f'{_NK_BASE}/P/2148056169/Raptadon-Hunters?awid=1576',
        False,
        False,
    ),

    # ── Terrain ───────────────────────────────────────────────────────────────
    (
        'seraphon-realmshaper-engine',
        'Realmshaper Engine',
        None,
        f'{_NK_BASE}/P/2147797663/Realmshaper-Engine?awid=1576',
        False,
        False,
    ),

    # SR-011 Ripperdactyl Riders — no NK listing

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-astrolith-bearer',
        'Saurus Astrolith Bearer',
        None,
        f'{_NK_BASE}/P/2148056188/Saurus-Astrolith-Bearer?awid=1576',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-guard',
        'Saurus Guard',
        None,
        f'{_NK_BASE}/P/2147601231/Saurus-Guard?awid=1576',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    # ⚠ Quad NK URL: SR-014 / SR-015 / SR-017 / SR-019 share same NK webstore-edition listing
    (
        'seraphon-saurus-oldblood',
        'Saurus Oldblood / Scar-Veteran / Oracle on Carnosaur / Troglodon',
        None,
        f'{_NK_BASE}/P/2148199737/Saurus-Oldblood-Scar-Veteran-Oracle-on-Carnosaur-Troglodon-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-saurus-oldblood-on-carnosaur',
        'Saurus Oldblood / Scar-Veteran / Oracle on Carnosaur / Troglodon',
        None,
        f'{_NK_BASE}/P/2148199737/Saurus-Oldblood-Scar-Veteran-Oracle-on-Carnosaur-Troglodon-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-saurus-scar-veteran-on-aggradon',
        'Saurus Scar-Veteran on Aggradon',
        None,
        f'{_NK_BASE}/P/2148056180/Saurus-Scar-Veteran-on-Aggradon?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-saurus-scar-veteran-on-carnosaur',
        'Saurus Oldblood / Scar-Veteran / Oracle on Carnosaur / Troglodon',
        None,
        f'{_NK_BASE}/P/2148199737/Saurus-Oldblood-Scar-Veteran-Oracle-on-Carnosaur-Troglodon-Webstore-Edition?awid=1576',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-warriors',
        'Saurus Warriors',
        None,
        f'{_NK_BASE}/P/2148056177/Saurus-Warriors?awid=1576',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    # ⚠ Quad NK URL: SR-019 shares NK listing with SR-014 / SR-015 / SR-017
    (
        'seraphon-skink-oracle-on-troglodon',
        'Saurus Oldblood / Scar-Veteran / Oracle on Carnosaur / Troglodon',
        None,
        f'{_NK_BASE}/P/2148199737/Saurus-Oldblood-Scar-Veteran-Oracle-on-Carnosaur-Troglodon-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-skink-starpriest',
        'Skink Starpriest',
        None,
        f'{_NK_BASE}/P/2147601578/Skink-Starpriest?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-skink-starseer',
        'Skink Starseer',
        None,
        f'{_NK_BASE}/P/2148056186/Skink-Starseer?awid=1576',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-skinks',
        'Skinks',
        None,
        f'{_NK_BASE}/P/2148060145/Skinks?awid=1576',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-slann-starmaster',
        'Slann Starmaster',
        None,
        f'{_NK_BASE}/P/2148056172/Slann-Starmaster?awid=1576',
        False,
        False,
    ),

    # ── Monsters ──────────────────────────────────────────────────────────────
    (
        'seraphon-spawn-of-chotec',
        'Spawn of Chotec',
        None,
        f'{_NK_BASE}/P/2148056183/Spawn-of-Chotec?awid=1576',
        False,
        False,
    ),

    # ── Monsters / War Engines ────────────────────────────────────────────────
    # ⚠ Triple kit: SR-025 / SR-026 share NK listing with SR-003
    (
        'seraphon-stegadon',
        'Seraphon Stegadon / Engine of the Gods',
        None,
        f'{_NK_BASE}/P/2147895549/Seraphon-Stegadon-Engine-of-the-Gods-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'seraphon-stegadon-chief',
        'Seraphon Stegadon / Engine of the Gods',
        None,
        f'{_NK_BASE}/P/2147895549/Seraphon-Stegadon-Engine-of-the-Gods-Webstore-Edition?awid=1576',
        False,
        False,
    ),

    # ── Flying Cavalry ────────────────────────────────────────────────────────
    (
        'seraphon-terradon-riders',
        'Terradon Riders',
        None,
        f'{_NK_BASE}/P/2147601229/Terradon-Riders?awid=1576',
        False,
        False,
    ),

    # ── Spearhead ─────────────────────────────────────────────────────────────
    (
        'spearhead-seraphon-sunblooded-prowlers',
        'Spearhead - Sunblooded Prowlers',
        None,
        f'{_NK_BASE}/P/2148312215/Spearhead---Sunblooded-Prowlers?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Seraphon products."""

    help = "Seeds Noble Knight listing URLs and prices for Seraphon. Idempotent."

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
