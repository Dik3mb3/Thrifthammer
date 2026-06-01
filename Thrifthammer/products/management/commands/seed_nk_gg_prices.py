"""
Management command: seed_nk_gg_prices

Seeds Noble Knight prices for Gloomspite Gitz products.

Source: Gloomspite - GW, NK, MM.xlsx (2026-05-30)

NK MATCHES (31 products):
  GG-001, GG-002, GG-003, GG-004, GG-005, GG-006, GG-008, GG-009,
  GG-010, GG-011, GG-012, GG-013, GG-015, GG-016, GG-017, GG-018,
  GG-019, GG-020, GG-021, GG-023, GG-024, GG-025, GG-026, GG-027,
  GG-028, GG-029, GG-030, GG-031, GG-032, GG-033, GG-034

NO NK LISTING (4 products):
  GG-007  Spider Riders
  GG-014  Loonboss
  GG-022  Fellwater Troggoths
  GG-035  Droggz da Sunchompa

Shared kit notes:
  GG-004 / GG-005   — Loonboss on Mangler Squigs / Mangler Squigs share NK listing
  GG-010 / GG-012   — Dankhold Troggboss / Dankhold Troggoth share NK listing
  GG-015 / GG-020   — Moonclan Shootas / Moonclan Stabbas share NK listing
  GG-030 / GG-031 / GG-032 / GG-034  — Arachnarok Spider variants share NK listing

Note: GG-025 Snarlpack Cavalry — NK URL slug reads "SNarlpack-Cavalry" (capital N typo
on NK side); confirmed correct listing, use as-is.

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

    # ── Squig units ───────────────────────────────────────────────────────────
    (
        'boingrot-bounderz',
        'Squig Hoppers',
        None,
        f'{_NK}/P/2148251168/Squig-Hoppers?awid=1576',
        False,
        False,
    ),
    (
        'squigboss-with-gnasha-squig',
        'Squigboss w/ Gnasha-Squig',
        None,
        f'{_NK}/P/2148034933/Squigboss-w-Gnasha-Squig?awid=1576',
        False,
        False,
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'loonboss-on-giant-cave-squig',
        'Loonboss on Giant Cave Squig',
        None,
        f'{_NK}/P/2148050313/Loonboss-on-Giant-Cave-Squig?awid=1576',
        False,
        False,
    ),
    # GG-014 Loonboss — no NK listing
    (
        'skragrott-the-loonking',
        'Skragrott the Loonking',
        None,
        f'{_NK}/P/2147741736/Skragrott-the-Loonking?awid=1576',
        False,
        False,
    ),
    (
        'fungoid-cave-shaman',
        'Moonclan - Fungoid Cave-Shaman Snazzgar Stinkmullett',
        None,
        f'{_NK}/P/2147690767/Moonclan---Fungoid-Cave-Shaman-Snazzgar-Stinkmullett?awid=1576',
        False,
        False,
    ),

    # ── Mangler Squigs (dual kit — share NK listing) ───────────────────────
    (
        'loonboss-on-mangler-squigs',
        'Mangler Squigs 2021 Edition',
        None,
        f'{_NK}/P/2148137997/Mangler-Squigs-2021-Edition?awid=1576',
        False,
        False,
    ),
    (
        'mangler-squigs',
        'Mangler Squigs 2021 Edition',
        None,
        f'{_NK}/P/2148137997/Mangler-Squigs-2021-Edition?awid=1576',
        False,
        False,
    ),

    # ── Troggoths ─────────────────────────────────────────────────────────────
    (
        'trugg-the-troggoth-king',
        'Trugg the Troggoth King',
        None,
        f'{_NK}/P/2148112912/Trugg-the-Troggoth-King?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Dankhold Troggboss / Dankhold Troggoth share NK listing
    (
        'dankhold-troggboss',
        'Dankhold Troggoth',
        None,
        f'{_NK}/P/2148201818/Dankhold-Troggoth?awid=1576',
        False,
        False,
    ),
    (
        'dankhold-troggoth',
        'Dankhold Troggoth',
        None,
        f'{_NK}/P/2148201818/Dankhold-Troggoth?awid=1576',
        False,
        False,
    ),
    # GG-022 Fellwater Troggoths — no NK listing
    (
        'rockgut-troggoths',
        'Rockgut Troggoths 2019 Edition',
        None,
        f'{_NK}/P/2147767611/Rockgut-Troggoths-2019-Edition?awid=1576',
        False,
        False,
    ),

    # ── Spider Riders / Snarlfangs ────────────────────────────────────────────
    # GG-007 Spider Riders — no NK listing
    (
        'snarlfang-riders',
        'Snarlfang Riders',
        None,
        f'{_NK}/P/2148034929/Snarlfang-Riders?awid=1576',
        False,
        False,
    ),

    # ── Kragnos ───────────────────────────────────────────────────────────────
    (
        'kragnos-the-end-of-empires',
        'Kragnos - The End of Empires',
        None,
        f'{_NK}/P/2148050442/Kragnos---The-End-of-Empires?awid=1576',
        False,
        False,
    ),

    # ── Moonclan units ────────────────────────────────────────────────────────
    (
        'gobbapalooza',
        'Gobbapalooza',
        None,
        f'{_NK}/P/2147742089/Gobbapalooza?awid=1576',
        False,
        False,
    ),
    (
        'sneaky-snufflers',
        'Sneaky Snufflers',
        None,
        f'{_NK}/P/2147742090/Sneaky-Snufflers?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Moonclan Shootas / Moonclan Stabbas share NK listing
    (
        'moonclan-shootas',
        'Moonclan Grots',
        None,
        f'{_NK}/P/2147674650/Moonclan-Grots?awid=1576',
        False,
        False,
    ),
    (
        'moonclan-stabbas',
        'Moonclan Grots',
        None,
        f'{_NK}/P/2147674650/Moonclan-Grots?awid=1576',
        False,
        False,
    ),
    (
        'loonsmasha-fanatics',
        'Fanatics Webstore Edition',
        None,
        f'{_NK}/P/2148199578/Fanatics-Webstore-Edition?awid=1576',
        False,
        False,
    ),

    # ── Endless Spells / Scenery ──────────────────────────────────────────────
    (
        'endless-spells-gloomspite-gitz',
        'Endless Spells - Gloomspite Gitz',
        None,
        f'{_NK}/P/2147741765/Endless-Spells---Gloomspite-Gitz?awid=1576',
        False,
        False,
    ),
    (
        'bad-moon-loonshrine',
        'Bad Moon Loonshrine Webstore Edition',
        None,
        f'{_NK}/P/2148095188/Bad-Moon-Loonshrine-Webstore-Edition?awid=1576',
        False,
        False,
    ),

    # ── New releases (2025) ───────────────────────────────────────────────────
    (
        'doom-diver-catapult',
        'Doom Diver Catapult',
        None,
        f'{_NK}/P/2148280454/Doom-Diver-Catapult?awid=1576',
        False,
        False,
    ),
    (
        'sunsteala-wheelas',
        'Sunsteala Wheelas',
        None,
        f'{_NK}/P/2148280398/Sunsteala-Wheelas?awid=1576',
        False,
        False,
    ),
    # Note: NK URL slug reads "SNarlpack-Cavalry" (capital N typo on NK side); use as-is.
    (
        'snarlpack-cavalry',
        'Snarlpack Cavalry',
        None,
        f'{_NK}/P/2148280412/SNarlpack-Cavalry?awid=1576',
        False,
        False,
    ),
    (
        'snarlboss-on-war-wheela',
        'Snarlboss on War-Wheela',
        None,
        f'{_NK}/P/2148280405/Snarlboss-on-War-Wheela?awid=1576',
        False,
        False,
    ),
    (
        'snarlboss-and-wolfgit-retinue',
        'Snarlboss and Wolfgit Retinue',
        None,
        f'{_NK}/P/2148280430/Snarlboss-and-Wolfgit-Retinue?awid=1576',
        False,
        False,
    ),
    (
        'rabble-rowza',
        'Rabble-Rowza',
        None,
        f'{_NK}/P/2148081613/Rabble-Rowza?awid=1576',
        False,
        False,
    ),
    # GG-035 Droggz da Sunchompa — no NK listing

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'destruction-battletome-gloomspite-gitz',
        'Battletome - Gloomspite Gitz',
        None,
        f'{_NK}/P/2148280348/Battletome---Gloomspite-Gitz?awid=1576',
        False,
        False,
    ),

    # ── Arachnarok Spider variants (quad kit — share NK listing) ─────────────
    # ⚠ Quad kit: Skitterstrand / Flinger / Webspinner Shaman / Spiderfang Warparty
    #   all share the same NK listing (Arachnarok-Spider).
    (
        'skitterstrand-arachnarok',
        'Arachnarok Spider',
        None,
        f'{_NK}/P/2147686427/Arachnarok-Spider?awid=1576',
        False,
        False,
    ),
    (
        'arachnarok-spider-with-flinger',
        'Arachnarok Spider',
        None,
        f'{_NK}/P/2147686427/Arachnarok-Spider?awid=1576',
        False,
        False,
    ),
    (
        'webspinner-shaman-on-arachnarok-spider',
        'Arachnarok Spider',
        None,
        f'{_NK}/P/2147686427/Arachnarok-Spider?awid=1576',
        False,
        False,
    ),
    (
        'arachnarok-spider-with-spiderfang-warparty',
        'Arachnarok Spider',
        None,
        f'{_NK}/P/2147686427/Arachnarok-Spider?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Gloomspite Gitz products."""

    help = 'Seeds Noble Knight listing URLs and prices for Gloomspite Gitz. Idempotent.'

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
