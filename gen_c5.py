import os, decimal

fp = os.path.join(chr(67)+chr(58), os.sep+chr(85)+chr(115)+chr(101)+chr(114)+chr(115), chr(107)+chr(104)+chr(108)+chr(101)+chr(117), chr(84)+chr(104)+chr(114)+chr(105)+chr(102)+chr(116)+chr(72)+chr(97)+chr(109)+chr(109)+chr(101)+chr(114), chr(84)+chr(104)+chr(114)+chr(105)+chr(102)+chr(116)+chr(104)+chr(97)+chr(109)+chr(109)+chr(101)+chr(114), chr(112)+chr(114)+chr(111)+chr(100)+chr(117)+chr(99)+chr(116)+chr(115), chr(109)+chr(97)+chr(110)+chr(97)+chr(103)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116), chr(99)+chr(111)+chr(109)+chr(109)+chr(97)+chr(110)+chr(100)+chr(115), chr(112)+chr(111)+chr(112)+chr(117)+chr(108)+chr(97)+chr(116)+chr(101)+chr(95)+chr(112)+chr(114)+chr(111)+chr(100)+chr(117)+chr(99)+chr(116)+chr(115)+chr(46)+chr(112)+chr(121))
with open(fp, 'r', encoding='utf-8') as f:
    c = f.read()
print('Lines:', len(c.splitlines()))

NL = chr(10); Q = chr(39); S12 = chr(32)*12; S13 = chr(32)*13; EN = chr(8211)

def entry(name, cat, faction, sku, price, d1, d2):
    fs = Q + faction + Q if faction else 'None'
    return NL.join([
        S12 + chr(40) + Q + name + Q + chr(44)+chr(32) + Q + cat + Q + chr(44)+chr(32) + fs + chr(44),
        S13 + Q + sku + Q + chr(44)+chr(32)+chr(100)+chr(101)+chr(99)+chr(105)+chr(109)+chr(97)+chr(108)+chr(46)+chr(68)+chr(101)+chr(99)+chr(105)+chr(109)+chr(97)+chr(108)+chr(40) + Q + price + Q + chr(41)+chr(44),
        S13 + Q + d1 + Q + chr(44),
        S13 + Q + d2 + Q + chr(41)+chr(44),
    ])

