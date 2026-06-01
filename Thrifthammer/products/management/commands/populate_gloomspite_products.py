"""
Management command: populate_gloomspite_products

Creates / updates all Gloomspite Gitz product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 35 products from Gloomspite - GW, NK, MM.xlsx (2026-05-30).

Category: Age of Sigmar
Faction:  Gloomspite Gitz  (already exists in DB — fetched via get())

Shared-listing products (same physical kit, multiple build options):
  GG-004 / GG-005  — Loonboss on Mangler Squigs / Mangler Squigs  (share MM + NK)
  GG-010 / GG-012  — Dankhold Troggboss / Dankhold Troggoth  (share NK)
  GG-015 / GG-020  — Moonclan Shootas / Moonclan Stabbas  (share NK)
  GG-030 / GG-031 / GG-032 / GG-034  — Arachnarok Spider variants  (share NK)

No MM listing (19 products):
  GG-007, GG-010, GG-011, GG-012, GG-013, GG-014, GG-015, GG-016,
  GG-018, GG-019, GG-020, GG-021, GG-022, GG-030, GG-031, GG-032,
  GG-033, GG-034, GG-035

No NK listing (4 products):
  GG-007, GG-014, GG-022, GG-035

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_gloomspite_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-30.
# ebay_search_name set per Excel 'Ebay Search Name' column.
PRODUCTS = [

    # ── Squig units ───────────────────────────────────────────────────────────
    (
        'boingrot-bounderz',
        'GG-001',
        'Boingrot Bounderz',
        60.00,
        '99120209152_GloomspiteGitzBoungrotBounderzRegimentREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/boingrot-bounderz-2023',
        'Squig Hoppers Gloomspite Gitz',
    ),
    (
        'squigboss-with-gnasha-squig',
        'GG-002',
        'Squigboss with Gnasha-squig',
        35.00,
        '99120209139_GloomspiteGitzSQUIGBOSSGNASHASQUIGREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-squigboss-with-gnasha-squig-2023',
        'Squigboss with Gnasha-squig Gloomspite Gitz',
    ),

    # ── Characters ────────────────────────────────────────────────────────────
    (
        'loonboss-on-giant-cave-squig',
        'GG-003',
        'Loonboss on Giant Cave Squig',
        43.50,
        '99120209154_GloomspiteGitzLOONBOSSONGIANTCAVESQUIGCharacterREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspte-Gitz-Loonboss-On-Giant-Cave-Squig-2020',
        'Loonboss on Giant Cave Squig Gloomspite Gitz',
    ),
    (
        'loonboss',
        'GG-014',
        'Loonboss',
        35.00,
        '99070209006_GloomspiteGItzLoonboss01.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Loonboss-2019',
        'Loonboss Gloomspite Gitz',
    ),
    (
        'skragrott-the-loonking',
        'GG-019',
        'Skragrott the Loonking',
        43.50,
        '99120209051_SkragrottLoonking01.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Skragrott-The-Loonking-2019',
        'Skragrott the Loonking Gloomspite Gitz',
    ),
    (
        'fungoid-cave-shaman',
        'GG-021',
        'Fungoid Cave-Shaman',
        43.50,
        '99120209045_Stinkmullett01.jpg',
        'https://www.warhammer.com/en-US/shop/Moonclan-Grots-Snazzgar-Stinkmullett-2018',
        'Fungoid Cave-Shaman Warhammer',
    ),

    # ── Mangler Squigs (dual kit) ─────────────────────────────────────────────
    # ⚠ Dual kit: Loonboss on Mangler Squigs / Mangler Squigs share MM + NK listing
    (
        'loonboss-on-mangler-squigs',
        'GG-004',
        'Loonboss on Mangler Squigs',
        96.00,
        '99120209151_GloomspiteGitzMANGLERSQUIGCharacterREPACKAGED2.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Loonboss-on-Mangler-Squigs-2019',
        'Mangler Squigs Gloomspite Gitz',
    ),
    (
        'mangler-squigs',
        'GG-005',
        'Mangler Squigs',
        96.00,
        '99120209151_GloomspiteGitzMANGLERSQUIGCharacterREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Mangler-Squigs-2019',
        'Mangler Squigs Gloomspite Gitz',
    ),

    # ── Troggoths ─────────────────────────────────────────────────────────────
    (
        'trugg-the-troggoth-king',
        'GG-006',
        'Trugg the Troggoth King',
        106.00,
        '99120209115_GloomspiteGitzTRUGGTHETROGGKINGCharacterREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-trugg-the-troggoth-king-2024',
        'Trugg the Troggoth King Gloomspite Gitz',
    ),
    # ⚠ Dual kit: Dankhold Troggboss / Dankhold Troggoth share NK listing
    (
        'dankhold-troggboss',
        'GG-010',
        'Dankhold Troggboss',
        82.00,
        '99120209153_GloomspiteGitzDANKHOLDTROGGOTHCharacterREPACKAGED2.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Dankhold-Troggboss-2019',
        'Dankhold Troggoth Gloomspite Gitz',
    ),
    (
        'dankhold-troggoth',
        'GG-012',
        'Dankhold Troggoth',
        82.00,
        '99120209153_GloomspiteGitzDANKHOLDTROGGOTHCharacterREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Dankhold-Troggoth-2019',
        'Dankhold Troggoth Gloomspite Gitz',
    ),
    (
        'fellwater-troggoths',
        'GG-022',
        'Fellwater Troggoths',
        60.00,
        '99120209042_FellwaterTroggothsUpdate01.jpg',
        'https://www.warhammer.com/en-US/shop/Fellwater-Troggoths-2017',
        'Fellwater Troggoths Gloomspite Gitz',
    ),
    (
        'rockgut-troggoths',
        'GG-033',
        'Rockgut Troggoths',
        65.00,
        '99120209150_GloomspiteGitzROCKGUTTROGGOTHSRegimentREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Rockgut-Troggoths-2019',
        'Rockgut Troggoths Gloomspite Gitz',
    ),

    # ── Spider Riders / Snarlfangs ────────────────────────────────────────────
    (
        'spider-riders',
        'GG-007',
        'Spider Riders',
        42.00,
        '99120209009_ForestGoblinSpiderRidersNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Grot-Spider-Riders',
        'Spider Riders Gloomspite Gitz',
    ),
    (
        'snarlfang-riders',
        'GG-008',
        'Snarlfang Riders',
        65.00,
        '99120209147_GloomspiteGitzSNARLFANGRIDERSRegimentREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-snarlfang-riders-2023',
        'Snarlfang Riders Gloomspite Gitz',
    ),

    # ── Kragnos ───────────────────────────────────────────────────────────────
    (
        'kragnos-the-end-of-empires',
        'GG-009',
        'Kragnos, the End of Empires',
        191.00,
        '99120209080_KragnosLead.jpg',
        'https://www.warhammer.com/en-US/shop/Kragnos-The-End-Of-Empires-2021',
        'Kragnos, the End of Empires Age of Sigmar',
    ),

    # ── Moonclan units ────────────────────────────────────────────────────────
    (
        'gobbapalooza',
        'GG-011',
        'Gobbapalooza',
        60.00,
        '99120209054_GloomspiteGItzGobbaPalooza01.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Gobbapalooza-2019',
        'Gobbapalooza Gloomspite Gitz',
    ),
    (
        'sneaky-snufflers',
        'GG-013',
        'Sneaky Snufflers',
        48.00,
        '99120209048_GloomspiteGitzSneakySnufflers01.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Sneaky-Snufflers-2019',
        'Sneaky Snufflers Gloomspite Gitz',
    ),
    # ⚠ Dual kit: Moonclan Shootas / Moonclan Stabbas share NK listing
    (
        'moonclan-shootas',
        'GG-015',
        'Moonclan Shootas',
        48.00,
        '99120209148_GloomspiteGitzMOONCLANSHOOTASRegimentREPACKAGED1.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Grots-Shootas-2019',
        'Moonclan Gloomspite Gitz',
    ),
    (
        'moonclan-stabbas',
        'GG-020',
        'Moonclan Stabbas',
        48.00,
        '99120209043_MoonclanGrots01.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz-Grots-2019',
        'Moonclan Gloomspite Gitz',
    ),
    (
        'loonsmasha-fanatics',
        'GG-018',
        'Loonsmasha Fanatics',
        48.00,
        '99120209055_GloomspiteGitzFanatics01.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-Gitz:-Fanatics-2019',
        'Gloomspite Gitz Fanatics',
    ),

    # ── Endless Spells / Scenery ──────────────────────────────────────────────
    (
        'endless-spells-gloomspite-gitz',
        'GG-016',
        'Endless Spells: Gloomspite Gitz',
        48.00,
        '99120209061_EndlessSpellsGloomspiteGitz01.jpg',
        'https://www.warhammer.com/en-US/shop/Endless-spells-gloomspite-gitz-2019',
        'Endless Spells: Gloomspite Gitz',
    ),
    (
        'bad-moon-loonshrine',
        'GG-017',
        'Bad Moon Loonshrine',
        69.00,
        '99120209060_BadMoonLoonshrine01.jpg',
        'https://www.warhammer.com/en-US/shop/Gloomspite-gitz-bad-moon-loonshrine-2019',
        'Bad Moon Loonshrine Gloomspite Gitz',
    ),

    # ── New releases (2025) ───────────────────────────────────────────────────
    (
        'doom-diver-catapult',
        'GG-023',
        'Doom Diver Catapult',
        112.00,
        '99120209129_GSGDoomDiverCatapult01.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-doom-diver-catapult-2025',
        'Doom Diver Catapult Gloomspite Gitz',
    ),
    (
        'sunsteala-wheelas',
        'GG-024',
        'Sunsteala Wheelas',
        96.00,
        '99120209128_GSGSunstealaWheelas01.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-sunsteala-wheelas-2025',
        'Sunsteala Wheelas Gloomspite Gitz',
    ),
    (
        'snarlpack-cavalry',
        'GG-025',
        'Snarlpack Cavalry',
        60.00,
        '99120209127_GSGSnarlpackCavalry01.jpg',
        'https://www.warhammer.com/en-US/shop/gloosmpite-gitz-snarlpack-cavalry-2025',
        'Snarlpack Cavalry Gloomspite Gitz',
    ),
    (
        'snarlboss-on-war-wheela',
        'GG-026',
        'Snarlboss on War-Wheela',
        102.00,
        '99120209130_GSGSnarlbossOnWarWheela01.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-snarlboss-on-war-wheela-2025',
        'Snarlboss on War-Wheela Gloomspite Gitz',
    ),
    (
        'snarlboss-and-wolfgit-retinue',
        'GG-027',
        'Snarlboss and Wolfgit Retinue',
        43.50,
        '99120209137_GSGSnarlbossAndWolfgitRetinue01.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-snarlboss-and-wolfgit-retinue-2025',
        'Snarlboss and Wolfgit Retinue Gloomspite Gitz',
    ),
    (
        'rabble-rowza',
        'GG-028',
        'Rabble-Rowza',
        35.00,
        '99120209141_GSGRabbleRowza1.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-rabble-rowza-2023',
        'Rabble-Rowza Gloomspite Gitz',
    ),
    (
        'droggz-da-sunchompa',
        'GG-035',
        'Droggz da Sunchompa',
        60.00,
        '99120209126_GSGDroggzDaSunchompa01extra.jpg',
        'https://www.warhammer.com/en-US/shop/gloomspite-gitz-droggz-da-sunchompa-2025',
        'Droggz da Sunchompa Gloomspite Gitz',
    ),

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'destruction-battletome-gloomspite-gitz',
        'GG-029',
        'Destruction Battletome: Gloomspite Gitz',
        60.00,
        '60030209015_EngGSG01.jpg',
        'https://www.warhammer.com/en-US/shop/battletome-gloomspite-gitz-2025-eng',
        'Destruction Battletome: Gloomspite Gitz',
    ),

    # ── Arachnarok Spider variants (quad kit — share NK listing) ─────────────
    # ⚠ Quad kit: Skitterstrand / Flinger / Webspinner Shaman / Spiderfang Warparty
    #   all share the same NK listing (Arachnarok-Spider). No MM listing for any.
    (
        'skitterstrand-arachnarok',
        'GG-030',
        'Skitterstrand Arachnarok',
        69.00,
        '99120209044_ArachnarokSpider01.jpg',
        'https://www.warhammer.com/en-US/shop/skitterstrand-arachnarok-2023',
        'Arachnarok Spider Gloomspite Gitz',
    ),
    (
        'arachnarok-spider-with-flinger',
        'GG-031',
        'Arachnarok Spider with Flinger',
        69.00,
        '99120209044_ArachnarokSpiderFliner01.jpg',
        'https://www.warhammer.com/en-US/shop/arachnarok-spider-with-flinger-2023',
        'Arachnarok Spider Gloomspite Gitz',
    ),
    (
        'webspinner-shaman-on-arachnarok-spider',
        'GG-032',
        'Webspinner Shaman on Arachnarok Spider',
        69.00,
        '99120209044_ArachnarokSpiderShaman01.jpg',
        'https://www.warhammer.com/en-US/shop/webspinner-shaman-on-arachnarok-spider-2023',
        'Arachnarok Spider Gloomspite Gitz',
    ),
    (
        'arachnarok-spider-with-spiderfang-warparty',
        'GG-034',
        'Arachnarok Spider with Spiderfang Warparty',
        69.00,
        '99120209044_Arachnarok01.jpg',
        'https://www.warhammer.com/en-US/shop/Arachnarok-Spider-2017',
        'Arachnarok Spider Gloomspite Gitz',
    ),
]


class Command(BaseCommand):
    """Populate Gloomspite Gitz products (GG-001 to GG-035)."""

    help = (
        'Creates / updates 35 Gloomspite Gitz products and seeds GW prices at MSRP. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_aos = Category.objects.get(slug='age-of-sigmar')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Age of Sigmar category not found — run populate_products first.'
            ))
            return

        try:
            gg_faction = Faction.objects.get(slug='gloomspite-gitz')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Gloomspite Gitz faction not found — run populate_products first.'
            ))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        product_created = product_updated = price_created = price_updated = 0

        for (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_name) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_name,
                    'category': category_aos,
                    'faction': gg_faction,
                    'is_active': True,
                    'batch_tag': 'gloomspite-gitz',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} ({gw_sku})'))
            if created:
                product_created += 1
            else:
                product_updated += 1

            # ── Seed GW CurrentPrice at MSRP ──────────────────────────────────
            if gw_retailer and gw_url:
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                if p_created:
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_gloomspite_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
