"""
Management command: populate_kharadron_overlords_products

Creates / updates all Kharadron Overlords product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Kharadron Overlords
faction if it does not already exist.

Covers 20 products (KO-001 to KO-020) from the
AOS Kharadron Overlords - GW, NK, MM.xlsx (2026-06-17).

Category: Age of Sigmar
Faction:  Kharadron Overlords (get_or_create -- safe whether pre-existing or new)

Dual-kit products (same physical box, multiple build options):
  - KO-005 Skywardens / KO-009 Endrinriggers (same Skyriggers kit gw-84-21).
    NK has separate listings for each build; MM listing only exists for Endrinriggers.

No NK entries for: KO-007 Brokk Grungsson.
No MM entries for: KO-003 Endrinmaster with Dirigible Suit, KO-005 Skywardens,
KO-006 Aether-Khemist, KO-007 Brokk Grungsson, KO-008 Aetheric Navigator,
KO-013 Arkanaut Frigate, KO-014 Arkanaut Admiral, KO-020 Endrinmaster
with Endrinharness.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_kharadron_overlords_products
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

    # -- Spearhead -------------------------------------------------------------
    (
        'spearhead-kharadron-overlords-grundstok-trailblazers',
        'KO-001',
        'Spearhead: Kharadron Overlords – Grundstok Trailblazers',
        150.00,
        '99120205063_KharadronOverlordsGrundstokTrailblazersSpearhead1.jpg',
        f'{_GW}spearhead-kharadron-overlords-grundstok-trailblazers-2025',
        'Spearhead Kharadron Overlords Grundstok Trailblazers Age of Sigmar',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'codewright',
        'KO-002',
        'Codewright',
        39.00,
        '99120205048_KOCodewright01.jpg',
        f'{_GW}kharadron-overlords-codewright-2023',
        'Codewright Age of Sigmar',
    ),
    (
        'endrinmaster-with-dirigible-suit',
        'KO-003',
        'Endrinmaster with Dirigible Suit',
        43.50,
        '99120205040_EndrinmasterDirigibleSuitLead.jpg',
        f'{_GW}Endrinmaster-with-Dirigible-Suit-2020',
        'Endrinmaster With Dirigible Suit Kharadron Overlords',
    ),
    (
        'aether-khemist',
        'KO-006',
        'Aether-Khemist',
        35.00,
        '99070205011_Khemist01.jpg',
        f'{_GW}Kharadron-Overlords-Aether-Khemist-2017',
        'Aether-Khemist Kharadron Overlords',
    ),
    (
        'brokk-grungsson-lord-magnate-of-barak-nar',
        'KO-007',
        'Brokk Grungsson, Lord-Magnate of Barak-Nar',
        48.00,
        '99120205023_BrokkGrungsson01.jpg',
        f'{_GW}Brokk-Grungsson-Lord-Magnate-Barak-nar-2017',
        'Brokk Grungsson Kharadron Overlords Warhammer',
    ),
    (
        'aetheric-navigator',
        'KO-008',
        'Aetheric Navigator',
        35.00,
        '99070205010_Navigator01.jpg',
        f'{_GW}Kharadron-Overlords-Aetheric-navigator-2017',
        'Aetheric Navigator Age of Sigmar',
    ),
    (
        'arkanaut-admiral',
        'KO-014',
        'Arkanaut Admiral',
        35.00,
        '99070205012_ArkanautAdmiral01.jpg',
        f'{_GW}Kharadron-Overlords-Arkanaut-admiral-2017',
        'Arkanaut Admiral Age of Sigmar',
    ),
    (
        'drekki-flynt',
        'KO-019',
        'Drekki Flynt',
        39.00,
        '99120205044_DrekkiFlyntLead.jpg',
        f'{_GW}kharadron-overlords-drekki-flynt-2022',
        'Warhammer Kharadron Overlords Drekki Flynt',
    ),
    (
        'endrinmaster-with-endrinharness',
        'KO-020',
        'Endrinmaster with Endrinharness',
        35.00,
        '99070205013_Endrinmaster01.jpg',
        f'{_GW}Kharadron-Overlords-Endrinmaster-2017',
        'Endrinmaster with Endrinharness Kharadron Overlords Warhammer',
    ),
    (
        'null-khemist',
        'KO-016',
        'Null-Khemist',
        48.00,
        '99120205067_KharadronOverlordsNullKhemistCharacter1.jpg',
        f'{_GW}kharadron-overlords-null-khemist-2025',
        'Null-Khemist Age of Sigmar',
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Skywardens and Endrinriggers share the same Skyriggers kit.
    #   NK has separate listings for each build. MM listing only for Endrinriggers.
    (
        'skywardens',
        'KO-005',
        'Skywardens',
        60.00,
        '99120205021_Skywardens01.jpg',
        f'{_GW}Skyriggers-2017',
        'Skywardens Age of Sigmar',
    ),
    (
        'endrinriggers',
        'KO-009',
        'Endrinriggers',
        60.00,
        '99120205053_KhardronOverlordsEndrinriggersUPDATE.jpg',
        f'{_GW}Endrinriggers-2017',
        'Skyriggers Age of Sigmar',
    ),
    (
        'grundstok-thunderers',
        'KO-010',
        'Grundstok Thunderers',
        60.00,
        '99120205054_KOGrundstokThunderers02.jpg',
        f'{_GW}Kharadron-Overlords-Grundstok-Thunderers-2017',
        'Warhammer Age of Sigmar Kharadron Grundstok Thunderers',
    ),
    (
        'arkanaut-company',
        'KO-012',
        'Arkanaut Company',
        60.00,
        '99120205020_ArkanautCompany01.jpg',
        f'{_GW}Kharadron-Overlords-Arkanaut-company-2017',
        'Arkanaut Company Age of Sigmar',
    ),
    (
        'vongrim-harpoon-crew',
        'KO-017',
        'Vongrim Harpoon Crew',
        60.00,
        '99120205064_KharadronOverlordsVongrimHarpoonCrew1.jpg',
        f'{_GW}kharadron-overlords-vongrim-harpoon-crew-2025',
        'Vongrim Harpoon Crew Age of Sigmar',
    ),

    # -- Large Kits / Vessels --------------------------------------------------
    (
        'arkanaut-ironclad',
        'KO-004',
        'Arkanaut Ironclad',
        150.00,
        '99120205028_ArkanautIronclad01.jpg',
        f'{_GW}Kharadron-Overlords-Arkanaut-Ironclad-2017',
        'Arkanaut Ironclad Age of Sigmar',
    ),
    (
        'grundstok-gunhauler',
        'KO-011',
        'Grundstok Gunhauler',
        65.00,
        '99120205051_KOGrundstokGunhauler01.jpg',
        f'{_GW}Kharadron-Overlords-Grundstok-Gunhauler-2017',
        'Grundstok Gunhauler Age of Sigmar',
    ),
    (
        'arkanaut-frigate',
        'KO-013',
        'Arkanaut Frigate',
        96.00,
        '99120205018_ArkanautFrigate01.jpg',
        f'{_GW}Kharadron-Overlords-Arkanaut-frigate-2017',
        'Arkanaut Frigate Age of Sigmar',
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'zontari-endrin-dock',
        'KO-015',
        'Zontari Endrin Dock',
        65.00,
        '99120205068_KharadronOverlordsZontariEndrinDockSceneryKit1.jpg',
        f'{_GW}kharadron-overlords-zontari-endrin-dock-2025',
        'Zontari Endrin Dock Age of Sigmar',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-kharadron-overlords',
        'KO-018',
        'Order Battletome: Kharadron Overlords',
        60.00,
        '60030205015_ENGKharadronOverlordsStdEdHBBattletome1.jpg',
        f'{_GW}battletome-kharadron-overlords-2025-eng',
        'Order Battletome: Kharadron Overlords Age of Sigmar',
    ),
]


class Command(BaseCommand):
    """Populate Kharadron Overlords products (KO-001 to KO-020)."""

    help = (
        'Creates / updates 20 Kharadron Overlords products and seeds GW prices at MSRP. '
        'Creates Kharadron Overlords faction if it does not exist. Idempotent.'
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

        ko_faction, faction_created = Faction.objects.get_or_create(
            slug='kharadron-overlords',
            defaults={'name': 'Kharadron Overlords', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Kharadron Overlords faction.')

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
                    'faction': ko_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'kharadron-overlords',
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
            f'populate_kharadron_overlords_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
