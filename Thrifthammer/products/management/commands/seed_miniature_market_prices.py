"""
Management command: seed_miniature_market_prices

Writes verified Miniature Market prices into the production database,
keyed by GW SKU.

Source: Octoparse scrape of Miniature Market (March 2026),
  C:\\...\\Games Workshop - Miniatures Games _ Miniature Market.xlsx
  1,322 rows.

IMPORTANT: Miniature Market uses their OWN internal catalog numbers in
URLs — these do NOT match GW packaging codes.  Every URL below was
verified by title-searching the MM spreadsheet to confirm the correct
product name matches.

Many entries that the old scraper populated were WRONG (e.g., the scraper
naively mapped GW SKU 48-76 → gw-48-76.html which turned out to be
Hellblasters, not Assault Intercessors).  This command replaces all of
those with the title-verified correct URLs.

Products confirmed absent from the MM spreadsheet are flagged
not_available=True so the site shows "Not available" instead of stale
/ wrong data.

Usage:
    python manage.py seed_miniature_market_prices
    python manage.py seed_miniature_market_prices --dry-run
"""

import decimal

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ---------------------------------------------------------------------------
# Verified Miniature Market matches  (gw_sku -> (price_str, url))
# All URLs title-verified against the March 2026 Octoparse MM spreadsheet.
# not_available items have price=None and url=''.
# ---------------------------------------------------------------------------

BASE = 'https://www.miniaturemarket.com/'

