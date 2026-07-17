"""
Management command: populate_marvel_crisis_protocol_products

Creates the Marvel Crisis Protocol product line as a new top-level Category
(no Faction subdivision -- Marvel Crisis Protocol is a standalone game
system, not a multi-faction wargame like 40k/AoS).

MSRP/images/URLs come from Asmodee's own store (store.asmodee.com), not
Games Workshop. This category has no GW retailer row at all -- product.msrp
still drives the site's MSRP/discount reference via the existing fallback in
views.py, since that fallback only looks for a not_available=False GW row
before falling back to product.msrp.

product.gw_url is populated with the Asmodee store product URL (not a real
GW link) per explicit instruction -- this enables the "View" button on the
product detail page. product_detail.html shows "View on Asmodee" instead of
"View on GW" for this category specifically.

Usage:
    python manage.py populate_marvel_crisis_protocol_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

_AMP_SKUS = {
    'MCP-002', 'MCP-003', 'MCP-004', 'MCP-006', 'MCP-007', 'MCP-008', 'MCP-009',
    'MCP-010', 'MCP-011', 'MCP-017', 'MCP-018', 'MCP-019', 'MCP-020', 'MCP-021',
    'MCP-023', 'MCP-036', 'MCP-048', 'MCP-053', 'MCP-054', 'MCP-055', 'MCP-056',
    'MCP-057', 'MCP-058', 'MCP-060', 'MCP-063', 'MCP-068', 'MCP-070', 'MCP-072',
}

# (slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('marvel-crisis-protocol-x-men-starter-set', 'MCP-001', 'Marvel: Crisis Protocol - X-Men Starter Set', decimal.Decimal('94.99'), 'https://store.asmodee.com/cdn/shop/files/CP271-image0_2000_535x.jpg?v=1755533197', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-x-men-starter-set', 'Marvel Crisis Protocol XMen Starter Set'),
    ('marvel-crisis-protocol-bastion-nimrod-omega-sentinel', 'MCP-002', 'Marvel: Crisis Protocol - Bastion, Nimrod & Omega Sentinel', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/MCP09-image0_2000_535x.jpg?v=1773928807', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-bastion-nimrod-omega-sentinel', 'Marvel Crisis Protocol Bastion, Nimrod & Omega Sentinel'),
    ('marvel-crisis-protocol-prowler-spider-man-2099-ultimate-spider-man', 'MCP-003', 'Marvel: Crisis Protocol - Prowler, Spider-Man 2099 & Ultimate Spider-Man', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/CP169-image0_2000_535x.jpg?v=1755610824', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-prowler-spider-man-2099-ultimate-spider-man', 'Marvel Crisis Protocol Prowler, SpiderMan 2099 & Ultimate SpiderMan'),
    ('marvel-crisis-protocol-phoenix-phoenix-unleashed', 'MCP-004', 'Marvel: Crisis Protocol - Phoenix & Phoenix Unleashed', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/CP83-image0_2000_535x.jpg?v=1744636465', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-phoenix-phoenix-unleashed', 'Marvel Crisis Protocol Phoenix & Phoenix Unleashed'),
    ('marvel-crisis-protocol-spider-foes-starter-set', 'MCP-005', 'Marvel: Crisis Protocol - Spider Foes Starter Set', decimal.Decimal('94.99'), 'https://store.asmodee.com/cdn/shop/files/CP272-image0_2000_535x.jpg?v=1755533294', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-spider-foes-starter-set', 'Marvel Crisis Protocol Spider Foes Starter Set'),
    ('marvel-crisis-protocol-silk-spider-ham-spider-man-noir', 'MCP-006', 'Marvel: Crisis Protocol - Silk, Spider-Ham & Spider-Man Noir', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/CP170-image0_2000_535x.jpg?v=1755610722', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-silk-spider-ham-spider-man-noir', 'Marvel Crisis Protocol Silk, SpiderHam & SpiderMan Noir'),
    ('marvel-crisis-protocol-operation-zero-tolerance-character-crisis-card-pack', 'MCP-007', 'Marvel: Crisis Protocol - Operation: Zero Tolerance Character & Crisis Card Pack', decimal.Decimal('44.99'), 'https://store.asmodee.com/cdn/shop/files/CA23-image0_2000_6fb2bd93-1971-4002-bfb2-29e49b334892_535x.jpg?v=1777384077', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-operation-zero-tolerance-character-crisis-card-pack', 'Marvel Crisis Protocol Operation Zero Tolerance Character & Crisis Card Pack'),
    ('marvel-crisis-protocol-bishop-nightcrawler', 'MCP-008', 'Marvel: Crisis Protocol - Bishop & Nightcrawler', decimal.Decimal('42.99'), 'https://store.asmodee.com/cdn/shop/files/CP112-image0_2000_535x.jpg?v=1703170292', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-bishop-nightcrawler', 'Marvel Crisis Protocol Bishop & Nightcrawler'),
    ('marvel-crisis-protocol-iron-lad-iron-monger-kang-the-conqueror-rescue', 'MCP-009', 'Marvel: Crisis Protocol - Iron Lad, Iron Monger, Kang the Conqueror & Rescue', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/CP154-image0_2000_535x.jpg?v=1767990031', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-iron-lad-iron-monger-kang-the-conqueror-rescue', 'Marvel Crisis Protocol Iron Lad, Iron Monger, Kang the Conqueror & Rescue'),
    ('marvel-crisis-protocol-iceman-shadowcat', 'MCP-010', 'Marvel: Crisis Protocol - Iceman & Shadowcat', decimal.Decimal('42.99'), 'https://store.asmodee.com/cdn/shop/files/CP96en-image0_2000_535x.jpg?v=1703170388', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-iceman-shadowcat', 'Marvel Crisis Protocol Iceman & Shadowcat'),
    ('marvel-crisis-protocol-adam-warlock-moondragon-quasar', 'MCP-011', 'Marvel: Crisis Protocol - Adam Warlock, Moondragon & Quasar', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/CP191-image0_2000_535x.jpg?v=1765465294', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-adam-warlock-moondragon-quasar', 'Marvel Crisis Protocol Adam Warlock, Moondragon & Quasar'),
    ('marvel-crisis-protocol-apocalypse', 'MCP-012', 'Marvel: Crisis Protocol - Apocalypse', decimal.Decimal('72.99'), 'https://store.asmodee.com/cdn/shop/files/CP107-image0_2000_535x.jpg?v=1720623271', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-apocalypse', 'Marvel Crisis Protocol Apocalypse'),
    ('marvel-crisis-protocol-monsters-unleashed-character-pack', 'MCP-013', 'Marvel: Crisis Protocol - Monsters Unleashed Character Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP245-image0_2000_535x.jpg?v=1725382009', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-monsters-unleashed-character-pack', 'Marvel Crisis Protocol Monsters Unleashed Character Pack'),
    ('marvel-crisis-protocol-war-of-kings-character-and-crisis-card-pack', 'MCP-014', 'Marvel: Crisis Protocol - War of Kings Character and Crisis Card Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/CA13-image0_2000_535x.jpg?v=1736436386', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-war-of-kings-character-and-crisis-card-pack', 'Marvel Crisis Protocol War of Kings Character and Crisis Card Pack'),
    ('marvel-crisis-protocol-xaviers-students-affiliation-pack', 'MCP-015', "Marvel: Crisis Protocol - Xavier's Students Affiliation Pack", decimal.Decimal('69.99'), 'https://store.asmodee.com/cdn/shop/files/CP226-image0_2000_535x.jpg?v=1763998819', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-xavier-s-students-affiliation-pack', "Marvel Crisis Protocol Xavier's Students Affiliation Pack"),
    ('marvel-crisis-protocol-web-swinging-heroes', 'MCP-016', 'Marvel: Crisis Protocol - Web-Swinging Heroes', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP234-image0_2000_535x.jpg?v=1755610616', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-web-swinging-heroes', 'Marvel Crisis Protocol WebSwinging Heroes'),
    ('marvel-crisis-protocol-professor-x-shadow-king', 'MCP-017', 'Marvel: Crisis Protocol - Professor X & Shadow King', decimal.Decimal('47.99'), 'https://store.asmodee.com/cdn/shop/files/CP151-image0_2000_535x.jpg?v=1703170826', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-professor-x-shadow-king', 'Marvel Crisis Protocol Professor X & Shadow King'),
    ('marvel-crisis-protocol-angel-archangel', 'MCP-018', 'Marvel: Crisis Protocol - Angel & Archangel', decimal.Decimal('47.99'), 'https://store.asmodee.com/cdn/shop/files/CP152-image0_2000_535x.jpg?v=1720646789', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-angel-archangel', 'Marvel Crisis Protocol Angel & Archangel'),
    ('marvel-crisis-protocol-avalanche-exodus-lady-mastermind', 'MCP-019', 'Marvel: Crisis Protocol - Avalanche, Exodus & Lady Mastermind', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/CP173-image0_2000_535x.jpg?v=1744636300', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-avalanche-exodus-lady-mastermind', 'Marvel Crisis Protocol Avalanche, Exodus & Lady Mastermind'),
    ('marvel-crisis-protocol-echo-ronin-tigra', 'MCP-020', 'Marvel: Crisis Protocol - Echo, Ronin & Tigra', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/CP168-image0_2000_535x.jpg?v=1755610875', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-echo-ronin-tigra', 'Marvel Crisis Protocol Echo, Ronin & Tigra'),
    ('marvel-crisis-protocol-abomination-wrecking-crew', 'MCP-021', 'Marvel: Crisis Protocol - Abomination & Wrecking Crew', decimal.Decimal('62.99'), 'https://store.asmodee.com/cdn/shop/files/CP162-image0_2000_535x.jpg?v=1725381875', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-abomination-wrecking-crew', 'Marvel Crisis Protocol Abomination & Wrecking Crew'),
    ('marvel-crisis-protocol-tomb-of-dracula-terrain-pack', 'MCP-022', 'Marvel: Crisis Protocol - Tomb of Dracula Terrain Pack', decimal.Decimal('119.99'), 'https://store.asmodee.com/cdn/shop/files/CPE05-image0_2000_535x.jpg?v=1725382175', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-tomb-of-dracula-terrain-pack', 'Marvel Crisis Protocol Tomb of Dracula Terrain Pack'),
    ('marvel-crisis-protocol-uncanny-telepaths-telekinetics', 'MCP-023', 'Marvel: Crisis Protocol - Uncanny Telepaths & Telekinetics', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/MCP13-image0_2000_535x.jpg?v=1782136197', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-uncanny-telepaths-telekinetics', 'Marvel Crisis Protocol Uncanny Telepaths & Telekinetics'),
    ('marvel-crisis-protocol-guardians-of-the-galaxy-starter-set', 'MCP-024', 'Marvel: Crisis Protocol - Guardians of the Galaxy Starter Set', decimal.Decimal('99.99'), 'https://store.asmodee.com/cdn/shop/files/MCP65-image0_2000_535x.jpg?v=1779812460', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-guardians-of-the-galaxy-starter-set', 'Marvel Crisis Protocol Guardians of the Galaxy Starter Set'),
    ('marvel-crisis-protocol-guardians-of-the-galaxy-affiliation-pack', 'MCP-025', 'Marvel: Crisis Protocol - Guardians of the Galaxy Affiliation Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP222-image0_2000_76d7893e-5ece-42f6-ae04-9e539393666e_535x.jpg?v=1737997549', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-guardians-of-the-galaxy-affiliation-pack', 'Marvel Crisis Protocol - Guardians of the Galaxy Affiliation Pack'),
    ('marvel-crisis-protocol-rejuvenation-chamber-ultimate-encounter', 'MCP-026', 'Marvel: Crisis Protocol - Rejuvenation Chamber Ultimate Encounter', decimal.Decimal('124.99'), 'https://store.asmodee.com/cdn/shop/files/CP194-image0_2000_535x.jpg?v=1720624938', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-rejuvenation-chamber-ultimate-encounter', 'Marvel Crisis Protocol Rejuvenation Chamber Ultimate Encounter'),
    ('marvel-crisis-protocol-asgardians-starter-set', 'MCP-027', 'Marvel: Crisis Protocol - Asgardians Starter Set', decimal.Decimal('124.99'), 'https://store.asmodee.com/cdn/shop/files/MCP64-image0_2000_535x.jpg?v=1780319250', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-asgardians-starter-set', 'Marvel Crisis Protocol - Asgardians Starter Set'),
    ('marvel-crisis-protocol-the-galaxys-deadliest-character-pack', 'MCP-028', "Marvel: Crisis Protocol - The Galaxy's Deadliest Character Pack", decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP223-image0_2000_0779bbbc-64e5-416a-8eaf-95beec4aaea9_535x.jpg?v=1737997635', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-the-galaxy-s-deadliest-character-pack', "Marvel Crisis Protocol The Galaxy's Deadliest Character Pack"),
    ('marvel-crisis-protocol-shield-affiliation-pack', 'MCP-029', 'Marvel: Crisis Protocol - S.H.I.E.L.D Affiliation Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/MCP03-image0_2000_535x.jpg?v=1773929713', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-s-h-i-e-l-d-affiliation-pack', 'Marvel Crisis Protocol - S.H.I.E.L.D Affiliation Pack'),
    ('marvel-crisis-protocol-criminal-syndicate-affiliation-pack', 'MCP-030', 'Marvel: Crisis Protocol - Criminal Syndicate Affiliation Pack', decimal.Decimal('69.99'), 'https://store.asmodee.com/cdn/shop/files/CP214-image0_2000_535x.jpg?v=1744817885', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-criminal-syndicate-affiliation-pack', 'Marvel Crisis Protocol Criminal Syndicate Affiliation Pack'),
    ('marvel-crisis-protocol-dark-future-terrain-pack', 'MCP-031', 'Marvel: Crisis Protocol - Dark Future Terrain Pack', decimal.Decimal('74.99'), 'https://store.asmodee.com/cdn/shop/files/CP185-image0_2000_535x.jpg?v=1720623395', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-dark-future-terrain-pack', 'Marvel Crisis Protocol Dark Future Terrain Pack'),
    ('marvel-crisis-protocol-shrine-to-en-sabah-nur-terrain-pack', 'MCP-032', 'Marvel: Crisis Protocol - Shrine to En Sabah Nur Terrain Pack', decimal.Decimal('69.99'), 'https://store.asmodee.com/cdn/shop/files/CP110-image0_2000_535x.jpg?v=1720623770', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-shrine-to-en-sabah-nur-terrain-pack', 'Marvel Crisis Protocol Shrine to En Sabah Nur Terrain Pack'),
    ('marvel-crisis-protocol-convocation-affiliation-pack', 'MCP-033', 'Marvel: Crisis Protocol - Convocation Affiliation Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP221-image0_2000_535x.jpg?v=1752067050', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-convocation-affiliation-pack', 'Marvel Crisis Protocol Convocation Affiliation Pack'),
    ('marvel-crisis-protocol-rival-panels-battle-for-the-throne', 'MCP-034', 'Marvel: Crisis Protocol - Rival Panels: Battle for the Throne', decimal.Decimal('99.99'), 'https://store.asmodee.com/cdn/shop/files/CPE04-image0_2000_535x.jpg?v=1700663822', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-rival-panels-battle-for-the-throne', 'Marvel Crisis Protocol Rival Panels Battle for the Throne'),
    ('marvel-crisis-protocol-hard-to-hit', 'MCP-035', 'Marvel: Crisis Protocol - Hard to Hit', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/MCP21-image0_2000_535x.jpg?v=1782134438', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-hard-to-hit', 'Marvel Crisis Protocol - Hard to Hit'),
    ('marvel-crisis-protocol-movement-range-tool-pack', 'MCP-036', 'Marvel: Crisis Protocol - Movement & Range Tool Pack', decimal.Decimal('19.99'), 'https://store.asmodee.com/cdn/shop/files/CA11-image0_2000_535x.jpg?v=1692891485', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-movement-range-tool-pack-1', 'Marvel Crisis Protocol Movement & Range Tool Pack'),
    ('marvel-crisis-protocol-dice-pack', 'MCP-037', 'Marvel: Crisis Protocol - Dice Pack', decimal.Decimal('14.99'), 'https://store.asmodee.com/cdn/shop/files/CP269-image0_2000_535x.jpg?v=1739563684', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-dice-pack-1', 'Marvel Crisis Protocol Dice Pack'),
    ('marvel-crisis-protocol-asgardian-shrine-terrain-pack', 'MCP-038', 'Marvel: Crisis Protocol - Asgardian Shrine Terrain Pack', decimal.Decimal('79.99'), 'https://store.asmodee.com/cdn/shop/files/CP106-image0_2000_535x.jpg?v=1717170253', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-asgardian-shrine-terrain-pack', 'Marvel Crisis Protocol - Asgardian Shrine Terrain Pack'),
    ('marvel-crisis-protocol-dimensional-terror-terrain-pack', 'MCP-039', 'Marvel: Crisis Protocol - Dimensional Terror Terrain Pack', decimal.Decimal('89.99'), 'https://store.asmodee.com/cdn/shop/files/MCP11-image0_2000_535x.jpg?v=1779812631', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-dimensional-terror-terrain-pack', 'Marvel Crisis Protocol Dimensional Terror Terrain Pack'),
    ('marvel-crisis-protocol-battle-for-asgard-terrain-pack', 'MCP-040', 'Marvel: Crisis Protocol - Battle for Asgard Terrain Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP95-image0_2000_535x.jpg?v=1717170386', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-battle-for-asgard-terrain-pack', 'Marvel Crisis Protocol - Battle for Asgard Terrain Pack'),
    ('marvel-crisis-protocol-inhumans-affiliation-pack', 'MCP-041', 'Marvel: Crisis Protocol - Inhumans Affiliation Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP218-image0_2000_535x.jpg?v=1763998970', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-inhumans-affiliation-pack', 'Marvel Crisis Protocol - Inhumans Affiliation Pack'),
    ('marvel-crisis-protocol-dark-dimension-incursion-terrain-pack', 'MCP-042', 'Marvel: Crisis Protocol - Dark Dimension Incursion Terrain Pack', decimal.Decimal('79.99'), 'https://store.asmodee.com/cdn/shop/files/MCP12-image0_2000_535x.jpg?v=1779812542', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-dark-dimension-incursion-terrain-pack', 'Marvel Crisis Protocol Dark Dimension Incursion Terrain Pack'),
    ('marvel-crisis-protocol-spider-foes-affiliation-pack', 'MCP-043', 'Marvel: Crisis Protocol - Spider-Foes Affiliation Pack', decimal.Decimal('62.99'), 'https://store.asmodee.com/cdn/shop/files/CP148-image0_2000_535x.jpg?v=1709827890', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-spider-foes-affiliation-pack', 'Marvel Crisis Protocol - SpiderFoes Affiliation Pack'),
    ('marvel-crisis-protocol-dormammu-ultimate-encounter', 'MCP-044', 'Marvel: Crisis Protocol - Dormammu Ultimate Encounter', decimal.Decimal('79.99'), 'https://store.asmodee.com/cdn/shop/files/CP217-image0_2000_535x.jpg?v=1769015464', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-dormammu-ultimate-encounter', 'Marvel Crisis Protocol - Dormammu Ultimate Encounter'),
    ('marvel-crisis-protocol-icons-of-bast-terrain-pack', 'MCP-045', 'Marvel: Crisis Protocol - Icons of Bast Terrain Pack', decimal.Decimal('84.99'), 'https://store.asmodee.com/cdn/shop/files/CP180-image0_2000_535x.jpg?v=1701969531', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-icons-of-bast-terrain-pack', 'Marvel Crisis Protocol Icons of Bast Terrain Pack'),
    ('marvel-crisis-protocol-winter-guard', 'MCP-046', 'Marvel: Crisis Protocol - Winter Guard', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/MCP19-image0_2000_535x.jpg?v=1782135130', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-winter-guard', 'Marvel Crisis Protocol - Winter Guard'),
    ('marvel-crisis-protocol-warriors-of-asgard-affiliation-pack', 'MCP-047', 'Marvel: Crisis Protocol - Warriors of Asgard Affiliation Pack', decimal.Decimal('69.99'), 'https://store.asmodee.com/cdn/shop/files/CP225-image0_2000_535x.jpg?v=1752066947', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-warriors-of-asgard-affiliation-pack', 'Marvel Crisis Protocol Warriors of Asgard Affiliation Pack'),
    ('marvel-crisis-protocol-movement-range-tools', 'MCP-048', 'Marvel: Crisis Protocol - Movement & Range Tools', decimal.Decimal('24.99'), 'https://store.asmodee.com/cdn/shop/files/CP270-image0_2000_535x.jpg?v=1744034910', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-movement-range-tools', 'Marvel Crisis Protocol Movement & Range Tools'),
    ('marvel-crisis-protocol-kingdom-of-wakanda-terrain-pack', 'MCP-049', 'Marvel: Crisis Protocol - Kingdom of Wakanda Terrain Pack', decimal.Decimal('84.99'), 'https://store.asmodee.com/cdn/shop/files/CP59-image1_2000_535x.jpg?v=1701967510', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-kingdom-of-wakanda-terrain-pack', 'Marvel Crisis Protocol Kingdom of Wakanda Terrain Pack'),
    ('marvel-crisis-protocol-cosmic-motherlode-terrain-pack', 'MCP-050', 'Marvel: Crisis Protocol - Cosmic Motherlode Terrain Pack', decimal.Decimal('89.99'), 'https://store.asmodee.com/cdn/shop/files/CP187-image0_2000_535x.jpg?v=1781118743', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-cosmic-motherlode-terrain-pack', 'Marvel Crisis Protocol - Cosmic Motherlode Terrain Pack'),
    ('marvel-crisis-protocol-avengers-affiliation-pack', 'MCP-051', 'Marvel: Crisis Protocol - Avengers Affiliation Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP141-image0_2000_535x.jpg?v=1709821905', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-avengers-affiliation-pack', 'Marvel Crisis Protocol - Avengers Affiliation Pack'),
    ('marvel-crisis-protocol-cabal-affiliation-pack', 'MCP-052', 'Marvel: Crisis Protocol - Cabal Affiliation Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP142-image0_2000_535x.jpg?v=1709822293', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-cabal-affiliation-pack', 'Marvel Crisis Protocol - Cabal Affiliation Pack'),
    ('marvel-crisis-protocol-hydra-tank-terrain-ultimate-encounter', 'MCP-053', 'Marvel: Crisis Protocol - Hydra Tank Terrain & Ultimate Encounter', decimal.Decimal('69.99'), 'https://store.asmodee.com/cdn/shop/products/CP78EN_535x.jpg?v=1690929059', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-hydra-tank-terrain-ultimate-encounter', 'Marvel Crisis Protocol Hydra Tank Terrain & Ultimate Encounter'),
    ('marvel-crisis-protocol-gwenom-scarlet-spider', 'MCP-054', 'Marvel: Crisis Protocol - Gwenom & Scarlet Spider', decimal.Decimal('42.99'), 'https://store.asmodee.com/cdn/shop/files/CP155-image0_2000_535x.jpg?v=1709827648', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-gwenom-scarlet-spider', 'Marvel Crisis Protocol - Gwenom & Scarlet Spider'),
    ('marvel-crisis-protocol-elsa-bloodstone-man-thing', 'MCP-055', 'Marvel: Crisis Protocol - Elsa Bloodstone & Man-Thing', decimal.Decimal('47.99'), 'https://store.asmodee.com/cdn/shop/files/CP186-image0_2000_535x.jpg?v=1732717515', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-elsa-bloodstone-man-thing', 'Marvel Crisis Protocol Elsa Bloodstone & ManThing'),
    ('marvel-crisis-protocol-mighty-thor-lady-sif-thor-hero-of-midgard-loki-prince-of-lies', 'MCP-056', 'Marvel: Crisis Protocol - Mighty Thor, Lady Sif, Thor, Hero of Midgard & Loki, Prince of Lies', decimal.Decimal('69.99'), 'https://store.asmodee.com/cdn/shop/files/CP91-image0_2000_535x.jpg?v=1717170505', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-mighty-thor-lady-sif-thor-hero-of-midgard-loki-prince-of-lies', 'Marvel Crisis Protocol - Mighty Thor, Lady Sif, Thor, Hero of Midgard & Loki, Prince of Lies'),
    ('marvel-crisis-protocol-valkyrie-on-elendil-warriors-three', 'MCP-057', 'Marvel: Crisis Protocol - Valkyrie on Elendil & Warriors Three', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/CP94-image0_2000_535x.jpg?v=1765465097', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-valkyrie-on-elendil-warriors-three', 'Marvel Crisis Protocol - Valkyrie on Elendil & Warriors Three'),
    ('marvel-crisis-protocol-yondu-nova', 'MCP-058', 'Marvel: Crisis Protocol - Yondu & Nova', decimal.Decimal('42.99'), 'https://store.asmodee.com/cdn/shop/files/CP126-image0_2000_535x.jpg?v=1732718262', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-yondu-nova', 'Marvel Crisis Protocol Yondu & Nova'),
    ('marvel-crisis-protocol-earths-mightiest-core-set', 'MCP-059', "Marvel: Crisis Protocol - Earth's Mightiest Core Set", decimal.Decimal('149.99'), 'https://store.asmodee.com/cdn/shop/files/CP143-image0_2000_535x.jpg?v=1692635246', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-earths-mightiest-core-set', "Marvel Crisis Protocol Earth's Mightiest Core Set"),
    ('marvel-crisis-protocol-black-panther-chosen-of-bast-namor-the-sub-mariner', 'MCP-060', 'Marvel: Crisis Protocol - Black Panther, Chosen of Bast & Namor, the Sub-Mariner', decimal.Decimal('52.99'), 'https://store.asmodee.com/cdn/shop/files/CP158-image0_2000_535x.jpg?v=1713977384', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-black-panther-chosen-of-bast-namor-the-sub-mariner', 'Marvel Crisis Protocol Black Panther, Chosen of Bast & Namor, the SubMariner'),
    ('marvel-crisis-protocol-defenders-affiliation-pack', 'MCP-061', 'Marvel: Crisis Protocol - Defenders Affiliation Pack', decimal.Decimal('69.99'), 'https://store.asmodee.com/cdn/shop/files/CP219-image0_2000_535x.jpg?v=1744817459', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-defenders-affiliation-pack', 'Marvel Crisis Protocol Defenders Affiliation Pack'),
    ('marvel-crisis-protocol-alliances-night-of-the-goblin', 'MCP-062', 'Marvel: Crisis Protocol Alliances - Night of the Goblin', decimal.Decimal('99.99'), 'https://store.asmodee.com/cdn/shop/files/MCA01-image0_2000_535x.jpg?v=1783344360', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-alliances-night-of-the-goblin', 'Marvel Crisis Protocol Alliances Night of the Goblin'),
    ('marvel-crisis-protocol-shang-chi-silver-sable', 'MCP-063', 'Marvel: Crisis Protocol - Shang Chi & Silver Sable', decimal.Decimal('42.99'), 'https://store.asmodee.com/cdn/shop/files/CP69-image0_2000_535x.jpg?v=1713977440', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-shang-chi-silver-sable', 'Marvel Crisis Protocol Shang Chi & Silver Sable'),
    ('marvel-crisis-protocol-sentinels-affiliation-pack', 'MCP-064', 'Marvel: Crisis Protocol - Sentinels Affiliation Pack', decimal.Decimal('74.99'), 'https://store.asmodee.com/cdn/shop/files/CP236-image0_2000_535x.jpg?v=1765830341', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-sentinels-affiliation-pack', 'Marvel Crisis Protocol Sentinels Affiliation Pack'),
    ('marvel-crisis-protocol-mojo-ball-scenario-pack', 'MCP-065', 'Marvel: Crisis Protocol - Mojo Ball Scenario Pack', decimal.Decimal('16.99'), 'https://store.asmodee.com/cdn/shop/files/CA14-image0_2000_535x.jpg?v=1713977499', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-mojo-ball-scenario-pack', 'Marvel Crisis Protocol - Mojo Ball Scenario Pack'),
    ('marvel-crisis-protocol-x-force-affiliation-pack', 'MCP-066', 'Marvel: Crisis Protocol - X-Force Affiliation Pack', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP224-image0_2000_535x.jpg?v=1765465168', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-x-force-affiliation-pack', 'Marvel Crisis Protocol XForce Affiliation Pack'),
    ('marvel-crisis-protocol-onslaught', 'MCP-067', 'Marvel: Crisis Protocol - Onslaught', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/MCP07-image0_2000_535x.jpg?v=1783966354', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-onslaught', 'Marvel Crisis Protocol Onslaught'),
    ('marvel-crisis-protocol-blue-marvel-spectrum', 'MCP-068', 'Marvel: Crisis Protocol - Blue Marvel & Spectrum', decimal.Decimal('42.99'), 'https://store.asmodee.com/cdn/shop/files/CP129-image1_2000_535x.png?v=1763413356', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-blue-marvel-spectrum', 'Marvel Crisis Protocol Blue Marvel & Spectrum'),
    ('marvel-crisis-protocol-inhuman-royal-court', 'MCP-069', 'Marvel: Crisis Protocol - Inhuman Royal Court', decimal.Decimal('64.99'), 'https://store.asmodee.com/cdn/shop/files/CP166-image0_2000_535x.jpg?v=1736436010', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-inhuman-royal-court', 'Marvel Crisis Protocol Inhuman Royal Court'),
    ('marvel-crisis-protocol-weapon-x-maverick', 'MCP-070', 'Marvel: Crisis Protocol - Weapon X & Maverick', decimal.Decimal('41.99'), 'https://store.asmodee.com/cdn/shop/files/CP109-image0_2000_535x.jpg?v=1720624356', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-weapon-x-maverick', 'Marvel Crisis Protocol Weapon X & Maverick'),
    ('marvel-crisis-protocol-nyc-city-block-terrain-collection', 'MCP-071', 'Marvel: Crisis Protocol - NYC City Block Terrain Collection', decimal.Decimal('154.99'), 'https://store.asmodee.com/cdn/shop/files/CPE06-image0_2000_535x.png?v=1755533372', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-nyc-city-block-terrain-collection', 'Marvel Crisis Protocol NYC City Block Terrain Collection'),
    ('marvel-crisis-protocol-sunspot-warlock', 'MCP-072', 'Marvel: Crisis Protocol - Sunspot & Warlock', decimal.Decimal('42.99'), 'https://store.asmodee.com/cdn/shop/files/CP153-image0_2000_535x.jpg?v=1720624510', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-sunspot-warlock', 'Marvel Crisis Protocol - Sunspot & Warlock'),
    ('marvel-crisis-protocol-mephisto', 'MCP-073', 'Marvel: Crisis Protocol - Mephisto', decimal.Decimal('34.99'), 'https://store.asmodee.com/cdn/shop/files/CP66-image0_2000_535x.jpg?v=1725570025', 'https://store.asmodee.com/collections/crisis-protocol/products/marvel-crisis-protocol-mephisto', 'Marvel Crisis Protocol Mephisto'),
]


class Command(BaseCommand):
    """Populate the Marvel Crisis Protocol product line (idempotent)."""

    help = 'Populates Marvel Crisis Protocol products (MCP-001 to MCP-073).'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='marvel-crisis-protocol',
            defaults={'name': 'Marvel Crisis Protocol'},
        )

        asmodee, _ = Retailer.objects.get_or_create(
            slug='asmodee',
            defaults={
                'name': 'Asmodee',
                'website': 'https://store.asmodee.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        products_created = 0
        products_updated = 0
        asmodee_prices_created = 0
        asmodee_prices_updated = 0

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
                    'ebay_allowed_title_words': '&' if gw_sku in _AMP_SKUS else '',
                    'batch_tag': 'marvel-crisis-protocol',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, asmodee_price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=asmodee,
                defaults={
                    'price': msrp,
                    'url': product_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if asmodee_price_created:
                asmodee_prices_created += 1
            else:
                asmodee_prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Asmodee prices: {asmodee_prices_created} created, {asmodee_prices_updated} updated.'
        ))
