"""
Management command: populate_bloodbowl_products

Creates the Blood Bowl category and all 100 Blood Bowl product entries.
Seeds GW CurrentPrice at MSRP for every product, and creates Amazon /
Miniature Market / Noble Knight CurrentPrice placeholder rows (price=None)
wherever a URL is available so scrapers can fill in prices on the next run.

Also sets sort_order on Warhammer 40,000 (sort_order=1) so it appears first
in category navigation, and sorts Blood Bowl last (sort_order=99).

No faction is assigned to Blood Bowl products — faction is left null.

Amazon URLs are stored in affiliate format (?tag=thrifthammer7-20).
Noble Knight URLs include the ?awid=1576 affiliate param.
Miniature Market has no affiliate programme — URLs are stored as-is.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_bloodbowl_products
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

AMAZON_TAG = 'thrifthammer7-20'
NK_AWID = '1576'
_GW_CDN = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{}'

_IMAGES = {
    'BB-001': '60010999014_ENGBloodBowlSeason3CoreGame1.jpg',
    'BB-002': '60040999029_ENGBloodBowlSeason3CoreGame19.jpg',
    'BB-003': '99120999016_BBAmazonTeamLead.jpg',
    'BB-004': '99120999015_BBNorseTeamLead.jpg',
    'BB-005': '99120901003_KhorneTeamLead.jpg',
    'BB-006': '99120907002_BBS2LizardmenTeamLead.jpg',
    'BB-007': '99120907002_NecromanticTeamLead.jpg',
    'BB-008': '99120901002_BBNurglesRottersTeam01.jpg',
    'BB-009': '99120999017_BBGnomeTeam02.jpg',
    'BB-010': '99120999018_OldWorldAlliance2.jpg',
    'BB-011': '99120902002_BBImperialNobilityTeamLead.jpg',
    'BB-012': '99120902001_ReiklandReaversTeam01.jpg',
    'BB-013': '99120913001_FireMountainGutbusters01.jpg',
    'BB-014': '99120912001_NaggarothNightwings01.jpg',
    'BB-015': '99120907001_ChampionsofDeathTeam01.jpg',
    'BB-016': '99120906002_BBSkavenTeamLead.jpg',
    'BB-017': '99120901001_DoomlordsChaosTeam01.jpg',
    'BB-018': '99120909004_CrudCreekNosepickersLead.jpg',
    'BB-019': '99120904001_BBAtherlornAvengersTeam01.jpg',
    'BB-020': '99120999004_GreenfieldGrasshuggersTeam01.jpg',
    'BB-021': '99120999003_ElfheimEaglesTeam01.jpg',
    'BB-022': '99120905001_DwarfGiants01.jpg',
    'BB-023': '99120910001_HighElvesTeam1.jpg',
    'BB-024': '99120917001_ENGBloodBowlSeason3CoreGame3.jpg',
    'BB-025': '99120903001_ENGBloodBowlSeason3CoreGame2.jpg',
    'BB-026': '99120911001_BBChaosDwarfTeam01.jpg',
    'BB-027': '99120907004_BBDrakfangThirsters02.jpg',
    'BB-028': '99850999042_SkrorgSnowpeltLead.jpg',
    'BB-029': '99850999039_BBYheteeLead.jpg',
    'BB-030': '99850906004_RatOgreLead.jpg',
    'BB-031': '99850999038_BBKroxigorLead.jpg',
    'BB-032': '99850999033_BBKhorneBloodspawnLead.jpg',
    'BB-033': '99120999011_BBOgreLead.jpg',
    'BB-034': '99120999007_TreemanLead.jpg',
    'BB-035': '99550999013_ChaosMinotaur01.jpg',
    'BB-036': '99550999007_BBGoblinSecretWeapons01.jpg',
    'BB-037': '99560905001_Deathroller01.jpg',
    'BB-038': '99120999002_BloodBowlTroll01.jpg',
    'BB-039': '99850999067_KirothKrakeneye1.jpg',
    'BB-040': '99850999047_Vargheist1.jpg',
    'BB-041': '99850999045_IvanAnimal1.jpg',
    'BB-042': '99850999056_RipperBolgrot1.jpg',
    'BB-043': '99850999057_DrullDrible2.jpg',
    'BB-044': '99850999055_BBPuggyBaconbreathAndCindyPiewhistle01.jpg',
    'BB-045': '99850999053_BBGlotlStopLead.jpg',
    'BB-046': '99850999051_BBBoaKonssstriktrLead.jpg',
    'BB-047': '99850999046_BBEstellelaVeneauxLead.jpg',
    'BB-048': '99850999043_RumbelowSheepskinLead.jpg',
    'BB-049': '99850999041_ThorssonStoutmeadLead.jpg',
    'BB-050': '99850999040_BBIvarErikssonLead.jpg',
    'BB-051': '99850909006_BBFungusTheLoonBomberDribblesnotLead.jpg',
    'BB-052': '99850999037_BBBarikFarblastLead.jpg',
    'BB-053': '99850999034_BBScylaAnfinngrimmLead.jpg',
    'BB-054': '99850999036_BBKreekTheVerminatorRustgougerLead.jpg',
    'BB-055': '99850907002_BBWilhelmChaneyLead.jpg',
    'BB-056': '99120999010_BiasedRefereesLead.jpg',
    'BB-057': '99120999009_VaragGhoulchewerUpdateLead.jpg',
    'BB-058': '99550999031_BBS2GretchenWachterLead.jpg',
    'BB-059': '99550907001_BBSkrullHalfheightLead.jpg',
    'BB-060': '99550999028_BBWillowRosebark01.jpg',
    'BB-061': '99560999026_DeeprootStrongbranch01.jpg',
    'BB-062': '99550999025_LordBoraktheDespoiler01.jpg',
    'BB-063': '99550999024_NurgleRotspawn01.jpg',
    'BB-064': '99550999022_HelmutWulf01.jpg',
    'BB-065': '99550999021_KarlaVonKill01.jpg',
    'BB-066': '99550999020_TheSwiftTwins01.jpg',
    'BB-067': '99550999017_RoxannaDarknail01.jpg',
    'BB-068': '99550999014_BBEldrilSidewinder01.jpg',
    'BB-069': '99700289055_SoulboundStarterSet1.jpg',
    'BB-070': '99550906003_GlartSmashrip01.jpg',
    'BB-071': '99550999010_GrombrindolBlackGobbo01.jpg',
    'BB-072': '99550999009_GrimIronjaw01.jpg',
    'BB-073': '99550906002_HakflemSkuttlespike01.jpg',
    'BB-074': '99550999003_MorgnThorg01.jpg',
    'BB-075': '99550999004_MightyZug01.jpg',
    'BB-076': '99860999073_BBMapleHighgroveAndSwiftvineGlimmershard01.jpg',
    'BB-077': '99850999091_BBJeremiahKoolCharacter01.jpg',
    'BB-078': '99850999090_BBRowenaForestfootCharacter01.jpg',
    'BB-079': '99850999089_BBGufflePusmawCharacter01.jpg',
    'BB-080': '99850999086_BBAnqiPanqiCharacter01.jpg',
    'BB-081': '99850999069_BBRashnakBackstabberCharacter01.jpg',
    'BB-082': '99850999070_BBZzhargMadeye01.jpg',
    'BB-083': '99850999050_BBHtharkTheUnstoppable01.jpg',
    'BB-084': '99850999078_BBJordellFreshbreeze01.jpg',
    'BB-085': '99850999076_BBRodneyRoachbait01.jpg',
    'BB-086': '99850999077_SkitterStabStab1.jpg',
    'BB-087': '99850999058_Bilerot1.jpg',
    'BB-088': '99850999048_LuthorVonDrakenborg1.jpg',
    'BB-089': '99850999072_GrashnakBlackhoof1.jpg',
    'BB-090': '99850999059_CptKarinaVonRieszFW1.jpg',
    'BB-091': '99120999019_UnderworldDenizens2.jpg',
    'BB-092': '99120909005_BlackOrcTeamLead.jpg',
    'BB-093': '99120909002_ScarcragSnivelersTeam01.jpg',
    'BB-094': '99120909006_BBOrcTeamLead.jpg',
    'BB-095': '99550999030_ZolcathZoatLead.jpg',
    'BB-096': '99850999054_WithergraspDoubledrool1.jpg',
    'BB-097': '99850999052_BBNobblaBlackwartaandScrappaSorehead01.jpg',
    'BB-098': '99850999032_BBMaxSpleenripperLead.jpg',
    'BB-099': '99120999008_BBGriffOberwaldLead.jpg',
    'BB-100': '99550999029_GSummerbloom01.jpg',
}

# ── Product definitions ────────────────────────────────────────────────────────
# Each tuple: (name, gw_sku, msrp, gw_url, amazon_asin, mm_url, nk_slug)
#
# amazon_asin : 10-char ASIN or None
# mm_url      : full Miniature Market URL or None
# nk_slug     : Noble Knight URL path (without ?awid) or None

PRODUCTS = [
    (
        'Blood Bowl – Third Season Edition Starter Set',
        'BB-001', 145.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-third-season-edition-2025-eng',
        'B0FXY5X1BB',
        'https://www.miniaturemarket.com/gw-200-01.html',
        'https://www.nobleknight.com/P/2148370844/Blood-Bowl-3rd-Season-Edition',
    ),
    (
        'Blood Bowl: The Official Rulebook – Third Season Edition!',
        'BB-002', 60.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-official-rulebook-3rd-2025-eng',
        'B0FY39QD9Z',
        'https://www.miniaturemarket.com/gw-200-03.html',
        None,
    ),
    (
        'Amazon Blood Bowl Team',
        'BB-003', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-amazon-team-2022',
        'B0BGHZJ1DW',
        'https://www.miniaturemarket.com/gw-202-26.html',
        None,
    ),
    (
        'Norse Blood Bowl Team',
        'BB-004', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-norse-team-2022',
        'B09XMXNKTR',
        'https://www.miniaturemarket.com/gw-202-24.html',
        None,
    ),
    (
        'Khorne Blood Bowl Team',
        'BB-005', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-khorne-team-2021',
        'B09L583JNT',
        'https://www.miniaturemarket.com/gw-202-19.html',
        None,
    ),
    (
        'Lizardmen Blood Bowl Team',
        'BB-006', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Lizardmen-Team-2020',
        'B07YQ7VHKC',
        'https://www.miniaturemarket.com/gw-200-74.html',
        None,
    ),
    (
        'Necromantic Horror Blood Bowl Team',
        'BB-007', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Necromantic-Horror-Team-2020',
        'B08N5FQN62',
        'https://www.miniaturemarket.com/gw-202-07.html',
        None,
    ),
    (
        'Nurgle Blood Bowl Team',
        'BB-008', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Nurgles-Rotters-Team-2018',
        None,
        'https://www.miniaturemarket.com/gw-200-57.html',
        None,
    ),
    (
        'Gnome Blood Bowl Team',
        'BB-009', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-gnome-team-2024',
        'B0CZP2YN7M',
        'https://www.miniaturemarket.com/blood-bowl-gnome-team-glimdwarrow-groundhogs-gw-202-41.html',
        None,
    ),
    (
        'Old World Alliance Blood Bowl Team',
        'BB-010', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-old-world-alliance-team-2023',
        'B0C9N1FCFV',
        'https://www.miniaturemarket.com/blood-bowl-old-world-alliance-team-middenheim-maulers-gw-202-05-2023.html',
        None,
    ),
    (
        'Imperial Nobility Blood Bowl Team',
        'BB-011', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Imperial-Nobility-Team-2021',
        'B0924V88VR',
        'https://www.miniaturemarket.com/gw-202-13.html',
        None,
    ),
    (
        'Human Blood Bowl Team',
        'BB-012', 55.50,
        'https://www.warhammer.com/en-US/shop/Reikland-Reavers-Blood-Bowl-Team-2020',
        'B06XCRTB98',
        None,
        None,
    ),
    (
        'Ogre Blood Bowl Team',
        'BB-013', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Ogre-Team-2020',
        'B082DPN2BL',
        'https://www.miniaturemarket.com/gw-202-02.html',
        None,
    ),
    (
        'Dark Elf Blood Bowl Team',
        'BB-014', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Dark-Elf-Team-2020',
        'B07FBDFLLC',
        'https://www.miniaturemarket.com/gw-200-54.html',
        None,
    ),
    (
        'Shambling Undead Blood Bowl Team',
        'BB-015', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Champions-of-Death-Team-2020',
        'B07KZL8W5L',
        'https://www.miniaturemarket.com/gw-200-62.html',
        None,
    ),
    (
        'Skaven Blood Bowl Team',
        'BB-016', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Skaven-Team-2020',
        None,
        'https://www.miniaturemarket.com/gw-200-11.html',
        None,
    ),
    (
        'Chaos Chosen Blood Bowl Team',
        'BB-017', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Chaos-Chosen-Team-2020',
        'B07CQ9PWL3',
        'https://www.miniaturemarket.com/gw-200-47.html',
        None,
    ),
    (
        'Snotling Blood Bowl Team',
        'BB-018', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Crud-Creek-Nosepickers-Team-2020',
        'B08GJ34V6Y',
        'https://www.miniaturemarket.com/gw-202-01.html',
        None,
    ),
    (
        'Wood Elf Blood Bowl Team',
        'BB-019', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-The-Athelorn-Avengers-2019',
        'B07V7ZX3SH',
        'https://www.miniaturemarket.com/gw-200-66.html',
        None,
    ),
    (
        'Halfling Blood Bowl Team',
        'BB-020', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Greenfield-Grasshuggers-2019',
        'B097C67DRT',
        'https://www.miniaturemarket.com/gw-200-65.html',
        None,
    ),
    (
        'Elven Union Blood Bowl Team',
        'BB-021', 55.50,
        'https://www.warhammer.com/en-US/shop/Elfheim-Eagles-Blood-Bowl-Team-2017',
        'B097C4XVCC',
        'https://www.miniaturemarket.com/gw-200-36.html',
        None,
    ),
    (
        'Dwarf Blood Bowl Team',
        'BB-022', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-The-Dwarf-Giants',
        'B01NAYFWHN',
        'https://www.miniaturemarket.com/gw-200-17.html',
        None,
    ),
    (
        'High Elf Blood Bowl Team',
        'BB-023', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-high-elf-blood-bowl-team-2026',
        'B0GRWBM78C',
        'https://www.miniaturemarket.com/Blood-Bowl-High-Elf-Team-The-Caledor-Dragons/GW-202-62-2026',
        None,
    ),
    (
        'Tomb Kings Blood Bowl Team',
        'BB-024', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-tomb-kings-team-2025',
        'B0FXY855KF',
        'https://www.miniaturemarket.com/Blood-Bowl-Tomb-Kings-Team-The-Nehekhara-Nightmares/GW-202-52',
        None,
    ),
    (
        'Bretonnian Blood Bowl Team',
        'BB-025', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-bretonnian-team-2025',
        'B0FXY83KK5',
        'https://www.miniaturemarket.com/Blood-Bowl-Bretonnian-Team-The-Brionne-Barons/GW-202-51',
        None,
    ),
    (
        'Chaos Dwarf Blood Bowl Team',
        'BB-026', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-chaos-dwarf-team-2024',
        'B0DHS77RJP',
        'https://www.miniaturemarket.com/blood-bowl-chaos-dwarf-team-zharr-naggrund-ziggurats-gw-201-11.html',
        None,
    ),
    (
        'Vampire Blood Bowl Team',
        'BB-027', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-vampire-team-2023',
        'B0CJ9BM8TK',
        'https://www.miniaturemarket.com/blood-bowl-vampire-team-the-drakfang-thirsters-gw-202-36.html',
        None,
    ),
    (
        'Skrorg Snowpelt',
        'BB-028', 45.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-skrorg-snowpelt-2022',
        None, None, None,
    ),
    (
        'Blood Bowl Yhetee',
        'BB-029', 44.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-yhetee-2022',
        None, None, None,
    ),
    (
        'Blood Bowl Rat Ogre',
        'BB-030', 44.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-rat-ogre-2022',
        None, None, None,
    ),
    (
        'Blood Bowl Kroxigor',
        'BB-031', 45.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-kroxigor-2021',
        None, None, None,
    ),
    (
        'Blood Bowl Khorne Bloodspawn',
        'BB-032', 47.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-khorne-bloodspawn-2021',
        None, None, None,
    ),
    (
        'Blood Bowl Ogre',
        'BB-033', 35.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Ogre-2020',
        'B08NGK1KL5',
        'https://www.miniaturemarket.com/gw-200-23.html',
        None,
    ),
    (
        'Blood Bowl Treeman',
        'BB-034', 35.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Treeman-2020',
        'B0CZP5G6QN',
        'https://www.miniaturemarket.com/gw-200-99.html',
        None,
    ),
    (
        'Blood Bowl Minotaur',
        'BB-035', 44.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Minotaur-2017',
        None, None, None,
    ),
    (
        'Blood Bowl Goblin Secret Weapons',
        'BB-036', 45.00,
        'https://www.warhammer.com/en-US/shop/Goblin-secret-weapons-2017',
        None, None, None,
    ),
    (
        'Blood Bowl Dwarf Deathroller',
        'BB-037', 89.00,
        'https://www.warhammer.com/en-US/shop/Dwarf-Deathroller',
        None, None, None,
    ),
    (
        'Blood Bowl Troll',
        'BB-038', 35.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Troll',
        'B06XY9RW2V',
        'https://www.miniaturemarket.com/gw-200-24.html',
        None,
    ),
    (
        'Blood Bowl Kiroth Krakeneye',
        'BB-039', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-kiroth-krakeneye-2023',
        None, None, None,
    ),
    (
        'Blood Bowl Vargheist',
        'BB-040', 44.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-vargheist-2023',
        None, None, None,
    ),
    (
        "Ivan 'the Animal' Deathshroud",
        'BB-041', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-ivan-the-animal-deathshroud-2023',
        None, None, None,
    ),
    (
        'Ripper Bolgrot',
        'BB-042', 45.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-ripper-bolgrot-2023',
        None, None, None,
    ),
    (
        'Dribl & Drull',
        'BB-043', 44.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-dribl-and-drull-2023',
        None, None, None,
    ),
    (
        'Cindy Piewhistle & Puggy Baconbreath',
        'BB-044', 44.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-puggy-baconbreath-and-cindy-piewhistle-2023',
        None, None, None,
    ),
    (
        'Glotl Stop',
        'BB-045', 52.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-glotl-stop-2022',
        None, None, None,
    ),
    (
        "Boa Kon'ssstriktr",
        'BB-046', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-boa-konssstriktr-2022',
        None, None, None,
    ),
    (
        'Estelle La Veneaux',
        'BB-047', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-estelle-la-veneaux-2022',
        None, None, None,
    ),
    (
        'Rumbelow Sheepskin',
        'BB-048', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-rumbelow-sheepskin-2022',
        None, None, None,
    ),
    (
        'Thorsson Stoutmead',
        'BB-049', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-thorsson-stoutmead-2022',
        None, None, None,
    ),
    (
        'Ivar Eriksson',
        'BB-050', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-ivar-eriksson-2022',
        None, None, None,
    ),
    (
        'Fungus The Loon and Bomber Dribblesnot',
        'BB-051', 44.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-fungus-the-loon-and-bomber-dribblesnot-2022',
        None, None, None,
    ),
    (
        'Barik Farblast',
        'BB-052', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-barik-farblast-2021',
        None, None, None,
    ),
    (
        'Scyla Anfingrimm',
        'BB-053', 75.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-scylla-anfingrimm-2021',
        None, None, None,
    ),
    (
        "Kreek 'the Verminator' Rustgouger",
        'BB-054', 52.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-kreek-the-verminator-rustgouger-2021',
        None, None, None,
    ),
    (
        'Wilhelm Chaney',
        'BB-055', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-wilhelm-chaney-2021',
        None, None, None,
    ),
    (
        'Elf and Dwarf Biased Referees',
        'BB-056', 21.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Elf-And-Dwarf-Biased-Referees-2021',
        'B0924SXFGZ',
        'https://www.miniaturemarket.com/gw-202-16.html',
        None,
    ),
    (
        'Varag Ghoul-Chewer',
        'BB-057', 21.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Varag-Ghoul-chewer-2021',
        'B0924THHHJ',
        'https://www.miniaturemarket.com/gw-202-15.html',
        None,
    ),
    (
        'Gretchen Wächter',
        'BB-058', 39.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Gretchen-Wachter-2021',
        None, None, None,
    ),
    (
        'Skrull Halfheight',
        'BB-059', 39.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Skrull-Halfheight-2020',
        None, None, None,
    ),
    (
        'Willow Rosebark',
        'BB-060', 39.00,
        'https://www.warhammer.com/en-US/shop/Willow-Rosebark-2019',
        None, None, None,
    ),
    (
        'Deeproot Strongbranch',
        'BB-061', 84.00,
        'https://www.warhammer.com/en-US/shop/Deeproot-Strongbranch-2019',
        None, None, None,
    ),
    (
        'Lord Borak the Despoiler',
        'BB-062', 39.00,
        'https://www.warhammer.com/en-US/shop/Lord-Borak-the-Despoiler-2019',
        None, None, None,
    ),
    (
        'Blood Bowl Nurgle Rotspawn',
        'BB-063', 45.00,
        'https://www.warhammer.com/en-US/shop/Nurgle-Rotspawn-2019',
        None, None, None,
    ),
    (
        'Helmut Wulf',
        'BB-064', 39.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Helmut-Wulf-2019',
        None, None, None,
    ),
    (
        'Karla von Kill',
        'BB-065', 39.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Karla-Von-Kill-2019',
        None, None, None,
    ),
    (
        'The Swift Twins',
        'BB-066', 58.00,
        'https://www.warhammer.com/en-US/shop/The-Swift-Twins-2018',
        None, None, None,
    ),
    (
        'Roxanna Darknail',
        'BB-067', 39.00,
        'https://www.warhammer.com/en-US/shop/Roxanna-Darknail-2018',
        None, None, None,
    ),
    (
        'Eldril Sidewinder',
        'BB-068', 39.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Eldril-Sidewinder-2018',
        None, None, None,
    ),
    (
        'Josef Bugman, Coach & Star Player',
        'BB-069', 47.00,
        'https://www.warhammer.com/en-US/shop/Bb-Josef-Bugman-Coach-Star-Player-2018',
        None, None, None,
    ),
    (
        'Glart Smashrip',
        'BB-070', 39.00,
        'https://www.warhammer.com/en-US/shop/Glart-Smashrip-2017',
        None, None, None,
    ),
    (
        'Grombrindal And The Black Gobbo',
        'BB-071', 45.00,
        'https://www.warhammer.com/en-US/shop/Blood-bowl-grombrindal-the-black-gobbo-2017',
        None, None, None,
    ),
    (
        'Grim Ironjaw',
        'BB-072', 39.00,
        'https://www.warhammer.com/en-US/shop/Blood-bowl-grim-ironjaw-2017',
        None, None, None,
    ),
    (
        'Hakflem Skuttlespike',
        'BB-073', 39.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Hakflem-Skuttlespike-2017',
        None, None, None,
    ),
    (
        "Morg 'n' Thorg",
        'BB-074', 45.00,
        'https://www.warhammer.com/en-US/shop/Morg-N-Thorg',
        None, None, None,
    ),
    (
        'The Mighty Zug',
        'BB-075', 39.00,
        'https://www.warhammer.com/en-US/shop/The-Mighty-Zug',
        None, None, None,
    ),
    (
        'Maple Highgrove & Swiftvine Glimmershard',
        'BB-076', 81.00,
        'https://www.warhammer.com/en-US/shop/maple-highgrove-and-swiftvine-glimmershard-2025',
        None, None, None,
    ),
    (
        'Jeremiah Kool',
        'BB-077', 38.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-jeremiah-kool-2025',
        None, None, None,
    ),
    (
        'Rowana Forestfoot',
        'BB-078', 38.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-rowana-forestfoot-2025',
        None, None, None,
    ),
    (
        'Guffle Pusmaw',
        'BB-079', 38.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-guffle-pusmaw-2025',
        None, None, None,
    ),
    (
        'Anqi Panqi',
        'BB-080', 38.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-anqi-panqi-2025',
        None, None, None,
    ),
    (
        'Rashnak Backstabber',
        'BB-081', 38.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-rashnak-backstabber-2025',
        None, None, None,
    ),
    (
        'Zzharg Madeye',
        'BB-082', 38.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-zzharg-madeye-2024',
        None, None, None,
    ),
    (
        "H'thark the Unstoppable",
        'BB-083', 52.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-hthark-the-unstoppable-2024',
        None, None, None,
    ),
    (
        'Jordell Freshbreeze',
        'BB-084', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-jordell-freshbreeze-2024',
        None, None, None,
    ),
    (
        'Rodney Roachbait',
        'BB-085', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-rodney-roachbait-2024',
        None, None, None,
    ),
    (
        'Skitter Stab-Stab',
        'BB-086', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-skitter-stab-stab-2024',
        None, None, None,
    ),
    (
        'Bilerot Vomitflesh',
        'BB-087', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-bilerot-vomitflesh-2023',
        None, None, None,
    ),
    (
        'Count Luthor von Drakenborg',
        'BB-088', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-count-luthor-von-drakenborg-2023',
        None, None, None,
    ),
    (
        'Grashnak Blackhoof',
        'BB-089', 52.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-grashnak-blackhoof-2024',
        None, None, None,
    ),
    (
        "'Captain' Karina von Riesz",
        'BB-090', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-captain-karina-von-riesz-2023',
        None, None, None,
    ),
    (
        'Underworld Denizens Blood Bowl Team',
        'BB-091', 55.50,
        'https://www.warhammer.com/en-US/shop/blood-bowl-underworld-denizens-team-2023',
        'B0C9N5HJZK',
        'https://www.miniaturemarket.com/blood-bowl-underworld-denizens-team-underworld-creepers-gw-202-04-2023.html',
        None,
    ),
    (
        'Black Orc Blood Bowl Team',
        'BB-092', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Black-Orc-Team-2021',
        'B0924TGX67',
        'https://www.miniaturemarket.com/gw-202-12.html',
        None,
    ),
    (
        'Goblin Blood Bowl Team',
        'BB-093', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Goblin-Team-2020',
        None,
        'https://www.miniaturemarket.com/gw-200-27.html',
        None,
    ),
    (
        'Orc Blood Bowl Team',
        'BB-094', 55.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Orc-Team-2020',
        None, None, None,
    ),
    (
        'Zolcath The Zoat',
        'BB-095', 75.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Zolcath-The-Zoat-2020',
        None, None, None,
    ),
    (
        'Withergrasp Doubledrool',
        'BB-096', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-withergrasp-doubledrool-2023',
        None, None, None,
    ),
    (
        'Nobbla Blackwart & Scrappa Sorehead',
        'BB-097', 44.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-nobbla-blackwart-and-scrappa-sorehead-2023',
        None, None, None,
    ),
    (
        'Max Spleenripper',
        'BB-098', 39.00,
        'https://www.warhammer.com/en-US/shop/blood-bowl-max-spleenripper-2021',
        None, None, None,
    ),
    (
        'Griff Oberwald',
        'BB-099', 21.50,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Griff-Oberwald-2021',
        None,
        'https://www.miniaturemarket.com/gw-202-14.html',
        None,
    ),
    (
        'Gloriel Summerbloom',
        'BB-100', 39.00,
        'https://www.warhammer.com/en-US/shop/Blood-Bowl-Gloriel-Summerbloom-2019',
        None, None, None,
    ),
]


class Command(BaseCommand):
    """Create Blood Bowl category, products, and seed retailer prices."""

    help = (
        'Populates the Blood Bowl category with 100 products. '
        'Seeds GW prices at MSRP and creates Amazon/MM/NK placeholder rows '
        'for scrapers to fill. Also pins Warhammer 40,000 as the first category. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        # ── Resolve retailers ─────────────────────────────────────────────────
        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        amazon = Retailer.objects.filter(name='Amazon').first()
        mm = Retailer.objects.filter(name='Miniature Market').first()
        nk = Retailer.objects.filter(slug='noble-knight-games').first()

        if not gw_retailer:
            self.stderr.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        # ── Create Blood Bowl category ────────────────────────────────────────
        bb_category, bb_created = Category.objects.get_or_create(
            name='Blood Bowl',
            defaults={
                'slug': 'blood-bowl',
                'description': (
                    'Blood Bowl is Games Workshop\'s fantasy football game. '
                    'Compare prices on team boxes, star players, and special characters.'
                ),
                'sort_order': 99,
            },
        )
        if bb_created:
            self.stdout.write(self.style.SUCCESS('Created category: Blood Bowl (sort_order=99)'))
        else:
            if bb_category.sort_order != 99:
                bb_category.sort_order = 99
                bb_category.save(update_fields=['sort_order'])
            self.stdout.write(f'Found category: Blood Bowl (pk={bb_category.pk})')

        # ── Pin Warhammer 40,000 as the first category ────────────────────────
        wh40k = Category.objects.filter(name='Warhammer 40,000').first()
        if wh40k:
            if wh40k.sort_order != 1:
                wh40k.sort_order = 1
                wh40k.save(update_fields=['sort_order'])
                self.stdout.write(self.style.SUCCESS(
                    'Set Warhammer 40,000 sort_order=1 (pinned first)'
                ))
            else:
                self.stdout.write('Warhammer 40,000 already sort_order=1')
        else:
            self.stdout.write(self.style.WARNING(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))

        # ── Seed products ─────────────────────────────────────────────────────
        prod_created = prod_updated = 0
        gw_created = gw_updated = 0
        amz_created = amz_updated = 0
        mm_created = mm_updated = 0
        nk_created = nk_updated = 0

        for (name, gw_sku, msrp, gw_url, amazon_asin, mm_url, nk_url) in PRODUCTS:
            slug = slugify(name)

            product, created = Product.objects.update_or_create(
                gw_sku=gw_sku,
                defaults={
                    'name': name,
                    'slug': slug,
                    'msrp': msrp,
                    'gw_url': gw_url,
                    'image_url': _GW_CDN.format(_IMAGES.get(gw_sku, '')),
                    'category': bb_category,
                    'faction': None,
                    'is_active': True,
                    'batch_tag': 'blood-bowl',
                },
                # ebay_negative_keywords is a create-time default only -- it
                # gets manually curated per-product afterward (extra keywords
                # appended as mismatches are found), so this command must
                # never overwrite it on an update or that curation is lost
                # on every deploy. 'Dice' is just the sensible starting
                # value for a brand-new Blood Bowl product.
                create_defaults={
                    'ebay_negative_keywords': 'Dice',
                },
            )
            if created:
                prod_created += 1
            else:
                prod_updated += 1

            # ── GW price ──────────────────────────────────────────────────────
            if gw_retailer:
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    defaults={
                        'price': msrp,
                        'url': gw_url,
                        'in_stock': True,
                        'not_available': False,
                        'listing_title': name,
                    },
                )
                if p_created:
                    gw_created += 1
                else:
                    gw_updated += 1

            # ── Amazon placeholder — create only; never overwrite a scraped price ──
            if amazon and amazon_asin:
                affiliate_url = f'https://www.amazon.com/dp/{amazon_asin}?tag={AMAZON_TAG}'
                cp, p_created = CurrentPrice.objects.get_or_create(
                    product=product,
                    retailer=amazon,
                    defaults={
                        'price': None,
                        'url': affiliate_url,
                        'in_stock': False,
                        'not_available': False,
                        'listing_title': '',
                    },
                )
                if p_created:
                    amz_created += 1
                else:
                    amz_updated += 1
                    if cp.url != affiliate_url:
                        cp.url = affiliate_url
                        cp.save(update_fields=['url'])

            # ── Miniature Market placeholder ──────────────────────────────────
            if mm and mm_url:
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=mm,
                    defaults={
                        'url': mm_url,
                        'not_available': False,
                        'listing_title': '',
                    },
                    create_defaults={
                        'price': None,
                        'in_stock': False,
                    },
                )
                if p_created:
                    mm_created += 1
                else:
                    mm_updated += 1

            # ── Noble Knight placeholder ──────────────────────────────────────
            if nk and nk_url:
                nk_affiliate = f'{nk_url}?awid={NK_AWID}'
                _, p_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=nk,
                    defaults={
                        'url': nk_affiliate,
                        'not_available': False,
                        'listing_title': '',
                    },
                    create_defaults={
                        'price': None,
                        'in_stock': False,
                    },
                )
                if p_created:
                    nk_created += 1
                else:
                    nk_updated += 1

            self.stdout.write(
                f"  {'Created' if created else 'Updated'}: {name} [{gw_sku}]"
            )

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_bloodbowl_products complete.\n'
            f'  Products: {prod_created} created, {prod_updated} updated.\n'
            f'  GW prices: {gw_created} created, {gw_updated} updated.\n'
            f'  Amazon rows: {amz_created} created, {amz_updated} updated.\n'
            f'  MM rows: {mm_created} created, {mm_updated} updated.\n'
            f'  NK rows: {nk_created} created, {nk_updated} updated.'
        ))