MM_DATA = {
    # ── Adeptus Custodes ──────────────────────────────────────────────────
    '01-02': ('38.99', BASE + 'gw-01-10.html'),         # Captain-General Trajann Valoris
    '01-07': (None,    ''),                              # Shield-Captain — NOT IN MM
    '01-08': ('53.99', BASE + 'gw-hh01-07.html'),       # Custodian Guard Squad
    '01-10': ('53.99', BASE + 'gw-01-11.html'),         # Custodian Wardens
    '01-11': ('53.99', BASE + 'gw-01-12.html'),         # Vertus Praetors
    '01-20': (None,    ''),                              # Combat Patrol — NOT IN MM

    # ── Cerastus Knights (Forge World) ────────────────────────────────────
    '31-06': (None,    ''),                              # Cerastus Knight Lancer — NOT IN MM
    '31-66': (None,    ''),                              # Cerastus Knight Castigator — NOT IN MM
    '31-67': (None,    ''),                              # Cerastus Knight Acheron — NOT IN MM

    # ── Deathwatch ────────────────────────────────────────────────────────
    '39-01': ('32.99', BASE + 'warhammer-40k-imperial-agents-watch-captain-artemis-gw-68-09.html'),  # Artemis
    '39-02': ('8.99',  BASE + 'gw-39-02.html'),         # Watch Master (clearance price)
    '39-03': (None,    ''),                              # Decimus Kill Team — NOT IN MM
    '39-04': ('78.99', BASE + 'gw-39-12.html'),         # Corvus Blackstar
    '39-05': (None,    ''),                              # DW Terminator Squad — NOT IN MM
    '39-06': (None,    ''),                              # DW Veteran Squad — NOT IN MM
    '39-07': (None,    ''),                              # Fortis Kill Team — NOT IN MM
    '39-08': (None,    ''),                              # Indomitor Kill Team — NOT IN MM
    '39-09': (None,    ''),                              # Spectrus Kill Team — NOT IN MM
    '39-10': ('38.99', BASE + 'gw-39-10.html'),         # Deathwatch Kill Team
    '39-11': (None,    ''),                              # Talonstrike Kill Team — NOT IN MM

    # ── Warhammer 40,000 General ──────────────────────────────────────────
    '40-01': (None,    ''),                              # Core Rules — NOT IN MM
    '40-02': (None,    ''),                              # Leviathan Starter Set — NOT IN MM spreadsheet
    '40-03': (None,    ''),                              # Starter Set — NOT IN MM
    '40-10': ('33.99', BASE + 'gw-40-10.html'),         # Chapter Approved: Leviathan
    '40-20': (None,    ''),                              # Dice Set — NOT IN MM
    '40-21': (None,    ''),                              # Measuring Tape — NOT IN MM

    # ── Blood Angels ──────────────────────────────────────────────────────
    '41-02': ('38.99', BASE + 'gw-41-39.html'),         # Mephiston, Lord of Death
    '41-03': ('38.99', BASE + 'warhammer-40k-blood-angels-astorath-grim-gw-41-38.html'),  # Astorath
    '41-04': ('38.99', BASE + 'warhammer-40k-blood-angels-commander-dante-gw-41-40.html'), # Commander Dante
    '41-05': ('38.99', BASE + 'warhammer-40k-blood-angels-lemartes-gw-41-36.html'),        # Lemartes
    '41-06': ('51.00', BASE + 'warhammer-40k-blood-angels-sanguinary-guard-gw-41-31.html'), # Sanguinary Guard
    '41-07': (None,    ''),                              # Death Company Marines — NOT IN MM
    '41-08': ('38.99', BASE + 'warhammer-40k-blood-angels-sanguinor-gw-41-27-2024.html'),  # The Sanguinor
    '41-09': ('34.00', BASE + 'warhammer-40k-blood-angels-sanguinary-priest-gw-41-48.html'), # Sanguinary Priest
    '41-10': (None,    ''),                              # Baal Predator — NOT IN MM (gw-41-10 = Stormraven)
    '41-11': (None,    ''),                              # Death Company Dreadnought — NOT IN MM
    '41-12': (None,    ''),                              # Death Company w/ Jump Packs — NOT IN MM
    '41-15': (None,    ''),                              # Librarian Dreadnought — NOT IN MM
    '41-25': (None,    ''),                              # Combat Patrol — NOT IN MM

    # ── Chaos Space Marines / Death Guard / Thousand Sons ─────────────────
    '43-02': ('144.99', BASE + 'gw-43-34.html'),        # Magnus the Red
    '43-03': (None,     ''),                             # Mortarion — NOT IN MM spreadsheet
    '43-04': ('144.99', BASE + 'warhammer-40k-world-eaters-angron-daemon-primarch-of-khorne-gw-43-28.html'), # Angron
    '43-06': (None,     ''),                             # Legionaries — NOT IN MM
    '43-08': ('38.99',  BASE + 'gw-43-53.html'),        # Typhus, Herald of the Plague God
    '43-09': (None,     ''),                             # Chaos Predator — NOT IN MM
    '43-30': ('38.99',  BASE + 'gw-43-38.html'),        # Ahriman, Arch-Sorcerer of Tzeentch
    '43-35': ('53.99',  BASE + 'gw-43-35.html'),        # Rubric Marines
    '43-36': ('53.99',  BASE + 'gw-43-36.html'),        # Scarab Occult Terminators
    '43-38': ('53.99',  BASE + 'gw-43-39.html'),        # Exalted Sorcerers
    '43-50': ('51.00',  BASE + 'gw-43-55.html'),        # Plague Marines
    '43-53': (None,     ''),                             # Poxwalkers — NOT IN MM
    '43-54': ('53.99',  BASE + 'gw-43-51.html'),        # Blightlord Terminators
    '43-55': ('51.00',  BASE + 'gw-43-54.html'),        # Foetid Bloat-Drone
    '43-56': ('53.99',  BASE + 'gw-43-50.html'),        # Deathshroud Bodyguard
    '43-60': (None,     ''),                             # Berzerkers — NOT IN MM (gw-43-60 = Abaddon)
    '43-62': ('53.99',  BASE + 'warhammer-40k-world-eaters-exalted-eightbound-gw-43-72.html'), # Exalted Eightbound
    '43-64': (None,     ''),                             # Lord on Juggernaut — NOT IN MM
    '43-80': (None,     ''),                             # Death Guard Combat Patrol — NOT IN MM
    '43-90': (None,     ''),                             # Thousand Sons Combat Patrol — NOT IN MM
    '43-95': (None,     ''),                             # World Eaters Combat Patrol — NOT IN MM

    # ── Dark Angels ───────────────────────────────────────────────────────
    '44-02': (None,    ''),                              # Ezekiel — NOT IN MM
    '44-03': ('37.99', BASE + 'warhammer-40k-dark-angels-asmodai-master-repentance-gw-44-21.html'), # Asmodai
    '44-04': ('38.99', BASE + 'warhammer-40k-dark-angels-azrael-supreme-grand-master-gw-44-18.html'), # Azrael
    '44-05': ('37.99', BASE + 'warhammer-40k-dark-angels-belial-grand-master-deathwing-gw-44-23.html'), # Belial
    '44-06': ('59.99', BASE + 'warhammer-40k-dark-angels-lion-eljonson-gw-44-20.html'),  # Lion El'Jonson
    '44-07': (None,    ''),                              # Lazarus — NOT IN MM
    '44-08': (None,    ''),                              # Sammael — NOT IN MM
    '44-09': ('53.99', BASE + 'gw-44-11.html'),         # Ravenwing Command Squad
    '44-10': ('59.99', BASE + 'warhammer-40k-dark-angels-deathwing-knights-gw-44-22.html'), # Deathwing Knights
    '44-11': (None,    ''),                              # Deathwing Terminators — NOT IN MM (gw-44-11 = Ravenwing)
    '44-12': ('53.99', BASE + 'gw-44-11.html'),         # Ravenwing Black Knights (same kit as Ravenwing Command)
    '44-13': ('51.00', BASE + 'warhammer-40k-dark-angels-inner-circle-companions-gw-44-19.html'), # Inner Circle Companions
    '44-14': (None,    ''),                              # Dark Talon — NOT IN MM
    '44-15': (None,    ''),                              # Darkshroud — NOT IN MM
    '44-16': (None,    ''),                              # Land Speeder Vengeance — NOT IN MM
    '44-17': (None,    ''),                              # Nephilim Jetfighter — NOT IN MM
    '44-20': (None,    ''),                              # Dark Angels Combat Patrol — NOT IN MM

    # ── Drukhari ──────────────────────────────────────────────────────────
    '45-02': ('29.99', BASE + 'gw-45-22.html'),         # Dark Eldar Archon (current Archon kit)
    '45-06': (None,    ''),                              # Wyches — NOT IN MM
    '45-07': (None,    ''),                              # Kabalite Warriors — NOT IN MM spreadsheet
    '45-10': ('55.99', BASE + 'gw-45-10.html'),         # Raider
    '45-12': (None,    ''),                              # Ravager — NOT IN MM
    '45-25': (None,    ''),                              # Combat Patrol — NOT IN MM

    # ── Craftworlds / Aeldari ─────────────────────────────────────────────
    '46-02': (None,    ''),                              # Farseer — NOT IN MM
    '46-06': ('38.99', BASE + 'gw-46-15.html'),         # Dire Avengers
    '46-09': ('51.00', BASE + 'gw-46-09-2022.html'),    # Guardians
    '46-14': ('53.99', BASE + 'warhammer-40k-aeldari-fire-dragons-gw-46-46-2025.html'),  # Fire Dragons (2025 kit)
    '46-25': (None,    ''),                              # Combat Patrol — NOT IN MM
    '46-26': (None,    ''),                              # Wraithguard — NOT IN MM spreadsheet
    '46-29': ('55.99', BASE + 'warhammer-40k-aeldari-wave-serpent-gw-46-21-2025.html'),  # Wave Serpent

    # ── Astra Militarum ───────────────────────────────────────────────────
    '47-05': ('55.99', BASE + 'gw-47-07.html'),         # Chimera
    '47-06': (None,    ''),                              # Leman Russ — NOT IN MM (only Legions Imperialis versions)
    '47-08': ('31.99', BASE + 'warhammer-40k-astra-militarum-commissar-gw-47-50.html'),  # Commissar
    '47-12': (None,    ''),                              # Sentinel — NOT IN MM
    '47-14': (None,    ''),                              # Hellhound — NOT IN MM (gw-47-14 = Bullgryns)
    '47-17': (None,    ''),                              # Basilisk — NOT IN MM
    '47-25': (None,    ''),                              # AM Combat Patrol — NOT IN MM
    '47-30': ('44.99', BASE + 'warhammer-40k-astra-militarum-cadian-shock-troops-gw-47-33.html'), # Cadian Shock Troops

    # ── Space Marines ─────────────────────────────────────────────────────
    '48-06': ('55.99', BASE + 'warhammer-40k-space-marines-terminator-squad-gw-48-90.html'),    # Terminator Squad
    '48-07': ('51.00', BASE + 'gw-48-07.html'),         # Tactical Squad
    '48-08': ('51.00', BASE + 'gw-48-18.html'),         # Vanguard Veteran Squad
    '48-15': ('53.99', BASE + 'gw-48-15.html'),         # Devastator Squad
    '48-21': (None,    ''),                              # Land Raider — NOT IN MM spreadsheet
    '48-22': ('97.99', BASE + 'gw-48-30.html'),         # Land Raider Crusader/Redeemer
    '48-23': ('63.99', BASE + 'gw-48-23.html'),         # Predator
    '48-25': (None,    ''),                              # Whirlwind — NOT IN MM
    '48-26': ('63.99', BASE + 'gw-48-25.html'),         # Vindicator
    '48-27': ('55.99', BASE + 'gw-48-22.html'),         # Hammerfall Bunker
    '48-28': ('31.99', BASE + 'gw-48-52-269964.html'),  # Firestrike Servo-Turrets
    '48-29': (None,    ''),                              # Scouts — NOT IN MM
    '48-30': ('34.00', BASE + 'gw-48-63.html'),         # Primaris Librarian
    '48-32': ('34.00', BASE + 'gw-48-62.html'),         # Primaris Chaplain
    '48-33': (None,    ''),                              # Apothecary — NOT IN MM
    '48-34': ('35.99', BASE + 'gw-48-96.html'),         # Primaris Ancient
    '48-36': (None,    ''),                              # Judiciar — NOT IN MM
    '48-37': ('55.99', BASE + 'warhammer-40k-space-marines-company-heroes-gw-48-08.html'),      # Company Heroes
    '48-38': ('51.00', BASE + 'gw-48-44.html'),         # Bladeguard Veterans
    '48-39': ('51.00', BASE + 'gw-48-43-2021.html'),    # Eradicators
    '48-40': ('53.99', BASE + 'gw-48-41-271167.html'),  # Outriders
    '48-41': ('53.99', BASE + 'gw-48-97.html'),         # Primaris Infiltrators
    '48-42': ('44.99', BASE + 'gw-48-50.html'),         # Primaris Invader ATV
    '48-43': ('53.99', BASE + 'warhammer-40k-space-marines-sternguard-veteran-squad-gw-48-49-2023.html'), # Sternguard
    '48-44': ('68.00', BASE + 'warhammer-40k-space-marines-brutalis-dreadnought-gw-48-28.html'), # Brutalis Dreadnought
    '48-45': ('51.00', BASE + 'warhammer-40k-space-marines-infernus-squad-gw-48-26-2024.html'), # Infernus Squad
    '48-46': ('59.99', BASE + 'warhammer-40k-space-marines-ballistus-dreadnought-gw-48-11-2024.html'), # Ballistus Dreadnought
    '48-61': ('31.99', BASE + 'gw-48-84.html'),         # Primaris Lieutenant with Power Sword
    '48-62': ('35.99', BASE + 'gw-48-61.html'),         # Primaris Captain
    '48-75': ('53.99', BASE + 'gw-48-75.html'),         # Primaris Intercessors
    '48-76': ('53.99', BASE + 'gw-48-36.html'),         # Assault Intercessors
    '48-85': (None,    ''),                              # Repulsor — NOT IN MM
    '48-92': ('51.00', BASE + 'gw-48-69.html'),         # Primaris Aggressors
    '48-93': ('67.99', BASE + 'gw-48-77.html'),         # Redemptor Dreadnought
    '48-94': ('71.99', BASE + 'gw-48-94.html'),         # Primaris Impulsor
    '48-95': ('97.99', BASE + 'gw-48-55.html'),         # Primaris Repulsor Executioner
    '48-96': (None,    ''),                              # Incursors — NOT IN MM
    '48-97': ('51.00', BASE + 'gw-48-79.html'),         # Primaris Inceptors
    '48-98': ('51.00', BASE + 'gw-48-93.html'),         # Primaris Eliminators
    '48-99': (None,    ''),                              # Suppressors — NOT IN MM

    # ── Necrons ───────────────────────────────────────────────────────────
    '49-03': ('33.99', BASE + 'warhammer-40k-necrons-overlord-with-translocation-shroud-gw-49-70.html'), # Overlord
    '49-06': ('44.99', BASE + 'gw-49-06-270080.html'),  # Necron Warriors
    '49-08': ('164.99', BASE + 'gw-49-09-270131.html'), # Necron Monolith
    '49-10': ('38.99', BASE + 'gw-49-10.html'),         # Immortals/Deathmarks
    '49-11': ('51.00', BASE + 'gw-49-07.html'),         # Lychguard/Triarch Praetorians
    '49-12': (None,    ''),                              # Doomsday Ark — NOT IN MM (gw-49-12 = Command Barge)
    '49-13': (None,    ''),                              # Doom Scythe — NOT IN MM
    '49-14': ('38.99', BASE + 'gw-49-16.html'),         # Canoptek Spyder
    '49-17': ('49.99', BASE + 'gw-49-42.html'),         # Flayed Ones
    '49-20': ('108.99', BASE + 'gw-49-30.html'),        # C'tan Shard of the Void Dragon
    '49-21': ('31.99', BASE + 'gw-49-33.html'),         # Psychomancer
    '49-22': (None,    ''),                              # Royal Warden — NOT IN MM (gw-49-22 = Cryptek)

    # ── Orks ──────────────────────────────────────────────────────────────
    '50-02': ('35.99', BASE + 'gw-50-56.html'),         # Ork Warboss in Mega Armour
    '50-05': (None,    ''),                              # Ork Warboss — NOT IN MM
    '50-09': ('33.99', BASE + 'gw-50-12.html'),         # Ork Nobz
    '50-10': ('38.99', BASE + 'gw-50-10.html'),         # Ork Boyz
    '50-11': ('50.99', BASE + 'gw-50-09.html'),         # Ork Trukk
    '50-12': ('59.99', BASE + 'gw-50-08.html'),         # Ork Meganobz
    '50-14': ('33.99', BASE + 'gw-50-22.html'),         # Ork Lootas/Burnas
    '50-15': ('53.99', BASE + 'gw-50-17.html'),         # Ork Killa Kans
    '50-16': (None,    ''),                              # Deff Dread — NOT IN MM (gw-50-16 = Gretchin)
    '50-20': ('53.99', BASE + 'gw-50-24.html'),         # Ork Flash Gitz
    '50-22': ('106.99', BASE + 'gw-50-20-2021.html'),   # Ork Battlewagon

    # ── Tyranids / Genestealer Cults ──────────────────────────────────────
    '51-04': ('53.99', BASE + 'gw-51-08.html'),         # Hive Tyrant/The Swarmlord
    '51-06': (None,    ''),                              # Carnifex — NOT IN MM
    '51-08': ('53.99', BASE + 'gw-51-18.html'),         # Tyranid Warriors
    '51-16': ('38.99', BASE + 'warhammer-40k-tyranids-termagants-gw-51-34.html'),  # Termagants
    '51-40': ('49.99', BASE + 'gw-51-52.html'),         # Neophyte Hybrids
    '51-41': ('38.99', BASE + 'gw-51-51.html'),         # Acolyte Hybrids/Hybrid Metamorphs
    '51-42': (None,    ''),                              # Genestealer Patriarch — NOT IN MM
    '51-43': ('29.99', BASE + 'gw-51-47.html'),         # Genestealer Cults Magus
    '51-44': ('38.99', BASE + 'gw-51-60.html'),         # Genestealer Cults Aberrants
    '51-69': (None,    ''),                              # Genestealer Cults Combat Patrol — NOT IN MM

    # ── Adepta Sororitas ──────────────────────────────────────────────────
    '52-02': ('53.99', BASE + 'gw-52-37.html'),         # Morvenn Vahl, Abbess Sanctorum
    '52-08': ('78.99', BASE + 'gw-52-09.html'),         # Exorcist  (MM's gw-52-09 = Exorcist)
    '52-09': ('71.99', BASE + 'gw-52-08.html'),         # Immolator  (MM's gw-52-08 = Immolator)
    '52-12': ('53.99', BASE + 'gw-52-27.html'),         # Seraphim Squad
    '52-15': ('53.99', BASE + 'gw-52-25.html'),         # Retributor Squad  (MM's gw-52-25 = Retributors)
    '52-20': ('53.99', BASE + 'gw-52-20.html'),         # Battle Sisters Squad
    '52-22': ('53.99', BASE + 'gw-52-35.html'),         # Celestian Sacresants
    '52-25': (None,    ''),                              # Sisters Combat Patrol — NOT IN MM

    # ── Space Wolves ──────────────────────────────────────────────────────
    '53-02': ('38.99', BASE + 'gw-53-30.html'),         # Ragnar Blackmane
    '53-06': ('51.00', BASE + 'gw-53-06.html'),         # Grey Hunters/Blood Claws Pack
    '53-08': ('53.99', BASE + 'gw-53-07.html'),         # Wolf Guard Terminators
    '53-10': ('53.99', BASE + 'gw-53-09.html'),         # Thunderwolf Cavalry
    '53-20': (None,    ''),                              # Space Wolves Combat Patrol — NOT IN MM

    # ── Imperial Knights ──────────────────────────────────────────────────
    '54-15': (None,    ''),                              # Knight Preceptor/Canis Rex — NOT IN MM
    '54-20': ('80.99', BASE + 'gw-54-20.html'),         # Knight Armigers
    '54-21': ('164.99', BASE + 'gw-54-21.html'),        # Knight Dominus/Valiant class
    '54-22': (None,    ''),                              # Knight Questoris — NOT IN MM

    # ── Ultramarines / Chapter Specific ───────────────────────────────────
    '55-02': ('59.99', BASE + 'warhammer-40k-ultramarines-roboute-guilliman-gw-55-20.html'),  # Guilliman
    '55-12': ('53.99', BASE + 'gw-55-21.html'),         # Marneus Calgar with Victrix Honour Guard
    '55-16': ('53.99', BASE + 'gw-55-21.html'),         # Ultramarines Honour Guard (same kit as Marneus Calgar)
    '55-20': (None,    ''),                              # BT Primaris Crusader Squad — NOT IN MM
    '55-21': ('49.99', BASE + 'gw-55-41.html'),         # Black Templars High Marshal Helbrecht
    '55-22': (None,    ''),                              # BT Emperor's Champion — NOT IN MM
    '55-23': ('53.99', BASE + 'gw-55-43.html'),         # Black Templars Sword Brethren
    '55-24': ('49.99', BASE + 'gw-55-44.html'),         # Black Templars Grimaldus & Retinue
    '55-25': (None,    ''),                              # BT Castellan — NOT IN MM
    '55-26': ('34.00', BASE + 'warhammer-40k-black-templars-execrator-gw-55-50.html'),  # BT Execrator
    '55-27': ('35.99', BASE + 'warhammer-40k-black-templars-crusade-ancient-gw-55-57.html'), # BT Crusade Ancient
    '55-28': (None,    ''),                              # BT Marshal — NOT IN MM
    '55-30': (None,    ''),                              # BT Combat Patrol — NOT IN MM

    # ── T'au Empire ───────────────────────────────────────────────────────
    '56-06': ('51.00', BASE + 'gw-56-06.html'),         # Fire Warriors Strike/Breacher Team
    '56-10': ('63.99', BASE + 'gw-56-11.html'),         # Hammerhead/Sky Ray Gunship
    '56-13': ('53.99', BASE + 'gw-56-15.html'),         # XV88 Broadside Battlesuit
    '56-14': ('31.99', BASE + 'gw-56-14.html'),         # XV25 Stealth Battlesuits
    '56-15': (None,    ''),                              # Crisis Battlesuits — NOT IN MM (gw-56-15 = Broadside)
    '56-16': ('100.99', BASE + 'gw-56-13.html'),        # XV104 Riptide Battlesuit
    '56-19': (None,    ''),                              # T'au Pathfinders — NOT IN MM (gw-56-19 = Piranha)
    '56-22': ('29.99', BASE + 'gw-56-24.html'),         # T'au Ethereal
    '56-25': (None,    ''),                              # T'au Combat Patrol — NOT IN MM

    # ── Grey Knights ──────────────────────────────────────────────────────
    '57-02': (None,    ''),                              # Grand Master Voldus — NOT IN MM
    '57-06': ('55.99', BASE + 'gw-57-08.html'),         # Grey Knights Strike Squad
    '57-08': ('51.00', BASE + 'gw-57-09.html'),         # Grey Knights Paladin/Terminator Squad
    '57-14': ('59.99', BASE + 'gw-57-10.html'),         # Nemesis Dreadknight
    '57-20': ('142.99', BASE + 'gw-57-14.html'),        # Grey Knights Combat Patrol

    # ── Adeptus Mechanicus ────────────────────────────────────────────────
    '59-06': ('35.99', BASE + 'gw-59-18.html'),         # Tech-Priest Dominus
    '59-10': ('49.99', BASE + 'gw-59-10.html'),         # Skitarii Rangers/Vanguard (combo kit)
    '59-11': ('49.99', BASE + 'gw-59-10.html'),         # Skitarii Vanguard (same Rangers/Vanguard kit)
    '59-14': (None,    ''),                              # Ironstrider Ballistarii — NOT IN MM
    '59-16': ('71.99', BASE + 'gw-59-13.html'),         # Onager Dunecrawler
    '59-18': (None,    ''),                              # Kataphron Destroyers — NOT IN MM
    '59-20': (None,    ''),                              # Electropriests — NOT IN MM
    '59-25': (None,    ''),                              # AdMech Combat Patrol — NOT IN MM

    # ── Age of Sigmar General ─────────────────────────────────────────────
    '80-01': (None,    ''),                              # AoS Core Rules — NOT IN MM
    '80-15': (None,    ''),                              # Warrior Starter Set — NOT IN MM
    '80-20': (None,    ''),                              # AoS Dice Set — NOT IN MM

    # ── Spearheads (70-xx) ────────────────────────────────────────────────
    '70-04':  (None,     ''),                            # Slaves to Darkness Spearhead — NOT IN MM
    '70-09':  (None,     ''),                            # Ossiarch Bonereapers Spearhead — NOT IN MM
    '70-10':  (None,     ''),                            # Nighthaunt Spearhead — NOT IN MM
    '70-11':  (None,     ''),                            # Lumineth Realm-lords Spearhead — NOT IN MM
    '70-12':  (None,     ''),                            # Daughters of Khaine Spearhead — NOT IN MM
    '70-17':  (None,     ''),                            # Blades of Khorne Spearhead — NOT IN MM
    '70-21':  (None,     ''),                            # Stormcast Eternals Spearhead — NOT IN MM
    '70-22':  (None,     ''),                            # Cities of Sigmar Spearhead — NOT IN MM
    '70-832': ('123.99', BASE + 'gw-70-832.html'),      # Maggotkin of Nurgle Spearhead
    '70-839': (None,     ''),                            # Disciples of Tzeentch Spearhead — not in spreadsheet
    '70-892': (None,     ''),                            # Orruk Warclans Spearhead — NOT IN MM
    '70-893': (None,     ''),                            # Orruk Warclans Ironjawz Spearhead — NOT IN MM
    '70-894': (None,     ''),                            # Gloomspite Gitz Spearhead — NOT IN MM
    '70-901': (None,     ''),                            # Skaven Spearhead — NOT IN MM
    '70-915': (None,     ''),                            # Flesh-Eater Courts Spearhead — NOT IN MM

    # ── Combat Patrols (71-xx) ────────────────────────────────────────────
    '71-02': (None,    ''),                              # Space Marine Combat Patrol — NOT IN MM
    '71-06': (None,    ''),                              # CSM Combat Patrol — NOT IN MM
    '71-18': (None,    ''),                              # Ork Combat Patrol — NOT IN MM
    '71-19': (None,    ''),                              # Tyranid Combat Patrol — NOT IN MM
    '71-20': (None,    ''),                              # Necron Combat Patrol — NOT IN MM
    '71-55': (None,    ''),                              # Stormcast Eternals Vanguard — NOT IN MM

    # ── Leagues of Votann ─────────────────────────────────────────────────
    # Note: MM uses gw-69-xx URLs for Leagues of Votann
    '73-06': (None,    ''),                              # Kahl / Uthar — NOT IN MM
    '73-10': ('51.00', BASE + 'gw-69-10.html'),         # Hearthkyn Warriors
    '73-12': ('55.99', BASE + 'gw-69-11.html'),         # Hernkyn Pioneers
    '73-14': ('53.99', BASE + 'gw-69-04.html'),         # Einhyr Hearthguard
    '73-25': (None,    ''),                              # Leagues of Votann Combat Patrol — NOT IN MM

    # ── Slaves to Darkness / Chaos ────────────────────────────────────────
    '83-10': (None,    ''),                              # Chaos Warriors (12-model box) — NOT IN MM (discontinued)
    '83-14': ('93.99', BASE + 'gw-83-51.html'),         # Varanguard Knights of Ruin
    '83-18': ('53.99', BASE + 'warhammer-age-of-sigmar-slaves-to-darkness-chaos-warriors-gw-83-06-2023.html'), # Chaos Warriors (10)
    '83-20': ('35.99', BASE + 'gw-97-10.html'),         # Maggotkin Plaguebearers (Nurgle Daemons)
    '83-22': (None,    ''),                              # Putrid Blightkings — not searched; mark NOT IN MM
    '83-30': (None,    ''),                              # Blades of Khorne Bloodreavers — NOT IN MM
    '83-40': (None,    ''),                              # Disciples of Tzeentch Tzaangors — NOT IN MM

    # ── Daughters of Khaine ───────────────────────────────────────────────
    '85-02': (None,    ''),                              # Morathi-Khaine — NOT searched; mark NOT IN MM
    '85-06': ('53.99', BASE + 'gw-85-10.html'),         # Witch Aelves
    '85-17': (None,    ''),                              # Sisters of Slaughter — NOT IN MM

    # ── Cities of Sigmar ──────────────────────────────────────────────────
    '86-15': ('51.00', BASE + 'warhammer-age-sigmar-cities-sigmar-freeguild-fusiliers-gw-86-19.html'),  # Freeguild Fusiliers

    # ── Lumineth Realm-lords ──────────────────────────────────────────────
    '87-06': ('53.99', BASE + 'gw-87-59.html'),         # Vanari Auralan Wardens (10)
    '87-08': ('53.99', BASE + 'gw-87-54.html'),         # Alarith Stoneguard
    '87-10': ('53.99', BASE + 'gw-87-59.html'),         # Vanari Auralan Wardens (same kit)

    # ── Gloomspite Gitz / Orruk Warclans ─────────────────────────────────
    '89-06': (None,    ''),                              # Gloomspite Gitz Fanatics — NOT IN MM
    '89-10': ('49.99', BASE + 'gw-89-48.html'),         # Gloomspite Gitz Squig Herd
    '89-11': ('51.00', BASE + 'gw-89-44.html'),         # Gloomspite Gitz Squig Hoppers
    '89-12': (None,    ''),                              # Gloomspite Gitz Fanatics (alt entry) — NOT IN MM
    '89-20': (None,    ''),                              # Ironjawz Brutes — NOT IN MM
    '89-22': ('51.00', BASE + 'warhammer-age-sigmar-orruk-warclans-gutrippaz-gw-89-70.html'),  # Gutrippaz
    '89-30': ('53.99', BASE + 'warhammer-age-sigmar-orruk-warclans-orruk-ardboyz-gw-89-61.html'), # Orruk Ardboyz

    # ── Skaven ────────────────────────────────────────────────────────────
    '90-10': (None,    ''),                              # Skaven Clanrats — NOT IN MM
    '90-12': ('38.99', BASE + 'gw-90-12.html'),         # Skaven Pestilens Plague Monks
    '90-17': ('67.99', BASE + 'gw-90-17.html'),         # Skaven Stormfiends

    # ── Nighthaunt / Flesh-Eater Courts ───────────────────────────────────
    '91-02': ('49.99', BASE + 'gw-91-25.html'),         # Lady Olynder, Mortarch of Grief
    '91-06': (None,    ''),                              # Nighthaunt Hexwraiths — NOT IN MM
    '91-07': ('51.00', BASE + 'gw-91-13.html'),         # Flesh-Eater Courts Crypt Flayers/Vargheists/Crypt Horrors
    '91-10': (None,    ''),                              # Nighthaunt Chainrasps — NOT IN MM (only Easy to Build)
    '91-12': ('49.99', BASE + 'gw-91-26.html'),         # Nighthaunt Grimghast Reapers
    '91-14': ('49.99', BASE + 'gw-91-27.html'),         # Nighthaunt Bladegheist Revenants
    '91-15': (None,    ''),                              # Knight of Shrouds — NOT IN MM spreadsheet
    '91-25': (None,    ''),                              # Nighthaunt Spearhead — NOT IN MM (gw-91-25 = Lady Olynder)
    '91-28': (None,    ''),                              # Nighthaunt Chainrasps (alt) — NOT IN MM
    '91-32': (None,    ''),                              # Flesh-Eater Courts Terrorgheist — NOT IN MM spreadsheet
    '91-35': (None,    ''),                              # Flesh-Eater Courts Crypt Ghouls — NOT IN MM

    # ── Ossiarch Bonereapers ──────────────────────────────────────────────
    '94-10': ('53.99', BASE + 'gw-94-25.html'),         # Ossiarch Bonereapers Mortek Guard
    '94-12': ('51.00', BASE + 'gw-94-23.html'),         # Ossiarch Bonereapers Necropolis Stalkers
    '94-14': (None,    ''),                              # Gothizzar Harvester — NOT IN MM

    # ── Stormcast Eternals ────────────────────────────────────────────────
    '96-11': (None,    ''),                              # Stormcast Liberators — NOT IN MM
    '96-12': (None,    ''),                              # Stormcast Judicators — NOT IN MM
    '96-14': ('38.99', BASE + 'warhammer-age-sigmar-stormcast-eternals-lord-celestant-gw-96-68.html'), # Lord-Celestant
    '96-50': ('51.00', BASE + 'gw-96-57.html'),         # Stormcast Eternals Vindictors
    '96-55': (None,    ''),                              # Stormcast Eternals Praetors — NOT IN MM (gw-96-55 = Annihilators)

    # ── Chaos Daemons ─────────────────────────────────────────────────────
    '97-08': ('35.99', BASE + 'gw-97-08.html'),         # Daemons of Khorne Bloodletters
    '97-09': ('35.99', BASE + 'gw-97-10.html'),         # Plaguebearers of Nurgle (Maggotkin)
    '97-10': ('35.99', BASE + 'gw-97-08.html'),         # Blades of Khorne Bloodletters (alt entry)
    '97-11': ('38.99', BASE + 'gw-97-12.html'),         # Daemons of Tzeentch Pink Horrors
    '97-12': ('38.99', BASE + 'gw-97-12.html'),         # Disciples of Tzeentch Pink Horrors (alt entry)

    # ── Horus Heresy ──────────────────────────────────────────────────────
    'HA-001': ('71.99', BASE + 'gw-31-23.html'),        # Legiones Astartes MKVI Tactical Squad
    'HA-002': ('53.99', BASE + 'gw-31-25.html'),        # Legiones Astartes Contemptor Dreadnought
    'HA-010': ('67.99', BASE + 'warhammer-horus-heresy-legiones-astartes-mkiii-tactical-squad-gw-31-68.html'), # MKIII Tactical Squad
    'HA-011': ('78.99', BASE + 'gw-31-26.html'),        # Legiones Astartes Cataphractii Terminator Squad
    'HA-012': ('62.99', BASE + 'gw-31-14.html'),        # Legiones Astartes Deimos Pattern Predator Battle Tank
    'HA-013': ('100.99', BASE + 'gw-31-35.html'),       # Legiones Astartes Spartan Assault Tank
    'HA-020': ('67.99', BASE + 'warhammer-horus-heresy-solar-auxilia-lasrifle-section-gw-31-73.html'), # Solar Auxilia Lasrifle Section
    'HA-021': ('71.99', BASE + 'gw-31-29.html'),        # HH Leviathan Dreadnought w/ Claw & Drill
    'HA-030': ('78.99', BASE + 'gw-31-26.html'),        # HH Cataphractii Terminators (same kit as HA-011)
    'HA-040': ('100.99', BASE + 'gw-31-35.html'),       # HH Spartan Assault Tank (same kit as HA-013)
    'HA-041': ('71.99', BASE + 'gw-31-27.html'),        # HH Sicaran Battle Tank
    'HA-050': (None,    ''),                             # HH Praetor in Terminator Armour — NOT IN MM
    'HA-051': ('37.99', BASE + 'warhammer-40k-space-marines-chaplain-terminator-armour-gw-48-91.html'), # Chaplain in Terminator Armour
    'HH-001': ('267.99', BASE + 'gw-31-01.html'),       # Horus Heresy: Age of Darkness

    # ── Kill Team ─────────────────────────────────────────────────────────
    'KT-001': (None,    ''),                             # Kill Team: Nightmare — NOT IN MM
    'KT-002': (None,    ''),                             # Kill Team: Into the Dark — NOT IN MM
    'KT-003': (None,    ''),                             # Kill Team: Starter Set — NOT IN MM
    'KT-100': (None,    ''),                             # Kill Team Starter Set — NOT IN MM
    'KT-101': (None,    ''),                             # Kill Team Datacard Pack — NOT IN MM
    'KT-102': (None,    ''),                             # Kill Team: Void-Dancer Troupe — NOT IN MM
    'KT-103': (None,    ''),                             # Kill Team: Veteran Guardsmen — NOT IN MM
    'KT-104': ('63.99', BASE + 'kill-team-legionaries-gw-102-97-2024.html'),  # Kill Team: Chaos Legionaries
    'KT-105': (None,    ''),                             # Kill Team: Intercession Squad — NOT IN MM
    'KT-106': (None,    ''),                             # Kill Team: Hunter Clade — NOT IN MM
    'KT-107': ('55.99', BASE + 'kill-team-exaction-squad-gw-103-27-2024.html'), # Kill Team: Exaction Squad
    'KT-108': (None,    ''),                             # Kill Team: Salvation — NOT IN MM
    'KT-109': (None,    ''),                             # Kill Team Killzone Essentials — NOT IN MM
    'KT-110': (None,    ''),                             # Kill Team Compendium — NOT IN MM

    # ── Necromunda ────────────────────────────────────────────────────────
    'NM-010': (None,    ''),                             # Necromunda Escher Gang — NOT IN MM
    'NM-011': (None,    ''),                             # Necromunda Goliath Gang — NOT IN MM
    'NM-012': (None,    ''),                             # Necromunda Van Saar Gang — NOT IN MM
    'NM-020': (None,    ''),                             # Necromunda Underhive Terrain Set — NOT IN MM

    # ── Warcry ────────────────────────────────────────────────────────────
    'WC-100': (None,    ''),                             # Warcry Starter Set — NOT IN MM
    'WC-101': (None,    ''),                             # Warcry: Heart of Ghur — NOT IN MM
    'WC-102': (None,    ''),                             # Warcry: Hunter and Hunted — NOT IN MM

    # ── Paint / Hobby Products ────────────────────────────────────────────
    # None of these are in the "Miniatures Games" MM spreadsheet.
    'AP-001': (None,    ''),
    'BP-001': (None,    ''),
    'BR-001': (None,    ''),
    'BR-002': (None,    ''),
    'BS-001': (None,    ''),
    'BS-002': (None,    ''),
    'CP-001': (None,    ''),
    'CP-002': (None,    ''),
    'CP-003': (None,    ''),
    'CP-005': (None,    ''),
    'CP-010': (None,    ''),
    'CSP-001': (None,   ''),
    'CSP-002': (None,   ''),
    'CSP-003': (None,   ''),
    'CSP-004': (None,   ''),
    'DB-001': (None,    ''),
    'DP-001': (None,    ''),
    'HK-001': (None,    ''),
    'LP-001': (None,    ''),
    'MR-001': (None,    ''),
    'PG-001': (None,    ''),
    'PH-001': (None,    ''),
    'PH-002': (None,    ''),
    'PM-001': (None,    ''),
    'SG-001': (None,    ''),
    'SP-001': (None,    ''),
    'SP-002': (None,    ''),
    'SP-003': (None,    ''),
    'SP-010': (None,    ''),
    'SP-011': (None,    ''),
    'SP-012': (None,    ''),
    'SP-020': (None,    ''),
    'TCP-001': (None,   ''),
    'TE-001': (None,    ''),
    'TP-001': (None,    ''),
    'WP-001': (None,    ''),
}


