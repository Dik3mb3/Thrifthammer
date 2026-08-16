"""
Management command: seed_nk_chaos_necron_prices

Seeds Noble Knight prices for Necrons, Death Guard, Thousand Sons, World Eaters,
and Aeldari phase-3 products.

Source: Warhammer 40,000 - Noble Knight Gamesv3.xlsx (761 rows scraped Apr 2026)
Matching: keyword-based title matching + manual slug verification against DB.

DUPLICATE HANDLING (most recent/current edition used):
  - Tomb Blades: 2021 Edition preferred
  - Ahriman: "Ahriman the Sorcerer" (newest sculpt) preferred
  - Rubric Marines: 2021 preferred
  - Scarab Occult Terminators: 2021 preferred
  - Spiritseer: standard (no year) preferred
  - Death Jester: standard (no year) preferred
  - Nauseous Rotbone (Plague Surgeon): standard preferred
  - Icon Bearer: standard preferred

NOTE (2026-08-16): Combat Patrol, Dire Avengers, Guardians, Wave Serpent, and
Wraithguard were removed from this file. They were seeded here under stale
'craftworlds-*' slugs that no longer match any product (the Aeldari faction
consolidation renamed these to 'aeldari-*'), so these entries were silently
skipped on every run. All five are now correctly seeded in
seed_nk_aeldari_prices.py instead -- including Wave Serpent, whose "2022
Edition preferred" listing here was actually a discontinued/out-of-print
NK listing; the current in-stock listing is used in the Aeldari file.

GAPS - not in NK spreadsheet (NK does not currently stock these):
  Necrons: Trazyn, Illuminor Szeras, Lychguard, Deathmarks, Flayed Ones,
    Night Scythe, Void Dragon, Nightbringer, Monolith, Overlord, Nekrosor,
    Royal Warden, Hexmark Destroyer, Lokhust Destroyers squad
  Death Guard: Plague Marines, Poxwalkers, Plagueburst Crawler, Foetid Bloat-Drone,
    Foul Blightspawn, Biologus Putrifier, Lord of Contagion set
  Thousand Sons: Magnus, Tzaangors, Infernal Master, Exalted Sorcerers, Sekhetar
  World Eaters: Eightbound (base), Kharn, Khorne Berserkers, Slaughterbound
  Aeldari: Warp Spiders, Fire Dragons, Swooping Hawks, Dark Reapers, Striking Scorpions,
    Windriders, Wraithlord, Fire Prism, Night Spinner, Vyper, Starweaver, Voidweaver,
    Falcon, Solitaire, Yvraine, Visarch, Illic Nightspear

Affiliate tag ?awid=1576 appended to all URLs.
Idempotent -- safe to re-run.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

NK_PRICES = [
    # ── NECRONS ──────────────────────────────────────────────────────────────
    ('necron-canoptek-doomstalker', 'Canoptek Doomstalker', 47.95,
     'https://www.nobleknight.com/P/2147838255/Canoptek-Doomstalker?awid=1576', False, False),
    ('necron-canoptek-spyder', 'Canoptek Spyder (2021 Edition)', 43.95,
     'https://www.nobleknight.com/P/2147886329/Canoptek-Spyder?awid=1576', False, False),
    ('necron-canoptek-wraiths', 'Canoptek Wraiths (2020 Edition)', 58.95,
     'https://www.nobleknight.com/P/2147831475/Canoptek-Wraiths-2020-Edition?awid=1576', False, False),
    ('necron-chronomancer', 'Chronomancer', 37.95,
     'https://www.nobleknight.com/P/2147889355/Chronomancer?awid=1576', False, False),
    ('necron-convergence-of-dominion', 'Convergence of Dominion', 62.95,
     'https://www.nobleknight.com/P/2147844405/Convergence-of-Dominion?awid=1576', False, False),
    ('necron-cryptek', 'Cryptek (2020 Edition)', 33.95,
     'https://www.nobleknight.com/P/2147831533/Cryptek-2020-Edition?awid=1576', False, False),
    ('necron-doom-scythe', 'Doom Scythe (2020 Edition)', 69.95,
     'https://www.nobleknight.com/P/2147845817/Doom-Scythe-2020-Edition?awid=1576', False, False),
    # Ghost Ark and Doomsday Ark share the same NK combo-kit listing
    ('necron-ghost-ark', 'Ghost Ark/Doomsday Ark', 62.95,
     'https://www.nobleknight.com/P/2147936588/Ghost-Ark-Doomsday-Ark?awid=1576', False, False),
    ('necron-doomsday-ark', 'Ghost Ark/Doomsday Ark', 62.95,
     'https://www.nobleknight.com/P/2147936588/Ghost-Ark-Doomsday-Ark?awid=1576', False, False),
    ('necron-immortals', 'Immortals', 41.95,
     'https://www.nobleknight.com/P/2147831509/Immortals?awid=1576', False, False),
    ('necron-imotekh-the-stormlord', 'Imotekh the Stormlord', 43.95,
     'https://www.nobleknight.com/P/2148098550/Imotekh-the-Stormlord?awid=1576', False, False),
    ('necron-lokhust-heavy-destroyer', 'Lokhusts Heavy Destroyer', 35.95,
     'https://www.nobleknight.com/P/2147838256/Lokhusts-Heavy-Destroyer?awid=1576', False, False),
    ('necron-ophydian-destroyers', 'Ophydian Destroyers', 58.95,
     'https://www.nobleknight.com/P/2147844407/Ophydian-Destroyers?awid=1576', False, False),
    ('necron-orikan-the-diviner', 'Orikan the Diviner', 43.95,
     'https://www.nobleknight.com/P/2148098554/Orikan-the-Diviner?awid=1576', False, False),
    ('necron-psychomancer', 'Psychomancer', 35.95,
     'https://www.nobleknight.com/P/2147864794/Psychomancer?awid=1576', False, False),
    ('necron-skorpekh-destroyers', 'Skorpekh Destroyers', 58.95,
     'https://www.nobleknight.com/P/2147841727/Skorpekh-Destroyers?awid=1576', False, False),
    ('necron-szarekh-the-silent-king', 'Szarekh, The Silent King', 157.95,
     'https://www.nobleknight.com/P/2147838254/Szarekh-the-Silent-King?awid=1576', False, False),
    # Tomb Blades: 2021 edition preferred over 2018
    ('necron-tomb-blades', 'Tomb Blades (2021 Edition)', 54.95,
     'https://www.nobleknight.com/P/2147886189/Tomb-Blades?awid=1576', False, False),
    ('necron-triarch-praetorians', 'Triarch Praetorians (2020 Edition)', 51.95,
     'https://www.nobleknight.com/P/2147831489/Triarch-Praetorians-2020-Edition?awid=1576', False, False),
    ('necron-triarch-stalker', 'Triarch Stalker (2020 Edition)', 58.95,
     'https://www.nobleknight.com/P/2147895501/Triarch-Stalker?awid=1576', False, False),

    # ── DEATH GUARD ──────────────────────────────────────────────────────────
    ('death-guard-blightlord-terminators', 'Blightlord Terminators', 58.95,
     'https://www.nobleknight.com/P/2147857649/Blightlord-Terminators?awid=1576', False, False),
    ('death-guard-deathshroud-bodyguard', 'Deathshroud Bodyguard', 58.95,
     'https://www.nobleknight.com/P/2147920323/Deathshroud-Bodyguard?awid=1576', False, False),
    ('death-guard-lord-of-virulence', 'Lord of Virulence', 39.95,
     'https://www.nobleknight.com/P/2147860483/Lord-of-Virulence?awid=1576', False, False),
    ('death-guard-miasmic-malignifier', 'Miasmic Malignifier', 62.95,
     'https://www.nobleknight.com/P/2147860490/Miasmic-Malignifier?awid=1576', False, False),
    ('death-guard-mortarion-daemon-primarch', 'Mortarion - Daemon Primarch of Nurgle', 157.95,
     'https://www.nobleknight.com/P/2147865408/Mortarion---Daemon-Primarch-of-Nurgle?awid=1576', False, False),
    ('death-guard-myphitic-blight-hauler', 'Myphitic Blight-Hauler', 27.95,
     'https://www.nobleknight.com/P/2147889284/Myphitic-Blight-Hauler?awid=1576', False, False),
    # Plague Surgeon = Nauseous Rotbone; standard edition preferred
    ('death-guard-plague-surgeon', 'Nauseous Rotbone, The Plague Surgeon', 31.95,
     'https://www.nobleknight.com/P/2147857605/Nauseous-Rotbone-The-Plague-Surgeon?awid=1576', False, False),
    ('death-guard-plague-marine-champion', 'Plague Marine Champion', 31.95,
     'https://www.nobleknight.com/P/2147996480/Plague-Marine-Champion?awid=1576', False, False),
    # Icon Bearer: standard preferred over 2017
    ('death-guard-icon-bearer', 'Plague Marine Icon Bearer', 29.95,
     'https://www.nobleknight.com/P/2147922353/Plague-Marine-Icon-Bearer-2017-Edition?awid=1576', False, False),
    ('death-guard-tallyman', 'Scribbus Wretch, the Tallyman', 31.95,
     'https://www.nobleknight.com/P/2147940219/Scribbus-Wretch-the-Tallyman?awid=1576', False, False),
    ('death-guard-typhus', 'Typhus - Herald of the Plague God', 43.95,
     'https://www.nobleknight.com/P/2147946040/Typhus---Herald-of-the-Plague-God?awid=1576', False, False),

    # ── THOUSAND SONS ────────────────────────────────────────────────────────
    # Ahriman: most recent sculpt preferred
    ('thousand-sons-ahriman', 'Ahriman the Sorcerer', 43.95,
     'https://www.nobleknight.com/P/2147936751/Ahriman-the-Sorcerer?awid=1576', False, False),
    # Rubric Marines: 2021 edition preferred
    ('thousand-sons-rubric-marines', 'Rubric Marines', 55.95,
     'https://www.nobleknight.com/P/2147930748/Rubric-Marines?awid=1576', False, False),
    # Scarab Occult: 2021 edition preferred
    ('thousand-sons-scarab-occult-terminators', 'Scarab Occult Terminators (2021 Edition)', 58.95,
     'https://www.nobleknight.com/P/2147936762/Scarab-Occult-Terminators-2021-Edition?awid=1576', False, False),

    # ── WORLD EATERS ─────────────────────────────────────────────────────────
    ('world-eaters-angron', 'Angron, Daemon Primarch of Khorne', 150.95,
     'https://www.nobleknight.com/P/2148034914/Angron-Daemon-Primarch-of-Khorne?awid=1576', False, False),
    ('world-eaters-exalted-eightbound', 'Exalted Eightbound', 55.95,
     'https://www.nobleknight.com/P/2148034918/Exalted-Eightbound?awid=1576', False, False),
    ('world-eaters-jakhals', 'Jakhals', 51.95,
     'https://www.nobleknight.com/P/2148034919/Jakhals?awid=1576', False, False),
    ('world-eaters-lord-invocatus', 'Lord Invocatus', 62.95,
     'https://www.nobleknight.com/P/2148034922/Lord-Invocatus?awid=1576', False, False),

    # ── AELDARI (Craftworlds + Harlequins) ───────────────────────────────────
    ('aeldari-autarch', 'Autarch (2022 Edition)', 39.95,
     'https://www.nobleknight.com/P/2147968542/Autarch-2022-Edition?awid=1576', False, False),
    ('aeldari-eldrad-ulthran', 'Eldrad Ulthran', 35.95,
     'https://www.nobleknight.com/P/2147993158/Eldrad-Ulthran?awid=1576', False, False),
    ('aeldari-farseer-skyrunner', 'Farseer Skyrunner', 39.95,
     'https://www.nobleknight.com/P/2147966428/Farseer-Skyrunner?awid=1576', False, False),
    # Hemlock/Crimson Hunter share the same NK combo-kit listing
    ('aeldari-hemlock-wraithfighter', 'Hemlock Wraithfighter/Crimson Hunter', 86.95,
     'https://www.nobleknight.com/P/2148174004/Hemlock-Wraithfighter-Crimson-Hunter?awid=1576', False, False),
    ('aeldari-crimson-hunter', 'Hemlock Wraithfighter/Crimson Hunter', 86.95,
     'https://www.nobleknight.com/P/2148174004/Hemlock-Wraithfighter-Crimson-Hunter?awid=1576', False, False),
    ('aeldari-howling-banshees', 'Howling Banshees', 129.95,
     'https://www.nobleknight.com/P/2148009777/Howling-Banshees?awid=1576', False, False),
    ('aeldari-rangers', 'Rangers (2022 Edition)', 56.95,
     'https://www.nobleknight.com/P/2147968538/Rangers-2022-Edition?awid=1576', False, False),
    ('aeldari-shining-spears', 'Shining Spears', 62.95,
     'https://www.nobleknight.com/P/2147968539/Shining-Spears?awid=1576', False, False),
    ('aeldari-shroud-runners', 'Shroud Runners', 62.95,
     'https://www.nobleknight.com/P/2147968537/Shroud-Runners?awid=1576', False, False),
    ('aeldari-spiritseer', 'Spiritseer', 29.95,
     'https://www.nobleknight.com/P/2148005089/Spiritseer?awid=1576', False, False),
    ('aeldari-war-walkers', 'War Walkers', 72.95,
     'https://www.nobleknight.com/P/2148255223/War-Walkers?awid=1576', False, False),
    ('aeldari-warlocks', 'Warlocks', 54.95,
     'https://www.nobleknight.com/P/2147962132/Aeldari-Warlocks?awid=1576', False, False),
    ('aeldari-wraithknight', 'Wraithknight', 153.95,
     'https://www.nobleknight.com/P/2147966367/Wraithknight?awid=1576', False, False),
    # Harlequins
    ('aeldari-death-jester', 'Harlequin Death Jester', 31.95,
     'https://www.nobleknight.com/P/2147974284/Harlequin-Death-Jester?awid=1576', False, False),
    ('aeldari-shadowseer', 'Harlequin Shadowseer', 31.95,
     'https://www.nobleknight.com/P/2147994370/Harlequin-Shadowseer?awid=1576', False, False),
    ('aeldari-harlequin-troupe', 'Harlequin Troupe', 43.95,
     'https://www.nobleknight.com/P/2148009785/Harlequin-Troupe?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Necrons, Death Guard, TS, WE, and Aeldari."""

    help = (
        'Seeds Noble Knight listing URLs and prices for Necrons, Death Guard, '
        'Thousand Sons, World Eaters, and Aeldari. Idempotent.'
    )

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
            self.stdout.write(f'  {status}: {product.name} @ ${price}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Seeded={seeded}, Missing={missing}'
        ))
