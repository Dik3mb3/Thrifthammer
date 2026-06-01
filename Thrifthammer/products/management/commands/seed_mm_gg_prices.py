"""
Management command: seed_mm_gg_prices

Seeds Miniature Market prices for Gloomspite Gitz products.

Source: Gloomspite - GW, NK, MM.xlsx (2026-05-30)

MM MATCHES (16 products):
  GG-001, GG-002, GG-003, GG-004, GG-005, GG-006, GG-008, GG-009,
  GG-017, GG-023, GG-024, GG-025, GG-026, GG-027, GG-028, GG-029

NO MM LISTING (19 products):
  GG-007, GG-010, GG-011, GG-012, GG-013, GG-014, GG-015, GG-016,
  GG-018, GG-019, GG-020, GG-021, GG-022, GG-030, GG-031, GG-032,
  GG-033, GG-034, GG-035

Shared kit notes:
  GG-004 / GG-005  — Loonboss on Mangler Squigs / Mangler Squigs share MM listing

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

    # ── Squig units ───────────────────────────────────────────────────────────
    (
        'boingrot-bounderz',
        '',
        None,
        f'{_MM}gw-89-44.html',
        False,
        False,
    ),
    (
        'squigboss-with-gnasha-squig',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-gloomspite-gitz-squigboss-with-gnasha-squig-gw-89-75.html',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'loonboss-on-giant-cave-squig',
        '',
        None,
        f'{_MM}gw-89-35.html',
        False,
        False,
    ),

    # ── Mangler Squigs (dual kit — share MM listing) ───────────────────────
    (
        'loonboss-on-mangler-squigs',
        '',
        None,
        f'{_MM}gw-89-46.html',
        False,
        False,
    ),
    (
        'mangler-squigs',
        '',
        None,
        f'{_MM}gw-89-46.html',
        False,
        False,
    ),

    # ── Troggoths ─────────────────────────────────────────────────────────────
    (
        'trugg-the-troggoth-king',
        '',
        None,
        f'{_MM}warhammer-age-sigmar-gloomspite-gitz-trugg-troggoth-king-gw-89-54.html',
        False,
        False,
    ),
    # GG-010 Dankhold Troggboss — no MM listing
    # GG-011 Gobbapalooza — no MM listing
    # GG-012 Dankhold Troggoth — no MM listing
    # GG-013 Sneaky Snufflers — no MM listing
    # GG-014 Loonboss — no MM listing
    # GG-022 Fellwater Troggoths — no MM listing
    # GG-033 Rockgut Troggoths — no MM listing

    # ── Spider Riders / Snarlfangs ────────────────────────────────────────────
    # GG-007 Spider Riders — no MM listing
    (
        'snarlfang-riders',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-gloomspite-gitz-snarlfang-riders-gw-89-76.html',
        False,
        False,
    ),

    # ── Kragnos ───────────────────────────────────────────────────────────────
    (
        'kragnos-the-end-of-empires',
        '',
        None,
        f'{_MM}gw-89-65.html',
        False,
        False,
    ),

    # ── Moonclan units ────────────────────────────────────────────────────────
    # GG-015 Moonclan Shootas — no MM listing
    # GG-016 Endless Spells: Gloomspite Gitz — no MM listing
    (
        'bad-moon-loonshrine',
        '',
        None,
        f'{_MM}gw-89-36.html',
        False,
        False,
    ),
    # GG-018 Loonsmasha Fanatics — no MM listing
    # GG-019 Skragrott the Loonking — no MM listing
    # GG-020 Moonclan Stabbas — no MM listing
    # GG-021 Fungoid Cave-Shaman — no MM listing

    # ── New releases (2025) ───────────────────────────────────────────────────
    (
        'doom-diver-catapult',
        '',
        None,
        f'{_MM}warhammer-age-sigmar-gloomspite-gitz-doom-diver-catapult-gw-89-90.html',
        False,
        False,
    ),
    (
        'sunsteala-wheelas',
        '',
        None,
        f'{_MM}warhammer-age-sigmar-gloomspite-gitz-sunsteala-wheelas-gw-89-89.html',
        False,
        False,
    ),
    (
        'snarlpack-cavalry',
        '',
        None,
        f'{_MM}warhammer-age-sigmar-gloomspite-gitz-snarlpack-cavalry-gw-89-88.html',
        False,
        False,
    ),
    (
        'snarlboss-on-war-wheela',
        '',
        None,
        f'{_MM}warhammer-age-sigmar-gloomspite-gitz-snarlboss-on-war-wheela-gw-89-91.html',
        False,
        False,
    ),
    (
        'snarlboss-and-wolfgit-retinue',
        '',
        None,
        f'{_MM}warhammer-age-sigmar-gloomspite-gitz-snarlboss-wolfgit-retinue-gw-89-98.html',
        False,
        False,
    ),
    (
        'rabble-rowza',
        '',
        None,
        f'{_MM}warhammer-age-of-sigmar-gloomspite-gitz-rabble-rowza-gw-89-84.html',
        False,
        False,
    ),
    # GG-035 Droggz da Sunchompa — no MM listing

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'destruction-battletome-gloomspite-gitz',
        '',
        None,
        f'{_MM}warhammer-age-sigmar-destruction-battletome-gloomspite-gitz-gw-89-63-2025.html',
        False,
        False,
    ),

    # ── Arachnarok Spider variants — no MM listing for any ────────────────────
    # GG-030 Skitterstrand Arachnarok — no MM listing
    # GG-031 Arachnarok Spider with Flinger — no MM listing
    # GG-032 Webspinner Shaman on Arachnarok Spider — no MM listing
    # GG-034 Arachnarok Spider with Spiderfang Warparty — no MM listing
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Gloomspite Gitz products."""

    help = 'Seeds Miniature Market listing URLs and prices for Gloomspite Gitz. Idempotent.'

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
