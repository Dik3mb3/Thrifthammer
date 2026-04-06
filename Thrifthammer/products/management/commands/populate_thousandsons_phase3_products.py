"""
Management command: populate_thousandsons_phase3_products

Adds Thousand Sons phase-3 products scraped from:
https://www.warhammer.com/en-US/shop/warhammer-40000/armies-of-chaos/thousand-sons

Page showed: 32 of 32 products.

SKIPPED (already in DB): Ahriman, Combat Patrol, Exalted Sorcerers, Magnus the Red,
  Rubric Marines, Scarab Occult Terminators
SKIPPED (shared CSM already in DB faction=4): Daemon Prince, Maulerfiend, Chaos Rhino,
  Heldrake, Forgefiend, Chaos Predator, Chaos Land Raider
SKIPPED (already added under Death Guard): Helbrute (chaos-helbrute, faction=4)

AoS/40K shared units (user instruction: add if not in DB, tag to both):
  - Tzaangors: existing DB entry is 'disciples-of-tzeentch-tzaangors' (faction=39).
    Adding 'thousand-sons-tzaangors' (faction=17) as the 40K TS variant.
  - Pink Horrors: existing DB entry is 'disciples-of-tzeentch-pink-horrors-97-11' (faction=39).
    Adding 'tzeentch-pink-horrors' (faction=39) as a clean 40K entry pointing to current product.
    (Pink Horrors are Tzeentch daemons, not TS-specific, so faction=39 is correct for both.)

New shared CSM units being added here (not yet in DB):
  - Sorcerer Lord in Terminator Armour (faction=4)
  - Chaos Vindicator (faction=4) -- Online Only, may be scarce on eBay

Also adding Defiler here (first occurrence; shared CSM, faction=4).
  Appears on Death Guard, Thousand Sons, and World Eaters pages.

Image sources: agents scraping GW Thousand Sons page confirmed all 32 images.
SKUs: catalog numbers (43-XX style) from MM Excel where available; internal prod* IDs otherwise.
  Note: prod*/P-* SKUs mean MM scraper will mark as not_available -- use seed_mm command instead.

Idempotent -- safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

GW_BASE = 'https://www.warhammer.com/en-US/shop/'
GW_IMG_BASE = 'https://www.warhammer.com/app/resources/catalog/product/920x950/'

# (slug, name, gw_sku, msrp, image_filename, gw_url_slug, ebay_search_name, faction_slug)
PRODUCTS = [
    # -- Thousand Sons specific -----------------------------------------------
    (
        'thousand-sons-infernal-master',
        'Thousand Sons Infernal Master',
        '43-79',
        43.50,
        '99120102122_TSInfernalMasterLead.jpg',
        'thousand-sons-infernal-master-2022',
        'Thousand Sons Infernal Master Warhammer',
        'thousand-sons',
    ),
    (
        'thousand-sons-sekhetar-robots',
        'Thousand Sons Sekhetar Robots',
        'P-TS-SEKHETAR-2025',
        52.00,
        '99120102197_ThousandSonsSekhetarRobotsVehicleSquad01.jpg',
        'thousand-sons-sekhetar-robots-2025',
        'Thousand Sons Sekhetar Robots Warhammer',
        'thousand-sons',
    ),
    # AoS/40K shared -- adding 40K variant of Tzaangors for TS faction page
    (
        'thousand-sons-tzaangors',
        'Thousand Sons Tzaangors',
        'P-TZAANGORS-40K',
        60.00,
        '99120201065_TzaangorWarriors01.jpg',
        'Tzaangors-AoS',
        'Tzaangors Thousand Sons Warhammer 40k',
        'thousand-sons',
    ),
    (
        'thousand-sons-tzaangor-shaman',
        'Tzaangor Shaman',
        'P-TZAANGOR-SHAMAN',
        39.00,
        '99070201021_TzaangorShamen01.jpg',
        'Tzaangor-Shaman',
        'Tzaangor Shaman Warhammer',
        'thousand-sons',
    ),
    (
        'thousand-sons-tzaangor-enlightened',
        'Tzaangor Enlightened',
        'P-TZAANGOR-ENL',
        60.00,
        '99120201064_TzaangorEnlightened01.jpg',
        'Tzaangor-Enlightened',
        'Tzaangor Enlightened Warhammer',
        'thousand-sons',
    ),
    (
        'thousand-sons-tzaangor-upgrade-pack',
        'Tzaangor Upgrade Pack',
        'P-TZAANGOR-UPG',
        15.00,
        '99120102068_ThousandSonsTzangors08.jpg',
        'tzaangor-upgrade-pack',
        'Tzaangor Upgrade Pack Thousand Sons Warhammer',
        'thousand-sons',
    ),
    (
        'thousand-sons-mutalith-vortex-beast',
        'Mutalith Vortex Beast',
        'P-MUTALITH-VB',
        96.00,
        '99120201021_MutilithVortexBeast01.jpg',
        'MutilithVortexBeast',
        'Mutalith Vortex Beast Thousand Sons Warhammer',
        'thousand-sons',
    ),
    # -- Tzeentch Daemons (faction=disciples-of-tzeentch) --------------------
    # AoS/40K shared -- Pink Horrors already in DB as disciples-of-tzeentch-pink-horrors-97-11
    # Adding clean 40K entry
    (
        'tzeentch-pink-horrors',
        'Pink Horrors of Tzeentch',
        'P-PINK-HORRORS-40K',
        48.00,
        '99129915032_PinkHorrors01.jpg',
        'pink-horrors-of-tzeentch',
        'Pink Horrors Tzeentch Daemon Warhammer',
        'disciples-of-tzeentch',
    ),
    (
        'tzeentch-flamers',
        'Flamers of Tzeentch',
        'P-TZEENTCH-FLAMERS',
        39.00,
        '99129915031_TzeentchFlamers01.jpg',
        'flamers-of-tzeentch',
        'Flamers Tzeentch Daemon Warhammer',
        'disciples-of-tzeentch',
    ),
    (
        'tzeentch-blue-horrors-brimstone-horrors',
        'Blue Horrors and Brimstone Horrors',
        'P-TZEENTCH-BLUEHORRORS',
        48.00,
        '99129915029_BlueHorrors01.jpg',
        'blue-horrors-brimstone-horrors',
        'Blue Horrors Brimstone Horrors Tzeentch Warhammer',
        'disciples-of-tzeentch',
    ),
    (
        'tzeentch-screamers',
        'Screamers of Tzeentch',
        'P-TZEENTCH-SCREAMERS',
        39.00,
        '99129915033_TzeentchScreamers01.jpg',
        'screamers-of-tzeentch',
        'Screamers Tzeentch Daemon Warhammer',
        'disciples-of-tzeentch',
    ),
    (
        'tzeentch-kairos-fateweaver',
        'Kairos Fateweaver',
        'P-TZEENTCH-KAIROS',
        170.00,
        '99129915028_KairosFateweaver01.jpg',
        'kairos-fateweaver',
        'Kairos Fateweaver Tzeentch Daemon Warhammer',
        'disciples-of-tzeentch',
    ),
    (
        'tzeentch-lord-of-change',
        'Lord of Change',
        'P-TZEENTCH-LOC',
        170.00,
        '99129915028_LordofChange01.jpg',
        'lord-of-change',
        'Lord of Change Tzeentch Daemon Warhammer',
        'disciples-of-tzeentch',
    ),
    # -- Codex ----------------------------------------------------------------
    (
        'codex-thousand-sons',
        'Codex: Thousand Sons',
        'P-TS-CODEX-2023',
        60.00,
        '60030102033_EngTSCodex01.jpg',
        'codex-thousand-sons-2023',
        'Codex Thousand Sons Warhammer 40k',
        'thousand-sons',
    ),
    # -- Shared CSM units (new to DB, appear on TS page) ----------------------
    (
        'chaos-sorcerer-lord-terminator',
        'Chaos Sorcerer Lord in Terminator Armour',
        'P-CSM-SORC-TERM',
        35.00,
        '99120102093_CSMTerminatorLord02.jpg',
        'chaos-sorcerer-lord-terminator-armour-2024',
        'Chaos Sorcerer Lord Terminator Armour Warhammer',
        'chaos-space-marines',
    ),
    (
        'chaos-vindicator',
        'Chaos Vindicator',
        'P-CSM-VINDICATOR',
        80.00,
        '99120102025_ChaosVindicatorNEW_01.jpg',
        'chaos-vindicator-2023',
        'Chaos Vindicator Warhammer 40k',
        'chaos-space-marines',
    ),
    # Defiler: pre-order (2026), shared across DG/TS/WE pages -- adding once here
    (
        'chaos-defiler',
        'Chaos Defiler',
        'P-CSM-DEFILER-2026',
        145.00,
        '99120102229_CSMDefiler2.jpg',
        'chaos-space-marines-defiler-2026',
        'Chaos Defiler Warhammer 40k',
        'chaos-space-marines',
    ),
]


class Command(BaseCommand):
    """Seed Thousand Sons phase-3 products into the database."""

    help = 'Populates Thousand Sons phase-3 products. Idempotent via update_or_create on slug.'

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
