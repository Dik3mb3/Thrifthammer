"""
Management command: seed_nk_sm_phase2_prices

Seeds Noble Knight Games CurrentPrice entries for Space Marines phase-2 and
phase-3 products (from populate_sm_phase2_products, populate_sm_phase3_products,
and populate_successor_chapters_products).

URLs sourced from NK category pages and web search — 2026-04-04.
Affiliate parameter ?awid=1576 appended to all URLs per NK affiliate program.

Because no NK Octoparse scrape exists for these SM products yet, all found
products are seeded with price=None, in_stock=False as placeholders. The NK
price scraper will populate real prices and stock status on its next run.

Products not listed on NK are seeded with not_available=True and no URL.

SHARED-KIT MAPPINGS (same physical box → same NK URL):
  - Centurion Devastator + Centurion Assault → /P/2147531872/Centurion-Devastator-Squad
  - Storm Speeder Thunderstrike / Hammerstrike / Hailstrike → /P/2147864793/Storm-Speeder
  - Gladiator Lancer / Reaper / Valiant → /P/2147851146/Space-Marines-Gladiator
  - Murderfang + Wulfen Dreadnought → /P/2147845669/Space-Wolves-Venerable-Dreadnought
    (NK lists Bjorn separately at /P/2147440744/Bjorn-the-Fell-Handed---Dreadnought)
  - GK Purifier/Purgation/Interceptor → /P/2147555962/Grey-Knight-Purifiers (same box)

QUESTIONABLE MATCHES — verify before next scraper run:
  ┌─────────────────────────────────────────────┬────────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┐
  │ Product (slug)                              │ NK URL                                     │ Note                                                                │
  ├─────────────────────────────────────────────┼────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ blood-angels-librarian-terminator-armour    │ /P/2147566992/Librarian-in-Terminator-Armor│ Old Finecast-era kit (2014). Only BA Librarian in Term. Armour on NK │
  │ grey-knights-paladins                       │ /P/2147931148/Brotherhood-Terminator-Squad │ Brotherhood Terminator box builds as Paladins; no standalone kit     │
  │ grey-knights-purifier/purgation/interceptor │ /P/2147555962/Grey-Knight-Purifiers        │ One box builds all 3 unit types; linked to Purifiers listing         │
  │ space-wolves-bjorn-fell-handed              │ /P/2147440744/Bjorn-the-Fell-Handed        │ NK has a separate Bjorn listing but it's same plastic as SW Ven.Dread│
  │ imperial-fists-tor-garadon                  │ /P/2147770655/Tor-Garadon                  │ Listed as "Out of Print" on NK; URL seeded for scraper               │
  │ white-scars-korsarro-khan                   │ /P/2147971026/White-Scars-KorSarro-Khan    │ 2020 edition (old single-pose Primaris sculpt); correct match        │
  │ raven-guard-kayvaan-shrike                  │ /P/2147766283/Raven-Guard-Kayvaan-Shrike   │ 2019 edition listing; newest available Shrike retail kit on NK       │
  │ space-marine-centurion-assault-squad        │ /P/2147531872/Centurion-Devastator-Squad   │ Same physical box as Devastator Squad; linked to that NK listing     │
  ├─────────────────────────────────────────────┼────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────┤
  │ NOT FOUND ON NK (not_available=True):                                                                                                                       │
  │ space-marine-captain-with-relic-shield      │ —                                          │ Only loose numbered minis found; no retail box listing on NK         │
  │ blood-angels-chaplain-jump-pack             │ —                                          │ No retail box found; only old loose metal minis                      │
  │ dark-angels-interrogator-chaplain           │ —                                          │ Only loose Seraphicus minis; no current retail box                   │
  │ iron-hands-caanok-var                       │ —                                          │ 2025 GW release; not yet listed on NK                                │
  │ salamanders-vulkan-hestan                   │ —                                          │ 2025 GW release; not yet listed on NK                                │
  │ imperial-fists-darnath-lysander             │ —                                          │ 2025 GW release; not yet listed on NK                                │
  │ white-scars-suboden-khan                    │ —                                          │ 2025 GW release; not yet listed on NK                                │
  │ raven-guard-aethon-shaan                    │ —                                          │ 2025 GW release; not yet listed on NK                                │
  └─────────────────────────────────────────────┴────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────┘

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_nk_sm_phase2_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# ── Noble Knight SM phase-2 / phase-3 URL data ───────────────────────────────
# (slug, listing_title, price, url, in_stock, not_available)
# price=None → placeholder; NK price scraper will populate on next run.
# not_available=True → product not found on NK; no URL seeded.
# All URLs include ?awid=1576 affiliate parameter.
NK_PRICES = [

    # ── Generic SM Phase-2: Characters ───────────────────────────────────────

    (
        'space-marine-techmarine',
        'Primaris Techmarine',
        None,
        'https://www.nobleknight.com/P/2147844408/Primaris-Techmarine?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-captain-in-gravis-armour',
        'Captain in Gravis Armor',
        None,
        'https://www.nobleknight.com/P/2147955095/Captain-in-Gravis-Armor?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-captain-in-phobos-armour',
        'Primaris Captain in Phobos Armor (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147831544/Primaris-Captain-in-Phobos-Armor-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-captain-with-jump-pack',
        'Captain w/Jump Pack',
        None,
        'https://www.nobleknight.com/P/2148086755/Captain-w-Jump-Pack?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-captain-jump-pack-relic-shield',
        'Captain w/Jump Pack & Relic Shield',
        None,
        'https://www.nobleknight.com/P/2148359689/Captain-w-Jump-Pack-and-Relic-Shield?awid=1576',
        False,
        False,
    ),
    (
        # No retail box found on NK — only loose numbered individual minis
        'space-marine-captain-with-relic-shield',
        'Captain with Relic Shield',
        None,
        '',
        False,
        True,
    ),
    (
        'space-marine-captain-in-terminator-armour',
        'Captain in Terminator Armour',
        None,
        'https://www.nobleknight.com/P/2148118434/Captain-in-Terminator-Armour?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-lieutenant-in-phobos-armour',
        'Primaris Lieutenant in Reiver Armour',
        None,
        'https://www.nobleknight.com/P/2147845620/Primaris-Lieutenant-in-Reiver-Armour?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-lieutenant-with-power-sword',
        'Primaris Lieutenant w/Power Sword (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147831538/Primaris-Lieutenant-w-Power-Sword-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-lieutenant-with-storm-shield',
        'Primaris Lieutenant w/Storm Shield',
        None,
        'https://www.nobleknight.com/P/2147948407/Primaris-Lieutenant-w-Storm-Shield-Space-Marines?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-librarian-in-phobos-armour',
        'Primaris Librarian in Phobos Armor',
        None,
        'https://www.nobleknight.com/P/2147867312/Primaris-Librarian-in-Phobos-Armor?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-librarian-in-terminator-armour',
        'Librarian in Terminator Armour',
        None,
        'https://www.nobleknight.com/P/2148065641/Librarian-in-Terminator-Armour?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-ancient-in-terminator-armour',
        'Ancient in Terminator Armour',
        None,
        'https://www.nobleknight.com/P/2148378733/Ancient-in-Terminator-Armour?awid=1576',
        False,
        False,
    ),

    # ── Generic SM Phase-2: Infantry ─────────────────────────────────────────

    (
        'space-marine-hellblaster-squad',
        'Primaris Hellblasters',
        None,
        'https://www.nobleknight.com/P/2147673854/Primaris-Hellblasters?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-reiver-squad',
        'Primaris Reivers (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147833307/Primaris-Reivers-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-heavy-intercessor-squad',
        'Heavy Intercessors',
        None,
        'https://www.nobleknight.com/P/2147889353/Heavy-Intercessors?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-terminator-assault-squad',
        'Terminator Assault Squad',
        None,
        'https://www.nobleknight.com/P/2148378732/Terminator-Assault-Squad?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-centurion-devastator-squad',
        'Centurion Devastator Squad',
        None,
        'https://www.nobleknight.com/P/2147531872/Centurion-Devastator-Squad?awid=1576',
        False,
        False,
    ),
    (
        # Same physical box as Centurion Devastator Squad
        'space-marine-centurion-assault-squad',
        'Centurion Devastator Squad',
        None,
        'https://www.nobleknight.com/P/2147531872/Centurion-Devastator-Squad?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-assault-intercessors-jump-packs',
        'Jump Pack Intercessors',
        None,
        'https://www.nobleknight.com/P/2148086752/Jump-Pack-Intercessors?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-desolation-squad',
        'Desolation Squad',
        None,
        'https://www.nobleknight.com/P/2148086770/Desolation-Squad?awid=1576',
        False,
        False,
    ),

    # ── Generic SM Phase-2: Vehicles ─────────────────────────────────────────

    (
        'space-marine-chaplain-on-bike',
        'Primaris Chaplain on Bike',
        None,
        'https://www.nobleknight.com/P/2147838257/Primaris-Chaplain-on-Bike?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-venerable-dreadnought',
        'Venerable Dreadnought (2023 Edition)',
        None,
        'https://www.nobleknight.com/P/2148034746/Venerable-Dreadnought-2023-Edition?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-invictor-tactical-warsuit',
        'Primaris Invictor Tactical Warsuit (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147831502/Primaris-Invictor-Tactical-Warsuit-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-rhino',
        'Rhino (2017 Edition)',
        None,
        'https://www.nobleknight.com/P/2147930176/Rhino-2017-Edition?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-razorback',
        'Razorback (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147852271/Razorback-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-drop-pods',
        'Drop Pods',
        None,
        'https://www.nobleknight.com/P/2148320283/Drop-Pods?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-land-raider-redeemer',
        'Land Raider Crusader/Redeemer (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147831482/Land-Raider-Crusader-Redeemer-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        # Same physical kit as Predator Annihilator
        'space-marine-predator-destructor',
        'Predator',
        None,
        'https://www.nobleknight.com/P/2147930816/Predator?awid=1576',
        False,
        False,
    ),

    # ── Storm Speeders (same physical kit — 3 build options) ─────────────────

    (
        'space-marine-storm-speeder-thunderstrike',
        'Storm Speeder',
        None,
        'https://www.nobleknight.com/P/2147864793/Storm-Speeder?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-storm-speeder-hammerstrike',
        'Storm Speeder',
        None,
        'https://www.nobleknight.com/P/2147864793/Storm-Speeder?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-storm-speeder-hailstrike',
        'Storm Speeder',
        None,
        'https://www.nobleknight.com/P/2147864793/Storm-Speeder?awid=1576',
        False,
        False,
    ),

    # ── Gladiators (same physical kit — 3 build options) ─────────────────────

    (
        'space-marine-gladiator-lancer',
        'Space Marines Gladiator',
        None,
        'https://www.nobleknight.com/P/2147851146/Space-Marines-Gladiator?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-gladiator-reaper',
        'Space Marines Gladiator',
        None,
        'https://www.nobleknight.com/P/2147851146/Space-Marines-Gladiator?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-gladiator-valiant',
        'Space Marines Gladiator',
        None,
        'https://www.nobleknight.com/P/2147851146/Space-Marines-Gladiator?awid=1576',
        False,
        False,
    ),

    # ── Aircraft ─────────────────────────────────────────────────────────────

    (
        'space-marine-stormtalon-gunship',
        'Stormtalon Gunship',
        None,
        'https://www.nobleknight.com/P/2147470174/Stormtalon-Gunship?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-stormhawk-interceptor',
        'Stormhawk Interceptor (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147831484/Stormhawk-Interceptor-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        'space-marine-stormraven-gunship',
        'Stormraven Gunship',
        None,
        'https://www.nobleknight.com/P/2147442754/Stormraven-Gunship?awid=1576',
        False,
        False,
    ),

    # ── Codex ─────────────────────────────────────────────────────────────────

    (
        'codex-space-marines',
        'Codex - Space Marines (10th Edition)',
        None,
        'https://www.nobleknight.com/P/2148086745/Codex---Space-Marines-10th-Edition?awid=1576',
        False,
        False,
    ),

    # ── Phase-3: Blood Angels ─────────────────────────────────────────────────

    (
        # No current retail box found on NK — only old loose metal minis
        'blood-angels-chaplain-jump-pack',
        'Blood Angels Chaplain With Jump Pack',
        None,
        '',
        False,
        True,
    ),
    (
        # Old Finecast-era BA Librarian in Terminator Armour — only current listing on NK
        'blood-angels-librarian-terminator-armour',
        'Librarian in Terminator Armor',
        None,
        'https://www.nobleknight.com/P/2147566992/Librarian-in-Terminator-Armor?awid=1576',
        False,
        False,
    ),
    (
        'blood-angels-captain',
        'Blood Angels Captain',
        None,
        'https://www.nobleknight.com/P/2148203620/Blood-Angels-Captain?awid=1576',
        False,
        False,
    ),
    (
        'codex-supplement-blood-angels',
        'Codex Supplement - Blood Angels',
        None,
        'https://www.nobleknight.com/P/2148203594/Codex-Supplement---Blood-Angels?awid=1576',
        False,
        False,
    ),

    # ── Phase-3: Black Templars ───────────────────────────────────────────────

    (
        'codex-supplement-black-templars',
        'Codex Supplement - Black Templars',
        None,
        'https://www.nobleknight.com/P/2148370321/Codex-Supplement---Black-Templars?awid=1576',
        False,
        False,
    ),

    # ── Phase-3: Dark Angels ──────────────────────────────────────────────────

    (
        # Only loose Seraphicus minis found; no current retail box on NK
        'dark-angels-interrogator-chaplain',
        'Dark Angels Interrogator-Chaplain',
        None,
        '',
        False,
        True,
    ),
    (
        'dark-angels-ravenwing-bike-squadron',
        'Ravenwing Bike Squadron (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147850826/Bike-Squadron-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        'codex-supplement-dark-angels',
        'Codex - Dark Angels',
        None,
        'https://www.nobleknight.com/P/2148121771/Codex---Dark-Angels?awid=1576',
        False,
        False,
    ),

    # ── Phase-3: Grey Knights ─────────────────────────────────────────────────

    (
        'grey-knights-castellan-crowe',
        'Castellan Crowe',
        None,
        'https://www.nobleknight.com/P/2147970092/Castellan-Crowe?awid=1576',
        False,
        False,
    ),
    (
        # Grey Knight Purifiers box also builds Purgation and Interceptor Squads
        'grey-knights-purifier-squad',
        'Grey Knight Purifiers',
        None,
        'https://www.nobleknight.com/P/2147555962/Grey-Knight-Purifiers?awid=1576',
        False,
        False,
    ),
    (
        # Same physical box as Purifiers
        'grey-knights-purgation-squad',
        'Grey Knight Purifiers',
        None,
        'https://www.nobleknight.com/P/2147555962/Grey-Knight-Purifiers?awid=1576',
        False,
        False,
    ),
    (
        # Same physical box as Purifiers
        'grey-knights-interceptor-squad',
        'Grey Knight Purifiers',
        None,
        'https://www.nobleknight.com/P/2147555962/Grey-Knight-Purifiers?awid=1576',
        False,
        False,
    ),
    (
        # Brotherhood Terminator Squad box builds as Paladins; no standalone Paladins kit on NK
        'grey-knights-paladins',
        'Brotherhood Terminator Squad',
        None,
        'https://www.nobleknight.com/P/2147931148/Brotherhood-Terminator-Squad?awid=1576',
        False,
        False,
    ),
    (
        'grey-knights-grand-master-nemesis-dreadknight',
        'Grand Master in Nemesis Dreadknight',
        None,
        'https://www.nobleknight.com/P/2148347545/Grand-Master-in-Nemesis-Dreadknight?awid=1576',
        False,
        False,
    ),
    (
        'codex-grey-knights',
        'Codex - Grey Knights',
        None,
        'https://www.nobleknight.com/P/2148358528/Codex---Grey-Knights?awid=1576',
        False,
        False,
    ),

    # ── Phase-3: Space Wolves ─────────────────────────────────────────────────

    (
        'space-wolves-ulrik-the-slayer',
        'Ulrik the Slayer',
        None,
        'https://www.nobleknight.com/P/2147956505/Ulrik-the-Slayer?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-iron-priest',
        'Iron Priest',
        None,
        'https://www.nobleknight.com/P/2148382168/Iron-Priest?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-wulfen',
        'Wulfen',
        None,
        'https://www.nobleknight.com/P/2147930675/Wulfen?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-venerable-dreadnought',
        'Space Wolves Venerable Dreadnought',
        None,
        'https://www.nobleknight.com/P/2147845669/Space-Wolves-Venerable-Dreadnought?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-fenrisian-wolves',
        'Fenrisian Wolves',
        None,
        'https://www.nobleknight.com/P/2147932374/Fenrisian-Wolves?awid=1576',
        False,
        False,
    ),
    (
        # Same physical box as SW Venerable Dreadnought
        'space-wolves-murderfang',
        'Space Wolves Venerable Dreadnought',
        None,
        'https://www.nobleknight.com/P/2147845669/Space-Wolves-Venerable-Dreadnought?awid=1576',
        False,
        False,
    ),
    (
        # NK has a dedicated Bjorn listing; same plastic kit as SW Venerable Dreadnought
        'space-wolves-bjorn-fell-handed',
        'Bjorn the Fell-Handed - Dreadnought',
        None,
        'https://www.nobleknight.com/P/2147440744/Bjorn-the-Fell-Handed---Dreadnought?awid=1576',
        False,
        False,
    ),
    (
        # Same physical box as SW Venerable Dreadnought
        'space-wolves-wulfen-dreadnought',
        'Space Wolves Venerable Dreadnought',
        None,
        'https://www.nobleknight.com/P/2147845669/Space-Wolves-Venerable-Dreadnought?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-wolf-priest',
        'Wolf Priest',
        None,
        'https://www.nobleknight.com/P/2148320289/Wolf-Priest?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-wolf-guard-battle-leader',
        'Wolf Guard Battle Leader',
        None,
        'https://www.nobleknight.com/P/2148320293/Wolf-Guard-Battle-Leader?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-blood-claws',
        'Blood Claws',
        None,
        'https://www.nobleknight.com/P/2148320303/Blood-Claws?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-arjac-rockfist',
        'Arjac Rockfist',
        None,
        'https://www.nobleknight.com/P/2148320291/Arjac-Rockfist?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-njal-stormcaller',
        'Njal Stormcaller',
        None,
        'https://www.nobleknight.com/P/2148320297/Njal-Stormcaller?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-wolf-guard-headtakers',
        'Wolf Guard Headtakers',
        None,
        'https://www.nobleknight.com/P/2148320309/Wolf-Guard-Headtakers?awid=1576',
        False,
        False,
    ),
    (
        'space-wolves-logan-grimnar',
        'Logan Grimnar',
        None,
        'https://www.nobleknight.com/P/2148320311/Logan-Grimnar?awid=1576',
        False,
        False,
    ),
    (
        'codex-supplement-space-wolves',
        'Codex Supplement - Space Wolves',
        None,
        'https://www.nobleknight.com/P/2148320275/Codex-Supplement---Space-Wolves?awid=1576',
        False,
        False,
    ),

    # ── Successor Chapters: Iron Hands ────────────────────────────────────────

    (
        'iron-hands-iron-father-feirros',
        'Iron Father Feirros',
        None,
        'https://www.nobleknight.com/P/2147970086/Iron-Father-Feirros?awid=1576',
        False,
        False,
    ),
    (
        # 2025 GW release; not yet listed on NK
        'iron-hands-caanok-var',
        'Caanok Var',
        None,
        '',
        False,
        True,
    ),

    # ── Successor Chapters: Salamanders ──────────────────────────────────────

    (
        'salamanders-adrax-agatone',
        'Adrax Agatone (2020 Edition)',
        None,
        'https://www.nobleknight.com/P/2147841337/Adrax-Agatone-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        # 2025 GW release; not yet listed on NK
        'salamanders-vulkan-hestan',
        "Vulkan He'stan",
        None,
        '',
        False,
        True,
    ),

    # ── Successor Chapters: Imperial Fists ───────────────────────────────────

    (
        # Listed as Out of Print on NK; URL seeded for scraper to verify
        'imperial-fists-tor-garadon',
        'Tor Garadon (2019 Edition)',
        None,
        'https://www.nobleknight.com/P/2147770655/Tor-Garadon?awid=1576',
        False,
        False,
    ),
    (
        # 2025 GW release; not yet listed on NK
        'imperial-fists-darnath-lysander',
        'Darnath Lysander',
        None,
        '',
        False,
        True,
    ),

    # ── Successor Chapters: White Scars ──────────────────────────────────────

    (
        'white-scars-korsarro-khan',
        "White Scars Kor'Sarro Khan (2020 Edition)",
        None,
        'https://www.nobleknight.com/P/2147971026/White-Scars-KorSarro-Khan-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        # 2025 GW release; not yet listed on NK
        'white-scars-suboden-khan',
        'Suboden Khan',
        None,
        '',
        False,
        True,
    ),

    # ── Successor Chapters: Raven Guard ──────────────────────────────────────

    (
        'raven-guard-kayvaan-shrike',
        'Raven Guard Kayvaan Shrike (2019 Edition)',
        None,
        'https://www.nobleknight.com/P/2147766283/Raven-Guard-Kayvaan-Shrike?awid=1576',
        False,
        False,
    ),
    (
        # 2025 GW release; not yet listed on NK
        'raven-guard-aethon-shaan',
        'Aethon Shaan',
        None,
        '',
        False,
        True,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight Games URL rows for SM phase-2/3 products."""

    help = (
        'Seeds Noble Knight Games CurrentPrice URL placeholders for Space Marines phase-2 '
        'and phase-3 products. price=None for all rows — NK price scraper populates real '
        'prices on next run. Products not found on NK get not_available=True. '
        'Affiliate links use ?awid=1576. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        nk = Retailer.objects.filter(name='Noble Knight Games').first()
        if not nk:
            self.stderr.write(self.style.ERROR(
                'Noble Knight Games retailer not found — run populate_products first.'
            ))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0
        not_available_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  Skipped (product not found): {slug}'
                ))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={
                    'price': price,
                    'url': url,
                    'listing_title': listing_title,
                    'in_stock': in_stock,
                    'not_available': not_available,
                },
            )
            status = 'Created' if created else 'Updated'
            if not_available:
                self.stdout.write(self.style.WARNING(
                    f'  {status} (not available): {product.name}'
                ))
                not_available_count += 1
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'  {status}: {product.name} — URL seeded (price TBD by scraper)'
                ))
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nseed_nk_sm_phase2_prices complete.\n'
            f'  {created_count} created, {updated_count} updated, {skipped_count} skipped.\n'
            f'  {not_available_count} marked not_available (not listed on NK).'
        ))
