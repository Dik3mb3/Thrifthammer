"""
Management command: populate_blades_of_khorne_products

Creates / updates all Blades of Khorne product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Blades of Khorne
faction if it does not already exist.

Covers 12 net-new products (BOK-001 to BOK-012) from the
AOS Blades of Khorne - GW, NK, MM.xlsx (2026-06-24).

Category: Age of Sigmar
Faction:  Blades of Khorne (created here via get_or_create)

Dual-kit products (same physical box, multiple build options):
  - BOK-003 Skullreapers / BOK-005 Wrathmongers (same NK listing)

No MM entries for: BOK-002, BOK-003, BOK-004, BOK-005, BOK-007,
BOK-008, BOK-010, BOK-012.

Dual-tagged products (NOT created here — primary faction is Chaos Daemons
or 40K daemon factions; add_blades_of_khorne_secondary_faction tags them):
  CD-006  Skulltaker
  CD-007  Skull Altar
  CD-011  Karanak
  CD-012  Bloodmaster, Herald of Khorne
  CD-019  Skull Cannon
  CD-020  Rendmaster, Herald of Khorne on Blood Throne
  P-KHORNE-FLESHHOUNDS     Flesh Hounds
  P-KHORNE-BLOODTHIRSTER   Bloodthirster
  P-KHORNE-BLOODCRUSHERS   Bloodcrushers
  P-KHORNE-SKARBRAND       Skarbrand

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_blades_of_khorne_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# -- Product definitions -------------------------------------------------------
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-24.
# ebay_search_name is set directly -- single source of truth for eBay search.
PRODUCTS = [

    # -- Heroes ----------------------------------------------------------------
    (
        'realmgore-ritualist',
        'BOK-001',
        'Realmgore Ritualist',
        39.00,
        '99070201031_RealmgoreRitualist1.jpg',
        f'{_GW}blades-of-khorne-realmgore-ritualist-2023',
        'Realmgore Ritualist Blades of Khorne',
    ),
    (
        'slaughterpriest',
        'BOK-007',
        'Slaughterpriest',
        35.00,
        '99070201012_KhorneSlaughterpriest01.jpg',
        f'{_GW}Khorne-Bloodbound-Slaughterpriest',
        'Slaughterpriest Blades of Khorne',
    ),
    (
        'deathbringer',
        'BOK-008',
        'Deathbringer',
        36.50,
        '99120201211_BOKDeathbringer01.jpg',
        f'{_GW}blades-of-khorne-deathbringer-2025',
        'Deathbringer Blades of Khorne',
    ),
    (
        'skullgrinder',
        'BOK-010',
        'Skullgrinder',
        35.00,
        '99070201011_KhorneSkullgrinder01.jpg',
        f'{_GW}Khorne-Bloodbound-Skullgrinder',
        'Skullgrinder Blades of Khorne',
    ),

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Skullreapers and Wrathmongers are built from the same box.
    #   Both share one NK listing.
    (
        'skullreapers',
        'BOK-003',
        'Skullreapers',
        62.50,
        '99120201042_KhorneSkullreapers01.jpg',
        f'{_GW}Khorne-Bloodbound-Skullreapers',
        'Wrathmongers Blades of Khorne',
    ),
    (
        'wrathmongers',
        'BOK-005',
        'Wrathmongers',
        62.50,
        '99120201042_KhorneWrathmongers01.jpg',
        f'{_GW}Khorne-Bloodbound-Wrathmongers',
        'Wrathmongers Blades of Khorne',
    ),
    (
        'blood-warriors',
        'BOK-006',
        'Blood Warriors',
        69.00,
        '99120201036_KhorneBloodWarriors01.jpg',
        f'{_GW}Khorne-Bloodbound-Blood-Warriors',
        'Blood Warriors Blades of Khorne',
    ),
    (
        'mighty-skullcrushers',
        'BOK-004',
        'Mighty Skullcrushers',
        110.00,
        '99120201043_KhorneSkullCrushers01.jpg',
        f'{_GW}Khorne-Bloodbound-Mighty-Skullcrushers',
        'Mighty Skullcrushers Blades of Khorne',
    ),
    (
        'claws-of-karanak',
        'BOK-011',
        'Claws of Karanak',
        60.00,
        '60010299039_Bloodhunt4.jpg',
        f'{_GW}blades-of-khorne-claws-of-karanak-2025',
        'Claws of Karanak Warcry',
    ),
    (
        'goreblade-warband',
        'BOK-012',
        'Goreblade Warband',
        102.00,
        '99120201215_BOKGorebladeWarband01.jpg',
        f'{_GW}blades-of-khorne-goreblade-warband-2025',
        'Goreblade Warband Blades of Khorne',
    ),

    # -- Terrain / Endless Spells ----------------------------------------------
    (
        'judgements-of-khorne',
        'BOK-002',
        'Judgements of Khorne',
        42.00,
        '99120201082_BoKHJudgementsofKhorne01.jpg',
        f'{_GW}Judgements-of-Khorne-2019',
        'Judgements of Khorne Blades of Khorne',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'chaos-battletome-blades-of-khorne',
        'BOK-009',
        'Chaos Battletome: Blades of Khorne',
        60.00,
        '60030201031_ENGBOKBattletome01.jpg',
        f'{_GW}battletome-blades-of-khorne-2025-eng',
        'Chaos Battletome: Blades of Khorne',
    ),
]


class Command(BaseCommand):
    """Populate Blades of Khorne products (BOK-001 to BOK-012)."""

    help = (
        'Creates / updates 12 Blades of Khorne products and seeds GW prices at MSRP. '
        'Creates Blades of Khorne faction if not present. Idempotent.'
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

        bok_faction, faction_created = Faction.objects.get_or_create(
            slug='blades-of-khorne',
            defaults={'name': 'Blades of Khorne', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Blades of Khorne faction.')

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
                    'faction': bok_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'blades-of-khorne',
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
            f'populate_blades_of_khorne_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
