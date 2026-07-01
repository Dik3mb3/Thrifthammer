"""
Management command: populate_cult_mechanicum_products

Creates / updates all Cult Mechanicum product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Category: Horus Heresy (already exists in DB)
Faction:  Cult Mechanicum (created if not present)

Dual-kit notes:
  Age of Darkness Armiger Helverins / Age of Darkness Armiger Warglaives share GW catalog 99123008002.

Excludes 2 products (Cerastus Knight Acheron / Castigator) that are the
same physical kits as existing Imperial Knights catalog entries (31-67,
31-66). Those are cross-tagged via secondary_factions instead of
duplicated. See add_cult_mechanicum_secondary_faction.py.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_cult_mechanicum_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
PRODUCTS = [
    (
        'mechanicum-combat-force',
        'CM-001',
        'Mechanicum: Combat Force',
        170.00,
        '99123016015_HorusHeresyMechanicumCombatForceArmy1.jpg',
        'https://www.warhammer.com/en-US/shop/horus-heresy-mechanicum-combat-force-2025',
        'Mechanicum: Combat Force Horus Heresy',
    ),
    (
        'skitarii-battle-pilgrym-marshal',
        'CM-002',
        'Skitarii Battle-Pilgrym Marshal',
        40.00,
        '99123016011_MechanicumSkitariiBattlePilgrymMarshal1.jpg',
        'https://www.warhammer.com/en-US/shop/skitarii-battle-pilgrym-marshal-2026',
        'Skitarii Battle-Pilgrym Marshal Horus Heresy',
    ),
    (
        'vultarax-stratos-automata',
        'CM-003',
        'Vultarax Stratos-Automata',
        82.00,
        '99123016012_MechanicumVultaraxStratosAutomata1.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-vultarax-stratos-automata-2026',
        'Vultarax Stratos-Automata Horus Heresy',
    ),
    (
        'skitarii-battle-pilgrym-corpus',
        'CM-004',
        'Skitarii Battle-Pilgrym Corpus',
        90.00,
        '99123016010_MechanicumSkitariiBattlepilgrymCorpus1.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-skitarii-battle-pilgrym-corpus-2026',
        'Skitarii Battle-Pilgrym Corpus Horus Heresy',
    ),
    (
        'ursarax-cohort',
        'CM-005',
        'Ursarax Cohort',
        77.00,
        '99123016008_THHMechanicumUrsaraxCohort01.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-ursarax-cohort-2025',
        'Ursarax Cohort Horus Heresy',
    ),
    (
        'krios-battle-tank-venator',
        'CM-006',
        'Krios Battle Tank/Venator',
        80.00,
        '99123016009_THHMechanicumKriosBattletank01.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-krios-battle-tank-2025',
        'Krios Battle Tank/Venator Horus Heresy',
    ),
    (
        'karacnos-assault-tank',
        'CM-007',
        'Karacnos Assault Tank',
        112.00,
        '99123016014_THHMechanicumKaracnosAssaultTankVehicle01.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-karacnos-assault-tank-2025',
        'Karacnos Assault Tank Horus Heresy',
    ),
    (
        'thanatar-calix-siege-automata',
        'CM-008',
        'Thanatar Calix Siege-automata',
        106.00,
        '99123016018_THHMechanicumThanatarCalixSiegeAutomata01.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-thanatar-calix-siege-automata-2025',
        'Thanatar Calix Siege-automata Horus Heresy',
    ),
    (
        'archmagos-prime',
        'CM-009',
        'Archmagos Prime',
        40.00,
        '99123016004_ADMECHArchmagosPrime1.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-archmagos-prime-2024',
        'Archmagos Prime Horus Heresy',
    ),
    (
        'thallax-cohort',
        'CM-010',
        'Thallax Cohort',
        82.00,
        '99123016002_ADMECHThallaxCohort1.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-thallax-cohort-2024',
        'Thallax Cohort Horus Heresy',
    ),
    (
        'triaros-armoured-conveyor',
        'CM-011',
        'Triaros Armoured Conveyor',
        96.00,
        '99123016006_TriarosArmouredConveyor1.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-triaros-armoured-conveyor-2024',
        'Triaros Armoured Conveyor Horus Heresy',
    ),
    (
        'tech-thralls-covenant',
        'CM-012',
        'Tech-thralls Covenant',
        82.00,
        '99123016005_ADMECHTechThrallsCovenant01.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-tech-thralls-covenant-2024',
        'Tech-thralls Covenant Horus Heresy',
    ),
    (
        'castellax-battle-automata-maniple',
        'CM-013',
        'Castellax Battle-automata Maniple',
        82.00,
        '99123016003_ADMECHCastellaxBattleAutomataManiple1.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-castellax-battle-automata-maniple-2024',
        'Castellax Battle-automata Maniple Horus Heresy',
    ),
    (
        # ⚠ Dual kit: shares GW catalog 99123008002 with 'Age of Darkness Armiger Warglaives'
        'age-of-darkness-armiger-helverins',
        'CM-014',
        'Age of Darkness Armiger Helverins',
        100.00,
        '99123008002_HHArmigersLead02.jpg',
        'https://www.warhammer.com/en-US/shop/questoris-households-armiger-helverin-talon-2022',
        'Age of Darkness Armiger Helverins Horus Heresy',
    ),
    (
        # ⚠ Dual kit: shares GW catalog 99123008002 with 'Age of Darkness Armiger Helverins'
        'age-of-darkness-armiger-warglaives',
        'CM-015',
        'Age of Darkness Armiger Warglaives',
        100.00,
        '99123008002_HHArmigersLead01.jpg',
        'https://www.warhammer.com/en-US/shop/questoris-households-armiger-warglaive-talon-2022',
        'Age of Darkness Armiger Warglaives Horus Heresy',
    ),
    (
        'age-of-darkness-knight-questoris',
        'CM-016',
        'Age of Darkness Knight Questoris',
        190.00,
        '99123008001_HHKnightQuestorisLead.jpg',
        'https://www.warhammer.com/en-US/shop/questoris-households-knight-questoris-2022',
        'Age of Darkness Knight Questoris Horus Heresy',
    ),
    (
        'myrmidon-destructor-host',
        'CM-017',
        'Myrmidon Destructor Host',
        77.00,
        '99123016019_MechanicumMyrmidonDestructorHost1.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-myrmidon-destructor-host-2026',
        'Myrmidon Destructor Host Horus Heresy',
    ),
    (
        'thanatar-cavas-siege-automata',
        'CM-018',
        'Thanatar Cavas Siege-automata',
        106.00,
        '99123016007_ADMECHThanatarCavasSiegeAutomata1.jpg',
        'https://www.warhammer.com/en-US/shop/mechanicum-thanatar-cavas-siege-automata-2024',
        'Thanatar Cavas Siege-automata Horus Heresy',
    ),
]


class Command(BaseCommand):
    help = 'Creates / updates Cult Mechanicum products and seeds GW prices. Idempotent.'

    def handle(self, *args, **options):
        hh_category, _ = Category.objects.get_or_create(
            slug='horus-heresy',
            defaults={'name': 'Horus Heresy'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='cult-mechanicum',
            defaults={'name': 'Cult Mechanicum', 'category': hh_category},
        )
        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()

        created_count = updated_count = price_created = price_updated = 0

        for (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_name) in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': _IMG.format(filename=img_filename),
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_name,
                    'category': hh_category,
                    'faction': faction,
                    'is_active': True,
                    'batch_tag': 'cult-mechanicum',
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
            self.stdout.write(f'  {"Created" if created else "Updated"}: {name} ({gw_sku})')

            if gw_retailer and msrp is not None:
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
            f'\npopulate_cult_mechanicum_products complete. '
            f'Products: {created_count} created, {updated_count} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
