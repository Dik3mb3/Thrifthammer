"""
Management command: seed_nk_slaves_to_darkness_prices

Seeds Noble Knight prices for Slaves to Darkness products (S2D-001 to S2D-035).

Source: AOS Slaves to Darkness - GW, NK, MM.xlsx (2026-06-03)

NK MATCHES (27 products):
  S2D-002, S2D-003, S2D-004, S2D-005, S2D-006, S2D-007,
  S2D-008, S2D-009, S2D-010, S2D-011, S2D-012, S2D-013, S2D-014,
  S2D-016, S2D-018, S2D-019, S2D-021, S2D-022, S2D-023, S2D-024,
  S2D-025, S2D-028, S2D-029, S2D-030, S2D-032, S2D-033, S2D-034

NO NK LISTING (8 products, including removed duplicates):
  S2D-001  Spearhead (removed — use 70-04)
  S2D-015  Abraxia, Spear of the Everchosen
  S2D-017  Chaos Warriors (removed — use 83-18)
  S2D-020  Mindstealer Sphiranx
  S2D-026  Varanguard (removed — use 83-14)
  S2D-027  Slaughterbrute
  S2D-031  Chaos Battletome: Slaves to Darkness
  S2D-035  Darkoath Wilderfiend

Shared kit notes:
  S2D-003 / S2D-006 / S2D-012  Chaos Lord on Daemonic Mount / Chaos Lord on
                                Karkadrak / Chaos Lord  share NK listing
  S2D-002 / S2D-013             Warcry: Centaurion Marshal / Centaurion Marshal
                                share NK listing
  S2D-010 / S2D-032             Darkoath Chieftain / Darkoath Chieftain on
                                Warsteed  share NK listing
  S2D-023 / S2D-025             Gorebeast Chariot / Chaos Chariot share NK listing

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

    # ── Warcry ────────────────────────────────────────────────────────────────
    # ⚠ Shared kit: Warcry: Centaurion Marshal / Centaurion Marshal share NK listing
    (
        'warcry-centaurion-marshal',
        'Centaurion Marshal',
        None,
        f'{_NK}/P/2147996720/Centaurion-Marshal?awid=1576',
        False,
        False,
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    # ⚠ Shared kit (triple): Chaos Lord on Daemonic Mount / Chaos Lord on
    #   Karkadrak / Chaos Lord  share NK listing
    (
        'chaos-lord-on-daemonic-mount',
        'Chaos Lord on Karkadrak',
        None,
        f'{_NK}/P/2148030855/Chaos-Lord-on-Karkadrak?awid=1576',
        False,
        False,
    ),
    (
        'exalted-hero-of-chaos',
        'Exalted Hero of Chaos',
        None,
        f'{_NK}/P/2148030845/Exalted-Hero-of-Chaos?awid=1576',
        False,
        False,
    ),
    (
        'eternus-blade-of-the-first-prince',
        'Eternus - Blade of the First Prince',
        None,
        f'{_NK}/P/2148030853/Eternus---Blade-of-the-First-Prince?awid=1576',
        False,
        False,
    ),
    # ⚠ Shared kit (triple): see Chaos Lord on Daemonic Mount note
    (
        'chaos-lord-on-karkadrak',
        'Chaos Lord on Karkadrak',
        None,
        f'{_NK}/P/2148030855/Chaos-Lord-on-Karkadrak?awid=1576',
        False,
        False,
    ),
    (
        'ogroid-myrmidon',
        'Ogroid Myrmidon',
        None,
        f'{_NK}/P/2147793065/Ogroid-Myrmidon?awid=1576',
        False,
        False,
    ),
    (
        'darkoath-warqueen',
        'Slaves to Darkness - Darkoath Warqueen Marakarr Blood-Sky',
        None,
        f'{_NK}/P/2147690769/Slaves-to-Darkness---Darkoath-Warqueen-Marakarr-Blood-Sky?awid=1576',
        False,
        False,
    ),
    (
        'gaunt-summoner',
        'Gaunt Summoner of Tzeentch 2015 Edition',
        None,
        f'{_NK}/P/2147607128/Gaunt-Summoner-of-Tzeentch-2015-Edition?awid=1576',
        False,
        False,
    ),
    # ⚠ Shared kit (dual): Darkoath Chieftain / Darkoath Chieftain on Warsteed
    #   share NK listing
    (
        'darkoath-chieftain',
        'Darkoath Chieftain on Warsteed',
        None,
        f'{_NK}/P/2148145421/Darkoath-Chieftain-on-Warsteed?awid=1576',
        False,
        False,
    ),
    (
        'archaon-everchosen',
        'Archaon - Marshal of Apocalypse 2023 Edition',
        None,
        f'{_NK}/P/2148050445/Archaon---Marshal-of-Apocalypse-2023-Edition?awid=1576',
        False,
        False,
    ),
    # ⚠ Shared kit (triple): see Chaos Lord on Daemonic Mount note
    (
        'chaos-lord',
        'Chaos Lord on Karkadrak',
        None,
        f'{_NK}/P/2148030855/Chaos-Lord-on-Karkadrak?awid=1576',
        False,
        False,
    ),
    # ⚠ Shared kit (dual): see Warcry: Centaurion Marshal note
    (
        'centaurion-marshal',
        'Centaurion Marshal',
        None,
        f'{_NK}/P/2147996720/Centaurion-Marshal?awid=1576',
        False,
        False,
    ),
    (
        'chaos-sorcerer-lord',
        'Chaos Sorcerer Lord',
        None,
        f'{_NK}/P/2147454348/Chaos-Sorcerer-Lord?awid=1576',
        False,
        False,
    ),

    # S2D-015 Abraxia — no NK listing

    (
        'brands-oathbound',
        "Brand's Oathbound",
        None,
        f'{_NK}/P/2148145510/Brands-Oathbound?awid=1576',
        False,
        False,
    ),

    # S2D-017 Chaos Warriors — no NK listing

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'ogroid-theridons',
        'Ogroid Theridons',
        None,
        f'{_NK}/P/2148030873/Ogroid-Theridons?awid=1576',
        False,
        False,
    ),
    (
        'chaos-knights',
        'Chaos Knights 2008 Edition',
        None,
        f'{_NK}/P/2147387068/Chaos-Knights-2008-Edition?awid=1576',
        False,
        False,
    ),

    # S2D-020 Mindstealer Sphiranx — no NK listing

    # ── Monsters ──────────────────────────────────────────────────────────────
    (
        'fomoroid-crusher',
        'Fomoroid Crusher',
        None,
        f'{_NK}/P/2147794804/Fomoroid-Crusher?awid=1576',
        False,
        False,
    ),
    (
        'chaotic-beasts',
        'Chaotic Beasts',
        None,
        f'{_NK}/P/2147766235/Chaotic-Beasts?awid=1576',
        False,
        False,
    ),

    # ── War machines ──────────────────────────────────────────────────────────
    # ⚠ Shared kit (dual): Gorebeast Chariot / Chaos Chariot share NK listing
    (
        'gorebeast-chariot',
        'Chaos Chariot',
        None,
        f'{_NK}/P/2147614150/Chaos-Chariot?awid=1576',
        False,
        False,
    ),

    # ── Endless Spells ────────────────────────────────────────────────────────
    (
        'endless-spells-slaves-to-darkness',
        'Endless Spells - Slaves to Darkness',
        None,
        f'{_NK}/P/2147775632/Endless-Spells---Slaves-to-dArkness?awid=1576',
        False,
        False,
    ),

    # ⚠ Shared kit (dual): see Gorebeast Chariot note
    (
        'chaos-chariot',
        'Chaos Chariot',
        None,
        f'{_NK}/P/2147614150/Chaos-Chariot?awid=1576',
        False,
        False,
    ),

    # S2D-026 Varanguard — removed (use pre-existing 83-14 record)
    # S2D-027 Slaughterbrute — no NK listing (same as P-MUTALITH-VB in DB)

    # ── Terrain ───────────────────────────────────────────────────────────────
    (
        'nexus-chaotica',
        'Nexus Chaotica',
        None,
        f'{_NK}/P/2148145594/Nexus-Chaotica?awid=1576',
        False,
        False,
    ),

    # ── Cavalry / Infantry (Darkoath) ─────────────────────────────────────────
    (
        'darkoath-fellriders',
        'Darkoath Fellriders',
        None,
        f'{_NK}/P/2148145474/Darkoath-Fellriders?awid=1576',
        False,
        False,
    ),
    (
        'darkoath-marauders',
        'Darkoath Marauders',
        None,
        f'{_NK}/P/2148145488/Darkoath-Marauders?awid=1576',
        False,
        False,
    ),

    # S2D-031 Chaos Battletome: Slaves to Darkness — no NK listing

    # ⚠ Shared kit (dual): see Darkoath Chieftain note
    (
        'darkoath-chieftain-on-warsteed',
        'Darkoath Chieftain on Warsteed',
        None,
        f'{_NK}/P/2148145421/Darkoath-Chieftain-on-Warsteed?awid=1576',
        False,
        False,
    ),

    # ── Infantry (cont.) ──────────────────────────────────────────────────────
    (
        'chaos-chosen',
        'Chaos Chosen',
        None,
        f'{_NK}/P/2148030859/Chaos-Chosen?awid=1576',
        False,
        False,
    ),

    # ── Warcry (cont.) ────────────────────────────────────────────────────────
    (
        'chaos-legionnaires',
        'Chaos Legionnaires',
        None,
        f'{_NK}/P/2147996722/Chaos-Legionnaires?awid=1576',
        False,
        False,
    ),

    # S2D-035 Darkoath Wilderfiend — no NK listing
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Slaves to Darkness products."""

    help = 'Seeds Noble Knight listing URLs and prices for Slaves to Darkness. Idempotent.'

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
