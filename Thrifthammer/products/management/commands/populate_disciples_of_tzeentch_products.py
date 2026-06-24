"""
Management command: populate_disciples_of_tzeentch_products

Creates / updates all Disciples of Tzeentch product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Disciples of Tzeentch
faction if it does not already exist.

Covers 12 net-new products (DOT-001 to DOT-012) from the
AOS Disciples of Tzeentch - GW, NK, MM.xlsx (2026-06-24).

Category: Age of Sigmar
Faction:  Disciples of Tzeentch (created here via get_or_create)

Dual-kit products (same physical box, multiple build options):
  - DOT-005 Magister / DOT-008 Magister on Disc of Tzeentch
    share one NK listing (older model and newer 2026 mounted model
    appear to be the same NK listing entry).

No NK entries for: DOT-003, DOT-004.
No MM entries for: DOT-001, DOT-003, DOT-004, DOT-005, DOT-006,
DOT-007, DOT-008, DOT-011.

Dual-tagged products (NOT created here; add_disciples_of_tzeentch_secondary_faction tags them):
  CD-010  Changecaster
  CD-015  The Changeling
  CD-016  Burning Chariot of Tzeentch
  CD-017  Exalted Flamer of Tzeentch
  CD-018  Fateskimmer, Herald of Tzeentch on Burning Chariot
  P-TZEENTCH-SCREAMERS    Screamers of Tzeentch
  P-TZEENTCH-FLAMERS      Flamers of Tzeentch
  P-TZEENTCH-BLUEHORRORS  Blue Horrors and Brimstone Horrors
  P-TZEENTCH-KAIROS       Kairos Fateweaver
  P-TZEENTCH-LOC          Lord of Change
  S2D-009                 Gaunt Summoner (Slaves to Darkness)
  99120201050             Chaos Spawn

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_disciples_of_tzeentch_products
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

    # -- Warcry ----------------------------------------------------------------
    (
        'warcry-the-jade-obelisk',
        'DOT-001',
        'Warcry: The Jade Obelisk',
        65.00,
        '60010299038_WCSunderedFateJadeObeliskLead.jpg',
        f'{_GW}warcry-the-jade-obelisk-2023',
        'Warcry The Jade Obelisk',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'curseling-eye-of-tzeentch',
        'DOT-002',
        'Curseling, Eye of Tzeentch',
        39.00,
        '60010299033_EAoSArcaneCataclysmSingle02.jpg',
        f'{_GW}tzeentch-curseling-eye-of-tzeentch-2022',
        'Curseling, Eye of Tzeentch Disciples of Tzeentch',
    ),
    (
        'tzaangor-shaman',
        'DOT-004',
        'Tzaangor Shaman',
        39.00,
        '99070201021_TzaangorShamen01.jpg',
        f'{_GW}Tzaangor-Shaman',
        'Tzaangor Shaman Disciples of Tzeentch',
    ),
    # ⚠ Dual kit: Magister (old model) and Magister on Disc of Tzeentch (2026)
    #   share one NK listing.
    (
        'magister',
        'DOT-005',
        'Magister',
        20.00,
        '99070201019_TzeentchMagister01.jpg',
        f'{_GW}Tzeentch-Arcanites-Magister',
        'Magister on Disc of Tzeentch Disciples of Tzeentch',
    ),
    (
        'magister-on-disc-of-tzeentch',
        'DOT-008',
        'Magister on Disc of Tzeentch',
        40.00,
        '99120201216_DisciplesofTzeentchMagisteronDiscofTzeentch1.jpg',
        f'{_GW}disciples-of-tzeentch-magister-on-disc-of-tzeentch-2026',
        'Magister on Disc of Tzeentch Disciples of Tzeentch',
    ),
    (
        'ogroid-thaumaturge',
        'DOT-007',
        'Ogroid Thaumaturge',
        48.00,
        '99120201062_OgroidThaumaturge01.jpg',
        f'{_GW}Ogrid-Thaumaturge',
        'Ogroid Thaumaturge Disciples of Tzeentch',
    ),
    (
        'fatemaster',
        'DOT-009',
        'Fatemaster',
        40.00,
        '99120201214_DisciplesofTzeentchFatemasterALT.jpg',
        f'{_GW}disciples-of-tzeentch-fatemaster-2026',
        'Fatemaster Disciples of Tzeentch',
    ),

    # -- Units -----------------------------------------------------------------
    (
        'tzaangor-enlightened',
        'DOT-003',
        'Tzaangor Enlightened',
        60.00,
        '99120201064_TzaangorEnlightened01.jpg',
        f'{_GW}Tzaangor-Enlightened',
        'Tzaangor Enlightened Disciples of Tzeentch',
    ),
    (
        'kairic-acolytes',
        'DOT-006',
        'Kairic Acolytes',
        60.00,
        '99120201063_KairicAcolytes01.jpg',
        f'{_GW}Kairic-Acolytes',
        'Kairic Acolytes Disciples of Tzeentch',
    ),

    # -- Endless Spells / Terrain ----------------------------------------------
    (
        'endless-spells-disciples-of-tzeentch',
        'DOT-011',
        'Endless Spells: Disciples of Tzeentch',
        53.00,
        '99120201112_DoTSpells01.jpg',
        f'{_GW}Endless-Spells-Disciples-Of-Tzeentch-2020',
        'Endless Spells: Disciples of Tzeentch',
    ),
    (
        'argent-shards',
        'DOT-012',
        'Argent Shards',
        65.00,
        '99120201236_DisciplesOfTzeentchArgentShards01.jpg',
        f'{_GW}disciples-of-tzeentch-argent-shards-2026',
        'Argent Shards Disciples of Tzeentch',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'chaos-battletome-disciples-of-tzeentch',
        'DOT-010',
        'Chaos Battletome: Disciples of Tzeentch',
        60.00,
        '60030201033_ENGDoTHBBattletome1.jpg',
        f'{_GW}battletome-disciples-of-tzeentch-2026-eng',
        'Chaos Battletome: Disciples of Tzeentch',
    ),
]


class Command(BaseCommand):
    """Populate Disciples of Tzeentch products (DOT-001 to DOT-012)."""

    help = (
        'Creates / updates 12 Disciples of Tzeentch products and seeds GW prices at MSRP. '
        'Creates Disciples of Tzeentch faction if not present. Idempotent.'
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

        dot_faction, faction_created = Faction.objects.get_or_create(
            slug='disciples-of-tzeentch',
            defaults={'name': 'Disciples of Tzeentch', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Disciples of Tzeentch faction.')

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
                    'faction': dot_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'disciples-of-tzeentch',
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
            f'populate_disciples_of_tzeentch_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
