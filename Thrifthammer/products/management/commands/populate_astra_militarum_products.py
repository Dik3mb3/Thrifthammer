"""
Management command: populate_astra_militarum_products

Seeds 49 Astra Militarum products (AM-001 to AM-049) with GW, Amazon,
Miniature Market, and Noble Knight price rows.

Idempotent — safe to re-run.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

AMAZON_TAG = 'thrifthammer7-20'
NK_AWID = '1576'
_GW_CDN = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{}'

# Images verified directly from GW product pages via browser.
# fetch_gw_images (Algolia) returns wrong images for several AM products;
# these overrides ensure the correct image is used on first deploy.
_IMAGES = {
    'AM-001': '99120105108_AMAegisDefenceline01.jpg',
    'AM-002': '99120105124_AstraMilitarumCombatPatrol1.jpg',  # placeholder — product not on GW site yet
    'AM-003': '99120105126_AstraMilitarumKriegArtilleryTeam1.jpg',
    'AM-004': '99120105092_AMAttilanRoughRidersUpdate2.jpg',
    'AM-005': '99120105107_AMBanebladeLeadBaneblade.jpg',
    'AM-006': '99120105107_AMBanebladeLeadBanehammer.jpg',
    'AM-007': '99120105107_AMBanebladeLeadBanesword.jpg',
    'AM-008': '99120105117_AMBullgryns1.jpg',
    'AM-009': '99120105100_CadianCastellan1.jpg',
    'AM-010': '60010105001_EngAMCoreGame02.jpg',
    'AM-011': '99120105106_CadianUpgrades2.jpg',
    'AM-012': '99120105037_CatachanCommandSquadNEW01.jpg',
    'AM-013': '99120105014_CatachanHeavyWeaponsNEW01.jpg',
    'AM-014': '99120105040_AstraMilitarumCatachanJungleFightersUPDATE1.jpg',
    'AM-015': '60030105013_EngAMCodex01.jpg',
    'AM-016': '99120105140_AstraMilitarumCommissarGraves1.jpg',
    'AM-017': '99120105138_AstraMilitarumCommissarYarrick01.jpg',
    'AM-018': '99120105135_AstraMilitarumDeathKorpsKriegInfantrySquad1.jpg',
    'AM-019': '99120105128_AstraMilitarumKriegDeathRidersSquad1.jpg',
    'AM-020': '99120105049_DeathstrikeNEW02.jpg',
    'AM-021': '99120105107_AMBanebladeLeadDoomhammer.jpg',
    'AM-022': '99120105104_AMFieldOrdnanceBattery01.jpg',
    'AM-023': '99120105087_GauntsGhostsLead.jpg',
    'AM-024': '99120105097_AMCadianHeavyWeaponsSquad01.jpg',
    'AM-025': '99120105107_AMBanebladeLeadHellhammer.jpg',
    'AM-026': '99120105115_AMHydra1.jpg',
    'AM-027': '99120105129_AstraMilitarumKriegCombatEngineersSquad1.jpg',
    'AM-028': '99120105127_AstraMilitarumKriegCommandSquad1.jpg',
    'AM-029': '99120105130_AstraMilitarumKriegHeavyWeaponsSquad1.jpg',
    'AM-030': '99120105096_AMLordCastellanUrsulaCreed01.jpg',
    'AM-031': '99120105125_AstraMilitarumKriegLordMarshalDreir1.jpg',
    'AM-032': '99120105095_AMLordSolarLeontus01.jpg',
    'AM-033': '99120105049_ManticoreNEW01.jpg',
    'AM-034': '99120105055_TempestusScionsCommand01.jpg',
    'AM-035': '99070108011_ASMinistorumPriest01.jpg',
    'AM-036': '99120105077_AMBullgrynNorkDeddog01.jpg',
    'AM-037': '99120105117_AMBullgryns2.jpg',
    'AM-038': '99070105003_AMPrimarisPsyker01.jpg',
    'AM-039': '99120105098_AMRogalDornBattleTank01.jpg',
    'AM-040': '99120105107_AMBanebladeLeadShadowsword.jpg',
    'AM-041': '99810105030_SlyMarbo01.jpg',
    'AM-042': '99120105107_AMBanebladeLeadStormlord.jpg',
    'AM-043': '99120105107_AMBanebladeLeadStormsword.jpg',
    'AM-044': '99120105054_Taurox01.jpg',
    'AM-045': '99120105054_Taurox01.jpg',
    'AM-046': '99070105002_TechpriestEnginseer01.jpg',
    'AM-047': '99120105055_TempestusScions01.jpg',
    'AM-048': '99120105113_AMValkyreLEAD.jpg',
    'AM-049': '99120105115_AMHydra2.jpg',
}


def _amazon_url(asin):
    if not asin:
        return ''
    return f'https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}'


def _nk_url(base_url):
    if not base_url:
        return ''
    return f'{base_url}?awid={NK_AWID}'


_EBAY_NEGATIVE_KEYWORDS = {
    # AM-035 "Ministorum Priest" — eBay returns Adepta Sororitas / Blackstone
    # Fortress / Vourne listings that share keywords.  Excluding these terms
    # keeps results focused on the standalone Ministorum Priest blister.
    'AM-035': 'Taddeus Sister Blackstone Vourne Pious Zealot',
}

# (gw_sku, name, msrp, gw_url, amazon_asin, mm_url, nk_base_url)
PRODUCTS = [
    ('AM-001', 'Astra Militarum Aegis Defence Line', Decimal('85.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-aegis-defence-line-2023',
     'B0BVMJDL5Q',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-aegis-defence-line-gw-47-69.html',
     'https://www.nobleknight.com/P/2148037171/Aegis-Defence-Line'),

    ('AM-002', 'Armageddon Battalion: Astra Militarum', Decimal('255.00'),
     'https://www.warhammer.com/en-US/shop/armageddon-battalion-astra-militarum-2026',
     'B0GYG61JXZ', '', ''),

    ('AM-003', 'Astra Militarum Artillery Team', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-krieg-artillery-team-2025',
     'B0DVT8SMLN',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-artillery-team-gw-47-78.html',
     ''),

    ('AM-004', 'Astra Militarum Attilan Rough Riders', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-attilan-rough-riders-2023',
     '',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-attilan-rough-riders-gw-47-38.html',
     'https://www.nobleknight.com/P/2148037170/Attilan-Rough-Riders'),

    ('AM-005', 'Astra Militarum Baneblade', Decimal('197.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-baneblade-2023',
     'B0BSFR52RV',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-baneblade-gw-47-24-2023.html',
     'https://www.nobleknight.com/P/2148031750/Baneblade'),

    ('AM-006', 'Astra Militarum Banehammer', Decimal('197.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-banehammer-2023',
     'B0BSFR52RV',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-baneblade-gw-47-24-2023.html',
     'https://www.nobleknight.com/P/2148031750/Baneblade'),

    ('AM-007', 'Astra Militarum Banesword', Decimal('197.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-banesword-2023',
     'B0BSFR52RV',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-baneblade-gw-47-24-2023.html',
     'https://www.nobleknight.com/P/2148031750/Baneblade'),

    ('AM-008', 'Astra Militarum Bullgryns', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/Militarum-Auxilla-Bullgryns',
     'B07VGZVF6J',
     'https://www.miniaturemarket.com/gw-47-14.html',
     'https://www.nobleknight.com/P/2148067824/Bullgryns'),

    ('AM-009', 'Astra Militarum Cadian Castellan', Decimal('39.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-cadian-castellan-2023',
     'B0BVMFYDWD',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-cadian-castellan-gw-47-34.html',
     'https://www.nobleknight.com/P/2148037161/Cadian-Castellan'),

    ('AM-010', 'Astra Militarum Cadian Command Squad', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-cadian-command-squad-2023',
     'B0BSFPXPLX',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-cadian-command-squad-gw-47-09-2023.html',
     'https://www.nobleknight.com/P/2148031704/Cadian-Command-Squad'),

    ('AM-011', 'Astra Militarum Cadian Upgrades', Decimal('35.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-cadian-upgrades-2023',
     'B0BVMFCFZH',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-cadian-upgrades-gw-47-40.html',
     'https://www.nobleknight.com/P/2148037163/Cadian-Upgrades'),

    ('AM-012', 'Astra Militarum Catachan Command Squad', Decimal('39.00'),
     'https://www.warhammer.com/en-US/shop/Imperial-Guard-Catachan-Command-Squad',
     '', '', ''),

    ('AM-013', 'Astra Militarum Catachan Heavy Weapons Squad', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/Imperial-Guard-Catachan-Heavy-Weapon-Squad',
     '', '', ''),

    ('AM-014', 'Astra Militarum Catachan Jungle Fighters', Decimal('39.00'),
     'https://www.warhammer.com/en-US/shop/Imperial-Guard-Catachan-Jungle-Fighters',
     '', '', ''),

    ('AM-015', 'Codex: Astra Militarum', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/codex-astra-militarum-2025-eng',
     '1804574767',
     'https://www.miniaturemarket.com/warhammer-40k-codex-astra-militarum-gw-47-01-2025.html',
     'https://www.nobleknight.com/P/2148356827/Codex---Astra-Militarum-10th-Edition'),

    ('AM-016', 'Astra Militarum Commissar Graves', Decimal('102.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-commissar-graves-2026',
     '', '', ''),

    ('AM-017', 'Astra Militarum Commissar Yarrick', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-commissar-yarrick-2026',
     '', '', ''),

    ('AM-018', 'Astra Militarum Death Korps of Krieg', Decimal('53.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-death-korps-of-krieg-2025',
     'B0DVTB8V1Y',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-death-korps-krieg-gw-47-80.html',
     'https://www.nobleknight.com/P/2148318413/Death-Korps-of-Krieg'),

    ('AM-019', 'Astra Militarum Death Riders', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-death-riders-2025',
     'B0DVTBZH2T',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-death-riders-gw-47-74.html',
     'https://www.nobleknight.com/P/2148318413/Death-Korps-of-Krieg'),

    ('AM-020', 'Astra Militarum Deathstrike', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/Imperial-Guard-Deathstrike',
     'B003P12IZQ', '',
     'https://www.nobleknight.com/P/2148431611/Manticore-5'),

    ('AM-021', 'Astra Militarum Doomhammer', Decimal('197.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-doomhammer-2023',
     'B0BSFR52RV',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-baneblade-gw-47-24-2023.html',
     'https://www.nobleknight.com/P/2148031750/Baneblade'),

    ('AM-022', 'Astra Militarum Field Ordnance Battery', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-field-ordnance-battery-2023',
     'B0BSFP2RDS',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-field-ordnance-battery-gw-47-41.html',
     'https://www.nobleknight.com/P/2148031721/Field-Ordinance-Battery'),

    ('AM-023', "Astra Militarum Gaunt's Ghosts", Decimal('82.00'),
     'https://www.warhammer.com/en-US/shop/Astra-Militarum-Gaunts-Ghosts-2021',
     'B0973J7CLR',
     'https://www.miniaturemarket.com/gw-47-30.html',
     'https://www.nobleknight.com/P/2147895978/Gaunts-Ghosts-2021-Edition'),

    ('AM-024', 'Astra Militarum Cadian Heavy Weapons Squad', Decimal('53.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-cadian-heavy-weapons-squad-2023',
     'B0BSFQ6J6B',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-cadian-heavy-weapons-squad-gw-47-19-2023.html',
     ''),

    ('AM-025', 'Astra Militarum Hellhammer', Decimal('197.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-hellhammer-2023',
     'B0BSFR52RV',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-baneblade-gw-47-24-2023.html',
     'https://www.nobleknight.com/P/2148031750/Baneblade'),

    ('AM-026', 'Astra Militarum Hydra', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/Astra-Militarum-Hydra',
     'B0BSHF4G6G',
     'https://www.miniaturemarket.com/gw-47-21.html', ''),

    ('AM-027', 'Astra Militarum Krieg Combat Engineers', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-krieg-combat-engineers-2025',
     'B0DVT9575R',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-krieg-combat-engineers-gw-47-76.html',
     ''),

    ('AM-028', 'Astra Militarum Krieg Command Squad', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-krieg-command-squad-2025',
     'B0DVTBRYYX',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-krieg-comand-squad-gw-47-72.html',
     ''),

    ('AM-029', 'Astra Militarum Krieg Heavy Weapons Squad', Decimal('53.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-krieg-heavy-weapons-squad-2025',
     'B0DVT9Q8Y9', '', ''),

    ('AM-030', 'Astra Militarum Lord Castellan Ursula Creed', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-lord-castellan-ursula-creed-2023',
     'B0BSFQBMVB',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-lord-castellan-ursula-creed-gw-47-32.html',
     ''),

    ('AM-031', 'Astra Militarum Lord Marshal Dreir', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-krieg-lord-marshal-dreir-2025',
     'B0DVTB6CCQ',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-lord-marshal-dreir-gw-47-77.html',
     ''),

    ('AM-032', 'Astra Militarum Lord Solar Leontus', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-lord-solar-leontus-2023',
     'B0BSFQK8NT',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-lord-solar-leontus-gw-47-35.html',
     ''),

    ('AM-033', 'Astra Militarum Manticore', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/Astra-Militarum-Manticore',
     'B003P12IZQ', '',
     'https://www.nobleknight.com/P/2148431611/Manticore-5'),

    ('AM-034', 'Astra Militarum Militarum Tempestus Scions Command Squad', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/Militarum-Tempestus-Scions-Command-Squad-2017',
     'B0BSHFN9QS', '', ''),

    ('AM-035', 'Astra Militarum Ministorum Priest', Decimal('35.00'),
     'https://www.warhammer.com/en-US/shop/adepta-sororitas-ministorum-priest-2024',
     'B0DC6NVD8N',
     'https://www.miniaturemarket.com/warhammer-40k-adepta-sororitas-ministorum-priest-gw-57-51.html',
     ''),

    ('AM-036', 'Astra Militarum Nork Deddog', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/Militarum-Auxilla-Nork-Deddog',
     'B07VGZVF6J',
     'https://www.miniaturemarket.com/gw-47-14.html',
     'https://www.nobleknight.com/P/2148067824/Bullgryns'),

    ('AM-037', 'Astra Militarum Ogryns', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/Militarum-Auxilla-Ogryns',
     'B07VGZVF6J',
     'https://www.miniaturemarket.com/gw-47-14.html',
     'https://www.nobleknight.com/P/2148067824/Bullgryns'),

    ('AM-038', 'Astra Militarum Primaris Psyker', Decimal('35.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-primaris-psyker-2023',
     'B0BSFN5XJX',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-primaris-psyker-gw-47-39.html',
     ''),

    ('AM-039', 'Astra Militarum Rogal Dorn Battle Tank', Decimal('105.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-rogal-dorn-battle-tank-2023',
     'B0BSFPDY7G',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-rogal-dorn-battle-tank-gw-47-31.html',
     ''),

    ('AM-040', 'Astra Militarum Shadowsword', Decimal('197.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-shadowsword-2023',
     'B0BSFR52RV',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-baneblade-gw-47-24-2023.html',
     'https://www.nobleknight.com/P/2148031750/Baneblade'),

    ('AM-041', 'Astra Militarum Sly Marbo', Decimal('33.50'),
     'https://www.warhammer.com/en-US/shop/Astra-Militarum-Sly-Marbo-2018',
     '', '', ''),

    ('AM-042', 'Astra Militarum Stormlord', Decimal('197.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-stormlord-2023',
     'B0BSFR52RV',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-baneblade-gw-47-24-2023.html',
     'https://www.nobleknight.com/P/2148031750/Baneblade'),

    ('AM-043', 'Astra Militarum Stormsword', Decimal('197.00'),
     'https://www.warhammer.com/en-US/shop/astra-militarum-stormsword-2023',
     'B0BSFR52RV',
     'https://www.miniaturemarket.com/warhammer-40k-astra-militarum-baneblade-gw-47-24-2023.html',
     'https://www.nobleknight.com/P/2148031750/Baneblade'),

    ('AM-044', 'Astra Militarum Taurox', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/Taurox',
     'B00JH152QK', '', ''),

    ('AM-045', 'Astra Militarum Taurox Prime', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/Taurox-Prime',
     'B00JH152QK', '', ''),

    ('AM-046', 'Astra Militarum Tech-Priest Enginseer', Decimal('39.00'),
     'https://www.warhammer.com/en-US/shop/Astra-Militarum-Tech-Priest-Enginseer',
     'B01GU9DT0C', '', ''),

    ('AM-047', 'Astra Militarum Tempestus Scions', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/Militarum-Tempestus-Scions-2017',
     'B0BSHFN9QS',
     'https://www.miniaturemarket.com/gw-47-15.html', ''),

    ('AM-048', 'Astra Militarum Valkyrie', Decimal('96.00'),
     'https://www.warhammer.com/en-US/shop/Imperial-Guard-Valkyrie',
     'B00274PJJO',
     'https://www.miniaturemarket.com/gw-47-10.html', ''),

    ('AM-049', 'Astra Militarum Wyvern', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/Astra-Militarum-Wyvern',
     'B0BSHF4G6G',
     'https://www.miniaturemarket.com/gw-47-21.html', ''),
]


class Command(BaseCommand):
    """Seed 49 Astra Militarum products (AM-001 to AM-049) with retailer price rows."""

    help = 'Seed Astra Militarum products and their GW, Amazon, MM, and NK price rows.'

    def handle(self, *args, **options):
        """Run the seed."""
        try:
            category = Category.objects.get(name='Warhammer 40,000')
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Category "Warhammer 40,000" not found — run populate_products first.'
            ))
            return

        faction = Faction.objects.filter(name='Astra Militarum').first()
        if not faction:
            self.stdout.write(self.style.ERROR(
                'Faction "Astra Militarum" not found — create it in admin first.'
            ))
            return

        retailers = {
            slug: Retailer.objects.get(slug=slug)
            for slug in ['games-workshop', 'amazon', 'miniature-market', 'noble-knight-games']
        }

        created_count = 0
        updated_count = 0

        for gw_sku, name, msrp, gw_url, amazon_asin, mm_url, nk_base_url in PRODUCTS:
            image_url = _GW_CDN.format(_IMAGES.get(gw_sku, ''))
            product, created = Product.objects.update_or_create(
                gw_sku=gw_sku,
                defaults={
                    'name': name,
                    'slug': slugify(name),
                    'msrp': msrp,
                    'gw_url': gw_url,
                    'image_url': image_url,
                    'category': category,
                    'faction': faction,
                    'is_active': True,
                    'batch_tag': 'astra-militarum',
                },
            )

            if gw_sku in _EBAY_NEGATIVE_KEYWORDS:
                Product.objects.filter(gw_sku=gw_sku).update(
                    ebay_negative_keywords=_EBAY_NEGATIVE_KEYWORDS[gw_sku],
                )
            if created:
                created_count += 1
            else:
                updated_count += 1

            # GW — seed at MSRP
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailers['games-workshop'],
                defaults={
                    'price': msrp,
                    'url': gw_url,
                    'in_stock': True,
                    'not_available': False,
                    'listing_title': name,
                },
            )

            # Amazon — create placeholder only; never overwrite a scraped price
            amazon_url = _amazon_url(amazon_asin)
            if amazon_url:
                cp, cp_created = CurrentPrice.objects.get_or_create(
                    product=product,
                    retailer=retailers['amazon'],
                    defaults={
                        'price': None,
                        'url': amazon_url,
                        'in_stock': False,
                        'not_available': False,
                        'listing_title': '',
                    },
                )
                if not cp_created and cp.url != amazon_url:
                    cp.url = amazon_url
                    cp.save(update_fields=['url'])

            # Miniature Market — only create row if URL exists
            if mm_url:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailers['miniature-market'],
                    defaults={
                        'price': None,
                        'url': mm_url,
                        'in_stock': False,
                        'not_available': False,
                        'listing_title': '',
                    },
                )

            # Noble Knight — only create row if URL exists
            nk_url = _nk_url(nk_base_url)
            if nk_url:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailers['noble-knight-games'],
                    defaults={
                        'price': None,
                        'url': nk_url,
                        'in_stock': False,
                        'not_available': False,
                        'listing_title': '',
                    },
                )

            self.stdout.write(f'  [{"new" if created else "upd"}] {gw_sku} — {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}  Updated: {updated_count}'
        ))
