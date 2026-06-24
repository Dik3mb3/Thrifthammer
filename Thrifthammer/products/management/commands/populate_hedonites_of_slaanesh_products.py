"""
Management command: populate_hedonites_of_slaanesh_products

Creates / updates all Hedonites of Slaanesh product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Hedonites of Slaanesh
faction if it does not already exist.

Covers 15 net-new products (HOS-001 to HOS-015) from the
AOS Hedonites of Slaanesh - GW, NK, MM.xlsx (2026-06-24).

Slug collision resolved: HOS-016 The Masque already exists in the DB as
CD-005 (Chaos Daemons). It is dual-tagged via
add_hedonites_of_slaanesh_secondary_faction instead.

Category: Age of Sigmar
Faction:  Hedonites of Slaanesh (created here via get_or_create)

Dual-kit products (same physical box, multiple build options):
  - HOS-002 Synessa, the Voice of Slaanesh / HOS-003 Dexcessa, the Talon
    of Slaanesh share one NK listing (Dexcessa) and one MM listing.
  - HOS-004 Symbaresh Twinsouls / HOS-011 Myrmidesh Painbringers share one
    NK listing (Myrmidesh Painbringers) and one MM listing.
  - HOS-005 Blissbarb Seekers / HOS-010 Slickblade Seekers share one NK
    listing (Slickblade Seekers).

No MM entries for: HOS-005, HOS-007, HOS-010, HOS-014, HOS-015, HOS-016.

All 16 products have confirmed NK URLs.

Dual-tagged products (NOT created here; add_hedonites_of_slaanesh_secondary_faction tags them):
  CD-002  Syll'Esske: The Vengeful Allegiance
  CD-003  The Contorted Epitome
  CD-004  Infernal Enrapturess
  CD-005  The Masque (slug collision -- already in DB as Chaos Daemons)
  99129915036  Daemonettes of Slaanesh
  99129915056  Keeper of Secrets / Shalaxi Helbane (same GW SKU)
  99129915052  Fiends
  99129915005  Seekers of Slaanesh

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_hedonites_of_slaanesh_products
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
        'lord-of-hubris',
        'HOS-001',
        'Lord of Hubris',
        39.00,
        '99070201033_SLALordOfHubris01.jpg',
        f'{_GW}hedonites-of-slaanesh-lord-of-hubris-2023',
        'Lord of Hubris Hedonites of Slaanesh',
    ),
    # ⚠ Dual kit: Synessa and Dexcessa share one NK listing and one MM listing.
    (
        'synessa-the-voice-of-slaanesh',
        'HOS-002',
        'Synessa, the Voice of Slaanesh',
        130.00,
        '99129915059_DexcessaSyncessaLeadAlt.jpg',
        f'{_GW}Synessa-the-Voice-of-Slaanesh-2021',
        'Dexcessa, the Talon of Slaanesh Hedonites of Slaanesh',
    ),
    (
        'dexcessa-the-talon-of-slaanesh',
        'HOS-003',
        'Dexcessa, the Talon of Slaanesh',
        130.00,
        '99129915059_DexcessaSyncessaLead.jpg',
        f'{_GW}Dexcessa-The-Talon-Of-Slaanesh-2021',
        'Dexcessa, the Talon of Slaanesh Hedonites of Slaanesh',
    ),
    (
        'glutos-orscollion-lord-of-gluttony',
        'HOS-007',
        'Glutos Orscollion, Lord of Gluttony',
        145.00,
        '99120201105_GlutosOrscollionLordofGluttonyLead.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Glutos-Orscollion-Lord-Of-Gluttony-2020',
        'Glutos Orscollion Hedonites of Slaanesh',
    ),
    (
        'sigvald-prince-of-slaanesh',
        'HOS-009',
        'Sigvald, Prince of Slaanesh',
        65.00,
        '99120201103_SigvaldPrinceofSlaaneshLead.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Sigvald-Prince-Of-Slaanesh-2020',
        'Sigvald Prince of Slaanesh Hedonites of Slaanesh',
    ),
    (
        'lord-of-pain',
        'HOS-012',
        'Lord of Pain',
        35.00,
        '99070201026_HoSLordofPainLead.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Lord-Of-Pain-2020',
        'Lord of Pain Hedonites of Slaanesh',
    ),
    (
        'shardspeaker-of-slaanesh',
        'HOS-013',
        'Shardspeaker of Slaanesh',
        35.00,
        '99070201025_HoSShardspeakerofSlaaneshLead.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Shardspeaker-Of-Slaanesh-2020',
        'Shardspeaker of Slaanesh Hedonites of Slaanesh',
    ),
    # -- Units -----------------------------------------------------------------
    # ⚠ Dual kit: Symbaresh Twinsouls and Myrmidesh Painbringers share one NK + MM listing.
    (
        'symbaresh-twinsouls',
        'HOS-004',
        'Symbaresh Twinsouls',
        62.50,
        '99120201101_HoSSymbareshTwinsoulsLead.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Symbaresh-Twinsouls-2020',
        'Myrmidesh Painbringers Hedonites of Slaanesh',
    ),
    # ⚠ Dual kit: Blissbarb Seekers and Slickblade Seekers share one NK listing.
    (
        'blissbarb-seekers',
        'HOS-005',
        'Blissbarb Seekers',
        73.50,
        '99120201102_HoSSlickbladeBlissbarbSeekersLead2.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Blissbarb-Seekers-2020',
        'Slickblade Seekers Hedonites of Slaanesh',
    ),
    (
        'slaangor-fiendbloods',
        'HOS-006',
        'Slaangor Fiendbloods',
        60.00,
        '99120201106_HoSSlaangorFiendbloodsLead.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Slaangor-Fiendbloods-2020',
        'Slaangor Fiendbloods Hedonites of Slaanesh',
    ),
    (
        'blissbarb-archers',
        'HOS-008',
        'Blissbarb Archers',
        60.00,
        '99120201104_BlissbarbArchersLead.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Blissbarb-Archers-2020',
        'Blissbarb Archers Hedonites of Slaanesh',
    ),
    (
        'slickblade-seekers',
        'HOS-010',
        'Slickblade Seekers',
        73.50,
        '99120201102_HoSSlickbladeBlissbarbSeekersLead1.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Slickblade-Seekers-2020',
        'Slickblade Seekers Hedonites of Slaanesh',
    ),
    (
        'myrmidesh-painbringers',
        'HOS-011',
        'Myrmidesh Painbringers',
        62.50,
        '99120201101_HoSMyrmideshPainbringersLead.jpg',
        f'{_GW}Hedonites-Of-Slaanesh-Myrmidesh-Painbringers-2020',
        'Myrmidesh Painbringers Hedonites of Slaanesh',
    ),

    # -- Terrain / Endless Spells ----------------------------------------------
    (
        'fane-of-slaanesh',
        'HOS-014',
        'Fane of Slaanesh',
        53.00,
        '99120299060_CITDoSFaneofSlaanesh01.jpg',
        f'{_GW}Fane-of-Slaanesh-2019',
        'Fane of Slaanesh Hedonites of Slaanesh',
    ),
    (
        'endless-spells-hedonites-of-slaanesh',
        'HOS-015',
        'Endless Spells: Hedonites of Slaanesh',
        48.00,
        '99120299059_CITDoSHedonitesofSlaaneshEndlessSpells01.jpg',
        f'{_GW}Endless-Spells-Hedonites-of-Slaanesh-2019',
        'Endless Spells Hedonites of Slaanesh',
    ),
]


class Command(BaseCommand):
    """Populate Hedonites of Slaanesh products (HOS-001 to HOS-016)."""

    help = (
        'Creates / updates 15 Hedonites of Slaanesh products and seeds GW prices at MSRP. '
        'Creates Hedonites of Slaanesh faction if not present. Idempotent.'
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

        hos_faction, faction_created = Faction.objects.get_or_create(
            slug='hedonites-of-slaanesh',
            defaults={'name': 'Hedonites of Slaanesh', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Hedonites of Slaanesh faction.')

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
                    'faction': hos_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'hedonites-of-slaanesh',
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
            f'populate_hedonites_of_slaanesh_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
