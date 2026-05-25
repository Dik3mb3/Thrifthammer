"""
Management command: populate_admech_products

Creates / updates all Adeptus Mechanicus product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 25 products from the Admech - GW,NK,MM, AMAZON.xlsx spreadsheet (2026-05-19).

Category: Warhammer 40,000
Faction:  Adeptus Mechanicus

Dual-kit / shared-listing products (same physical box):
  - Archaeopter Fusilave / Stratoraptor / Transvector  (MC-001 / MC-002 / MC-003)
    share one Amazon ASIN, one MM URL, one NK listing
  - Pteraxii Skystalkers / Sterylizors               (MC-010 / MC-011)
  - Serberys Raiders / Sulphurhounds                 (MC-012 / MC-013)
  - Sicarian Infiltrators / Ruststalkers             (MC-014 / MC-015)
  - Skorpius Disintegrator / Dunerider               (MC-017 / MC-018)

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_admech_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-19.
# ebay_search_name is blank unless the default name gives poor eBay results.
PRODUCTS = [

    # ── Archaeopter (triple kit: Fusilave / Stratoraptor / Transvector) ──────
    (
        'adeptus-mechanicus-archaeopter-fusilave',
        'MC-001',
        'Adeptus Mechanicus Archaeopter Fusilave',
        122.00,
        '99120116024_AMFusilaveLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Archaeopter-Fusilave-2020',
        '',
    ),
    (
        'adeptus-mechanicus-archaeopter-stratoraptor',
        'MC-002',
        'Adeptus Mechanicus Archaeopter Stratoraptor',
        122.00,
        '99120116024_AMStratoraptorLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Archaeopter-Stratoraptor-2020',
        '',
    ),
    (
        'adeptus-mechanicus-archaeopter-transvector',
        'MC-003',
        'Adeptus Mechanicus Archaeopter Transvector',
        122.00,
        '99120116024_AMTransvectorLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Archaeopter-2020',
        '',
    ),

    # ── Kill Team ─────────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-battleclade',
        'MC-004',
        'Kill Team: Battleclade',
        73.50,
        '99120116048_ENGKillTeamTyphonCoreGame2.jpg',
        'https://www.warhammer.com/en-US/shop/kill-team-battleclade-2025',
        'Kill Team Battleclade',
    ),

    # ── Named characters ──────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-belisarius-cawl',
        'MC-005',
        'Adeptus Mechanicus Belisarius Cawl',
        65.00,
        '99120108008_TriumvirateoftheImperium02.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Belisarius-Cawl-2017',
        '',
    ),
    (
        'adeptus-mechanicus-thulia-ghuld',
        'MC-024',
        'Adeptus Mechanicus Thulia Ghuld',
        65.00,
        '99120116050_ThuliaGhuld1.jpg',
        'https://www.warhammer.com/en-US/shop/adeptus-mechanicus-thulia-ghuld-2026',
        '',
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-fulgurite-electro-priests',
        'MC-006',
        'Adeptus Mechanicus Fulgurite Electro-Priests',
        60.00,
        '99120116009_AdMechFulguriteElectroPriests01.jpg',
        'https://www.warhammer.com/en-US/shop/Ad-Mec-Fulgurite-Electro-Priests',
        'Adeptus Mechanicus Electro-Priests',
    ),
    (
        'adeptus-mechanicus-hastarii',
        'MC-007',
        'Adeptus Mechanicus Hastarii',
        60.00,
        '99120116051_HastariiALT.jpg',
        'https://www.warhammer.com/en-US/shop/adeptus-mechanicus-hastarii-2026',
        '',
    ),
    (
        'adeptus-mechanicus-pteraxii-skystalkers',
        'MC-010',
        'Adeptus Mechanicus Pteraxii Skystalkers',
        65.00,
        '99120116025_PteraxiiLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Pteraxii-2020',
        '',
    ),
    (
        'adeptus-mechanicus-pteraxii-sterylizors',
        'MC-011',
        'Adeptus Mechanicus Pteraxii Sterylizors',
        65.00,
        '99120116025_SterylizorsLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Pteraxii-Sterylizors-2020',
        '',
    ),
    (
        'adeptus-mechanicus-serberys-raiders',
        'MC-012',
        'Adeptus Mechanicus Serberys Raiders',
        65.00,
        '99120116026_AMSerberysRaidersLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Serberys-Raiders-2020',
        '',
    ),
    (
        'adeptus-mechanicus-serberys-sulphurhounds',
        'MC-013',
        'Adeptus Mechanicus Serberys Sulphurhounds',
        65.00,
        '99120116026_AMSerberysSulphurhoundsLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Serberys-Sulphurhounds--2020',
        '',
    ),
    (
        'adeptus-mechanicus-sicarian-infiltrators',
        'MC-014',
        'Adeptus Mechanicus Sicarian Infiltrators',
        60.00,
        '99120116003_SicarianInfiltrators01.jpg',
        'https://www.warhammer.com/en-US/shop/Sicarian-Infiltrators-2017',
        '',
    ),
    (
        'adeptus-mechanicus-sicarian-ruststalkers',
        'MC-015',
        'Adeptus Mechanicus Sicarian Ruststalkers',
        60.00,
        '99120116003_SicarianRuststalkers01.jpg',
        'https://www.warhammer.com/en-US/shop/Sicarians-2017',
        '',
    ),

    # ── Vehicles / Walkers ────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-kastelan-robots',
        'MC-008',
        'Adeptus Mechanicus Kastelan Robots',
        85.00,
        '99120116005_AdMechKastelanRobots01.jpg',
        'https://www.warhammer.com/en-US/shop/Kastelan-Robots-2017',
        '',
    ),
    (
        'adeptus-mechanicus-kataphron-breachers',
        'MC-009',
        'Adeptus Mechanicus Kataphron Breachers',
        65.00,
        '99120116006_AdMechBattleServitorsBreachers01.jpg',
        'https://www.warhammer.com/en-US/shop/Kataphron-Battle-Servitors-Breachers-2017',
        '',
    ),
    (
        'adeptus-mechanicus-skorpius-disintegrator',
        'MC-017',
        'Adeptus Mechanicus Skorpius Disintegrator',
        84.00,
        '99120116023_SkorpiusDistintegrator01.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Skorpius-Disintegrator-2019',
        '',
    ),
    (
        'adeptus-mechanicus-skorpius-dunerider',
        'MC-018',
        'Adeptus Mechanicus Skorpius Dunerider',
        84.00,
        '99120116023_SkorpiusDistintegrator02.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Skorpius-Dunerider-2019',
        '',
    ),
    (
        'adeptus-mechanicus-sydonian-dragoon',
        'MC-019',
        'Adeptus Mechanicus Sydonian Dragoon',
        65.00,
        '99120116001_SydonianDragoon01.jpg',
        'https://www.warhammer.com/en-US/shop/Sydonian-Dragoon-2017',
        '',
    ),

    # ── Leaders / HQ ─────────────────────────────────────────────────────────
    (
        'adeptus-mechanicus-skitarii-marshal',
        'MC-016',
        'Adeptus Mechanicus Skitarii Marshal',
        35.00,
        '99070116003_AMSkitariiMarshalLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Skitarii-Marshall-2021',
        '',
    ),
    (
        'adeptus-mechanicus-sydonian-skatros',
        'MC-020',
        'Adeptus Mechanicus Sydonian Skatros',
        42.00,
        '99120116045_ADMECHSydonianSkatros01.jpg',
        'https://www.warhammer.com/en-US/shop/adeptus-mechanicus-sydonian-skatros-2023',
        '',
    ),
    (
        'adeptus-mechanicus-technoarcheologist',
        'MC-021',
        'Adeptus Mechanicus Technoarcheologist',
        35.00,
        '99070116007_AMTechnoarchaeologist01.jpg',
        'https://www.warhammer.com/en-US/shop/adeptus-mechanicus-technoarchaeologist-2022',
        '',
    ),
    (
        'adeptus-mechanicus-tech-priest-enginseer',
        'MC-022',
        'Adeptus Mechanicus Tech-Priest Enginseer',
        39.00,
        '99070105002_TechpriestEnginseer01.jpg',
        'https://www.warhammer.com/en-US/shop/Astra-Militarum-Tech-Priest-Enginseer',
        '',
    ),
    (
        'adeptus-mechanicus-tech-priest-manipulus',
        'MC-023',
        'Adeptus Mechanicus Tech-Priest Manipulus',
        43.50,
        '99070116002_TechPriestManipulusLead.jpg',
        'https://www.warhammer.com/en-US/shop/Adeptus-Mechanicus-Tech-priest-Manipulus-2020',
        '',
    ),

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-adeptus-mechanicus',
        'MC-025',
        'Codex: Adeptus Mechanicus',
        60.00,
        '60030116008_ENGADMECHCodex01.jpg',
        'https://www.warhammer.com/en-US/shop/codex-adeptus-mechanicus-hb-eng-2023',
        'Codex Adeptus Mechanicus',
    ),
]


class Command(BaseCommand):
    """Populate Adeptus Mechanicus products (MC-001 to MC-025)."""

    help = (
        'Creates / updates 25 Adeptus Mechanicus products and seeds GW prices at MSRP. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_40k = Category.objects.get(slug='warhammer-40000')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        try:
            admech_faction = Faction.objects.get(slug='adeptus-mechanicus')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Adeptus Mechanicus faction not found — run populate_products first.'
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
                    'category': category_40k,
                    'faction': admech_faction,
                    'is_active': True,
                    'batch_tag': 'adeptus-mechanicus',
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
            f'\npopulate_admech_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
