"""
Management command: populate_warhammer_40k_books

Creates the Warhammer 40,000 Books batch (Category: Warhammer, under Books
and Novels; Faction: Warhammer 40,000 Books -- both already created directly
against production, not by this command -- Faction created via one-off shell
command 2026-09-06, sibling to Horus Heresy Series under the same Category)
and seeds their Softback / Hardback BookFormatPrice rows from Games Workshop.

Sourced from a user-provided "Warhammer 40K Books.xlsx" GW storefront scrape
(80 rows). Six items were excluded as premium/collector editions that do not
fit the site's normal price-comparison categories (Deathwatch Special
Edition $75, Mephiston: The Box Set Limited Edition $170, Lucius: The
Faultless Blade Limited Edition $75, Hell's Last Special Edition $75, Outer
Dark Special Edition $75, Ghazghkull Thraka: Prophet of the Waaagh!
Illustrated and Annotated Edition $40 -- the regular $9.99 paperback of the
same book is kept). The Art of Warhammer 40,000 ($65 art book, no
traditional author/story) was excluded per explicit user instruction --
novels only. Faith & Fire (Hardback Anniversary Edition) was kept as a
normal hardback since it is priced in line with other hardbacks ($35), not
a $75+ collector edition.

One genuine Paperback+Hardback pair was found: The Infinite and the Divine.
Every other title in this batch is single-format only in GW's own listing.

Authors and ISBNs were cross-verified via WebSearch against Amazon, Simon &
Schuster (Black Library's US print distributor), Goodreads, and specialty
retailers -- never scraped from warhammer.com directly (bot-detection).
Where a confident value could not be found, the field is left blank rather
than guessed: Paragon of Faith and Other Stories' paperback ISBN, and Da
Freebooterz Code's hardback ISBN. "Legends of the Waaagh!" and "The Green
Tide" are genuinely multi-author anthologies (the publisher's storefront
credits only the lead contributor) -- shown as "Various Authors" per the
same convention used for Horus Heresy Series anthologies.

Amazon / eBay / Noble Knight / Miniature Market sourcing for these books is
out of scope for this batch -- GW only, US only, matching the Horus Heresy
Series rollout order.

Safe to run repeatedly (idempotent via update_or_create keyed on gw_sku).

Usage:
    python manage.py populate_warhammer_40k_books
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from prices.models import BookFormatPrice
from products.models import Category, Faction, Product, Retailer

_GW_CDN = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{}'

SOFTBACK = BookFormatPrice.FORMAT_SOFTBACK
HARDBACK = BookFormatPrice.FORMAT_HARDBACK

BOOKS = [
    {
        'sku': 'BOOK-40K-001', 'title': 'Above and Beyond', 'author': 'Denny Flowers',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836091622',
             'url': 'https://www.warhammer.com/en-US/shop/pb-above-and-beyond-eng-2025',
             'listing_title': 'Above and Beyond (Paperback)',
             'image': '60100181522_BLAboveAndBeyond2025.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-002', 'title': 'Aestred Thurga: Pyre of Faith', 'author': 'Danie Ware',
        'formats': [
            {'format': HARDBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836092988',
             'url': 'https://www.warhammer.com/en-US/shop/aestred-thurga-pyre-of-faith-hb-eng-2026',
             'listing_title': 'Aestred Thurga: Pyre of Faith (Hardback)',
             'image': '60040181436_BLAestredThurgaPyreOfFaith2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-003', 'title': 'Ahriman: The Omnibus', 'author': 'John French',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781784965099',
             'url': 'https://www.warhammer.com/en-US/shop/Ahriman-pb-en',
             'listing_title': 'Ahriman: The Omnibus (Paperback)',
             'image': '60100181432_AhrimanOmnibusBformat.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-004', 'title': 'Apostle', 'author': 'David Annandale',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836092452',
             'url': 'https://www.warhammer.com/en-US/shop/hb-apostle-eng-2026',
             'listing_title': 'Apostle (Hardback)',
             'image': '60040181424_BLApostole2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-005', 'title': 'Archmagos', 'author': 'Guy Haley',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836094012',
             'url': 'https://www.warhammer.com/en-US/shop/belisarius-cawl-archmagos-pb-eng-2026',
             'listing_title': 'Archmagos (Paperback)',
             'image': '60100181554_BLArchmagos2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-006', 'title': 'Armageddon: Season of Fire', 'author': 'Jude Reid',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836093800',
             'url': 'https://www.warhammer.com/en-US/shop/armageddon-season-of-fire-hb-eng-2026',
             'listing_title': 'Armageddon: Season of Fire (Hardback)',
             'image': '60040181455_ArmageddonSeasonofFireHBENG.jpg.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-007', 'title': 'Assassinorum: Kingmaker', 'author': 'Robert Rath',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781800262706',
             'url': 'https://www.warhammer.com/en-US/shop/assassinorum-kingmaker-pb-2023-eng',
             'listing_title': 'Assassinorum: Kingmaker (Paperback)',
             'image': '60100181813_AssassinorumKingmakerENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-008', 'title': 'Belisarius Cawl: The Great Work', 'author': 'Guy Haley',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781789990584',
             'url': 'https://www.warhammer.com/en-US/shop/Belisarius-Cawl-The-Great-Work-PB-2020',
             'listing_title': 'Belisarius Cawl: The Great Work (Paperback)',
             'image': '60100181739_ENGGreaterWorkBelisariusCawlBPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-009', 'title': 'Bjorn: The Fell-handed', 'author': 'Justin D. Hill',
        'formats': [
            {'format': HARDBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836094593',
             'url': 'https://www.warhammer.com/en-US/shop/bjorn-the-fell-handed-eng-hb-2026',
             'listing_title': 'Bjorn: The Fell-handed (Hardback)',
             'image': '60040181472_BLBjornTheFelHanded2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-010', 'title': 'Blackheart: Claws of the Maelstrom', 'author': 'Marc Collins',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836094647',
             'url': 'https://www.warhammer.com/en-US/shop/blackheart-claws-of-the-maelstrom-eng-hb-2026',
             'listing_title': 'Blackheart: Claws of the Maelstrom (Hardback)',
             'image': '60040181474_BLBlackheartClawsOfTheMaelstrom2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-011', 'title': 'Brutal Kunnin', 'author': 'Mike Brooks',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781789998269',
             'url': 'https://www.warhammer.com/en-US/shop/Brutal-Kunnin-PB-2021',
             'listing_title': 'Brutal Kunnin (Paperback)',
             'image': '60100181776_BrutalKunninENGBFormatPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-012', 'title': 'Carnage Unending', 'author': 'Various Authors',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836092964',
             'url': 'https://www.warhammer.com/en-US/shop/carnage-unending-pb-eng-2026',
             'listing_title': 'Carnage Unending (Paperback)',
             'image': '60100181541_BLCarnageUnending2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-013', 'title': 'Chem Dog', 'author': 'Callum Davis',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836092827',
             'url': 'https://www.warhammer.com/en-US/shop/chem-dog-hb-eng-2026',
             'listing_title': 'Chem Dog (Hardback)',
             'image': '60040181432_BLChemDog2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-014', 'title': 'Ciaphas Cain: Hero of the Imperium', 'author': 'Sandy Mitchell',
        'formats': [
            {'format': SOFTBACK, 'price': 18.00, 'in_stock': True, 'isbn': '9781849702706',
             'url': 'https://www.warhammer.com/en-US/shop/hero-of-the-imperium-pb',
             'listing_title': 'Ciaphas Cain: Hero of the Imperium (Paperback)',
             'image': '60100181201_CiaphasCainHerooftheImperiumENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-015', 'title': 'Ciaphas Cain: Vainglorious', 'author': 'Sandy Mitchell',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804073575',
             'url': 'https://www.warhammer.com/en-US/shop/ciaphas-cain-vainglorious-pb-eng-2024',
             'listing_title': 'Ciaphas Cain: Vainglorious (Paperback)',
             'image': '60100181189_BLVaingloriousENG01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-016', 'title': 'Cypher: Lord of the Fallen', 'author': 'John French',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781804077863',
             'url': 'https://www.warhammer.com/en-US/shop/cypher-lord-of-the-fallen-2024',
             'listing_title': 'Cypher: Lord of the Fallen (Paperback)',
             'image': '60100181016_BLCypherLordOfTheFallenENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-017', 'title': 'Da Big Dakka', 'author': 'Mike Brooks',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076620',
             'url': 'https://www.warhammer.com/en-US/shop/da-big-dakka-pb-eng-2024',
             'listing_title': 'Da Big Dakka (Paperback)',
             'image': '60100181364_DaBigDakkaENGPBNovel.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-018', 'title': 'Da Freebooterz Code', 'author': 'Justin Woolley',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '',
             'url': 'https://www.warhammer.com/en-US/shop/da-freebooterz-code-hb-2026',
             'listing_title': 'Da Freebooterz Code (Hardback)',
             'image': '60040181446_BLDaFreebooterzCode2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-019', 'title': 'Dark Imperium', 'author': 'Guy Haley',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781800261242',
             'url': 'https://www.warhammer.com/en-US/shop/dark-imperium-pb-eng-2022',
             'listing_title': 'Dark Imperium (Paperback)',
             'image': '60100181794_DarkImperiumReduxENGBPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-020', 'title': 'Dark Imperium: Godblight', 'author': 'Guy Haley',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781800262034',
             'url': 'https://www.warhammer.com/en-US/shop/dark-imperium-godblight-pb-2022-eng',
             'listing_title': 'Dark Imperium: Godblight (Paperback)',
             'image': '60100181799_DarkImperiumGodblightENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-021', 'title': 'Dark Imperium: Plague War', 'author': 'Guy Haley',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781800261235',
             'url': 'https://www.warhammer.com/en-US/shop/dark-imperium-plague-war-pb-eng-2022',
             'listing_title': 'Dark Imperium: Plague War (Paperback)',
             'image': '60100181798_DarkImperiumPlagueWarENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-022', 'title': 'Death Rider', 'author': 'Rhuairidh James',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836094807',
             'url': 'https://www.warhammer.com/en-US/shop/death-rider-hb-eng-2026',
             'listing_title': 'Death Rider (Hardback)',
             'image': '60040181428_BLDeathRider2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-023', 'title': 'Deathwatch', 'author': 'Steve Parker',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781789991246',
             'url': 'https://www.warhammer.com/en-US/shop/deathwatch-pb-eng-2026',
             'listing_title': 'Deathwatch (Paperback)',
             'image': '60100181722_BLDeathwatch2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-024', 'title': 'Demolisher', 'author': 'Andy Clark',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836094586',
             'url': 'https://www.warhammer.com/en-US/shop/demolisher-eng-pb-2026',
             'listing_title': 'Demolisher (Paperback)',
             'image': '60100181557_BLDemolisher2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-025', 'title': 'Dominion Genesis', 'author': 'Jonathan D. Beer',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836091493',
             'url': 'https://www.warhammer.com/en-US/shop/dominion-genesis-pb-eng-2025',
             'listing_title': 'Dominion Genesis (Paperback)',
             'image': '60100181518_BLDominionGenesis2025.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-026', 'title': 'Faith & Fire', 'author': 'James Swallow',
        'formats': [
            {'format': HARDBACK, 'price': 35.00, 'in_stock': True, 'isbn': '9781836092698',
             'url': 'https://www.warhammer.com/en-US/shop/faith-and-fire-20th-anniversary-edition-hb-eng-2026',
             'listing_title': 'Faith & Fire (Hardback)',
             'image': '60040181425_BLFaithAndFireRoyalHBAnniversaryEdition202601.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-027', 'title': 'Farsight: Blade of Truth', 'author': 'Phil Kelly',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836092032',
             'url': 'https://www.warhammer.com/en-US/shop/pb-farsight-blade-of-truth-eng-2026',
             'listing_title': 'Farsight: Blade of Truth (Paperback)',
             'image': '60100181535_BLFarsightBladeOfTruth2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-028', 'title': 'Fulgrim – The Perfect Son', 'author': 'Jude Reid',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836092049',
             'url': 'https://www.warhammer.com/en-US/shop/pb-fulgrim-the-perfect-son-eng-2026',
             'listing_title': 'Fulgrim – The Perfect Son (Paperback)',
             'image': '60100181536_BLFulgrimThePerfectSon2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-029', 'title': "Gaunt's Ghosts: The Founding", 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781784966171',
             'url': 'https://www.warhammer.com/en-US/shop/Gaunts-Ghosts-The-Founding-omnibus-1-2017',
             'listing_title': "Gaunt's Ghosts: The Founding (Paperback)",
             'image': '60100181462_FoundingOmnibusBFormatENGPB01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-030', 'title': "Gaunt's Ghosts: The Victory (Part Two)", 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 18.00, 'in_stock': True, 'isbn': '9781804070789',
             'url': 'https://www.warhammer.com/en-US/shop/gaunts-ghosts-the-victory-part-2-eng-pb-2022',
             'listing_title': "Gaunt's Ghosts: The Victory (Part Two) (Paperback)",
             'image': '60100181822_GGVictory2ENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-031', 'title': 'Genefather', 'author': 'Guy Haley',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804074930',
             'url': 'https://www.warhammer.com/en-US/shop/genefather-pb-eng-2024',
             'listing_title': 'Genefather (Paperback)',
             'image': '60100181352_GenefatherENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-032', 'title': 'Ghazghkull Thraka: Prophet of the Waaagh!', 'author': 'Nate Crowley',
        'formats': [
            {'format': SOFTBACK, 'price': 9.99, 'in_stock': True, 'isbn': '9781804076149',
             'url': 'https://www.warhammer.com/en-US/shop/ghazghkull-thraka-prophet-ot-waaagh-pb-2024',
             'listing_title': 'Ghazghkull Thraka: Prophet of the Waaagh! (Paperback)',
             'image': '60100181351_BLGhazghkullThrakaProphetOfTheWaaaghENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-033', 'title': 'Ghost Legion', 'author': 'Mike Brooks',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836094814',
             'url': 'https://www.warhammer.com/en-US/shop/ghost-legion-hb-eng-2026',
             'listing_title': 'Ghost Legion (Hardback)',
             'image': '60040181431_BLGhostLegion2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-034', 'title': 'Ghosts of Cadia', 'author': 'Rob Young',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836093893',
             'url': 'https://www.warhammer.com/en-US/shop/ghosts-of-cadia-hb-eng-2026',
             'listing_title': 'Ghosts of Cadia (Hardback)',
             'image': '60040181461_BLGhostOfCadia2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-035', 'title': 'Harrowmaster', 'author': 'Mike Brooks',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804073322',
             'url': 'https://www.warhammer.com/en-US/shop/renegades-harrowmaster-pb-eng-2023',
             'listing_title': 'Harrowmaster (Paperback)',
             'image': '60100181834_BLRenegadesHarrowmasterENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-036', 'title': 'Huron Blackheart: Master of the Maelstrom', 'author': 'Mike Brooks',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836092728',
             'url': 'https://www.warhammer.com/en-US/shop/huron-blackheart-master-of-the-maelstrom-pb-eng-2026',
             'listing_title': 'Huron Blackheart: Master of the Maelstrom (Paperback)',
             'image': '60100181539_BLHuronBlackheartMasterOfTheMaelstrom2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-037', 'title': 'Interceptor City', 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 19.99, 'in_stock': True, 'isbn': '9781836091981',
             'url': 'https://www.warhammer.com/en-US/shop/pb-interceptor-city-eng-2025',
             'listing_title': 'Interceptor City (Paperback)',
             'image': '60100181533_BLInterceptorCity2025.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-038', 'title': 'Krakenblood', 'author': 'Marc Collins',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093763',
             'url': 'https://www.warhammer.com/en-US/shop/krakenblood-pb-eng-2026',
             'listing_title': 'Krakenblood (Paperback)',
             'image': '60100181549_BLKrakenblood2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-039', 'title': 'Krieg', 'author': 'Steve Lyons',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781800262041',
             'url': 'https://www.warhammer.com/en-US/shop/krieg-pb-eng-2022',
             'listing_title': 'Krieg (Paperback)',
             'image': '60100181805_KriegENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-040', 'title': "Lazarus: Enmity's Edge", 'author': 'Gary Kloster',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076682',
             'url': 'https://www.warhammer.com/en-US/shop/lazarus-enmitys-edge-pb-eng-2024',
             'listing_title': "Lazarus: Enmity's Edge (Paperback)",
             'image': '60100181366_BLLazarusEnmitysEdgeEng.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-041', 'title': 'Legends of the Waaagh!', 'author': 'Various Authors',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836093046',
             'url': 'https://www.warhammer.com/en-US/shop/legends-of-the-waaagh-pb-2026',
             'listing_title': 'Legends of the Waaagh! (Paperback)',
             'image': '60100181543_BLLegendsOfTheWaaagh2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-042', 'title': 'Legends of the Wolf: The Omnibus', 'author': 'Chris Wraight',
        'formats': [
            {'format': SOFTBACK, 'price': 25.00, 'in_stock': True, 'isbn': '9781804077283',
             'url': 'https://www.warhammer.com/en-US/shop/pb-legends-of-the-wolf-the-omnibus-eng-2025',
             'listing_title': 'Legends of the Wolf: The Omnibus (Paperback)',
             'image': '60100181515_BLLegendsOfTheWolf01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-043', 'title': 'Leviathan', 'author': 'Darius Hinks',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804073872',
             'url': 'https://www.warhammer.com/en-US/shop/leviathan-pb-eng-2023',
             'listing_title': 'Leviathan (Paperback)',
             'image': '60100181141_BLLeviathanBPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-044', 'title': 'Longshot', 'author': 'Rob Young',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836093862',
             'url': 'https://www.warhammer.com/en-US/shop/longshot-hb-eng-2026',
             'listing_title': 'Longshot (Hardback)',
             'image': '60040181463_BLLongshot2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-045', 'title': 'Minka Lesk: The Last Whiteshield', 'author': 'Justin D. Hill',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781804073001',
             'url': 'https://www.warhammer.com/en-US/shop/minka-lesk-the-last-whiteshield-omnibus-pb-eng-2023',
             'listing_title': 'Minka Lesk: The Last Whiteshield (Paperback)',
             'image': '60100181839_BLLastWhiteshieldENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-046', 'title': 'Morvenn Vahl: Spear of Faith', 'author': 'Jude Reid',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076699',
             'url': 'https://www.warhammer.com/en-US/shop/morvenn-vahl-spear-of-faith-pb-eng-2025',
             'listing_title': 'Morvenn Vahl: Spear of Faith (Paperback)',
             'image': '60100181519_MorvennVahlSpearofFaithBformatPBENGNovel1.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-047', 'title': 'Night Lords: The Omnibus', 'author': 'Aaron Dembski-Bowden',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781849706124',
             'url': 'https://www.warhammer.com/en-US/shop/Night-Lords-The-Omnibus-Paperback',
             'listing_title': 'Night Lords: The Omnibus (Paperback)',
             'image': '60100181272_NightLordsOmnibusENG2024.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-048', 'title': 'Once a Killer', 'author': 'Various Authors',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804073278',
             'url': 'https://www.warhammer.com/en-US/shop/once-a-killer-anthology-pb-eng-2023',
             'listing_title': 'Once a Killer (Paperback)',
             'image': '60100181845_BLOnceAKillerENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-049', 'title': 'Paragon of Faith and Other Stories', 'author': 'Various Authors',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '',
             'url': 'https://www.warhammer.com/en-US/shop/paragon-of-faith-and-other-stories-pb-eng-2026',
             'listing_title': 'Paragon of Faith and Other Stories (Paperback)',
             'image': '60100181542_BLParagonOfFaithAndOtherStories2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-050', 'title': 'Ravenor: The Omnibus', 'author': 'Dan Abnett',
        'formats': [
            {'format': SOFTBACK, 'price': 25.00, 'in_stock': True, 'isbn': '9781836090915',
             'url': 'https://www.warhammer.com/en-US/shop/pb-ravenor-the-omnibus-eng-2025',
             'listing_title': 'Ravenor: The Omnibus (Paperback)',
             'image': '60100181511_BLRavenorTheOmnibus2025.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-051', 'title': 'Shadow of the Eighth', 'author': 'Justin D. Hill',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804073612',
             'url': 'https://www.warhammer.com/en-US/shop/shadow-of-the-eighth-pb-2024',
             'listing_title': 'Shadow of the Eighth (Paperback)',
             'image': '60100181178_BLShadowOfTheEighthENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-052', 'title': 'Siege of Vraks', 'author': 'Steve Lyons',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076941',
             'url': 'https://www.warhammer.com/en-US/shop/siege-of-vraks-pb-eng-2025',
             'listing_title': 'Siege of Vraks (Paperback)',
             'image': '60100181509_BLSiegeOfVraksENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-053', 'title': 'The Dark Coil: Damnation', 'author': 'Peter Fehervari',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836090007',
             'url': 'https://www.warhammer.com/en-US/shop/the-dark-coil-damnation-pb-eng-2025',
             'listing_title': 'The Dark Coil: Damnation (Paperback)',
             'image': '60100181482_BLTheDarkCoilDamnationENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-054', 'title': 'The Devastation of Baal', 'author': 'Guy Haley',
        'formats': [
            {'format': HARDBACK, 'price': 35.00, 'in_stock': True, 'isbn': '9781836093879',
             'url': 'https://www.warhammer.com/en-US/shop/the-devastation-of-baal-hb-eng-2026',
             'listing_title': 'The Devastation of Baal (Hardback)',
             'image': '60040181458_BLDevastationOfBaal2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-055', 'title': 'The Fall of Cadia', 'author': 'Robert Rath',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804076392',
             'url': 'https://www.warhammer.com/en-US/shop/the-fall-of-cadia-pb-eng-2024',
             'listing_title': 'The Fall of Cadia (Paperback)',
             'image': '60100181354_FallofCadiaENGPB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-056', 'title': 'The Green Tide', 'author': 'Various Authors',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836092865',
             'url': 'https://www.warhammer.com/en-US/shop/the-green-tide-omnibus-pb-eng-2026',
             'listing_title': 'The Green Tide (Paperback)',
             'image': '60100181540_BLTheGreenTide2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-057', 'title': "The High Kâhl's Oath", 'author': 'Gav Thorpe',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836091646',
             'url': 'https://www.warhammer.com/en-US/shop/pb-the-high-kahls-oath-eng-2025',
             'listing_title': "The High Kâhl's Oath (Paperback)",
             'image': '60100181524_BLHighKahlsOath2025.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-058', 'title': 'The Infinite and the Divine', 'author': 'Robert Rath',
        'formats': [
            {'format': HARDBACK, 'price': 35.00, 'in_stock': True, 'isbn': '9781789991642',
             'url': 'https://www.warhammer.com/en-US/shop/the-infinite-and-the-divine-hb-eng-2026',
             'listing_title': 'The Infinite and the Divine (Hardback)',
             'image': '60040181504_BLTheInfiniteandTheDivine2026.jpg'},
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781789998320',
             'url': 'https://www.warhammer.com/en-US/shop/The-Infinite-And-The-Divine-pb-2021',
             'listing_title': 'The Infinite and the Divine (Paperback)',
             'image': '60100181775_InfiniteDivineENGPBNovel.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-059', 'title': 'The Lion: Son of the Forest', 'author': 'Mike Brooks',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804073568',
             'url': 'https://www.warhammer.com/en-US/shop/the-lion-son-of-the-forest-pb-eng-2023',
             'listing_title': 'The Lion: Son of the Forest (Paperback)',
             'image': '60100181507_BLLionSonOfTheForestENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-060', 'title': 'The Macharian Crusade: Angel of Fire', 'author': 'William King',
        'formats': [
            {'format': SOFTBACK, 'price': 16.00, 'in_stock': True, 'isbn': '9781849703994',
             'url': 'https://www.warhammer.com/en-US/shop/the-macharian-crusade-angel-of-fire-pb-readers-choice-2023-eng',
             'listing_title': 'The Macharian Crusade: Angel of Fire (Paperback)',
             'image': '60100181222_BLAngelOfFireReadersChoicePB.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-061', 'title': 'The Relentless Dead', 'author': 'Steve Lyons',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093961',
             'url': 'https://www.warhammer.com/en-US/shop/the-relentless-dead-pb-eng-2026',
             'listing_title': 'The Relentless Dead (Paperback)',
             'image': '60100181556_BLRelentlessDead2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-062', 'title': 'The Remnant Blade', 'author': 'Mike Vincent',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093794',
             'url': 'https://www.warhammer.com/en-US/shop/the-remnant-blade-pb-eng-2026',
             'listing_title': 'The Remnant Blade (Paperback)',
             'image': '60100181551_RemnantBladeBFormatPBENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-063', 'title': 'The Twice-Dead King: Omnibus', 'author': 'Nate Crowley',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781804076965',
             'url': 'https://www.warhammer.com/en-US/shop/pb-the-twice-dead-king-the-omnibus-2025',
             'listing_title': 'The Twice-Dead King: Omnibus (Paperback)',
             'image': '60100181510_BLTwiceDeadKing01.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-064', 'title': 'The Wicked and the Warped', 'author': 'Robert Rath',
        'formats': [
            {'format': HARDBACK, 'price': 35.00, 'in_stock': True, 'isbn': '9781804073209',
             'url': 'https://www.warhammer.com/en-US/shop/the-wicked-and-the-warped-hb-eng-2026',
             'listing_title': 'The Wicked and the Warped (Hardback)',
             'image': '60040181452_BLTheWickedandtheWarped2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-065', 'title': 'Tomb World', 'author': 'Jonathan D. Beer',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093787',
             'url': 'https://www.warhammer.com/en-US/shop/tomb-world-pb-eng-2026',
             'listing_title': 'Tomb World (Paperback)',
             'image': '60100181552_TombWorldBFormatPBENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-066', 'title': 'Vagabond Squadron', 'author': 'Robbie MacNiven',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093954',
             'url': 'https://www.warhammer.com/en-US/shop/vagabond-squadron-pb-eng-2026',
             'listing_title': 'Vagabond Squadron (Paperback)',
             'image': '60100181553_BLVagabondSquadron2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-067', 'title': 'Vaults of Terra: The Omnibus', 'author': 'Chris Wraight',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781836092438',
             'url': 'https://www.warhammer.com/en-US/shop/pb-vaults-of-terra-omnibus-eng-2025',
             'listing_title': 'Vaults of Terra: The Omnibus (Paperback)',
             'image': '60100181534_BLVaultsOfTerraTheOmnibus2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-068', 'title': 'Veterans of the Fall', 'author': 'William Crowe',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093053',
             'url': 'https://www.warhammer.com/en-US/shop/veterans-of-the-fall-pb-2026',
             'listing_title': 'Veterans of the Fall (Paperback)',
             'image': '60100181545_BLVeteransOfTheFall2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-069', 'title': 'Voice of Command', 'author': 'Richard Swan',
        'formats': [
            {'format': HARDBACK, 'price': 30.00, 'in_stock': True, 'isbn': '9781836094555',
             'url': 'https://www.warhammer.com/en-US/shop/voice-of-command-eng-hb-2026',
             'listing_title': 'Voice of Command (Hardback)',
             'image': '60040181469_BLVoiceOfCommand2026.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-070', 'title': 'Voidscarred', 'author': 'Mike Brooks',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781836093640',
             'url': 'https://www.warhammer.com/en-US/shop/voidscarred-pb-eng-2026',
             'listing_title': 'Voidscarred (Paperback)',
             'image': '60100181548_VoidscarredBFormatPBENG.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-071', 'title': 'Warboss', 'author': 'Mike Brooks',
        'formats': [
            {'format': SOFTBACK, 'price': 17.99, 'in_stock': True, 'isbn': '9781804073452',
             'url': 'https://www.warhammer.com/en-US/shop/warboss-pb-eng-2023',
             'listing_title': 'Warboss (Paperback)',
             'image': '60100181175_BLWarboss.jpg'},
        ],
    },
    {
        'sku': 'BOOK-40K-072', 'title': 'Yarrick: The Omnibus', 'author': 'David Annandale',
        'formats': [
            {'format': SOFTBACK, 'price': 21.00, 'in_stock': True, 'isbn': '9781804075401',
             'url': 'https://www.warhammer.com/en-US/shop/yarrick-the-omnibus-pb-2026',
             'listing_title': 'Yarrick: The Omnibus (Paperback)',
             'image': '60100181550_BLYarrickTheOmnibus2026.jpg'},
        ],
    },
]


class Command(BaseCommand):
    """Create the Warhammer 40,000 Books batch and seed GW format prices."""

    help = (
        'Populates the Warhammer 40,000 Books product batch under the '
        'Warhammer (Books and Novels) category, with Softback/Hardback '
        'BookFormatPrice rows sourced from Games Workshop. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category = Category.objects.get(slug='warhammer', parent_category__slug='books-and-novels')
        except Category.DoesNotExist:
            raise CommandError(
                "Category 'Warhammer' (under 'Books and Novels') not found. "
                "It must already exist -- this command does not create categories."
            )

        try:
            faction = Faction.objects.get(slug='warhammer-40000-books')
        except Faction.DoesNotExist:
            raise CommandError(
                "Faction 'Warhammer 40,000 Books' not found. "
                "It must already exist -- this command does not create factions."
            )

        gw_retailer = Retailer.objects.filter(name='Games Workshop').filter(is_uk=False).first()
        if not gw_retailer:
            raise CommandError('Games Workshop (US) retailer not found.')

        prod_created = prod_updated = 0
        price_created = price_updated = 0

        for book in BOOKS:
            slug = slugify(book['title'])
            primary_image = _GW_CDN.format(book['formats'][0]['image'])

            product, created = Product.objects.update_or_create(
                gw_sku=book['sku'],
                defaults={
                    'name': book['title'],
                    'slug': slug,
                    'author': book['author'],
                    'category': category,
                    'faction': faction,
                    'image_url': primary_image,
                    'is_active': True,
                    'batch_tag': 'warhammer-40k-books',
                },
            )
            if created:
                prod_created += 1
            else:
                prod_updated += 1

            for fmt in book['formats']:
                _, p_created = BookFormatPrice.objects.update_or_create(
                    product=product,
                    retailer=gw_retailer,
                    format=fmt['format'],
                    defaults={
                        'price': fmt['price'],
                        'currency': 'USD',
                        'url': fmt['url'],
                        'listing_title': fmt['listing_title'],
                        'in_stock': fmt['in_stock'],
                        'not_available': False,
                        'is_msrp_source': True,
                        'isbn': fmt['isbn'],
                    },
                )
                if p_created:
                    price_created += 1
                else:
                    price_updated += 1

            self.stdout.write(
                f"  {'Created' if created else 'Updated'}: {book['title']} [{book['sku']}] "
                f"({', '.join(f['format'] for f in book['formats'])})"
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Products: {prod_created} created, {prod_updated} updated. '
            f'BookFormatPrice rows: {price_created} created, {price_updated} updated.'
        ))
