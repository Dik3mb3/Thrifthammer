"""
Management command: populate_deathguard_phase3_products

Adds Death Guard phase-3 products scraped from:
https://www.warhammer.com/en-US/shop/warhammer-40000/armies-of-chaos/death-guard

SKIPPED (already in DB): Blightlord Terminators, Combat Patrol, Deathshroud Bodyguard,
  Foetid Bloat-drone, Mortarion, Plague Marines, Poxwalkers, Typhus
SKIPPED (shared units already in DB faction=4): Daemon Prince, Chaos Rhino, Chaos Predator,
  Chaos Land Raider, Forgefiend, Heldrake, Maulerfiend, Chaos Spawn, Defiler (added in TS)
SKIPPED (AoS duplicate): Plaguebearers already in DB as maggotkin-of-nurgle-plaguebearers

FLAGGED - missing image (CAPTCHA blocked product page during scrape):
  - nurgle-rotigus          image_filename='' needs manual update
  - nurgle-great-unclean-one image_filename='' needs manual update

Faction assignments:
  faction=death-guard       DG-specific units
  faction=chaos-space-marines Helbrute (shared CSM unit)
  faction=maggotkin-of-nurgle Nurgle daemon models (consistent with existing plaguebearers)

Idempotent -- safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

GW_BASE = 'https://www.warhammer.com/en-US/shop/'
GW_IMG_BASE = 'https://www.warhammer.com/app/resources/catalog/product/920x950/'

# (slug, name, gw_sku, msrp, image_filename, gw_url_slug, ebay_search_name, faction_slug)
PRODUCTS = [
    # -- Death Guard specific -------------------------------------------------
    (
        'death-guard-lord-of-poxes',
        'Death Guard Lord of Poxes',
        'P-223010-99120102198',
        43.50,
        '99120102198_ChaosSpaceMarineDeathGuardLordofPoxes1.jpg',
        'death-guard-lord-of-poxes-2025',
        'Death Guard Lord of Poxes Warhammer',
        'death-guard',
    ),
    (
        'death-guard-lord-of-contagion-blightlord-terminators',
        'Death Guard Lord of Contagion and Blightlord Terminators',
        'prod4650190-99120102150',
        48.00,
        '99120102150_LordFelthiusCohortLead.jpg',
        'Lord-Felthius-And-The-Tainted-Cohort-2021',
        'Lord of Contagion Blightlord Terminators Death Guard Warhammer',
        'death-guard',
    ),
    (
        'death-guard-icon-bearer',
        'Death Guard Plague Marine Icon Bearer',
        '43-47',
        35.00,
        '99070102006_DGIconBearer01.jpg',
        'Death-Guard-Plague-Marine-Icon-Bearer-2020',
        'Death Guard Icon Bearer Plague Marine Warhammer',
        'death-guard',
    ),
    (
        'death-guard-myphitic-blight-hauler',
        'Death Guard Myphitic Blight-hauler',
        '43-56',
        32.00,
        '99120102080_ETBDeathGuardBlighthauler01.jpg',
        'Etb-Death-Guard-Myphitic-Blight-hauler-2020',
        'Death Guard Myphitic Blight Hauler Warhammer',
        'death-guard',
    ),
    (
        'death-guard-tallyman',
        'Death Guard Tallyman',
        '43-45',
        35.00,
        '99070102003_DeathGuardScribbusWretch01.jpg',
        'Death-Guard-Scribbus-Wretch-2020',
        'Death Guard Tallyman Scribbus Wretch Warhammer',
        'death-guard',
    ),
    (
        'death-guard-plagueburst-crawler',
        'Death Guard Plagueburst Crawler',
        '43-52',
        80.00,
        '99120102075_Crawler01.jpg',
        'Death-Guard-Plagueburst-Crawler-2020',
        'Death Guard Plagueburst Crawler Warhammer',
        'death-guard',
    ),
    (
        'death-guard-plague-surgeon',
        'Death Guard Plague Surgeon',
        '43-29',
        35.00,
        '99070102004_Rotbone01.jpg',
        'Death-Guard-Nauseous-Rotbone-2020',
        'Death Guard Plague Surgeon Nauseous Rotbone Warhammer',
        'death-guard',
    ),
    (
        'death-guard-foul-blightspawn',
        'Death Guard Foul Blightspawn',
        '43-46',
        35.00,
        '99070102002_DeathGuardFoulBlightSpawn01.jpg',
        'Death-Guard-Foul-Blightspawn-2020',
        'Death Guard Foul Blightspawn Warhammer',
        'death-guard',
    ),
    (
        'death-guard-biologus-putrifier',
        'Death Guard Biologus Putrifier',
        '43-24',
        35.00,
        '99070102005_BiologusPutrifier01.jpg',
        'Death-Guard-Biologus-Putrifier-2020',
        'Death Guard Biologus Putrifier Warhammer',
        'death-guard',
    ),
    (
        'death-guard-miasmic-malignifier',
        'Death Guard Miasmic Malignifier',
        '43-78',
        69.00,
        '99120102118_DGMiasmicMalignifierLead.jpg',
        'Death-Guard-Miasmic-Malignifier-2020',
        'Death Guard Miasmic Malignifier Warhammer',
        'death-guard',
    ),
    (
        'death-guard-lord-of-virulence',
        'Death Guard Lord of Virulence',
        '43-77',
        43.50,
        '99120102117_DGLordofVirulenceLead.jpg',
        'Death-Guard-Lord-of-Virulence-2020',
        'Death Guard Lord of Virulence Warhammer',
        'death-guard',
    ),
    (
        'death-guard-chosen-of-mortarion',
        'Death Guard Malignant Plaguecaster, Noxious Blightbringer & Plague Marine Champion',
        'prod4570149-99120102114',
        73.50,
        '99120102114_DGChosenofMortarionLead.jpg',
        'Death-Guard-Chosen-Of-Mortarion-2020',
        'Death Guard Chosen Mortarion Plaguecaster Blightbringer Warhammer',
        'death-guard',
    ),
    (
        'death-guard-plague-marine-champion',
        'Death Guard Plague Marine Champion',
        '43-48',
        35.00,
        '99070102007_DeathguardChampion01.jpg',
        'Death-Guard-Plague-Marine-Champion-2020',
        'Death Guard Plague Marine Champion Warhammer',
        'death-guard',
    ),
    # -- Shared Chaos Space Marine (Helbrute on DG page) ----------------------
    (
        'chaos-helbrute',
        'Chaos Helbrute',
        'prod2430129-99120102043',
        65.00,
        '99120102043_CSMHelbrute01.jpg',
        'Helbrute',
        'Chaos Helbrute Warhammer 40k',
        'chaos-space-marines',
    ),
    # -- Nurgle Daemons (on DG page, faction=maggotkin-of-nurgle) -------------
    # FLAGGED: image_filename empty -- CAPTCHA blocked during scrape
    (
        'nurgle-rotigus',
        'Rotigus',
        'P-NURGLE-ROTIGUS',
        170.00,
        '',
        'Rotigus-Rainmaker',
        'Rotigus Nurgle Daemon Warhammer',
        'maggotkin-of-nurgle',
    ),
    # FLAGGED: image_filename empty -- CAPTCHA blocked during scrape
    (
        'nurgle-great-unclean-one',
        'Great Unclean One',
        'P-NURGLE-GUO',
        170.00,
        '',
        'Great-Unclean-One-2018',
        'Great Unclean One Nurgle Daemon Warhammer',
        'maggotkin-of-nurgle',
    ),
    (
        'nurgle-beast-of-nurgle',
        'Beast of Nurgle',
        'prod3700246-99129915062',
        60.00,
        '99129915044_BeastofNurgle01.jpg',
        'Beast-Of-Nurgle-2018',
        'Beast of Nurgle Daemon Warhammer',
        'maggotkin-of-nurgle',
    ),
    (
        'nurgle-plague-drones',
        'Plague Drones of Nurgle',
        'prod3610130-99129915038',
        65.00,
        '99129915017_PlagueDrones01.jpg',
        'plague-drones-of-nurgle-2017',
        'Plague Drones Nurgle Daemon Warhammer',
        'maggotkin-of-nurgle',
    ),
    (
        'nurgle-nurglings',
        'Nurglings',
        'prod3550127-99129915060',
        39.00,
        '99129915037_Nurglings01.jpg',
        'Nurglings-2017',
        'Nurglings Nurgle Daemon Warhammer',
        'maggotkin-of-nurgle',
    ),
    # -- Nurgle Daemons AoS/40K shared ----------------------------------------
    # Plaguebearers: existing DB entry is 'maggotkin-of-nurgle-plaguebearers' (faction=38).
    # Adding 40K variant per user instruction to tag shared AoS/40K units to both factions.
    (
        'nurgle-plaguebearers',
        'Plaguebearers of Nurgle',
        'P-NURGLE-PLAGUEBEARERS-40K',
        43.50,
        '99129915018_Plaguebearers01.jpg',
        'Chaos-Daemons-Plaguebearers-of-Nurgle-2018',
        'Plaguebearers Nurgle Daemon Warhammer',
        'maggotkin-of-nurgle',
    ),
    # -- Codex ----------------------------------------------------------------
    (
        'codex-death-guard',
        'Codex: Death Guard',
        'P-213409-60030102032',
        60.00,
        '60030102032_EFGISDGCodex01.jpg',
        'codex-death-guard-hb-2025-eng',
        'Codex Death Guard Warhammer 40k 10th edition',
        'death-guard',
    ),
]


class Command(BaseCommand):
    """Seed Death Guard phase-3 products into the database."""

    help = 'Populates Death Guard phase-3 products. Idempotent via update_or_create on slug.'

    def handle(self, *args, **options):
        """Run the command."""
        faction_cache = {}

        def get_faction(slug):
            """Return cached Faction object by slug."""
            if slug not in faction_cache:
                try:
                    faction_cache[slug] = Faction.objects.get(slug=slug)
                except Faction.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  Faction not found: {slug}'))
                    faction_cache[slug] = None
            return faction_cache[slug]

        created_count = 0
        updated_count = 0

        for slug, name, gw_sku, msrp, img, gw_url_slug, ebay_name, faction_slug in PRODUCTS:
            faction = get_faction(faction_slug)
            obj, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': (GW_IMG_BASE + img) if img else '',
                    'gw_url': GW_BASE + gw_url_slug,
                    'ebay_search_name': ebay_name,
                    'faction': faction,
                    'batch_tag': 'phase-3',
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {name}'))
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created={created_count}, Updated={updated_count}'
        ))
        self.stdout.write(self.style.WARNING(
            '\n  ACTION NEEDED: nurgle-rotigus and nurgle-great-unclean-one'
            ' have empty image_filename -- update once GW CAPTCHA clears.'
        ))
