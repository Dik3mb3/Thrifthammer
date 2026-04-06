"""
Management command: populate_votann_phase3_products

Adds Leagues of Votann phase-3 products scraped from:
https://www.warhammer.com/en-US/shop/warhammer-40000/xenos-armies/leagues-of-votann

Page showed: 23 of 23 products.

SKIPPED (already in DB):
  - Einhyr Champion          (leagues-of-votann-einhyr-champion)
  - Einhyr Hearthguard       (leagues-of-votann-einhyr-hearthguard)
  - Hearthkyn Warriors       (leagues-of-votann-hearthkyn-warriors)
  - Hernkyn Pioneers         (leagues-of-votann-hernkyn-pioneers)
  - Combat Patrol (old 73-25)(leagues-of-votann-combat-patrol)

NOTE: A new 2025 Combat Patrol box exists at GW URL
  combat-patrol-leagues-of-votann-2025 ($170). It may be a different product
  from the existing 73-25 DB entry. Excluded here as the slug already exists.
  Confirm and add manually if needed.

ONLINE ONLY (GW): Kahl, Grimnyr -- no retailer discount expected.

KILL TEAM products included (flagged in name):
  - Kill Team: Hearthkyn Salvagers (P-198770, $69)
  - Kill Team: Hernkyn Yaegirs    (P-189754, $69)

2025/2026 NEW RELEASES (P-* SKUs -- MM scraper will mark not_available):
  Kapricus Defender/Carrier, Cthonian Earthshakers, Buri Aegnirssen,
  Arkanyst Evaluator, Memnyr Strategist, Ironkin Steeljacks, Berehk Stornbrow

Image filenames and SKUs confirmed via authenticated JS fetch from GW product pages.
Prices confirmed from GW category page text (Apr 2026).

Idempotent -- safe to re-run.
"""

from django.core.management.base import BaseCommand

from products.models import Faction, Product

GW_BASE = 'https://www.warhammer.com/en-US/shop/'
GW_IMG_BASE = 'https://www.warhammer.com/app/resources/catalog/product/920x950/'

