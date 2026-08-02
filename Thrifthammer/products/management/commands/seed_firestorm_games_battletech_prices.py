"""
Seed Firestorm Games UK prices for BattleTech, and derive a UK-side
Catalyst Game Labs GBP reference price from Firestorm's RRP.

SPECIAL CASE (explicit one-time user instruction per category, same
pattern as Malifaux -- not a default for future categories): unlike
every other seed_firestorm_games_*_prices command, this one DOES
overwrite product.msrp_gbp, using Firestorm's RRP (the higher,
struck-through price on each listing). No GBP MSRP source exists for
BattleTech (msrp_gbp was null for all 114 DB SKUs going in), so
Firestorm's real GBP RRP is used as the reference price instead.

This command ALSO writes a SEPARATE new UK-flagged retailer,
catalyst-game-labs-uk, priced at that same Firestorm RRP in GBP, using
the URL already stored on the existing US `catalyst-game-labs`
retailer's CurrentPrice row (the publisher's own store has no separate
UK storefront). It NEVER touches the existing `catalyst-game-labs` (US,
is_uk=False, USD) retailer or its CurrentPrice rows -- those are
read-only here, only used as a URL source. It also never touches any
other existing BattleTech file.

The `firestorm-games` CurrentPrice row follows the normal pattern used
for every other category this session: the lower (sale) price, GBP,
linking to Firestorm's own product page with the affiliate code. One
exception: BT-024 "Alpha Strike (2022 Box Set)" shows only a single
£87.99 price on Firestorm (no struck-through RRP) -- that single price
is used for both the sale price and the RRP/msrp_gbp value.

https://www.firestormgames.co.uk/wargames-miniatures/battletech
84/114 active DB BT-XXX SKUs matched. Unlike other Firestorm categories
this page has no sub-category headings and no cross-listing -- every
listing appeared exactly once.

The "___ Lance" / "___ Star" ForcePack naming required care: Firestorm
drops the "ForcePack:" prefix the DB uses (e.g. DB "ForcePack: Black
Remnant Command Lance" = Firestorm "Black Remnant Command Lance"), and
several factions/lances share near-identical names at the same price
(e.g. House Davion Heavy Battle Lance vs House Davion Cavalry Lance) --
each was verified by the distinguishing faction/lance-type word, not
price alone.

Matched despite a naming variant (verified by being the only candidate
at that price/theme, not a literal string match): BT-011 "A Game of
Armored Combat" -> Firestorm's "A Game of Armored Combat 40th
Anniversary" (same core rulebook, anniversary edition); BT-070 "Hansen's
Rough Riders" -> Firestorm "Hansens Roughriders" (spelling); BT-118
"Wolf Dragoon's Assault Star" -> Firestorm "Wolf's Dragoons Assault
Star" (word order); BT-115 "Clan Elementals" -> Firestorm "Elemental
Star" (Elementals are Clan battle armor, sold as an "Elemental Star"
unit pack).

Several DB SKUs intentionally share one catalyst-game-labs URL (e.g.
BT-098 through BT-106 all point to ".../battletech-forcepack-inner-sphere",
BT-107 through BT-115 to ".../battletech-forcepack-clan") -- Catalyst
sells those individual Lance/Star ForcePacks as a variant selector on a
single product page. This is pre-existing DB data, copied as-is.

Gaps (30, no Firestorm listing found under any name -- largely
individually-named/lettered BattleMats and MapPacks Firestorm doesn't
carry the full range of, plus premium miniatures, DropShips, and a
handful of sourcebooks):
- BT-003 Alpha Strike: Commander's Edition
- BT-004 Battle of Tukayyid (sourcebook; only the Map Pack version is
  carried, matched to BT-052)
- BT-008 BattleMat (Grasslands) -- 5 differently-lettered/themed
  "Grasslands" battlemats exist on Firestorm, none named plainly
  "Grasslands"; too ambiguous to pick one
- BT-013 A Time of War: The BattleTech RPG
- BT-016 BattleMat (Battles of Tukayyid)
- BT-017 BattleMat (Alien Worlds) -- only the Map Pack version is
  carried, matched to BT-041
- BT-018 Strategic Operations
- BT-019 Black Knight (Premium Miniature)
- BT-021 Hot Spots: Hinterlands
- BT-025 Phoenix Hawk (Premium Miniature)
- BT-031 Rifleman (Premium Miniature)
- BT-040 Mercenaries Box Set -- Firestorm only carries "Mercenaries:
  Paint Set", a different product
- BT-042 Union-Class Map Scale DropShip
- BT-046 MapPack: Deserts
- BT-048 Premium Miniature: BattleMaster
- BT-051 Overlord-Class Map Scale DropShip
- BT-054 CountersPack: BattleForce (only "Counters Pack - Alpha Strike"
  is carried, matched to BT-039)
- BT-057 BattleMat (Alpha Strike) -- 3 different Alpha-Strike-themed
  battlemats exist on Firestorm at the same price; too ambiguous
- BT-062 Overlord C-Class Map Scale Dropship
- BT-065 House Kurita Ranger Lance ForcePack (only the Command Lance is
  carried, matched to BT-044)
- BT-073 BattleMat: Twycross Plain of Curtains & Great Gash
- BT-084 BFM: Volcanic/Glacier
- BT-085 BattleMat: Legendary Battles Thunder Rift & Misery
- BT-090 MapPack: Volcanic
- BT-091 Somerset Strikers ForcePack
- BT-092 BattleTech Encounters
- BT-093 BattleMat: Fire and Ice 01: Erupting Canyon
- BT-094 BattleMat: Savannah Large Lakes
- BT-095 BattleMat: Savannah Desert Sinkholes
- BT-097 BattleMat: Fire and Ice 02: Magma Fjords
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'
_CATALYST_UK_SLUG = 'catalyst-game-labs-uk'
_FS_BASE = 'https://www.firestormgames.co.uk'
_FS_AFF = '?aff=6a4ab07d1c6f9'

# (gw_sku, label, firestorm_sale_gbp, firestorm_rrp_gbp, firestorm_path, catalyst_us_url)
_PRICES = [
    ('BT-006', 'Battletech - Beginner Box', Decimal('22.49'), Decimal('24.99'),
     '/battletech---beginner-box',
     'https://store.catalystgamelabs.com/products/battletech-beginner-box?_pos=6&_fid=715e41335&_ss=c'),
    ('BT-007', 'BattleTech: Campaign Operations', Decimal('30.59'), Decimal('33.99'),
     '/battletech:-campaign-operations',
     'https://store.catalystgamelabs.com/products/battletech-campaign-operations-pdf?_pos=8&_fid=715e41335&_ss=c'),
    ('BT-010', 'BattleTech - Clan Invasion Salvage - Blind Box', Decimal('6.79'), Decimal('7.99'),
     '/battletech---clan-invasion-salvage---blind-box',
     'https://store.catalystgamelabs.com/products/battletech-salvage-box-clan-invasion-full?_pos=11&_fid=715e41335&_ss=c'),
    ('BT-011', 'BattleTech: A Game of Armored Combat 40th Anniversary', Decimal('50.99'), Decimal('59.99'),
     '/battletech:-a-game-of-armored-combat-40th-anniversary',
     'https://store.catalystgamelabs.com/products/battletech-a-game-of-armored-combat?_pos=12&_fid=715e41335&_ss=c'),
    ('BT-012', 'Battletech: MechWarrior - Destiny', Decimal('30.59'), Decimal('33.99'),
     '/battletech:-mechwarrior---destiny',
     'https://store.catalystgamelabs.com/products/mechwarrior-destiny?_pos=13&_fid=715e41335&_ss=c'),
    ('BT-014', 'Battletech: Tactical Operations - Advanced Units & Equipment', Decimal('30.59'), Decimal('33.99'),
     '/battletech:-tactical-operations---advanced-units--equipment',
     'https://store.catalystgamelabs.com/products/battletech-tactical-operations-advanced-units-equipement?_pos=15&_fid=715e41335&_ss=c'),
    ('BT-015', 'Battletech: Tactical Operations - Advanced Rules', Decimal('30.59'), Decimal('33.99'),
     '/battletech:-tactical-operations---advanced-rules',
     'https://store.catalystgamelabs.com/products/battletech-tactical-operations-advanced-rules?_pos=16&_fid=715e41335&_ss=c'),
    ('BT-022', 'BattleTech: Star League Command Lance', Decimal('29.74'), Decimal('34.99'),
     '/battletech:-star-league-command-lance',
     'https://store.catalystgamelabs.com/products/battletech-star-league-command-lance?_pos=23&_fid=715e41335&_ss=c'),
    ('BT-023', 'BattleTech - Interstellar Operations Alternate Eras', Decimal('32.29'), Decimal('37.99'),
     '/battletech---interstellar-operations-alternate-eras',
     'https://store.catalystgamelabs.com/products/battletech-interstellar-operations-alternate-eras?_pos=24&_fid=715e41335&_ss=c'),
    ('BT-024', 'Battletech - Alpha Strike (2022 Box Set)', Decimal('87.99'), Decimal('87.99'),
     '/battletech---alpha-strike-2022-box-set',
     'https://store.catalystgamelabs.com/products/battletech-alpha-strike-box-set?_pos=25&_fid=715e41335&_ss=c'),
    ('BT-026', 'BattleTech - Interstellar Operations Battleforce', Decimal('35.69'), Decimal('41.99'),
     '/battletech---interstellar-operations-battleforce',
     'https://store.catalystgamelabs.com/products/battletech-interstellar-operations-battleforce?_pos=27&_fid=715e41335&_ss=c'),
    ('BT-027', 'BattleTech: Black Remnant Command Lance', Decimal('28.79'), Decimal('31.99'),
     '/battletech:-black-remnant-command-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-black-remnant-command-lance?_pos=28&_fid=715e41335&_ss=c'),
    ('BT-028', 'BattleTech: Second Star League Assault Lance', Decimal('40.49'), Decimal('44.99'),
     '/battletech:-second-star-league-assault-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-second-star-league-assault-lance?_pos=29&_fid=715e41335&_ss=c'),
    ('BT-029', 'BattleTech Battle Mat: Strana Mechty (Circle of Equals / Bloody Basin)', Decimal('35.99'), Decimal('39.99'),
     '/battletech-battle-mat:-strana-mechty-circle-of-equals--bloody-basin',
     'https://store.catalystgamelabs.com/products/battletech-battlemat-circle-of-equals?_pos=30&_fid=715e41335&_ss=c'),
    ('BT-030', 'BattleTech - Essentials Boxed Set', Decimal('21.24'), Decimal('24.99'),
     '/battletech---essentials-boxed-set',
     'https://store.catalystgamelabs.com/products/battletech-essentials?_pos=31&_fid=715e41335&_ss=c'),
    ('BT-032', 'BattleTech Aces: Scouring Sands Alpha Strike', Decimal('71.99'), Decimal('79.99'),
     '/battletech-aces:-scouring-sands-alpha-strike',
     'https://store.catalystgamelabs.com/products/battletech-aces-scouring-sands?_pos=33&_fid=715e41335&_ss=c'),
    ('BT-033', 'BattleTech: House Davion Heavy Battle Lance', Decimal('28.79'), Decimal('31.99'),
     '/battletech:-house-davion-heavy-battle-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-house-davion-heavy-battle-lance?_pos=34&_fid=715e41335&_ss=c'),
    ('BT-034', 'Battletech Salvage Box: UrbanMech LAM', Decimal('26.99'), Decimal('29.99'),
     '/battletech-salvage-box:-urbanmech-lam',
     'https://store.catalystgamelabs.com/products/battletech-salvage-box-urbanmech-lam?_pos=35&_fid=715e41335&_ss=c'),
    ('BT-035', 'BattleTech: Map Pack Grasslands', Decimal('26.99'), Decimal('29.99'),
     '/battletech:-map-pack-grasslands',
     'https://store.catalystgamelabs.com/products/map-set-grasslands?_pos=36&_fid=715e41335&_ss=c'),
    ('BT-036', 'BattleTech: Third Star League Strike Team', Decimal('41.39'), Decimal('45.99'),
     '/battletech:-third-star-league-strike-team',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-3rd-star-league-strike-team?_pos=37&_fid=715e41335&_ss=c'),
    ('BT-037', 'Battletech: Alpha Strike - Clan Invasion Cards', Decimal('17.99'), Decimal('19.99'),
     '/battletech:-alpha-strike---clan-invasion-cards',
     'https://store.catalystgamelabs.com/products/battletech-alpha-strike-clan-invasion-cards?_pos=38&_fid=715e41335&_ss=c'),
    ('BT-038', 'Battletech: UrbanMech Lance Force Pack', Decimal('26.99'), Decimal('29.99'),
     '/battletech:-urbanmech-lance-force-pack',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-urbanmech-lance?_pos=39&_fid=715e41335&_ss=c'),
    ('BT-039', 'BattleTech: Counters Pack - Alpha Strike', Decimal('22.49'), Decimal('24.99'),
     '/battletech:-counters-pack---alpha-strike',
     'https://store.catalystgamelabs.com/products/battletech-counterspack-alpha-strike?_pos=40&_fid=715e41335&_ss=c'),
    ('BT-041', 'Battletech - Map Pack Alien Worlds', Decimal('16.15'), Decimal('19.00'),
     '/battletech---map-pack-alien-worlds',
     'https://store.catalystgamelabs.com/products/mappack-alien-worlds?_pos=42&_fid=715e41335&_ss=c'),
    ('BT-043', 'Battletech BFM Desert / Grasslands', Decimal('134.99'), Decimal('149.99'),
     '/battletech-bfm-desert--grasslands',
     'https://store.catalystgamelabs.com/products/battletech-battlemat-bfm-grasslands-desert?_pos=44&_fid=715e41335&_ss=c'),
    ('BT-044', 'BattleTech: House Kurita Command Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech:-house-kurita-command-lance',
     'https://store.catalystgamelabs.com/products/battletech-house-kurita-command-lance-forcepack?_pos=45&_fid=715e41335&_ss=c'),
    ('BT-045', 'Battletech: Proliferation Cycle Boxed Set', Decimal('49.49'), Decimal('54.99'),
     '/battletech:-proliferation-cycle-boxed-set',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-proliferation-cycle?_pos=46&_fid=715e41335&_ss=c'),
    ('BT-047', 'BattleTech - Initiative Deck', Decimal('10.79'), Decimal('11.99'),
     '/battletech---initiative-deck',
     'https://store.catalystgamelabs.com/products/battletech-initiative-deck?_pos=48&_fid=715e41335&_ss=c'),
    ('BT-049', 'BattleTech: House Davion Cavalry Lance', Decimal('28.79'), Decimal('31.99'),
     '/battletech:-house-davion-cavalry-lance',
     'https://store.catalystgamelabs.com/products/battletech-house-davion-cavalry-lance-forcepack?_pos=50&_fid=715e41335&_ss=c'),
    ('BT-050', 'Battletech Battle Mat: Aerospace', Decimal('35.99'), Decimal('39.99'),
     '/battletech-battle-mat:-aerospace',
     'https://store.catalystgamelabs.com/products/battletech-battlemat-aerospace?_pos=51&_fid=715e41335&_ss=c'),
    ('BT-052', 'Battletech: Map Pack - Battle of Tukayyid', Decimal('26.24'), Decimal('34.99'),
     '/battletech:-map-pack---battle-of-tukayyid',
     'https://store.catalystgamelabs.com/products/battletech-mappack-battle-of-tukayyid?_pos=53&_fid=715e41335&_ss=c'),
    ('BT-053', 'BattleTech: Kell Hounds Striker Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech:-kell-hounds-striker-lance',
     'https://store.catalystgamelabs.com/products/battletech-kell-hounds-striker-lance?_pos=54&_fid=715e41335&_ss=c'),
    ('BT-055', 'BattleTech: Gray Death Legion Heavy Battle Lance', Decimal('30.59'), Decimal('33.99'),
     '/battletech:-gray-death-legion-heavy-battle-lance',
     'https://store.catalystgamelabs.com/products/battletech-gray-death-legion-heavy-battle-lance?_pos=56&_fid=715e41335&_ss=c'),
    ('BT-056', 'BattleTech: Battlefield Support - Battle & Fire Lances', Decimal('37.79'), Decimal('41.99'),
     '/battletech:-battlefield-support---battle--fire-lances',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-battle-fire-lances?_pos=57&_fid=715e41335&_ss=c'),
    ('BT-058', 'BattleTech: Gothic', Decimal('89.99'), Decimal('99.99'),
     '/battletech:-gothic',
     'https://store.catalystgamelabs.com/products/battletech-gothic?_pos=59&_fid=715e41335&_ss=c'),
    ('BT-059', 'BattleTech: Third Star League Battle Group', Decimal('41.39'), Decimal('45.99'),
     '/battletech:-third-star-league-battle-group',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-third-star-league-battle-group?_pos=60&_fid=715e41335&_ss=c'),
    ('BT-060', 'BattleTech: Battlefield Support Recon And Hunter Lances', Decimal('37.79'), Decimal('41.99'),
     '/battletech:-battlefield-support-recon-and-hunter-lances',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-recon-hunter-lances?_pos=61&_fid=715e41335&_ss=c'),
    ('BT-061', 'BattleTech: Northwind Highlanders Command Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech:-northwind-highlanders-command-lance',
     'https://store.catalystgamelabs.com/products/battletech-northwind-highlanders-command-lance?_pos=62&_fid=715e41335&_ss=c'),
    ('BT-063', 'Battletech: Legendary Mechwarriors III', Decimal('36.89'), Decimal('40.99'),
     '/battletech:-legendary-mechwarriors-iii',
     'https://store.catalystgamelabs.com/products/battletech-legendary-mechwarriors-iii-forcepack?_pos=64&_fid=715e41335&_ss=c'),
    ('BT-064', 'BattleTech: Clan Direct Fire Star', Decimal('35.09'), Decimal('38.99'),
     '/battletech:-clan-direct-fire-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan-direct-fire-star?_pos=65&_fid=715e41335&_ss=c'),
    ('BT-066', 'BattleTech - Inner Sphere Recon Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech---inner-sphere-recon-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere-recon-lance?_pos=67&_fid=715e41335&_ss=c'),
    ('BT-067', 'BattleTech - Inner Sphere Security Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech---inner-sphere-security-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere-security-lance?_pos=68&_fid=715e41335&_ss=c'),
    ('BT-068', 'BattleTech: McCarrons Armored Cavalry Assault Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech:-mccarrons-armored-cavalry-assault-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-mccarrons-armored-cavalry-assault-lance?_pos=69&_fid=715e41335&_ss=c'),
    ('BT-069', 'Battletech: Support Rifle And Command Lances', Decimal('36.89'), Decimal('40.99'),
     '/battletech:-support-rifle-and-command-lances',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-rifle-command-lances?_pos=70&_fid=715e41335&_ss=c'),
    ('BT-070', 'BattleTech Hansens Roughriders Battle Lance', Decimal('28.04'), Decimal('32.99'),
     '/battletech-hansens-roughriders-battle-lance',
     'https://store.catalystgamelabs.com/products/battletech-hansens-rough-riders-battle-lance?_pos=71&_fid=715e41335&_ss=c'),
    ('BT-071', 'BattleTech - Clan Cavalry Star', Decimal('35.09'), Decimal('38.99'),
     '/battletech---clan-cavalry-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan-cavalry-star?_pos=72&_fid=715e41335&_ss=c'),
    ('BT-072', 'BattleTech: Battlefield Support - Assault & Cavalry Lances', Decimal('37.79'), Decimal('41.99'),
     '/battletech:-battlefield-support---assault--cavalry-lances',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-assault-calvalry-lances?_pos=73&_fid=715e41335&_ss=c'),
    ('BT-074', 'Battletech: Map Pack Savannahs', Decimal('24.29'), Decimal('26.99'),
     '/battletech:-map-pack-savannahs',
     'https://store.catalystgamelabs.com/products/battletech-map-pack-savannahs?_pos=75&_fid=715e41335&_ss=c'),
    ('BT-075', 'Battletech: Battlefield Support Deck', Decimal('8.99'), Decimal('9.99'),
     '/battletech:-battlefield-support-deck',
     'https://store.catalystgamelabs.com/products/battletech-battlefield-support-deck-revised?_pos=76&_fid=715e41335&_ss=c'),
    ('BT-076', 'Battletech: Battlefield Support Emplacements', Decimal('40.49'), Decimal('44.99'),
     '/battletech:-battlefield-support-emplacements',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-support-emplacements?_pos=77&_fid=715e41335&_ss=c'),
    ('BT-077', 'Battletech: Map Pack City', Decimal('28.79'), Decimal('31.99'),
     '/battletech:-map-pack-city',
     'https://store.catalystgamelabs.com/products/battletech-map-pack-city?_pos=78&_fid=715e41335&_ss=c'),
    ('BT-078', 'BattleTech Eridani Light Horse Hunter Lance', Decimal('28.04'), Decimal('32.99'),
     '/battletech-eridani-light-horse-hunter-lance',
     'https://store.catalystgamelabs.com/products/battletech-eridani-light-horse-hunter-lance?_pos=79&_fid=715e41335&_ss=c'),
    ('BT-079', 'BattleTech - Inner Sphere Pursuit Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech---inner-sphere-pursuit-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere-pursuit-lance?_pos=80&_fid=715e41335&_ss=c'),
    ('BT-080', 'BattleTech - Inner Sphere Heavy Recon Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech---inner-sphere-heavy-recon-lance',
     'https://store.catalystgamelabs.com/products/battletech-inner-sphere-heavy-recon-lance?_pos=81&_fid=715e41335&_ss=c'),
    ('BT-081', 'BattleTech - Inner Sphere Battle Armor Platoon', Decimal('29.69'), Decimal('32.99'),
     '/battletech---inner-sphere-battle-armor-platoon',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere-battle-armor-platoon?_pos=82&_fid=715e41335&_ss=c'),
    ('BT-082', 'BattleTech - SalvageBox Legendary Warriors blind Box', Decimal('8.10'), Decimal('9.00'),
     '/battletech---salvagebox-legendary-warriors-blind-box',
     'https://store.catalystgamelabs.com/products/battletech-salvagebox-legendary-warriors-individual?_pos=83&_fid=715e41335&_ss=c'),
    ('BT-083', 'BattleTech: Battlefield Support Objectives', Decimal('28.79'), Decimal('31.99'),
     '/battletech:-battlefield-support-objectives',
     'https://store.catalystgamelabs.com/products/battletech-battlefield-support-objectives-forcepack?_pos=84&_fid=715e41335&_ss=c'),
    ('BT-086', 'Battletech: Legendary MechWarriors II Force Pack', Decimal('32.39'), Decimal('35.99'),
     '/battletech:-legendary-mechwarriors-ii-force-pack',
     'https://store.catalystgamelabs.com/products/battletech-legendary-mechwarriors-ii-forcepack?_pos=87&_fid=715e41335&_ss=c'),
    ('BT-087', 'Battletech: Battlefield Support Heavy Battle & Sweep Lances', Decimal('36.89'), Decimal('40.99'),
     '/battletech:-battlefield-support-heavy-battle--sweep-lances',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-heavy-battle-sweep-lances?_pos=88&_fid=715e41335&_ss=c'),
    ('BT-088', 'BattleTech - Inner Sphere Assault Lance', Decimal('29.69'), Decimal('32.99'),
     '/battletech---inner-sphere-assault-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere-assault-lance?_pos=89&_fid=715e41335&_ss=c'),
    ('BT-089', 'BattleTech - Timber Wolf C-Scale', Decimal('35.99'), Decimal('39.99'),
     '/battletech---timber-wolf-c-scale',
     'https://store.catalystgamelabs.com/products/battletech-timber-wolf-c-scale?_pos=90&_fid=715e41335&_ss=c'),
    ('BT-096', 'BattleTech - Salvage Box Gothic POP', Decimal('9.50'), Decimal('10.00'),
     '/battletech---salvage-box-gothic-pop',
     'https://store.catalystgamelabs.com/products/battletech-gothic-salvage-box-individual-blind-box?_pos=97&_fid=715e41335&_ss=c'),
    ('BT-098', 'Battletech: Inner Sphere Command Lance', Decimal('22.50'), Decimal('25.00'),
     '/battletech:-inner-sphere-command-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-099', 'Battletech: Inner Sphere Battle Lance', Decimal('31.49'), Decimal('34.99'),
     '/battletech:-inner-sphere-battle-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-100', 'BattleTech - Inner Sphere Direct Fire Lance', Decimal('31.48'), Decimal('34.99'),
     '/battletech---inner-sphere-direct-fire-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-101', 'BattleTech - Inner Sphere Heavy Lance', Decimal('31.49'), Decimal('34.99'),
     '/battletech---inner-sphere-heavy-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-102', 'Battletech: Inner Sphere Striker Lance', Decimal('31.49'), Decimal('34.99'),
     '/battletech:-inner-sphere-striker-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-103', 'BattleTech: Inner Sphere Fire Lance', Decimal('22.49'), Decimal('24.99'),
     '/battletech:-inner-sphere-fire-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-104', 'BattleTech - Inner Sphere Heavy Battle Lance', Decimal('31.48'), Decimal('34.99'),
     '/battletech---inner-sphere-heavy-battle-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-105', 'BattleTech Inner Sphere Urban Lance', Decimal('22.49'), Decimal('24.99'),
     '/battletech-inner-sphere-urban-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-106', 'BattleTech - Inner Sphere Support Lance', Decimal('31.49'), Decimal('34.99'),
     '/battletech---inner-sphere-support-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-inner-sphere?_pos=1&_fid=715e41335&_ss=c'),
    ('BT-107', 'Battletech: Clan Command Star', Decimal('35.99'), Decimal('39.99'),
     '/battletech:-clan-command-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-108', 'Battletech: Clan Heavy Striker Star', Decimal('35.99'), Decimal('39.99'),
     '/battletech:-clan-heavy-striker-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-109', 'Battletech: Clan Fire Star', Decimal('26.99'), Decimal('29.99'),
     '/battletech:-clan-fire-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-110', 'BattleTech Clan Heavy Star', Decimal('26.99'), Decimal('29.99'),
     '/battletech-clan-heavy-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-111', 'BattleTech - Clan Support Star', Decimal('35.99'), Decimal('39.99'),
     '/battletech---clan-support-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-112', 'Battletech: Clan Heavy Battle Star', Decimal('26.99'), Decimal('29.99'),
     '/battletech:-clan-heavy-battle-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-113', 'BattleTech - Clan Striker Star', Decimal('35.99'), Decimal('39.99'),
     '/battletech---clan-striker-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-114', 'BattleTech - Clan Ad Hoc Star', Decimal('26.99'), Decimal('29.99'),
     '/battletech---clan-ad-hoc-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-115', 'Battletech: Elemental Star', Decimal('22.49'), Decimal('24.99'),
     '/battletech:-elemental-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepack-clan?_pos=2&_fid=715e41335&_ss=c'),
    ('BT-116', 'BattleTech - ComStar Command Level II', Decimal('40.49'), Decimal('44.99'),
     '/battletech---comstar-command-level-ii',
     'https://store.catalystgamelabs.com/products/battletech-forcepacks-comstar?_pos=10&_fid=715e41335&_ss=c'),
    ('BT-117', 'BattleTech - ComStar Battle Level II', Decimal('31.49'), Decimal('34.99'),
     '/battletech---comstar-battle-level-ii',
     'https://store.catalystgamelabs.com/products/battletech-forcepacks-comstar?_pos=10&_fid=715e41335&_ss=c'),
    ('BT-118', "BattleTech - Wolf's Dragoons Assault Star", Decimal('29.69'), Decimal('32.99'),
     '/battletech---wolfs-dragoons-assault-star',
     'https://store.catalystgamelabs.com/products/battletech-forcepacks-wolfs-dragoons?_pos=21&_fid=715e41335&_ss=c'),
    ('BT-119', "Battletech: Snord's Irregulars Assault Lance", Decimal('29.69'), Decimal('32.99'),
     '/battletech:-snords-irregulars-assault-lance',
     'https://store.catalystgamelabs.com/products/battletech-forcepacks-wolfs-dragoons?_pos=21&_fid=715e41335&_ss=c'),
]


class Command(BaseCommand):
    help = (
        'Seed Firestorm Games UK prices for BattleTech and a UK-side Catalyst Game Labs '
        'GBP reference price derived from Firestorm RRP. Idempotent.'
    )

    def handle(self, *args, **options):
        firestorm, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': f'{_FS_BASE}/{_FS_AFF}',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {firestorm.name}')

        catalyst_uk, created = Retailer.objects.get_or_create(
            slug=_CATALYST_UK_SLUG,
            defaults={
                'name': 'Catalyst Game Labs UK',
                'website': 'https://store.catalystgamelabs.com',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {catalyst_uk.name}')

        seeded = 0
        skipped = 0
        for sku, label, sale_gbp, rrp_gbp, fs_path, catalyst_url in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
                skipped += 1
                continue

            fs_url = f'{_FS_BASE}{fs_path}{_FS_AFF}'

            for product in products:
                if product.msrp_gbp != rrp_gbp:
                    product.msrp_gbp = rrp_gbp
                    product.save(update_fields=['msrp_gbp'])

                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=firestorm,
                    defaults={
                        'price': sale_gbp,
                        'currency': 'GBP',
                        'url': fs_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=catalyst_uk,
                    defaults={
                        'price': rrp_gbp,
                        'currency': 'GBP',
                        'url': catalyst_url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} BattleTech UK prices (Firestorm + Catalyst Game Labs UK). Skipped: {skipped}.'
            )
        )
