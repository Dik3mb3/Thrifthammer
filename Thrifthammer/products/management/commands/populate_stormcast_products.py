"""
Management command: populate_stormcast_products

Creates / updates all Stormcast Eternals product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates UnitType entries so
Stormcast Eternals appears in the Army Cost Calculator.

Covers all 46 products from the AOS Stormcasts spreadsheet (2026-05-13).

Category: Age of Sigmar
Faction:  Stormcast Eternals

Dual-kit products (share retailer URLs — same physical box):
  - Karazai the Scarred / Krondys, Son of Dracothion         (SE-007 / SE-008)
  - Annihilators / Annihilators with Meteoric Grandhammers   (SE-004 / SE-009)
  - Drakesworn Templar / Lord-Celestant on Stardrake          (SE-021 / SE-022)
  - Knight-Draconis / Stormdrake Guard                        (SE-037 / SE-038)
  - Vanguard-Raptors Longstrike / Hurricane                   (SE-040 / SE-043)
  - Tempestors / Lord-Celestant on Dracoth / Desolators /
    Concussors / Fulminators  (SE-041 / SE-042 / SE-044 / SE-045 / SE-046)

Images are baked in as one-off GW CDN URLs — never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_stormcast_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-13.
# ebay_search_name is blank unless the default name gives poor eBay results.
PRODUCTS = [

    # ── Battletome / General ─────────────────────────────────────────────────
    (
        'stormcast-eternals-battletome',
        'SE-001',
        'Order Battletome: Stormcast Eternals',
        60.00,
        '60030218008_EngSCEBattletome01.jpg',
        'https://www.warhammer.com/en-US/shop/battletome-stormcast-eternals-hb-2024-eng',
        '',
    ),
    (
        'age-of-sigmar-introductory-set',
        'SE-002',
        'Warhammer Age of Sigmar: Introductory Set',
        69.00,
        '13010299050_ENGUSCANKRAgeOfSigmarIntroductorySet01.jpg',
        'https://www.warhammer.com/en-US/shop/age-of-sigmar-introductory-set-2026-us-can-kr-eng',
        '',
    ),
    (
        'age-of-sigmar-starter-set',
        'SE-003',
        'Warhammer Age of Sigmar: Starter Set',
        114.00,
        '60010299045_ENGAoSStarterSet1.jpg',
        'https://www.warhammer.com/en-US/shop/age-of-sigmar-starter-set-2024-eng',
        '',
    ),

    # ── Units ────────────────────────────────────────────────────────────────
    (
        'stormcast-eternals-annihilators',
        'SE-004',
        'Stormcast Eternals Annihilators',
        60.00,
        '99120218058_SCEAnnihilatorsLeadALT.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-annihilators-2021',
        '',
    ),
    (
        'stormcast-eternals-vanguard-hunters',
        'SE-005',
        'Stormcast Eternals Vanguard-Hunters',
        69.00,
        '99120218021_VanguardHunters01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Vanguard-Hunters-2017',
        '',
    ),
    (
        'stormcast-eternals-stormcoven',
        'SE-006',
        'Stormcast Eternals Stormcoven',
        43.50,
        '99120218100_Stormcoven1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-stormcoven-2024',
        '',
    ),
    # ⚠ Dual kit: Karazai the Scarred / Krondys share the same box
    (
        'stormcast-eternals-karazai-the-scarred',
        'SE-007',
        'Stormcast Eternals Karazai the Scarred',
        175.00,
        '99120218054_SCEKrondysSonofDracothionKarazaitheScarredLeadALT.jpg',
        'https://www.warhammer.com/en-US/shop/karazai-the-scarred-2021',
        '',
    ),
    (
        'stormcast-eternals-krondys-son-of-dracothion',
        'SE-008',
        'Stormcast Eternals Krondys, Son of Dracothion',
        175.00,
        '99120218054_SCEKrondysSonofDracothionKarazaitheScarredLead.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-krondys-son-of-dracothian-2021',
        '',
    ),
    # ⚠ Dual kit: Annihilators variants share the same box
    (
        'stormcast-eternals-annihilators-with-meteoric-grandhammers',
        'SE-009',
        'Stormcast Eternals Annihilators with Meteoric Grandhammers',
        60.00,
        '99120218058_SCEAnnihilatorsLead.jpg',
        'https://www.warhammer.com/en-US/shop/annihilators-with-meteoric-grandhammers-2021',
        '',
    ),
    (
        'stormcast-eternals-vanquishers',
        'SE-010',
        'Stormcast Eternals Vanquishers',
        69.00,
        '99120218055_SCEVanquishersLead.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-vanquishers-2021',
        '',
    ),
    (
        'stormcast-eternals-vigilors',
        'SE-011',
        'Stormcast Eternals Vigilors',
        69.00,
        '99120218053_SCEVigilorsLead.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-vigilors-2021',
        '',
    ),
    (
        'stormcast-eternals-lord-commander-bastian-carthalos',
        'SE-012',
        'Stormcast Eternals Lord-Commander Bastian Carthalos',
        48.00,
        '99120218052_SCELordCommanderBastianCarthalosLead.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-lord-commander-bastian-carthalos-2021',
        '',
    ),
    (
        'stormcast-eternals-stormstrike-chariot',
        'SE-013',
        'Stormcast Eternals Stormstrike Chariot',
        60.00,
        '99120218051_StormstrikeChariotLead.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-stormstrike-chariot-2021',
        '',
    ),
    (
        'stormcast-eternals-gardus-steel-soul',
        'SE-014',
        'Stormcast Eternals Gardus Steel Soul',
        43.50,
        '99120218048_StormcastEternalsGardusSteelSoulLead.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Gardus-Steel-Soul-2021',
        '',
    ),
    (
        'stormcast-eternals-endless-spells',
        'SE-015',
        'Stormcast Eternals Endless Spells: Stormcast Eternals',
        48.00,
        '99120218032_StormcastBattleMagic01.jpg',
        'https://www.warhammer.com/en-US/shop/Battlemagic-Stormcast-2018',
        '',
    ),
    (
        'stormcast-eternals-vandus-hammerhand',
        'SE-016',
        'Stormcast Eternals Vandus Hammerhand',
        48.00,
        '99120218024_VandusHammerhand01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Vandus-Hammerhand',
        '',
    ),
    (
        'stormcast-eternals-vanguard-palladors',
        'SE-017',
        'Stormcast Eternals Vanguard-Palladors',
        65.00,
        '99120218022_PalladorsVanguard01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Vanguard-Palladors-2017',
        '',
    ),
    (
        'stormcast-eternals-lord-aquilor',
        'SE-018',
        'Stormcast Eternals Lord-Aquilor',
        48.00,
        '99120218020_LordAquillar02.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Lord-Aquilor-2017',
        '',
    ),
    (
        'stormcast-eternals-gryph-hounds',
        'SE-019',
        'Stormcast Eternals Gryph-hounds',
        35.00,
        '99120218019_GryphHounds01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Gryph-hounds-2017',
        '',
    ),
    (
        'stormcast-eternals-knight-questor',
        'SE-020',
        'Stormcast Eternals Knight-Questor',
        35.00,
        '99070218011_KnightQuestor01.jpg',
        'https://www.warhammer.com/en-US/shop/knight-questor',
        '',
    ),
    # ⚠ Dual kit: Drakesworn Templar / Lord-Celestant on Stardrake share same box
    (
        'stormcast-eternals-drakesworn-templar',
        'SE-021',
        'Stormcast Eternals Drakesworn Templar',
        191.00,
        '99020218024_DrakeswornTemple02.jpg',
        'https://www.warhammer.com/en-US/shop/Drakesworn-Templar',
        'Lord-Celestant on Stardrake',
    ),
    (
        'stormcast-eternals-lord-celestant-on-stardrake',
        'SE-022',
        'Stormcast Eternals Lord-Celestant on Stardrake',
        191.00,
        '99120218008_StormcastStardrake01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Stardrake',
        '',
    ),
    (
        'stormcast-eternals-celestant-prime',
        'SE-023',
        'Stormcast Eternals Celestant-Prime, Hammer of Sigmar',
        96.00,
        '99120218001_CelestantPrime01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Celestant-Prime',
        '',
    ),
    (
        'stormcast-eternals-questor-soulsworn',
        'SE-024',
        'Stormcast Eternals Questor Soulsworn',
        58.00,
        '60010299040_ENGWCNMQuest3.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-questor-soulsworn-2025',
        '',
    ),
    (
        'stormcast-eternals-stormreach-portal',
        'SE-025',
        'Stormcast Eternals Stormreach Portal',
        85.00,
        '99120218096_StormreachPortal1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-stormreach-portal-2024',
        '',
    ),
    (
        'stormcast-eternals-lord-imperatant',
        'SE-026',
        'Stormcast Eternals Lord-Imperatant',
        43.50,
        '99120218094_LordImperatant1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-lord-imperatant-2024',
        '',
    ),
    (
        'stormcast-eternals-knight-arcanum',
        'SE-027',
        'Stormcast Eternals Knight-Arcanum',
        40.00,
        '99120218093_SCEKnightArcanum1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-knight-arcanum-2024',
        '',
    ),
    (
        'stormcast-eternals-prosecutors',
        'SE-028',
        'Stormcast Eternals Prosecutors',
        60.00,
        '99120218092_Prosecuters1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-prosecutors-2024',
        '',
    ),
    (
        'stormcast-eternals-iridan-the-witness',
        'SE-029',
        'Stormcast Eternals Iridan the Witness',
        122.00,
        '99120218089_IridanWitness1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-iridan-the-witness-2024',
        '',
    ),
    (
        'stormcast-eternals-reclusians',
        'SE-030',
        'Stormcast Eternals Reclusians',
        64.00,
        '99120218088_Reclusians1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-reclusians-2024',
        '',
    ),
    (
        'stormcast-eternals-lord-terminos',
        'SE-031',
        'Stormcast Eternals Lord-Terminos',
        43.50,
        '99120218087_LordTerminos1New.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-lord-terminos-2024',
        '',
    ),
    (
        'stormcast-eternals-lord-relictor',
        'SE-032',
        'Stormcast Eternals Lord-Relictor',
        43.50,
        '99120218085_LordRelictor1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-lord-relictor-2024',
        '',
    ),
    (
        'stormcast-eternals-tornus-the-redeemed',
        'SE-033',
        'Stormcast Eternals Tornus the Redeemed',
        53.00,
        '99120218095_SCETornusRedeemed1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-tornus-the-redeemed-2024',
        '',
    ),
    (
        'stormcast-eternals-stormstrike-palladors',
        'SE-034',
        'Stormcast Eternals Stormstrike Palladors',
        69.00,
        '99120218086_StormstrikePalladors1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-stormstrike-palladors-2024',
        '',
    ),
    (
        'stormcast-eternals-ionus-cryptborn',
        'SE-035',
        'Stormcast Eternals Ionus Cryptborn, Warden of Lost Souls',
        145.00,
        '99120218082_IonusCryptborn1.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-ionus-cryptborn-2024',
        '',
    ),
    (
        'stormcast-eternals-the-blacktalons',
        'SE-036',
        'Stormcast Eternals The Blacktalons',
        82.00,
        '99120218080_SCETheBlacktalons01.jpg',
        'https://www.warhammer.com/en-US/shop/the-blacktalons-2023',
        '',
    ),
    # ⚠ Dual kit: Knight-Draconis / Stormdrake Guard share same box
    (
        'stormcast-eternals-knight-draconis',
        'SE-037',
        'Stormcast Eternals Knight-Draconis',
        130.00,
        '99120218056_SCEStormdrakeGuardKnightDraconisLeadAltFlightcheck.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-knight-draconis-2021',
        '',
    ),
    (
        'stormcast-eternals-stormdrake-guard',
        'SE-038',
        'Stormcast Eternals Stormdrake Guard',
        130.00,
        '99120218056_SCEStormdrakeGuardKnightDraconisLead.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-stormdrake-guard-2021',
        '',
    ),
    (
        'stormcast-eternals-knight-relictor',
        'SE-039',
        'Stormcast Eternals Knight-Relictor',
        39.00,
        '99070218057_SCEKnightRelictorLead.jpg',
        'https://www.warhammer.com/en-US/shop/stormcast-eternals-knight-relictor-2021',
        '',
    ),
    # ⚠ Dual kit: Vanguard-Raptors variants share same box
    (
        'stormcast-eternals-vanguard-raptors-longstrike',
        'SE-040',
        'Stormcast Eternals Vanguard-Raptors With Longstrike Crossbows & Aetherwings',
        48.00,
        '99120218023_StormcastLongstrikeRaptors01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Vanguard-Raptors-2017',
        'Stormcast Eternals Vanguard-Raptors',
    ),
    # ⚠ Quad kit: Dracothian Guard — Tempestors / Lord-Celestant on Dracoth /
    #   Desolators / Concussors / Fulminators all from same box
    (
        'stormcast-eternals-tempestors',
        'SE-041',
        'Stormcast Eternals Tempestors',
        82.00,
        '99120218074_TempestorsvolleystormcrossbowsUpdate1.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Tempestors',
        'Stormcast Eternals Dracothian Guard',
    ),
    (
        'stormcast-eternals-lord-celestant-on-dracoth',
        'SE-042',
        'Stormcast Eternals Lord-Celestant on Dracoth',
        82.00,
        '99120218074_DracothianGuardMountedCelestantUpdate1.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Lord-Celestant-on-Dracoth',
        'Stormcast Eternals Dracothian Guard',
    ),
    (
        'stormcast-eternals-vanguard-raptors-hurricane',
        'SE-043',
        'Stormcast Eternals Vanguard-Raptors With Hurricane Crossbows & Aetherwings',
        48.00,
        '99120218023_StormcastHurricaneRaptors01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Vanguard-Raptors-with-Hurricaine-Crossbows-2017',
        'Stormcast Eternals Vanguard-Raptors',
    ),
    (
        'stormcast-eternals-desolators',
        'SE-044',
        'Stormcast Eternals Desolators',
        82.00,
        '99120218074_DesolatorsThunderaxesUpdate1.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Desolators',
        'Stormcast Eternals Dracothian Guard',
    ),
    (
        'stormcast-eternals-concussors',
        'SE-045',
        'Stormcast Eternals Concussors',
        82.00,
        '99120218009_StormcastDracothianCastelant02.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Concussors',
        'Stormcast Eternals Dracothian Guard',
    ),
    (
        'stormcast-eternals-fulminators',
        'SE-046',
        'Stormcast Eternals Fulminators',
        82.00,
        '99120218009_Fulminators01.jpg',
        'https://www.warhammer.com/en-US/shop/Stormcast-Eternals-Dracothian-Guard',
        'Stormcast Eternals Dracothian Guard',
    ),
]


class Command(BaseCommand):
    """Populate Stormcast Eternals products (SE-001 to SE-046)."""

    help = (
        'Creates / updates 46 Stormcast Eternals products and seeds GW prices at MSRP. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_aos = Category.objects.get(slug='age-of-sigmar')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Age of Sigmar category not found — run populate_products first.'
            ))
            return

        try:
            sce_faction = Faction.objects.get(slug='stormcast-eternals')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Stormcast Eternals faction not found — run populate_products first.'
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
                    'category': category_aos,
                    'faction': sce_faction,
                    'is_active': True,
                    'batch_tag': 'stormcast-eternals',
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
            f'\npopulate_stormcast_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
