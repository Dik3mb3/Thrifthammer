"""
Management command: populate_worldeaters_phase3_products

Adds World Eaters phase-3 products scraped from:
https://www.warhammer.com/en-US/shop/warhammer-40000/armies-of-chaos/world-eaters

Page showed: 30 of 30 products.

SKIPPED (already in DB): Angron, Khorne Berzerkers, Combat Patrol, Eightbound,
  Lord on Juggernaut
SKIPPED (shared CSM already in DB faction=4): Daemon Prince, Maulerfiend, Chaos Rhino,
  Heldrake, Forgefiend, Chaos Predator, Chaos Land Raider
SKIPPED (already added in other commands): Helbrute (populate_deathguard),
  Defiler (populate_thousandsons), Chaos Spawn (already in DB faction=4),
  Chaos Terminator Squad (already in DB)

AoS/40K shared (user instruction: add if not in DB, tag to both):
  - Bloodletters: existing DB entry is 'blades-of-khorne-bloodletters-97-08' (faction=37).
    Adding 'khorne-bloodletters' (faction=37) as a clean 40K entry.

NOTE: Kill Team Goremongers ($69) is a Kill Team product, not standard 40K.
  Including it as it appears on the WE page -- flagged in name.

NOTE: Lord Invocatus and Lord on Juggernaut are the same dual-build plastic kit.
  Lord on Juggernaut already in DB. Adding Lord Invocatus as second variant (dual-kit).

Image filenames confirmed by agent scraping GW World Eaters page.
SKUs: prod*/P-* for newer/daemon models (MM scraper marks not_available; use seed_mm instead).

Idempotent -- safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

GW_BASE = 'https://www.warhammer.com/en-US/shop/'
GW_IMG_BASE = 'https://www.warhammer.com/app/resources/catalog/product/920x950/'

# (slug, name, gw_sku, msrp, image_filename, gw_url_slug, ebay_search_name, faction_slug)
PRODUCTS = [
    # -- World Eaters specific ------------------------------------------------
    (
        'world-eaters-kharn-the-betrayer',
        'World Eaters Kharn the Betrayer',
        'P-WE-KHARN-2023',
        43.50,
        '99120102184_WEKharnTheBetrayer01.jpg',
        'world-eaters-kharn-the-betrayer-2023',
        'Kharn the Betrayer World Eaters Warhammer',
        'world-eaters',
    ),
    (
        'world-eaters-lord-invocatus',
        'World Eaters Lord Invocatus',
        'P-WE-LORD-INVOC-2023',
        69.00,
        '99120102155_WELordInvocatus01.jpg',
        'world-eaters-lord-invocatus-2023',
        'Lord Invocatus World Eaters Warhammer',
        'world-eaters',
    ),
    (
        'world-eaters-jakhals',
        'World Eaters Jakhals',
        'P-WE-JAKHALS-2023',
        60.00,
        '99120102156_WEJakhals015.jpg',
        'world-eaters-jakhals-2023',
        'Jakhals World Eaters Warhammer',
        'world-eaters',
    ),
    (
        'world-eaters-exalted-eightbound',
        'World Eaters Exalted Eightbound',
        'P-WE-EXL-EIGHT-2023',
        65.00,
        '99120102154_ExhaltedEightbound2.jpg',
        'world-eaters-exalted-eightbound-2023',
        'Exalted Eightbound World Eaters Warhammer',
        'world-eaters',
    ),
    (
        'world-eaters-slaughterbound',
        'World Eaters Slaughterbound',
        'P-WE-SLAUGHTER-2025',
        43.50,
        '99120102199_ChaosSpaceMarineWorldEatersSlaughterbound1.jpg',
        'world-eaters-slaughter-bound-2025',
        'Slaughterbound World Eaters Warhammer',
        'world-eaters',
    ),
    # FLAG: Kill Team product -- included as it appears on WE GW page
    (
        'world-eaters-kill-team-goremongers',
        'Kill Team: Goremongers (World Eaters)',
        'P-WE-KT-GOREMONGERS-2025',
        69.00,
        '99120102208_KillTeamGoremongers01.jpg',
        'kill-team-goremongers-2025',
        'Kill Team Goremongers World Eaters Warhammer',
        'world-eaters',
    ),
    (
        'world-eaters-lord-of-skulls',
        'Khorne Lord of Skulls',
        'P-WE-LORD-SKULLS',
        197.00,
        '99120102041_LordofSkulls01.jpg',
        'Chaos-Space-Marines-Khorne-Lord-of-Skulls',
        'Khorne Lord of Skulls Warhammer 40k',
        'world-eaters',
    ),
    # -- Codex ----------------------------------------------------------------
    (
        'codex-world-eaters',
        'Codex: World Eaters',
        'P-WE-CODEX-2025',
        60.00,
        '60030102034_WorldEatersStdEdHBCodex1.jpg',
        'codex-world-eaters-2025-eng',
        'Codex World Eaters Warhammer 40k',
        'world-eaters',
    ),
    # -- Shared CSM (new to DB, on WE page) -----------------------------------
    (
        'chaos-master-of-executions',
        'Master of Executions',
        'P-CSM-MASTER-EXEC',
        35.00,
        '99070102013_CSMMasterofExecutions01.jpg',
        'Master-Of-Executions-2019',
        'Master of Executions Chaos Warhammer 40k',
        'chaos-space-marines',
    ),
    # -- Khorne Daemons (faction=blades-of-khorne) ----------------------------
    # AoS/40K shared -- Bloodletters already in DB as blades-of-khorne-bloodletters-97-08
    # Adding clean 40K entry per user instruction
    (
        'khorne-bloodletters',
        'Bloodletters of Khorne',
        'P-KHORNE-BLOODLETTERS-40K',
        43.50,
        '99129915023_DaemonsofKhorneBloodLetters01.jpg',
        'Daemons-Of-Khorne-Bloodletters-40k-2017',
        'Bloodletters Khorne Daemon Warhammer',
        'blades-of-khorne',
    ),
    (
        'khorne-bloodthirster',
        'Bloodthirster',
        'P-KHORNE-BLOODTHIRSTER',
        170.00,
        '99129915024_DaemonsofKhorneBloodThirster01.jpg',
        'Daemons-Of-Khorne-Bloodthirster',
        'Bloodthirster Khorne Daemon Warhammer',
        'blades-of-khorne',
    ),
    (
        'khorne-bloodcrushers',
        'Bloodcrushers of Khorne',
        'P-KHORNE-BLOODCRUSHERS',
        110.00,
        '99129915022_DaemonsofKhorneBloodCrushers01.jpg',
        'Daemons-Of-Khorne-Bloodcrushers',
        'Bloodcrushers Khorne Daemon Warhammer',
        'blades-of-khorne',
    ),
    (
        'khorne-skarbrand',
        'Skarbrand the Bloodthirster',
        'P-KHORNE-SKARBRAND',
        170.00,
        '99129915071_Skarbrand1.jpg',
        'Skarbrand-Bloodthirster',
        'Skarbrand Bloodthirster Khorne Daemon Warhammer',
        'blades-of-khorne',
    ),
    (
        'khorne-flesh-hounds',
        'Flesh Hounds of Khorne',
        'P-KHORNE-FLESHHOUNDS',
        60.00,
        '99129915050_BoKHFleshhounds01.jpg',
        'Flesh-Hounds-2019',
        'Flesh Hounds Khorne Daemon Warhammer',
        'blades-of-khorne',
    ),
]


class Command(BaseCommand):
    """Seed World Eaters phase-3 products into the database."""

    help = 'Populates World Eaters phase-3 products. Idempotent via update_or_create on slug.'

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