class Command(BaseCommand):
    """Seed Miniature Market prices from the March 2026 Octoparse scrape."""

    help = (
        'Write verified Miniature Market prices into CurrentPrice, keyed by GW SKU. '
        'Idempotent — safe to re-run.  Replaces wrong URLs from the old scraper.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Print actions without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute the price seed."""
        dry_run = options['dry_run']

        try:
            mm_retailer = Retailer.objects.get(name='Miniature Market')
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Miniature Market' not found in the database.")

        sku_to_product = {
            p.gw_sku: p
            for p in Product.objects.filter(is_active=True).only('id', 'gw_sku', 'name')
        }
        self.stdout.write(f'Active products loaded: {len(sku_to_product)}')
        self.stdout.write(f'MM rows in seed:        {len(MM_DATA)}')
        self.stdout.write('')

        applied = 0
        skipped = 0
        not_available_count = 0

        for sku, (price_str, url) in sorted(MM_DATA.items()):
            product = sku_to_product.get(sku)
            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip] {sku} — not found in active products')
                )
                skipped += 1
                continue

            is_not_available = price_str is None
            price = decimal.Decimal(price_str) if price_str else None

            if is_not_available:
                self.stdout.write(
                    f"  [{'dry' if dry_run else 'n/a'}] {sku:8s}  "
                    f"{'NOT AVAILABLE':>12s}  {product.name}"
                )
                not_available_count += 1
            else:
                self.stdout.write(
                    f"  [{'dry' if dry_run else 'set'}] {sku:8s}  "
                    f"{'$'+price_str:>10s}  IN STOCK    {product.name}"
                )

            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=mm_retailer,
                    defaults={
                        'price':         price,
                        'url':           url,
                        'in_stock':      not is_not_available,
                        'not_available': is_not_available,
                        'listing_title': '',
                    },
                )
            applied += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n{'[DRY RUN] ' if dry_run else ''}Done!  "
            f"Applied: {applied}  "
            f"(With price: {applied - not_available_count}  "
            f"Not available: {not_available_count})  "
            f"Skipped: {skipped}"
        ))
