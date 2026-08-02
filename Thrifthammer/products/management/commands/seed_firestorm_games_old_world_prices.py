"""
Seed Firestorm Games UK prices for Warhammer: The Old World.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. Only
games-workshop-uk writes msrp_gbp.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.
RRP is only used as a matching aid to confirm which DB SKU a listing
corresponds to (it should equal Product.msrp_gbp for the matched SKU).

Unlike Age of Sigmar/40k, The Old World tracks "Arcane Journal" supplement
books as their own faction-specific DB SKUs (not excluded like Warscroll
Cards/Battletomes elsewhere).

https://www.firestormgames.co.uk/wargames-miniatures/warhammer-the-old-world
-- Batch 1: Armies of Grand Cathay
12/15 matched. Gaps: GCA-003 Astromancers of the Celestial Court, GCA-004
Grand Cannon & Fire Rain Rocket Battery, GCA-013 The Northern Provinces of
Grand Cathay Transfer Sheet -- none found on the page. "Battalion: Grand
Cathay" (bundle box) has no DB counterpart, consistent with the Battleforce/
Combat Patrol exclusion pattern used throughout this project.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

_PRICES = [
    ('GCA-001', 'Grand Cathay: Iron Hail & Crane Gunners', Decimal('47.96'),
     'https://www.firestormgames.co.uk/grand-cathay:-iron-hail--crane-gunners?aff=6a4ab07d1c6f9'),
    ('GCA-002', 'Grand Cathay: Peasant Levy', Decimal('47.96'),
     'https://www.firestormgames.co.uk/grand-cathay:-peasant-levy?aff=6a4ab07d1c6f9'),
    ('GCA-015', 'Arcane Journal: Breaching Of The Great Bastion', Decimal('14.96'),
     'https://www.firestormgames.co.uk/arcane-journal:-breaching-of-the-great-bastion?aff=6a4ab07d1c6f9'),
    ('GCA-011', 'Arcane Journal: Dawn Of The Storm Dragon', Decimal('14.96'),
     'https://www.firestormgames.co.uk/arcane-journal:-dawn-of-the-storm-dragon?aff=6a4ab07d1c6f9'),
    ('GCA-006', 'Grand Cathay: Miao Ying The Storm Dragon', Decimal('81.84'),
     'https://www.firestormgames.co.uk/grand-cathay:-miao-ying-the-storm-dragon?aff=6a4ab07d1c6f9'),
    ('GCA-014', 'Grand Cathay: Jade Warriors', Decimal('47.96'),
     'https://www.firestormgames.co.uk/grand-cathay:-jade-warriors?aff=6a4ab07d1c6f9'),
    ('GCA-005', 'Grand Cathay: Jade Lancers', Decimal('47.96'),
     'https://www.firestormgames.co.uk/grand-cathay:-jade-lancers?aff=6a4ab07d1c6f9'),
    ('GCA-010', 'Grand Cathay: Shugengan Lord on Great Spirit Longma', Decimal('36.00'),
     'https://www.firestormgames.co.uk/grand-cathay:-shugengan-lord-on-great-spirit-longma?aff=6a4ab07d1c6f9'),
    ('GCA-008', 'Grand Cathay: Cathayan Sentinel', Decimal('56.00'),
     'https://www.firestormgames.co.uk/grand-cathay:-cathayan-sentinel?aff=6a4ab07d1c6f9'),
    ('GCA-007', 'Grand Cathay: Sky Lantern', Decimal('73.50'),
     'https://www.firestormgames.co.uk/grand-cathay:-sky-lantern?aff=6a4ab07d1c6f9'),
    ('GCA-009', 'Grand Cathay: Gate Masters of the Celestial Cities', Decimal('28.60'),
     'https://www.firestormgames.co.uk/grand-cathay:-gate-masters-of-the-celestial-cities?aff=6a4ab07d1c6f9'),
    ('GCA-012', 'Arcane Journal: Armies of Grand Cathay', Decimal('8.50'),
     'https://www.firestormgames.co.uk/arcane-journal:-armies-of-grand-cathay?aff=6a4ab07d1c6f9'),
    ('BBH-001', 'Beastmen Brayherds - Tuskgor Chariot', Decimal('25.65'),
     'https://www.firestormgames.co.uk/beastmen-brayherds---tuskgor-chariot?aff=6a4ab07d1c6f9'),
    ('BBH-002', 'Beastmen Brayherds: Beastman Chieftain', Decimal('17.57'),
     'https://www.firestormgames.co.uk/beastmen-brayherds:-beastman-chieftain?aff=6a4ab07d1c6f9'),
    ('BBH-004', 'Beastmen Brayherds: Cygor/Ghorgon', Decimal('47.03'),
     'https://www.firestormgames.co.uk/beastmen-brayherds:-cygorghorgon?aff=6a4ab07d1c6f9'),
    ('BBH-005', 'Beastmen Brayherds: Minotaur Herd', Decimal('33.73'),
     'https://www.firestormgames.co.uk/beastmen-brayherds:-minotaur-herd?aff=6a4ab07d1c6f9'),
    ('BBH-003', 'Beastmen Brayherds: Ungor Herd', Decimal('51.78'),
     'https://www.firestormgames.co.uk/beastmen-brayherds:-ungor-herd?aff=6a4ab07d1c6f9'),
    ('BBH-008', 'Beastmen Brayherds: Beastman Shaman', Decimal('16.28'),
     'https://www.firestormgames.co.uk/beastmen-brayherds:-beastman-shaman?aff=6a4ab07d1c6f9'),
    ('BBH-006', 'Beastmen Brayherds: Gor Herd', Decimal('47.96'),
     'https://www.firestormgames.co.uk/beastmen-brayherds:-gor-herd?aff=6a4ab07d1c6f9'),
    ('BBH-007', 'Beastmen Brayherds: Bestigor Herd', Decimal('47.96'),
     'https://www.firestormgames.co.uk/beastmen-brayherds:-bestigor-herd?aff=6a4ab07d1c6f9'),
    ('DMH-002', 'Dwarfen Mountain Holds: Dwarf King With Oathstone', Decimal('16.28'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-king-with-oathstone?aff=6a4ab07d1c6f9'),
    ('DMH-003', 'Dwarfen Mountain Holds: Slayer Of Legend', Decimal('16.28'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-slayer-of-legend?aff=6a4ab07d1c6f9'),
    ('DMH-004', 'Dwarfen Mountain Holds: Dwarf Cannon & Organ Gun', Decimal('31.24'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-cannon--organ-gun?aff=6a4ab07d1c6f9'),
    ('DMH-005', 'Dwarfen Mountain Holds: Gyrocopters & Gyrobombers', Decimal('43.56'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-gyrocopters--gyrobombers?aff=6a4ab07d1c6f9'),
    ('DMH-006', 'Dwarfen Mountain Holds: Dwarf Miners', Decimal('35.20'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-miners?aff=6a4ab07d1c6f9'),
    ('DMH-007', 'Dwarfen Mountain Holds: Dwarf Lords With Shieldbearers', Decimal('28.60'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-lords-with-shieldbearers?aff=6a4ab07d1c6f9'),
    ('DMH-008', 'Dwarfen Mountain Holds: Dwarf Hammerers', Decimal('47.96'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-hammerers?aff=6a4ab07d1c6f9'),
    ('DMH-009', 'Dwarfen Mountain Holds: Dwarf Ironbreakers', Decimal('47.96'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-ironbreakers?aff=6a4ab07d1c6f9'),
    ('DMH-010', 'Dwarfen Mountain Holds: Dwarf Quarrellers', Decimal('47.96'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-quarrellers?aff=6a4ab07d1c6f9'),
    ('DMH-011', 'Dwarfen Mountain Holds: Dwarf Warriors', Decimal('47.96'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-warriors?aff=6a4ab07d1c6f9'),
    ('DMH-012', 'Dwarfen Mountain Holds: Dwarf Runesmith', Decimal('16.28'),
     'https://www.firestormgames.co.uk/dwarfen-mountain-holds:-dwarf-runesmith?aff=6a4ab07d1c6f9'),
    ('EOM-018', 'Empire of Man: War Altar of Sigmar', Decimal('47.02'),
     'https://www.firestormgames.co.uk/empire-of-man:-war-altar-of-sigmar?aff=6a4ab07d1c6f9'),
    ('EOM-002', 'Empire of Man: Empire Steam Tank', Decimal('47.02'),
     'https://www.firestormgames.co.uk/empire-of-man:-empire-steam-tank?aff=6a4ab07d1c6f9'),
    ('EOM-017', 'Empire of Man: Captain of the Empire', Decimal('18.05'),
     'https://www.firestormgames.co.uk/empire-of-man:-captain-of-the-empire?aff=6a4ab07d1c6f9'),
    ('EOM-003', 'Empire Of Man: Helblaster Volleygun/Helstorm Battery', Decimal('31.24'),
     'https://www.firestormgames.co.uk/empire-of-man:-helblaster-volleygunhelstorm-battery-?aff=6a4ab07d1c6f9'),
    ('EOM-016', 'Empire Of Man: Archers', Decimal('35.20'),
     'https://www.firestormgames.co.uk/empire-of-man:-archers?aff=6a4ab07d1c6f9'),
    ('EOM-004', 'Empire Of Man: Greatswords', Decimal('47.96'),
     'https://www.firestormgames.co.uk/empire-of-man:-greatswords-?aff=6a4ab07d1c6f9'),
    ('EOM-005', 'Empire Of Man: Flagellants', Decimal('43.56'),
     'https://www.firestormgames.co.uk/empire-of-man:-flagellants?aff=6a4ab07d1c6f9'),
    ('EOM-006', 'Empire Of Man: State Missile Troops', Decimal('47.96'),
     'https://www.firestormgames.co.uk/empire-of-man:-state-missile-troops?aff=6a4ab07d1c6f9'),
    ('EOM-007', 'Empire Of Man: Empire State Troops', Decimal('47.96'),
     'https://www.firestormgames.co.uk/empire-of-man:-empire-state-troops?aff=6a4ab07d1c6f9'),
    ('EOM-015', 'Empire Of Man: Commanders Of The Empire', Decimal('16.28'),
     'https://www.firestormgames.co.uk/empire-of-man:-commanders-of-the-empire?aff=6a4ab07d1c6f9'),
    ('EOM-009', 'Empire Of Man: Cannons & Mortars', Decimal('31.24'),
     'https://www.firestormgames.co.uk/empire-of-man:-cannons--mortars?aff=6a4ab07d1c6f9'),
    ('EOM-010', 'Empire Of Man: Demigryph Knights', Decimal('35.20'),
     'https://www.firestormgames.co.uk/empire-of-man:-demigryph-knights?aff=6a4ab07d1c6f9'),
    ('EOM-011', 'Empire Of Man: Empire Pistoliers', Decimal('35.20'),
     'https://www.firestormgames.co.uk/empire-of-man:-empire-pistoliers?aff=6a4ab07d1c6f9'),
    ('EOM-012', 'Empire Of Man: Empire Knights', Decimal('35.20'),
     'https://www.firestormgames.co.uk/empire-of-man:-empire-knights?aff=6a4ab07d1c6f9'),
    ('EOM-013', 'Empire Of Man: Free Company Militia', Decimal('47.96'),
     'https://www.firestormgames.co.uk/empire-of-man:-free-company-militia?aff=6a4ab07d1c6f9'),
    ('EOM-014', 'Empire Of Man: General On Imperial Griffon', Decimal('43.56'),
     'https://www.firestormgames.co.uk/empire-of-man:-general-on-imperial-griffon?aff=6a4ab07d1c6f9'),
    ('HER-001', 'High Elf Realms: Tiranoc Chariots', Decimal('51.77'),
     'https://www.firestormgames.co.uk/high-elf-realms:-tiranoc-chariots?aff=6a4ab07d1c6f9'),
    ('HER-024', 'High Elf Realms: Elven Archers', Decimal('51.77'),
     'https://www.firestormgames.co.uk/high-elf-realms:-elven-archers?aff=6a4ab07d1c6f9'),
    ('HER-022', 'High Elf Realms: Korhil Lionmane', Decimal('11.40'),
     'https://www.firestormgames.co.uk/high-elf-realms:-korhil-lionmane?aff=6a4ab07d1c6f9'),
    ('HER-020', 'High Elf Realms: Great Eagle of the Elven Realms', Decimal('19.48'),
     'https://www.firestormgames.co.uk/high-elf-realms:-great-eagle-of-the-elven-realms?aff=6a4ab07d1c6f9'),
    ('HER-007', 'High Elf Realms: Lothern Skycutter', Decimal('47.03'),
     'https://www.firestormgames.co.uk/high-elf-realms:-lothern-skycutter?aff=6a4ab07d1c6f9'),
    ('HER-021', 'Handmaiden of the Everqueen', Decimal('8.55'),
     'https://www.firestormgames.co.uk/handmaiden-of-the-everqueen?aff=6a4ab07d1c6f9'),
    ('HER-006', 'High Elf Realms: Flamespyre Phoenix', Decimal('47.02'),
     'https://www.firestormgames.co.uk/high-elf-realms:-flamespyre-phoenix?aff=6a4ab07d1c6f9'),
    ('HER-025', 'High Elf Realms: Lothern Sea Guard', Decimal('51.78'),
     'https://www.firestormgames.co.uk/high-elf-realms:-lothern-sea-guard?aff=6a4ab07d1c6f9'),
    ('HER-004', 'High Elf Realms: Silver Helms', Decimal('35.20'),
     'https://www.firestormgames.co.uk/high-elf-realms:-silver-helms?aff=6a4ab07d1c6f9'),
    ('HER-005', 'High Elf Realms: High Elf Loremaster', Decimal('16.28'),
     'https://www.firestormgames.co.uk/high-elf-realms:-high-elf-loremaster?aff=6a4ab07d1c6f9'),
    ('HER-008', 'High Elf Realms: Dragon Princes of Caledor', Decimal('47.96'),
     'https://www.firestormgames.co.uk/high-elf-realms:-dragon-princes-of-caledor?aff=6a4ab07d1c6f9'),
    ('HER-003', 'High Elf Realms: Elven Spearmen', Decimal('47.96'),
     'https://www.firestormgames.co.uk/high-elf-realms:-elven-spearmen?aff=6a4ab07d1c6f9'),
    ('HER-011', 'High Elf Realms: Mages', Decimal('24.20'),
     'https://www.firestormgames.co.uk/high-elf-realms:-mages?aff=6a4ab07d1c6f9'),
    ('HER-010', 'High Elf Realms: Sisters Of Avelorn', Decimal('29.04'),
     'https://www.firestormgames.co.uk/high-elf-realms:-sisters-of-avelorn?aff=6a4ab07d1c6f9'),
    ('HER-009', 'High Elf Realms: Phoenix Guard', Decimal('47.96'),
     'https://www.firestormgames.co.uk/high-elf-realms:-phoenix-guard?aff=6a4ab07d1c6f9'),
    ('HER-012', 'High Elf Realms: High Elf Lords', Decimal('24.20'),
     'https://www.firestormgames.co.uk/high-elf-realms:-high-elf-lords?aff=6a4ab07d1c6f9'),
    ('HER-023', 'High Elf Realms Transfer Sheet', Decimal('22.32'),
     'https://www.firestormgames.co.uk/high-elf-realms-transfer-sheet?aff=6a4ab07d1c6f9'),
    ('HER-013', 'High Elf Realms: Ellyrian Reavers', Decimal('51.78'),
     'https://www.firestormgames.co.uk/high-elf-realms:-ellyrian-reavers?aff=6a4ab07d1c6f9'),
    ('HER-016', 'High Elf Realms: Lord On Dragon', Decimal('43.56'),
     'https://www.firestormgames.co.uk/high-elf-realms:-lord-on-dragon?aff=6a4ab07d1c6f9'),
    ('HER-017', 'High Elf Realms: Swordmasters Of Hoeth', Decimal('47.96'),
     'https://www.firestormgames.co.uk/high-elf-realms:-swordmasters-of-hoeth?aff=6a4ab07d1c6f9'),
    ('HER-014', 'High Elf Realms: White Lions Of Chrace', Decimal('47.96'),
     'https://www.firestormgames.co.uk/high-elf-realms:-white-lions-of-chrace?aff=6a4ab07d1c6f9'),
    ('HER-015', 'High Elf Realms: Claw Bolt Throwers', Decimal('31.24'),
     'https://www.firestormgames.co.uk/high-elf-realms:-claw-bolt-throwers?aff=6a4ab07d1c6f9'),
    ('HER-002', 'Arcane Journal: High Elf Realms', Decimal('14.96'),
     'https://www.firestormgames.co.uk/arcane-journal:-high-elf-realms?aff=6a4ab07d1c6f9'),
    ('KOB-001', 'Kingdom of Bretonnia: Peasant Bowmen', Decimal('47.96'),
     'https://www.firestormgames.co.uk/kingdom-of-bretonnia:-peasant-bowmen?aff=6a4ab07d1c6f9'),
    ('KOB-002', 'Kingdom of Bretonnia: Men at Arms', Decimal('47.96'),
     'https://www.firestormgames.co.uk/kingdom-of-bretonnia:-men-at-arms?aff=6a4ab07d1c6f9'),
    ('KOB-004', 'Kingdom of Bretonnia: Lord on Royal Pegasus', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kingdom-of-bretonnia:-lord-on-royal-pegasus?aff=6a4ab07d1c6f9'),
    ('KOB-003', 'Kingdom Of Bretonnia: Knights of the Realm', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kingdom-of-bretonnia:-knights-of-the-realm?aff=6a4ab07d1c6f9'),
    ('KOB-007', 'Kingdom Of Bretonnia: Knights Of The Realm On Foot', Decimal('47.96'),
     'https://www.firestormgames.co.uk/kingdom-of-bretonnia:-knights-of-the-realm-on-foot?aff=6a4ab07d1c6f9'),
    ('KOB-005', 'Kingdom Of Bretonnia: Pegasus Knights', Decimal('34.00'),
     'https://www.firestormgames.co.uk/kingdom-of-bretonnia:-pegasus-knights?aff=6a4ab07d1c6f9'),
    ('KOB-006', 'Kingdom Of Bretonnia: Battle Standard On Royal Pegasus', Decimal('37.40'),
     'https://www.firestormgames.co.uk/kingdom-of-bretonnia:-battle-standard-on-royal-pegasus?aff=6a4ab07d1c6f9'),
    ('OGT-005', 'Orc & Goblin Tribes: Black Orc Mob', Decimal('47.96'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-black-orc-mob?aff=6a4ab07d1c6f9'),
    ('OGT-001', 'Orc & Goblin Tribes: Goblin Shaman', Decimal('17.57'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-goblin-shaman?aff=6a4ab07d1c6f9'),
    ('OGT-010', 'Orc & Goblin Tribes: Night Goblin Mob', Decimal('47.96'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-night-goblin-mob?aff=6a4ab07d1c6f9'),
    ('OGT-002', 'Orc & Goblin Tribes: Goblin Wolf Rider Mob', Decimal('37.40'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-goblin-wolf-rider-mob?aff=6a4ab07d1c6f9'),
    ('OGT-003', 'Orc & Goblin Tribes: Goblin Mob', Decimal('51.77'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-goblin-mob?aff=6a4ab07d1c6f9'),
    ('OGT-004', 'Orc & Goblin Tribes: Orc Boar Chariots', Decimal('51.77'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-orc-boar-chariots?aff=6a4ab07d1c6f9'),
    ('OGT-006', 'Orc & Goblin Tribes: Orc Boar Boyz Mob', Decimal('37.40'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-orc-boar-boyz-mob?aff=6a4ab07d1c6f9'),
    ('OGT-007', 'Orc & Goblin: Orc Boyz Arrer Boyz Mobs', Decimal('47.96'),
     'https://www.firestormgames.co.uk/orc--goblin:-orc-boyz-arrer-boyz-mobs?aff=6a4ab07d1c6f9'),
    ('OGT-008', 'Orc & Goblin Tribes: Orc Boyz Mob', Decimal('47.96'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-orc-boyz-mob?aff=6a4ab07d1c6f9'),
    ('OGT-009', 'Orc & Goblin Tribes: Orc Bosses', Decimal('25.52'),
     'https://www.firestormgames.co.uk/orc--goblin-tribes:-orc-bosses?aff=6a4ab07d1c6f9'),
    ('TKK-012', 'Arcane Journal: The War Of Settra\'s Fury', Decimal('14.96'),
     'https://www.firestormgames.co.uk/arcane-journal:-the-war-of-settras-fury?aff=6a4ab07d1c6f9'),
    ('TKK-003', 'Tomb Kings Of Khemri: Liche Priests', Decimal('28.60'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-liche-priests?aff=6a4ab07d1c6f9'),
    ('TKK-004', 'Tomb Kings Of Khemri: Royal Heralds', Decimal('28.60'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-royal-heralds?aff=6a4ab07d1c6f9'),
    ('TKK-001', 'Tomb Kings Of Khemri: Chariots', Decimal('27.25'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-chariots?aff=6a4ab07d1c6f9'),
    ('TKK-005', 'Tomb Kings Of Khemri: Skeleton Horsemen', Decimal('21.25'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-skeleton-horsemen?aff=6a4ab07d1c6f9'),
    ('TKK-002', 'Tomb Kings Of Khemri: Skeleton Warriors', Decimal('38.15'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-skeleton-warriors?aff=6a4ab07d1c6f9'),
    ('TKK-006', 'Tomb Kings Of Khemri: Tomb King On Necrolith Bone Dragon', Decimal('48.38'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-tomb-king-on-necrolith-bone-dragon?aff=6a4ab07d1c6f9'),
    ('TKK-009', 'Tomb Kings Of Khemri: Necrosphinx', Decimal('43.56'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-necrosphinx?aff=6a4ab07d1c6f9'),
    ('TKK-008', 'Tomb Kings Of Khemri: Khemrian Warsphinx (Necrosphinx kit)', Decimal('43.56'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-necrosphinx?aff=6a4ab07d1c6f9'),
    ('TKK-010', 'Tomb Kings Of Khemri: Sepulchral Stalkers', Decimal('37.40'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-sepulchral-stalkers?aff=6a4ab07d1c6f9'),
    ('TKK-007', 'Tomb Kings Of Khemri: Necropolis Knights (Sepulchral Stalkers kit)', Decimal('37.40'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-sepulchral-stalkers?aff=6a4ab07d1c6f9'),
    ('TKK-011', 'Tomb Kings Of Khemri: Tomb Guard', Decimal('47.96'),
     'https://www.firestormgames.co.uk/tomb-kings-of-khemri:-tomb-guard?aff=6a4ab07d1c6f9'),
    ('WOC-001', 'Warriors Of Chaos: Chaos Marauder Horsemen', Decimal('47.96'),
     'https://www.firestormgames.co.uk/warriors-of-chaos:-chaos-marauder-horsemen?aff=6a4ab07d1c6f9'),
    ('WOC-003', 'Warriors Of Chaos: Chaos Marauders', Decimal('47.96'),
     'https://www.firestormgames.co.uk/warriors-of-chaos:-chaos-marauders?aff=6a4ab07d1c6f9'),
    ('WOC-006', 'Warriors Of Chaos: Chimera', Decimal('38.00'),
     'https://www.firestormgames.co.uk/warriors-of-chaos:-chimera?aff=6a4ab07d1c6f9'),
    ('WOC-009', 'Warriors Of Chaos: Dragon Ogres', Decimal('38.00'),
     'https://www.firestormgames.co.uk/warriors-of-chaos:-dragon-ogres?aff=6a4ab07d1c6f9'),
    ('WOC-007', 'Warriors Of Chaos: Sorcerer Of Chaos', Decimal('16.72'),
     'https://www.firestormgames.co.uk/warriors-of-chaos:-sorcerer-of-chaos?aff=6a4ab07d1c6f9'),
    ('WOC-010', 'Warriors Of Chaos: Lord On Manticore', Decimal('43.56'),
     'https://www.firestormgames.co.uk/warriors-of-chaos:-lord-on-manticore?aff=6a4ab07d1c6f9'),
    ('WOC-002', 'Arcane Journal: Warriors Of Chaos', Decimal('14.96'),
     'https://www.firestormgames.co.uk/arcane-journal:-warriors-of-chaos?aff=6a4ab07d1c6f9'),
    ('WOC-008', 'Arcane Journal: The Razing Of Westerland', Decimal('14.96'),
     'https://www.firestormgames.co.uk/arcane-journal:-the-razing-of-westerland?aff=6a4ab07d1c6f9'),
    ('WOC-004', 'Warriors Of Chaos: Chaos Chariot / Gorebeast Chariot', Decimal('51.80'),
     'https://www.firestormgames.co.uk/warriors-of-chaos:-chaos-chariot--gorebeast-chariot?aff=6a4ab07d1c6f9'),
    ('WER-003', 'Wood Elf Realms: Wood Elf Noble on Forest Dragon', Decimal('49.40'),
     'https://www.firestormgames.co.uk/wood-elf-realms:-wood-elf-noble-on-forest-dragon?aff=6a4ab07d1c6f9'),
    ('WER-005', 'Wood Elf Realms: Wild Riders', Decimal('51.78'),
     'https://www.firestormgames.co.uk/wood-elf-realms:-wild-riders?aff=6a4ab07d1c6f9'),
    ('WER-001', 'Battalion: Wood Elf Realms', Decimal('101.20'),
     'https://www.firestormgames.co.uk/battalion:-wood-elf-realms?aff=6a4ab07d1c6f9'),
    ('WER-004', 'Wood Elf Realms: Araloth Lord Of Talsyn', Decimal('16.28'),
     'https://www.firestormgames.co.uk/wood-elf-realms:-araloth-lord-of-talsyn?aff=6a4ab07d1c6f9'),
    ('WER-007', 'Wood Elf Realms: Eternal Guard', Decimal('47.96'),
     'https://www.firestormgames.co.uk/wood-elf-realms:-eternal-guard?aff=6a4ab07d1c6f9'),
    ('WER-008', 'Wood Elf Realms: Glade Guard', Decimal('47.96'),
     'https://www.firestormgames.co.uk/wood-elf-realms:-glade-guard?aff=6a4ab07d1c6f9'),
    ('WER-006', 'Wood Elf Realms: Glade Riders', Decimal('33.88'),
     'https://www.firestormgames.co.uk/wood-elf-realms:-glade-riders?aff=6a4ab07d1c6f9'),
    ('WER-002', 'Arcane Journal: Wood Elf Realms', Decimal('14.96'),
     'https://www.firestormgames.co.uk/arcane-journal:-wood-elf-realms?aff=6a4ab07d1c6f9'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Warhammer: The Old World. Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_FIRESTORM_SLUG,
            defaults={
                'name': 'Firestorm Games',
                'website': 'https://www.firestormgames.co.uk/?aff=6a4ab07d1c6f9',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for sku, label, gbp_price, url in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stderr.write(f'SKIP — SKU {sku} ({label}) not in DB')
                skipped += 1
                continue

            for product in products:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'currency': 'GBP',
                        'url': url,
                        'in_stock': True,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Firestorm Games Old World prices. Skipped: {skipped}.'
            )
        )
