"""
Management command: populate_middle_earth_products

Creates the Middle Earth (MESBG) product line as a new top-level Category
(no Faction subdivision -- Middle Earth Strategy Battle Game is treated as a
standalone game system on this site, same pattern as Star Wars: Shatterpoint
and Battletech).

Plastic kits only -- metal/resin/Finecast models are intentionally excluded
per user direction (2026-07-27).

MSRP/images/URLs come directly from Games Workshop (warhammer.com), so this
category has a real GW retailer row, same as every other GW-catalog category.

Usage:
    python manage.py populate_middle_earth_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

# (slug, gw_sku, name, msrp, image_url, gw_url, ebay_search_name)
PRODUCTS = [
    ('the-war-of-the-rohirrim-battle-of-edoras', 'MESBG-001', 'The War of the Rohirrim – Battle of Edoras', decimal.Decimal('230'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60011499013_ENGWotRBattleEdoras1a.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/war-of-the-rohirrim-battle-of-edoras-eng-2024', 'Middle Earth Battle Game The War of the Rohirrim – Battle of Edoras'),
    ('middle-earth-strategy-battle-game-the-treachery-of-gollum', 'MESBG-002', 'Middle-earth Strategy Battle Game: The Treachery of Gollum', decimal.Decimal('29'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60041499056_MiddleEarthTreacheryOfGollumBook01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-journal-the-treachery-of-gollum-sb-eng-2026', 'Middle Earth Battle Game Middle-earth Strategy Battle Game: The Treachery of Gollum'),
    ('middle-earth-strategy-battle-game-the-burning-of-the-westfold', 'MESBG-003', 'Middle-earth Strategy Battle Game: The Burning of the Westfold', decimal.Decimal('29'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60041499062_MEJournalBurningOfTheWestfold01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-burning-of-the-westfold-2026-eng', 'Middle Earth Battle Game Middle-earth Strategy Battle Game: The Burning of the Westfold'),
    ('the-lord-of-the-rings-the-war-of-the-rohirrim', 'MESBG-004', 'The Lord of the Rings: The War of the Rohirrim', decimal.Decimal('29'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60041499061_WaroftheRohirrimJounalMiddleEarthSBRulebook1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-the-war-of-the-rohirrim-eng-sb-2025', 'Middle Earth Battle Game The Lord of the Rings: The War of the Rohirrim'),
    ('middle-earth-strategy-battle-game-matched-play-guide', 'MESBG-005', 'Middle-earth Strategy Battle Game: Matched Play Guide', decimal.Decimal('35'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60041499055_MEMatchedPlayGuide01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-matched-play-guide-sb-eng-2025', 'Middle Earth Battle Game Middle-earth Strategy Battle Game: Matched Play Guide'),
    ('armies-of-middle-earth', 'MESBG-006', 'Armies of Middle-earth', decimal.Decimal('60'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60041499060_ArmiesofMiddleEarthHBRulebook1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/armies-of-middle-earth-hb-eng-2025', 'Middle Earth Battle Game Armies of Middle-earth'),
    ('armies-of-the-hobbit', 'MESBG-007', 'Armies of The Hobbit', decimal.Decimal('60'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60041499059_MEHoBBArmiesOfTheHobbitHBArmyBook01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/armies-of-the-hobbit-eng-hb-2024', 'Middle Earth Battle Game Armies of The Hobbit'),
    ('armies-of-the-lord-of-the-rings', 'MESBG-008', 'Armies of The Lord of The Rings', decimal.Decimal('65'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60041499058_ArmiesoftheLordoftheRingsRulebook1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/armies-of-the-lord-of-the-rings-eng-hb-2024', 'Middle Earth Battle Game Armies of The Lord of The Rings'),
    ('middle-earth-strategy-battle-game-rules-manual', 'MESBG-009', 'Middle-earth Strategy Battle Game Rules Manual', decimal.Decimal('60'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/60041499057_WotRRulebook1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-strategy-battle-game-rules-manual-eng-2024', 'Middle Earth Battle Game Middle-earth Strategy Battle Game Rules Manual'),
    ('hill-tribesmen-commanders', 'MESBG-010', 'Hill Tribesmen Commanders', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464044_MEHillTribesmenCommanders01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-hill-tribesmen-commanders-2026', 'Middle Earth Battle Game Hill Tribesmen Commanders'),
    ('warriors-of-rohan-commanders', 'MESBG-011', 'Warriors of Rohan Commanders', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464042_MEWarriorsOfRohanCommanders01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-warriors-of-rohan-commanders-2026', 'Middle Earth Battle Game Warriors of Rohan Commanders'),
    ('minas-tirith-battlehost', 'MESBG-012', 'Minas Tirith Battlehost', decimal.Decimal('96'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464032_MinasTirithBattlehostLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/minas-tirith-battlehost-2022', 'Middle Earth Battle Game Minas Tirith Battlehost'),
    ('gondor-tower', 'MESBG-013', 'Gondor Tower', decimal.Decimal('69'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499053_MEGondorTower01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-gondor-tower-2023', 'Middle Earth Battle Game Gondor Tower'),
    ('gondor-mansion', 'MESBG-014', 'Gondor Mansion', decimal.Decimal('89'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499052_MEGondorMansion01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-gondor-mansion-2023', 'Middle Earth Battle Game Gondor Mansion'),
    ('gondor-ruins', 'MESBG-015', 'Gondor Ruins', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499051_GondorRuins2.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-gondor-ruins-2023', 'Middle Earth Battle Game Gondor Ruins'),
    ('gothmog-lieutenant-of-sauron', 'MESBG-016', 'Gothmog, Lieutenant of Sauron', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462024_MEGothmogLieutenantOfSauron01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/gothmog-lieutenant-of-sauron-2023', 'Middle Earth Battle Game Gothmog, Lieutenant of Sauron'),
    ('ruins-of-middle-earth', 'MESBG-017', 'Ruins of Middle-earth', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499054_RuinsofMiddleEarthLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/ruins-of-middle-earth-2022', 'Middle Earth Battle Game Ruins of Middle-earth'),
    ('isengard-battlehost', 'MESBG-018', 'Isengard Battlehost', decimal.Decimal('96'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462027_IsenguardBattlehostLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/isengard-battlehost-2022', 'Middle Earth Battle Game Isengard Battlehost'),
    ('elrond-master-of-rivendell', 'MESBG-019', 'Elrond, Master of Rivendell', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121463015_MEElrondMasterofRivendellLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-elrond-master-of-rivendell-2022', 'Middle Earth Battle Game Elrond, Master of Rivendell'),
    ('ruins-of-dol-guldur', 'MESBG-020', 'Ruins of Dol Guldur', decimal.Decimal('82'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499047_RuinsofDolGuldurLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/ruins-of-dol-guldur-2021', 'Middle Earth Battle Game Ruins of Dol Guldur'),
    ('treebeard-mighty-ent', 'MESBG-021', 'Treebeard, Mighty Ent', decimal.Decimal('89'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499046_METreebeardMightyEntLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Treebeard-Mighty-Ent-2021', 'Middle Earth Battle Game Treebeard, Mighty Ent'),
    ('mines-of-moria', 'MESBG-022', 'Mines of Moria', decimal.Decimal('33.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99081499001_MinesMoriaTerLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Mines-of-Moria-Terrain-2020', 'Middle Earth Battle Game Mines of Moria'),
    ('saruman-the-white-grima', 'MESBG-023', 'Saruman the White & Gríma', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464029_SarumanWhiteGrima01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Saruman-The-White-and-Grima-2019', 'Middle Earth Battle Game Saruman the White & Gríma'),
    ('mounted-rohan-command', 'MESBG-024', 'Mounted Rohan Command', decimal.Decimal('69'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99111464205_MERohanMountedCommand01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Mounted-Rohan-Command-2019', 'Middle Earth Battle Game Mounted Rohan Command'),
    ('rohan-royal-knights', 'MESBG-025', 'Rohan Royal Knights', decimal.Decimal('64'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99111464204_RohanRoyalKnights01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Rohan-Royal-Knights-2019', 'Middle Earth Battle Game Rohan Royal Knights'),
    ('king-of-the-dead-heralds', 'MESBG-026', 'King of the Dead & Heralds', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121466014_KingOfTheDeadHeralds01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/King-Of-The-Dead-And-Heralds-2019', 'Middle Earth Battle Game King of the Dead & Heralds'),
    ('eowyn-merry', 'MESBG-027', 'Éowyn & Merry', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499042_EowynandMerry01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Eowyn-and-Merry-2019', 'Middle Earth Battle Game Éowyn & Merry'),
    ('the-three-hunters', 'MESBG-028', 'The Three Hunters', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499041_ThreeHunters01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/The-Three-Hunters-2019', 'Middle Earth Battle Game The Three Hunters'),
    ('thorin-oakenshield-company', 'MESBG-029', 'Thorin Oakenshield & Company', decimal.Decimal('60'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499031_ThorinandCompany01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Thorin-Oakenshield-And-Company-2018', 'Middle Earth Battle Game Thorin Oakenshield & Company'),
    ('gandalf-the-white-and-peregrin-took', 'MESBG-030', 'Gandalf the White and Peregrin Took', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99221499015_GandalfandPeregrinTook01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Gandalf-The-White-and-Peregrin-Took-2018', 'Middle Earth Battle Game Gandalf the White and Peregrin Took'),
    ('grim-hammers', 'MESBG-031', 'Grim Hammers', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121465010_MiddleearthGrimmHammers01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Grim-Hammers-2018', 'Middle Earth Battle Game Grim Hammers'),
    ('warriors-of-erebor', 'MESBG-032', 'Warriors of Erebor', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121465009_MiddleearthWarriorsErebor01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Warriors-Of-Erebor-2018', 'Middle Earth Battle Game Warriors of Erebor'),
    ('palace-guards', 'MESBG-033', 'Palace Guards', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121463013_PalaceGuardsLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Palace-Guards-2018', 'Middle Earth Battle Game Palace Guards'),
    ('mirkwood-rangers', 'MESBG-034', 'Mirkwood Rangers', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121463012_MirkwoodRangers01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Mirkwood-Rangers-2018', 'Middle Earth Battle Game Mirkwood Rangers'),
    ('goblin-warriors', 'MESBG-035', 'Goblin Warriors', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462021_MiddleearthGoblinWarriors01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Goblin-Warriors-2018', 'Middle Earth Battle Game Goblin Warriors'),
    ('hunter-orcs', 'MESBG-036', 'Hunter Orcs', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462020_HunterOrcs01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Hunter-Orcs-2018', 'Middle Earth Battle Game Hunter Orcs'),
    ('warriors-of-the-last-alliance', 'MESBG-037', 'Warriors of the Last Alliance', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499036_WarriorsofLastAlliance.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Warriors-Of-The-Last-Alliance-2018', 'Middle Earth Battle Game Warriors of the Last Alliance'),
    ('wild-wargs', 'MESBG-038', 'Wild Wargs', decimal.Decimal('21.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499025_WildWargsNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Wild-Wargs-2018', 'Middle Earth Battle Game Wild Wargs'),
    ('fellowship-of-the-ring', 'MESBG-039', 'Fellowship Of The Ring', decimal.Decimal('60'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499028_TheFellowshipoftheRingPlasticNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Fellowship-Of-The-Ring-2018', 'Middle Earth Battle Game Fellowship Of The Ring'),
    ('winged-nazgul', 'MESBG-040', 'Winged Nazgûl', decimal.Decimal('73.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121466005_NEWWingedNazgulNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Winged-Nazgul-2018', 'Middle Earth Battle Game Winged Nazgûl'),
    ('the-balrog', 'MESBG-041', 'The Balrog', decimal.Decimal('73.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499016_BalrogNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/The-Balrog-2018', 'Middle Earth Battle Game The Balrog'),
    ('mordor-troll', 'MESBG-042', 'Mordor Troll', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121466002_MordorTrollIsengardTrollNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Mordor-Troll-2018', 'Middle Earth Battle Game Mordor Troll'),
    ('dwarf-rangers', 'MESBG-043', 'Dwarf Rangers', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121465008_DwarfRangers.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Dwarf-Rangers-2018', 'Middle Earth Battle Game Dwarf Rangers'),
    ('dwarf-warriors-middle-earth', 'MESBG-044', 'Dwarf Warriors (Middle-earth)', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121465007_DwarfWarriors01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Dwarf-Warriors-2018', 'Middle Earth Battle Game Dwarf Warriors'),
    ('knights-of-dol-amroth', 'MESBG-045', 'Knights Of Dol Amroth', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464005_KnightsofDolAmrothMountedNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Knights-Of-Dol-amroth-2018', 'Middle Earth Battle Game Knights Of Dol Amroth'),
    ('morgul-knights', 'MESBG-046', 'Morgul Knights', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464006_MorgulKnightsNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Morgul-Knights-2018', 'Middle Earth Battle Game Morgul Knights'),
    ('haradrim-warriors', 'MESBG-047', 'Haradrim Warriors', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464023_HaradrimWarriorsLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Haradrim-Warriors-2018', 'Middle Earth Battle Game Haradrim Warriors'),
    ('rangers-of-middle-earth', 'MESBG-048', 'Rangers of Middle-earth', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464022_RangersofMiddleEarth.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Rangers-Of-Middle-earth-2018', 'Middle Earth Battle Game Rangers of Middle-earth'),
    ('easterling-kataphracts', 'MESBG-049', 'Easterling Kataphracts', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464007_EasterlingKataphraktsNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Easterling-Kataphracts-2018', 'Middle Earth Battle Game Easterling Kataphracts'),
    ('easterling-warriors', 'MESBG-050', 'Easterling Warriors', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464018_EasterlingWarriors.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Easterling-Warriors-2018', 'Middle Earth Battle Game Easterling Warriors'),
    ('warriors-of-minas-tirith', 'MESBG-051', 'Warriors of Minas Tirith', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464016_WarriorsofMinasTirith.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Warriors-Of-Minas-Tirith-2018', 'Middle Earth Battle Game Warriors of Minas Tirith'),
    ('galadhrim-knights', 'MESBG-052', 'Galadhrim Knights', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121463001_GaladhrimKnightsNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Galadhrim-Knights-2018', 'Middle Earth Battle Game Galadhrim Knights'),
    ('galadhrim-warriors', 'MESBG-053', 'Galadhrim Warriors', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121463009_GaladhrimWarriors01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Galadhrim-Warriors-2018', 'Middle Earth Battle Game Galadhrim Warriors'),
    ('lothlorien-wood-elf-warriors', 'MESBG-054', 'LOTHLÓRIEN Wood Elf Warriors', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121463008_WoodElfWarriors.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Wood-Elf-Warriors-2018', 'Middle Earth Battle Game LOTHLÓRIEN Wood Elf Warriors'),
    ('moria-goblins', 'MESBG-055', 'Moria Goblins', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462019_MoriaGoblins.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Moria-Goblins-2018', 'Middle Earth Battle Game Moria Goblins'),
    ('warg-riders', 'MESBG-056', 'Warg Riders', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499012_WargRidersNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Warg-Riders-2018', 'Middle Earth Battle Game Warg Riders'),
    ('morannon-orcs', 'MESBG-057', 'Morannon Orcs', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462016_MorannonOrcs01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Morannon-Orcs-2018', 'Middle Earth Battle Game Morannon Orcs'),
    ('mordor-orcs', 'MESBG-058', 'Mordor Orcs', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462015_MordorOrcsUPDATE1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Mordor-Orcs-2018', 'Middle Earth Battle Game Mordor Orcs'),
    ('uruk-hai-warriors', 'MESBG-059', 'Uruk-hai Warriors', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462013_UrukHaiWarriors01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Uruk-hai-Warriors-2018', 'Middle Earth Battle Game Uruk-hai Warriors'),
    ('knights-of-rivendell', 'MESBG-060', 'Knights of Rivendell', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121463007_RivendellKnights01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Knights-of-Rivendell', 'Middle Earth Battle Game Knights of Rivendell'),
    ('hunter-orcs-on-fell-wargs', 'MESBG-061', 'Hunter Orcs on Fell Wargs', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462009_HunterOrcsonFellWargsNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Hunter-Orcs-on-Fell-Wargs', 'Middle Earth Battle Game Hunter Orcs on Fell Wargs'),
    ('the-path-of-cirith-ungol-shelob-gollum', 'MESBG-062', 'The Path of Cirith Ungol: Shelob & Gollum', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499065_MiddleEarthPathOfCirithUngolShelobAndGollum01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/the-path-of-cirith-ungol-shelob-and-gollum-2026', 'Middle Earth Battle Game The Path of Cirith Ungol: Shelob & Gollum'),
    ('frealaf-hildeson-olwyn-lief-heroes-of-rohan', 'MESBG-063', 'Fréaláf Hildeson, Olwyn & Lief, Heroes of Rohan', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464039_MiddleEarthFrealafHildesonOlwynAndLiefHeroesofRohan01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-frealeaf-hildeson-and-olwyn-and-lief-2025', 'Middle Earth Battle Game Fréaláf Hildeson, Olwyn & Lief, Heroes of Rohan'),
    ('helm-hammerhand-king-of-rohan', 'MESBG-064', 'Helm Hammerhand, King of Rohan', decimal.Decimal('36.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464041_MiddleEarthHelmHammerhandKingofRohan01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-helm-hammerhand-king-of-rohan-2025', 'Middle Earth Battle Game Helm Hammerhand, King of Rohan'),
    ('hera-daughter-of-helm', 'MESBG-065', 'Héra Daughter of Helm', decimal.Decimal('36.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464040_HeraDaughterofHelm1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/hera-daughter-of-helm-2025', 'Middle Earth Battle Game Héra Daughter of Helm'),
    ('rohan-house', 'MESBG-066', 'Rohan House', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499063_MERohanHouseTerrain01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/rohan-house-2025', 'Middle Earth Battle Game Rohan House'),
    ('rohan-watchtower-palisades', 'MESBG-067', 'Rohan Watchtower & Palisades', decimal.Decimal('89'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499064_MERohanWatchtowerPalisadesTerrain01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/rohan-watchtower-and-palisades-2025', 'Middle Earth Battle Game Rohan Watchtower & Palisades'),
    ('rohan-stronghold', 'MESBG-068', 'Rohan Stronghold', decimal.Decimal('322'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499060_MERohanStrongholdTerrain01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/rohan-stronghold-2025', 'Middle Earth Battle Game Rohan Stronghold'),
    ('tom-bill-and-bert-the-trolls', 'MESBG-069', 'Tom, Bill, and Bert – The Trolls', decimal.Decimal('94'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121466013_HoBBTrollsRegiment12025.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/the-trolls-2025', 'Middle Earth Battle Game Tom, Bill, and Bert – The Trolls'),
    ('the-goblin-king-retinue', 'MESBG-070', 'The Goblin King & Retinue', decimal.Decimal('60'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462023_HoBBGoblinKingRetinueRegiment12025.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/goblin-king-and-retinue-2025', 'Middle Earth Battle Game The Goblin King & Retinue'),
    ('uruk-hai-demolition-team', 'MESBG-071', 'Uruk-Hai Demolition Team', decimal.Decimal('35'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462028_LotRsUrukHaiSiegeDemolitionTeam12025.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/uruk-hai-demolition-team-2025', 'Middle Earth Battle Game Uruk-Hai Demolition Team'),
    ('wulf-high-lord-of-the-hill-tribes-and-general-targg', 'MESBG-072', 'Wulf, High Lord of the Hill Tribes and General Targg', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464037_MEWotRWulfHighLordHillTribesGeneralTaraggRegiment12025.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/wulf-high-lord-of-the-hill-tribes-and-general-targg-2025', 'Middle Earth Battle Game Wulf, High Lord of the Hill Tribes and General Targg'),
    ('haleth-hama-princes-of-rohan', 'MESBG-073', 'Haleth & Háma, Princes of Rohan', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464038_WotRHalethHamaPrincesRohanRegiment1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/haleth-and-hama-princes-of-rohan-2025', 'Middle Earth Battle Game Haleth & Háma, Princes of Rohan'),
    ('great-eagles-of-the-misty-mountains', 'MESBG-074', 'Great Eagles of the Misty Mountains', decimal.Decimal('60'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499062_GreatEaglesandFledglings1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/great-eagles-2024', 'Middle Earth Battle Game Great Eagles of the Misty Mountains'),
    ('warriors-of-rohan', 'MESBG-075', 'Warriors of Rohan', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464036_WarriorsRohan1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/warriors-of-rohan-2024', 'Middle Earth Battle Game Warriors of Rohan'),
    ('riders-of-rohan', 'MESBG-076', 'Riders of Rohan', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464043_MERidersOfRohan01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/middle-earth-riders-of-rohan-2026', 'Middle Earth Battle Game Riders of Rohan'),
    ('faramir-madril-and-damrod-rangers-of-ithilien', 'MESBG-077', 'Faramir, Madril and Damrod, Rangers of Ithilien', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464031_MEFaramirMadrilDamrod04.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/faramir-madril-and-damrod-2023', 'Middle Earth Battle Game Faramir, Madril and Damrod, Rangers of Ithilien'),
    ('the-witch-king-of-angmar', 'MESBG-078', 'The Witch-king of Angmar', decimal.Decimal('36.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121466015_WitchkingAngmarLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/m-e-sbg-the-witch-king-of-angmar-2021', 'Middle Earth Battle Game The Witch-king of Angmar'),
    ('eomer-marshal-of-the-riddermark', 'MESBG-079', 'Éomer, Marshal of the Riddermark', decimal.Decimal('36.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464030_EomerMarshalLead.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Eomer-Marshal-Of-The-Riddermark-2020', 'Middle Earth Battle Game Éomer, Marshal of the Riddermark'),
    ('warriors-of-dale', 'MESBG-080', 'Warriors of Dale', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464028_WarriorsofDale01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Warriors-Of-Dale-2018', 'Middle Earth Battle Game Warriors of Dale'),
    ('theoden-king-of-rohan', 'MESBG-081', 'Théoden, King of Rohan', decimal.Decimal('36.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464027_TheodenKingofRohan01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Theoden-King-Of-Rohan-2018', 'Middle Earth Battle Game Théoden, King of Rohan'),
    ('legolas-greenleaf-tauriel', 'MESBG-082', 'Legolas Greenleaf & Tauriel', decimal.Decimal('36.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121463011_LegolasGreenleafTauriel01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Legolas-Greenleaf-And-tauriel-2018', 'Middle Earth Battle Game Legolas Greenleaf & Tauriel'),
    ('ent', 'MESBG-083', 'Ent', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499020_EntNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Ent-2018', 'Middle Earth Battle Game Ent'),
    ('warriors-of-the-dead', 'MESBG-084', 'Warriors of the Dead', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121466011_WarriorsoftheDead01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Warriors-Of-The-Dead-2018', 'Middle Earth Battle Game Warriors of the Dead'),
    ('war-mumak-of-harad', 'MESBG-085', 'War Mûmak Of Harad', decimal.Decimal('122'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121466001_WarMumakofHaradNEW02.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/War-Mumak-Of-Harad-2018', 'Middle Earth Battle Game War Mûmak Of Harad'),
    ('corsairs-of-umbar', 'MESBG-086', 'Corsairs of Umbar', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464025_CorsairsofUmbar.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Corsairs-Of-Umbar-2018', 'Middle Earth Battle Game Corsairs of Umbar'),
    ('haradrim-raiders', 'MESBG-087', 'Haradrim Raiders', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464004_HaradrimRaidersNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Haradrim-Raiders-2018', 'Middle Earth Battle Game Haradrim Raiders'),
    ('knights-of-minas-tirith', 'MESBG-088', 'Knights of Minas Tirith', decimal.Decimal('48'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464002_KnightsofMinasTirithNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Knights-Of-Minas-Tirith-2018', 'Middle Earth Battle Game Knights of Minas Tirith'),
    ('uruk-hai-scouts', 'MESBG-089', 'Uruk-hai Scouts', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462018_UrukHaiScouts.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Uruk-hai-Scouts-2018', 'Middle Earth Battle Game Uruk-hai Scouts'),
    ('lake-town-house', 'MESBG-090', 'Lake-town House', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499030_Laketown01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Lake-Town-House', 'Middle Earth Battle Game Lake-town House'),
    ('fell-wargs', 'MESBG-091', 'Fell Wargs', decimal.Decimal('35'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121499027_FellWargsNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Fell-Wargs', 'Middle Earth Battle Game Fell Wargs'),
    ('goblin-town', 'MESBG-092', 'Goblin Town', decimal.Decimal('73.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462007_GoblinTownNEW01.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/Goblin-Town', 'Middle Earth Battle Game Goblin Town'),
    ('bolg-spawn-of-azog', 'MESBG-093', 'Bolg, Spawn of Azog', decimal.Decimal('36.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121462025_BolgSpawnOfAzog1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/bolg-spawn-of-azog-2025', 'Middle Earth Battle Game Bolg, Spawn of Azog'),
    ('prince-imrahil-of-dol-amroth', 'MESBG-094', 'Prince Imrahil of Dol Amroth', decimal.Decimal('36.5'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464034_PrinceImrahilofDolAmroth1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/prince-imrahil-of-dol-amroth-2025', 'Middle Earth Battle Game Prince Imrahil of Dol Amroth'),
    ('hill-tribesmen', 'MESBG-095', 'Hill Tribesmen', decimal.Decimal('53'), 'https://www.warhammer.com/app/resources/catalog/product/920x950/99121464035_HillTribesmenWarriors1.jpg?fm=webp&w=320&h=330', 'https://www.warhammer.com/en-US/shop/hill-tribesmen-2024', 'Middle Earth Battle Game Hill Tribesmen'),
]


class Command(BaseCommand):
    help = "Populate Middle Earth (MESBG) products with GW US prices. Idempotent."

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            name='Middle Earth (MESBG)',
            defaults={'name': 'Middle Earth (MESBG)'},
        )

        gw, _ = Retailer.objects.get_or_create(
            slug='games-workshop',
            defaults={
                'name': 'Games Workshop',
                'website': 'https://www.warhammer.com/en-US/',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        products_created = 0
        products_updated = 0
        gw_prices_created = 0
        gw_prices_updated = 0

        for slug, gw_sku, name, msrp, image_url, gw_url, ebay_search_name in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'middle-earth',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, gw_price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=gw,
                defaults={
                    'price': msrp,
                    'url': gw_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if gw_price_created:
                gw_prices_created += 1
            else:
                gw_prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'GW prices: {gw_prices_created} created, {gw_prices_updated} updated.'
        ))