products = [
    S12 + '# === KILL TEAM ===',
    entry('Kill Team: Operatives Datacard Pack 2024','Kill Team',None,'KT-101','25.00','Reference datacards for all Kill Team operatives, covering stats, ','abilities, and equipment in a handy card format.'),
    entry('Kill Team: Void-Dancer Troupe','Kill Team',None,'KT-102','40.00','Harlequin operatives bringing acrobatic lethality to the Kill Team ','game – a unique and deadly faction.'),
    entry('Kill Team: Veteran Guardsmen','Kill Team',None,'KT-103','40.00','Battle-hardened Astra Militarum veterans with a wealth of special ','weapons and veteran skills for Kill Team.'),
    entry('Kill Team: Chaos Legionaries','Kill Team',None,'KT-104','40.00','Corrupted Chaos Space Marine operatives armed with dark weapons ','and driven by the powers of Chaos.'),
    entry('Kill Team: Intercession Squad','Kill Team',None,'KT-105','40.00','Elite Primaris Space Marine operatives including specialists with ','unique equipment and abilities.'),
    entry('Kill Team: Hunter Clade','Kill Team',None,'KT-106','45.00','Skitarii Ranger and Vanguard operatives of the Adeptus Mechanicus ','hunting heresy with precise, lethal efficiency.'),
    entry('Kill Team: Exaction Squad','Kill Team',None,'KT-107','40.00','Adeptus Arbites enforcers maintaining the Emperor’s law in the ','underhives and void stations of the Imperium.'),
    entry('Kill Team: Salvation','Kill Team',None,'KT-108','130.00','A Kill Team boxed set pitting Adeptus Arbites against Genestealer ','Cult Neophytes in an underhive setting with terrain.'),
    entry('Kill Team: Terrain – Killzone Essentials','Kill Team',None,'KT-109','55.00','A set of modular terrain pieces for creating Kill Team battlefield ','environments, compatible with all killzones.'),
    entry('Kill Team: Compendium','Kill Team',None,'KT-110','40.00','The essential reference guide containing rules for all Kill Team ','factions in one comprehensive volume.'),
    S12 + '# === ADDITIONAL SPACE MARINES ===',
    entry('Space Marine Marneus Calgar','Warhammer 40,000','Ultramarines','55-12','45.00','Chapter Master of the Ultramarines and Lord Macragge, armed with ','the Gauntlets of Ultramar and accompanied by his Honour Guard.'),
    entry('Space Marine Roboute Guilliman','Warhammer 40,000','Ultramarines','55-02','60.00','The Primarch of the Ultramarines, returned to lead the Imperium. ','An iconic centrepiece model armed with the Emperor’s Sword.'),
    entry('Space Marine Judiciar','Warhammer 40,000','Space Marines','48-36','30.00','A warrior of justice armed with an executioner relic blade, ','whose ominous presence slows the enemy’s reactions.'),
    entry('Space Marine Primaris Lieutenant','Warhammer 40,000','Space Marines','48-61','27.50','A Primaris Lieutenant providing tactical command, armed with a ','master-crafted auto bolt rifle and power sword.'),
    entry('Space Marine Company Heroes','Warhammer 40,000','Space Marines','48-37','45.00','A set of Company Heroes including an Ancient, Company Champion, ','and two Bladeguard Veterans supporting the Chapter Master.'),
    entry('Space Marine Bladeguard Veterans','Warhammer 40,000','Space Marines','48-38','45.00','Three elite Bladeguard Veterans armed with master-crafted power ','swords and storm shields – the finest duelists of the Chapter.'),
    entry('Space Marine Hammerfall Bunker','Warhammer 40,000','Space Marines','48-27','52.50','A deployable fortification dropped from orbit, armed with a ','hammerfall missile launcher to provide firebase support.'),
    entry('Space Marine Firestrike Servo-Turrets','Warhammer 40,000','Space Marines','48-28','45.00','Two twin-linked lascannon or accelerator autocannon turrets ','providing automated long-range fire support.'),
    entry('Space Marine Eradicators','Warhammer 40,000','Space Marines','48-39','42.50','Three Primaris Eradicators carrying melta rifles capable of ','reducing even the heaviest vehicles to molten slag.'),
    entry('Space Marine Vanguard Veteran Squad','Warhammer 40,000','Space Marines','48-08','40.00','Five veterans bearing jump packs and a plethora of melee weapons ','including lightning claws and thunder hammers.'),
    S12 + '# === ADDITIONAL NECRONS ===',
    entry('Necron Flayed Ones','Warhammer 40,000','Necrons','49-17','35.00','Five Necron Flayed Ones, cursed warriors who wear the flesh of ','their victims and strike from ambush.'),
    entry('Necron Lychguard','Warhammer 40,000','Necrons','49-11','40.00','Five Necron Lychguard in ornate ceremonial warplate, serving ','as the personal bodyguard of Necron Overlords.'),
    entry('Necron Canoptek Spyder','Warhammer 40,000','Necrons','49-14','30.00','A single Canoptek Spyder repairing and reanimating nearby Necron ','warriors in the heat of battle.'),
    entry('Necron Doom Scythe','Warhammer 40,000','Necrons','49-13','42.50','A fast attack flyer armed with a death ray and twin tesla ','destructors, devastating enemy formations from the air.'),
    entry('Necron Doomsday Ark','Warhammer 40,000','Necrons','49-12','52.50','A massive Necron artillery vehicle armed with a doomsday cannon ','capable of vaporising entire squads in a single shot.'),
    entry('Necron C’tan Shard of the Void Dragon','Warhammer 40,000','Necrons','49-20','55.00','A fragment of the god of machines, imprisoned by the Necron ','nobles and unleashed upon the battlefield as a weapon.'),
    entry('Necron Psychomancer','Warhammer 40,000','Necrons','49-21','25.00','A Cryptek specialist who weaponises fear and illusion, driving ','enemy minds to madness on the battlefield.'),
    entry('Necron Royal Warden','Warhammer 40,000','Necrons','49-22','22.50','An enforcer of the Necron Overlord’s will, armed with a relic ','gauss blaster and bearing authority to execute deserters.'),
    S12 + '# === ADDITIONAL ORKS ===',
    entry('Ork Nobz','Warhammer 40,000','Orks','50-09','35.00','Five Ork Nobz, the biggest and meanest Boyz in a mob, armed ','with power klaws, big choppas, and kombi-weapons.'),
    entry('Ork Meganobz','Warhammer 40,000','Orks','50-12','47.50','Three Meganobz in mega armour, nigh-unstoppable Ork elites ','carrying power klaws and kombi-shootas.'),
    entry('Ork Deff Dread','Warhammer 40,000','Orks','50-16','35.00','A ramshackle Ork walker piloted by a crazed Ork, armed with ','klaws, drills, saws, and sluggas in all configurations.'),
    entry('Ork Killa Kans','Warhammer 40,000','Orks','50-15','42.50','Three Killa Kans – small walkers piloted by crazed Gretchin ','with a variety of scavenged weapons.'),
    entry('Ork Battlewagon','Warhammer 40,000','Orks','50-22','67.50','A massive Ork troop carrier and heavy transport armed with ','a deff rolla, big shootas, and extensive upgrades.'),
    entry('Ork Trukk','Warhammer 40,000','Orks','50-11','30.00','An Ork troop transport built from scrap, capable of delivering ','a mob of Boyz into combat with reckless speed.'),
    entry('Ork Warboss in Mega Armour','Warhammer 40,000','Orks','50-02','35.00','The biggest Ork wearing the biggest armour – a warlord in ','mega armour with a klaw and shootier weapons.'),
    entry('Ork Flash Gitz','Warhammer 40,000','Orks','50-20','40.00','Five flashily armoured Ork pirates with snazzguns – the ','wealthiest and vainest Orks in any Waaagh!'),
    entry('Ork Combat Patrol','Warhammer 40,000','Orks','71-18','105.00','Start your Waaagh! with a Warboss, Boyz, Deff Koptas, ','and a Deff Dread in this ready-to-play Combat Patrol.'),
    S12 + '# === ADDITIONAL TAU ===',
    entry('T'+Q+'au Crisis Battlesuits','Warhammer 40,000','T'+Q+'au Empire','56-14','55.00','Three T'+Q+'au Crisis Battlesuits with an enormous range of weapons ','including plasma rifles, burst cannons, and fusion blasters.'),
    entry('T'+Q+'au Riptide Battlesuit','Warhammer 40,000','T'+Q+'au Empire','56-15','80.00','The massive XV104 Riptide – a T'+Q+'au super-heavy battlesuit armed ','with a heavy burst cannon or ion accelerator.'),
    entry('T'+Q+'au Hammerhead Gunship','Warhammer 40,000','T'+Q+'au Empire','56-10','52.50','A T'+Q+'au main battle tank armed with a railgun or ion cannon, ','capable of destroying the heaviest enemy vehicles.'),
    entry('T'+Q+'au Commander','Warhammer 40,000','T'+Q+'au Empire','56-22','37.50','A T'+Q+'au Commander in a XV86 Coldstar or XV85 Enforcer battlesuit, ','the supreme tactical leader of a T'+Q+'au sept.'),
    entry('T'+Q+'au Stealth Battlesuits','Warhammer 40,000','T'+Q+'au Empire','56-20','35.00','Three XV25 Stealth Battlesuits with burst cannons, moving ','invisibly through the battlefield to strike at weak points.'),
    entry('T'+Q+'au Combat Patrol','Warhammer 40,000','T'+Q+'au Empire','71-24','105.00','A complete T'+Q+'au Combat Patrol: Commander, Fire Warriors, ','Stealth Battlesuits, and a Hammerhead Gunship.'),
    S12 + '# === ADDITIONAL AGE OF SIGMAR ===',
    entry('Nighthaunt Chainrasps','Age of Sigmar','Nighthaunt','91-28','35.00','Twenty spectral Chainrasp Hordes – the mournful spirits who ','form the core of any Nighthaunt force.'),
    entry('Nighthaunt Knight of Shrouds','Age of Sigmar','Nighthaunt','91-15','22.50','A single Knight of Shrouds on ethereal steed, a powerful ','Nighthaunt commander capable of emboldening nearby spirits.'),
    entry('Nighthaunt Hexwraiths','Age of Sigmar','Nighthaunt','91-06','35.00','Five spectral horsemen who drain the life from mortals they ','ride through, impossible to stop with mortal weapons.'),
    entry('Ossiarch Bonereapers Mortek Guard','Age of Sigmar','Ossiarch Bonereapers','94-10','42.50','Twenty Mortek Guard – the unyielding infantry of the Ossiarch ','legions, armed with nadirite blades and shields.'),
    entry('Ossiarch Bonereapers Gothizzar Harvester','Age of Sigmar','Ossiarch Bonereapers','94-12','52.50','A bone-harvesting construct that collects the remains of the ','slain to repair and reinforce nearby Mortek Guard.'),
    entry('Flesh-Eater Courts Crypt Ghouls','Age of Sigmar','Flesh-Eater Courts','91-35','35.00','Twenty Crypt Ghouls – the delusional flesh-eating servants of ','the Abhorrant Archregent, believing themselves noble warriors.'),
    entry('Flesh-Eater Courts Terrorgheist','Age of Sigmar','Flesh-Eater Courts','91-32','55.00','A massive undead bat-dragon that serves as the centrepiece of ','any Flesh-Eater Courts army.'),
    entry('Gloomspite Gitz Squig Hoppers','Age of Sigmar','Gloomspite Gitz','89-11','35.00','Five Squig Hoppers bounding unpredictably across the battlefield ','on their mouth-on-legs squig mounts.'),
    entry('Gloomspite Gitz Fanatics','Age of Sigmar','Gloomspite Gitz','89-06','30.00','Five Fanatics swinging enormous balls and chains in manic frenzy ','hidden inside Moonclan Grots until the moment of attack.'),
    entry('Orruk Warclans Ardboys','Age of Sigmar','Orruk Warclans','89-30','35.00','Ten heavily armoured Orruk Ardboys carrying choppas, shields, ','and bows – reliable infantry for any Ironjawz or Bonesplitterz list.'),
    entry('Daughters of Khaine Sisters of Slaughter','Age of Sigmar','Daughters of Khaine','85-17','40.00','Ten fanatic warriors of Khaine armed with blade bucklers and ','sacrificial knives, frenzied in battle.'),
    entry('Lumineth Realm-lords Vanari Auralan Wardens','Age of Sigmar','Lumineth Realm-lords','87-10','42.50','Ten Vanari Auralan Wardens wielding long sun spears – the ','disciplined pinnacle of Lumineth defensive warfare.'),
    entry('Cities of Sigmar Freeguild Fusiliers','Age of Sigmar','Cities of Sigmar','86-15','42.50','Ten Freeguild Fusiliers armed with handguns and pistols, ','the black-powder ranged core of any Cities force.'),
    entry('Slaves to Darkness Chaos Warriors','Age of Sigmar','Slaves to Darkness','83-18','42.50','Ten Chaos Warriors clad in ensorcelled plate armour, wielding ','hand weapons and shields in service of the dark gods.'),
    entry('Blades of Khorne Bloodletters','Age of Sigmar','Blades of Khorne','97-08','35.00','Ten Bloodletters – the foot soldiers of Khorne, armed with ','hellblades and driven by boundless fury.'),
    entry('Maggotkin of Nurgle Plaguebearers','Age of Sigmar','Maggotkin of Nurgle','97-09','35.00','Ten Plaguebearers of Nurgle, putrid daemons carrying plagueswords ','and spreading corruption across the Mortal Realms.'),
    entry('Disciples of Tzeentch Pink Horrors','Age of Sigmar','Disciples of Tzeentch','97-11','35.00','Ten Pink Horrors of Tzeentch, magical daemons who split into ','Blue Horrors when slain. A core unit of any Tzeentch force.'),
    entry('Stormcast Eternals Praetors','Age of Sigmar','Stormcast Eternals','96-55','42.50','Three Praetors – the elite bodyguard of the Lord-Commander, ','armed with halberd-length stormstrike glaives.'),
    entry('Stormcast Eternals Vindictors','Age of Sigmar','Stormcast Eternals','96-50','42.50','Five Vindictors in heavy plate armour with stormspears and ','shields – the dependable core infantry of any Stormhost.'),
    entry('Skaven Plague Monks','Age of Sigmar','Skaven','90-12','30.00','Twenty fanatical Plague Monks of Clan Pestilens, spreading ','disease and decay with foetid blades.'),
    S12 + '# === ASTRA MILITARUM ===',
    entry('Astra Militarum Infantry Squad','Warhammer 40,000','Astra Militarum','47-19','30.00','Ten Astra Militarum Guardsmen armed with lasguns, a sergeant, ','and options for a special weapon and a heavy weapon team.'),
    entry('Astra Militarum Cadian Command Squad','Warhammer 40,000','Astra Militarum','47-08','32.50','An officer and four veteran Cadian Guardsmen acting as a ','command unit with vox-caster, medic, and banner options.'),
    entry('Astra Militarum Leman Russ Battle Tank','Warhammer 40,000','Astra Militarum','47-06','52.50','The iconic Leman Russ in seven variants including the Demolisher, ','Punisher, Executioner, and Exterminator.'),
    entry('Astra Militarum Chimera','Warhammer 40,000','Astra Militarum','47-04','37.50','A reliable armoured infantry carrier equipped with a multi-laser ','or heavy flamer turret and hull-mounted heavy bolter.'),
    entry('Astra Militarum Sentinel','Warhammer 40,000','Astra Militarum','47-10','30.00','A single Sentinel scout walker armed with autocannon, lascannon, ','or missile launcher – fast and effective reconnaissance.'),
    entry('Astra Militarum Commissar','Warhammer 40,000','Astra Militarum','47-16','17.50','A ruthless political officer who maintains discipline through ','fear, armed with a bolt pistol and power sword.'),
    entry('Astra Militarum Combat Patrol','Warhammer 40,000','Astra Militarum','71-22','105.00','A Combat Patrol for the Astra Militarum: Cadian Shock Troops, ','a Sentinel, a Leman Russ, and a Commissar.'),
    S12 + '# === DEATH GUARD ===',
    entry('Death Guard Plague Marines','Warhammer 40,000','Death Guard','43-54','42.50','Seven plastic Plague Marines oozing corruption, with massive ','kit variety including plague weapons and blight launchers.'),
    entry('Death Guard Myphitic Blight-Haulers','Warhammer 40,000','Death Guard','43-55','45.00','Three insectoid walkers armed with missile launchers and ','multi-meltas, spewing toxic fumes as they advance.'),
    entry('Death Guard Mortarion','Warhammer 40,000','Death Guard','43-40','115.00','The Daemon Primarch of the Death Guard – a massive winged ','model armed with Silence, the Lantern, and Phosphex bombs.'),
    entry('Death Guard Typhus','Warhammer 40,000','Death Guard','43-42','27.50','The Herald of Nurgle and host of the Destroyer Hive, Typhus ','brings plague and pestilence to every battlefield.'),
    entry('Death Guard Foetid Bloat-drone','Warhammer 40,000','Death Guard','43-60','40.00','A pus-filled daemonic engine drifting lazily into combat with ','a fleshmower or plaguespitter and plague probe.'),
    S12 + '# === HORUS HERESY ===',
    entry('Legiones Astartes MKIII Infantry Squad','Horus Heresy',None,'HA-010','45.00','Ten Space Marine legionaries in Mark III Iron Armour – the ','original heresy-era close-assault armour variant.'),
    entry('Legiones Astartes Cataphractii Terminators','Horus Heresy',None,'HA-011','55.00','Five Terminators in the ancient Cataphractii pattern plate, ','the heaviest armour available to the Legiones Astartes.'),
    entry('Legiones Astartes Predator','Horus Heresy',None,'HA-012','57.50','The classic Predator tank in Heresy-era configuration, armed ','with a predator cannon or twin lascannons.'),
    entry('Legiones Astartes Spartan Assault Tank','Horus Heresy',None,'HA-013','105.00','A massive super-heavy assault tank capable of transporting ','twenty Terminators into the heart of the enemy.'),
    entry('Solar Auxilia Lasrifle Section','Horus Heresy',None,'HA-020','45.00','Ten elite Solar Auxilia infantry armed with volkite chargers ','and las-rifles, the best conventional troops of the Heresy era.'),
    S12 + '# === CITADEL PAINTS ===',
    entry('Citadel Layer Paint','Paint & Supplies',None,'LP-001','4.55','A single Citadel Layer paint (12ml), formulated for highlighting ','over base coats to add depth and detail.'),
    entry('Citadel Dry Paint','Paint & Supplies',None,'DP-001','4.55','A single Citadel Dry paint (12ml) for drybrushing effects, ','with a thick consistency that picks out raised details.'),
    entry('Citadel Technical Paint (Nihilakh Oxide)','Paint & Supplies',None,'TE-001','5.50','A weathering paint that creates verdigris and corrosion effects ','in the recesses of aged brass and bronze models.'),
    entry('Citadel Air Paint','Paint & Supplies',None,'AP-001','6.30','A single pre-thinned Citadel Air paint (24ml) ready for use ','with an airbrush without further thinning needed.'),
    entry('Citadel Spray: Chaos Black','Paint & Supplies',None,'SP-010','15.00','A 400ml aerosol spray primer in Chaos Black, providing an ','excellent base coat for dark colour schemes.'),
    entry('Citadel Spray: Wraithbone','Paint & Supplies',None,'SP-011','15.00','A 400ml aerosol spray primer in Wraithbone, the ideal base ','for contrast and bright colour schemes.'),
    entry('Citadel Spray: Grey Seer','Paint & Supplies',None,'SP-012','15.00','A 400ml aerosol spray primer in Grey Seer – the best base ','colour for Contrast paints on a neutral mid-grey.'),
    entry('Citadel Munitorum Varnish','Paint & Supplies',None,'SP-020','15.00','A 400ml aerosol matt varnish that protects painted models ','from chipping and wear without affecting colour.'),
    entry('Citadel Brush: Medium Base','Paint & Supplies',None,'BR-001','6.30','A medium-sized Citadel Base brush, ideal for basecoating ','infantry models and vehicles quickly and evenly.'),
    entry('Citadel Brush: Medium Layer','Paint & Supplies',None,'BR-002','6.30','A medium Citadel Layer brush for painting details, layering ','highlights, and applying Contrast paints with precision.'),
    entry('Citadel Hobby Knife','Paint & Supplies',None,'HK-001','12.00','A precision hobby knife with a replaceable blade for cutting ','plastic sprues, trimming mould lines, and fine conversion work.'),
    entry('Citadel Plastic Glue','Paint & Supplies',None,'PG-001','6.00','A 25ml tube of Citadel plastic glue that bonds plastic ','components with a strong, invisible join.'),
]

# Find insertion point
marker = chr(32)*8 + chr(35) + chr(32) + 'Re-use the faction lookup built in _create_products'
idx = c.find(marker)
print('Marker at:', idx)
if idx > 0:
    bracket_pat = chr(10) + chr(32)*8 + chr(93) + chr(10)
    bracket_pos = c.rfind(bracket_pat, 0, idx)
    print('Bracket at:', bracket_pos)
    insertion = chr(10) + chr(10).join(products)
    c = c[:bracket_pos] + insertion + c[bracket_pos:]
    with open(fp, chr(119), encoding=chr(117)+chr(116)+chr(102)+chr(45)+chr(56)) as f:
        f.write(c)
    print('CHANGE 5: OK '+chr(45)+'', len(c.splitlines()), 'lines total')
else:
    print('CHANGE 5: FAILED')
