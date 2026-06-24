"""
Management command: populate_maggotkin_of_nurgle_products

Creates / updates all Maggotkin of Nurgle product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Maggotkin of Nurgle
faction if it does not already exist.

Covers 21 net-new products (MON-001 to MON-021) from the
AOS Maggotkin of Nurgle - GW, NK, MM.xlsx (2026-06-24).

Category: Age of Sigmar
Faction:  Maggotkin of Nurgle (created here via get_or_create)

Dual-kit products (same physical box, multiple build options):
  - MON-002 Lord of Afflictions / MON-003 Pusgoyle Blightlords
    share one NK listing.
  - MON-005 Morbidex Twiceborn / MON-006 Bloab Rotspawned /
    MON-008 Orghotts Daemonspew
    share one NK listing (Maggoth Lord triple-kit).

No NK entries for: MON-011 The Court of Gelgus Pust, MON-012 Cankerborn,
MON-014 Pox-Wretches.
No MM entries for: MON-001, MON-002, MON-003, MON-004, MON-005,
MON-006, MON-008, MON-009, MON-010, MON-011, MON-012, MON-013,
MON-014, MON-018.

Dual-tagged products (NOT created here; add_maggotkin_of_nurgle_secondary_faction tags them):
  CD-008                    Feculent Gnarlmaw
  CD-009                    Horticulous Slimux
  CD-013                    Sloppity Bilepiper
  CD-014                    Poxbringer
  prod3700271-99129915063   Rotigus
  prod3700247-99129915063   Great Unclean One
  prod3700246-99129915062   Beast of Nurgle
  prod3610130-99129915038   Plague Drones
  prod3550127-99129915060   Nurglings

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_maggotkin_of_nurgle_products
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
        'rotbringer-sorcerer',
        'MON-001',
        'Rotbringer Sorcerer',
        35.00,
        '99070201027_RotbringerSorcererLead.jpg',
        f'{_GW}maggotkin-of-nurgle-rotbringer-sorcerer-2021',
        'Rotbringer Sorcerer Maggotkin of Nurgle',
    ),
    # ⚠ Dual kit: Lord of Afflictions and Pusgoyle Blightlords share one NK listing.
    (
        'lord-of-afflictions',
        'MON-002',
        'Lord of Afflictions',
        82.00,
        '99120201073_PusgoyleLordofAffliction01.jpg',
        f'{_GW}Lord-of-Afflictions-2018',
        'Pusgoyle Blightlords Maggotkin of Nurgle',
    ),
    (
        'lord-of-blights',
        'MON-004',
        'Lord of Blights',
        35.00,
        '99070201024_LordofBlights01.jpg',
        f'{_GW}Nurgle-Rotbringers-Lord-Of-Blights-2018',
        'Lord of Blights Maggotkin of Nurgle',
    ),
    # ⚠ Dual kit (triple): Morbidex Twiceborn, Bloab Rotspawned, and Orghotts Daemonspew
    #   all come from the same Maggoth Lord kit -- share one NK listing.
    (
        'morbidex-twiceborn',
        'MON-005',
        'Morbidex Twiceborn',
        89.00,
        '99120201038_MorbidexTwiceBorn01.jpg',
        f'{_GW}Rotbringers-Morbidex-Twiceborn',
        'Maggoth Lord Maggotkin of Nurgle',
    ),
    (
        'bloab-rotspawned',
        'MON-006',
        'Bloab Rotspawned',
        89.00,
        '99120201038_BlaobRotSpawn01.jpg',
        f'{_GW}Rotbringers-Bloab-Rotspawned',
        'Maggoth Lord Maggotkin of Nurgle',
    ),
    (
        'orghotts-daemonspew',
        'MON-008',
        'Orghotts Daemonspew',
        89.00,
        '99120201038_OrghottsDaemonSpew01.jpg',
        f'{_GW}Rotbringers-Orghotts-Daemonspew',
        'Maggoth Lord Maggotkin of Nurgle',
    ),
    (
        'lord-of-plagues',
        'MON-009',
        'Lord of Plagues',
        20.00,
        '99070201009_LordofPlagues01.jpg',
        f'{_GW}Rotbringers-Lord-of-Plagues',
        'Lord of Plagues Maggotkin of Nurgle',
    ),
    (
        'gutrot-spume',
        'MON-010',
        'Gutrot Spume',
        33.50,
        '99070201008_GutrotSprume01.jpg',
        f'{_GW}Rotbringers-Gutrot-Spume',
        'Gutrot Spume Maggotkin of Nurgle',
    ),
    (
        'spoilpox-scrivener',
        'MON-013',
        'Spoilpox Scrivener',
        40.00,
        '99120201213_WEBMaggotkinofNurgleSpoilpoxScrivener1.jpg',
        f'{_GW}maggotkin-of-nurgle-spoilpox-scrivener-2026',
        'Spoilpox Scrivener Maggotkin of Nurgle',
    ),
    (
        'festus-the-leechlord',
        'MON-016',
        'Festus the Leechlord',
        94.00,
        '99120201206_WEBMaggotkinofNurgleFestustheLeechlord1.jpg',
        f'{_GW}maggotkin-of-nurgle-festus-the-leechlord-2026',
        'Festus the Leechlord Maggotkin of Nurgle',
    ),
    (
        'harbinger-of-decay',
        'MON-018',
        'Harbinger of Decay',
        60.00,
        '99120201162_MaggothkinPhulgothsShudderhood1.jpg',
        f'{_GW}harbinger-of-decay-2023',
        'Harbinger of Decay Maggotkin of Nurgle',
    ),

    # -- Units -----------------------------------------------------------------
    (
        'pusgoyle-blightlords',
        'MON-003',
        'Pusgoyle Blightlords',
        82.00,
        '99120201073_PusgoyleBlightlords01.jpg',
        f'{_GW}Nurgle-Rotbringers-Pusgoyle-Blightlords-2018',
        'Pusgoyle Blightlords Maggotkin of Nurgle',
    ),
    (
        'pox-wretches',
        'MON-014',
        'Pox-Wretches',
        60.00,
        '99120201212_WEBMaggotkinofNurglePoxWretches1.jpg',
        f'{_GW}maggotkin-of-nurgle-pox-wretches-2026',
        'Pox-Wretches Maggotkin of Nurgle',
    ),
    (
        'pestigors',
        'MON-015',
        'Pestigors',
        60.00,
        '99120201208_WEBMaggotkinofNurglePestigors1.jpg',
        f'{_GW}maggotkin-of-nurgle-pestigors-2026',
        'Pestigors Maggotkin of Nurgle',
    ),
    (
        'sloven-knights',
        'MON-020',
        'Sloven Knights',
        69.00,
        '99120201209_WEBMaggotkinofNurgleSlovenKnights1.jpg',
        f'{_GW}maggotkin-of-nurgle-sloven-knights-2026',
        'Sloven Knights Maggotkin of Nurgle',
    ),
    (
        'rotswords',
        'MON-021',
        'Rotswords',
        65.00,
        '99120201207_WEBMaggotkinNurgleRotswords1.jpg',
        f'{_GW}maggotkin-of-nurgle-rotswords-2026',
        'Rotswords Maggotkin of Nurgle',
    ),

    # -- Named Characters / Monsters -------------------------------------------
    (
        'the-glottkin',
        'MON-007',
        'The Glottkin',
        145.00,
        '99120201040_TheGlottkin01.jpg',
        f'{_GW}Rotbringers-The-Glottkin',
        'The Glottkin Maggotkin of Nurgle',
    ),
    (
        'the-court-of-gelgus-pust',
        'MON-011',
        'The Court of Gelgus Pust',
        82.00,
        '99120201238_WEBMaggotkinofNurgleCourtofGelgusPust1.jpg',
        f'{_GW}maggotkin-of-nurgle-court-of-gelgus-pust-2026',
        'The Court of Gelgus Pust Maggotkin of Nurgle',
    ),
    (
        'cankerborn',
        'MON-012',
        'Cankerborn',
        52.00,
        '99120201237_WEBMaggotkinofNurgleCankerborn1.jpg',
        f'{_GW}maggotkin-of-nurgle-cankerborn-2026',
        'Cankerborn Maggotkin of Nurgle',
    ),

    # -- Warcry ----------------------------------------------------------------
    (
        'rotmire-creed',
        'MON-017',
        'Rotmire Creed',
        60.00,
        '99120201145_RotmireCreed2.jpg',
        f'{_GW}maggotkin-of-nurgle-rotmire-creed-2025',
        'Warcry Rotmire Creed',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'chaos-battletome-maggotkin-of-nurgle',
        'MON-019',
        'Chaos Battletome: Maggotkin of Nurgle',
        60.00,
        '60030201032_ENGWEBMaggotkinNurgleBattletomeHB1.jpg',
        f'{_GW}battletome-maggotkin-of-nurgle-2026-eng',
        'Chaos Battletome Maggotkin of Nurgle',
    ),
]


class Command(BaseCommand):
    """Populate Maggotkin of Nurgle products (MON-001 to MON-021)."""

    help = (
        'Creates / updates 21 Maggotkin of Nurgle products and seeds GW prices at MSRP. '
        'Creates Maggotkin of Nurgle faction if not present. Idempotent.'
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

        mon_faction, faction_created = Faction.objects.get_or_create(
            slug='maggotkin-of-nurgle',
            defaults={'name': 'Maggotkin of Nurgle', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Maggotkin of Nurgle faction.')

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
                    'faction': mon_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'maggotkin-of-nurgle',
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
            f'populate_maggotkin_of_nurgle_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
