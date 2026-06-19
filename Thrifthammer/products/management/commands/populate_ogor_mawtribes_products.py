"""
Management command: populate_ogor_mawtribes_products

Creates / updates all Ogor Mawtribes product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Ogor Mawtribes
faction if it does not already exist.

Covers 26 products (OM-001 to OM-026) from the
AOS Ogor Mawtribes - GW, NK, MM.xlsx (2026-06-18).

Category: Age of Sigmar
Faction:  Ogor Mawtribes (new -- created here via get_or_create)

Dual-kit products (same physical box, multiple build options):
  - OM-009 Thundertusk Beastriders / OM-010 Stonehorn Beastriders /
    OM-011 Huskard on Thundertusk / OM-012 Huskard on Stonehorn /
    OM-013 Frostlord on Thundertusk / OM-015 Frostlord on Stonehorn
    (all from the Beastclaw Raiders kit -- same NK listing)

No NK entries for: OM-014 Icefall Yhetees, OM-021 Leadbelchers,
OM-026 Firebelly.
No MM entries for: all except OM-001, OM-004, OM-025.

Shared product (do NOT create here):
  - GG-009 Kragnos, the End of Empires (primary faction: Gloomspite Gitz)
    → secondary faction added by add_kragnos_secondary_factions command.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_ogor_mawtribes_products
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

    # -- Spearhead -------------------------------------------------------------
    (
        'spearhead-ogor-mawtribes-scrapglutt',
        'OM-001',
        'Spearhead: Ogor Mawtribes – Scrapglutt',
        150.00,
        '99120213034_OgorMawtribesScrapgluttSpearhead1.jpg',
        f'{_GW}spearhead-ogor-mawtribes-scrapglutt-2025',
        'Spearhead: Ogor Mawtribes – Scrapglutt Age of Sigmar',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'tyrant',
        'OM-002',
        'Tyrant',
        39.00,
        '99120213022_OMTyrant01.jpg',
        f'{_GW}Ogor-Mawtribes-Tyrant-2020',
        'Tyrant Ogor Mawtribes',
    ),
    (
        'maneaters',
        'OM-003',
        'Maneaters',
        106.00,
        '99810213025_OMManeatersLead.jpg',
        f'{_GW}ogor-mawtribes-2022',
        'Maneaters Ogor Mawtribes',
    ),
    (
        'bloodpelt-hunter',
        'OM-004',
        'Bloodpelt Hunter',
        47.00,
        '99120213025_BloodpeltHunterLead.jpg',
        f'{_GW}ogor-mawtribes-bloodpelt-hunter-2022',
        'Bloodpelt Hunter Ogor Mawtribes',
    ),
    (
        'slaughtermaster',
        'OM-016',
        'Slaughtermaster',
        82.00,
        '99810213017_Slaughtermaster01.jpg',
        f'{_GW}Butcher2',
        'Slaughtermaster Ogor Mawtribes',
    ),
    (
        'butcher',
        'OM-017',
        'Butcher',
        53.00,
        '99810213002_Butcher01.jpg',
        f'{_GW}Ogre-Kingdoms-Slaughtermaster-Butcher',
        'Butcher Ogor Mawtribes',
    ),
    (
        'icebrow-hunter',
        'OM-023',
        'Icebrow Hunter',
        53.00,
        '99800213022_IcebrowHunter01.jpg',
        f'{_GW}beastclaw-raiders-icebrow-hunter',
        'Icebrow Hunter Ogor Mawtribes',
    ),
    (
        'firebelly',
        'OM-026',
        'Firebelly',
        53.00,
        '99810213004_Firebelly01.jpg',
        f'{_GW}Firebelly',
        'Firebelly Ogor Mawtribes',
    ),

    # -- Units -----------------------------------------------------------------
    (
        'ogor-gluttons',
        'OM-005',
        'Ogor Gluttons',
        60.00,
        '99120213019_OgorBulls01.jpg',
        f'{_GW}Gutbusters-Ogors-2018',
        'Ogor Gluttons Ogor Mawtribes',
    ),
    (
        'great-mawpot',
        'OM-006',
        'Great Mawpot',
        53.00,
        '99120213021_CITOMGreatMawpot01.jpg',
        f'{_GW}Ogre-Mawtribes-Great-Mawpot-2019',
        'Great Mawpot Ogor Mawtribes',
    ),
    (
        'gnoblar-scraplauncher',
        'OM-007',
        'Gnoblar Scraplauncher',
        43.50,
        '99120213020_GutbustersScraplauncher01.jpg',
        f'{_GW}Scraplauncher-2018',
        'Gnoblar Scraplauncher Ogor Mawtribes',
    ),
    (
        'ironblaster',
        'OM-008',
        'Ironblaster',
        43.50,
        '99120213020_GutbustersIronblaster01.jpg',
        f'{_GW}Gutbusters-Ironblaster-2018',
        'Ironblaster Ogor Mawtribes',
    ),
    # ⚠ Dual kit: Thundertusk Beastriders, Stonehorn Beastriders,
    #   Huskard on Thundertusk, Huskard on Stonehorn, Frostlord on Thundertusk,
    #   Frostlord on Stonehorn all come from the same Beastclaw Raiders box.
    #   All six share one NK listing; none have a MM listing.
    (
        'thundertusk-beastriders',
        'OM-009',
        'Thundertusk Beastriders',
        77.00,
        '99120213016_RaidersonThundertusk01.jpg',
        f'{_GW}beastclaw-raiders-thundertusk-beastriders',
        'Thundertusk Beastriders Ogor Mawtribes',
    ),
    (
        'stonehorn-beastriders',
        'OM-010',
        'Stonehorn Beastriders',
        77.00,
        '99120213016_RaidersOnStonehorn01.jpg',
        f'{_GW}beastclaw-raiders-stonehorn-beastriders',
        'Stonehorn Beastriders Ogor Mawtribes',
    ),
    (
        'huskard-on-thundertusk',
        'OM-011',
        'Huskard on Thundertusk',
        77.00,
        '99120213016_HuskardOnThundertusk01.jpg',
        f'{_GW}beastclaw-raiders-huskard-on-thundertusk',
        'Huskard on Thundertusk Ogor Mawtribes',
    ),
    (
        'huskard-on-stonehorn',
        'OM-012',
        'Huskard on Stonehorn',
        77.00,
        '99120213016_HuskardOnStonehorn01.jpg',
        f'{_GW}beastclaw-raiders-huskard-on-stonehorn',
        'Huskard on Stonehorn Ogor Mawtribes',
    ),
    (
        'frostlord-on-thundertusk',
        'OM-013',
        'Frostlord on Thundertusk',
        77.00,
        '99120213016_FrostlordOnThundertusk01.jpg',
        f'{_GW}beastclaw-raiders-frostlord-on-thundertusk',
        'Frostlord on Thundertusk Ogor Mawtribes',
    ),
    (
        'icefall-yhetees',
        'OM-014',
        'Icefall Yhetees',
        60.00,
        '99810213020_BeastclawYhetees01.jpg',
        f'{_GW}beastclaw-raiders-icefall-yhetees',
        'Icefall Yhetees Ogor Mawtribes',
    ),
    (
        'frostlord-on-stonehorn',
        'OM-015',
        'Frostlord on Stonehorn',
        77.00,
        '99120213016_FrostlordonStonehorn01.jpg',
        f'{_GW}beastclaw-raiders-frostlord-on-stonehorn',
        'Frostlord on Stonehorn Ogor Mawtribes',
    ),
    (
        'gorger-mawpack',
        'OM-018',
        'Gorger Mawpack',
        60.00,
        '60120299003_WCHandHCoreGame4.jpg',
        f'{_GW}ogor-mawtribes-gorger-mawpack-2025',
        'Gorger Mawpack Ogor Mawtribes',
    ),
    (
        'mawpit',
        'OM-019',
        'Mawpit',
        60.00,
        '99120299098_OMMawpit01.jpg',
        f'{_GW}ogor-mawtribes-maw-pit-2023',
        'Mawpit Ogor Mawtribes',
    ),
    (
        'mournfang-pack',
        'OM-020',
        'Mournfang Pack',
        82.00,
        '99120213015_MournfangPack01.jpg',
        f'{_GW}beastclaw-raiders-mournfang-pack',
        'Mournfang Pack Ogor Mawtribes',
    ),
    (
        'leadbelchers',
        'OM-021',
        'Leadbelchers',
        48.00,
        '99120213013_OMLeadbelchers01.jpg',
        f'{_GW}Ogre-Kingdoms-Leadbelchers',
        'Leadbelchers Ogor Mawtribes',
    ),
    (
        'gnoblars',
        'OM-022',
        'Gnoblars',
        42.00,
        '99120213012_OMGnoblars01.jpg',
        f'{_GW}Gnoblar-Fighters',
        'Gnoblars Ogor Mawtribes',
    ),
    (
        'frost-sabres',
        'OM-024',
        'Frost Sabres',
        25.00,
        '99800213021_FrostSabres01.jpg',
        f'{_GW}beastclaw-raiders-frost-sabres',
        'Frost Sabres Ogor Mawtribes',
    ),
    (
        'ironguts',
        'OM-025',
        'Ironguts',
        48.00,
        '99120213014_OMIronguts01.jpg',
        f'{_GW}Ogre-Kingdoms-Ironguts',
        'Ironguts Ogor Mawtribes',
    ),
]


class Command(BaseCommand):
    """Populate Ogor Mawtribes products (OM-001 to OM-026)."""

    help = (
        'Creates / updates 26 Ogor Mawtribes products and seeds GW prices at MSRP. '
        'Creates Ogor Mawtribes faction if not present. Idempotent.'
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

        om_faction, faction_created = Faction.objects.get_or_create(
            slug='ogor-mawtribes',
            defaults={'name': 'Ogor Mawtribes', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Ogor Mawtribes faction.')

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
                    'faction': om_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'ogor-mawtribes',
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
            f'populate_ogor_mawtribes_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
