"""
Management command: seed_amazon_prices

Writes all verified Amazon prices (from the March 2026 Octoparse scrape)
into the production database, keyed by GW SKU.

All ASINs manually verified on Amazon.com in March 2026.
Wrong matches corrected; products with no Amazon listing removed.

Usage:
    python manage.py seed_amazon_prices
    python manage.py seed_amazon_prices --dry-run
"""

import decimal

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ---------------------------------------------------------------------------
# Verified Amazon matches  (gw_sku -> (price_str, url, in_stock))
# All ASINs hand-verified on Amazon.com — March 2026 Octoparse scrape.
# ---------------------------------------------------------------------------
AMAZON_DATA = {
    # ── Adepta Sororitas (Sisters of Battle) ──────────────────────────────
    '52-20': ('55.25',  'https://www.amazon.com/dp/B083P7M8TF', True),   # Battle Sisters Squad
    '52-25': ('143.89', 'https://www.amazon.com/dp/B0D63B2XCY', False),  # Combat Patrol
    '52-08': ('78.20',  'https://www.amazon.com/dp/B09HH3Z7ZC', True),   # Exorcist
    '52-09': ('71.40',  'https://www.amazon.com/dp/B09HJC9CFQ', True),   # Immolator
    '52-02': ('55.00',  'https://www.amazon.com/dp/B0968RM9H1', True),   # Morvenn Vahl
    '52-15': ('53.66',  'https://www.amazon.com/dp/B083P6HN5P', True),   # Retributor Squad
    '52-12': ('55.25',  'https://www.amazon.com/dp/B085Q29R7P', True),   # Seraphim Squad
    # ── Adepta Sororitas phase-2 (AS-xxx SKUs) — prices TBD, scraper will update ──
    'AS-001': ('', 'https://www.amazon.com/dp/B0GXWY9XHL', False),   # Armageddon Battalion
    'AS-002': ('', 'https://www.amazon.com/dp/B0968R7668', False),   # Celestian Insidiants
    'AS-003': ('', 'https://www.amazon.com/dp/B0GXX3LWWV', False),   # Intranzia Fraye - Dogmata Superior
    'AS-004': ('', 'https://www.amazon.com/dp/1804573965', False),   # Codex: Adepta Sororitas
    'AS-005': ('', 'https://www.amazon.com/dp/B0FCG9TJ21', False),   # Kill Team: Sanctifiers
    # AS-006 Aestred Thurga — no Amazon listing
    'AS-007': ('', 'https://www.amazon.com/dp/B09B7WW1BV', False),   # Castigator
    'AS-008': ('', 'https://www.amazon.com/dp/B0968PW797', False),   # Paragon Warsuits
    'AS-009': ('', 'https://www.amazon.com/dp/B0968NKKQ3', False),   # Palatine
    'AS-010': ('', 'https://www.amazon.com/dp/B08BNPCD55', False),   # Daemonifuge - Ephrael Stern & Kyganil
    'AS-011': ('', 'https://www.amazon.com/dp/B085Q29R7P', False),   # Zephyrim Squad  ⚠ same kit as 52-12 Seraphim Squad
    'AS-012': ('', 'https://www.amazon.com/dp/B09CLJHHVB', False),   # Rhino
    'AS-013': ('', 'https://www.amazon.com/dp/B085PWHGLX', False),   # Repentia Squad
    'AS-014': ('', 'https://www.amazon.com/dp/B09HJLK4Z8', False),   # Canoness
    'AS-015': ('', 'https://www.amazon.com/dp/B085Q24S9T', False),   # Dialogus
    'AS-016': ('', 'https://www.amazon.com/dp/B09HJH84JR', False),   # Imagifier
    'AS-017': ('', 'https://www.amazon.com/dp/B09XKS4PML', False),   # Arco-flagellants
    'AS-018': ('', 'https://www.amazon.com/dp/B083ZJB1K9', False),   # Junith Eruita
    'AS-019': ('', 'https://www.amazon.com/dp/B09HJLL599', False),   # Hospitaller
    'AS-020': ('', 'https://www.amazon.com/dp/B083P6J94L', False),   # The Triumph of Saint Katherine
    'AS-021': ('', 'https://www.amazon.com/dp/B09HJDZQ5M', False),   # Celestine, the Living Saint
    'AS-022': ('', 'https://www.amazon.com/dp/B083P7M8TF', False),   # Dominion Squad  ⚠ same kit as 52-20 Battle Sisters Squad
    'AS-023': ('', 'https://www.amazon.com/dp/B0FNS2C4VW', False),   # Sisters Novitiate Squad
    'AS-024': ('', 'https://www.amazon.com/dp/B0DJFGFGSB', False),   # Canoness with Jump Pack
    'AS-025': ('', 'https://www.amazon.com/dp/B0DC6NVD8N', False),   # Ministorum Priest
    'AS-026': ('', 'https://www.amazon.com/dp/B0D63BGVJW', False),   # Ministorum Priest with Vindictor
    'AS-027': ('', 'https://www.amazon.com/dp/B096SJWN6B', False),   # Sister Dogmata
    'AS-028': ('', 'https://www.amazon.com/dp/B083ZHWJYC', False),   # Mortifiers  ⚠ same kit as AS-029
    'AS-029': ('', 'https://www.amazon.com/dp/B083ZHWJYC', False),   # Penitent Engines  ⚠ same kit as AS-028
    'AS-030': ('', 'https://www.amazon.com/dp/B07TDV4N2V', False),   # Sister Superior Amalia Novena

    # ── Adeptus Custodes ──────────────────────────────────────────────────
    '01-20': ('138.53', 'https://www.amazon.com/dp/B0D14W3KTM', True),   # Combat Patrol
    '01-08': ('55.25',  'https://www.amazon.com/dp/B06XT84VV8', False),  # Custodian Guard
    '01-10': ('53.13',  'https://www.amazon.com/dp/B079CJ6YLL', True),   # Custodian Wardens
    '01-07': ('35.70',  'https://www.amazon.com/dp/B0D639NL6S', True),   # Shield-Captain  ✓ FIXED (old B0795XTD6L was wrong product)
    '01-02': ('40.80',  'https://www.amazon.com/dp/B0795Y92B5', True),   # Trajann Valoris  ✓ FIXED (price updated $62.48→$40.80)
    '01-11': ('52.18',  'https://www.amazon.com/dp/B09TM1TGZ3', True),   # Vertus Praetors

    # ── Adeptus Mechanicus ────────────────────────────────────────────────
    '59-25': ('138.29', 'https://www.amazon.com/dp/B0CNTTMBPD', True),   # Combat Patrol
    '59-16': ('71.40',  'https://www.amazon.com/dp/B00WA4QHPQ', True),   # Dunecrawler
    '59-20': ('48.99',  'https://www.amazon.com/dp/B00YHWCMO4', True),   # Electropriests  ✓ FIXED (old B095J6PXFF was bundle, not unit box)
    '59-18': ('55.25',  'https://www.amazon.com/dp/B00XTZUSB4', True),   # Kataphron Destroyers  ✓ FIXED (old B0CNTVKXZD was Kastelans)
    '59-10': ('49.30',  'https://www.amazon.com/dp/B00VE6WTPI', True),   # Skitarii Rangers
    '59-11': ('49.30',  'https://www.amazon.com/dp/B00VE6WTPI', True),   # Skitarii Vanguard (same kit)
    '59-06': ('33.15',  'https://www.amazon.com/dp/B09BBKFJD4', True),   # Tech-Priest Dominus
    # ── Adeptus Mechanicus phase-2 (MC-xxx SKUs) — prices TBD, scraper will update ──
    # ⚠ MC-001/002/003 Archaeopter (Fusilave/Stratoraptor/Transvector) share one kit/ASIN
    'MC-001': ('', 'https://www.amazon.com/dp/B0899J6L6G', False),   # Archaeopter Fusilave
    'MC-002': ('', 'https://www.amazon.com/dp/B0899J6L6G', False),   # Archaeopter Stratoraptor  ⚠ same kit
    'MC-003': ('', 'https://www.amazon.com/dp/B0899J6L6G', False),   # Archaeopter Transvector   ⚠ same kit
    'MC-004': ('', 'https://www.amazon.com/dp/B0FNS1MKFZ', False),   # Battleclade (Kill Team)
    'MC-005': ('', 'https://www.amazon.com/dp/B075R36H3Q', False),   # Belisarius Cawl
    'MC-006': ('', 'https://www.amazon.com/dp/B09HJX1435', False),   # Fulgurite Electro-Priests
    'MC-007': ('', 'https://www.amazon.com/dp/B0GVGFNX61', False),   # Hastarii
    'MC-008': ('', 'https://www.amazon.com/dp/B096YZ167X', False),   # Kastelan Robots
    'MC-009': ('', 'https://www.amazon.com/dp/B00XTZUSB4', False),   # Kataphron Breachers  ⚠ same kit as 59-18 Kataphron Destroyers
    # ⚠ MC-010/011 Pteraxii (Skystalkers/Sterylizors) share one kit/ASIN
    'MC-010': ('', 'https://www.amazon.com/dp/B0899FYZHD', False),   # Pteraxii Skystalkers
    'MC-011': ('', 'https://www.amazon.com/dp/B0899FYZHD', False),   # Pteraxii Sterylizors  ⚠ same kit
    # ⚠ MC-012/013 Serberys (Raiders/Sulphurhounds) share one kit/ASIN
    'MC-012': ('', 'https://www.amazon.com/dp/B0899MR5DQ', False),   # Serberys Raiders
    'MC-013': ('', 'https://www.amazon.com/dp/B0899MR5DQ', False),   # Serberys Sulphurhounds  ⚠ same kit
    # ⚠ MC-014/015 Sicarians (Infiltrators/Ruststalkers) share one kit/ASIN
    'MC-014': ('', 'https://www.amazon.com/dp/B096G7QHD3', False),   # Sicarian Infiltrators
    'MC-015': ('', 'https://www.amazon.com/dp/B096G7QHD3', False),   # Sicarian Ruststalkers  ⚠ same kit
    'MC-016': ('', 'https://www.amazon.com/dp/B095J4QXSW', False),   # Skitarii Marshal
    # ⚠ MC-017/018 Skorpius (Disintegrator/Dunerider) share one kit/ASIN
    'MC-017': ('', 'https://www.amazon.com/dp/B07TS4QN8W', False),   # Skorpius Disintegrator
    'MC-018': ('', 'https://www.amazon.com/dp/B07TS4QN8W', False),   # Skorpius Dunerider  ⚠ same kit
    'MC-019': ('', 'https://www.amazon.com/dp/B0965W1ZD8', False),   # Sydonian Dragoon (Ironstrider kit)
    'MC-020': ('', 'https://www.amazon.com/dp/B0CNTVKXZD', False),   # Sydonian Skatros
    # MC-021 Technoarcheologist — no Amazon listing
    'MC-022': ('', 'https://www.amazon.com/dp/B09BBKFJD4', False),   # Tech-Priest Enginseer  ⚠ same ASIN as 59-06
    'MC-023': ('', 'https://www.amazon.com/dp/B00YHVDG6S', False),   # Tech-Priest Manipulus
    'MC-024': ('', 'https://www.amazon.com/dp/B0GVGFP28V', False),   # Thulia Ghuld
    'MC-025': ('', 'https://www.amazon.com/dp/1804572780', False),   # Codex: Adeptus Mechanicus

    # ── Age of Sigmar ─────────────────────────────────────────────────────
    '80-20': ('26.70',  'https://www.amazon.com/dp/B0D8LHNZB2', True),   # Dice Set
    # 80-15 Warrior Starter Set — SKU deactivated Mar 2026 (discontinued); removed from seed

    # ── Orruk Warclans ────────────────────────────────────────────────────
    '89-30': ('55.25',  'https://www.amazon.com/dp/B0CHRYV6WD', True),   # Ardboys  ✓ FIXED wave F (old B0CHRXGQ8N $33.15 wrong)
    '89-22': ('51.00',  'https://www.amazon.com/dp/B09GBLLTKZ', True),   # Gutrippaz
    '89-20': ('53.13',  'https://www.amazon.com/dp/B01EVDPFBK', True),   # Ironjawz Brutes
    '89-06': ('53.86',  'https://www.amazon.com/dp/B07MFCSZCZ', True),   # Gloomspite Fanatics
    '89-11': ('51.00',  'https://www.amazon.com/dp/B0FGK5WQJL', True),   # Gloomspite Squig Hoppers

    # ── Astra Militarum ───────────────────────────────────────────────────
    '47-30': ('45.05',  'https://www.amazon.com/dp/B0BSFPT9VX', False),  # Cadian Shock Troops
    '47-05': ('55.25',  'https://www.amazon.com/dp/B003CRRMU4', True),   # Chimera
    '47-08': ('33.15',  'https://www.amazon.com/dp/B0BVMGVP2X', True),   # Commissar  ✓ FIXED (old B0DHLRML9F was datasheet card pack, not miniature)
    '47-25': ('138.00', 'https://www.amazon.com/dp/B0DVT8JDQ6', False),  # Combat Patrol
    '47-14': ('61.75',  'https://www.amazon.com/dp/B002ICCZDS', True),   # Hellhound  ✓ FIXED
    '47-06': ('59.50',  'https://www.amazon.com/dp/B0BSFPSMZ6', False),  # Leman Russ Battle Tank
    '47-12': ('40.80',  'https://www.amazon.com/dp/B0BSFPTZWJ', True),   # Sentinel  ✓ ADDED (previously omitted; old scrape found JoyToy figure)
    # 47-17 Basilisk — Amazon listing at $29.75 was wrong (toy, not GW kit); removed

    # ── Blood Angels ──────────────────────────────────────────────────────
    '41-03': ('29.92',  'https://www.amazon.com/dp/B005FPTQJQ', True),   # Astorath
    '41-10': ('78.41',  'https://www.amazon.com/dp/B003E6N2L6', True),   # Baal Predator
    '41-25': ('130.00', 'https://www.amazon.com/dp/B0DK3T1QSG', True),   # Combat Patrol
    '41-04': ('40.80',  'https://www.amazon.com/dp/B0C2459XDP', True),   # Commander Dante
    # 41-07 Death Company Marines — no correct Amazon listing found; removed
    # 41-12 Death Company Marines with Jump Packs — no correct Amazon listing; removed
    '41-05': ('38.99',  'https://www.amazon.com/dp/B0DJFF398H', True),   # Lemartes  ✓ FIXED (old B0FPR7Q65F was Librarian Dreadnought — wrong product!)
    # 41-15 Librarian Dreadnought — SKU deactivated Mar 2026; removed from seed
    '41-02': ('40.80',  'https://www.amazon.com/dp/B08PS67BH6', True),   # Mephiston
    '41-06': ('51.00',  'https://www.amazon.com/dp/B08RCBMNNS', True),   # Sanguinary Guard
    '41-09': ('40.00',  'https://www.amazon.com/dp/B08Y5P6S4N', True),   # Sanguinary Priest
    '41-08': ('39.95',  'https://www.amazon.com/dp/B0DJFGCBFS', True),   # The Sanguinor

    # ── Black Templars ────────────────────────────────────────────────────
    '55-25': ('33.15',  'https://www.amazon.com/dp/B09LG7FH94', False),  # Castellan
    '55-24': ('51.00',  'https://www.amazon.com/dp/B09LGDYQ4T', False),  # Chaplain Grimaldus
    '55-30': ('144.50', 'https://www.amazon.com/dp/B0FJ91WF8T', True),   # Combat Patrol
    '55-27': ('36.98',  'https://www.amazon.com/dp/B0FJ933BDM', True),   # Crusade Ancient
    '55-22': ('36.98',  'https://www.amazon.com/dp/B09LG7MHBR', False),  # Emperor's Champion
    '55-26': ('35.70',  'https://www.amazon.com/dp/B0FJ923FZS', True),   # Execrator
    '55-21': ('51.00',  'https://www.amazon.com/dp/B09LGJBP32', True),   # Helbrecht
    '55-28': ('34.84',  'https://www.amazon.com/dp/B09LGGR5BV', True),   # Marshal  ✓ FIXED
    '55-20': ('55.25',  'https://www.amazon.com/dp/B09LG7HSLY', True),   # Primaris Crusader Squad
    '55-23': ('53.47',  'https://www.amazon.com/dp/B09LG1SKWF', True),   # Sword Brethren

    # ── Blades of Khorne ──────────────────────────────────────────────────
    '97-08': ('',       'https://www.amazon.com/Warhammer-Daemons-Chaos-Khorne-Bloodletters/dp/B076F9VWXX/ref=sr_1_1?crid=3TZY4PZOUVBE3&dib=eyJ2IjoiMSJ9.FEi69s2jROlFANV2lQeApFwcAEkGnnyUMGUh-KvAPetUajz6_g1N30pppFLkKiIumtwm9rMEbZpb43yoOeKfnIl18PxVYoZGH43bplFky6Fi87Xk4qSDHzz3Rrn44YJKjocYk3TGW4GIb-w6KPCHpGH1xmcWLW2WPBZZQoUckDC8FK0q8y9UN28Rivh-PGLgTKjofYmpvjSo2VTQ4dJG6TThOu82sQJd1f-S0wKZPWrtp0EcMEGovgKDyDXA_qRMg_m0zlc2a-rdE2NaMjd_VKGe9QOaQWNzBLEToNV74EU.f5itZrUrjDOg_wGC4oFtx_k1raiJeYwWWdZ4gjcbsa0&dib_tag=se&keywords=Blades+of+Khorne+Bloodletters&qid=1777641970&sprefix=blades+of+khorne+bloodletters%2Caps%2C249&sr=8-1', False),  # Bloodletters
    '83-30': ('69.48',  'https://www.amazon.com/dp/B013QJBOGK', True),   # Bloodreavers  ✓ FIXED

    # ── Cerastus Knights ──────────────────────────────────────────────────
    '31-67': ('167.61', 'https://www.amazon.com/dp/B0CJ9C8T2T', True),   # Acheron
    '31-66': ('180.29', 'https://www.amazon.com/dp/B0CJ99HNZ7', True),   # Castigator
    '31-06': ('165.00', 'https://www.amazon.com/dp/B0CD7HZXX4', True),   # Lancer

    # ── Chaos Space Marines ───────────────────────────────────────────────
    '71-06': ('144.50', 'https://www.amazon.com/dp/B0D3HZ2SG2', True),   # Combat Patrol

    # ── Chaos Predator ────────────────────────────────────────────────────
    '43-09': ('68.00',  'https://www.amazon.com/dp/B000CESE20', False),  # Chaos Predator

    # ── Cities of Sigmar ──────────────────────────────────────────────────
    '86-15': ('44.95',  'https://www.amazon.com/dp/B0CLM7582R', True),   # Freeguild Fusiliers

    # ── Citadel Paints & Supplies ─────────────────────────────────────────
    'AP-001': ('6.95',  'https://www.amazon.com/dp/B07SWZ3C5K', True),   # Air Paint
    'BP-001': ('7.95',  'https://www.amazon.com/dp/B007RQ4060', True),   # Base Paint (single)
    'BR-001': ('6.80',  'https://www.amazon.com/dp/B094Y8KNQS', True),   # Brush: Medium Base
    'BR-002': ('9.99',  'https://www.amazon.com/dp/B094Y3SRW9', True),   # Brush: Medium Layer
    'BS-001': ('38.25', 'https://www.amazon.com/dp/B0CBKHZY3V', True),   # Colour Base Paint Set  ✓ FIXED (old B0B6Z81PKV was single pot $4.55 — NOT the set!)
    # BS-002 Colour Shade Set — SKU deactivated Mar 2026; removed from seed
    # CP-005 Contrast Paint Bundle x5 — SKU deactivated Mar 2026; removed from seed
    # CP-010 Contrast Paint Bundle x10 — SKU deactivated Mar 2026; removed from seed
    'CP-001': ('9.99',  'https://www.amazon.com/dp/B07SSQ1LG8', True),   # Contrast Paint (single)
    'CP-003': ('9.99',  'https://www.amazon.com/dp/B07SRQ88S2', True),   # Contrast Blood Angels Red
    # CP-002 Contrast Wraithbone 18ml — SKU deactivated Mar 2026 (confused with SP-011 spray); removed
    # CSP-003 Spray Corax White — Amazon listing was wrong size; not available on Amazon
    'CSP-004': ('25.00','https://www.amazon.com/dp/B00T86KNJK', True),   # Spray Zandri Dust
    # DB-001 Detail Brush Set — SKU deactivated Mar 2026; removed from seed
    # DP-001 Dry Paint — SKU deactivated Mar 2026; removed from seed
    # HK-001 Hobby Knife — SKU deactivated Mar 2026; removed from seed
    'LP-001': ('4.25',  'https://www.amazon.com/dp/B007RS6EWQ', True),   # Layer Paint
    'MR-001': ('22.95', 'https://www.amazon.com/dp/B0BHTRDSJ5', False),  # Mouldline Remover
    'PH-001': ('13.67', 'https://www.amazon.com/dp/B08MC88KWZ', False),  # Painting Handle
    'PH-002': ('17.95', 'https://www.amazon.com/dp/B09KHBPRVL', False),  # Painting Handle XL
    # PM-001 Painting Mat — SKU deactivated Mar 2026; removed from seed
    'PG-001': ('12.49', 'https://www.amazon.com/dp/B004CDA3GC', True),   # Plastic Glue  ✓ ADDED (previously omitted)
    # SG-001 Super Glue — SKU deactivated Mar 2026; removed from seed
    'SP-001': ('14.43', 'https://www.amazon.com/dp/B01H7JECW8', True),   # Shade: Nuln Oil
    'SP-002': ('9.99',  'https://www.amazon.com/dp/B0B6CK8PD5', False),  # Shade: Agrax Earthshade
    'SP-003': ('15.12', 'https://www.amazon.com/dp/B018GZD62E', True),   # Shade: Reikland Fleshshade
    'SP-010': ('23.64', 'https://www.amazon.com/dp/B000A5CHHE', True),   # Spray: Chaos Black  ✓ FIXED
    'SP-011': ('24.60', 'https://www.amazon.com/dp/B08ZHWMFX3', False),  # Spray: Wraithbone
    'SP-012': ('32.33', 'https://www.amazon.com/dp/B08ZHKMTRV', True),   # Spray: Grey Seer
    'SP-020': ('26.90', 'https://www.amazon.com/dp/B08JJNFHKR', True),   # Munitorum Varnish
    'TCP-001': ('4.55', 'https://www.amazon.com/dp/B0C69CR9JH', True),   # Technical Paint
    # TE-001 Technical Paint (Nihilakh Oxide) — SKU deactivated Mar 2026; removed from seed
    # TP-001 Texture Paint (Astrogranite) — SKU deactivated Mar 2026; removed from seed
    # WP-001 Water Pot — SKU deactivated Mar 2026; removed from seed

    # ── Craftworlds (Aeldari) ─────────────────────────────────────────────
    '46-06': ('40.80',  'https://www.amazon.com/dp/B077XLMHX7', True),   # Dire Avengers
    '46-02': ('29.75',  'https://www.amazon.com/dp/B0B2X2C51V', True),   # Farseer          ✓ FIXED (old B09WNGQTBT wrong)
    '46-14': ('53.11',  'https://www.amazon.com/dp/B0DV41T8NQ', True),   # Fire Dragons     ✓ ADDED (old B0D3CPJRSC was paint)
    '46-29': ('60.00',  'https://www.amazon.com/dp/B0746GG3PF', False),  # Wave Serpent
    '46-26': ('51.00',  'https://www.amazon.com/dp/B074MCDX59', True),   # Wraithguard
    '46-25': ('136.00', 'https://www.amazon.com/dp/B0DYFB9D4G', True),   # Combat Patrol    ✓ FIXED (had empty price + in_stock=False)

    # ── Dark Angels ───────────────────────────────────────────────────────
    '44-03': ('39.95',  'https://www.amazon.com/dp/B0CVXN5W6P', False),  # Asmodai
    '44-04': ('40.80',  'https://www.amazon.com/dp/B0C244GN97', False),  # Azrael
    '44-05': ('39.95',  'https://www.amazon.com/dp/B0CVXP43B1', True),   # Belial
    '44-20': ('136.00', 'https://www.amazon.com/dp/B0CVXCZ5YL', True),   # Combat Patrol         ✓ FIXED (old B0F53YP53G wrong; price est.)
    '44-10': ('59.48',  'https://www.amazon.com/dp/B0CVXNHD3P', True),   # Deathwing Knights
    # 44-11 Deathwing Terminator Squad — SKU deactivated Mar 2026b; removed from seed
    # 44-02 Ezekiel — Amazon not available (old ASIN was eBook); removed
    '44-13': ('51.00',  'https://www.amazon.com/dp/B0CVXNJHNP', True),   # Inner Circle Companions
    # 44-16 Land Speeder Vengeance — not sold on Amazon (old B0CVXCZ5YL was Combat Patrol); removed
    '44-07': ('44.00',  'https://www.amazon.com/dp/B08THKXQ5J', True),   # Lazarus
    '44-06': ('62.48',  'https://www.amazon.com/dp/B0CB1BFQCZ', True),   # Lion El'Jonson        ✓ FIXED (old B0CKPSLCQ4 $155.99 wrong)
    '44-17': ('84.55',  'https://www.amazon.com/dp/B00AYU3YZY', True),   # Nephilim Jetfighter
    '44-12': ('55.25',  'https://www.amazon.com/dp/B00AYUGFZ0', True),   # Ravenwing Black Knights ✓ FIXED (old B0CVXP43B1 was Belial)
    '44-09': ('55.25',  'https://www.amazon.com/dp/B08THMGCVL', False),  # Ravenwing Command Squad
    '44-14': ('84.55',  'https://www.amazon.com/dp/B00AYU3YZY', True),   # Ravenwing Dark Talon  ✓ FIXED
    # 44-15 Ravenwing Darkshroud — SKU deactivated Mar 2026b (same kit as Dark Talon); removed
    '44-08': ('64.48',  'https://www.amazon.com/dp/B0067PVHLS', True),   # Sammael  ✓ FIXED

    # ── Death Guard ───────────────────────────────────────────────────────
    '43-54': ('55.25',  'https://www.amazon.com/dp/B08QW34YBG', True),   # Blightlord Terminators
    '43-80': ('143.93', 'https://www.amazon.com/dp/B0F63T4RKC', True),   # Combat Patrol
    '43-56': ('55.25',  'https://www.amazon.com/dp/B075TH143V', False),  # Deathshroud Bodyguard
    '43-55': ('51.00',  'https://www.amazon.com/dp/B0763KGZ9W', True),   # Foetid Bloat-drone
    '43-03': ('138.99', 'https://www.amazon.com/dp/B08RK1HD85', True),   # Mortarion
    '43-50': ('51.00',  'https://www.amazon.com/dp/B08T54H49C', True),   # Plague Marines
    '43-53': ('33.15',  'https://www.amazon.com/dp/B08T7K36TM', False),  # Poxwalkers
    '43-08': ('40.80',  'https://www.amazon.com/dp/B08QFS24H5', True),   # Typhus  ✓ FIXED

    # ── Deathwatch ────────────────────────────────────────────────────────
    # 39-03 Decimus Kill Team      — SKU deactivated Mar 2026b; removed from seed
    # 39-07 Fortis Kill Team       — SKU deactivated Mar 2026b; removed from seed
    # 39-08 Indomitor Kill Team    — SKU deactivated Mar 2026b; removed from seed
    # 39-10 Kill Team              — SKU deactivated Mar 2026b; removed from seed
    # 39-09 Spectrus Kill Team     — SKU deactivated Mar 2026b; removed from seed
    # 39-11 Talonstrike Kill Team  — SKU deactivated Mar 2026b; removed from seed
    # 39-05 Terminator Squad       — SKU deactivated Mar 2026b; removed from seed
    # 39-06 Veteran Squad          — Vanguard Veterans ASIN wrong; no Amazon listing; removed
    '39-02': ('33.15',  'https://www.amazon.com/dp/B01KUYPREO', True),   # Watch Master
    '39-01': ('34.00',  'https://www.amazon.com/dp/B0DC6PBHSD', True),   # Watch Captain Artemis
    '39-04': ('81.60',  'https://www.amazon.com/dp/B08MC6BF6V', True),   # Corvus Blackstar

    # ── Disciples of Tzeentch ─────────────────────────────────────────────
    '97-11': ('40.80',  'https://www.amazon.com/dp/B0BL1KFDM5', True),   # Pink Horrors
    # 97-12 Pink Horrors duplicate — SKU deactivated Mar 2026c; removed from seed
    '83-40': ('57.53',  'https://www.amazon.com/dp/B01NBYRM58', True),   # Tzaangors           ✓ ADDED

    # ── Drukhari ──────────────────────────────────────────────────────────
    '45-02': ('34.00',  'https://www.amazon.com/dp/B0FX34K7JW', True),   # Archon
    '45-25': ('134.95', 'https://www.amazon.com/dp/B0FS2J7JDV', False),  # Combat Patrol
    '45-07': ('',       'https://www.amazon.com/dp/B096SW4W7G', False),  # Kabalite Warriors
    '45-10': ('85.05',  'https://www.amazon.com/dp/B091VXBHQ1', True),   # Raider
    '45-06': ('46.13',  'https://www.amazon.com/dp/B09998YRWC', True),   # Wyches

    # ── Flesh-Eater Courts ────────────────────────────────────────────────
    '91-35': ('49.48',  'https://www.amazon.com/dp/B01FY2RCD6', True),   # Crypt Ghouls
    '91-07': ('50.99',  'https://www.amazon.com/dp/B0FGKQN38V', True),   # Crypt Horrors/Flayers (same kit)  ✓ FIXED
    # 91-32 Terrorgheist — Amazon has no listing (old ASIN 1788264290 was an ISBN/book); removed

    # ── Genestealer Cults ─────────────────────────────────────────────────
    '51-44': ('40.80',  'https://www.amazon.com/dp/B07NG31CVQ', True),   # Aberrants
    '51-41': ('40.80',  'https://www.amazon.com/dp/B09VBDN5BF', True),   # Acolyte Hybrids
    '51-69': ('138.00', 'https://www.amazon.com/dp/B0D63C96WS', True),   # Combat Patrol
    '51-43': ('29.75',  'https://www.amazon.com/dp/B09RMTQ1HV', True),   # Magus
    '51-40': ('51.00',  'https://www.amazon.com/dp/B09XLWHDHP', True),   # Neophyte Hybrids
    # ── Genestealer Cults phase-2 (GC-xxx SKUs) — prices TBD, scraper will update ──
    'GC-001': ('', 'https://www.amazon.com/dp/1804573884', False),   # Codex: Genestealer Cults
    'GC-002': ('', 'https://www.amazon.com/dp/B0B1DX87Z2', False),   # Reductus Saboteur
    'GC-003': ('', 'https://www.amazon.com/dp/B09QXRC667', False),   # Kelermorph
    'GC-004': ('', 'https://www.amazon.com/dp/B09SJ5SLX5', False),   # Abominant
    'GC-005': ('', 'https://www.amazon.com/dp/B09TM375L9', False),   # Biophagus
    'GC-006': ('', 'https://www.amazon.com/dp/B07N8FQLXY', False),   # Atalan Jackals
    'GC-007': ('', 'https://www.amazon.com/dp/B07N8MC6XT', False),   # Nexos
    'GC-008': ('', 'https://www.amazon.com/dp/B09QH11PYX', False),   # Locus
    'GC-009': ('', 'https://www.amazon.com/dp/B09RMYKS5B', False),   # Sanctus
    # ⚠ GC-010/011 Goliath (Rockgrinder/Truck) share one kit/ASIN
    'GC-010': ('', 'https://www.amazon.com/dp/B09RMWKQR7', False),   # Goliath Rockgrinder
    'GC-011': ('', 'https://www.amazon.com/dp/B09RMWKQR7', False),   # Goliath Truck  ⚠ same kit
    'GC-012': ('', 'https://www.amazon.com/dp/B01LZEUULK', False),   # Acolyte Iconward
    'GC-013': ('', 'https://www.amazon.com/dp/B09XLWHDHP', False),   # Hybrid Metamorphs  ⚠ same ASIN as 51-40 Neophyte Hybrids
    'GC-014': ('', 'https://www.amazon.com/dp/B0DJFGZZGW', False),   # Benefictus
    'GC-015': ('', 'https://www.amazon.com/dp/B0CGV7GF6V', False),   # Genestealers
    'GC-016': ('', 'https://www.amazon.com/dp/B07NFFJWLF', False),   # Achilles Ridgerunner
    'GC-017': ('', 'https://www.amazon.com/dp/B07N8LKKJB', False),   # Jackal Alphus
    'GC-018': ('', 'https://www.amazon.com/dp/B07N8KK6DL', False),   # Clamavus

    # ── Seraphon (SR-xxx SKUs) — prices TBD, scraper will update ─────────────
    'SR-001': ('', 'https://www.amazon.com/dp/B0C5XPQ558', False),   # Aggradon Lancers
    'SR-002': ('', 'https://www.amazon.com/dp/B017K7M58U', False),   # Bastiladon
    # ⚠ SR-003 / SR-025 / SR-026 Engine of the Gods / Stegadon / Stegadon Chief share one kit/ASIN
    'SR-003': ('', 'https://www.amazon.com/dp/B017K7M2EW', False),   # Engine of the Gods
    'SR-004': ('', 'https://www.amazon.com/dp/B0BVGP6R5P', False),   # Hunters of Huanchi
    # ⚠ SR-005 / SR-006 Kroxigor / Kroxigor Warspawned share one kit/ASIN
    'SR-005': ('', 'https://www.amazon.com/dp/B0C5XNZ3W4', False),   # Kroxigor
    'SR-006': ('', 'https://www.amazon.com/dp/B0C5XNZ3W4', False),   # Kroxigor Warspawned  ⚠ same kit
    'SR-007': ('', 'https://www.amazon.com/dp/B0FSLDPZJL', False),   # Lord Kroak
    # ⚠ SR-008 / SR-009 Raptadon Chargers / Raptadon Hunters share one kit/ASIN
    'SR-008': ('', 'https://www.amazon.com/dp/B0C5XN4TCW', False),   # Raptadon Chargers
    'SR-009': ('', 'https://www.amazon.com/dp/B0C5XN4TCW', False),   # Raptadon Hunters  ⚠ same kit
    'SR-010': ('', 'https://www.amazon.com/dp/B085LR2GC5', False),   # Realmshaper Engine
    # ⚠ SR-011 / SR-027 Ripperdactyl Riders / Terradon Riders share one kit/ASIN
    'SR-011': ('', 'https://www.amazon.com/dp/B017K7LW8O', False),   # Ripperdactyl Riders
    'SR-012': ('', 'https://www.amazon.com/dp/B0C5XND1DS', False),   # Saurus Astrolith Bearer
    # SR-013 Saurus Guard — no Amazon listing
    'SR-014': ('', 'https://www.amazon.com/dp/B005LVHRFY', False),   # Saurus Oldblood
    # SR-015 Saurus Oldblood on Carnosaur — no Amazon listing
    'SR-016': ('', 'https://www.amazon.com/dp/B0C5XNLS7W', False),   # Saurus Scar-Veteran on Aggradon
    # SR-017 Saurus Scar-Veteran on Carnosaur — no Amazon listing
    'SR-018': ('', 'https://www.amazon.com/dp/B0C5XQPH2C', False),   # Saurus Warriors
    # SR-019 Skink Oracle on Troglodon — no Amazon listing
    'SR-020': ('', 'https://www.amazon.com/dp/B017K7LIWO', False),   # Skink Starpriest
    'SR-021': ('', 'https://www.amazon.com/dp/B0C5XL7JLP', False),   # Skink Starseer
    'SR-022': ('', 'https://www.amazon.com/dp/B002EJI002', False),   # Skinks
    'SR-023': ('', 'https://www.amazon.com/dp/B0C5XJYCGF', False),   # Slann Starmaster
    'SR-024': ('', 'https://www.amazon.com/dp/B0C5XLZ5H9', False),   # Spawn of Chotec
    'SR-025': ('', 'https://www.amazon.com/dp/B017K7M2EW', False),   # Stegadon  ⚠ same kit as SR-003
    'SR-026': ('', 'https://www.amazon.com/dp/B017K7M2EW', False),   # Stegadon Chief  ⚠ same kit as SR-003
    'SR-027': ('', 'https://www.amazon.com/dp/B017K7LW8O', False),   # Terradon Riders  ⚠ same kit as SR-011
    'SR-028': ('', 'https://www.amazon.com/dp/B0F9YT2H9W', False),   # Spearhead: Sunblooded Prowlers

    # ── Grey Knights ──────────────────────────────────────────────────────
    '57-14': ('68.17',  'https://www.amazon.com/dp/B0FPDMT27L', False),  # Dreadknight
    '57-20': ('142.18', 'https://www.amazon.com/dp/B0FJ915PXJ', True),   # Combat Patrol
    '57-02': ('35.70',  'https://www.amazon.com/dp/B074MB4X97', True),   # Grand Master Voldus
    '57-06': ('58.65',  'https://www.amazon.com/dp/B00MYGOM3Y?tag=thrifthammer7-20', True),   # Strike Squad  ✓ FIXED (old B08QJ4FCSL wrong product; same kit as 57-24/26/27)
    '57-24': ('58.65',  'https://www.amazon.com/dp/B00MYGOM3Y?tag=thrifthammer7-20', True),   # Interceptor Squad  ⚠ same kit as Strike Squad
    '57-26': ('58.65',  'https://www.amazon.com/dp/B00MYGOM3Y?tag=thrifthammer7-20', True),   # Purgation Squad  ⚠ same kit as Strike Squad
    '57-27': ('58.65',  'https://www.amazon.com/dp/B00MYGOM3Y?tag=thrifthammer7-20', True),   # Purifier Squad  ⚠ same kit as Strike Squad

    # ── Horus Heresy ──────────────────────────────────────────────────────
    'HA-001': ('44.00',  'https://www.amazon.com/dp/B0CP673J8F', True),  # MKVI Tactical Squad  ✓ FIXED (old B0CWBVGDKG wrong)
    'HA-002': ('55.25',  'https://www.amazon.com/dp/B0B8ZMZ99L', True),  # Contemptor Dreadnought  ✓ FIXED (old B0CRH15FDS wrong)
    'HA-010': ('66.95',  'https://www.amazon.com/dp/B0CKRY88GB', True),   # MKIII Tactical Squad  ✓ FIXED (old B0D6RF8C3V wrong; price $45.05 too low)
    # HA-011 Cataphractii Terminators (B0GJV364PB) — deactivated wave D; removed
    'HA-012': ('66.30',  'https://www.amazon.com/dp/B0BD5H9WRZ', True),  # Legiones Astartes Predator
    # HA-013 Spartan Assault Tank — deactivated wave E (duplicate of HA-040); removed
    'HA-020': ('67.15',  'https://www.amazon.com/dp/B0CYCQJ4NQ', True),  # Solar Auxilia Lasrifle Section  ✓ FIXED wave F (old B0CYCSZ4QV $29.75 wrong)
    'HA-021': ('65.00',  'https://www.amazon.com/dp/B0B6W3RPPQ', True),  # Leviathan Dreadnought  ✓ FIXED (old B0B8ZMZ99L was Contemptor; price est.)
    'HA-040': ('101.30', 'https://www.amazon.com/dp/B0B8ZNSRXZ', True),  # Spartan Assault Tank  ✓ FIXED (old B0F29NXG8C wrong)
    'HA-041': ('75.65',  'https://www.amazon.com/dp/B0B8ZM7M3T', True),  # Sicaran Battle Tank   ✓ FIXED (old B0F29RQ8JH wrong)
    'HA-051': ('39.95',  'https://www.amazon.com/dp/B0CJRZJPM9', True),  # Space Marine Chaplain in Terminator Armour (renamed from HH)
    # HH-001 Age of Darkness starter — Dice ASIN wrong; starter box not on Amazon; removed

    # ── Imperial Knights ──────────────────────────────────────────────────
    '54-20': ('85.00',  'https://www.amazon.com/dp/B0B116QHMG', False),  # Armigers
    '54-21': ('165.63', 'https://www.amazon.com/dp/B09ZYS4W54', True),   # Knight Dominus
    # 54-15 Knight Preceptor/Canis Rex — same ASIN as Questoris; no separate listing; removed
    '54-22': ('158.77', 'https://www.amazon.com/dp/B0FPDM6H37', True),   # Knight Questoris

    # ── Kill Team ─────────────────────────────────────────────────────────
    # All Kill Team faction boxes / supplements deactivated wave D.
    # KT-003 (Kill Team: Starter Set) remains active but has no Amazon listing.
    # KT-100 (Starter Set duplicate, B07HMRPD11) — deactivated; removed
    # KT-002 (Into the Dark, 1804570087)         — deactivated; removed
    # KT-101 (Datacards 2024, B0DH4XZH2D)        — deactivated; removed
    # KT-103 (Veteran Guardsmen, B0BVMGVP2X)     — deactivated; removed
    # KT-104 (Chaos Legionaries, B0DKNVQX8X)     — deactivated; removed
    # KT-107 (Exaction Squad, B0C448FPG7)        — deactivated; removed
    # KT-109 (Killzone Terrain, B0DPMY5CFW)      — deactivated; removed
    # KT-110 (Compendium, 1839064218)            — deactivated; removed

    # ── Leagues of Votann ─────────────────────────────────────────────────
    '73-06': ('36.00',  'https://www.amazon.com/dp/B0BK9MJ83N', True),   # Einhyr Champion  ✓ FIXED (was NOT_AVAIL)
    '73-10': ('51.00',  'https://www.amazon.com/dp/B0BK9NSQDP', True),   # Hearthkyn Warriors
    '73-12': ('58.65',  'https://www.amazon.com/dp/B0BK9NKXYW', False),  # Hernkyn Pioneers
    '73-14': ('53.13',  'https://www.amazon.com/dp/B0BK9NJJFH', True),   # Einhyr Hearthguard
    '73-25': ('138.56', 'https://www.amazon.com/dp/B0FL37XSL6', True),   # Combat Patrol

    # ── Lumineth Realm-lords ──────────────────────────────────────────────
    '87-08': ('53.13',  'https://www.amazon.com/dp/B08HWKPQP8', True),   # Alarith Stoneguard
    # 87-06 Vanari Auralan Wardens (10) — deactivated wave E (duplicate of 87-10); removed
    '87-10': ('55.25',  'https://www.amazon.com/dp/B08HK4QRK7', True),   # Vanari Auralan Wardens (canonical)

    # ── Maggotkin of Nurgle ───────────────────────────────────────────────
    # 97-09 Plaguebearers — deactivated wave E (duplicate of 83-20); removed
    '83-20': ('36.98',  'https://www.amazon.com/dp/B0746GFZYZ', True),   # Plaguebearers  ✓ FIXED (was NOT_AVAIL)
    '83-22': ('55.25',  'https://www.amazon.com/dp/B0G9W5XWLR', True),   # Putrid Blightkings

    # ── Necromunda ────────────────────────────────────────────────────────
    # NM-001 Hive War               — deactivated wave E; no Amazon listing
    'NM-010': ('45.05', 'https://www.amazon.com/dp/B0779NTT1V', True),   # Escher Gang  ✓ FIXED (old B0BNJ3ZHVR was Dice Set at $19.99)
    'NM-011': ('45.05', 'https://www.amazon.com/dp/B0779Q1K7P', True),   # Goliath Gang
    'NM-012': ('45.05', 'https://www.amazon.com/dp/B07CQCCXMD', True),   # Van Saar Gang
    # NM-020 Underhive Terrain Set  — deactivated wave E; removed

    # ── Necrons ───────────────────────────────────────────────────────────
    '49-14': ('40.80',  'https://www.amazon.com/dp/B007Y9PVA4', True),   # Canoptek Spyder
    '49-12': ('58.65',  'https://www.amazon.com/dp/B08HCL7SFY', True),   # Doomsday Ark  ✓ FIXED (old B0FNN67JTJ $18.00 clearly wrong; dual-build kit w/ Ghost Ark)
    '49-13': ('65.45',  'https://www.amazon.com/dp/B08GC4PD6K', True),   # Doom Scythe  ✓ ADDED (was NOT_AVAIL)
    '49-17': ('51.00',  'https://www.amazon.com/dp/B095J8FYZP', True),   # Flayed Ones
    '49-10': ('40.80',  'https://www.amazon.com/dp/B00631UMA8', True),   # Immortals
    '49-11': ('51.00',  'https://www.amazon.com/dp/B00631WTB8', True),   # Lychguard
    '49-08': ('159.00', 'https://www.amazon.com/dp/B08LBBMQX4', True),   # Monolith  ✓ FIXED
    '49-03': ('35.70',  'https://www.amazon.com/dp/B0CNTVXSM6', True),   # Overlord
    '49-21': ('33.15',  'https://www.amazon.com/dp/B08VHDDS6N', True),   # Psychomancer
    '49-22': ('43.48',  'https://www.amazon.com/dp/B0CTXT3ZM3', False),  # Royal Warden
    '49-20': ('110.50', 'https://www.amazon.com/dp/B08LB8JYHP', True),   # C'tan Void Dragon
    '49-06': ('44.20',  'https://www.amazon.com/dp/B08KXCSZ5S', False),  # Warriors

    # ── Nighthaunt ────────────────────────────────────────────────────────
    '91-14': ('55.77',  'https://www.amazon.com/dp/B07G2S55DT', True),   # Bladegheist Revenants
    # 91-10 Chainrasps — deactivated wave E (duplicate of 91-28); removed
    '91-28': ('40.80',  'https://www.amazon.com/dp/B07FSWK3D7', True),   # Chainrasps (canonical)  ✓ ADDED (was NOT_AVAIL)
    '91-12': ('51.00',  'https://www.amazon.com/dp/B07F1YC259', True),   # Grimghast Reapers
    '91-06': ('52.50',  'https://www.amazon.com/dp/B07FBJQY74', True),   # Hexwraiths
    # 91-15 Knight of Shrouds — confirmed no active Amazon listing; removed wave F
    '91-02': ('51.00',  'https://www.amazon.com/dp/B07F1WS813', True),   # Lady Olynder

    # ── Orks ──────────────────────────────────────────────────────────────
    '50-22': ('',       'https://www.amazon.com/dp/B001O35G0G', False),  # Battlewagon
    '50-10': ('40.80',  'https://www.amazon.com/dp/B07JYGJ4JL', True),   # Boyz
    '50-16': ('35.00',  'https://www.amazon.com/dp/B003B1V9D2', True),   # Deff Dread  ✓ ADDED wave P
    '50-20': ('55.25',  'https://www.amazon.com/dp/B09HJX1436', False),  # Flash Gitz
    '50-15': ('55.25',  'https://www.amazon.com/dp/B09FYQG7P3', False),  # Killa Kans
    '50-14': ('35.70',  'https://www.amazon.com/dp/B09HJBSNNW', True),   # Lootas
    '50-12': ('62.48',  'https://www.amazon.com/dp/B00LKE10EK', True),   # Meganobz
    '50-09': ('35.70',  'https://www.amazon.com/dp/B09HJNCZNR', True),   # Nobz
    '50-11': ('51.00',  'https://www.amazon.com/dp/B000CESDXA', True),   # Trukk
    # 50-05 Warboss (regular) — Mega Armour ASIN wrong; regular Warboss not on Amazon; removed
    '50-02': ('36.98',  'https://www.amazon.com/dp/B09NSSWG75', True),   # Warboss in Mega Armour
    '71-18': ('144.50', 'https://www.amazon.com/dp/B0D14VVJ26', True),  # Combat Patrol  ✓ ADDED wave F (was NOT_AVAIL)

    # ── Ossiarch Bonereapers ──────────────────────────────────────────────
    '94-10': ('55.25',  'https://www.amazon.com/dp/B07ZTPJ69Q', True),   # Mortek Guard
    '94-12': ('51.00',  'https://www.amazon.com/dp/B07ZTQ263Z', True),   # Necropolis Stalkers

    # ── Skaven ────────────────────────────────────────────────────────────
    # 90-10 Clanrats — listing B0DFWN8F73 out of stock / unavailable; removed wave F
    '90-12': ('40.80',  'https://www.amazon.com/dp/B013XDID9K', False),  # Plague Monks
    '90-17': ('69.70',  'https://www.amazon.com/dp/B0C2YQYPB2', True),   # Stormfiends

    # ── Slaves to Darkness ────────────────────────────────────────────────
    # 83-10 Chaos Warriors (12) — deactivated wave F (duplicate of 83-18); removed
    '83-14': ('93.50',  'https://www.amazon.com/dp/B0CH4B6G13', True),   # Varanguard
    '83-18': ('54.35',  'https://www.amazon.com/dp/B0BRY3JPBX', True),   # Chaos Warriors (renamed in wave F; same ASIN)

    # ── Space Marines ─────────────────────────────────────────────────────
    '48-92': ('51.00',  'https://www.amazon.com/dp/B0746GR78Q',  True),  # Aggressors  ✓ FIXED wave F (old B0CJS1MKVJ $33.15 wrong)
    '48-33': ('35.70',  'https://www.amazon.com/dp/B08F2V3TP6', True),   # Apothecary
    '48-34': ('36.98',  'https://www.amazon.com/dp/B09RG8VTR7', False),  # Ancient
    '48-76': ('55.25',  'https://www.amazon.com/dp/B08P7XNWPG', False),  # Assault Intercessors
    '48-44': ('72.25',  'https://www.amazon.com/dp/B0CJS1HRQY', False),  # Brutalis Dreadnought
    '48-46': ('62.48',  'https://www.amazon.com/dp/B0CVKJJB63', False),  # Ballistus Dreadnought
    '48-38': ('51.00',  'https://www.amazon.com/dp/B08VHDSFSC', False),  # Bladeguard Veterans
    '48-32': ('35.70',  'https://www.amazon.com/dp/B074DSM6W1',  True),  # Chaplain  ✓ FIXED wave F (old B0055UCUR6 $69.95 wrong)
    '48-37': ('57.45',  'https://www.amazon.com/dp/B0CJS1GK5P', True),   # Company Heroes
    '48-15': ('55.25',  'https://www.amazon.com/dp/B0775237DV', False),  # Devastator Squad
    '48-98': ('50.00',  'https://www.amazon.com/dp/B08MVMPLJQ',  True),  # Primaris Eliminators  ✓ FIXED wave F (old B0D3FN245T $42.99 wrong)
    '48-39': ('51.00',  'https://www.amazon.com/dp/B08VHF72L8',  True),  # Eradicators  ✓ FIXED wave F (old B0DH4W3XYK $28.90 was Scouts!)
    '48-28': ('33.15',  'https://www.amazon.com/dp/B08KHQPW8M',  True),  # Firestrike Servo-Turrets  ✓ FIXED wave F (old B0FTZYXRQV $152.50 wrong)
    '48-27': ('58.65',  'https://www.amazon.com/dp/B08LB95FQ5', False),  # Hammerfall Bunker
    '48-97': ('51.00',  'https://www.amazon.com/dp/B074RJKKBP', True),   # Inceptors
    '48-96': ('55.25',  'https://www.amazon.com/dp/B08GC37WBR', True),   # Incursors (dual kit with Infiltrators 48-41)  ✓ FIXED wave R (old B07J3PG964 $24.97 wrong), price corrected wave V
    '48-45': ('51.00',  'https://www.amazon.com/dp/B0CVS2PN2X', True),   # Infernus Squad  ✓ FIXED
    '48-41': ('55.25',  'https://www.amazon.com/dp/B08GC37WBR', True),   # Infiltrators
    '48-75': ('55.25',  'https://www.amazon.com/dp/B074MCKC99', True),   # Intercessors
    '48-42': ('45.05',  'https://www.amazon.com/dp/B08KHQ2CMC', True),   # Invader ATV
    # 48-36 Judiciar — Primaris Ancient ASIN wrong; no Amazon listing; removed
    # 48-21 Land Raider — deactivated wave G (duplicate of 48-22 Crusader/Redeemer); removed
    '48-22': ('97.75',  'https://www.amazon.com/dp/B001GQQT2A', True),   # Land Raider Crusader/Redeemer
    '48-30': ('35.70',  'https://www.amazon.com/dp/B08HSS6KJ1', True),   # Librarian  ✓ FIXED wave G (old B08CTK7K4F $75.00 wrong)
    '48-40': ('55.25',  'https://www.amazon.com/dp/B08LZYX55N', True),   # Outriders  ✓ FIXED wave G (old B0DYJKS2JP $34.99 wrong)
    '48-62': ('39.20',  'https://www.amazon.com/dp/B09RGCPT3L', True),   # Primaris Captain
    '48-61': ('33.15',  'https://www.amazon.com/dp/B07WJ7CF9D', True),   # Primaris Lieutenant
    '48-23': ('68.00',  'https://www.amazon.com/dp/B07WJHVDFC', True),   # Predator  ✓ FIXED wave G (old B0FL3X8DFY $28.99 wrong)
    '48-93': ('69.70',  'https://www.amazon.com/dp/B08HSRX6Z3', False),  # Redemptor Dreadnought
    '48-85': ('81.60',  'https://www.amazon.com/dp/B08HSVFY4N', True),   # Repulsor  ✓ FIXED
    '48-95': ('97.75',  'https://www.amazon.com/dp/B08J5NZ8RH', False),  # Repulsor Executioner
    '55-02': ('62.48',  'https://www.amazon.com/dp/B0795YC5J2', True),   # Roboute Guilliman
    '55-12': ('47.18',  'https://www.amazon.com/dp/B0FX34N7PR', True),   # Marneus Calgar  ✓ PRICE UPDATED (was 69.29)
    '55-16': ('92.42',  'https://www.amazon.com/dp/B0FXNDT7XR', True),   # Ultramarines Honour Guard  ✓ FIXED wave J (old B0F9DPFMP3 $28.99 wrong)
    '48-29': ('69.70',  'https://www.amazon.com/dp/B0DH4Y2GJS', True),   # Scouts (Kill Team 2024)  ✓ FIXED wave G (old B0DH4W3XYK $28.90 wrong)
    '48-43': ('55.25',  'https://www.amazon.com/dp/B0CJS1VS6C', True),   # Sternguard Veteran Squad  ✓ FIXED
    # 48-99 Suppressors — deactivated wave H (B08MVMPLJQ belongs to Eliminators); removed
    '48-07': ('51.00',  'https://www.amazon.com/dp/B077Y4PTR4', True),   # Tactical Squad
    '48-06': ('61.22',  'https://www.amazon.com/dp/B0G3D2F6BH', True),   # Terminator Squad  ✓ FIXED wave H (old B000CEM3E0 $51.00 wrong)
    '48-08': ('51.00',  'https://www.amazon.com/dp/B08HPXH2GV', True),   # Vanguard Veteran Squad
    '48-26': ('68.00',  'https://www.amazon.com/dp/B00109WAOY', True),   # Vindicator
    '48-25': ('74.00',  'https://www.amazon.com/dp/B000CESE1G', True),   # Whirlwind
    '48-94': ('75.65',  'https://www.amazon.com/dp/B08HY7FY5K', True),   # Impulsor  ✓ FIXED
    '71-02': ('147.58', 'https://www.amazon.com/dp/B0CLVTKD9K', True),  # Combat Patrol  ✓ ADDED wave F (was NOT_AVAIL)

    # ── Space Wolves ──────────────────────────────────────────────────────
    '53-20': ('144.50', 'https://www.amazon.com/dp/B0FJ935YFL', True),   # Combat Patrol
    '53-06': ('53.13',  'https://www.amazon.com/dp/B0FF4NG625', True),   # Grey Hunters
    '53-02': ('40.02',  'https://www.amazon.com/dp/B08LZY9Z3K', True),   # Ragnar Blackmane  ✓ FIXED wave H (old B0FGJVB1LQ $62.99 wrong)
    '53-10': ('55.25',  'https://www.amazon.com/dp/B08MV13YVH', True),   # Thunderwolf Cavalry  ✓ FIXED wave H (old B0DTDYR7BM $249.00 wrong)
    '53-08': ('58.65',  'https://www.amazon.com/dp/B0FF4X73N1', False),  # Wolf Guard Terminators

    # ── Spearhead ─────────────────────────────────────────────────────────
    '70-17':  ('127.50', 'https://www.amazon.com/dp/B0FHHNS29Y', True),   # Blades of Khorne
    '70-22':  ('127.50', 'https://www.amazon.com/dp/B0F9YW8SZ5', True),   # Cities of Sigmar
    '70-12':  ('127.50', 'https://www.amazon.com/dp/B0D74W7R2H', True),   # Daughters of Khaine
    '70-839': ('127.50', 'https://www.amazon.com/dp/B0D9YXFMNY', True),   # Disciples of Tzeentch
    '70-915': ('127.50', 'https://www.amazon.com/dp/B0FLZLQ7YY', True),   # Flesh-Eater Courts
    '70-894': ('118.95', 'https://www.amazon.com/dp/B0FQ6TJGQM', True),   # Gloomspite Gitz Snarlpack Huntaz  ✓ FIXED wave H (old B0DZ32PLNB $51.00 wrong)
    '70-10':  ('123.99', 'https://www.amazon.com/dp/B0FLZW4SYX', True),   # Nighthaunt
    '70-892': ('124.39', 'https://www.amazon.com/dp/B0D9YT1G2R', True),   # Orruk Warclans
    '70-893': ('127.50', 'https://www.amazon.com/dp/B0DR8VR7Y7', True),   # Orruk Warclans Ironjawz
    '70-901': ('123.25', 'https://www.amazon.com/dp/B0DFWLXLY6', True),   # Skaven
    '70-04':  ('123.25', 'https://www.amazon.com/dp/B0DNFZDMWN', True),   # Slaves to Darkness
    '70-09':  ('127.51', 'https://www.amazon.com/dp/B0D6N7B7GZ', True),   # Ossiarch Bonereapers Spearhead  ✓ ADDED wave I
    '70-21':  ('127.00', 'https://www.amazon.com/dp/B0CX1WC7JJ', False),  # Stormcast Eternals
    '70-11':  ('128.89', 'https://www.amazon.com/dp/B0D9YTJT5Y', True),   # Lumineth Realm-lords Hurakan Vanguard  ✓ ADDED wave H
    '70-832': ('127.50', 'https://www.amazon.com/dp/B0G9VMQW9D', True),   # Maggotkin of Nurgle Spearhead  ✓ ADDED wave H

    # ── Stormcast Eternals ────────────────────────────────────────────────
    '96-12': ('31.46',  'https://www.amazon.com/dp/B09FXBFW1P', True),   # Knight-Judicator with Gryph-hounds  ✓ FIXED wave I (old 1785813609 $22.72 wrong — that's a rulebook)
    # 96-11 Liberators — Amazon NOT_AVAIL wave I (old B0CJPDMR9C $85.00 wrong); removed
    # 96-14 Lord-Celestant — Amazon NOT_AVAIL wave I (old B09CV9CD6J $162.35 wrong); removed
    '96-55': ('49.30',  'https://www.amazon.com/dp/B09K4K9T89', True),   # Praetors
    '96-50': ('51.00',  'https://www.amazon.com/dp/B09K4JGTVX', True),   # Vindictors  ✓ FIXED wave I (old B0C1P2G6ZS $35.00 wrong)
    # ── Stormcast Eternals phase-3 (SE-xxx SKUs) — prices TBD, scraper will update ──
    'SE-001': ('', 'https://www.amazon.com/dp/1804574287', False),  # Order Battletome: Stormcast Eternals
    'SE-002': ('', 'https://www.amazon.com/dp/B0D9XMP1VD', False),  # AoS Introductory Set
    'SE-003': ('', 'https://www.amazon.com/dp/B0D9W5192H', False),  # AoS Starter Set
    'SE-004': ('', 'https://www.amazon.com/dp/B09K4HM19R', False),  # Annihilators
    'SE-005': ('', 'https://www.amazon.com/dp/B06X1BNT3Y', False),  # Vanguard-Hunters
    # SE-006 Stormcoven — no Amazon listing
    'SE-007': ('', 'https://www.amazon.com/dp/B09MNH2FTG', False),  # Karazai the Scarred (dual kit with SE-008)
    'SE-008': ('', 'https://www.amazon.com/dp/B09MNH2FTG', False),  # Krondys, Son of Dracothion (dual kit with SE-007)
    'SE-009': ('', 'https://www.amazon.com/dp/B09K4HM19R', False),  # Annihilators with Meteoric Grandhammers (dual kit with SE-004)
    # SE-010 Vanquishers — no Amazon listing
    'SE-011': ('', 'https://www.amazon.com/dp/B09K4G47VW', False),  # Vigilors
    'SE-012': ('', 'https://www.amazon.com/dp/B09K4H9W13', False),  # Lord-Commander Bastian Carthalos
    'SE-013': ('', 'https://www.amazon.com/dp/B09FXJ7Y3V', False),  # Stormstrike Chariot
    # SE-014 Gardus Steel Soul — no Amazon listing
    'SE-015': ('', 'https://www.amazon.com/dp/B07F3DM8YG', False),  # Endless Spells: Stormcast Eternals
    'SE-016': ('', 'https://www.amazon.com/dp/B072V5S7M7', False),  # Vandus Hammerhand
    # SE-017 Vanguard-Palladors — no Amazon listing
    'SE-018': ('', 'https://www.amazon.com/dp/B06X6N2R1N', False),  # Lord-Aquilor
    'SE-019': ('', 'https://www.amazon.com/dp/B06X93VBPX', False),  # Gryph-hounds
    # SE-020 Knight-Questor — no Amazon listing
    'SE-021': ('', 'https://www.amazon.com/dp/B09CV9CD6J', False),  # Drakesworn Templar (dual kit with SE-022)
    'SE-022': ('', 'https://www.amazon.com/dp/B09CV9CD6J', False),  # Lord-Celestant on Stardrake (dual kit with SE-021)
    'SE-023': ('', 'https://www.amazon.com/dp/B014P5T2NG', False),  # Celestant-Prime, Hammer of Sigmar
    'SE-024': ('', 'https://www.amazon.com/dp/B0CCP99MF3', False),  # Questor Soulsworn
    'SE-025': ('', 'https://www.amazon.com/dp/B0DJLZPK3G', False),  # Stormreach Portal
    # SE-026 Lord-Imperatant — no Amazon listing
    # SE-027 Knight-Arcanum — no Amazon listing
    # SE-028 Prosecutors — no Amazon listing
    'SE-029': ('', 'https://www.amazon.com/dp/B0DJM2TJ2P', False),  # Iridan the Witness
    'SE-030': ('', 'https://www.amazon.com/dp/B0DJM1WW2Y', False),  # Reclusians
    'SE-031': ('', 'https://www.amazon.com/dp/B0DJM35PVN', False),  # Lord-Terminos
    'SE-032': ('', 'https://www.amazon.com/dp/B0DJM2XNP2', False),  # Lord-Relictor
    'SE-033': ('', 'https://www.amazon.com/dp/B0DJM31VFR', False),  # Tornus the Redeemed
    'SE-034': ('', 'https://www.amazon.com/dp/B0DJM1X56K', False),  # Stormstrike Palladors
    'SE-035': ('', 'https://www.amazon.com/dp/B0CRSPL1ZT', False),  # Ionus Cryptborn, Warden of Lost Souls
    'SE-036': ('', 'https://www.amazon.com/dp/B0CLM88T89', False),  # The Blacktalons
    'SE-037': ('', 'https://www.amazon.com/dp/B09MNFSWVQ', False),  # Knight-Draconis (dual kit with SE-038)
    'SE-038': ('', 'https://www.amazon.com/dp/B09MNFSWVQ', False),  # Stormdrake Guard (dual kit with SE-037)
    'SE-039': ('', 'https://www.amazon.com/dp/B09K4F7BL6', False),  # Knight-Relictor
    'SE-040': ('', 'https://www.amazon.com/dp/B09HJN394F', False),  # Vanguard-Raptors Longstrike (dual kit with SE-043)
    'SE-041': ('', 'https://www.amazon.com/dp/B01CY9IM54', False),  # Tempestors (multi-kit SE-041/042/044/045/046)
    'SE-042': ('', 'https://www.amazon.com/dp/B01CY9IM54', False),  # Lord-Celestant on Dracoth (multi-kit)
    'SE-043': ('', 'https://www.amazon.com/dp/B09HJN394F', False),  # Vanguard-Raptors Hurricane (dual kit with SE-040)
    'SE-044': ('', 'https://www.amazon.com/dp/B01CY9IM54', False),  # Desolators (multi-kit)
    'SE-045': ('', 'https://www.amazon.com/dp/B01CY9IM54', False),  # Concussors (multi-kit)
    'SE-046': ('', 'https://www.amazon.com/dp/B01CY9IM54', False),  # Fulminators (multi-kit)
    # 71-55 Stormcast Vanguard — deactivated wave I (duplicate starter-set entry); removed

    # ── T'au Empire ───────────────────────────────────────────────────────
    '56-13': ('53.03',  'https://www.amazon.com/dp/B011KPL5BQ', True),   # Broadside Battlesuit  ✓ FIXED wave I (old B000CEQBSY $55.25 wrong)
    '56-25': ('144.50', 'https://www.amazon.com/dp/B0D2J2XJG8', False),  # Combat Patrol
    '56-15': ('75.65',  'https://www.amazon.com/dp/B09SZPLZ7X', True),   # Crisis Battlesuits
    '56-22': ('29.75',  'https://www.amazon.com/dp/B09RFZGL74', True),   # Ethereal
    '56-06': ('59.95',  'https://www.amazon.com/dp/B07G8N6HJ8', True),   # Fire Warriors
    '56-10': ('68.00',  'https://www.amazon.com/dp/B00C4UUYPK', True),   # Hammerhead Gunship
    '56-19': ('40.80',  'https://www.amazon.com/dp/B016S4S9OK', True),   # Pathfinders  ✓ FIXED wave I (old B07KW5TRCL $21.87 wrong)
    '56-16': ('103.70', 'https://www.amazon.com/dp/B09SZMQV11', True),   # Riptide Battlesuit
    '56-14': ('',       'https://www.amazon.com/dp/B075X58BFJ', False),  # Stealth Battlesuits
    # ── T'au Empire phase-2 (TE-xxx SKUs) — prices TBD, scraper will update ──
    'TE-001': ('', 'https://www.amazon.com/dp/B09WM2KFC8', False),  # Tidewall Shieldline
    'TE-002': ('', 'https://www.amazon.com/dp/B0D2J3XJK5', False),  # Kroot Hounds
    'TE-003': ('', 'https://www.amazon.com/dp/B0GQVVZS78', False),  # The Twin Lance
    'TE-004': ('', 'https://www.amazon.com/dp/B0CB1BGFX3', False),  # Commander Farsight
    'TE-005': ('', 'https://www.amazon.com/dp/B09RG6NNFF', False),  # Darkstrider
    'TE-006': ('', 'https://www.amazon.com/dp/B09SZLDTYD', False),  # Commander Shadowsun
    'TE-007': ('', 'https://www.amazon.com/dp/B09SBXJ53W', False),  # Fire Warriors Breacher Team (dual kit with TE-008)
    'TE-008': ('', 'https://www.amazon.com/dp/B09SBXJ53W', False),  # Fire Warriors Strike Team (dual kit with TE-007)
    'TE-009': ('', 'https://www.amazon.com/dp/B09WCHJNK5', False),  # Empire Commander
    'TE-010': ('', 'https://www.amazon.com/dp/B09VZFJSYH', False),  # Cadre Fireblade
    # TE-011 Ta'unar Heavy Rail Cannon — no Amazon listing
    # TE-012 Ta'unar Nexus Missile — no Amazon listing
    # TE-013 Tidewall Droneport — no Amazon listing
    'TE-014': ('', 'https://www.amazon.com/dp/B0177V7NWW', False),  # Tactical Drones
    'TE-015': ('', 'https://www.amazon.com/dp/B09RG24ZXJ', False),  # XV95 Ghostkeel Battlesuit
    'TE-016': ('', 'https://www.amazon.com/dp/B09SZNZQYJ', False),  # KV128 Stormsurge
    'TE-017': ('', 'https://www.amazon.com/dp/B00C4V6IRW', False),  # Razorshark Strike Fighter (dual kit with TE-019)
    'TE-018': ('', 'https://www.amazon.com/dp/B00C4UUYPK', False),  # Sky Ray Gunship (dual kit with 56-10 Hammerhead)
    'TE-019': ('', 'https://www.amazon.com/dp/B00C4V6IRW', False),  # Sun Shark Bomber (dual kit with TE-017)
    'TE-020': ('', 'https://www.amazon.com/dp/B09S6V7MFK', False),  # Devilfish
    'TE-021': ('', 'https://www.amazon.com/dp/B0DPMYQNCS', False),  # Kill Team: Farstalker Kinband
    'TE-022': ('', 'https://www.amazon.com/dp/B0DPMWDS2D', False),  # Kill Team: Vespid Stingwings
    'TE-023': ('', 'https://www.amazon.com/dp/B0D2J34PWH', False),  # Kroot Lone-Spear
    'TE-024': ('', 'https://www.amazon.com/dp/B0D2J41PJQ', False),  # Kroot Trail Shaper
    'TE-025': ('', 'https://www.amazon.com/dp/B0D2J2XXYF', False),  # Kroot Flesh Shaper
    'TE-026': ('', 'https://www.amazon.com/dp/B0D2HYH14S', False),  # Kroot War Shaper
    'TE-027': ('', 'https://www.amazon.com/dp/B0D2J3KXSJ', False),  # Krootox Rider
    'TE-028': ('', 'https://www.amazon.com/dp/B0D2J74BLC', False),  # Krootox Rampagers
    'TE-029': ('', 'https://www.amazon.com/dp/1804573523',  False),  # Codex: T'au Empire
    # TE-030 Tiger Shark — no Amazon listing
    # TE-031 Ta'unar Fusion Eradicator — no Amazon listing
    # TE-032 Ta'unar Pulse Ordnance Multi-driver — no Amazon listing
    # TE-033 Ta'unar Tri-axis Ion Cannon — no Amazon listing
    # TE-034 Manta — no Amazon listing
    # TE-035 Firesight Team — no Amazon listing
    'TE-036': ('', 'https://www.amazon.com/dp/B09TGRTXNJ', False),  # Piranha
    'TE-037': ('', 'https://www.amazon.com/dp/B0D2J28FS7', False),  # Kroot Carnivores

    # ── Thousand Sons ─────────────────────────────────────────────────────
    '43-30': ('40.80',  'https://www.amazon.com/dp/B09KFQYBJ8', True),   # Ahriman  ✓ FIXED wave I (old B0B2PKL77J $29.75 wrong)
    '43-90': ('135.96', 'https://www.amazon.com/dp/B0F8BVJ69F', True),   # Combat Patrol
    '43-38': ('55.25',  'https://www.amazon.com/dp/B09FYQ38GZ', False),  # Exalted Sorcerers
    '43-02': ('150.17', 'https://www.amazon.com/dp/B09HJNFB65', True),   # Magnus the Red  ✓ FIXED wave I (old B0F4QTPVS4 $125.99 wrong)
    '43-35': ('55.25',  'https://www.amazon.com/dp/B01N1LRFWV', False),  # Rubric Marines
    '43-36': ('55.25',  'https://www.amazon.com/dp/B09FYSF6Y6', True),   # Scarab Occult Terminators

    # ── Tyranids ──────────────────────────────────────────────────────────
    '51-04': ('55.25',  'https://www.amazon.com/dp/B007G9NQ40', True),   # Hive Tyrant
    '51-06': ('104.88', 'https://www.amazon.com/dp/B00HSS263G', True),   # Carnifex Brood  ✓ ADDED wave I (previously removed; B00HSS263G confirmed correct)
    '51-16': ('40.80',  'https://www.amazon.com/dp/B0CGV6V47P', True),   # Termagants  ✓ FIXED wave I (old B0D5ZSGDC3 $22.65 wrong)
    '51-08': ('55.26',  'https://www.amazon.com/dp/B075GWMKMT', True),   # Warriors

    # ── Warcry ────────────────────────────────────────────────────────────
    # WC-100 Warcry Starter Set — deactivated wave J; removed
    # WC-101 Warcry Heart of Ghur — deactivated wave J; removed
    # WC-102 Warcry Hunter and Hunted — deactivated wave J; removed

    # ── Warhammer 40,000 General ──────────────────────────────────────────
    # 40-01 Core Rules — deactivated wave J; removed
    # 40-02 Leviathan Starter Set — Amazon does not carry this limited launch box; NOT_AVAIL (wave E)
    # 40-03 Starter Set — deactivated wave J; removed
    # 40-10 Chapter Approved: Leviathan — deactivated wave J; removed
    # 40-20 Dice Set — deactivated wave J; removed
    # 40-21 Measuring Tape — deactivated wave J; removed

    # ── World Eaters ──────────────────────────────────────────────────────
    '43-04': ('140.00', 'https://www.amazon.com/dp/B0BTDDDLD5', True),   # Angron  ✓ FIXED wave J (old B0DZZNHNJ2 $345.00 wrong)
    '43-60': ('57.45',  'https://www.amazon.com/dp/B0BTDHL1MH', False),  # Berzerkers
    '43-95': ('134.03', 'https://www.amazon.com/dp/B0F5X8GV4B', True),   # Combat Patrol
    '43-62': ('55.25',  'https://www.amazon.com/dp/B0BTDD6Z24', False),  # Eightbound
    '43-64': ('58.65',  'https://www.amazon.com/dp/B0BTDDBHPM', False),  # Lord on Juggernaut
}


