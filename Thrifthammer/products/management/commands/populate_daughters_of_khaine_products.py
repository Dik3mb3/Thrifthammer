"""
Management command: populate_daughters_of_khaine_products

Creates / updates all Daughters of Khaine product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and uses the existing Daughters of Khaine
faction (slug=daughters-of-khaine, already in DB).

Covers 15 products (DOK-001 to DOK-015) from the
Daughters of Khaine - GW, NK, MM.xlsx (2026-06-17).

Category: Age of Sigmar
Faction:  Daughters of Khaine (existing -- get_or_create is safe/idempotent)

Dual-kit products (same physical box, multiple build options):
  - DOK-001 Blood Stalkers / DOK-006 Blood Sisters (Melusai kit, gw-85-20)
  - DOK-002 Khinerai Lifetakers / DOK-007 Khinerai Heartrenders (Khinerai kit, gw-85-19)
  - DOK-003 Bloodwrack Shrine / DOK-004 Slaughter Queen on Cauldron of Blood /
    DOK-005 Hag Queen on Cauldron of Blood (Cauldron of Blood kit -- three builds)

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_daughters_of_khaine_products
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

    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Blood Stalkers and Blood Sisters share the Melusai kit (gw-85-20).
    #   NK listing covers both builds under "Melusai Blood Stalkers".
    (
        'blood-stalkers',
        'DOK-001',
        'Blood Stalkers',
        62.50,
        '99120212033_DoKBloodSistersLead02.jpg',
        f'{_GW}Daughters-Of-Khaine-Melusai-Blood-Stalkers-2018',
        'Blood Sisters Age of Sigmar',
    ),
    # ⚠ Dual kit: Khinerai Lifetakers and Khinerai Heartrenders share the Khinerai
    #   kit (gw-85-19). NK listing covers both builds.
    (
        'khinerai-lifetakers',
        'DOK-002',
        'Khinerai Lifetakers',
        62.50,
        '99120212032_DoKKhineraiHeartrendersLifetakersLead02_a.jpg',
        f'{_GW}Daughters-Of-Khaine-Khinerai-Lifetakers-2018',
        'Khinerai Lifetakers Age of Sigmar',
    ),
    # ⚠ Triple kit: Bloodwrack Shrine, Slaughter Queen on Cauldron of Blood, and
    #   Hag Queen on Cauldron of Blood all build from the same Cauldron of Blood box.
    #   NK listing covers all three builds under "Cauldron of Blood / Bloodwrack Shrine".
    (
        'bloodwrack-shrine',
        'DOK-003',
        'Bloodwrack Shrine',
        89.00,
        '99120212018_BloodwrackShrine01.jpg',
        f'{_GW}Bloodwrack-Shine-2018',
        'Cauldron of Blood Daughters Khaine',
    ),
    (
        'slaughter-queen-on-cauldron-of-blood',
        'DOK-004',
        'Slaughter Queen on Cauldron of Blood',
        89.00,
        '99120212018_SlaughterQueenCauldronofBlood01.jpg',
        f'{_GW}Slaughter-Queen-on-Cauldron-of-Blood-2018',
        'Cauldron of Blood Daughters Khaine',
    ),
    (
        'hag-queen-on-cauldron-of-blood',
        'DOK-005',
        'Hag Queen on Cauldron of Blood',
        89.00,
        '99120212018_HagQueenCauldronofBlood01.jpg',
        f'{_GW}Haq-Queen-on-Cauldron-Blood-2018',
        'Cauldron of Blood Daughters Khaine',
    ),
    (
        'blood-sisters',
        'DOK-006',
        'Blood Sisters',
        62.50,
        '99120212033_DoKBloodSistersLead01.jpg',
        f'{_GW}Daughters-Of-Khaine-Melusai-Blood-Sisters-2018',
        'Blood Sisters Age of Sigmar',
    ),
    (
        'khinerai-heartrenders',
        'DOK-007',
        'Khinerai Heartrenders',
        62.50,
        '99120212032_DoKKhineraiHeartrendersLifetakersLead_a.jpg',
        f'{_GW}Daughters-Of-Khaine-Khinerai-Heartrenders-2018',
        'Khinerai Heartrenders Age of Sigmar',
    ),
    (
        'blood-hags',
        'DOK-010',
        'Blood Hags',
        60.00,
        '99120212045_DaughtersofKhaineBloodHags01.jpg',
        f'{_GW}daughters-of-khaine-blood-hags-2026',
        'Blood Hags Age of Sigmar',
    ),
    (
        'khainite-shadowstalkers',
        'DOK-012',
        'Khainite Shadowstalkers',
        60.00,
        '99120212036_KhainiteShadowstalkersUpdateLEAD.jpg',
        f'{_GW}khainite-shadowstalkers-2022',
        'Khainite Shadowstalkers Warhammer',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'shrine-of-dark-tribute',
        'DOK-008',
        'Shrine of Dark Tribute',
        69.00,
        '99120212050_DaughtersofKhaineShrine1.jpg',
        f'{_GW}daughters-of-khaine-shrine-of-dark-tribute-2026',
        'Shrine of Dark Tribute Age of Sigmar',
    ),
    (
        'melusai-ironscale',
        'DOK-009',
        'Melusai Ironscale',
        40.00,
        '99120212046_DaughtersOfKhaineMelusaiIronscale01.jpg',
        f'{_GW}daughters-of-khaine-melusai-ironscale-2026',
        'Melusai Ironscale Age of Sigmar',
    ),
    (
        'high-gladiatrix',
        'DOK-013',
        'High Gladiatrix',
        39.00,
        '99070212004_DokHighGladiatorixLead.jpg',
        f'{_GW}daughters-of-khaine-high-gladiatrix-2022',
        'High Gladiatrix Age of Sigmar',
    ),
    (
        'krethusa-the-croneseer',
        'DOK-015',
        'Krethusa the Croneseer',
        60.00,
        '99120212037_S2DKrethusaTheCroneseer01.jpg',
        f'{_GW}daughters-of-khaine-krethusa-the-croneseer-2024',
        'Krethusa the Croneseer Age of Sigmar',
    ),

    # -- Endless Spells --------------------------------------------------------
    (
        'endless-spells-daughters-of-khaine',
        'DOK-014',
        'Endless Spells: Daughters of Khaine',
        48.00,
        '99120212026_DoKEndlessSpellsLead.jpg',
        f'{_GW}Endless-Spells-Daughters-Of-Khaine-2021',
        'Endless Spells: Daughters of Khaine Age of Sigmar',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'order-battletome-daughters-of-khaine',
        'DOK-011',
        'Order Battletome: Daughters of Khaine',
        60.00,
        '60030212010_engDaughtersOfKhaineBattletome01.jpg',
        f'{_GW}battletome-daughters-of-khaine-2026-eng',
        'Order Battletome: Daughters of Khaine Age of Sigmar',
    ),
]


class Command(BaseCommand):
    """Populate Daughters of Khaine products (DOK-001 to DOK-015)."""

    help = (
        'Creates / updates 15 Daughters of Khaine products and seeds GW prices at MSRP. '
        'Uses existing Daughters of Khaine faction. Idempotent.'
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

        dok_faction, faction_created = Faction.objects.get_or_create(
            slug='daughters-of-khaine',
            defaults={'name': 'Daughters of Khaine', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Daughters of Khaine faction.')

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
                    'faction': dok_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'daughters-of-khaine',
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
            f'populate_daughters_of_khaine_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
