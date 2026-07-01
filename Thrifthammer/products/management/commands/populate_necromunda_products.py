"""
Management command: populate_necromunda_products

Creates / updates all Necromunda product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 70 products from the Necromunda.xlsx spreadsheet (2026-06-28).
Three pre-existing NM- gang boxes (Escher, Goliath, Van Saar) were already
in the DB — they are tagged by this command but not created by it.

Category: Necromunda (created if not present)
Faction:  Necromunda (created if not present)

Dual-tagged products (already in DB under other factions — NOT created here):
  GC-006  Genestealer Cults Atalan Jackals
  GC-010  Genestealer Cults Goliath Rockgrinder
  GC-011  Genestealer Cults Goliath Truck
  GC-016  Genestealer Cults Achilles Ridgerunner
  AM-044  Taurox
  → secondary faction tagging handled by add_necromunda_secondary_faction

Images are baked in as one-off GW CDN URLs — never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_necromunda_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

_EBAY_NEG_KEYWORDS = {
    'cargo-8-ridgehauler': 'Tanks Trailer Frames Promethium',
    'cawdor-gang': 'redemptionists',
}

_EBAY_ALLOWED_TITLE_WORDS = {
    # Root 1: '8' in 'Cargo-8' triggers standalone-digit filter
    'promethium-tanks-on-cargo-8-ridgehauler-trailer': '8',
    'cargo-8-ridgehauler-gunner-frames': '8',
    'cargo-8-ridgehauler-trailer': '8',
    'cargo-8-ridgehauler': '8',
    # Root 2: '&' in product name triggers bundle filter — scoped to these SKUs only
    'goliath-weapons-upgrades': '&',
    'van-saar-archeoteks-grav-cutters': '&',
    'palanite-enforcer-weapons-upgrades': '&',
    'palanite-enforcer-captains-sergeants': '&',
    'ironhead-squat-prospectors-weapons-upgrades': 'squat &',
    # Root 3: product name words that trigger the bits filter
    'orlock-arms-masters-and-wreckers': 'arms',
    'ironhead-squat-charter-masters-and-drill-masters': 'squat',
    'ironhead-squat-svenotar-scout-trikes': 'squat',
    'ironhead-squat-prospectors-exo-kyn': 'squat',
    'ironhead-squat-prospectors-gang': 'squat',
}

# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-28.
# ebay_search_name is blank unless the default name gives poor eBay results.
PRODUCTS = [

    # ── Starter Sets & Rules ─────────────────────────────────────────────────
    (
        'necromunda-hive-secundus',
        'NM-001',
        'Necromunda: Hive Secundus',
        180.00,
        '60010599005_NECHiveSecundusGame01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-hive-secundus-2024',
        '',
    ),
    (
        'necromunda-hive-war',
        'NM-002',
        'Necromunda: Hive War',
        190.00,
        '60010599003_HiveWarLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Hive-War-EN-2021',
        'Necromunda Hive War Warhammer',
    ),
    (
        'necromunda-core-rulebook',
        'NM-003',
        'Necromunda: Core Rulebook',
        73.50,
        '60040599042_NECCoreRulebook01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-rulebook-eng-2023',
        '',
    ),

    # ── Enforcers ────────────────────────────────────────────────────────────
    (
        'enforcer-sanctioner-pattern-automata',
        'NM-004',
        "Enforcer 'Sanctioner' Pattern Automata",
        53.00,
        '99120599042_NECEnforcerSancAutomata02.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-enforcer-sanctioner-automata-2023',
        '',
    ),
    (
        'palanite-enforcer-patrol',
        'NM-013',
        'Palanite Enforcer Patrol',
        53.00,
        '99120599011_NECPalaniteEnforcerPatrol01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Palanite-Enforcer-Patrol-2019',
        '',
    ),
    (
        'palanite-subjugator-patrol',
        'NM-040',
        'Palanite Subjugator Patrol',
        53.00,
        '99120599012_PalaniteSubjucatorPatrol01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Palanite-Subjugator-Patrol-2020',
        '',
    ),
    (
        'palanite-enforcer-tauros-venator',
        'NM-062',
        'Palanite Enforcer Tauros Venator',
        60.00,
        '99120599065_PalaniteEnforcerTaurusVenatorConcussionCannons1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-palanite-enforcer-tauros-venator-2023',
        '',
    ),
    (
        'palanite-enforcer-weapons-upgrades',
        'NM-044',
        'Palanite Enforcer Weapons & Upgrades',
        32.00,
        '99120599109_NecromundaEnforcerWeaponsUpgrades1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-enforcer-weapons-and-upgrades-2025',
        'Palanite Enforcer Weapons & Upgrades Necromunda Warhammer',
    ),
    (
        'palanite-justicars',
        'NM-046',
        'Palanite Justicars',
        43.50,
        '99120599091_NecromundaPalaniteJusticars1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-palanite-justicars-2025',
        '',
    ),
    (
        'palanite-enforcer-captains-sergeants',
        'NM-049',
        'Palanite Enforcer Captains & Sergeants',
        53.00,
        '99120599080_NecromundaPalaniteEnforcerCaptainsSergeants1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-palatine-enforcer-captains-and-sergeants-2025',
        'Palanite Enforcer Captains & Sergeants Necromunda Warhammer',
    ),

    # ── Van Saar ─────────────────────────────────────────────────────────────
    # Van Saar Gang is a pre-existing NM-012 record — tagged below, not created here.
    (
        'van-saar-weapons-upgrades',
        'NM-029',
        'Van Saar Weapons & Upgrades',
        32.00,
        '99120599033_VanSaarWeaponsUpgradesLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-van-saar-weapons-and-upgrades-2021',
        '',
    ),
    (
        'van-saar-archeoteks-grav-cutters',
        'NM-035',
        'Van Saar Archeoteks & Grav-cutters',
        53.00,
        '99120599024_NECVanSaaeArcheoteksGravcuttersLead.jpg',
        'https://www.warhammer.com/en-US/shop/Van-Saar-Archeoteks-and-Grav-cutters-2020',
        'Van Saar Archeoteks & Grav-Cutters Necromunda Warhammer',
    ),
    (
        'van-saar-ash-wastes-arachni-rig',
        'NM-063',
        'Van Saar Ash Wastes Arachni-rig',
        53.00,
        '99120599056_VanSaarArachnirig2.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-van-saar-ash-wastes-arachni-rig-2023',
        '',
    ),
    (
        'van-saar-tek-hunters',
        'NM-057',
        'Van Saar Tek-hunters',
        53.00,
        '99120599068_NMVanSaarTekHunters01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-van-saar-tek-hunters-2024',
        '',
    ),

    # ── Cawdor ───────────────────────────────────────────────────────────────
    (
        'cawdor-gang',
        'NM-006',
        'Cawdor Gang',
        53.00,
        '99120599007_CawdorGang01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Cawdor-Gang-2018',
        '',
    ),
    (
        'cawdor-ridge-walkers',
        'NM-014',
        'Cawdor Ridge Walkers',
        53.00,
        '99120599057_CawdorRidgeWalkers2.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-cawdor-ridge-walkers-2023',
        '',
    ),
    (
        'cawdor-redemptionists',
        'NM-032',
        'Cawdor Redemptionists',
        53.00,
        '99120599025_CawdorRedemptionistsLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Cawdor-Redemptionists-2021',
        '',
    ),
    (
        'cawdor-weapons-upgrades',
        'NM-066',
        'Cawdor Weapons & Upgrades',
        32.00,
        '99120599031_NECCawdorWeaponsandUpgradesLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-cawdor-weapons-and-upgrades-2021',
        '',
    ),

    # ── Delaque ──────────────────────────────────────────────────────────────
    (
        'delaque-gang',
        'NM-007',
        'Delaque Gang',
        53.00,
        '99120599008_DelaqueGang01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Delaque-Gang-2018',
        '',
    ),
    (
        'delaque-weapons-upgrades',
        'NM-027',
        'Delaque Weapons & Upgrades',
        32.00,
        '99120599041_NECDelaqueWeaponsandUpgradesLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-delaque-weapons-2022',
        '',
    ),
    (
        'delaque-nacht-ghul-psy-gheists-and-piscean-spektor',
        'NM-031',
        'Delaque Nacht-Ghul, Psy-Gheists and Piscean Spektor',
        53.00,
        '99120599028_NECDelaqueNachtGhulandPsyGheistsLead.jpg',
        'https://www.warhammer.com/en-US/shop/delaque-nacht-ghul-and-psy-gheists-2021',
        '',
    ),

    # ── Orlock ───────────────────────────────────────────────────────────────
    (
        'orlock-gang',
        'NM-008',
        'Orlock Gang',
        53.00,
        '99120599005_OrlockGang01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Orlock-Gang-2018',
        '',
    ),
    (
        'orlock-outrider-quads',
        'NM-024',
        'Orlock Outrider Quads',
        53.00,
        '99120599037_OrlockOutriderQuadsLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-orlock-outrider-quads-2022',
        '',
    ),
    (
        'orlock-weapons-upgrades',
        'NM-030',
        'Orlock Weapons & Upgrades',
        32.00,
        '99120599029_NECOrlockWeaponsUpgradesLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-orlock-weapons-upgrades-2021',
        '',
    ),
    (
        'orlock-arms-masters-and-wreckers',
        'NM-036',
        'Orlock Arms Masters and Wreckers',
        53.00,
        '99120599023_OrlockArmsMastersWreckersLead.jpg',
        'https://www.warhammer.com/en-US/shop/Orlock-Arms-Masters-and-Wreckers-2020',
        'Necromunda Orlock Arms Masters and Wreckers Warhammer',
    ),

    # ── Escher ───────────────────────────────────────────────────────────────
    # Escher Gang is a pre-existing NM-010 record — tagged below, not created here.
    (
        'escher-cutters',
        'NM-017',
        'Escher Cutters',
        53.00,
        '99120599046_EscherCuttersLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-escher-cutters-2022',
        '',
    ),
    (
        'escher-weapons-upgrades',
        'NM-034',
        'Escher Weapons & Upgrades',
        32.00,
        '99120599026_EscherWeapsUpgradesLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Escher-Weapons-and-Upgrades-2021',
        '',
    ),
    (
        'escher-death-maidens-and-wyld-runners',
        'NM-038',
        'Escher Death-maidens and Wyld Runners',
        53.00,
        '99120599019_EscherDMWRLead.jpg',
        'https://www.warhammer.com/en-US/shop/Escher-Death-Maidens-and-Wyld-Runners-2020',
        '',
    ),

    # ── Goliath ──────────────────────────────────────────────────────────────
    # Goliath Gang is a pre-existing NM-011 record — tagged below, not created here.
    (
        'goliath-weapons-upgrades',
        'NM-033',
        'Goliath Weapons & Upgrades',
        32.00,
        '99120599027_GoliathWeaponsUpgradesLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Goliath-Weapons-and-Upgrades-2021',
        'Goliath Weapons & Upgrades Necromunda Warhammer',
    ),
    (
        'goliath-stimmers-and-forge-born',
        'NM-039',
        'Goliath Stimmers and Forge-born',
        53.00,
        '99120599018_GoliathStimmers01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Goliath-Stimmers-And-Forgeborn-2020',
        '',
    ),
    (
        'goliath-maulters',
        'NM-064',
        'Goliath Maulters',
        53.00,
        '99120599034_NECGoliathMaulersFeature.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-goliath-maulers-2022',
        'Goliath Maulers Necromunda Warhammer',
    ),

    # ── Corpse Grinder Cult ──────────────────────────────────────────────────
    (
        'corpse-grinder-cult-gang',
        'NM-074',
        'Corpse Grinder Cult Gang',
        53.00,
        '99120599013_CorpseGrinderCult01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Corpse-Grinder-Cult-2020',
        '',
    ),

    # ── Ironhead Squat Prospectors ───────────────────────────────────────────
    (
        'ironhead-squat-prospectors-gang',
        'NM-075',
        'Ironhead Squat Prospectors Gang',
        53.00,
        '99120599038_NECIronheadSquatProspectorsLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-ironhead-squat-prospectors-2022',
        'Necromunda: Ironhead Squat Prospectors Gang Warhammer',
    ),
    (
        'ironhead-squat-charter-masters-and-drill-masters',
        'NM-045',
        'Ironhead Squat Charter Masters and Drill Masters',
        53.00,
        '99120599092_NecromundaIronheadSquatCharterDrillMasters1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-ironhead-squat-charter-and-drill-masters-2025',
        'Ironhead Squat Charter Masters and Drill Masters Necromunda Warhammer',
    ),
    (
        'ironhead-squat-svenotar-scout-trikes',
        'NM-054',
        'Ironhead Squat Svenotar Scout Trikes',
        53.00,
        '99120599074_NECIronheadSquatProspectorSvenotarScoutTrike01.jpg',
        'https://www.warhammer.com/en-US/shop/ironhead-squat-svenotar-scout-trikes-2024',
        'Necromunda: Ironhead Squat Svenotar Scout Trikes Warhammer',
    ),
    (
        'ironhead-squat-prospectors-weapons-upgrades',
        'NM-055',
        'Ironhead Squat Prospectors Weapons & Upgrades',
        32.00,
        '99120599070_NECIronheadSquatProspectorsWeaponsAndUpgrades01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-squat-prospectors-weapons-and-upgrades-2024',
        'Ironhead Squat Prospectors Weapons & Upgrades Necromunda Warhammer',
    ),
    (
        'ironhead-squat-prospectors-exo-kyn',
        'NM-056',
        'Ironhead Squat Prospectors Exo-kyn',
        53.00,
        '99120599073_NECIronheadProspectorsExoKyn01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-squat-prospectors-exo-kyn-2024',
        'Necromunda: Ironhead Squat Prospectors Exo-Kyn Warhammer',
    ),

    # ── Ash Waste Nomads ─────────────────────────────────────────────────────
    (
        'ash-waste-nomads-dustback-helamites',
        'NM-025',
        'Ash Waste Nomads Dustback Helamites',
        53.00,
        '99120599036_AshWasteDustbackHelamitesLead.jpg',
        'https://www.warhammer.com/en-US/shop/ash-waste-nomads-dustback-helamites-2022',
        '',
    ),
    (
        'ash-waste-nomads-war-party',
        'NM-026',
        'Ash Waste Nomads War Party',
        53.00,
        '99120599035_AshWasteNomadWarPartyLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-ash-wastes-nomads-war-party-2022',
        '',
    ),
    (
        'ash-waste-nomads-weapons-upgrades',
        'NM-052',
        'Ash Waste Nomads: Weapons & Upgrades',
        32.00,
        '99120599075_NecromundaAshWastesNomadsWeaponsUpgrades1.jpg',
        'https://www.warhammer.com/en-US/shop/ash-waste-nomads-weapons-and-upgrades-2025',
        '',
    ),
    (
        'ashwing-helamites',
        'NM-048',
        'Ashwing Helamites',
        53.00,
        '99120599082_NecromundaAshWastesNomadsAshwingHelemites1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-nomads-ashwing-helamites-2025',
        '',
    ),
    (
        'shadar-hunters-and-arthromite-spinewyrms',
        'NM-053',
        "Sha'dar Hunters and Arthromite Spinewyrms",
        53.00,
        '99120599076_NecromundaAshWastesShadarHuntersArthromiteSpinewyrms1.jpg',
        'https://www.warhammer.com/en-US/shop/shadar-hunters-and-arthromite-spinewyrms-2025',
        '',
    ),

    # ── Malstrain ────────────────────────────────────────────────────────────
    (
        'malstrain-genestealer-abomination-gang',
        'NM-073',
        'Malstrain Genestealer Abomination Gang',
        53.00,
        '99120599066_NMMalstrainGenestealerAbominationGang01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-genestealer-abomination-gang-2024',
        '',
    ),

    # ── Spyre Hunters ────────────────────────────────────────────────────────
    (
        'malcadon-yeld-and-jakara-spyre-hunters',
        'NM-058',
        'Malcadon, Yeld, and Jakara Spyre Hunters',
        53.00,
        '99120599072_NMMalcadonYeldAndJakaraSpyreHunters01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-malcadon-yeld-and-jakara-spyre-hunter-2024',
        '',
    ),
    (
        'orrus-spyre-hunters',
        'NM-059',
        'Orrus Spyre Hunters',
        53.00,
        '99120599067_NMOrrusSpyreHunters01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-orrus-spyre-hunters-2024',
        '',
    ),

    # ── Hired Guns & Hangers-on ──────────────────────────────────────────────
    (
        'hive-scum',
        'NM-028',
        'Hive Scum',
        21.50,
        '99120599039_HiveScumLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-hive-scum-2022',
        '',
    ),
    (
        'jotunn-h-grade-industrial-servitor-ogryns',
        'NM-037',
        "'Jotunn' H-Grade Industrial Servitor Ogryns",
        48.50,
        '99120599020_JotunnHGraIndSerOgrLead.jpg',
        'https://www.warhammer.com/en-US/shop/Jotunn-H-grade-Servitor-Ogryns-2020',
        '',
    ),
    (
        'luther-pattern-excavation-automata-ambot',
        'NM-041',
        'Luther Pattern Excavation Automata "Ambot"',
        53.00,
        '99120599009_NECAmbot01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Ambot-2019',
        '',
    ),
    (
        'kal-jericho-and-scabs',
        'NM-071',
        'Kal Jericho and Scabs',
        39.00,
        '99120599010_KalJerichoandScabs01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Kal-Jerico-and-Scabs-2019',
        '',
    ),
    (
        'underhive-hangers-on',
        'NM-043',
        'Underhive Hangers-on',
        43.50,
        '99120599084_NecromundaUnderhiveHangerson1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-underhive-hangers-on-2025',
        '',
    ),
    (
        'ozostium-aranthus-the-divine-prince',
        'NM-047',
        'Ozostium Aranthus, the Divine Prince',
        40.00,
        '99120599093_NecromundaOzostiumAranthusDivinePrince1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-ozostium-aranthus-2025',
        '',
    ),

    # ── Vehicles ─────────────────────────────────────────────────────────────
    (
        'promethium-tanks-on-cargo-8-ridgehauler-trailer',
        'NM-015',
        'Promethium Tanks on Cargo-8 Ridgehauler Trailer',
        65.00,
        '99120599060_NECPromethiumTanksonCargo8RidgehaulerTrailerLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-promethium-tanks-on-cargo-8-trailer-2022',
        'Promethium Tanks on Cargo-8 Necromunda Warhammer',
    ),
    (
        'promethium-tanks-refuelling-station',
        'NM-016',
        'Promethium Tanks Refuelling Station',
        53.00,
        '99120599053_NECPromethiumTanksRefuellingStationLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-promethium-tanks-refuelling-station-2022',
        '',
    ),
    (
        'cargo-8-ridgehauler-gunner-frames',
        'NM-018',
        'Cargo-8 Ridgehauler Gunner Frames',
        32.00,
        '99120599055_Cargo8RHGunnerFrameLead.jpg',
        'https://www.warhammer.com/en-US/shop/cargo-8-ridgehauler-gunner-frames-2022',
        'Cargo-8 Ridgehauler Gunner Frames Warhammer',
    ),
    (
        'cargo-8-ridgehauler-trailer',
        'NM-019',
        'Cargo-8 Ridgehauler Trailer',
        65.00,
        '99120599054_Cargo8TrailerLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-cargo-8-ridgehauler-trailer-2022',
        'Cargo-8 Ridgehauler Trailer Necromunda Warhammer',
    ),
    (
        'cargo-8-ridgehauler',
        'NM-020',
        'Cargo-8 Ridgehauler',
        106.00,
        '99120599043_NECCargo8RidgehaulerLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-cargo-8-ridgehauler-2022',
        'Cargo-8 Ridgehauler',
    ),

    # ── Accessories ──────────────────────────────────────────────────────────
    (
        'necromunda-barricades-and-objectives',
        'NM-042',
        'Necromunda Barricades and Objectives',
        48.50,
        '99120599001_NecromundaBarricades00.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Barricades-Objectives-2017',
        '',
    ),
    (
        'trazior-pattern-sentry-guns',
        'NM-072',
        'Trazior Pattern Sentry Guns',
        43.50,
        '99120599059_NMTraziorPatternSentryGuns01.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-trazior-pattern-sentry-guns-2024',
        '',
    ),
    (
        'hive-data-stack-cluster',
        'NM-061',
        'Hive Data Stack Cluster',
        53.00,
        '99120599069_HiveDataStackCluster1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-hive-data-stack-cluster-2024',
        '',
    ),

    # ── Terrain: Thatos Pattern ──────────────────────────────────────────────
    (
        'thatos-pattern-extended-hab-module',
        'NM-021',
        'Thatos Pattern: Extended Hab Module',
        112.00,
        '99120599048_NECTPExtendedHabModuleLead.jpg',
        'https://www.warhammer.com/en-US/shop/thatos-pattern-extended-hab-module-2022',
        '',
    ),
    (
        'thatos-pattern-platforms-walkways',
        'NM-022',
        'Thatos Pattern: Platforms & Walkways',
        82.00,
        '99120599047_NECTPWalkwaySetLead.jpg',
        'https://www.warhammer.com/en-US/shop/thatos-pattern-platforms-and-walkways-2022',
        '',
    ),
    (
        'thatos-pattern-hab-module',
        'NM-023',
        'Thatos Pattern: Hab Module',
        82.00,
        '99120599044_NECTPHabModuleLead.jpg',
        'https://www.warhammer.com/en-US/shop/thatos-pattern-hab-module-2022',
        '',
    ),
    (
        'thatos-pattern-fortified-hab-module',
        'NM-051',
        'Thatos Pattern Fortified Hab Module',
        114.00,
        '99120599071_ThatosPatternFortifiedHabModule1.jpg',
        'https://www.warhammer.com/en-US/shop/thatos-pattern-fortified-hab-module-2025',
        '',
    ),

    # ── Terrain: Zone Mortalis ────────────────────────────────────────────────
    (
        'zone-mortalis-floor-tile-set',
        'NM-070',
        'Zone Mortalis: Floor Tile Set',
        85.00,
        '99120599017_NECZoneMortalisFloorTile01.jpg',
        'https://www.warhammer.com/en-US/shop/Necromunda-Zone-Mortalis-Floor-Tile-Set-2019',
        '',
    ),
    (
        'necromunda-zone-mortalis-columns-and-walls',
        'NM-069',
        'Necromunda Zone Mortalis Columns and Walls',
        102.00,
        '99120599014_ZMCW01.jpg',
        'https://www.warhammer.com/en-US/shop/Zone-Mortalis-Columns-And-Walls-2020',
        '',
    ),
    (
        'necromunda-zone-mortalis-platforms-and-stairs',
        'NM-068',
        'Necromunda Zone Mortalis Platforms and Stairs',
        82.00,
        '99120599015_NECZMPlatformsStairs01.jpg',
        'https://www.warhammer.com/en-US/shop/Zone-Mortalis-Platforms-And-Stairs-2020',
        '',
    ),
    (
        'zone-mortalis-gang-stronghold',
        'NM-067',
        'Zone Mortalis: Gang Stronghold',
        106.00,
        '99120599030_ZoneMortalisGangStrongholdLead.jpg',
        'https://www.warhammer.com/en-US/shop/Zone-Mortalis-Gang-Stronghold-2020',
        '',
    ),
    (
        'zone-mortalis-underhive-market',
        'NM-065',
        'Zone Mortalis: Underhive Market',
        60.00,
        '99120599045_NECUnderhiveMarketLead.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-zone-mortalis-underhive-market-2021',
        '',
    ),
    (
        'ruined-zone-mortalis',
        'NM-060',
        'Ruined Zone Mortalis',
        90.00,
        '99120599081_RuinedZoneMortalis1.jpg',
        'https://www.warhammer.com/en-US/shop/necromunda-ruined-zone-mortalis-2024',
        '',
    ),
    (
        'zone-mortalis-ruined-underhive-sector',
        'NM-050',
        'Zone Mortalis: Ruined Underhive Sector',
        175.00,
        '99120599083_NMZoneMortalisRuinedUnderhiveSectorTerrainExtra01.jpg',
        'https://www.warhammer.com/en-US/shop/zone-mortalis-ruined-underhive-sector-2025',
        '',
    ),
]


class Command(BaseCommand):
    """Populate Necromunda products (70 created + 3 pre-existing tagged) and seed GW prices."""

    help = (
        'Creates / updates 70 Necromunda products and seeds GW prices at MSRP. '
        'Tags 3 pre-existing gang boxes with the Necromunda faction. '
        'Also creates the Necromunda category and faction if not present. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        necromunda_category, cat_created = Category.objects.get_or_create(
            slug='necromunda',
            defaults={'name': 'Necromunda'},
        )
        if cat_created:
            self.stdout.write(self.style.SUCCESS('  Created category: Necromunda'))

        necromunda_faction, fac_created = Faction.objects.get_or_create(
            slug='necromunda',
            defaults={
                'name': 'Necromunda',
                'category': necromunda_category,
            },
        )
        if fac_created:
            self.stdout.write(self.style.SUCCESS('  Created faction: Necromunda'))

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
                    'ebay_negative_keywords': _EBAY_NEG_KEYWORDS.get(slug, ''),
                    'ebay_allowed_title_words': _EBAY_ALLOWED_TITLE_WORDS.get(slug, ''),
                    'category': necromunda_category,
                    'faction': necromunda_faction,
                    'is_active': True,
                    'batch_tag': 'necromunda',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} ({gw_sku})'))
            if created:
                product_created += 1
            else:
                product_updated += 1

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

        # Tag pre-existing gang boxes (NM-010 Escher, NM-011 Goliath, NM-012 Van Saar)
        # that existed before this populate command was written.
        pre_existing_slugs = [
            'necromunda-escher-gang',
            'necromunda-goliath-gang',
            'necromunda-van-saar-gang',
        ]
        tagged = Product.objects.filter(slug__in=pre_existing_slugs).update(
            faction=necromunda_faction,
            batch_tag='necromunda',
        )
        if tagged:
            self.stdout.write(f'  Tagged {tagged} pre-existing Necromunda gang product(s).')

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_necromunda_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