class Command(BaseCommand):
    """Seed Amazon prices from the March 2026 Octoparse scrape."""

    help = (
        'Write verified Amazon prices into CurrentPrice, keyed by GW SKU. '
        'Idempotent — safe to re-run.'
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
            amazon_retailer = Retailer.objects.get(name='Amazon')
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Amazon' not found in the database.")

        sku_to_product = {
            p.gw_sku: p
            for p in Product.objects.filter(is_active=True).only('id', 'gw_sku', 'name')
        }
        self.stdout.write(f'Active products loaded: {len(sku_to_product)}')
        self.stdout.write(f'Amazon rows to import:  {len(AMAZON_DATA)}')
        self.stdout.write('')

        applied = 0
        skipped = 0

        for sku, (price_str, url, in_stock) in sorted(AMAZON_DATA.items()):
            product = sku_to_product.get(sku)
            if not product:
                self.stdout.write(
                    self.style.WARNING(f'  [skip] {sku} — not found in active products')
                )
                skipped += 1
                continue

            price = decimal.Decimal(price_str) if price_str else None
            self.stdout.write(
                f"  [{'dry' if dry_run else 'set'}] {sku:8s}  "
                f"{'$'+price_str if price_str else 'no price':>10s}  "
                f"{'IN STOCK' if in_stock else 'out-of-stock':12s}  {product.name}"
            )

            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=amazon_retailer,
                    defaults={
                        'price'        : price,
                        'url'          : url,
                        'in_stock'     : in_stock,
                        'not_available': False,
                        'listing_title': '',
                    },
                )
            applied += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n{'[DRY RUN] ' if dry_run else ''}Done!  "
            f"Applied: {applied}  Skipped: {skipped}"
        ))
