"""
Management command: seed_mm_seraphon_prices

Seeds Miniature Market prices for Seraphon products.

Source: AOS Seraphon - GW, NK, MM, AMAZON.xlsx (2026-05-19)

MM MATCHES (14 products with MM URLs):
  SR-001, SR-005, SR-006, SR-007, SR-008, SR-009, SR-012, SR-016,
  SR-018, SR-021, SR-022, SR-023, SR-024, SR-028

NO MM LISTING (14 products):
  SR-002 (Bastiladon) -- spreadsheet MM column contained the Aggradon Lancers URL (data entry error)
  SR-003 (Engine of the Gods)
  SR-004 (Hunters of Huanchi)
  SR-010 (Realmshaper Engine)
  SR-011 (Ripperdactyl Riders)
  SR-013 (Saurus Guard)
  SR-014 (Saurus Oldblood)
  SR-015 (Saurus Oldblood on Carnosaur)
  SR-017 (Saurus Scar-Veteran on Carnosaur)
  SR-019 (Skink Oracle on Troglodon)
  SR-020 (Skink Starpriest)
  SR-025 (Stegadon)
  SR-026 (Stegadon Chief)
  SR-027 (Terradon Riders)

Dual-kit / shared MM URLs:
  SR-005 / SR-006 — Kroxigor / Kroxigor Warspawned (gw-88-23)
  SR-008 / SR-009 — Raptadon Chargers / Raptadon Hunters (gw-88-21)

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

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-aggradon-lancers',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-aggradon-lancers-gw-88-18.html',
        False,
        False,
    ),
    # SR-002 Bastiladon — spreadsheet MM column had the Aggradon Lancers URL (data entry error); no MM URL

    # SR-003 Engine of the Gods — no MM listing
    # SR-004 Hunters of Huanchi — no MM listing

    # ── Infantry ──────────────────────────────────────────────────────────────
    # ⚠ Dual kit: SR-005 / SR-006 share same MM URL (gw-88-23)
    (
        'seraphon-kroxigor',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-kroxigor-gw-88-23.html',
        False,
        False,
    ),
    (
        'seraphon-kroxigor-warspawned',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-kroxigor-gw-88-23.html',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-lord-kroak',
        '',
        None,
        f'{_MM}gw-88-15.html',
        False,
        False,
    ),

    # ── Cavalry ───────────────────────────────────────────────────────────────
    # ⚠ Dual kit: SR-008 / SR-009 share same MM URL (gw-88-21)
    (
        'seraphon-raptadon-chargers',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-raptadon-hunters-gw-88-21.html',
        False,
        False,
    ),
    (
        'seraphon-raptadon-hunters',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-raptadon-hunters-gw-88-21.html',
        False,
        False,
    ),

    # SR-010 Realmshaper Engine — no MM listing
    # SR-011 Ripperdactyl Riders — no MM listing

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-astrolith-bearer',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-saurus-astrolith-bearer-gw-88-20.html',
        False,
        False,
    ),

    # SR-013 Saurus Guard — no MM listing
    # SR-014 Saurus Oldblood — no MM listing
    # SR-015 Saurus Oldblood on Carnosaur — no MM listing

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-scar-veteran-on-aggradon',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-saurus-scar-veteran-on-aggradon-gw-88-24.html',
        False,
        False,
    ),

    # SR-017 Saurus Scar-Veteran on Carnosaur — no MM listing

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-saurus-warriors',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-saurus-warriors-gw-88-06-2023.html',
        False,
        False,
    ),

    # SR-019 Skink Oracle on Troglodon — no MM listing
    # SR-020 Skink Starpriest — no MM listing

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-skink-starseer',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-skink-starseer-gw-88-25.html',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'seraphon-skinks',
        '',
        None,
        f'{_MM}gw-88-07.html',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'seraphon-slann-starmaster',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-slann-starmaster-gw-88-19.html',
        False,
        False,
    ),

    # ── Monsters ──────────────────────────────────────────────────────────────
    (
        'seraphon-spawn-of-chotec',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-seraphon-spawn-of-chotec-gw-88-22.html',
        False,
        False,
    ),

    # SR-025 Stegadon — no MM listing (triple kit, no separate MM page)
    # SR-026 Stegadon Chief — no MM listing (triple kit)
    # SR-027 Terradon Riders — no MM listing

    # ── Spearhead ─────────────────────────────────────────────────────────────
    (
        'spearhead-seraphon-sunblooded-prowlers',
        '',
        None,
        f'{_MM}warhammer-age-sigmar-spearhead-seraphon-sunblooded-prowlers-gw-70-882.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Seraphon products."""

    help = "Seeds Miniature Market listing URLs and prices for Seraphon. Idempotent."

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
