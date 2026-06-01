"""
Management command: seed_nk_chaos_daemons_prices

Seeds Noble Knight prices for Chaos Daemons products (CD-001 to CD-021).

Source: Chaos Demons - GW, NK, MM.xlsx (2026-05-31)

NK MATCHES (19 products):
  CD-001, CD-002, CD-003, CD-004, CD-005, CD-006, CD-008, CD-009,
  CD-011, CD-012, CD-013, CD-014, CD-015, CD-016, CD-017, CD-018,
  CD-019, CD-020, CD-021

NO NK LISTING (2 products):
  CD-007  Skull Altar
  CD-010  Changecaster

Shared kit notes:
  CD-016 / CD-017 / CD-018 — Burning Chariot / Exalted Flamer / Fateskimmer
                              share the same NK listing
  CD-019 / CD-020           — Skull Cannon / Rendmaster, Herald of Khorne
                              on Blood Throne  share the same NK listing

Affiliate tag ?awid=1576 appended to all URLs.
Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)

    # ── Greater Daemon / Special ──────────────────────────────────────────────
    (
        'belakor-the-dark-master',
        "Be'lakor - The Dark Master",
        None,
        f"{_NK}/P/2148034711/Belakor---The-Dark-Master?awid=1576",
        False,
        False,
    ),

    # ── Slaanesh ─────────────────────────────────────────────────────────────
    (
        'syllesske-the-vengeful-allegiance',
        "Syll'Esske - The Vengeful Allegiance",
        None,
        f'{_NK}/P/2148217283/SyllEsske---The-Vengeful-Allegiance-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'the-contorted-epitome',
        'Contorted Epitome, The',
        None,
        f'{_NK}/P/2147749534/Contorted-Epitome-The?awid=1576',
        False,
        False,
    ),
    (
        'infernal-enrapturess',
        'Infernal Enrapturess',
        None,
        f'{_NK}/P/2147749539/Infernal-Enrapturess?awid=1576',
        False,
        False,
    ),
    (
        'the-masque',
        'Masque, The',
        None,
        f'{_NK}/P/2148176502/Masque-The?awid=1576',
        False,
        False,
    ),

    # ── Khorne ───────────────────────────────────────────────────────────────
    (
        'skulltaker',
        'Skulltaker',
        None,
        f'{_NK}/P/2148084226/Skulltaker?awid=1576',
        False,
        False,
    ),
    # CD-007 Skull Altar — no NK listing
    (
        'karanak',
        'Karanak - The Hound of Vengance',
        None,
        f'{_NK}/P/2147746894/Karanak---The-Hound-of-Vengance?awid=1576',
        False,
        False,
    ),
    (
        'bloodmaster-herald-of-khorne',
        'Bloodmaster - Herald of Khorne',
        None,
        f'{_NK}/P/2148050312/Bloodmaster---Herald-of-Khorne?awid=1576',
        False,
        False,
    ),

    # ── Nurgle ────────────────────────────────────────────────────────────────
    (
        'feculent-gnarlmaw',
        'Feculent Gnarlmaw 2021 Edition',
        None,
        f'{_NK}/P/2147956169/Feculent-Gnarlmaw-2021-Edition?awid=1576',
        False,
        False,
    ),
    (
        'horticulous-slimux',
        'Horticulous Slimux',
        None,
        f'{_NK}/P/2147688329/Horticulous-Slimux?awid=1576',
        False,
        False,
    ),
    (
        'sloppity-bilepiper',
        'Sloppity Bilepiper',
        None,
        f'{_NK}/P/2147691275/Sloppity-Bilepiper?awid=1576',
        False,
        False,
    ),
    (
        'poxbringer',
        'Poxbringer',
        None,
        f'{_NK}/P/2147920241/Poxbringer?awid=1576',
        False,
        False,
    ),

    # ── Tzeentch ─────────────────────────────────────────────────────────────
    # CD-010 Changecaster — no NK listing
    (
        'the-changeling',
        'Changeling, The (2022 Edition)',
        None,
        f'{_NK}/P/2148246042/Changeling-The-2022-Edition?awid=1576',
        False,
        False,
    ),
    # ⚠ Shared kit: Burning Chariot / Exalted Flamer / Fateskimmer share NK listing
    (
        'burning-chariot-of-tzeentch',
        'Herald of Tzeentch on Burning Chariot',
        None,
        f'{_NK}/P/2147654455/Herald-of-Tzeentch-on-Burning-Chariot?awid=1576',
        False,
        False,
    ),
    (
        'exalted-flamer-of-tzeentch',
        'Herald of Tzeentch on Burning Chariot',
        None,
        f'{_NK}/P/2147654455/Herald-of-Tzeentch-on-Burning-Chariot?awid=1576',
        False,
        False,
    ),
    (
        'fateskimmer-herald-of-tzeentch-on-burning-chariot',
        'Herald of Tzeentch on Burning Chariot',
        None,
        f'{_NK}/P/2147654455/Herald-of-Tzeentch-on-Burning-Chariot?awid=1576',
        False,
        False,
    ),

    # ── Khorne war machines ───────────────────────────────────────────────────
    # ⚠ Shared kit: Skull Cannon / Rendmaster share NK listing
    (
        'skull-cannon',
        'Blood Throne of Khorne / Skull Cannon of Khorne',
        None,
        f'{_NK}/P/2147486029/Blood-Throne-of-Khorne-Skull-Cannon-of-Khorne?awid=1576',
        False,
        False,
    ),
    (
        'rendmaster-herald-of-khorne-on-blood-throne',
        'Blood Throne of Khorne / Skull Cannon of Khorne',
        None,
        f'{_NK}/P/2147486029/Blood-Throne-of-Khorne-Skull-Cannon-of-Khorne?awid=1576',
        False,
        False,
    ),

    # ── Multi-god ─────────────────────────────────────────────────────────────
    (
        'soul-grinder',
        'Soul Grinder (2012 Edition)',
        None,
        f'{_NK}/P/2147476420/Soul-Grinder-2012-Edition?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Chaos Daemons products."""

    help = 'Seeds Noble Knight listing URLs and prices for Chaos Daemons. Idempotent.'

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
