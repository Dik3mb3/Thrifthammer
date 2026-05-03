# Generated 2026-05-03
#
# Imports Amazon URLs for Phase 2/3/4 products.
# Each URL is normalised to /dp/{ASIN}?tag=thrifthammer7-20 format.
# Prices are left for the Amazon scraper to fill in on its next run.
#
# Idempotent -- uses update_or_create, safe to re-run.

from django.db import migrations


# (gw_sku, amazon_url)
AMAZON_DATA = [
    ('63-01', 'https://www.amazon.com/dp/B08HR5R3FB?tag=thrifthammer7-20'),  # Adrax Agatone
    ('46-09', 'https://www.amazon.com/dp/B09TG2LS1N?tag=thrifthammer7-20'),  # Aeldari Guardians
    ('prod4390158', 'https://www.amazon.com/dp/B08HSTJXW3?tag=thrifthammer7-20'),  # Annihilation Barge
    ('53-21', 'https://www.amazon.com/dp/B0FF4WDW37?tag=thrifthammer7-20'),  # Arjac Rockfist
    ('P-222999-99120118025', 'https://www.amazon.com/dp/B0FL3MVTG8?tag=thrifthammer7-20'),  # Arkanyst Evaluator
    ('48-100', 'https://www.amazon.com/dp/B0CJS353L5?tag=thrifthammer7-20'),  # Assault Intercessors with Jump Packs
    ('P-203616', 'https://www.amazon.com/dp/B0DV3YNRHV?tag=thrifthammer7-20'),  # Asurmen
    ('prod4900146', 'https://www.amazon.com/dp/B09W2RYZ53?tag=thrifthammer7-20'),  # Autarch
    ('prod2810200', 'https://www.amazon.com/dp/B09W2RYZ53?tag=thrifthammer7-20'),  # Autarch Wayleaper
    ('prod4900143', 'https://www.amazon.com/dp/B09W2Q6N78?tag=thrifthammer7-20'),  # Avatar of Khaine
    ('P-203620', 'https://www.amazon.com/dp/B0DV3Z2S1H?tag=thrifthammer7-20'),  # Baharroth
    ('50-23', 'https://www.amazon.com/dp/B09F3XD3RY?tag=thrifthammer7-20'),  # Beastboss
    ('50-24', 'https://www.amazon.com/dp/B09H4K1B9X?tag=thrifthammer7-20'),  # Beastboss on Squigosaur
    ('prod3700246-99129915062', 'https://www.amazon.com/dp/B09PTTPRH5?tag=thrifthammer7-20'),  # Beast of Nurgle
    ('P-240930-99120118028', 'https://www.amazon.com/dp/B0GQVX8HCP?tag=thrifthammer7-20'),  # Berehk Stornbrow
    ('50-25', 'https://www.amazon.com/dp/B09F4MBYRJ?tag=thrifthammer7-20'),  # Big'ed Bossbunka
    ('50-26', 'https://www.amazon.com/dp/B0D63FQV1H?tag=thrifthammer7-20'),  # Big Mek
    ('50-27', 'https://www.amazon.com/dp/B00LKE10EK?tag=thrifthammer7-20'),  # Big Mek in Mega Armour
    ('50-28', 'https://www.amazon.com/dp/B0D63FQV1H?tag=thrifthammer7-20'),  # Big Mek with Shokk Attack Gun
    ('53-22', 'https://www.amazon.com/dp/B08K7PCLWD?tag=thrifthammer7-20'),  # Bjorn the Fell-handed
    ('50-29', 'https://www.amazon.com/dp/B09HJWQWB7?tag=thrifthammer7-20'),  # Blitza-Bommer
    ('41-26', 'https://www.amazon.com/dp/B0DJFGCLBW?tag=thrifthammer7-20'),  # Blood Angels Captain
    ('41-27', 'https://www.amazon.com/dp/B018KKGP3W?tag=thrifthammer7-20'),  # Blood Angels Chaplain With Jump Pack
    ('41-28', 'https://www.amazon.com/dp/B0CBKL1G2B?tag=thrifthammer7-20'),  # Blood Angels Librarian in Terminator Armour
    ('53-23', 'https://www.amazon.com/dp/B0FF4TF6X1?tag=thrifthammer7-20'),  # Blood Claws
    ('P-KHORNE-BLOODCRUSHERS', 'https://www.amazon.com/dp/B01B6LPYH0?tag=thrifthammer7-20'),  # Bloodcrushers of Khorne
    ('P-KHORNE-BLOODLETTERS-40K', 'https://www.amazon.com/dp/B0018OALAQ?tag=thrifthammer7-20'),  # Bloodletters of Khorne
    ('P-KHORNE-BLOODTHIRSTER', 'https://www.amazon.com/dp/B0FR56QT3T?tag=thrifthammer7-20'),  # Bloodthirster
    ('P-TZEENTCH-BLUEHORRORS', 'https://www.amazon.com/dp/B01MZH3ZZ9?tag=thrifthammer7-20'),  # Blue Horrors and Brimstone Horrors
    ('50-31', 'https://www.amazon.com/dp/B09FYRBR66?tag=thrifthammer7-20'),  # Boomdakka Snazzwagon
    ('50-32', 'https://www.amazon.com/dp/B0CB1B4L5D?tag=thrifthammer7-20'),  # Boss Snikrot
    ('prod5000444-99120118010', 'https://www.amazon.com/dp/B0BK9MRJP3?tag=thrifthammer7-20'),  # Brokhyr Iron-master
    ('prod5000439-99120118005', 'https://www.amazon.com/dp/B0BK9JF6SM?tag=thrifthammer7-20'),  # Brokhyr Thunderkyn
    ('P-223003-99120118019', 'https://www.amazon.com/dp/B0FL2YZDWT?tag=thrifthammer7-20'),  # Buri Aegnirssen
    ('50-33', 'https://www.amazon.com/dp/B09HJWQWB7?tag=thrifthammer7-20'),  # Burna-Bommer
    ('61-01', 'https://www.amazon.com/dp/B0FTZZV9PM?tag=thrifthammer7-20'),  # Caanok Var
    ('prod4390146', 'https://www.amazon.com/dp/B08KHNGVCX?tag=thrifthammer7-20'),  # Canoptek Doomstalker
    ('prod4390156', 'https://www.amazon.com/dp/B08GBYFKSC?tag=thrifthammer7-20'),  # Canoptek Wraiths
    ('48-101', 'https://www.amazon.com/dp/B09RGCPT3L?tag=thrifthammer7-20'),  # Captain in Gravis Armour
    ('48-102', 'https://www.amazon.com/dp/B08FZSLZT1?tag=thrifthammer7-20'),  # Captain in Phobos Armour
    ('48-103', 'https://www.amazon.com/dp/B0CVRZKPV3?tag=thrifthammer7-20'),  # Captain in Terminator Armour
    ('55-31', 'https://www.amazon.com/dp/B0GF8W95HF?tag=thrifthammer7-20'),  # Captain Titus and The Wardens of Ultramar
    ('48-104', 'https://www.amazon.com/dp/B0CJRZ2H4G?tag=thrifthammer7-20'),  # Captain with Jump Pack
    ('48-105', 'https://www.amazon.com/dp/B0FTZZS85K?tag=thrifthammer7-20'),  # Captain with Jump Pack and Relic Shield
    ('57-21', 'https://www.amazon.com/dp/B09VH19YMN?tag=thrifthammer7-20'),  # Castellan Crowe
    ('55-32', 'https://www.amazon.com/dp/B0FX53MF13?tag=thrifthammer7-20'),  # Cato Sicarius
    ('48-107', 'https://www.amazon.com/dp/B08SSMBWLV?tag=thrifthammer7-20'),  # Centurion Assault Squad
    ('48-108', 'https://www.amazon.com/dp/B08SSMBWLV?tag=thrifthammer7-20'),  # Centurion Devastator Squad
    ('prod2430129-99120102043', 'https://www.amazon.com/dp/B00J0AYRWS?tag=thrifthammer7-20'),  # Chaos Helbrute
    ('99120102052', 'https://www.amazon.com/dp/B001GQQT2A?tag=thrifthammer7-20'),  # Chaos Land Raider
    ('99120102092', 'https://www.amazon.com/dp/B0B834LHFL?tag=thrifthammer7-20'),  # Chaos Rhino
    ('P-CSM-SORC-TERM', 'https://www.amazon.com/dp/B07PY4Q529?tag=thrifthammer7-20'),  # Chaos Sorcerer Lord in Terminator Armour
    ('43-06', 'https://www.amazon.com/dp/B0B3JT7TKX?tag=thrifthammer7-20'),  # Chaos Space Marines Legionaries
    ('99070102015', 'https://www.amazon.com/dp/B081GBX6L3?tag=thrifthammer7-20'),  # Chaos Space Marines Sorcerer
    ('99120201050', 'https://www.amazon.com/dp/B01BVL23DI?tag=thrifthammer7-20'),  # Chaos Spawn
    ('99120102097', 'https://www.amazon.com/dp/B0B4F9985P?tag=thrifthammer7-20'),  # Chaos Terminator Squad
    ('P-CSM-VINDICATOR', 'https://www.amazon.com/dp/B08NHSYW88?tag=thrifthammer7-20'),  # Chaos Vindicator
    ('48-109', 'https://www.amazon.com/dp/B08KHP79L7?tag=thrifthammer7-20'),  # Chaplain on Bike
    ('55-33', 'https://www.amazon.com/dp/B08TWFNF9L?tag=thrifthammer7-20'),  # Chief Librarian Tigurius
    ('prod4900148', 'https://www.amazon.com/dp/B095J16T2X?tag=thrifthammer7-20'),  # Chronomancer
    ('46-30', 'https://www.amazon.com/dp/B0DV9XM5QQ?tag=thrifthammer7-20'),  # Codex: Aeldari
    ('P-213409-60030102032', 'https://www.amazon.com/dp/1804575003?tag=thrifthammer7-20'),  # Codex: Death Guard
    ('65-01', 'https://www.amazon.com/dp/B0F443WYQ4?tag=thrifthammer7-20'),  # Codex: Emperor's Children
    ('57-22', 'https://www.amazon.com/dp/1804575763?tag=thrifthammer7-20'),  # Codex: Grey Knights
    ('P-223015-60030118002', 'https://www.amazon.com/dp/180457631X?tag=thrifthammer7-20'),  # Codex: Leagues of Votann
    ('50-34', 'https://www.amazon.com/dp/1804573205?tag=thrifthammer7-20'),  # Codex: Orks
    ('48-110', 'https://www.amazon.com/dp/1804572381?tag=thrifthammer7-20'),  # Codex: Space Marines
    ('58-01', 'https://www.amazon.com/dp/B0FJMVKS4K?tag=thrifthammer7-20'),  # Codex Supplement: Black Templars
    ('41-29', 'https://www.amazon.com/dp/1804574449?tag=thrifthammer7-20'),  # Codex Supplement: Blood Angels
    ('44-21', 'https://www.amazon.com/dp/1804573116?tag=thrifthammer7-20'),  # Codex Supplement: Dark Angels
    ('53-24', 'https://www.amazon.com/dp/1839061138?tag=thrifthammer7-20'),  # Codex Supplement: Space Wolves
    ('P-TS-CODEX-2023', 'https://www.amazon.com/dp/B0F9B4ZZCZ?tag=thrifthammer7-20'),  # Codex: Thousand Sons
    ('P-WE-CODEX-2025', 'https://www.amazon.com/dp/1804575097?tag=thrifthammer7-20'),  # Codex: World Eaters
    ('99120102207', 'https://www.amazon.com/dp/B0F5XBQZ1L?tag=thrifthammer7-20'),  # Combat Patrol: Emperor's Children
    ('prod4390153', 'https://www.amazon.com/dp/B08LB6QZN7?tag=thrifthammer7-20'),  # Convergence of Dominion
    ('prod3600196', 'https://www.amazon.com/dp/B09VMHC9FY?tag=thrifthammer7-20'),  # Crimson Hunter
    ('prod4390141', 'https://www.amazon.com/dp/B08GL6VHZZ?tag=thrifthammer7-20'),  # Cryptek
    ('P-241016', 'https://www.amazon.com/dp/B0GG4MYRQV?tag=thrifthammer7-20'),  # C'tan Shard of the Nightbringer
    ('prod5000436-99120118002', 'https://www.amazon.com/dp/B0BKB72PGB?tag=thrifthammer7-20'),  # Cthonian Berserks
    ('P-223004-99120118021', 'https://www.amazon.com/dp/B0FL3DLZZ8?tag=thrifthammer7-20'),  # Cthonian Earthshakers
    ('99129915036', 'https://www.amazon.com/dp/B0742JDVCK?tag=thrifthammer7-20'),  # Daemonettes of Slaanesh
    ('99120201130', 'https://www.amazon.com/dp/B0BRY38LCC?tag=thrifthammer7-20'),  # Daemon Prince
    ('50-35', 'https://www.amazon.com/dp/B09HJWQWB7?tag=thrifthammer7-20'),  # Dakkajet
    ('44-02', 'https://www.amazon.com/dp/B000NVRX0Q?tag=thrifthammer7-20'),  # Dark Angels Ezekiel
    ('44-22', 'https://www.amazon.com/dp/B075X3Y4F3?tag=thrifthammer7-20'),  # Dark Angels Interrogator-Chaplain
    ('prod4870189', 'https://www.amazon.com/dp/B09TG4GJWC?tag=thrifthammer7-20'),  # Dark Reapers
    ('60-01', 'https://www.amazon.com/dp/B0FPDM6LH7?tag=thrifthammer7-20'),  # Darnath Lysander
    ('85-02', 'https://www.amazon.com/dp/B0BH9F7JM8?tag=thrifthammer7-20'),  # Daughters of Khaine Morathi-Khaine
    ('85-17', 'https://www.amazon.com/dp/B07B27617B?tag=thrifthammer7-20'),  # Daughters of Khaine Sisters of Slaughter
    ('43-24', 'https://www.amazon.com/dp/B076FF2DMC?tag=thrifthammer7-20'),  # Death Guard Biologus Putrifier
    ('prod4570149-99120102114', 'https://www.amazon.com/dp/B08RK1HD85?tag=thrifthammer7-20'),  # Death Guard Chosen of Mortarion
    ('43-46', 'https://www.amazon.com/dp/B08X75VGX3?tag=thrifthammer7-20'),  # Death Guard Foul Blightspawn
    ('prod4650190-99120102150', 'https://www.amazon.com/dp/B08QW34YBG?tag=thrifthammer7-20'),  # Death Guard Lord of Contagion and Blightlord Terminators
    ('43-77', 'https://www.amazon.com/dp/B08T7J2ZTT?tag=thrifthammer7-20'),  # Death Guard Lord of Virulence
    ('43-78', 'https://www.amazon.com/dp/B08T7HD5DV?tag=thrifthammer7-20'),  # Death Guard Miasmic Malignifier
    ('43-52', 'https://www.amazon.com/dp/B08PQ9PPWZ?tag=thrifthammer7-20'),  # Death Guard Plagueburst Crawler
    ('43-48', 'https://www.amazon.com/dp/B076FF8BY3?tag=thrifthammer7-20'),  # Death Guard Plague Marine Champion
    ('43-47', 'https://www.amazon.com/dp/B076FFF28P?tag=thrifthammer7-20'),  # Death Guard Plague Marine Icon Bearer
    ('43-29', 'https://www.amazon.com/dp/B0763KMV5S?tag=thrifthammer7-20'),  # Death Guard Plague Surgeon
    ('43-45', 'https://www.amazon.com/dp/B0763KR5DM?tag=thrifthammer7-20'),  # Death Guard Tallyman
    ('prod2620120', 'https://www.amazon.com/dp/B09Z77THN3?tag=thrifthammer7-20'),  # Death Jester
    ('prod4390142', 'https://www.amazon.com/dp/B00631UMA8?tag=thrifthammer7-20'),  # Deathmarks
    ('50-36', 'https://www.amazon.com/dp/B09HJGKXR3?tag=thrifthammer7-20'),  # Deffkilla Wartrike
    ('50-37', 'https://www.amazon.com/dp/B09NST65MS?tag=thrifthammer7-20'),  # Deffkoptas
    ('48-111', 'https://www.amazon.com/dp/B0CJS2VYVQ?tag=thrifthammer7-20'),  # Desolation Squad
    ('48-112', 'https://www.amazon.com/dp/B0FF4XDKQ2?tag=thrifthammer7-20'),  # Drop Pods
    ('45-12', 'https://www.amazon.com/dp/B091VXBHQ1?tag=thrifthammer7-20'),  # Drukhari Ravager
    ('prod3650164', 'https://www.amazon.com/dp/B076Q37BHZ?tag=thrifthammer7-20'),  # Eldrad Ulthran
    ('prod3650295', 'https://www.amazon.com/dp/B09WNGQTBT?tag=thrifthammer7-20'),  # Farseer Skyrunner
    ('53-25', 'https://www.amazon.com/dp/B078VCQBW4?tag=thrifthammer7-20'),  # Fenrisian Wolves
    ('99129915052', 'https://www.amazon.com/dp/B07R55R7QB?tag=thrifthammer7-20'),  # Fiends
    ('prod770019a', 'https://www.amazon.com/dp/B003P0YRLA?tag=thrifthammer7-20'),  # Fire Prism
    ('P-TZEENTCH-FLAMERS', 'https://www.amazon.com/dp/B01N4VDVTR?tag=thrifthammer7-20'),  # Flamers of Tzeentch
    ('99120102202', 'https://www.amazon.com/dp/B0F3XCNW1D?tag=thrifthammer7-20'),  # Flawless Blades
    ('P-KHORNE-FLESHHOUNDS', 'https://www.amazon.com/dp/B0C47VMPXV?tag=thrifthammer7-20'),  # Flesh Hounds of Khorne
    ('99120102089', 'https://www.amazon.com/dp/B07PWY44DY?tag=thrifthammer7-20'),  # Forgefiend
    ('P-203621', 'https://www.amazon.com/dp/B0DV421YK7?tag=thrifthammer7-20'),  # Fuegan
    ('99120102200', 'https://www.amazon.com/dp/B0F3XH9J9L?tag=thrifthammer7-20'),  # Fulgrim ? Daemon Primarch of Slaanesh
    ('50-38', 'https://www.amazon.com/dp/B08M2HJXTW?tag=thrifthammer7-20'),  # Ghazghkull Thraka
    ('prod4390157', 'https://www.amazon.com/dp/B08HCL7SFY?tag=thrifthammer7-20'),  # Ghost Ark
    ('48-113', 'https://www.amazon.com/dp/B08P7YJSM6?tag=thrifthammer7-20'),  # Gladiator Lancer
    ('48-114', 'https://www.amazon.com/dp/B08P7YJSM6?tag=thrifthammer7-20'),  # Gladiator Reaper
    ('48-115', 'https://www.amazon.com/dp/B08P7YJSM6?tag=thrifthammer7-20'),  # Gladiator Valiant
    ('89-10', 'https://www.amazon.com/dp/B07M71TWV4?tag=thrifthammer7-20'),  # Gloomspite Gitz Squig Herd
    ('50-39', 'https://www.amazon.com/dp/B09HJSR7Y8?tag=thrifthammer7-20'),  # Gorkanaut
    ('57-23', 'https://www.amazon.com/dp/B0FPDMT27L?tag=thrifthammer7-20'),  # Grand Master in Nemesis Dreadknight
    ('prod3700247-99129915063', 'https://www.amazon.com/dp/B09RQQMXQF?tag=thrifthammer7-20'),  # Great Unclean One
    ('57-25', 'https://www.amazon.com/dp/B09C3NTQSP?tag=thrifthammer7-20'),  # Grey Knights Paladins
    ('prod4870188', 'https://www.amazon.com/dp/B09TG2LS1N?tag=thrifthammer7-20'),  # Guardian Defenders
    ('prod3530579', 'https://www.amazon.com/dp/B09Y2DHTQV?tag=thrifthammer7-20'),  # Harlequin Troupe
    ('48-116', 'https://www.amazon.com/dp/B095J5ZPN7?tag=thrifthammer7-20'),  # Heavy Intercessor Squad
    ('prod5000440-99120118006', 'https://www.amazon.com/dp/B0BK9JNRVX?tag=thrifthammer7-20'),  # Hekaton Land Fortress
    ('99120102090', 'https://www.amazon.com/dp/B01LXTJ1JC?tag=thrifthammer7-20'),  # Heldrake
    ('48-117', 'https://www.amazon.com/dp/B08HSVBXTM?tag=thrifthammer7-20'),  # Hellblaster Squad
    ('prod3600197', 'https://www.amazon.com/dp/B09VMHC9FY?tag=thrifthammer7-20'),  # Hemlock Wraithfighter
    ('prod4390148', 'https://www.amazon.com/dp/B08KXCR2C6?tag=thrifthammer7-20'),  # Hexmark Destroyer
    ('prod4390157', 'https://www.amazon.com/dp/B09TLBQLG7?tag=thrifthammer7-20'),  # Howling Banshees
    ('50-41', 'https://www.amazon.com/dp/B09H4J1DXM?tag=thrifthammer7-20'),  # Hunta Rig
    ('prod4390160', 'https://www.amazon.com/dp/B08BNC4GL6?tag=thrifthammer7-20'),  # Illuminor Szeras
    ('prod4900149', 'https://www.amazon.com/dp/B0CNTV7SQK?tag=thrifthammer7-20'),  # Imotekh the Stormlord
    ('48-118', 'https://www.amazon.com/dp/B08GCKF1DW?tag=thrifthammer7-20'),  # Invictor Tactical Warsuit
    ('61-02', 'https://www.amazon.com/dp/B08LQT7D8W?tag=thrifthammer7-20'),  # Iron Father Feirros
    ('P-223001-99120118020', 'https://www.amazon.com/dp/B0FL3DG4ZQ?tag=thrifthammer7-20'),  # Ironkin Steeljacks
    ('53-26', 'https://www.amazon.com/dp/B01BU0P9JA?tag=thrifthammer7-20'),  # Iron Priest
    ('prod4390156', 'https://www.amazon.com/dp/B0856SCBXQ?tag=thrifthammer7-20'),  # Jain Zar
    ('prod5000456-99120118011', 'https://www.amazon.com/dp/B0BK9KZWZB?tag=thrifthammer7-20'),  # Kahl
    ('P-TZEENTCH-KAIROS', 'https://www.amazon.com/dp/B01N5WN83Y?tag=thrifthammer7-20'),  # Kairos Fateweaver
    ('P-223006-99120118022', 'https://www.amazon.com/dp/B0FL2YXDNQ?tag=thrifthammer7-20'),  # Kapricus Defender/Carrier
    ('62-02', 'https://www.amazon.com/dp/B08M6DJ925?tag=thrifthammer7-20'),  # Kayvaan Shrike
    ('99129915056', 'https://www.amazon.com/dp/B0CD2WVBPV?tag=thrifthammer7-20'),  # Keeper of Secrets
    ('50-42', 'https://www.amazon.com/dp/B09H4J1DXM?tag=thrifthammer7-20'),  # Kill Rig
    ('P-WE-KT-GOREMONGERS-2025', 'https://www.amazon.com/dp/B0FCG8V21Z?tag=thrifthammer7-20'),  # Kill Team: Goremongers (World Eaters)
    ('P-198770-99120118023', 'https://www.amazon.com/dp/B0DPMXJ9JR?tag=thrifthammer7-20'),  # Kill Team: Hearthkyn Salvagers (Leagues of Votann)
    ('P-189754-99120118018', 'https://www.amazon.com/dp/B0DH4VYQ39?tag=thrifthammer7-20'),  # Kill Team: Hernkyn Yaegirs (Leagues of Votann)
    ('50-43', 'https://www.amazon.com/dp/B0FNRZZG4M?tag=thrifthammer7-20'),  # Kommandos
    ('64-01', 'https://www.amazon.com/dp/B07W99YY6X?tag=thrifthammer7-20'),  # Kor'sarro Khan
    ('50-44', 'https://www.amazon.com/dp/B07P5P9GFX?tag=thrifthammer7-20'),  # Kustom Boosta-blasta
    ('48-119', 'https://www.amazon.com/dp/B001GQQT2A?tag=thrifthammer7-20'),  # Land Raider Redeemer
    ('P-203618', 'https://www.amazon.com/dp/B0DV3ZNSBT?tag=thrifthammer7-20'),  # Lhykhis
    ('48-120', 'https://www.amazon.com/dp/B0CBKL1G2B?tag=thrifthammer7-20'),  # Librarian in Terminator Armour
    ('48-121', 'https://www.amazon.com/dp/B08L44KSMZ?tag=thrifthammer7-20'),  # Lieutenant in Reiver Armour
    ('48-122', 'https://www.amazon.com/dp/B07WJ7CF9D?tag=thrifthammer7-20'),  # Lieutenant with Power Sword
    ('53-27', 'https://www.amazon.com/dp/B0FF4T3ZF2?tag=thrifthammer7-20'),  # Logan Grimnar
    ('prod4390155', 'https://www.amazon.com/dp/B00D6H2TIK?tag=thrifthammer7-20'),  # Lokhust Destroyer Squadron
    ('prod4390145', 'https://www.amazon.com/dp/B08KHPTP7Y?tag=thrifthammer7-20'),  # Lokhust Heavy Destroyer
    ('99120102206', 'https://www.amazon.com/dp/B0F3XG1KGX?tag=thrifthammer7-20'),  # Lord Exultant
    ('99120102205', 'https://www.amazon.com/dp/B0F3XH8X2N?tag=thrifthammer7-20'),  # Lord Kakophonist
    ('P-TZEENTCH-LOC', 'https://www.amazon.com/dp/B01N5WN83Y?tag=thrifthammer7-20'),  # Lord of Change
    ('99120102201', 'https://www.amazon.com/dp/B0F3XG2DDJ?tag=thrifthammer7-20'),  # Lucius the Eternal
    ('P-CSM-MASTER-EXEC', 'https://www.amazon.com/dp/B07QN8DJFK?tag=thrifthammer7-20'),  # Master of Executions
    ('prod4870190', 'https://www.amazon.com/dp/B09TG4HTD4?tag=thrifthammer7-20'),  # Maugan Ra
    ('99120102089', 'https://www.amazon.com/dp/B07PWY44DY?tag=thrifthammer7-20'),  # Maulerfiend
    ('50-45', 'https://www.amazon.com/dp/B09FYLC8GV?tag=thrifthammer7-20'),  # Megatrakk Scrapjet
    ('50-46', 'https://www.amazon.com/dp/B00L5JUSCK?tag=thrifthammer7-20'),  # Mek Gunz: Bubblechukka
    ('50-47', 'https://www.amazon.com/dp/B00L5JUSCK?tag=thrifthammer7-20'),  # Mek Gunz: Kustom Mega-kannon
    ('50-48', 'https://www.amazon.com/dp/B00L5JUSCK?tag=thrifthammer7-20'),  # Mek Gunz: Smasha Gun
    ('50-49', 'https://www.amazon.com/dp/B00L5JUSCK?tag=thrifthammer7-20'),  # Mek Gunz: Traktor Kannon
    ('P-222997-99120118026', 'https://www.amazon.com/dp/B0FL3NGM8D?tag=thrifthammer7-20'),  # Memnyr Strategist
    ('50-50', 'https://www.amazon.com/dp/B09HJSR7Y8?tag=thrifthammer7-20'),  # Morkanaut
    ('50-51', 'https://www.amazon.com/dp/B09H4K1B9X?tag=thrifthammer7-20'),  # Mozrog Skragbad
    ('53-28', 'https://www.amazon.com/dp/B08K7PCLWD?tag=thrifthammer7-20'),  # Murderfang
    ('prod4390158', 'https://www.amazon.com/dp/B08HSTJXW3?tag=thrifthammer7-20'),  # Necron Catacomb Command Barge
    ('P-241017', 'https://www.amazon.com/dp/B0GF84XVF9?tag=thrifthammer7-20'),  # Nekrosor Ammentar
    ('prod4390159', 'https://www.amazon.com/dp/B08GC4PD6K?tag=thrifthammer7-20'),  # Night Scythe
    ('prod2180123', 'https://www.amazon.com/dp/B003P0YRLA?tag=thrifthammer7-20'),  # Night Spinner
    ('53-29', 'https://www.amazon.com/dp/B0FF4RG3PC?tag=thrifthammer7-20'),  # Njal Stormcaller
    ('99120102204', 'https://www.amazon.com/dp/B0F3XFN1D3?tag=thrifthammer7-20'),  # Noise Marines
    ('prod3550127-99129915060', 'https://www.amazon.com/dp/B0B1VTZ3R7?tag=thrifthammer7-20'),  # Nurglings
    ('prod3590140', 'https://www.amazon.com/dp/B00DQLOI3U?tag=thrifthammer7-20'),  # Obelisk & Transcendent C'tan
    ('prod4390154', 'https://www.amazon.com/dp/B08LB7CSFD?tag=thrifthammer7-20'),  # Ophydian Destroyers
    ('prod4900151', 'https://www.amazon.com/dp/B0CNTVZSML?tag=thrifthammer7-20'),  # Orikan the Diviner
    ('50-52', 'https://www.amazon.com/dp/B09F3ZGTQC?tag=thrifthammer7-20'),  # Ork Beast Snagga Boyz
    ('50-54', 'https://www.amazon.com/dp/B09HP3GMD7?tag=thrifthammer7-20'),  # Ork Gretchin
    ('50-55', 'https://www.amazon.com/dp/B0D63FQV1H?tag=thrifthammer7-20'),  # Ork Mek
    ('50-56', 'https://www.amazon.com/dp/B00LBAL1GU?tag=thrifthammer7-20'),  # Ork Painboy
    ('50-57', 'https://www.amazon.com/dp/B09HJNNY87?tag=thrifthammer7-20'),  # Ork Stormboyz
    ('50-58', 'https://www.amazon.com/dp/B07JMMP6N9?tag=thrifthammer7-20'),  # Ork Warbiker Mob
    ('prod4900150', 'https://www.amazon.com/dp/B0CNTVXSM6?tag=thrifthammer7-20'),  # Overlord with Tachyon Arrow
    ('50-60', 'https://www.amazon.com/dp/B09H4HZ6N1?tag=thrifthammer7-20'),  # Painboss
    ('P-PINK-HORRORS-40K', 'https://www.amazon.com/dp/B07C7FMFN8?tag=thrifthammer7-20'),  # Pink Horrors of Tzeentch
    ('P-NURGLE-PLAGUEBEARERS-40K', 'https://www.amazon.com/dp/B0746GFZYZ?tag=thrifthammer7-20'),  # Plaguebearers of Nurgle
    ('prod3610130-99129915038', 'https://www.amazon.com/dp/B07BQGCGSW?tag=thrifthammer7-20'),  # Plague Drones of Nurgle
    ('48-124', 'https://www.amazon.com/dp/B07WJHVDFC?tag=thrifthammer7-20'),  # Predator Destructor
    ('48-125', 'https://www.amazon.com/dp/B08GCB5F1X?tag=thrifthammer7-20'),  # Primaris Librarian in Phobos Armour
    ('prod4900144', 'https://www.amazon.com/dp/B09W2SN6S5?tag=thrifthammer7-20'),  # Rangers
    ('44-23', 'https://www.amazon.com/dp/B08THMGCVL?tag=thrifthammer7-20'),  # Ravenwing Bike Squadron
    ('48-126', 'https://www.amazon.com/dp/B001D1A334?tag=thrifthammer7-20'),  # Razorback
    ('48-127', 'https://www.amazon.com/dp/B08HY6TYDW?tag=thrifthammer7-20'),  # Reiver Squad
    ('48-128', 'https://www.amazon.com/dp/B001D1A334?tag=thrifthammer7-20'),  # Rhino
    ('prod3700271-99129915063', 'https://www.amazon.com/dp/B09RQQMXQF?tag=thrifthammer7-20'),  # Rotigus
    ('50-61', 'https://www.amazon.com/dp/B09FYQKZ3B?tag=thrifthammer7-20'),  # Rukkatrukk Squigbuggy
    ('prod5000437-99120118003', 'https://www.amazon.com/dp/B0BK9NG2TB?tag=thrifthammer7-20'),  # Sagitaur
    ('P-TZEENTCH-SCREAMERS', 'https://www.amazon.com/dp/B01N6YBL9B?tag=thrifthammer7-20'),  # Screamers of Tzeentch
    ('99129915005', 'https://www.amazon.com/dp/B003YKLMOG?tag=thrifthammer7-20'),  # Seekers of Slaanesh
    ('prod2620121', 'https://www.amazon.com/dp/B00U2MWDT2?tag=thrifthammer7-20'),  # Shadowseer
    ('99129915056', 'https://www.amazon.com/dp/B0CD2WVBPV?tag=thrifthammer7-20'),  # Shalaxi Helbane
    ('prod4900142', 'https://www.amazon.com/dp/B09W2SM31C?tag=thrifthammer7-20'),  # Shining Spears
    ('50-62', 'https://www.amazon.com/dp/B07P8W28C7?tag=thrifthammer7-20'),  # Shokkjump Dragsta
    ('prod4900145', 'https://www.amazon.com/dp/B09W2RF2W4?tag=thrifthammer7-20'),  # Shroud Runners
    ('P-KHORNE-SKARBRAND', 'https://www.amazon.com/dp/B0GDL2C7K9?tag=thrifthammer7-20'),  # Skarbrand the Bloodthirster
    ('prod4390150', 'https://www.amazon.com/dp/B08KXDLBWX?tag=thrifthammer7-20'),  # Skorpekh Destroyers
    ('prod2620124', 'https://www.amazon.com/dp/B09YMFLLVX?tag=thrifthammer7-20'),  # Skyweavers
    ('prod2620122', 'https://www.amazon.com/dp/B00TBIORLA?tag=thrifthammer7-20'),  # Solitaire
    ('53-30', 'https://www.amazon.com/dp/B08K7PCLWD?tag=thrifthammer7-20'),  # Space Wolves Venerable Dreadnought
    ('prod4240206', 'https://www.amazon.com/dp/B07V2PBJBC?tag=thrifthammer7-20'),  # Spiritseer
    ('50-63', 'https://www.amazon.com/dp/B09F3WDVPC?tag=thrifthammer7-20'),  # Squighog Boyz
    ('P-240924', 'https://www.amazon.com/dp/B0GQVQPS9G?tag=thrifthammer7-20'),  # Starfang
    ('prod2600170', 'https://www.amazon.com/dp/B09XH827TD?tag=thrifthammer7-20'),  # Starweaver
    ('50-64', 'https://www.amazon.com/dp/B001UK5BCG?tag=thrifthammer7-20'),  # Stompa
    ('48-129', 'https://www.amazon.com/dp/B08PQ7GR1V?tag=thrifthammer7-20'),  # Stormhawk Interceptor
    ('48-130', 'https://www.amazon.com/dp/B08GC7RWF6?tag=thrifthammer7-20'),  # Stormraven Gunship
    ('48-131', 'https://www.amazon.com/dp/B08VHDJMBK?tag=thrifthammer7-20'),  # Storm Speeder Hailstrike
    ('48-132', 'https://www.amazon.com/dp/B08VHDJMBK?tag=thrifthammer7-20'),  # Storm Speeder Hammerstrike
    ('48-133', 'https://www.amazon.com/dp/B08VHDJMBK?tag=thrifthammer7-20'),  # Storm Speeder Thunderstrike
    ('48-134', 'https://www.amazon.com/dp/B08PQ7GR1V?tag=thrifthammer7-20'),  # Stormtalon Gunship
    ('64-02', 'https://www.amazon.com/dp/B0G313PXHG?tag=thrifthammer7-20'),  # Suboden Khan
    ('P-203614', 'https://www.amazon.com/dp/B0DV41PWSK?tag=thrifthammer7-20'),  # Swooping Hawks
    ('prod4390152', 'https://www.amazon.com/dp/B08KHQ2T6G?tag=thrifthammer7-20'),  # Szarekh, The Silent King
    ('48-135', 'https://www.amazon.com/dp/B08LBB1P58?tag=thrifthammer7-20'),  # Techmarine
    ('48-136', 'https://www.amazon.com/dp/B0G2ZRZ18V?tag=thrifthammer7-20'),  # Terminator Assault Squad
    ('prod3590140', 'https://www.amazon.com/dp/B00DQLOI3U?tag=thrifthammer7-20'),  # Tesseract Vault
    ('prod4870191', 'https://www.amazon.com/dp/B09WW3DV2J?tag=thrifthammer7-20'),  # The Yncarne
    ('43-79', 'https://www.amazon.com/dp/B09VH1B5D6?tag=thrifthammer7-20'),  # Thousand Sons Infernal Master
    ('P-TS-SEKHETAR-2025', 'https://www.amazon.com/dp/B0FPDL4SKL?tag=thrifthammer7-20'),  # Thousand Sons Sekhetar Robots
    ('P-TZAANGORS-40K', 'https://www.amazon.com/dp/B0BQCPFJPS?tag=thrifthammer7-20'),  # Thousand Sons Tzaangors
    ('prod3940162', 'https://www.amazon.com/dp/B007Y9PUIM?tag=thrifthammer7-20'),  # Tomb Blades
    ('60-02', 'https://www.amazon.com/dp/B07Z8H411Z?tag=thrifthammer7-20'),  # Tor Garadon
    ('99120102203', 'https://www.amazon.com/dp/B0F3X9ZZW2?tag=thrifthammer7-20'),  # Tormentors
    ('prod2791068', 'https://www.amazon.com/dp/B0064BIS26?tag=thrifthammer7-20'),  # Trazyn the Infinite
    ('prod4390144', 'https://www.amazon.com/dp/B08GBYD7LN?tag=thrifthammer7-20'),  # Triarch Praetorians
    ('P-TZAANGOR-ENL', 'https://www.amazon.com/dp/B01NAXLZRR?tag=thrifthammer7-20'),  # Tzaangor Enlightened
    ('P-TZAANGOR-SHAMAN', 'https://www.amazon.com/dp/B0BYXWPVVP?tag=thrifthammer7-20'),  # Tzaangor Shaman
    ('53-31', 'https://www.amazon.com/dp/B01BU0P86Y?tag=thrifthammer7-20'),  # Ulrik the Slayer
    ('55-34', 'https://www.amazon.com/dp/B0FX4YGG75?tag=thrifthammer7-20'),  # Ultramarines Upgrades and Transfers
    ('prod5000445-99120118011', 'https://www.amazon.com/dp/B0BK9KZWZB?tag=thrifthammer7-20'),  # Uthar the Destined
    ('48-137', 'https://www.amazon.com/dp/B08KWMHRLV?tag=thrifthammer7-20'),  # Venerable Dreadnought
    ('prod2780228', 'https://www.amazon.com/dp/B09XH827TD?tag=thrifthammer7-20'),  # Voidweaver
    ('63-02', 'https://www.amazon.com/dp/B0FL37KGMP?tag=thrifthammer7-20'),  # Vulkan He'stan
    ('prod4870187', 'https://www.amazon.com/dp/B09TG4MXX1?tag=thrifthammer7-20'),  # Warlocks
    ('prod3660120', 'https://www.amazon.com/dp/B09WNGQTBT?tag=thrifthammer7-20'),  # Warlock Skyrunner
    ('P-203611', 'https://www.amazon.com/dp/B0DV3Z9N17?tag=thrifthammer7-20'),  # Warp Spiders
    ('P-203606', 'https://www.amazon.com/dp/B0DV3WVLBL?tag=thrifthammer7-20'),  # War Walkers
    ('50-65', 'https://www.amazon.com/dp/B09HJWQWB7?tag=thrifthammer7-20'),  # Wazbom Blastajet
    ('50-66', 'https://www.amazon.com/dp/B0067PX1DA?tag=thrifthammer7-20'),  # Weirdboy
    ('prod3660121', 'https://www.amazon.com/dp/B09VB7LBFK?tag=thrifthammer7-20'),  # Windriders
    ('53-32', 'https://www.amazon.com/dp/B0FF4T51GS?tag=thrifthammer7-20'),  # Wolf Guard Battle Leader
    ('53-33', 'https://www.amazon.com/dp/B0FF537RSN?tag=thrifthammer7-20'),  # Wolf Guard Headtakers
    ('53-34', 'https://www.amazon.com/dp/B0FF4T21SD?tag=thrifthammer7-20'),  # Wolf Priest
    ('P-WE-EXL-EIGHT-2023', 'https://www.amazon.com/dp/B0BTDD6Z24?tag=thrifthammer7-20'),  # World Eaters Exalted Eightbound
    ('P-WE-JAKHALS-2023', 'https://www.amazon.com/dp/B0BTDGXMRQ?tag=thrifthammer7-20'),  # World Eaters Jakhals
    ('P-WE-KHARN-2023', 'https://www.amazon.com/dp/B01LVZGW31?tag=thrifthammer7-20'),  # World Eaters Kharn the Betrayer
    ('P-WE-LORD-INVOC-2023', 'https://www.amazon.com/dp/B0BTDDBHPM?tag=thrifthammer7-20'),  # World Eaters Lord Invocatus
    ('P-WE-SLAUGHTER-2025', 'https://www.amazon.com/dp/B0FL3N1H2Z?tag=thrifthammer7-20'),  # World Eaters Slaughterbound
    ('prod3590139', 'https://www.amazon.com/dp/B074MCDX59?tag=thrifthammer7-20'),  # Wraithblades
    ('prod3590128', 'https://www.amazon.com/dp/B074MCDX59?tag=thrifthammer7-20'),  # Wraithguard
    ('prod3580144', 'https://www.amazon.com/dp/B09VY2RWCM?tag=thrifthammer7-20'),  # Wraithknight
    ('prod3530578', 'https://www.amazon.com/dp/B09WSR9X26?tag=thrifthammer7-20'),  # Wraithlord
    ('53-35', 'https://www.amazon.com/dp/B08MC65J3D?tag=thrifthammer7-20'),  # Wulfen
    ('53-36', 'https://www.amazon.com/dp/B08K7PCLWD?tag=thrifthammer7-20'),  # Wulfen Dreadnought
    ('50-67', 'https://www.amazon.com/dp/B09F4MBYRH?tag=thrifthammer7-20'),  # Zodgrod Wortsnagga
    ('48-99', 'https://www.amazon.com/dp/B0G315GMCV?tag=thrifthammer7-20'),  # Ancient in Terminator Armour
]


