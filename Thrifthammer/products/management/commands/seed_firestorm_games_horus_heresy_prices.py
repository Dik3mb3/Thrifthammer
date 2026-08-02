"""
Seed Firestorm Games UK prices for Warhammer: The Horus Heresy.

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. Only
games-workshop-uk writes msrp_gbp.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.
RRP is only used as a matching aid to confirm which DB SKU a listing
corresponds to (it should equal Product.msrp_gbp for the matched SKU).

https://www.firestormgames.co.uk/wargames-miniatures/horus-heresy
106/110 active DB products under Category='Horus Heresy' matched (Astartes
Legions, Cult Mechanicum, Forces of the Emperor, and 8 legacy no-faction
HA-XXX SKUs). Matching was done by grouping every DB msrp_gbp and every
Firestorm RRP into buckets and verifying each pairing by name -- not by
price alone, since many items share identical price points.

Gaps (4, not carried by Firestorm at all):
- CM-014 Age of Darkness Armiger Helverins
- CM-015 Age of Darkness Armiger Warglaives
- CM-016 Age of Darkness Knight Questoris
- HA-021 Horus Heresy Leviathan Dreadnought (legacy generic-name SKU with
  no specific weapon loadout; both specific Leviathan listings on
  Firestorm -- Claw & Drill, Ranged Weapons -- were already claimed by
  AL-034 and AL-038 respectively, leaving nothing for this orphan SKU)

Excluded deliberately: the "Cerastus Knight Acheron / Castigator / Lancer"
Knight Houses listings on this page are the exact same physical kits
already priced under Warhammer 40,000 Imperial Knights in
seed_firestorm_games_warhammer_40k_prices.py (31-67 / 31-66 / 31-06) --
not duplicated here to avoid conflicting writes.

Judgment call: two Cataphractii Terminator listings ("with Power Fists"
and "with Power Mauls") were split between AL-018 (DB name explicitly
says "Combi-bolters and Power Fists" -> matched to the Power Fists
listing) and HA-030 (generic legacy name, no loadout specified -> matched
to Power Mauls by elimination, the only remaining listing at that price).

Other name-convention matches confirmed by exact price + clear product
identity, not literal string match: AL-027 "Scimitar Jetbike Squadron" =
Firestorm "Sky-Hunter Squadron" (GW's actual kit name); AL-031 "Land
Raider Explorator/Carrier" = Firestorm "Land Raider Proteus" (GW's kit
name for the same multi-build model).

Not in our catalog at all (no SKU exists to price -- would require
populate_products with explicit permission, not done here): new MKIV
Assault/Tactical Squad releases (pre-order), a "Combi-Weapons & Shotgun
Upgrades" set, and a small Legio Custodes vehicle line (Custodian
Dreadnought, Caladius Grav-Tank, Caladius Grav-Tank Annihilator, Coronus
Grav-Carrier, Shield Captain).
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

_PRICES = [
    ('AL-001', 'Horus Heresy - Age of Darkness: Saturnine', Decimal('176.00'),
     'https://www.firestormgames.co.uk/horus-heresy---age-of-darkness:-saturnine?aff=6a4ab07d1c6f9'),
    ('AL-002', 'Horus Heresy - Legion Astartes: Maximus Battle Group', Decimal('117.92'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes:-maximus-battle-group?aff=6a4ab07d1c6f9'),
    ('AL-003', 'Horus Heresy - Liber Astartes', Decimal('39.16'),
     'https://www.firestormgames.co.uk/horus-heresy---liber-astartes?aff=6a4ab07d1c6f9'),
    ('AL-004', 'Horus Heresy - Legiones Astartes Combat Force', Decimal('92.40'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes-combat-force?aff=6a4ab07d1c6f9'),
    ('AL-005', 'Horus Heresy - Legion Astartes: Whirlwind Missile Tank', Decimal('37.40'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes:-whirlwind-missile-tank?aff=6a4ab07d1c6f9'),
    ('AL-006', 'Horus Heresy - Legion Astartes: Falchion Super-Heavy Tank Destroyer', Decimal('110.00'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes:-falchion-super-heavy-tank-destroyer?aff=6a4ab07d1c6f9'),
    ('AL-007', 'Horus Heresy - Legion Astartes: Spartan Prometheus Tank', Decimal('65.12'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes:-spartan-prometheus-tank?aff=6a4ab07d1c6f9'),
    ('AL-008', 'Horus Heresy - Legiones Astartes: MkII Tactical Squad', Decimal('47.96'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-mkii-tactical-squad?aff=6a4ab07d1c6f9'),
    ('AL-009', 'Legiones Astartes - Praetor with Power Axe', Decimal('19.14'),
     'https://www.firestormgames.co.uk/legiones-astartes---praetor-with-power-axe?aff=6a4ab07d1c6f9'),
    ('AL-010', 'Legiones Astartes - Praetor with Power Sword', Decimal('19.14'),
     'https://www.firestormgames.co.uk/legiones-astartes---praetor-with-power-sword?aff=6a4ab07d1c6f9'),
    ('AL-011', 'Legiones Astartes - Praetor & Chaplain Consul', Decimal('31.24'),
     'https://www.firestormgames.co.uk/legiones-astartes---praetor--chaplain-consul?aff=6a4ab07d1c6f9'),
    ('AL-012', 'Legiones Astartes - Terminator Tartaros Squad', Decimal('51.04'),
     'https://www.firestormgames.co.uk/legiones-astartes---terminator-tartaros-squad?aff=6a4ab07d1c6f9'),
    ('AL-013', 'Horus Heresy - Space Wolves - Geigor Fell-Hand', Decimal('18.92'),
     'https://www.firestormgames.co.uk/horus-heresy---space-wolves---geigor-fell-hand?aff=6a4ab07d1c6f9'),
    ('AL-014', 'Blood Angels: Dominion Zephon', Decimal('18.92'),
     'https://www.firestormgames.co.uk/blood-angels:-dominion-zephon?aff=6a4ab07d1c6f9'),
    ('AL-015', 'Imperial Fists: Fafnir Rann', Decimal('18.92'),
     'https://www.firestormgames.co.uk/imperial-fists:-fafnir-rann?aff=6a4ab07d1c6f9'),
    ('AL-016', 'Horus Heresy - Legion Astartes: Breacher Squad Upgrade Set', Decimal('26.40'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes:-breacher-squad-upgrade-set?aff=6a4ab07d1c6f9'),
    ('AL-017', 'Horus Heresy: MKIII Breacher Squad', Decimal('39.16'),
     'https://www.firestormgames.co.uk/horus-heresy:-mkiii-breacher-squad?aff=6a4ab07d1c6f9'),
    ('AL-018', 'Horus Heresy - Legion Astartes: Cataphractii Terminators with Power Fists', Decimal('37.40'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes:-cataphractii-terminators-with-power-fists?aff=6a4ab07d1c6f9'),
    ('AL-019', 'Horus Heresy - Legiones Astartes MkII Assault Squad', Decimal('39.16'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes-mkii-assault-squad?aff=6a4ab07d1c6f9'),
    ('AL-020', 'Legiones Astartes - Saturnine Praetor', Decimal('28.60'),
     'https://www.firestormgames.co.uk/legiones-astartes---saturnine-praetor?aff=6a4ab07d1c6f9'),
    ('AL-021', 'Legiones Astartes - Saturnine Terminators', Decimal('43.56'),
     'https://www.firestormgames.co.uk/legiones-astartes---saturnine-terminators?aff=6a4ab07d1c6f9'),
    ('AL-022', 'Legiones Astartes - MKII Veteran Squad with Disintegrator Weapons', Decimal('36.58'),
     'https://www.firestormgames.co.uk/legiones-astartes---mkii-veteran-squad-with-disintegrator-weapons?aff=6a4ab07d1c6f9'),
    ('AL-023', 'Horus Heresy - MKVI Assault Marines', Decimal('39.16'),
     'https://www.firestormgames.co.uk/horus-heresy---mkvi-assault-marines?aff=6a4ab07d1c6f9'),
    ('AL-024', 'Legiones Astartes: Vindicator Siege Tank', Decimal('41.80'),
     'https://www.firestormgames.co.uk/legiones-astartes:-vindicator-siege-tank?aff=6a4ab07d1c6f9'),
    ('AL-025', 'Legiones Astartes: Cerberus Heavy Tank', Decimal('68.20'),
     'https://www.firestormgames.co.uk/legiones-astartes:-cerberus-heavy-tank?aff=6a4ab07d1c6f9'),
    ('AL-026', 'Legiones Astartes: Sicaran Venator', Decimal('48.40'),
     'https://www.firestormgames.co.uk/legiones-astartes:-sicaran-venator?aff=6a4ab07d1c6f9'),
    ('AL-027', 'Horus Heresy - Sky-Hunter Squadron', Decimal('39.60'),
     'https://www.firestormgames.co.uk/horus-heresy---sky-hunter-squadron?aff=6a4ab07d1c6f9'),
    ('AL-028', 'Legiones Astartes: Typhon Heavy Siege Tank', Decimal('68.20'),
     'https://www.firestormgames.co.uk/legiones-astartes:-typhon-heavy-siege-tank?aff=6a4ab07d1c6f9'),
    ('AL-029', 'Horus Heresy - Scorpius Missile Tank', Decimal('39.60'),
     'https://www.firestormgames.co.uk/horus-heresy---scorpius-missile-tank?aff=6a4ab07d1c6f9'),
    ('AL-030', 'Deimos Pattern Predator Support Tank', Decimal('41.80'),
     'https://www.firestormgames.co.uk/deimos-pattern-predator-support-tank?aff=6a4ab07d1c6f9'),
    ('AL-031', 'Horus Heresy - Legiones Astartes: Land Raider Proteus', Decimal('51.04'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-land-raider-proteus?aff=6a4ab07d1c6f9'),
    ('AL-032', 'Legiones Astartes - Volkite Culverins & Lascannnons & Autocannons', Decimal('26.40'),
     'https://www.firestormgames.co.uk/legiones-astartes---volkite-culverins--lascannnons--autocannons?aff=6a4ab07d1c6f9'),
    ('AL-033', 'Legiones Astartes - Heavy Flamers & Multi-Meltas & Plasma Cannons', Decimal('26.40'),
     'https://www.firestormgames.co.uk/legiones-astartes---heavy-flamers--multi-meltas--plasma-cannons?aff=6a4ab07d1c6f9'),
    ('AL-034', 'Leviathan Dreadnought with Claws/Drills', Decimal('47.96'),
     'https://www.firestormgames.co.uk/leviathan-dreadnought-with-clawsdrills?aff=6a4ab07d1c6f9'),
    ('AL-035', 'Leviathan Siege Dreadnought Ranged Weapons Frame', Decimal('17.57'),
     'https://www.firestormgames.co.uk/leviathan-siege-dreadnought-ranged-weapons-frame?aff=6a4ab07d1c6f9'),
    ('AL-036', 'Contemptor Dreadnought Weapons Frame 2', Decimal('17.57'),
     'https://www.firestormgames.co.uk/contemptor-dreadnought-weapons-frame-2?aff=6a4ab07d1c6f9'),
    ('AL-037', 'Contemptor Dreadnought Weapons Frame 1', Decimal('17.57'),
     'https://www.firestormgames.co.uk/contemptor-dreadnought-weapons-frame-1?aff=6a4ab07d1c6f9'),
    ('AL-038', 'Legiones Astartes - Leviathan Dreadnought & Ranged Weapons', Decimal('47.96'),
     'https://www.firestormgames.co.uk/legiones-astartes---leviathan-dreadnought--ranged-weapons?aff=6a4ab07d1c6f9'),
    ('AL-039', 'Horus Heresy - Legiones Astartes: Special Weapons Upgrade Set', Decimal('26.40'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-special-weapons-upgrade-set?aff=6a4ab07d1c6f9'),
    ('AL-040', 'Horus Heresy - Legiones Astartes: Missile Launchers & Heavy Bolters', Decimal('26.40'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-missile-launchers--heavy-bolters?aff=6a4ab07d1c6f9'),
    ('AL-041', 'Horus Heresy - Legiones Astartes: Kratos Heavy Assault Tank', Decimal('74.80'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-kratos-heavy-assault-tank?aff=6a4ab07d1c6f9'),
    ('AL-042', 'Horus Heresy - Legiones Astartes: Deimos Pattern Rhino', Decimal('30.58'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-deimos-pattern-rhino?aff=6a4ab07d1c6f9'),
    ('AL-043', 'Horus Heresy - Legiones Astartes: Glaive Super-Heavy Spec Weapons Tank', Decimal('110.00'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-glaive-super-heavy-spec-weapons-tank?aff=6a4ab07d1c6f9'),
    ('AL-044', 'Horus Heresy - Legiones Astartes Fellblade Super-heavy Battle Tank', Decimal('106.25'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes-fellblade-super-heavy-battle-tank?aff=6a4ab07d1c6f9'),
    ('AL-045', 'Legiones Astartes - Araknae Quad Accelerator Platform', Decimal('40.38'),
     'https://www.firestormgames.co.uk/legiones-astartes---araknae-quad-accelerator-platform?aff=6a4ab07d1c6f9'),
    ('AL-046', 'Legiones Astartes - Disintegrator Weapons Upgrade Set', Decimal('17.57'),
     'https://www.firestormgames.co.uk/legiones-astartes---disintegrator-weapons-upgrade-set?aff=6a4ab07d1c6f9'),
    ('AL-047', 'Legiones Astartes - Saturnine Dreadnought Weapons – Ophion Configuration', Decimal('17.57'),
     'https://www.firestormgames.co.uk/legiones-astartes---saturnine-dreadnought-weapons--ophion-configuration?aff=6a4ab07d1c6f9'),
    ('AL-048', 'Legiones Astartes - Saturnine Dreadnought Weapons – Chiron Configuration', Decimal('17.57'),
     'https://www.firestormgames.co.uk/legiones-astartes---saturnine-dreadnought-weapons--chiron-configuration?aff=6a4ab07d1c6f9'),
    ('AL-049', 'Legiones Astartes - Drop Pod', Decimal('31.24'),
     'https://www.firestormgames.co.uk/legiones-astartes---drop-pod?aff=6a4ab07d1c6f9'),
    ('AL-050', 'Legiones Astartes - Saturnine Dreadnought Ophion', Decimal('61.16'),
     'https://www.firestormgames.co.uk/legiones-astartes---saturnine-dreadnought-ophion?aff=6a4ab07d1c6f9'),
    ('AL-051', 'Legiones Astartes - Saturnine Siege Dreadnought – Chiron Configuration', Decimal('66.03'),
     'https://www.firestormgames.co.uk/legiones-astartes---saturnine-siege-dreadnought--chiron-configuration?aff=6a4ab07d1c6f9'),
    ('AL-052', 'Horus Heresy - Tarantula Sentry Guns', Decimal('31.68'),
     'https://www.firestormgames.co.uk/horus-heresy---tarantula-sentry-guns?aff=6a4ab07d1c6f9'),
    ('AL-053', 'Horus Heresy - Tarantula Missile Battery', Decimal('31.68'),
     'https://www.firestormgames.co.uk/horus-heresy---tarantula-missile-battery?aff=6a4ab07d1c6f9'),
    ('AL-054', 'Horus Heresy - Legion Astartes Rapier Quad Heavy Bolters', Decimal('39.16'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes-rapier-quad-heavy-bolters?aff=6a4ab07d1c6f9'),
    ('AL-055', 'Horus Heresy - Rapier Laser Destroyer', Decimal('39.16'),
     'https://www.firestormgames.co.uk/horus-heresy---rapier-laser-destroyer?aff=6a4ab07d1c6f9'),
    ('AL-056', 'Horus Heresy - Legion Astartes Melee Weapons Upgrade', Decimal('26.40'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes-melee-weapons-upgrade?aff=6a4ab07d1c6f9'),
    ('AL-057', 'Legiones Astartes: MKIII Command Squad', Decimal('28.60'),
     'https://www.firestormgames.co.uk/legiones-astartes:-mkiii-command-squad?aff=6a4ab07d1c6f9'),
    ('AL-058', 'Legiones Astartes: MKVI Command Squad', Decimal('28.60'),
     'https://www.firestormgames.co.uk/legiones-astartes:-mkvi-command-squad?aff=6a4ab07d1c6f9'),
    ('AL-059', 'Horus Heresy - Legiones Astartes: Deredeo Dreadnought Anvilus Configuration', Decimal('47.96'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-deredeo-dreadnought-anvilus-configuration?aff=6a4ab07d1c6f9'),
    ('AL-060', 'Legiones Astartes - Centurion With Power Maul', Decimal('22.00'),
     'https://www.firestormgames.co.uk/legiones-astartes---centurion-with-power-maul?aff=6a4ab07d1c6f9'),
    ('AL-061', 'Leviathan Siege Dreadnought Close Combat Weapons Frame', Decimal('17.57'),
     'https://www.firestormgames.co.uk/leviathan-siege-dreadnought-close-combat-weapons-frame?aff=6a4ab07d1c6f9'),
    ('AL-062', 'Horus Heresy - Liber Hereticus', Decimal('39.16'),
     'https://www.firestormgames.co.uk/horus-heresy---liber-hereticus?aff=6a4ab07d1c6f9'),
    ('AL-063', 'Horus Heresy - Thousand Sons: Azhek Ahriman', Decimal('18.92'),
     'https://www.firestormgames.co.uk/horus-heresy---thousand-sons:-azhek-ahriman?aff=6a4ab07d1c6f9'),
    ('CM-001', 'Horus Heresy - Mechanicum Combat Force', Decimal('92.40'),
     'https://www.firestormgames.co.uk/horus-heresy---mechanicum-combat-force?aff=6a4ab07d1c6f9'),
    ('CM-002', 'Horus Heresy - Mechanicum Skitarii Battle-Pilgrym Marshal', Decimal('22.00'),
     'https://www.firestormgames.co.uk/horus-heresy---mechanicum-skitarii-battle-pilgrym-marshal?aff=6a4ab07d1c6f9'),
    ('CM-003', 'Horus Heresy - Mechanicum Vultarax Stratos-Automata', Decimal('43.56'),
     'https://www.firestormgames.co.uk/horus-heresy---mechanicum-vultarax-stratos-automata?aff=6a4ab07d1c6f9'),
    ('CM-004', 'Horus Heresy - Mechanicum Skitarii Battle-Pilgrym Corpus', Decimal('47.96'),
     'https://www.firestormgames.co.uk/horus-heresy---mechanicum-skitarii-battle-pilgrym-corpus?aff=6a4ab07d1c6f9'),
    ('CM-005', 'Horus Heresy - Ursarax Cohort', Decimal('41.36'),
     'https://www.firestormgames.co.uk/horus-heresy---ursarax-cohort?aff=6a4ab07d1c6f9'),
    ('CM-006', 'Horus Heresy - Krios Battle Tank', Decimal('41.80'),
     'https://www.firestormgames.co.uk/horus-heresy---krios-battle-tank?aff=6a4ab07d1c6f9'),
    ('CM-007', 'Horus Heresy - Karacnos Assault Tank', Decimal('59.40'),
     'https://www.firestormgames.co.uk/horus-heresy---karacnos-assault-tank?aff=6a4ab07d1c6f9'),
    ('CM-008', 'Horus Heresy - Thanatar Calix Siege-Automata', Decimal('56.76'),
     'https://www.firestormgames.co.uk/horus-heresy---thanatar-calix-siege-automata?aff=6a4ab07d1c6f9'),
    ('CM-009', 'Mechanicum: Archmagos Prime', Decimal('22.00'),
     'https://www.firestormgames.co.uk/mechanicum:-archmagos-prime?aff=6a4ab07d1c6f9'),
    ('CM-010', 'Mechanicum: Thallax Cohort', Decimal('43.56'),
     'https://www.firestormgames.co.uk/mechanicum:-thallax-cohort?aff=6a4ab07d1c6f9'),
    ('CM-011', 'Mechanicum: Triaros Armoured Conveyor', Decimal('51.04'),
     'https://www.firestormgames.co.uk/mechanicum:-triaros-armoured-conveyor?aff=6a4ab07d1c6f9'),
    ('CM-012', 'Mechanicum: Tech-Thralls Covenant', Decimal('43.56'),
     'https://www.firestormgames.co.uk/mechanicum:-tech-thralls-covenant?aff=6a4ab07d1c6f9'),
    ('CM-013', 'Mechanicum: Castellax Battle-Automata Maniple', Decimal('43.56'),
     'https://www.firestormgames.co.uk/mechanicum:-castellax-battle-automata-maniple?aff=6a4ab07d1c6f9'),
    ('CM-017', 'Horus Heresy - Mechanicum Myrmidon Destructor Host', Decimal('41.36'),
     'https://www.firestormgames.co.uk/horus-heresy---mechanicum-myrmidon-destructor-host?aff=6a4ab07d1c6f9'),
    ('CM-018', 'Mechanicum: Thanatar Cavas Siege-Automata', Decimal('56.76'),
     'https://www.firestormgames.co.uk/mechanicum:-thanatar-cavas-siege-automata?aff=6a4ab07d1c6f9'),
    ('FOE-001', 'Solar Auxilia: Rapier Fire Support Battery', Decimal('39.16'),
     'https://www.firestormgames.co.uk/solar-auxilia:-rapier-fire-support-battery?aff=6a4ab07d1c6f9'),
    ('FOE-002', 'Solar Auxilia: Rapier Direct Fire Battery', Decimal('39.16'),
     'https://www.firestormgames.co.uk/solar-auxilia:-rapier-direct-fire-battery?aff=6a4ab07d1c6f9'),
    ('FOE-003', 'Horus Heresy - Liber Auxilia', Decimal('28.60'),
     'https://www.firestormgames.co.uk/horus-heresy---liber-auxilia-?aff=6a4ab07d1c6f9'),
    ('FOE-004', 'Solar Auxilia: Charonite Ogryn Section', Decimal('39.16'),
     'https://www.firestormgames.co.uk/solar-auxilia:-charonite-ogryn-section?aff=6a4ab07d1c6f9'),
    ('FOE-005', 'Legio Custodes: Sentinel Guard Sodality', Decimal('39.16'),
     'https://www.firestormgames.co.uk/legio-custodes:-sentinel-guard-sodality?aff=6a4ab07d1c6f9'),
    ('FOE-006', 'Legio Custodes: Venatari Sodality', Decimal('43.56'),
     'https://www.firestormgames.co.uk/legio-custodes:-venatari-sodality?aff=6a4ab07d1c6f9'),
    ('FOE-007', 'Legio Custodes: Custodian Guard Sodality', Decimal('39.16'),
     'https://www.firestormgames.co.uk/legio-custodes:-custodian-guard-sodality?aff=6a4ab07d1c6f9'),
    ('FOE-008', 'Horus Heresy - Solar Auxilia Combat Force', Decimal('92.40'),
     'https://www.firestormgames.co.uk/horus-heresy---solar-auxilia-combat-force?aff=6a4ab07d1c6f9'),
    ('FOE-009', 'Solar Auxilia: Malcador Infernus', Decimal('57.20'),
     'https://www.firestormgames.co.uk/solar-auxilia:-malcador-infernus?aff=6a4ab07d1c6f9'),
    ('FOE-010', 'Solar Auxilia: Valdor Tank Destroyer', Decimal('50.16'),
     'https://www.firestormgames.co.uk/solar-auxilia:-valdor-tank-destroyer?aff=6a4ab07d1c6f9'),
    ('FOE-011', 'Horus Heresy - Arvus Lighter', Decimal('43.56'),
     'https://www.firestormgames.co.uk/horus-heresy---arvus-lighter?aff=6a4ab07d1c6f9'),
    ('FOE-012', 'Horus Heresy - Solar Auxilia Hermes Sentinel Squadron', Decimal('37.40'),
     'https://www.firestormgames.co.uk/horus-heresy---solar-auxilia-hermes-sentinel-squadron?aff=6a4ab07d1c6f9'),
    ('FOE-013', 'Horus Heresy - Solar Auxilia Basilisk/Medusa', Decimal('37.40'),
     'https://www.firestormgames.co.uk/horus-heresy---solar-auxilia-basiliskmedusa?aff=6a4ab07d1c6f9'),
    ('FOE-014', 'Solar Auxilia Leman Russ Assault Tank', Decimal('37.40'),
     'https://www.firestormgames.co.uk/solar-auxilia-leman-russ-assault-tank?aff=6a4ab07d1c6f9'),
    ('FOE-015', 'Horus Heresy - Solar Auxilia Malcador', Decimal('51.04'),
     'https://www.firestormgames.co.uk/horus-heresy---solar-auxilia-malcador?aff=6a4ab07d1c6f9'),
    ('FOE-016', 'Solar Auxilia: Veletaris Storm Section', Decimal('33.44'),
     'https://www.firestormgames.co.uk/solar-auxilia:-veletaris-storm-section?aff=6a4ab07d1c6f9'),
    ('FOE-017', 'Horus Heresy - Solar Auxilia Aethon Heavy Sentinel', Decimal('33.44'),
     'https://www.firestormgames.co.uk/horus-heresy---solar-auxilia-aethon-heavy-sentinel-?aff=6a4ab07d1c6f9'),
    ('FOE-018', 'Solar Auxilia: Tactical Command Section', Decimal('18.92'),
     'https://www.firestormgames.co.uk/solar-auxilia:-tactical-command-section?aff=6a4ab07d1c6f9'),
    ('FOE-019', 'Horus Heresy - Solar Auxilia Lasrifle Section', Decimal('43.56'),
     'https://www.firestormgames.co.uk/horus-heresy---solar-auxilia-lasrifle-section?aff=6a4ab07d1c6f9'),
    ('FOE-020', 'Solar Auxilia Leman Russ Strike Tank', Decimal('37.40'),
     'https://www.firestormgames.co.uk/solar-auxilia-leman-russ-strike-tank-?aff=6a4ab07d1c6f9'),
    ('FOE-021', 'Horus Heresy - Solar Auxilia Dracosan', Decimal('51.04'),
     'https://www.firestormgames.co.uk/horus-heresy---solar-auxilia-dracosan?aff=6a4ab07d1c6f9'),
    ('HA-001', 'Legiones Astartes - MKVI Tactical Squad', Decimal('47.96'),
     'https://www.firestormgames.co.uk/legiones-astartes---mkvi-tactical-squad?aff=6a4ab07d1c6f9'),
    ('HA-002', 'Legiones Astartes - Contemptor Dreadnought', Decimal('35.20'),
     'https://www.firestormgames.co.uk/legiones-astartes---contemptor-dreadnought?aff=6a4ab07d1c6f9'),
    ('HA-010', 'Horus Heresy - Legiones Astartes: MKIII Tactical Squad', Decimal('44.44'),
     'https://www.firestormgames.co.uk/horus-heresy---legiones-astartes:-mkiii-tactical-squad?aff=6a4ab07d1c6f9'),
    ('HA-012', 'Deimos Pattern Predator Battle Tank', Decimal('41.80'),
     'https://www.firestormgames.co.uk/deimos-pattern-predator-battle-tank?aff=6a4ab07d1c6f9'),
    ('HA-030', 'Horus Heresy - Legion Astartes: Cataphractii Terminators with Power Mauls', Decimal('37.40'),
     'https://www.firestormgames.co.uk/horus-heresy---legion-astartes:-cataphractii-terminators-with-power-mauls?aff=6a4ab07d1c6f9'),
    ('HA-040', 'Legiones Astartes - Spartan Assault Tank', Decimal('65.12'),
     'https://www.firestormgames.co.uk/legiones-astartes---spartan-assault-tank?aff=6a4ab07d1c6f9'),
    ('HA-041', 'Legiones Astartes - Sicaran Battle Tank', Decimal('48.40'),
     'https://www.firestormgames.co.uk/legiones-astartes---sicaran-battle-tank?aff=6a4ab07d1c6f9'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Warhammer: The Horus Heresy. Idempotent.'

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
                f'Seeded {seeded} Firestorm Games Horus Heresy prices. Skipped: {skipped}.'
            )
        )
