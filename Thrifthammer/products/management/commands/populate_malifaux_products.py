"""
Management command: populate_malifaux_products

Creates the Malifaux product line as a new top-level Category (standalone
wargame published by Wyrd Games, not a Games Workshop product -- no GW
retailer row). MSRP/images/URLs come from Wyrd's own store.

product.gw_url is populated with the Wyrd store product URL (not a real GW
link) -- this enables the "View" button on the product detail page.
product_detail.html shows "View on Wyrd Games" instead of "View on GW" for
this category specifically.

Usage:
    python manage.py populate_malifaux_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

# (slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('malifaux-fourth-edition-two-player-starter', 'MAL-001', 'Malifaux Fourth Edition - Two Player Starter', decimal.Decimal('120'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24901_M4E-Starter-Box_FRONT.png?v=1753660314&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-two-player-starter', 'Malifaux Fourth Edition - Two Player Starter'),
    ('malifaux-fourth-edition-gaining-grounds-season-zero', 'MAL-002', 'Malifaux Fourth Edition - Gaining Grounds Season Zero', decimal.Decimal('11.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR34010_Gaining-Grounds-Zero.webp?v=1753660572&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-gaining-grounds-season-zero', 'Malifaux Fourth Edition - Gaining Grounds Season Zero'),
    ('malifaux-fourth-edition-rules-manual', 'MAL-003', 'Malifaux Fourth Edition Rules Manual', decimal.Decimal('15'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24009_Malifaux-Fourth-Edition-Rules-Manual.png?v=1753661076&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-rules-manual', 'Malifaux Fourth Edition Rules Manual'),
    ('malifaux-fourth-edition-pandora-despairs-desire', 'MAL-004', "Malifaux Fourth Edition: Pandora, Despair's Desire", decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24401_Pandora-Despairs-Desire_Front.png?v=1753709105&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-pandora-despairs-desire', "Malifaux Fourth Edition: Pandora, Despair's Desire"),
    ('malifaux-fourth-edition-seamus-the-last-breath', 'MAL-005', 'Malifaux Fourth Edition: Seamus, The Last Breath', decimal.Decimal('57.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24201_Seamus-Last-Breath_Front.png?v=1753665041&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-seamus-the-last-breath', 'Malifaux Fourth Edition: Seamus, The Last Breath'),
    ('malifaux-fourth-edition-sandeep-desai-the-quiet-flame', 'MAL-006', 'Malifaux Fourth Edition: Sandeep Desai, The Quiet Flame', decimal.Decimal('57.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24303_Sandeep-Quiet-Flame_Front.png?v=1753709835&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-sandeep-desai-the-quiet-flame', 'Malifaux Fourth Edition: Sandeep Desai, The Quiet Flame'),
    ('malifaux-fourth-edition-yan-lo-the-spirit-walker', 'MAL-007', 'Malifaux Fourth Edition: Yan Lo, The Spirit Walker', decimal.Decimal('57.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24208_Yan-Lo-Spirit-Walker_Front.png?v=1753712352&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-yan-lo-the-spirit-walker', 'Malifaux Fourth Edition: Yan Lo, The Spirit Walker'),
    ('malifaux-fourth-edition-wong-the-wonderful', 'MAL-008', 'Malifaux Fourth Edition: Wong, The Wonderful', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24609_Wong-The-Wonderful_Front.png?v=1753711128&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-wong-the-wonderful', 'Malifaux Fourth Edition: Wong, The Wonderful'),
    ('malifaux-fourth-edition-pandora-tyrant-torn', 'MAL-009', 'Malifaux Fourth Edition: Pandora, Tyrant-Torn', decimal.Decimal('57.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24402_Pandora-Tyrant-Torn_Front.png?v=1753710839&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-pandora-tyrant-torn', 'Malifaux Fourth Edition: Pandora, Tyrant-Torn'),
    ('malifaux-fourth-edition-the-dreamer-fast-asleep', 'MAL-010', 'Malifaux Fourth Edition: The Dreamer, Fast Asleep', decimal.Decimal('62.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24403_Dreamer-Fast-Asleep_Front.png?v=1753710467&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-the-dreamer-fast-asleep', 'Malifaux Fourth Edition: The Dreamer, Fast Asleep'),
    ('malifaux-fourth-edition-anya-lycarayen-the-resolute', 'MAL-011', 'Malifaux Fourth Edition: Anya Lycarayen, The Resolute', decimal.Decimal('57.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24803_Anya-The-Resolute_Front.png?v=1753710272&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-anya-lycarayen-the-resolute', 'Malifaux Fourth Edition: Anya Lycarayen, The Resolute'),
    ('malifaux-fourth-edition-viktoria-chambers-ashes-and-blood', 'MAL-012', 'Malifaux Fourth Edition: Viktoria Chambers, Ashes and Blood', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24501_Viktoria-Ashes-and-Blood_Front.png?v=1753710080&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-viktoria-chambers-ashes-and-blood', 'Malifaux Fourth Edition: Viktoria Chambers, Ashes and Blood'),
    ('malifaux-fourth-edition-the-clampetts-fisherfolk', 'MAL-013', 'Malifaux Fourth Edition: The Clampetts, Fisherfolk', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24605_Clampetts-Fisherfolk_Front.png?v=1753709637&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-the-clampetts-fisherfolk', 'Malifaux Fourth Edition: The Clampetts, Fisherfolk'),
    ('malifaux-fourth-edition-dr-mcmourning-malpractitioner', 'MAL-014', 'Malifaux Fourth Edition: Dr. McMourning, Malpractitioner', decimal.Decimal('57.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24203_McMourning-Malpractitioner_Front_601f2123-8744-4d60-b8eb-21ed58fd38e8.png?v=1753708643&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-dr-mcmourning-malpractitioner', 'Malifaux Fourth Edition: Dr. McMourning, Malpractitioner'),
    ('malifaux-fourth-edition-dr-mcmourning-insanitary', 'MAL-015', 'Malifaux Fourth Edition: Dr. McMourning, Insanitary', decimal.Decimal('62.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24204_McMourning-Insanitary_Front.png?v=1753667513&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-dr-mcmourning-insanitary', 'Malifaux Fourth Edition: Dr. McMourning, Insanitary'),
    ('malifaux-fourth-edition-seamus-aka-sebastian-baker', 'MAL-016', 'Malifaux Fourth Edition: Seamus, AKA Sebastian Baker', decimal.Decimal('57.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24202_Seamus-Sebastian-Baker_Front_3f2871ce-6c88-47c6-84e1-19690f27c970.png?v=1753666819&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-seamus-aka-sebastian-baker', 'Malifaux Fourth Edition: Seamus, AKA Sebastian Baker'),
    ('malifaux-fourth-edition-jack-daw-spirit-of-betrayal', 'MAL-017', 'Malifaux Fourth Edition: Jack Daw, Spirit of Betrayal', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24205_Jack-Daw-Spirit-of-Betrayal_Front.png?v=1753664507&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-jack-daw-spirit-of-betrayal', 'Malifaux Fourth Edition: Jack Daw, Spirit of Betrayal'),
    ('malifaux-fourth-edition-nellie-voice-of-disorder', 'MAL-018', 'Malifaux Fourth Edition: Nellie, Voice of Disorder', decimal.Decimal('62.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24106_Nellie-Voice-of-Disorder_Front.png?v=1753664595&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-nellie-cochrane-voice-of-disorder', 'Malifaux Fourth Edition: Nellie, Voice of Disorder'),
    ('malifaux-fourth-edition-lucius-mattheson-in-plain-sight', 'MAL-019', 'Malifaux Fourth Edition: Lucius Mattheson, In Plain Sight', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24101_Lucius-In-Plain-Sight_Front.png?v=1761944525&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-lucius-mattheson-in-plain-sight', 'Malifaux 4th Edition: Lucius Mattheson, In Plain Sight'),
    ('malifaux-fourth-edition-guild-faction-pack', 'MAL-020', 'Malifaux Fourth Edition: Guild Faction Pack', decimal.Decimal('25'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24011_M4E-Faction-Pack-Guild_Front.png?v=1764114941&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-guild-faction-pack', 'Malifaux Fourth Edition: Guild Faction Pack'),
    ('malifaux-fourth-edition-arcanist-faction-pack', 'MAL-021', 'Malifaux Fourth Edition: Arcanist Faction Pack', decimal.Decimal('25'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24013_M4E-Faction-Pack-Arcanists_Front.png?v=1764115216&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-arcanist-faction-pack', 'Malifaux Fourth Edition: Arcanist Faction Pack'),
    ('malifaux-fourth-edition-resurrectionist-faction-pack', 'MAL-022', 'Malifaux Fourth Edition: Resurrectionist Faction Pack', decimal.Decimal('25'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24012_M4E-Faction-Pack-Resurrectionists_Front.png?v=1764115465&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-resurrectionist-faction-pack', 'Malifaux Fourth Edition: Resurrectionist Faction Pack'),
    ('malifaux-fourth-edition-neverborn-faction-pack', 'MAL-023', 'Malifaux Fourth Edition: Neverborn Faction Pack', decimal.Decimal('25'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24014_M4E-Faction-Pack-Neverborn_Front.png?v=1764115735&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-neverborn-faction-pack', 'Malifaux Fourth Edition: Neverborn Faction Pack'),
    ('malifaux-fourth-edition-ten-thunders-faction-pack', 'MAL-024', 'Malifaux Fourth Edition: Ten Thunders Faction Pack', decimal.Decimal('25'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24017_M4E-Faction-Pack-Ten-Thunders_Front.png?v=1764116049&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-ten-thunders-faction-pack', 'Malifaux Fourth Edition: Ten Thunders Faction Pack'),
    ('malifaux-fourth-edition-outcast-faction-pack', 'MAL-025', 'Malifaux Fourth Edition: Outcast Faction Pack', decimal.Decimal('25'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24015_M4E-Faction-Pack-Outcasts_Front.png?v=1764116185&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-outcast-faction-pack', 'Malifaux Fourth Edition: Outcast Faction Pack'),
    ('malifaux-fourth-edition-bayou-faction-pack', 'MAL-026', 'Malifaux Fourth Edition: Bayou Faction Pack', decimal.Decimal('25'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24016_M4E-Faction-Pack-Bayou_Front.png?v=1764116340&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-bayou-faction-pack', 'Malifaux Fourth Edition: Bayou Faction Pack'),
    ('malifaux-fourth-edition-explorers-society-faction-pack', 'MAL-027', 'Malifaux Fourth Edition: Explorer’s Society Faction Pack', decimal.Decimal('25'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24018_M4E-Faction-Pack-Explorers_Front.png?v=1764116465&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-explorer-s-society-faction-pack', 'Malifaux Fourth Edition: Explorer’s Society Faction Pack'),
    ('malifaux-fourth-edition-guild-faction-book', 'MAL-028', 'Malifaux Fourth Edition: Guild Faction Book', decimal.Decimal('28'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Malifaux-Faction-Book_Guild.png?v=1764117699&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-guild-faction-book', 'Malifaux Fourth Edition: Guild Faction Book'),
    ('malifaux-fourth-edition-resurrectionist-faction-book', 'MAL-029', 'Malifaux Fourth Edition: Resurrectionist Faction Book', decimal.Decimal('28'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Malifaux-Faction-Book_Resurrectionists.png?v=1764118129&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-resurrectionist-faction-book', 'Malifaux Fourth Edition: Resurrectionist Faction Book'),
    ('malifaux-fourth-edition-arcanist-faction-book', 'MAL-030', 'Malifaux Fourth Edition: Arcanist Faction Book', decimal.Decimal('28'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Malifaux-Faction-Book_Arcanists.png?v=1764118289&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-arcanist-faction-book', 'Malifaux Fourth Edition: Arcanist Faction Book'),
    ('malifaux-fourth-edition-neverborn-faction-book', 'MAL-031', 'Malifaux Fourth Edition: Neverborn Faction Book', decimal.Decimal('28'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Malifaux-Faction-Book_Neverborn.png?v=1764118747&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-neverborn-faction-book', 'Malifaux Fourth Edition: Neverborn Faction Book'),
    ('malifaux-fourth-edition-ten-thunders-faction-book', 'MAL-032', 'Malifaux Fourth Edition: Ten Thunders Faction Book', decimal.Decimal('28'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Malifaux-Faction-Book_Ten-Thunders.png?v=1764118899&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-ten-thunders-faction-book', 'Malifaux Fourth Edition: Ten Thunders Faction Book'),
    ('malifaux-fourth-edition-outcast-faction-book', 'MAL-033', 'Malifaux Fourth Edition: Outcast Faction Book', decimal.Decimal('28'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Malifaux-Faction-Book_Outcasts.png?v=1764119011&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-outcast-faction-book', 'Malifaux Fourth Edition: Outcast Faction Book'),
    ('malifaux-fourth-edition-bayou-faction-book', 'MAL-034', 'Malifaux Fourth Edition: Bayou Faction Book', decimal.Decimal('28'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Malifaux-Faction-Book_Bayou.png?v=1764119142&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-bayou-faction-book', 'Malifaux Fourth Edition: Bayou Faction Book'),
    ('malifaux-fourth-edition-explorers-society-faction-book', 'MAL-035', 'Malifaux Fourth Edition: Explorer’s Society Faction Book', decimal.Decimal('28'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Malifaux-Faction-Book_Explorers-Society_cb807348-ff16-40b7-b97c-08297e580ddb.png?v=1764119381&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-explorer-s-society-faction-book', 'Malifaux Fourth Edition: Explorer’s Society Faction Book'),
    ('malifaux-fourth-edition-tara-voidcaller', 'MAL-036', 'Malifaux Fourth Edition: Tara, Voidcaller', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24503_Tara-Voidcaller_Front.png?v=1764121721&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/tara-voidcaller', 'Malifaux Fourth Edition: Tara, Voidcaller'),
    ('malifaux-fourth-edition-nexus-heart-of-the-hive', 'MAL-037', 'Malifaux Fourth Edition: Nexus, Heart of the Hive', decimal.Decimal('57.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24807_Nexus-Heart-Hive_Front.png?v=1764122066&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/nexus-heart-of-the-hive', 'Malifaux Fourth Edition: Nexus, Heart of the Hive'),
    ('iconic-haunted-harmony-molly-and-kirai', 'MAL-038', 'Iconic - Haunted Harmony - Molly and Kirai', decimal.Decimal('65'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR19017_Haunted-Harmony_Front.png?v=1764122142&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/iconic-haunted-harmony-molly-and-kirai', 'Iconic - Haunted Harmony - Molly and Kirai'),
    ('malifaux-fourth-edition-colette-du-bois-star-of-the-show', 'MAL-039', 'Malifaux Fourth Edition: Colette Du Bois, Star of the Show', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24305_Colette-Star-of-the-Show_Front.png?v=1764123159&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-colette-du-bois-star-of-the-show', 'Malifaux Fourth Edition: Colette Du Bois, Star of the Show'),
    ('malifaux-fourth-edition-jakob-lynch-wild-card', 'MAL-040', 'Malifaux Fourth Edition: Jakob Lynch, Wild Card', decimal.Decimal('62.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24703_Lynch-Wild-Card_Front.png?v=1764123999&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-jakob-lynch-wild-card', 'Wyrd Malifaux Fourth Edition Jakob Lynch, Wild Card'),
    ('malifaux-fourth-edition-tara-timeless', 'MAL-041', 'Malifaux Fourth Edition: Tara, Timeless', decimal.Decimal('60'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24504_Tara-Timeless_Front.png?v=1770324536&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-tara-timeless', 'Malifaux 4th Edition: Tara, Timeless'),
    ('malifaux-fourth-edition-sonnia-criid-unrelenting', 'MAL-042', 'Malifaux Fourth Edition: Sonnia Criid, Unrelenting', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24103_Sonnia-Unrelenting_Front.png?v=1770324841&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-sonnia-criid-unrelenting', 'Malifaux Fourth Edition: Sonnia Criid, Unrelenting'),
    ('malifaux-fourth-edition-sandeep-desai-font-of-magic', 'MAL-043', 'Malifaux Fourth Edition: Sandeep Desai, Font of Magic', decimal.Decimal('72.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24304_Sandeep-Font-of-Magic_Front.png?v=1770325408&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-sandeep-desai-font-of-magic', 'Malifaux Fourth Edition: Sandeep Desai, Font of Magic'),
    ('malifaux-fourth-edition-dashel-barker-the-old-guard', 'MAL-044', 'Malifaux Fourth Edition: Dashel Barker, The Old Guard', decimal.Decimal('60'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24109_Dashel-Barker-The-Old-Guard_Front.png?v=1776894523&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-dashel-barker-the-old-guard', 'Malifaux Fourth Edition: Dashel Barker, The Old Guard'),
    ('malifaux-fourth-edition-viktoria-chambers-twin-blades', 'MAL-045', 'Malifaux Fourth Edition: Viktoria Chambers, Twin Blades', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24502_Viktoria-Twin-Blades_Front.png?v=1776894705&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-viktoria-chambers-twin-blades', 'Wyrd Malifaux Fourth Edition: Viktoria Chambers, Twin Blades'),
    ('malifaux-fourth-edition-intrepid-fate', 'MAL-046', 'Malifaux Fourth Edition: Intrepid Fate', decimal.Decimal('42.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24813_Intrepid-Fate_Front.png?v=1776895022&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-intrepid-fate', 'Malifaux Fourth Edition: Intrepid Fate'),
    ('malifaux-fourth-edition-the-clampetts-bally-hoo-bucket', 'MAL-047', 'Malifaux Fourth Edition: The Clampetts, Bally-Hoo Bucket', decimal.Decimal('75'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24606_Clampetts-Bally-Hoo-Bucket_Front.png?v=1776895236&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-the-clampetts-bally-hoo-bucket', 'Malifaux Fourth Edition: The Clampetts, Bally-Hoo Bucket'),
    ('malifaux-fourth-edition-carrion-fate', 'MAL-048', 'Malifaux Fourth Edition: Carrion Fate', decimal.Decimal('42.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24213_Carrion-Fate_Front.png?v=1776895384&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-carrion-fate', 'Malifaux Fourth Edition: Carrion Fate'),
    ('malifaux-fourth-edition-arcane-fate', 'MAL-049', 'Malifaux Fourth Edition: Arcane Fate', decimal.Decimal('42.5'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24313_Arcane-Fate_Front.png?v=1776895581&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-arcane-fate', 'Malifaux Fourth Edition: Arcane Fate'),
    ('malifaux-fourth-edition-damian-ravencroft-aspirant', 'MAL-050', 'Malifaux Fourth Edition: Damian Ravencroft, Aspirant', decimal.Decimal('55'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/WYR24307_Ravencroft-Aspirant_Front.png?v=1781281454&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/damian-ravencroft-aspirant', 'Malifaux Fourth Edition: Damian Ravencroft, Aspirant'),
    ('malifaux-fourth-edition-index-of-the-untold-campaign-book', 'MAL-051', 'Malifaux Fourth Edition: Index of the Untold Campaign Book', decimal.Decimal('30'), 'https://giveusyourmoneypleasethankyou-wyrd.com/cdn/shop/files/Wyrd_M4E-Index-of-the-Untold.jpg?v=1781730281&width=1445', 'https://giveusyourmoneypleasethankyou-wyrd.com/collections/malifaux-fourth-edition/products/malifaux-fourth-edition-index-of-the-untold-campaign-book', 'Malifaux Fourth Edition: Index of the Untold Campaign Book'),
]


class Command(BaseCommand):
    """Populate the Malifaux product line (idempotent)."""

    help = 'Populates Malifaux products (MAL-001 to MAL-051).'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='malifaux',
            defaults={'name': 'Malifaux'},
        )

        wyrd_games, _ = Retailer.objects.get_or_create(
            slug='wyrd-games',
            defaults={
                'name': 'Wyrd Games',
                'website': 'https://giveusyourmoneypleasethankyou-wyrd.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        products_created = 0
        products_updated = 0
        wyrd_prices_created = 0
        wyrd_prices_updated = 0

        for slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': product_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'malifaux',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, wyrd_price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=wyrd_games,
                defaults={
                    'price': msrp,
                    'url': product_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if wyrd_price_created:
                wyrd_prices_created += 1
            else:
                wyrd_prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Wyrd Games prices: {wyrd_prices_created} created, {wyrd_prices_updated} updated.'
        ))