def apply(apps, schema_editor):
    """Seed Amazon URLs into CurrentPrice rows (price left for scraper)."""
    Product = apps.get_model('products', 'Product')
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')
    Retailer = apps.get_model('products', 'Retailer')

    amazon, _ = Retailer.objects.get_or_create(
        slug='amazon',
        defaults={'name': 'Amazon', 'base_url': 'https://www.amazon.com'},
    )

    updated = created = skipped = 0
    for gw_sku, url in AMAZON_DATA:
        products = Product.objects.filter(gw_sku=gw_sku)
        if not products.exists():
            print(f'  [skip] No product for SKU: {gw_sku}')
            skipped += 1
            continue
        for product in products:
            _, was_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=amazon,
                defaults={
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                    'manual_url_override': False,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

    print(f'  Amazon import: {created} created, {updated} updated, {skipped} SKUs not found')


def reverse(apps, schema_editor):
    """Clear URLs added by this migration (leaves rows, blanks the URL)."""
    Product = apps.get_model('products', 'Product')
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')
    Retailer = apps.get_model('products', 'Retailer')
    amazon = Retailer.objects.filter(slug='amazon').first()
    if not amazon:
        return
    urls = {url for _, url in AMAZON_DATA}
    CurrentPrice.objects.filter(retailer=amazon, url__in=urls).update(url='')


class Migration(migrations.Migration):

    dependencies = [
        ('prices', '0009_miniature_market_phase2_3_4_urls'),
        ('products', '0037_add_sku_negative_keywords_may2026'),
    ]

    operations = [
        migrations.RunPython(apply, reverse),
    ]
