"""
Management command: seed_mm_chaos_necron_prices

Seeds Miniature Market CurrentPrice entries for Necrons, Death Guard,
Thousand Sons, World Eaters, and associated daemon products.

Source: Miniature Market - Warhammer 40K ALL SKUS.xlsx (scraped Apr 2026)
Matching: keyword + SKU matching against MM URLs, verified against DB slugs.

SHARED-KIT ENTRIES (one MM listing, two DB slugs):
  - Immortals / Deathmarks              -> gw-49-10.html
  - Lychguard / Triarch Praetorians     -> gw-49-07.html
  - Ghost Ark / Doomsday Ark            -> gw-49-11.html
  - Catacomb Command Barge / Ann. Barge -> gw-49-12.html
  - Doom Scythe / Night Scythe          -> gw-49-15.html
  - Rotigus / Great Unclean One         -> gw-83-41.html

NOTE: DB gw_sku values don't always match MM catalog numbers
  (DB stores GW schema.org IDs; MM uses its own numbering).
  All MM URLs below are taken directly from the Excel source.

GAPS - no MM listing found for these DB products:
  Necrons:     Trazyn the Infinite, Royal Warden, Nekrosor Ammentar
               (Nightbringer, Void Dragon: not in catalog)
  Death Guard: Lord of Poxes (2025, P-* SKU only)
  World Eaters: Eightbound (base), Slaughterbound, Lord on Juggernaut,
                Lord of Skulls, Kill Team Goremongers
  Daemons:     Nurglings, Bloodcrushers, Skarbrand, Blue/Brimstone Horrors,
               Screamers of Tzeentch, Kairos Fateweaver

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_mm_chaos_necron_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

MM_BASE = 'https://www.miniaturemarket.com/'

# (slug, listing_title, price, url, in_stock)
# All prices sourced from MM Excel scrape Apr 2026.
# All items are Out of Stock unless noted.
MM_PRICES = [
    # ── NECRONS ──────────────────────────────────────────────────────────────
    # Immortals and Deathmarks are the same dual-build kit (gw-49-10)
    (
        'necron-immortals',
        'Necron Immortals/Deathmarks',
        38.99,
        MM_BASE + 'gw-49-10.html',
        False,
    ),
    (
        'necron-deathmarks',
        'Necron Immortals/Deathmarks',
        38.99,
        MM_BASE + 'gw-49-10.html',
        False,
    ),
    (
        'necron-warriors',
        'Necrons - Warriors',
        44.99,
        MM_BASE + 'gw-49-06-270080.html',
        False,
    ),
    # Lychguard and Triarch Praetorians share the same dual-build kit (gw-49-07)
    (
        'necron-lychguard',
        'Necron Lychguard/Triarch Praetorians',
        51.00,
        MM_BASE + 'gw-49-07.html',
        False,
    ),
    (
        'necron-triarch-praetorians',
        'Necron Lychguard/Triarch Praetorians',
        51.00,
        MM_BASE + 'gw-49-07.html',
        False,
    ),
    # Ghost Ark and Doomsday Ark share the same dual-build kit (gw-49-11)
    (
        'necron-ghost-ark',
        'Necron Ghost Ark/Doomsday Ark',
        55.99,
        MM_BASE + 'gw-49-11.html',
        False,
    ),
    (
        'necron-doomsday-ark',
        'Necron Ghost Ark/Doomsday Ark',
        55.99,
        MM_BASE + 'gw-49-11.html',
        False,
    ),
    # Catacomb Command Barge and Annihilation Barge share the same kit (gw-49-12)
    (
        'necron-catacomb-command-barge',
        'Necron Catacomb Command Barge/Annihilation Barge',
        51.00,
        MM_BASE + 'gw-49-12.html',
        False,
    ),
    (
        'necron-annihilation-barge',
        'Necron Catacomb Command Barge/Annihilation Barge',
        51.00,
        MM_BASE + 'gw-49-12.html',
        False,
    ),
    (
        'necron-tomb-blades',
        'Necron Tomb Blades',
        51.00,
        MM_BASE + 'gw-49-13.html',
        False,
    ),
    (
        'necron-canoptek-wraiths',
        'Necrons - Canoptek Wraiths',
        53.99,
        MM_BASE + 'gw-49-14.html',
        False,
    ),
    # Doom Scythe and Night Scythe are the same dual-build kit (gw-49-15)
    (
        'necron-doom-scythe',
        'Necron Doom Scythe/Night Scythe',
        63.99,
        MM_BASE + 'gw-49-15.html',
        False,
    ),
    (
        'necron-night-scythe',
        'Necron Doom Scythe/Night Scythe',
        63.99,
        MM_BASE + 'gw-49-15.html',
        False,
    ),
    (
        'necron-canoptek-spyder',
        'Necron Canoptek Spyder',
        38.99,
        MM_BASE + 'gw-49-16.html',
        False,
    ),
    (
        'necron-triarch-stalker',
        'Necron Triarch Stalker',
        53.99,
        MM_BASE + 'gw-49-18.html',
        False,
    ),
    (
        'necron-cryptek',
        'Necrons - Cryptek',
        31.99,
        MM_BASE + 'gw-49-22.html',
        False,
    ),
    (
        'necron-convergence-of-dominion',
        'Necrons - Convergence of Dominion',
        55.99,
        MM_BASE + 'gw-49-25.html',
        False,
    ),
    (
        'necron-szarekh-the-silent-king',
        'Necrons - Szarekh, the Silent King',
        144.99,
        MM_BASE + 'gw-49-26.html',
        False,
    ),
    (
        'necron-hexmark-destroyer',
        'Necrons - Hexmark Destroyer',
        31.99,
        MM_BASE + 'gw-49-27.html',
        False,
    ),
    # Push-fit/Easy-to-Build version -- only MM listing for this unit
    (
        'necron-lokhust-heavy-destroyer',
        'Necrons - Lokhusts Heavy Destroyer (Push-fit)',
        31.99,
        MM_BASE + 'gw-49-28.html',
        False,
    ),
    # Push-fit/Easy-to-Build version -- only MM listing for this unit
    (
        'necron-canoptek-doomstalker',
        'Necrons - Canoptek Doomstalker (Push-fit)',
        44.99,
        MM_BASE + 'gw-49-29.html',
        False,
    ),
    (
        'necron-skorpekh-destroyers',
        'Necrons - Skorpekh Destroyers',
        53.99,
        MM_BASE + 'gw-49-31.html',
        False,
    ),
    (
        'necron-ophydian-destroyers',
        'Necrons - Ophydian Destroyers',
        53.99,
        MM_BASE + 'gw-49-32.html',
        False,
    ),
    (
        'necron-psychomancer',
        'Necrons - Psychomancer',
        31.99,
        MM_BASE + 'gw-49-33.html',
        False,
    ),
    (
        'necron-flayed-ones',
        'Necrons - Flayed Ones',
        49.99,
        MM_BASE + 'gw-49-42.html',
        False,
    ),
    (
        'necron-chronomancer',
        'Necrons - Chronomancer',
        35.99,
        MM_BASE + 'gw-49-45.html',
        False,
    ),
    (
        'necron-imotekh-the-stormlord',
        'Necrons - Imotekh the Stormlord',
        38.99,
        MM_BASE + 'warhammer-40k-necrons-imotekh-stormlord-gw-49-63.html',
        False,
    ),
    (
        'necron-illuminor-szeras',
        'Necrons - Illuminor Szeras',
        51.00,
        MM_BASE + 'gw-49-66.html',
        False,
    ),
    (
        'necron-orikan-the-diviner',
        'Necrons - Orikan the Diviner',
        38.99,
        MM_BASE + 'warhammer-40k-necrons-orikan-diviner-gw-49-67.html',
        False,
    ),
    # "Overlord with Translocation Shroud" is the current standard Necron Overlord
    (
        'necron-overlord',
        'Necrons - Overlord with Translocation Shroud',
        33.99,
        MM_BASE + 'warhammer-40k-necrons-overlord-with-translocation-shroud-gw-49-70.html',
        False,
    ),

    # ── DEATH GUARD ──────────────────────────────────────────────────────────
    (
        'death-guard-biologus-putrifier',
        'Death Guard - Biologus Putrifier',
        29.99,
        MM_BASE + 'gw-43-24.html',
        False,
    ),
    (
        'death-guard-plague-surgeon',
        'Death Guard - Nauseous Rotbone the Plague Surgeon',
        29.99,
        MM_BASE + 'gw-43-29.html',
        False,
    ),
    (
        'death-guard-tallyman',
        'Death Guard - Scribbus Wretch the Tallyman',
        29.99,
        MM_BASE + 'gw-43-45.html',
        False,
    ),
    (
        'death-guard-foul-blightspawn',
        'Death Guard - Foul Blightspawn',
        29.99,
        MM_BASE + 'gw-43-46.html',
        False,
    ),
    (
        'death-guard-icon-bearer',
        'Death Guard - Plague Marine Icon Bearer',
        29.99,
        MM_BASE + 'gw-43-47.html',
        False,
    ),
    (
        'death-guard-plague-marine-champion',
        'Death Guard - Plague Marine Champion',
        29.99,
        MM_BASE + 'gw-43-48.html',
        False,
    ),
    (
        'death-guard-mortarion-daemon-primarch',
        'Death Guard Daemon Primarch Mortarion',
        144.99,
        MM_BASE + 'gw-43-49.html',
        False,
    ),
    (
        'death-guard-deathshroud-bodyguard',
        'Death Guard Deathshroud Bodyguard',
        53.99,
        MM_BASE + 'gw-43-50.html',
        False,
    ),
    (
        'death-guard-blightlord-terminators',
        'Death Guard - Blightlord Terminators',
        53.99,
        MM_BASE + 'gw-43-51.html',
        False,
    ),
    (
        'death-guard-plagueburst-crawler',
        'Death Guard - Plagueburst Crawler',
        67.99,
        MM_BASE + 'gw-43-52.html',
        False,
    ),
    (
        'death-guard-typhus',
        'Death Guard - Typhus, Herald of the Plague God',
        38.99,
        MM_BASE + 'gw-43-53.html',
        False,
    ),
    (
        'death-guard-foetid-bloat-drone',
        'Death Guard - Foetid Bloat-Drone',
        51.00,
        MM_BASE + 'gw-43-54.html',
        False,
    ),
    (
        'death-guard-plague-marines',
        'Death Guard - Plague Marines',
        51.00,
        MM_BASE + 'gw-43-55.html',
        False,
    ),
    # Easy-to-Build/push-fit kit -- only MM listing for Myphitic Blight-Hauler
    (
        'death-guard-myphitic-blight-hauler',
        'Easy to Build Death Guard Myphitic Blight-hauler',
        25.99,
        MM_BASE + 'gw-43-56.html',
        False,
    ),
    (
        'death-guard-poxwalkers',
        'Death Guard - Poxwalkers',
        31.99,
        MM_BASE + 'gw-43-76.html',
        False,
    ),
    (
        'death-guard-lord-of-virulence',
        'Death Guard - Lord of Virulence',
        35.99,
        MM_BASE + 'gw-43-77.html',
        False,
    ),
    (
        'death-guard-miasmic-malignifier',
        'Death Guard - Miasmic Malignifier',
        55.99,
        MM_BASE + 'gw-43-78.html',
        False,
    ),

    # ── THOUSAND SONS ────────────────────────────────────────────────────────
    (
        'thousand-sons-magnus-the-red',
        'Thousand Sons Magnus the Red',
        144.99,
        MM_BASE + 'gw-43-34.html',
        False,
    ),
    (
        'thousand-sons-rubric-marines',
        'Thousand Sons - Rubric Marines',
        53.99,
        MM_BASE + 'gw-43-35.html',
        False,
    ),
    (
        'thousand-sons-scarab-occult-terminators',
        'Thousand Sons Scarab Occult Terminators',
        53.99,
        MM_BASE + 'gw-43-36.html',
        False,
    ),
    # Ahriman: MM SKU 43-38 (DB gw_sku 43-30 is a GW schema.org ID mismatch)
    (
        'thousand-sons-ahriman',
        'Ahriman, Arch-Sorcerer of Tzeentch',
        38.99,
        MM_BASE + 'gw-43-38.html',
        False,
    ),
    # Exalted Sorcerers: MM SKU 43-39 (DB gw_sku 43-38 is a mismatch)
    (
        'thousand-sons-exalted-sorcerers',
        'Thousand Sons Exalted Sorcerers',
        53.99,
        MM_BASE + 'gw-43-39.html',
        False,
    ),
    (
        'thousand-sons-infernal-master',
        'Thousand Sons - Infernal Master',
        35.99,
        MM_BASE + 'gw-43-79.html',
        False,
    ),
    # Non-standard MM URL (2025 release)
    (
        'thousand-sons-sekhetar-robots',
        'Thousand Sons - Sekhetar Robots',
        42.99,
        MM_BASE + 'Warhammer-40K-Thousand-Sons-Sekhetar-Robots/GW-36-03',
        False,
    ),

    # ── WORLD EATERS ─────────────────────────────────────────────────────────
    # Angron: MM SKU 43-28 (DB gw_sku 43-04 is a GW internal ID mismatch)
    (
        'world-eaters-angron',
        'World Eaters - Angron, Daemon Primarch of Khorne',
        144.99,
        MM_BASE + 'warhammer-40k-world-eaters-angron-daemon-primarch-of-khorne-gw-43-28.html',
        False,
    ),
    # Kharn: listed under Chaos Space Marines on MM
    (
        'world-eaters-kharn-the-betrayer',
        'Chaos Space Marines Kharn the Betrayer',
        35.99,
        MM_BASE + 'gw-43-25.html',
        False,
    ),
    # Berzerkers: non-standard MM URL (2023 World Eaters kit)
    (
        'world-eaters-berzerkers',
        'World Eaters - Khorne Berserkers',
        55.99,
        MM_BASE + 'warhammer-40k-world-eaters-khorne-berserkers-gw-43-10-2023.html',
        False,
    ),
    (
        'world-eaters-exalted-eightbound',
        'World Eaters - Exalted Eightbound',
        53.99,
        MM_BASE + 'warhammer-40k-world-eaters-exalted-eightbound-gw-43-72.html',
        False,
    ),
    (
        'world-eaters-jakhals',
        'World Eaters - Jakhals',
        49.99,
        MM_BASE + 'warhammer-40k-world-eaters-jakhals-gw-43-57-2023.html',
        False,
    ),
    (
        'world-eaters-lord-invocatus',
        'World Eaters - Lord Invocatus',
        55.99,
        MM_BASE + 'warhammer-40k-world-eaters-lord-invocatus-gw-43-26-2023.html',
        False,
    ),

    # ── NURGLE DAEMONS ───────────────────────────────────────────────────────
    (
        'nurgle-plaguebearers',
        'Chaos Demons - Plaguebearers',
        35.99,
        MM_BASE + 'gw-97-10.html',
        False,
    ),
    # Great Unclean One and Rotigus are the same dual-build kit (gw-83-41)
    (
        'nurgle-great-unclean-one',
        'Daemons of Nurgle - Great Unclean One',
        142.99,
        MM_BASE + 'gw-83-41.html',
        False,
    ),
    (
        'nurgle-rotigus',
        'Daemons of Nurgle - Great Unclean One',
        142.99,
        MM_BASE + 'gw-83-41.html',
        False,
    ),
    (
        'nurgle-beast-of-nurgle',
        'Daemons of Nurgle - Beast of Nurgle',
        49.99,
        MM_BASE + 'gw-83-15.html',
        False,
    ),

    # ── KHORNE DAEMONS ───────────────────────────────────────────────────────
    (
        'khorne-bloodletters',
        'Daemons of Khorne - Bloodletters',
        35.99,
        MM_BASE + 'gw-97-08.html',
        False,
    ),
    (
        'khorne-bloodthirster',
        'Daemons of Khorne - Bloodthirster',
        142.99,
        MM_BASE + 'gw-97-27.html',
        False,
    ),
    (
        'khorne-flesh-hounds',
        'Daemons of Khorne - Flesh Hounds',
        51.00,
        MM_BASE + 'gw-97-63.html',
        False,
    ),

    # ── TZEENTCH DAEMONS ─────────────────────────────────────────────────────
    (
        'tzeentch-pink-horrors',
        'Daemons of Tzeentch - Pink Horrors',
        38.99,
        MM_BASE + 'gw-97-12.html',
        False,
    ),
    (
        'tzeentch-flamers',
        'Daemons of Tzeentch - Flamers',
        31.99,
        MM_BASE + 'gw-97-13.html',
        False,
    ),
    (
        'tzeentch-lord-of-change',
        'Daemons of Tzeentch - Lord of Change',
        142.99,
        MM_BASE + 'gw-97-26.html',
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Necrons, Death Guard, TS, WE, and daemons."""

    help = (
        'Seeds Miniature Market listing URLs and prices for Necrons, Death Guard, '
        'Thousand Sons, World Eaters, and their daemon allies. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stderr.write(self.style.ERROR(
                'Miniature Market retailer not found -- run populate_products first.'
            ))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for (slug, listing_title, price, url, in_stock) in MM_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  Skipped (product not found): {slug}'
                ))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
                defaults={
                    'price': price,
                    'url': url,
                    'listing_title': listing_title,
                    'in_stock': in_stock,
                    'not_available': False,
                },
            )
            status = 'Created' if created else 'Updated'
            stock_label = 'In Stock' if in_stock else 'Out of Stock'
            self.stdout.write(
                self.style.SUCCESS(
                    f'  {status}: {product.name} -- ${price:.2f} ({stock_label})'
                )
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created={created_count}, Updated={updated_count}, '
            f'Skipped={skipped_count}'
        ))
