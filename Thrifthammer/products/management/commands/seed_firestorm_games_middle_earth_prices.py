"""
Seed Firestorm Games UK prices for Middle-earth Strategy Battle Game (MESBG).

Idempotent -- CurrentPrice rows are written via update_or_create keyed on
(product, retailer), so re-running is always safe. NEVER writes msrp_gbp --
Firestorm is a discount competitor, not the MSRP source. Only
games-workshop-uk writes msrp_gbp.

Price parsing rule: Firestorm shows two numbers per listing (struck-through
RRP, then sale price). ALWAYS use the lower (sale) price, never the RRP.
RRP is only used as a matching aid to confirm which DB SKU a listing
corresponds to (it should equal Product.msrp_gbp for the matched SKU).

Built incrementally across multiple Firestorm category pages per user
request (MESBG catalog is being worked through in chunks). Do not treat
this file as "done" until the user explicitly says the full MESBG sweep
across Firestorm is complete -- more entries will be appended per chunk.

--- Chunk 1: https://www.firestormgames.co.uk/lord-of-the-rings---forces-of-evil ---
(Angmar, Barad-Dur, Corsairs of Umbar, Far Harad, Isengard, Mordor, Moria,
Sharkey's Rogues, The Easterlings, The Hill Tribes, The Serpent Horde
sub-categories, plus the separately-hosted Variags of Khand page which is
currently empty on Firestorm -- no products listed there at all.)
25 of 95 active DB MESBG-XXX SKUs matched on this page. Many Firestorm
listings on this page have no DB counterpart at all (character/unit kits
our catalog doesn't track individually, e.g. Dead Marsh Spectres, Shade
of Angmar, The Dark Lord Sauron, Lurtz and Ugluk, Suladan the Serpent
Lord, etc.) -- those are not gaps, just uncovered SKUs, and are not
reported until the full sweep across all chunks is complete per user
instruction. Care was taken NOT to force-match same-price Firestorm
listings with different unit names to DB SKUs (e.g. "Uruk-hai Berserkers"
and "Uruk-Hai With Crossbows" both share MESBG-071's £21.50 price point
but are named differently from "Uruk-Hai Demolition Team" -- left
unmatched rather than guessed).

--- Chunk 2: https://www.firestormgames.co.uk/lord-of-the-rings---forces-of-good ---
(Arnor, Fangorn, Lothlorien, Minas Tirith, Numenor, Rivendell, Rohan, The
Dead of Dunharrow, The Fellowship, The Fiefdoms, The Kingdom of
Khazad-Dum, The Misty Mountains, The Rangers, The Shire, Wanderers in the
Wild, Wildmen of Druadan sub-categories.)
35 more DB SKUs matched on this page (60/95 cumulative). Same
no-force-match discipline as chunk 1 applied throughout.

Flagged, NOT matched: "Rangers of Middle-earth" appears twice on this
page (Arnor and Minas Tirith sections), both at £35.63/£37.50 -- but
MESBG-048 "Rangers of Middle-earth" has msrp_gbp=32.50, a ~15% gap too
large to treat as a normal small RRP/msrp flag-and-match. Left unmatched
pending user confirmation rather than assumed.

Note: a second, differently-priced "Warriors of Rohan" listing exists at
/warriors-of-rohan (£29.93/£31.50, Unavailable) distinct from the exact
msrp-matching /middle-earth-strategy-battle-game:-warriors-of-rohan
(£28.60/£32.50) already used for MESBG-075 -- the duplicate/stale £31.50
listing was intentionally not used.

--- Chunk 3: https://www.firestormgames.co.uk/the-hobbit---forces-of-evil ---
(Azog's Hunters, Azog's Legion, Dark Powers of Dol Guldur, Goblin Town,
The Dark Denizens of Mirkwood, The Trolls sub-categories, plus the
separately-hosted Desolator of the North page which is currently empty
on Firestorm -- same as Variags of Khand in chunk 1.)
7 more DB SKUs matched (67/95 cumulative).

Flagged, NOT matched: "Mirkwood Spiders" is £35.63/£37.50 here -- no DB
SKU at that price; not the same product as MESBG-034 "Mirkwood Rangers"
(32.50) despite the similar name, so left unmatched rather than guessed.

--- Chunk 4: https://www.firestormgames.co.uk/the-hobbit---forces-of-good ---
(Army of Thror, Garrison of Dale, Halls of Thranduil, Radagast's
Alliance, The Army of Lake Town, The Survivor's of Lake Town, Thorin's
Company sub-categories, plus the separately-hosted Erebor Reclaimed page
which is currently empty on Firestorm.)
6 more DB SKUs matched (73/95 cumulative): MESBG-032 Warriors of Erebor,
MESBG-031 Grim Hammers, MESBG-080 Warriors of Dale, MESBG-034 Mirkwood
Rangers, MESBG-033 Palace Guards, MESBG-029 Thorin Oakenshield & Company.

--- Chunk 5 (final): https://www.firestormgames.co.uk/wargames-miniatures/middle-earth#c272187 ---
(Getting Started, Terrain sub-categories -- the hub page's own rulebook/
army-book/terrain listings not covered by any of the faction-specific
sub-pages in chunks 1-4.)
19 more DB SKUs matched (92/95 cumulative -- final total). 3 genuine gaps
remain after all 5 chunks, none found anywhere on Firestorm:
- MESBG-005 Middle-earth Strategy Battle Game: Matched Play Guide (msrp
  £20.00) -- NOT the same as "Rules Manual (Old Edition)" seen on this
  page (£20.00 sale / £40.00 RRP, a different, superseded product)
- MESBG-048 Rangers of Middle-earth (msrp £32.50) -- Firestorm carries a
  same-named item but at £37.50 RRP, a ~15% gap too large to force-match
  (seen twice in chunk 2, flagged there, never resolved)
- MESBG-071 Uruk-Hai Demolition Team (msrp £21.50) -- not found on any
  of the 5 pages/sub-pages covered this session
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_FIRESTORM_SLUG = 'firestorm-games'

_PRICES = [
    # --- Chunk 1: Forces of Evil ---
    ('MESBG-078', 'Middle-Earth Strategy Battle Game: The Witch-King of Angmar', Decimal('20.68'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-the-witch-king-of-angmar?aff=6a4ab07d1c6f9'),
    ('MESBG-038', 'Middle Earth Strategy Battle Game: Wild Wargs', Decimal('12.84'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-wild-wargs?aff=6a4ab07d1c6f9'),
    ('MESBG-056', 'Warg Riders', Decimal('25.08'),
     'https://www.firestormgames.co.uk/warg-riders?aff=6a4ab07d1c6f9'),
    ('MESBG-058', 'Mordor Orcs', Decimal('28.60'),
     'https://www.firestormgames.co.uk/mordor-orcs?aff=6a4ab07d1c6f9'),
    ('MESBG-046', 'Middle-Earth Strategy Battle Game: Morgul Knights', Decimal('27.09'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-morgul-knights?aff=6a4ab07d1c6f9'),
    ('MESBG-040', 'Middle Earth Strategy Battle Game: Winged Nazgul', Decimal('39.16'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-winged-nazgul?aff=6a4ab07d1c6f9'),
    ('MESBG-042', 'Middle Earth Strategy Battle Game: Mordor Troll / Isengard Troll', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-mordor-troll--isengard-troll?aff=6a4ab07d1c6f9'),
    ('MESBG-086', 'Middle-Earth Strategy Battle Game: Corsairs of Umbar', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-corsairs-of-umbar?aff=6a4ab07d1c6f9'),
    ('MESBG-085', 'War Mumak of Harad', Decimal('65.12'),
     'https://www.firestormgames.co.uk/war-mumak-of-harad?aff=6a4ab07d1c6f9'),
    ('MESBG-018', 'Middle-Earth Strategy Battle Game - Isengard Battlehost', Decimal('51.04'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game---isengard-battlehost?aff=6a4ab07d1c6f9'),
    ('MESBG-089', 'Middle Earth Strategy Battle Game: Uruk-hai Scouts', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-uruk-hai-scouts?aff=6a4ab07d1c6f9'),
    ('MESBG-023', 'Saruman the White and Grima Wormtongue', Decimal('25.08'),
     'https://www.firestormgames.co.uk/saruman-the-white-and-grima-wormtongue?aff=6a4ab07d1c6f9'),
    ('MESBG-059', 'Uruk-Hai Warriors', Decimal('28.60'),
     'https://www.firestormgames.co.uk/uruk-hai-warriors?aff=6a4ab07d1c6f9'),
    ('MESBG-062', 'Middle Earth Strategy Battle Game: The Path of Cirith Ungol: Shelob & Gollum', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-the-path-of-cirith-ungol:-shelob--gollum?aff=6a4ab07d1c6f9'),
    ('MESBG-016', 'Middle-Earth Strategy Battle Game: Gothmog, Lieutenant of Sauron', Decimal('27.07'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-gothmog-lieutenant-of-sauron?aff=6a4ab07d1c6f9'),
    ('MESBG-057', 'Morannon Orcs', Decimal('28.60'),
     'https://www.firestormgames.co.uk/morannon-orcs?aff=6a4ab07d1c6f9'),
    ('MESBG-055', 'Middle-Earth Strategy Battle Game: Moria Goblins', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-moria-goblins?aff=6a4ab07d1c6f9'),
    ('MESBG-041', 'The Balrog', Decimal('39.16'),
     'https://www.firestormgames.co.uk/the-balrog?aff=6a4ab07d1c6f9'),
    ('MESBG-049', 'Middle-Earth Strategy Battle Game: Easterling Kataphracts', Decimal('27.09'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-easterling-kataphracts?aff=6a4ab07d1c6f9'),
    ('MESBG-050', 'Middle Earth Strategy Battle Game: Easterling Warriors', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-easterling-warriors?aff=6a4ab07d1c6f9'),
    ('MESBG-010', 'Middle Earth Strategy Battle Game: Hill Tribesmen Commanders', Decimal('25.96'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-hill-tribesmen-commanders?aff=6a4ab07d1c6f9'),
    ('MESBG-072', 'Middle-Earth Strategy Battle Game: Wulf, High Lord of the Hill Tribes & General Targg', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-wulf-high-lord-of-the-hill-tribes--general-targg?aff=6a4ab07d1c6f9'),
    ('MESBG-295', 'Middle Earth Strategy Battle Game: Hill Tribesmen', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-hill-tribesmen?aff=6a4ab07d1c6f9'),
    ('MESBG-047', 'Middle-Earth Strategy Battle Game: Haradrim Warriors', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-haradrim-warriors?aff=6a4ab07d1c6f9'),
    ('MESBG-087', 'Middle-Earth Strategy Battle Game: Haradrim Raiders', Decimal('27.09'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-haradrim-raiders?aff=6a4ab07d1c6f9'),

    # --- Chunk 2: Forces of Good ---
    ('MESBG-021', 'Middle Earth SBG: Treebeard Mighty Ent', Decimal('47.96'),
     'https://www.firestormgames.co.uk/middle-earth-sbg:-treebeard-mighty-ent?aff=6a4ab07d1c6f9'),
    ('MESBG-083', 'Middle-Earth Strategy Battle Game: Ent', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-ent?aff=6a4ab07d1c6f9'),
    ('MESBG-054', 'Middle-Earth Strategy Battle Game: LOTHLÓRIEN Wood Elf Warriors', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-lothlrien-wood-elf-warriors?aff=6a4ab07d1c6f9'),
    ('MESBG-052', 'Middle-Earth Strategy Battle Game: Galadhrim Knights', Decimal('27.09'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-galadhrim-knights?aff=6a4ab07d1c6f9'),
    ('MESBG-053', 'Middle-Earth Strategy Battle Game: Galadhrim Warriors', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-galadhrim-warriors?aff=6a4ab07d1c6f9'),
    ('MESBG-077', 'Middle-Earth Strategy Battle Game: Faramir, Madril and Damrod, Rangers of Ithilien', Decimal('27.07'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-faramir-madril-and-damrod-rangers-of-ithilien?aff=6a4ab07d1c6f9'),
    ('MESBG-288', 'Middle Earth Strategy Battle Game: Imrahil Of Dol Amroth', Decimal('20.68'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-imrahil-of-dol-amroth?aff=6a4ab07d1c6f9'),
    ('MESBG-012', 'Middle-Earth Strategy Battle Game - Minas Tirith Battlehost', Decimal('51.04'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game---minas-tirith-battlehost?aff=6a4ab07d1c6f9'),
    ('MESBG-030', 'Gandalf the White & Peregrin Took', Decimal('25.08'),
     'https://www.firestormgames.co.uk/gandalf-the-white--peregrin-took?aff=6a4ab07d1c6f9'),
    ('MESBG-051', 'Middle Earth Strategy Battle Game: Warriors of Minas Tirith', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-warriors-of-minas-tirith?aff=6a4ab07d1c6f9'),
    ('MESBG-088', 'Knights of Minas Tirith', Decimal('25.08'),
     'https://www.firestormgames.co.uk/knights-of-minas-tirith?aff=6a4ab07d1c6f9'),
    ('MESBG-045', 'Middle-Earth Strategy Battle Game: Knights Of Dol Amroth', Decimal('27.07'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-knights-of-dol-amroth?aff=6a4ab07d1c6f9'),
    ('MESBG-037', 'Middle-Earth Strategy Battle Game: Warriors of the Last Alliance', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-warriors-of-the-last-alliance?aff=6a4ab07d1c6f9'),
    ('MESBG-019', 'Middle Earth Strategy Battle Game: Elrond Master of Rivendell', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-elrond-master-of-rivendell?aff=6a4ab07d1c6f9'),
    ('MESBG-060', 'Knights Of Rivendell', Decimal('30.88'),
     'https://www.firestormgames.co.uk/knights-of-rivendell?aff=6a4ab07d1c6f9'),
    ('MESBG-011', 'Middle Earth Strategy Battle Game: Warriors of Rohan Commanders', Decimal('25.96'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-warriors-of-rohan-commanders?aff=6a4ab07d1c6f9'),
    ('MESBG-076', 'Middle Earth Strategy Battle Game: Riders of Rohan', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-riders-of-rohan?aff=6a4ab07d1c6f9'),
    ('MESBG-063', 'Middle Earth Strategy Battle Game: Fréaláf Hildeson, Olwyn, Lief, Heroes of Rohan', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-fralf-hildeson-olwyn-lief-heroes-of-rohan?aff=6a4ab07d1c6f9'),
    ('MESBG-064', 'Middle Earth Strategy Battle Game: Helm Hammerhand, King of Rohan', Decimal('20.68'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-helm-hammerhand-king-of-rohan?aff=6a4ab07d1c6f9'),
    ('MESBG-065', 'Middle Earth Strategy Battle Game: Hera Daughter Of Helm', Decimal('20.68'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-hera-daughter-of-helm?aff=6a4ab07d1c6f9'),
    ('MESBG-073', 'Middle Earth Strategy Battle Game: Haleth & Háma, Princes of Rohan', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-haleth--hma-princes-of-rohan?aff=6a4ab07d1c6f9'),
    ('MESBG-075', 'Middle Earth Strategy Battle Game: Warriors Of Rohan', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-warriors-of-rohan?aff=6a4ab07d1c6f9'),
    ('MESBG-025', 'Middle-Earth Strategy Battle Game: Rohan Royal Knights', Decimal('36.58'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-rohan-royal-knights?aff=6a4ab07d1c6f9'),
    ('MESBG-024', 'Middle-Earth Strategy Battle Game: Mounted Rohan Command', Decimal('40.38'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-mounted-rohan-command?aff=6a4ab07d1c6f9'),
    ('MESBG-027', 'Middle Earth Strategy Battle Game: Eowyn and Merry', Decimal('25.08'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-eowyn-and-merry?aff=6a4ab07d1c6f9'),
    ('MESBG-081', 'Middle Earth Strategy Battle Game: Theoden King of Rohan', Decimal('22.32'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-theoden-king-of-rohan?aff=6a4ab07d1c6f9'),
    ('MESBG-026', 'Middle Earth: King of the Dead & Heralds', Decimal('25.08'),
     'https://www.firestormgames.co.uk/middle-earth:-king-of-the-dead--heralds?aff=6a4ab07d1c6f9'),
    ('MESBG-084', 'Middle-Earth Strategy Battle Game: Warriors of the Dead', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-warriors-of-the-dead?aff=6a4ab07d1c6f9'),
    ('MESBG-082', 'Legolas Greenleaf and Tauriel, Mirkwood Hunters', Decimal('22.32'),
     'https://www.firestormgames.co.uk/legolas-greenleaf-and-tauriel-mirkwood-hunters?aff=6a4ab07d1c6f9'),
    ('MESBG-028', 'Middle Earth Strategy Battle Game: The Three Hunters', Decimal('25.08'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-the-three-hunters?aff=6a4ab07d1c6f9'),
    ('MESBG-039', 'Middle Earth Strategy Battle Game: Fellowship of the Ring', Decimal('33.44'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-fellowship-of-the-ring?aff=6a4ab07d1c6f9'),
    ('MESBG-044', 'Middle-Earth Strategy Battle Game: Dwarf Warriors', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-dwarf-warriors?aff=6a4ab07d1c6f9'),
    ('MESBG-043', 'Middle-Earth Strategy Battle Game: Dwarf Rangers', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-dwarf-rangers?aff=6a4ab07d1c6f9'),
    ('MESBG-074', 'Middle Earth Strategy Battle Game: Great Eagles', Decimal('31.24'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-great-eagles-?aff=6a4ab07d1c6f9'),
    ('MESBG-079', 'Middle Earth Strategy Battle Game: Eomer, Marshal of the Riddermark', Decimal('20.68'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-eomer-marshal-of-the-riddermark?aff=6a4ab07d1c6f9'),

    # --- Chunk 3: The Hobbit - Forces of Evil ---
    ('MESBG-093', 'Middle Earth Strategy Battle Game: Bolg Spawn Of Azog', Decimal('20.68'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-bolg-spawn-of-azog?aff=6a4ab07d1c6f9'),
    ('MESBG-061', 'Middle-Earth Strategy Battle Game: Hunter Orcs on Fell Wargs', Decimal('27.09'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-hunter-orcs-on-fell-wargs?aff=6a4ab07d1c6f9'),
    ('MESBG-036', 'Middle-Earth Strategy Battle Game: Hunter Orcs', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-hunter-orcs?aff=6a4ab07d1c6f9'),
    ('MESBG-070', 'Middle-Earth Strategy Battle Game: The Goblin King & Retinue', Decimal('33.74'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-the-goblin-king--retinue?aff=6a4ab07d1c6f9'),
    ('MESBG-035', 'Goblin Warriors', Decimal('30.88'),
     'https://www.firestormgames.co.uk/goblin-warriors?aff=6a4ab07d1c6f9'),
    ('MESBG-091', 'Middle-Earth Strategy Battle Game: Fell Wargs', Decimal('20.90'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-fell-wargs?aff=6a4ab07d1c6f9'),
    ('MESBG-069', 'Middle-Earth Strategy Battle Game: Tom, Bill, and Bert - The Trolls', Decimal('54.16'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-tom-bill-and-bert---the-trolls?aff=6a4ab07d1c6f9'),

    # --- Chunk 4: The Hobbit - Forces of Good ---
    ('MESBG-032', 'Middle Earth Strategy Battle Game: Warriors of Erebor', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-warriors-of-erebor?aff=6a4ab07d1c6f9'),
    ('MESBG-031', 'Grim Hammers', Decimal('30.88'),
     'https://www.firestormgames.co.uk/grim-hammers?aff=6a4ab07d1c6f9'),
    ('MESBG-080', 'Middle Earth Strategy Battle Game: Warriors of Dale', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-warriors-of-dale?aff=6a4ab07d1c6f9'),
    ('MESBG-034', 'Middle-Earth Strategy Battle Game: Mirkwood Rangers', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-mirkwood-rangers?aff=6a4ab07d1c6f9'),
    ('MESBG-033', 'Middle Earth Strategy Battle Game: Palace Guards', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-palace-guards?aff=6a4ab07d1c6f9'),
    ('MESBG-029', 'Thorin Oakenshield & Company', Decimal('33.44'),
     'https://www.firestormgames.co.uk/thorin-oakenshield--company?aff=6a4ab07d1c6f9'),

    # --- Chunk 5 (final): Getting Started + Terrain hub sections ---
    ('MESBG-003', 'Middle Earth Strategy Battle Game: Burning Of The Westfold', Decimal('14.96'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-burning-of-the-westfold?aff=6a4ab07d1c6f9'),
    ('MESBG-002', 'Middle Earth Strategy Battle Game: The Treachery of Gollum', Decimal('14.96'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-the-treachery-of-gollum?aff=6a4ab07d1c6f9'),
    ('MESBG-004', 'Middle Earth Strategy Battle Game: The War of the Rohirrim', Decimal('14.96'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-the-war-of-the-rohirrim?aff=6a4ab07d1c6f9'),
    ('MESBG-006', 'Middle Earth Strategy Battle Game: Armies Of Middle-Earth', Decimal('31.24'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-armies-of-middle-earth?aff=6a4ab07d1c6f9'),
    ('MESBG-007', 'Middle Earth Strategy Battle Game: Armies of The Hobbit', Decimal('31.24'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-armies-of-the-hobbit?aff=6a4ab07d1c6f9'),
    ('MESBG-008', 'Middle Earth Strategy Battle Game: Armies of The Lord of The Rings', Decimal('36.00'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-armies-of-the-lord-of-the-rings?aff=6a4ab07d1c6f9'),
    ('MESBG-009', 'Middle Earth Strategy Battle Game: Rules Manual', Decimal('31.24'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-rules-manual?aff=6a4ab07d1c6f9'),
    ('MESBG-001', 'Middle Earth Strategy Battle Game: The War of the Rohirrim - Battle of Edoras', Decimal('119.00'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-the-war-of-the-rohirrim---battle-of-edoras?aff=6a4ab07d1c6f9'),
    ('MESBG-017', 'Middle-Earth Strategy Battle Game: Ruins of Middle-earth', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-ruins-of-middle-earth?aff=6a4ab07d1c6f9'),
    ('MESBG-092', 'Goblin Town', Decimal('42.27'),
     'https://www.firestormgames.co.uk/goblin-town?aff=6a4ab07d1c6f9'),
    ('MESBG-068', 'Middle Earth Strategy Battle Game: Rohan Stronghold', Decimal('176.00'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-rohan-stronghold?aff=6a4ab07d1c6f9'),
    ('MESBG-015', 'Middle Earth Strategy Battle Game: Gondor Ruins', Decimal('28.60'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-gondor-ruins?aff=6a4ab07d1c6f9'),
    ('MESBG-013', 'Middle Earth Strategy Battle Game: Gondor Tower', Decimal('37.40'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-gondor-tower?aff=6a4ab07d1c6f9'),
    ('MESBG-014', 'Middle Earth Strategy Battle Game: Gondor Mansion', Decimal('47.96'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-gondor-mansion?aff=6a4ab07d1c6f9'),
    ('MESBG-020', 'Middle-Earth Strategy Battle Game: Ruins of Dol Guldur', Decimal('43.56'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-ruins-of-dol-guldur?aff=6a4ab07d1c6f9'),
    ('MESBG-022', 'Middle-Earth Strategy Battle Game: Mines of Moria', Decimal('18.05'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-mines-of-moria?aff=6a4ab07d1c6f9'),
    ('MESBG-067', 'Middle-Earth Strategy Battle Game: Rohan Watchtower and Palisades', Decimal('51.77'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-rohan-watchtower-and-palisades?aff=6a4ab07d1c6f9'),
    ('MESBG-066', 'Middle-Earth Strategy Battle Game: Rohan House', Decimal('30.88'),
     'https://www.firestormgames.co.uk/middle-earth-strategy-battle-game:-rohan-house?aff=6a4ab07d1c6f9'),
    ('MESBG-090', 'Lake-Town House', Decimal('30.88'),
     'https://www.firestormgames.co.uk/lake-town-house?aff=6a4ab07d1c6f9'),
]


class Command(BaseCommand):
    help = 'Seed Firestorm Games UK prices for Middle-earth SBG. Idempotent.'

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
                f'Seeded {seeded} Firestorm Games Middle-earth SBG prices. Skipped: {skipped}.'
            )
        )