# (slug, name, gw_sku, msrp, image_filename, gw_url_slug, ebay_search_name)
# All products use faction=leagues-of-votann
PRODUCTS = [
    # ── 2022 Core Range ──────────────────────────────────────────────────────
    (
        'leagues-of-votann-kahl',
        'Kahl',
        'prod5000456-99120118011',
        43.50,
        '99120118011_KharlLead.jpg',
        'lov-kahl-2022',
        'Kahl Leagues of Votann Warhammer 40k',
    ),
    (
        'leagues-of-votann-uthar-the-destined',
        'Uthar the Destined',
        'prod5000445-99120118011',
        43.50,
        '99120118011_UtharDestinedLead.jpg',
        'lov-uthar-the-destined-2022',
        'Uthar Destined Leagues of Votann Warhammer',
    ),
    (
        'leagues-of-votann-brokhyr-iron-master',
        'Brokhyr Iron-master',
        'prod5000444-99120118010',
        60.00,
        '99120118010_BrokhyrIronMasterLead.jpg',
        'lov-brokhyr-iron-master-2022',
        'Brokhyr Iron Master Leagues of Votann Warhammer',
    ),
    (
        'leagues-of-votann-hekaton-land-fortress',
        'Hekaton Land Fortress',
        'prod5000440-99120118006',
        122.00,
        '99120118006_LandFortressLead.jpg',
        'lov-hekaton-land-fortress-2022',
        'Hekaton Land Fortress Leagues of Votann Warhammer',
    ),
    (
        'leagues-of-votann-brokhyr-thunderkyn',
        'Brokhyr Thunderkyn',
        'prod5000439-99120118005',
        60.00,
        '99120118005_LoVBrokhyrThunderkynLead.jpg',
        'lov-brokhyr-thunderkin-2022',
        'Brokhyr Thunderkyn Leagues of Votann Warhammer',
    ),
    # Online Only on GW
    (
        'leagues-of-votann-grimnyr',
        'Grimnyr',
        'prod5000438-99120118004',
        48.00,
        '99120118004_GrymnyrLead.jpg',
        'lov-grimnyr-2022',
        'Grimnyr Leagues of Votann Warhammer 40k',
    ),
    (
        'leagues-of-votann-sagitaur',
        'Sagitaur',
        'prod5000437-99120118003',
        69.00,
        '99120118003_LoVSagitarLead.jpg',
        'lov-sagitaur-2022',
        'Sagitaur Leagues of Votann Warhammer 40k',
    ),
    (
        'leagues-of-votann-cthonian-berserks',
        'Cthonian Berserks',
        'prod5000436-99120118002',
        62.50,
        '99120118002_LoVCthonianBeserksLead.jpg',
        'lov-chonian-berserks-2022',
        'Cthonian Berserks Leagues of Votann Warhammer',
    ),
    # ── Codex ────────────────────────────────────────────────────────────────
    (
        'codex-leagues-of-votann',
        'Codex: Leagues of Votann',
        'P-223015-60030118002',
        60.00,
        '60030118002_engLOVCodex01.jpg',
        'codex-leagues-of-votann-2025-eng',
        'Codex Leagues of Votann Warhammer 40k',
    ),
    # ── 2025 New Releases ────────────────────────────────────────────────────
    # Kapricus is a dual-build kit (Defender or Carrier)
    (
        'leagues-of-votann-kapricus',
        'Kapricus Defender/Carrier',
        'P-223006-99120118022',
        64.00,
        '99120118022_LOVKapricus01.jpg',
        'leagues-of-votann-kapricus-2025',
        'Kapricus Defender Carrier Leagues of Votann Warhammer',
    ),
    (
        'leagues-of-votann-cthonian-earthshakers',
        'Cthonian Earthshakers',
        'P-223004-99120118021',
        60.00,
        '99120118021_LovCthonianEarthshakers01.jpg',
        'leagues-of-votann-cthonian-earthshakers-2025',
        'Cthonian Earthshakers Leagues of Votann Warhammer',
    ),
    (
        'leagues-of-votann-buri-aegnirsson',
        'Buri Aegnirssen',
        'P-223003-99120118019',
        43.50,
        '99120118019_LOVBuriAegnirssen01.jpg',
        'leagues-of-votann-buri-aegnirsson-2025',
        'Buri Aegnirssen Leagues of Votann Warhammer',
    ),
    (
        'leagues-of-votann-arkanyst-evaluator',
        'Arkanyst Evaluator',
        'P-222999-99120118025',
        40.00,
        '99120118025_LOVArkanystEvaluator01.jpg',
        'leagues-of-votann-arkanyst-evaluator-2025',
        'Arkanyst Evaluator Leagues of Votann Warhammer',
    ),
    (
        'leagues-of-votann-memnyr-strategist',
        'Memnyr Strategist',
        'P-222997-99120118026',
        40.00,
        '99120118026_LOVMemnyrStrategist01.jpg',
        'leagues-of-votann-memnyr-strategist-2025',
        'Memnyr Strategist Leagues of Votann Warhammer',
    ),
    (
        'leagues-of-votann-ironkin-steeljacks',
        'Ironkin Steeljacks',
        'P-223001-99120118020',
        60.00,
        '99120118020_LOVIronkinSteeljacks01.jpg',
        'leagues-of-votann-ironkin-steeljacks-2025',
        'Ironkin Steeljacks Leagues of Votann Warhammer',
    ),
    # ── 2026 New Release (temporarily out of stock at time of scrape) ────────
    (
        'leagues-of-votann-berehk-stornbrow',
        'Berehk Stornbrow',
        'P-240930-99120118028',
        47.00,
        '99120118028_LOVBerehkStornbrow01.jpg',
        'leagues-of-votann-berehk-stornbrow-2026',
        'Berehk Stornbrow Leagues of Votann Warhammer',
    ),
    # ── Kill Team (on LOV GW page, flagged) ──────────────────────────────────
    (
        'leagues-of-votann-kill-team-hearthkyn-salvagers',
        'Kill Team: Hearthkyn Salvagers (Leagues of Votann)',
        'P-198770-99120118023',
        69.00,
        '99120118023_KTHearthkynSalvagers2.jpg',
        'kill-team-hearthkyn-salvagers-2024',
        'Kill Team Hearthkyn Salvagers Warhammer',
    ),
    (
        'leagues-of-votann-kill-team-hernkyn-yaegirs',
        'Kill Team: Hernkyn Yaegirs (Leagues of Votann)',
        'P-189754-99120118018',
        69.00,
        '60010199066_EngKTTerminationGroup02.jpg',
        'kill-team-hernkyn-yaegirs-2024',
        'Kill Team Hernkyn Yaegirs Warhammer',
    ),
]


class Command(BaseCommand):
    """Seed Leagues of Votann phase-3 products into the database."""

    help = 'Populates Leagues of Votann phase-3 products. Idempotent via update_or_create on slug.'

    def handle(self, *args, **options):
        """Run the command."""
        try:
            faction = Faction.objects.get(slug='leagues-of-votann')
        except Faction.DoesNotExist:
            self.stdout.write(self.style.ERROR('Faction leagues-of-votann not found'))
            return

        created_count = 0
        updated_count = 0

        for slug, name, gw_sku, msrp, img, gw_url_slug, ebay_name in PRODUCTS:
            obj, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': GW_IMG_BASE + img,
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
