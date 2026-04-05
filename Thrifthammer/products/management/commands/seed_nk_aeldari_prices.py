"""
Management command: seed_nk_aeldari_prices

Seeds Noble Knight Games CurrentPrice entries for all Aeldari products
(both existing phase-1 slugs and new phase-3 slugs).

Prices and stock status sourced from Octoparse scrape of NK spreadsheet
(Warhammer 40,000 - Noble Knight Gamesv3.xlsx) — 2026-04-05.
Affiliate parameter ?awid=1576 appended to all URLs.

Match notes / questionable matches:
  ⚠  Howling Banshees     — NK lists at $129.95 (MSRP is $62.50).
                             This appears to be the current in-stock price;
                             NK sometimes prices Aeldari above MSRP due to
                             demand. Included as-is — review if incorrect.
  ⚠  Wave Serpent         — NK has TWO listings:
                             "Wave Serpent"          $54.95 (older repack)
                             "Wave Serpent 2022 Ed." $99.95 (2022 repack)
                             Using the cheaper current-in-stock listing.
  ⚠  Crimson Hunter /
     Hemlock Wraithfighter — NK has a single combined listing
                             "Hemlock Wraithfighter/Crimson Hunter" at $86.95.
                             Both slugs point to the same URL (same physical box).
  ⚠  Guardian Defenders   — NK "Guardians (2022 Edition)" is the same dual-build
                             kit as Storm Guardians (craftworlds-guardians).
                             Both our slugs point to the same NK URL.
  ⚠  Wraithblades         — NK only lists "Wraithguard" (same dual-build box).
                             Using same URL for both Wraithguard and Wraithblades.
  ⚠  Spiritseer           — NK has two listings; using newer (non-2019) listing.

Products not on NK (marked not_available=True):
  codex-aeldari             — only Collector's Edition on NK (skipped)
  craftworlds-farseer       — no current NK listing found
  craftworlds-fire-dragons  — no current NK listing found
  aeldari-autarch-wayleaper — no NK listing found
  aeldari-warlock-skyrunner — no NK listing found
  aeldari-fuegan            — 2025 release, not yet on NK
  aeldari-baharroth         — 2025 release, not yet on NK
  aeldari-lhykhis           — 2025 release, not yet on NK
  aeldari-asurmen           — 2025 release, not yet on NK
  aeldari-prince-yriel      — 2026 release, not yet on NK
  aeldari-kharseth          — 2026 release, not yet on NK
  aeldari-dark-reapers      — no current NK listing found
  aeldari-swooping-hawks    — 2025 release, not yet on NK
  aeldari-warp-spiders      — 2025 release, not yet on NK
  aeldari-windriders        — no current NK listing found
  aeldari-corsair-voidreavers — 2026 release, not yet on NK
  aeldari-corsair-skyreavers  — 2026 release, not yet on NK
  aeldari-support-weapon    — no current NK listing found
  aeldari-wraithlord        — no current NK listing found
  aeldari-fire-prism        — no current NK listing found
  aeldari-night-spinner     — no current NK listing found
  aeldari-vyper             — 2026 release, not yet on NK
  aeldari-starfang          — 2026 release, not yet on NK
  aeldari-skyweavers        — no current NK listing found
  aeldari-starweaver        — no current NK listing found
  aeldari-voidweaver        — no current NK listing found
  aeldari-solitaire         — no current NK listing found
  aeldari-yvraine           — no current NK listing found
  aeldari-the-visarch       — no current NK listing found
  aeldari-the-yncarne       — no current NK listing found
  combat-patrol-aeldari-corsairs — 2026 release, not yet on NK

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_nk_aeldari_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ── NK price data ─────────────────────────────────────────────────────────────
# (slug, listing_title, price, url, in_stock, not_available)
# price=None → NK carries but price unknown (scraper will update)
# not_available=True → not carried by NK
NK_PRICES = [

    # ── Existing phase-1 Aeldari slugs ───────────────────────────────────────
    (
        'craftworlds-combat-patrol',
        'Combat Patrol - Aeldari',
        153.95,
        'https://www.nobleknight.com/P/2148381030/Combat-Patrol---Aeldari?awid=1576',
        True, False,
    ),
    (
        'craftworlds-dire-avengers',
        'Dire Avengers',
        43.95,
        'https://www.nobleknight.com/P/2147974202/Dire-Avengers?awid=1576',
        True, False,
    ),
    (
        'craftworlds-farseer',
        '',
        None, '', False, True,
    ),
    (
        'craftworlds-fire-dragons',
        '',
        None, '', False, True,
    ),
    (
        'craftworlds-guardians',
        'Guardians (2022 Edition)',
        54.95,
        'https://www.nobleknight.com/P/2147962130/Guardians-2022-Edition?awid=1576',
        True, False,
    ),
    (
        'craftworlds-wave-serpent',
        'Wave Serpent',
        54.95,
        'https://www.nobleknight.com/P/2148255136/Wave-Serpent?awid=1576',
        True, False,
    ),
    (
        'craftworlds-wraithguard',
        'Wraithguard',
        55.95,
        'https://www.nobleknight.com/P/2148009784/Wraithguard?awid=1576',
        True, False,
    ),

    # ── Phase-3 Aeldari — with NK matches ────────────────────────────────────
    (
        'aeldari-avatar-of-khaine',
        'Avatar of Khaine (2022 Edition)',
        102.95,
        'https://www.nobleknight.com/P/2147968540/Avatar-of-Khaine-2022-Edition?awid=1576',
        True, False,
    ),
    (
        'aeldari-autarch',
        'Autarch (2022 Edition)',
        39.95,
        'https://www.nobleknight.com/P/2147968542/Autarch-2022-Edition?awid=1576',
        True, False,
    ),
    (
        'aeldari-eldrad-ulthran',
        'Eldrad Ulthran',
        35.95,
        'https://www.nobleknight.com/P/2147993158/Eldrad-Ulthran?awid=1576',
        True, False,
    ),
    (
        'aeldari-spiritseer',
        'Spiritseer',
        29.95,
        'https://www.nobleknight.com/P/2148005089/Spiritseer?awid=1576',
        True, False,
    ),
    (
        'aeldari-farseer-skyrunner',
        'Farseer Skyrunner',
        39.95,
        'https://www.nobleknight.com/P/2147966428/Farseer-Skyrunner?awid=1576',
        True, False,
    ),
    (
        'aeldari-warlocks',
        'Warlocks',
        54.95,
        'https://www.nobleknight.com/P/2147962132/Aeldari-Warlocks?awid=1576',
        True, False,
    ),
    (
        'aeldari-maugan-ra',
        'Maugan Ra',
        43.95,
        'https://www.nobleknight.com/P/2147962131/Maugan-Ra?awid=1576',
        True, False,
    ),
    (
        'aeldari-jain-zar',
        'Phoenix Lord Jain Zar',
        43.95,
        'https://www.nobleknight.com/P/2147974195/Phoenix-Lord-Jain-Zar?awid=1576',
        True, False,
    ),
    (
        'aeldari-guardian-defenders',
        'Guardians (2022 Edition)',
        54.95,
        # Same dual-build kit as craftworlds-guardians (Storm Guardians)
        'https://www.nobleknight.com/P/2147962130/Guardians-2022-Edition?awid=1576',
        True, False,
    ),
    (
        'aeldari-rangers',
        'Rangers (2022 Edition)',
        56.95,
        'https://www.nobleknight.com/P/2147968538/Rangers-2022-Edition?awid=1576',
        True, False,
    ),
    (
        'aeldari-howling-banshees',
        # ⚠ NK price of $129.95 is well above $62.50 MSRP — verify if correct
        'Howling Banshees',
        129.95,
        'https://www.nobleknight.com/P/2148009777/Howling-Banshees?awid=1576',
        True, False,
    ),
    (
        'aeldari-shining-spears',
        'Shining Spears',
        62.95,
        'https://www.nobleknight.com/P/2147968539/Shining-Spears?awid=1576',
        True, False,
    ),
    (
        'aeldari-shroud-runners',
        'Shroud Runners',
        62.95,
        'https://www.nobleknight.com/P/2147968537/Shroud-Runners?awid=1576',
        True, False,
    ),
    (
        'aeldari-wraithguard',
        'Wraithguard',
        55.95,
        'https://www.nobleknight.com/P/2148009784/Wraithguard?awid=1576',
        True, False,
    ),
    (
        'aeldari-wraithblades',
        # ⚠ NK only lists "Wraithguard" — same dual-build box
        'Wraithguard',
        55.95,
        'https://www.nobleknight.com/P/2148009784/Wraithguard?awid=1576',
        True, False,
    ),
    (
        'aeldari-wraithknight',
        'Wraithknight',
        153.95,
        'https://www.nobleknight.com/P/2147966367/Wraithknight?awid=1576',
        True, False,
    ),
    (
        'aeldari-crimson-hunter',
        # ⚠ NK combined listing covers both Crimson Hunter and Hemlock
        'Hemlock Wraithfighter/Crimson Hunter',
        86.95,
        'https://www.nobleknight.com/P/2148174004/Hemlock-Wraithfighter-Crimson-Hunter?awid=1576',
        True, False,
    ),
    (
        'aeldari-hemlock-wraithfighter',
        'Hemlock Wraithfighter/Crimson Hunter',
        86.95,
        'https://www.nobleknight.com/P/2148174004/Hemlock-Wraithfighter-Crimson-Hunter?awid=1576',
        True, False,
    ),
    (
        'aeldari-war-walkers',
        'War Walkers',
        72.95,
        'https://www.nobleknight.com/P/2148255223/War-Walkers?awid=1576',
        True, False,
    ),
    (
        'aeldari-harlequin-troupe',
        'Harlequin Troupe',
        43.95,
        'https://www.nobleknight.com/P/2148009785/Harlequin-Troupe?awid=1576',
        True, False,
    ),
    (
        'aeldari-shadowseer',
        'Harlequin Shadowseer',
        31.95,
        'https://www.nobleknight.com/P/2147994370/Harlequin-Shadowseer?awid=1576',
        True, False,
    ),
    (
        'aeldari-death-jester',
        'Harlequin Death Jester',
        31.95,
        'https://www.nobleknight.com/P/2147974284/Harlequin-Death-Jester?awid=1576',
        True, False,
    ),

    # ── Phase-3 Aeldari — NOT on NK ──────────────────────────────────────────
    ('codex-aeldari',               '', None, '', False, True),
    ('aeldari-autarch-wayleaper',   '', None, '', False, True),
    ('aeldari-warlock-skyrunner',   '', None, '', False, True),
    ('aeldari-fuegan',              '', None, '', False, True),
    ('aeldari-baharroth',           '', None, '', False, True),
    ('aeldari-lhykhis',             '', None, '', False, True),
    ('aeldari-asurmen',             '', None, '', False, True),
    ('aeldari-prince-yriel',        '', None, '', False, True),
    ('aeldari-kharseth',            '', None, '', False, True),
    ('aeldari-dark-reapers',        '', None, '', False, True),
    ('aeldari-swooping-hawks',      '', None, '', False, True),
    ('aeldari-warp-spiders',        '', None, '', False, True),
    ('aeldari-windriders',          '', None, '', False, True),
    ('aeldari-corsair-voidreavers', '', None, '', False, True),
    ('aeldari-corsair-skyreavers',  '', None, '', False, True),
    ('aeldari-support-weapon',      '', None, '', False, True),
    ('aeldari-wraithlord',          '', None, '', False, True),
    ('aeldari-fire-prism',          '', None, '', False, True),
    ('aeldari-night-spinner',       '', None, '', False, True),
    ('aeldari-vyper',               '', None, '', False, True),
    ('aeldari-starfang',            '', None, '', False, True),
    ('aeldari-skyweavers',          '', None, '', False, True),
    ('aeldari-starweaver',          '', None, '', False, True),
    ('aeldari-voidweaver',          '', None, '', False, True),
    ('aeldari-solitaire',           '', None, '', False, True),
    ('aeldari-yvraine',             '', None, '', False, True),
    ('aeldari-the-visarch',         '', None, '', False, True),
    ('aeldari-the-yncarne',         '', None, '', False, True),
    ('combat-patrol-aeldari-corsairs', '', None, '', False, True),
]


class Command(BaseCommand):
    """Seed Noble Knight Games prices for all Aeldari products."""

    help = (
        'Seeds Noble Knight Games CurrentPrice entries for Aeldari products '
        '(phase-1 and phase-3). Sourced from NK spreadsheet scrape 2026-04-05. '
        'Affiliate links include ?awid=1576. Idempotent.'
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

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  Skipped (not found): {slug}'))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={
                    'price': price,
                    'url': url,
                    'listing_title': listing_title,
                    'in_stock': in_stock,
                    'not_available': not_available,
                },
            )
            status = 'Created' if created else 'Updated'
            if not_available:
                label = 'Not Available on NK'
            elif price:
                label = f'${price:.2f}'
            else:
                label = 'Price TBD'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {product.name} — {label}'))
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nseed_nk_aeldari_prices complete. '
            f'{created_count} created, {updated_count} updated, {skipped_count} skipped.'
        ))
