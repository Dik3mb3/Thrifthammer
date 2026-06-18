"""
Management command: populate_lumineth_realm_lords_products

Creates / updates all Lumineth Realm-lords product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Lumineth Realm-lords
faction if it does not already exist.

Covers 26 products (LRL-001 to LRL-026) from the
AOS Lumineth Realm Lords - GW, NK, MM.xlsx (2026-06-17).

Category: Age of Sigmar
Faction:  Lumineth Realm-lords (get_or_create -- safe whether pre-existing or new)

Dual-kit products (same physical box, multiple build options):
  - LRL-001 Alarith Spirit of the Mountain / LRL-004 Avalenor, the Stoneheart King
    (same kit -- NK listing covers both builds; no MM for either)
  - LRL-007 Hurakan Spirit of the Wind / LRL-016 Sevireth, Lord of the Seventh Wind
    (same kit -- NK and MM listings cover both builds)
  - LRL-010 Lyrior Uthralle, Warden of Ymetrica / LRL-023 Vanari Lord Regent (2021)
    (same kit -- NK listing covers both builds; no MM for either)

Note: LRL-023 Vanari Lord Regent (2021) is a different product from
LRL-024 Vanari Lord Regent (2026 new model). The 2021 version shares a kit
with Lyrior Uthralle; the 2026 version is a new standalone model. Names
distinguished with (2021) qualifier to avoid slug collision.

Note: LRL-026 Warcry Ydrilan Riverblades is a Warcry warband tagged to
Lumineth Realm-lords per user data.

No NK entries for: LRL-006 Endless Spells.
No MM entries for: LRL-001, LRL-002, LRL-003, LRL-004, LRL-005, LRL-006,
LRL-009, LRL-010, LRL-012, LRL-013, LRL-015, LRL-017, LRL-018, LRL-020,
LRL-022, LRL-023, LRL-025.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_lumineth_realm_lords_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# -- Product definitions -------------------------------------------------------
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-17.
# ebay_search_name is set directly -- single source of truth for eBay search.
PRODUCTS = [

    # -- Heroes ----------------------------------------------------------------
    (
        'alarith-stonemage',
        'LRL-002',
        'Alarith Stonemage',
        47.00,
        '99120210037_LRLAlaStonLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Alarith-Stonemage-2020',
        'Alarith Stonemage Age of Sigmar',
    ),
    (
        'archmage-teclis-and-celennar-spirit-of-hysh',
        'LRL-003',
        'Archmage Teclis and Celennar, Spirit of Hysh',
        195.00,
        '99120210038_LRLArchTecCelSpiHysLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Archmage-Teclis-2020',
        'Archmage Teclis Age of Sigmar',
    ),
    (
        'ellania-and-ellathor-eclipsian-warsages',
        'LRL-005',
        'Ellania and Ellathor, Eclipsian Warsages',
        60.00,
        '99120210029_LRLEllaniaEllathorLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Ellania-And-Ellathor-2021',
        'Ellania and Ellathor Warhammer',
    ),
    (
        'hurakan-windmage',
        'LRL-009',
        'Hurakan Windmage',
        43.50,
        '99120210028_HurakanWindmageLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Hurakan-Windmage-2021',
        'Hurakan Windmage Age of Sigmar',
    ),
    (
        'lyrior-uthralle-warden-of-ymetrica',
        'LRL-010',
        'Lyrior Uthralle, Warden of Ymetrica',
        65.00,
        '99120210031_LRLLyriorUthralleVanariLordRegentLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Lyrior-Uthralle-2021',
        'Lyrior Uthralle Warden of Ymetrica Lumineth Realm-Lords Warhammer',
    ),
    (
        'scinari-calligrave',
        'LRL-012',
        'Scinari Calligrave',
        35.00,
        '99070210002_LRLScinariCalligraveLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Scinari-Calligrave-2021',
        'Scinari Calligrave Lumineth Realm Lords Warhammer',
    ),
    (
        'scinari-cathallar',
        'LRL-013',
        'Scinari Cathallar',
        35.00,
        '99070210004_LRLScinariCathLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Scinari-Cathallar-2020',
        'Scinari Cathallar Age of Sigmar',
    ),
    (
        'scinari-enlightener',
        'LRL-014',
        'Scinari Enlightener',
        35.00,
        '60010299033_EAoSArcaneCataclysmSingle01.jpg',
        f'{_GW}lumineth-scinari-enlightener-2022',
        'Scinari Enlightener Age of Sigmar',
    ),
    (
        'scinari-loreseeker',
        'LRL-015',
        'Scinari Loreseeker',
        35.00,
        '99070210003_LRLScinariLoreseekerLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Scinari-Loreseeker-2021',
        'Scinari Loreseeker Lumineth Realm Lords Warhammer',
    ),
    (
        'the-light-of-eltharion',
        'LRL-018',
        'The Light of Eltharion',
        48.00,
        '99120210040_LightEltharionLead.jpg',
        f'{_GW}Lumineth-Realm-lords-The-Light-of-Eltharion-2020',
        'The Light of Eltharion Age of Sigmar',
    ),
    (
        'vanari-bannerblade',
        'LRL-020',
        'Vanari Bannerblade',
        39.00,
        '99120210032_LRLVanariBannerbladeLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Vanari-Bannerblade-2021',
        'Vanari Bannerblade Age of Sigmar',
    ),
    # ⚠ Dual kit: Lyrior Uthralle and Vanari Lord Regent (2021) share the same
    #   kit. NK listing covers both builds under "Lyrior Uthralle". Named with
    #   (2021) qualifier to distinguish from the separate 2026 Vanari Lord Regent.
    (
        'vanari-lord-regent-2021',
        'LRL-023',
        'Vanari Lord Regent (2021)',
        65.00,
        '99120210031_LRLLyriorUthralleVanariLordRegentLeadAlt.jpg',
        f'{_GW}Vanari-Lord-Regent-2021',
        'Lyrior Uthralle Warden of Ymetrica Lumineth Realm-Lords Warhammer',
    ),
    (
        'vanari-lord-regent',
        'LRL-024',
        'Vanari Lord Regent',
        43.50,
        '99120210065_LuminethRealmlordsVanariLordRegent01.jpg',
        f'{_GW}lumineth-realmlords-vanari-lord-regent-2026',
        'Vanari Lord Regent Age of Sigmar',
    ),

    # -- Large Kits / Monsters -------------------------------------------------
    # ⚠ Dual kit: Alarith Spirit of the Mountain and Avalenor, the Stoneheart King
    #   share the same kit. NK listing covers both builds under "Avalenor".
    (
        'alarith-spirit-of-the-mountain',
        'LRL-001',
        'Alarith Spirit of the Mountain',
        130.00,
        '99120210039_LRLAvalenorStoneheartKingAlt.jpg',
        f'{_GW}Lumineth-Realm-lords-Sprit-of-the-Mountain-2020',
        'Avalenor, the Stoneheart King Age of Sigmar',
    ),
    (
        'avalenor-the-stoneheart-king',
        'LRL-004',
        'Avalenor, the Stoneheart King',
        130.00,
        '99120210039_LRLAvalenorStoneheartKingLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Avalenor-The-Stoneheart-King-2020',
        'Avalenor, the Stoneheart King Age of Sigmar',
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Hurakan Spirit of the Wind and Sevireth, Lord of the Seventh
    #   Wind share the same kit. NK and MM listings cover both builds under "Sevireth".
    (
        'hurakan-spirit-of-the-wind',
        'LRL-007',
        'Hurakan Spirit of the Wind',
        65.00,
        '99120210027_SpiritofWindLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Hurakan-Spirit-of-the-Wind-2021',
        'Sevireth, Lord of the Seventh Wind Age of Sigmar',
    ),
    (
        'sevireth-lord-of-the-seventh-wind',
        'LRL-016',
        'Sevireth, Lord of the Seventh Wind',
        65.00,
        '99120210027_SevirethLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Sevireth-Lord-of-the-Seventh-Wind-2021',
        'Sevireth, Lord of the Seventh Wind Age of Sigmar',
    ),
    (
        'hurakan-windchargers',
        'LRL-008',
        'Hurakan Windchargers',
        73.50,
        '99120210030_LRLHurakanWindchargersLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Hurakan-Windchargers-2021',
        'Hurakan Windchargers Age of Sigmar',
    ),
    (
        'vanari-auralan-sentinels',
        'LRL-019',
        'Vanari Auralan Sentinels',
        65.00,
        '99120210041_VanAurSenLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Vanari-Auralan-Sentinels-2020',
        'Vanari Auralan Sentinels Age of Sigmar',
    ),
    (
        'vanari-bladelords',
        'LRL-021',
        'Vanari Bladelords',
        62.50,
        '99120210033_LRLVanariBladelordsLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Vanari-Bladelords-2021',
        'Vanari Bladelords Age of Sigmar',
    ),
    (
        'vanari-dawnriders',
        'LRL-022',
        'Vanari Dawnriders',
        73.50,
        '99120210043_LRLVanDawLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Vanari-Dawnriders-2020',
        'Vanari Dawnriders Warhammer Age of Sigmar',
    ),
    (
        'vanari-starshard-ballista',
        'LRL-025',
        'Vanari Starshard Ballista',
        60.00,
        '99120210026_LRLVanariStarshardBallistaLead.jpg',
        f'{_GW}Vanari-Starshard-Ballista-2021',
        'Vanari Starshard Ballista Age of Sigmar',
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'shrine-luminor',
        'LRL-017',
        'Shrine Luminor',
        69.00,
        '99120210035_LRLShrineLuminorLead.jpg',
        f'{_GW}Lumineth-Realm-lords-Shrine-Luminor-2021',
        'Shrine Luminor Age of Sigmar',
    ),

    # -- Endless Spells --------------------------------------------------------
    (
        'endless-spells-lumineth-realm-lords',
        'LRL-006',
        'Endless Spells: Lumineth Realm-lords',
        48.00,
        '99120210034_LRLEndlessSpellsLead.jpg',
        f'{_GW}Endless-Spells-Lumineth-Realm-lords-2020',
        'Endless Spells Lumineth Realm-lords Age of Sigmar',
    ),

    # -- Warcry ----------------------------------------------------------------
    (
        'warcry-ydrilan-riverblades',
        'LRL-026',
        'Warcry Ydrilan Riverblades',
        65.00,
        '60120299005_EngWCPyreAndFlood02.jpg',
        f'{_GW}warcry-ydrilan-riverblades-2024',
        'Warcry Ydrilan Riverblades Age of Sigmar',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-lumineth-realm-lords',
        'LRL-011',
        'Order Battletome: Lumineth Realm-lords',
        60.00,
        '60030210012_engLuminethRealmlordsBattletome01.jpg',
        f'{_GW}battletome-lumineth-realmlords-2026-eng',
        'Warhammer Age of Sigmar Battletome Lumineth Realm Lords 2026',
    ),
]


class Command(BaseCommand):
    """Populate Lumineth Realm-lords products (LRL-001 to LRL-026)."""

    help = (
        'Creates / updates 26 Lumineth Realm-lords products and seeds GW prices at MSRP. '
        'Creates Lumineth Realm-lords faction if it does not exist. Idempotent.'
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

        lrl_faction, faction_created = Faction.objects.get_or_create(
            slug='lumineth-realm-lords',
            defaults={'name': 'Lumineth Realm-lords', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Lumineth Realm-lords faction.')

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
                    'faction': lrl_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'lumineth-realm-lords',
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
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                if price_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'populate_lumineth_realm_lords_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
