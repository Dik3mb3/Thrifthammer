"""
Management command: populate_orruk_warclans_products

Creates / updates Orruk Warclans product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP. Uses the existing Orruk Warclans
faction (slug=orruk-warclans, already in DB).

Covers 29 products (OW-001 to OW-029) from the
AOS - Orruk Warclans - GW, NK, MM.xlsx (2026-06-18).

NOTE: The Orruk Warclans faction already has 5 existing products in the DB
(gw_skus: 89-30, 89-22, 89-20, 70-892, 70-893) which are NOT touched by
this command. This command adds only the new OW-prefix batch.

Category: Age of Sigmar
Faction:  Orruk Warclans (existing -- get_or_create is safe/idempotent)

Dual-kit products (same physical box, multiple build options):
  - OW-007 Killaboss on Corpse-rippa Vulcha / OW-009 Gobsprakk, The Mouth of Mork
    (same NK and MM listing)
  - OW-008 Snatchaboss on Sludgeraker Beast / OW-011 Swampboss Skumdrekk
    (same NK and MM listing)
  - OW-013 Gordrakk, the Fist of Gork / OW-014 Megaboss on Maw-krusha
    (same NK and MM listing)
  - OW-019 Brute Ragerz / OW-020 Weirdbrute Wrekkaz
    (same NK and MM listing)
  - OW-027 Maw-grunta Gouger / OW-028 Maw-grunta with Hakkin' Krew /
    OW-029 Tuskboss on Maw-grunta
    (same NK and MM listing)

Shared product (do NOT create here):
  - GG-009 Kragnos, the End of Empires (primary faction: Gloomspite Gitz)
    → secondary faction added by add_kragnos_secondary_factions command.

No NK entries for: OW-004 Hobgrot Slittaboss, OW-005 Swampcalla Shaman,
OW-006 Killaboss with Stab-grot.
No MM entries for: OW-005 Swampcalla Shaman, OW-006 Killaboss with Stab-grot,
OW-015 Gore-gruntas, OW-016 Warchanter, OW-017 Megaboss, OW-018 Monsta Killaz.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_orruk_warclans_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# -- Product definitions -------------------------------------------------------
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-18.
# ebay_search_name is set directly -- single source of truth for eBay search.
PRODUCTS = [

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'bossrokk-tower',
        'OW-002',
        'Bossrokk Tower',
        65.00,
        '99120299114_OWBossrokkTowerTerrainPack01.jpg',
        f'{_GW}orruk-warclans-bossrokk-tower-2025',
        'Bossrokk Tower Orruk Warclans',
    ),

    # -- Manifestations --------------------------------------------------------
    (
        'orruk-warclans-manifestations',
        'OW-003',
        'Orruk Warclans Manifestations',
        60.00,
        '99120209132_OWManifestations01.jpg',
        f'{_GW}manifestations-orruk-warclans-2025',
        'Orruk Warclans Manifestations',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'hobgrot-slittaboss',
        'OW-004',
        'Hobgrot Slittaboss',
        35.00,
        '99120209136_OWHobgrotSlittabossCharacter1.jpg',
        f'{_GW}orruk-warclans-hobgrot-slittaboss-2025',
        'Hobgrot Slittaboss Orruk Warclans',
    ),
    (
        'swampcalla-shaman-with-pot-grot',
        'OW-005',
        'Swampcalla Shaman with Pot-grot',
        42.00,
        '99120209124_OWSwampcallaShamanPotgrotCharacter1.jpg',
        f'{_GW}orruk-warclans-swampcalla-shaman-with-pot-grot-2025',
        'Swampcalla Shaman Orruk Warclans',
    ),
    (
        'killaboss-with-stab-grot',
        'OW-006',
        'Killaboss with Stab-grot',
        42.00,
        '99120209123_OWKillabossStabgrotCharacter1.jpg',
        f'{_GW}orruk-warclans-killa-boss-with-stab-grot-2025',
        'Killaboss with Stab-grot Orruk Warclans',
    ),
    # ⚠ Dual kit: Killaboss on Corpse-rippa Vulcha and Gobsprakk, The Mouth of
    #   Mork share the same NK listing and MM listing.
    (
        'killaboss-on-corpse-rippa-vulcha',
        'OW-007',
        'Killaboss on Corpse-rippa Vulcha',
        170.00,
        '99120209078_ORKGobsprakktheMouthofMorkLeadALT.jpg',
        f'{_GW}killaboss-on-corpse-rippa-vulcha-2021',
        'Gobsprakk, The Mouth of Mork Orruk Warclans',
    ),
    (
        'gobsprakk-the-mouth-of-mork',
        'OW-009',
        'Gobsprakk, The Mouth of Mork',
        170.00,
        '99120209078_ORKGobsprakktheMouthofMorkLead.jpg',
        f'{_GW}gobsprakk-the-mouth-of-mork-2021',
        'Gobsprakk, The Mouth of Mork Orruk Warclans',
    ),
    (
        'marshcrawla-sloggoth',
        'OW-010',
        'Marshcrawla Sloggoth',
        60.00,
        '99120209076_SloggothLead.jpg',
        f'{_GW}marshcrawla-sloggoth-2021',
        'Marshcrawla Sloggoth Orruk Warclans',
    ),
    (
        'zoggrok-anvilsmasha',
        'OW-026',
        'Zoggrok Anvilsmasha',
        47.00,
        '99120209113_ORRZoggtokAnvilsmasha02.jpg',
        f'{_GW}orruk-warclans-zoggrok-anvilsmasha-2023',
        'Zoggrok Anvilsmasha Orruk Warclans',
    ),
    (
        'ardboy-big-boss',
        'OW-021',
        'Ardboy Big Boss',
        39.00,
        '99070209010_ORRArdboyBigBoss01.jpg',
        f'{_GW}orruk-warclans-ardboy-big-boss-2023',
        'Ardboy Big Boss Orruk Warclans',
    ),
    (
        'weirdnob-shaman',
        'OW-025',
        'Weirdnob Shaman',
        39.00,
        '99070209005_WeirdNobShaman01.jpg',
        f'{_GW}Ironjawz-Orruk-Weirdnob-Shaman',
        'Weirdnob Shaman Orruk Warclans',
    ),
    (
        'warchanter',
        'OW-016',
        'Warchanter',
        35.00,
        '99070209004_Warchanter01.jpg',
        f'{_GW}Ironjawz-Orruk-Warchanter',
        'Warchanter Orruk Warclans',
    ),
    (
        'megaboss',
        'OW-017',
        'Megaboss',
        48.00,
        '99070209003_Megaboss01.jpg',
        f'{_GW}Ironjawz-Orruk-Megaboss',
        'Megaboss Orruk Warclans',
    ),
    # ⚠ Dual kit: Gordrakk, the Fist of Gork and Megaboss on Maw-krusha share
    #   the same NK listing and MM listing.
    (
        'gordrakk-the-fist-of-gork',
        'OW-013',
        'Gordrakk, the Fist of Gork',
        145.00,
        '99120209032_GodrakkonBigTeef01.jpg',
        f'{_GW}Ironjawz-Orruk-Gordrakk-on-Bigteef',
        'Gordrakk, the Fist of Gork Orruk Warclans',
    ),
    (
        'megaboss-on-maw-krusha',
        'OW-014',
        'Megaboss on Maw-krusha',
        145.00,
        '99120209032_MawKrusha01.jpg',
        f'{_GW}Ironjawz-Orruk-Maw-Krusha',
        'Gordrakk, the Fist of Gork Orruk Warclans',
    ),
    (
        'breaka-boss-on-mirebrute-troggoth',
        'OW-022',
        'Breaka-boss on Mirebrute Troggoth',
        60.00,
        '99120209073_BreakaBossMirebruteTroggothLead.jpg',
        f'{_GW}orruk-warclans-breaka-boss-on-mirebrute-troggoth-2021',
        'Breaka-boss on Mirebrute Troggoth Orruk Warclans',
    ),
    # ⚠ Dual kit: Snatchaboss on Sludgeraker Beast and Swampboss Skumdrekk
    #   share the same NK listing and MM listing.
    (
        'snatchaboss-on-sludgeraker-beast',
        'OW-008',
        'Snatchaboss on Sludgeraker Beast',
        65.00,
        '99120209074_SwampbossSkumdrekkALT.jpg',
        f'{_GW}snatchaboss-on-sludgeraker-beast-2021',
        'Swampboss Skumdrekk Orruk Warclans',
    ),
    (
        'swampboss-skumdrekk',
        'OW-011',
        'Swampboss Skumdrekk',
        65.00,
        '99120209074_SwampbossSkumdrekkLead.jpg',
        f'{_GW}swampboss-skumdrekk-2021',
        'Swampboss Skumdrekk Orruk Warclans',
    ),

    # -- Units -----------------------------------------------------------------
    (
        'hobgrot-slittaz',
        'OW-001',
        'Hobgrot Slittaz',
        60.00,
        '99120209079_OWHobgrotSlittasLead.jpg',
        f'{_GW}orruk-warclans-hobgrot-slittas-2021',
        'Hobgrot Slittaz Orruk Warclans',
    ),
    (
        'beast-skewer-killbow',
        'OW-012',
        'Beast-skewer Killbow',
        39.00,
        '99120209072_BeastSkewerKillbowLead.jpg',
        f'{_GW}orruk-warclans-beast-skewer-killbow-2021',
        'Beast-skewer Killbow Orruk Warclans',
    ),
    (
        'gore-gruntas',
        'OW-015',
        'Gore-gruntas',
        89.00,
        '99120209031_GoreGruntaz01.jpg',
        f'{_GW}Ironjawz-Orruk-Gore-Gruntas',
        'Gore gruntas Orruk Warclans',
    ),
    (
        'monsta-killaz',
        'OW-018',
        'Monsta Killaz',
        60.00,
        '99120209116_KruleboyzMonstaKillaz3.jpg',
        f'{_GW}orruk-warclans-kruleboyz-monsta-killaz-2025',
        'Monsta Killaz Warcry',
    ),
    # ⚠ Dual kit: Brute Ragerz and Weirdbrute Wrekkaz share the same NK
    #   listing and MM listing.
    (
        'brute-ragerz',
        'OW-019',
        'Brute Ragerz',
        60.00,
        '99120209114_ORRWeirdbruteWrekkaz02Alt.jpg',
        f'{_GW}orruk-warclans-brute-ragerz-2023',
        'Weirdbrute Wrekkaz Orruk Warclans',
    ),
    (
        'weirdbrute-wrekkaz',
        'OW-020',
        'Weirdbrute Wrekkaz',
        60.00,
        '99120209114_ORRWeirdbruteWrekkaz02.jpg',
        f'{_GW}orruk-warclans-weirdbrute-wrekkaz-2023',
        'Weirdbrute Wrekkaz Orruk Warclans',
    ),
    (
        'man-skewer-boltboyz',
        'OW-024',
        'Man-Skewer Boltboyz',
        60.00,
        '99120209075_ORKManSkewerBoltboyzLead.jpg',
        f'{_GW}man-skewer-boltboyz-2021',
        'Man-Skewer Boltboyz Orruk Warclans',
    ),
    # ⚠ Dual kit: Maw-grunta Gouger, Maw-grunta with Hakkin' Krew, and
    #   Tuskboss on Maw-grunta all share the same NK listing and MM listing.
    (
        'maw-grunta-gouger',
        'OW-027',
        'Maw-grunta Gouger',
        85.00,
        '99120209111_ORRTuskbossOnMawGruntaAlt02.jpg',
        f'{_GW}orruk-warclans-maw-grunta-gougers-2023',
        'Tuskboss on Maw-grunta Orruk Warclans',
    ),
    (
        'maw-grunta-with-hakkin-krew',
        'OW-028',
        "Maw-grunta with Hakkin' Krew",
        85.00,
        '99120209111_ORRTuskbossOnMawGruntaAlt01.jpg',
        f'{_GW}orruk-warclans-maw-grunta-with-hakkin-krew-2023',
        'Tuskboss on Maw-grunta Orruk Warclans',
    ),
    (
        'tuskboss-on-maw-grunta',
        'OW-029',
        'Tuskboss on Maw-grunta',
        85.00,
        '99120209111_ORRTuskbossOnMawGrunta01.jpg',
        f'{_GW}orruk-warclans-tuskboss-on-maw-grunta-2023',
        'Tuskboss on Maw-grunta Orruk Warclans',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'destruction-battletome-orruk-warclans',
        'OW-023',
        'Destruction Battletome: Orruk Warclans',
        60.00,
        '60030209014_ENGOWSTDEDBattletome1.jpg',
        f'{_GW}battletome-orruk-warclans-hb-2025-eng',
        'Destruction Battletome: Orruk Warclans 4th Edition',
    ),
]


class Command(BaseCommand):
    """Populate Orruk Warclans products (OW-001 to OW-029)."""

    help = (
        'Creates / updates 29 Orruk Warclans products and seeds GW prices at MSRP. '
        'Uses existing Orruk Warclans faction. Does not touch the 5 pre-existing '
        'products with GW catalog SKUs. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_aos = Category.objects.get(slug='age-of-sigmar')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Age of Sigmar category not found -- run populate_products first.'
            ))
            return

        ow_faction, faction_created = Faction.objects.get_or_create(
            slug='orruk-warclans',
            defaults={'name': 'Orruk Warclans', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Orruk Warclans faction.')

        gw = Retailer.objects.filter(name='Games Workshop').first()

        products_created = 0
        products_updated = 0
        prices_created = 0
        prices_updated = 0

        for (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name) in PRODUCTS:
            image_url = _IMG.format(filename=image_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'faction': ow_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'orruk-warclans',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
                self.stdout.write(f'  Created: {name} ({gw_sku})')
            else:
                products_updated += 1
                self.stdout.write(f'  Updated: {name} ({gw_sku})')

            if gw:
                _, price_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw,
                    defaults={'price': msrp, 'url': gw_url, 'in_stock': True, 'not_available': False},
                )
                if price_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'populate_orruk_warclans_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
