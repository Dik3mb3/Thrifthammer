"""
Management command: populate_star_wars_shatterpoint_products

Creates the Star Wars: Shatterpoint product line as a new top-level Category
(no Faction subdivision -- Star Wars: Shatterpoint is a standalone game
system, not a multi-faction wargame like 40k/AoS). Follows the same pattern
as Star Wars: Legion and Marvel Crisis Protocol.

MSRP/images/URLs come from Asmodee's own store (store.asmodee.com), not
Games Workshop. This category has no GW retailer row at all -- product.msrp
still drives the site's MSRP/discount reference via the existing fallback in
views.py, since that fallback only looks for a not_available=False GW row
before falling back to product.msrp.

product.gw_url is populated with the Asmodee store product URL (not a real
GW link) -- this enables the "View" button on the product detail page, same
pattern as Star Wars: Legion and Marvel Crisis Protocol.

Usage:
    python manage.py populate_star_wars_shatterpoint_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

# (slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('star-wars-shatterpoint-i-am-no-jedi-deluxe-duel-pack', 'SWS-001', 'Star Wars: Shatterpoint - I Am No Jedi Deluxe Duel Pack', decimal.Decimal('99.99'), 'https://store.asmodee.com/cdn/shop/files/SWP81-image0_2000_535x.jpg?v=1736438347', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-i-am-no-jedi-deluxe-duel-pack', 'Star Wars: Shatterpoint - I Am No Jedi Deluxe Duel Pack'),
    ('star-wars-shatterpoint-fear-and-dead-men-squad-pack', 'SWS-002', 'Star Wars: Shatterpoint - Fear and Dead Men Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP21-image0_2000_535x.jpg?v=1700059838', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-fear-and-dead-men-squad-pack', 'Star Wars: Shatterpoint - Fear and Dead Men Squad Pack'),
    ('star-wars-shatterpoint-delta-squad-form-up-squad-pack', 'SWS-003', 'Star Wars: Shatterpoint - Delta Squad, Form Up Squad Pack', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/SWP62-image0_2000_535x.png?v=1751982546', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-delta-squad-form-up-squad-pack', 'Star Wars: Shatterpoint - Delta Squad, Form Up Squad Pack'),
    ('star-wars-shatterpoint-all-the-way-squad-pack', 'SWS-004', 'Star Wars: Shatterpoint - All the Way Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP31-image0_2000_535x.jpg?v=1738338575', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-all-the-way-squad-pack-squad-pack', 'Star Wars: Shatterpoint - All the Way Squad Pack'),
    ('star-wars-shatterpoint-certified-guild-squad-pack', 'SWS-005', 'Star Wars: Shatterpoint - Certified Guild Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP24-image0_2000_535x.jpg?v=1706555583', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-certified-guild-squad-pack', 'Star Wars: Shatterpoint - Certified Guild Squad Pack'),
    ('star-wars-shatterpoint-deploy-the-garrison-squad-pack', 'SWS-006', 'Star Wars: Shatterpoint - Deploy the Garrison Squad Pack', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/SWP51-image0_2000_535x.jpg?v=1738338714', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-deploy-the-garrison-squad-pack', 'Star Wars: Shatterpoint - Deploy the Garrison Squad Pack'),
    ('star-wars-shatterpoint-make-the-impossible-possible-squad-pack', 'SWS-007', 'Star Wars: Shatterpoint - Make the Impossible Possible Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP44-image0_2000_535x.jpg?v=1713977608', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-make-the-impossible-possible-squad-pack', 'Star Wars: Shatterpoint - Make the Impossible Possible Squad Pack'),
    ('star-wars-shatterpoint-lead-by-example-squad-pack', 'SWS-008', 'Star Wars: Shatterpoint - Lead by Example Squad Pack', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/SWP11-image0_2000_535x.jpg?v=1701889925', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-lead-by-example-squad-pack', 'Star Wars: Shatterpoint - Lead by Example Squad Pack'),
    ('star-wars-shatterpoint-fearless-and-inventive-squad-pack', 'SWS-009', 'Star Wars: Shatterpoint - Fearless and Inventive Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP22-image0_2000_535x.jpg?v=1700059940', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-fearless-and-inventive-squad-pack', 'Star Wars: Shatterpoint - Fearless and Inventive Squad Pack'),
    ('star-wars-shatterpoint-stronger-than-fear-squad-pack', 'SWS-010', 'Star Wars: Shatterpoint - Stronger Than Fear Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP29-image0_2000_535x.jpg?v=1713977645', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-stronger-than-fear-squad-pack', 'Star Wars: Shatterpoint - Stronger Than Fear Squad Pack'),
    ('star-wars-shatterpoint-first-contact-mission-pack', 'SWS-011', 'Star Wars: Shatterpoint - First Contact Mission Pack', decimal.Decimal('14.99'), 'https://store.asmodee.com/cdn/shop/files/SWP49-image0_2000_535x.jpg?v=1738338795', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-first-contact-mission-pack', 'Star Wars: Shatterpoint - First Contact Mission Pack'),
    ('star-wars-shatterpoint-never-tell-me-the-odds-mission-pack', 'SWS-012', 'Star Wars: Shatterpoint - Never Tell Me the Odds Mission Pack', decimal.Decimal('14.99'), 'https://store.asmodee.com/cdn/shop/files/SWP48-image0_2000_535x.jpg?v=1712153361', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-never-tell-me-the-odds-mission-pack', 'Star Wars: Shatterpoint - Never Tell Me the Odds Mission Pack'),
    ('star-wars-shatterpoint-you-have-something-i-want-squad-pack', 'SWS-013', 'Star Wars: Shatterpoint - You Have Something I Want Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP26-image0_2000_535x.jpg?v=1706555658', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-you-have-something-i-want-squad-pack', 'Star Wars: Shatterpoint - You Have Something I Want Squad Pack'),
    ('star-wars-shatterpoint-sabotage-showdown', 'SWS-014', 'Star Wars: Shatterpoint - Sabotage Showdown', decimal.Decimal('14.99'), 'https://store.asmodee.com/cdn/shop/files/SWP45-image0_2000_535x.jpg?v=1694618474', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-sabotage-showdown', 'Star Wars: Shatterpoint - Sabotage Showdown'),
    ('star-wars-shatterpoint-this-is-rogue-one-squad-pack', 'SWS-015', 'Star Wars: Shatterpoint - This is Rogue One Squad Pack', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/SWP52-image0_2000_535x.jpg?v=1751982644', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-this-is-rogue-one-squad-pack', 'Star Wars: Shatterpoint - This is Rogue One Squad Pack'),
    ('star-wars-shatterpoint-we-dont-need-their-scum-unit-pack', 'SWS-016', 'Star Wars: Shatterpoint - We Don\'t Need Their Scum Unit Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP25-image0_2000_535x.jpg?v=1724967393', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-we-don-t-need-their-scum-squad-pack', 'Star Wars: Shatterpoint - We Don\'t Need Their Scum Unit Pack'),
    ('star-wars-shatterpoint-this-is-the-way-squad-pack', 'SWS-017', 'Star Wars: Shatterpoint - This Is The Way Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP16-image0_2000_535x.jpg?v=1724967185', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-this-is-the-way-squad-pack', 'Star Wars: Shatterpoint - This Is The Way Squad Pack'),
    ('star-wars-shatterpoint-yub-nub-squad-pack', 'SWS-018', 'Star Wars: Shatterpoint - Yub Nub Squad Pack', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/SWP39-image0_2000_535x.jpg?v=1701889973', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-yub-nub-squad-pack', 'Star Wars: Shatterpoint - Yub Nub Squad Pack'),
    ('star-wars-shatterpoint-i-am-no-jedi-duel-pack', 'SWS-019', 'Star Wars: Shatterpoint - I Am No Jedi Duel Pack', decimal.Decimal('42.99'), 'https://store.asmodee.com/cdn/shop/files/SWP42-image0_2000_535x.jpg?v=1751982688', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-i-am-no-jedi-duel-pack', 'Star Wars: Shatterpoint - I Am No Jedi Duel Pack'),
    ('star-wars-shatterpoint-today-the-rebellion-dies-squad-pack', 'SWS-020', 'Star Wars: Shatterpoint - Today the Rebellion Dies Squad Pack', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/SWP34-image0_2000_535x.jpg?v=1712598895', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-today-the-rebellion-dies-squad-pack', 'Star Wars: Shatterpoint - Today the Rebellion Dies Squad Pack'),
    ('star-wars-shatterpoint-hello-there-general-obi-wan-kenobi-squad-pack', 'SWS-021', 'Star Wars: Shatterpoint - Hello There: General Obi - Wan Kenobi Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/products/SWP06_535x.jpg?v=1690405016', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-hello-there-general-obi-wan-kenobi-squad-pack', 'Star Wars: Shatterpoint - Hello There: General Obi - Wan Kenobi Squad Pack'),
    ('star-wars-shatterpoint-twice-the-pride-count-dooku-squad-pack', 'SWS-022', 'Star Wars: Shatterpoint - Twice the Pride: Count Dooku Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/products/SWP03_535x.jpg?v=1690405044', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-twice-the-pride-count-dooku-squad-pack', 'Star Wars: Shatterpoint - Twice the Pride: Count Dooku Squad Pack'),
    ('star-wars-shatterpoint-this-partys-over-mace-windu-squad-pack', 'SWS-023', 'Star Wars: Shatterpoint - This Party\'s Over: Mace Windu Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP08-image0_2000_535x.jpg?v=1691009008', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-this-partys-over-mace-windu-squad-pack', 'Star Wars: Shatterpoint - This Party\'s Over: Mace Windu Squad Pack'),
    ('star-wars-shatterpoint-witches-of-dathomir-mother-talzin-squad-pack', 'SWS-024', 'Star Wars: Shatterpoint - Witches of Dathomir: Mother Talzin Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP07-image0_2000_535x.jpg?v=1691008942', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-witches-of-dathomir-mother-talzin-squad-pack', 'Star Wars: Shatterpoint - Witches of Dathomir: Mother Talzin Squad Pack'),
    ('star-wars-shatterpoint-jedi-hunters', 'SWS-025', 'Star Wars: Shatterpoint - Jedi Hunters', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP12-image0_2000_535x.jpg?v=1691009365', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-jedi-hunters', 'Star Wars: Shatterpoint - Jedi Hunters'),
    ('star-wars-shatterpoint-we-are-brave-squad-pack', 'SWS-026', 'Star Wars: Shatterpoint - We Are Brave: Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP15-image0_2000_535x.jpg?v=1691009449', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-we-are-brave-squad-pack', 'Star Wars: Shatterpoint - We Are Brave: Squad Pack'),
    ('star-wars-shatterpoint-fistful-of-credits-cad-bane-squad-pack', 'SWS-027', 'Star Wars: Shatterpoint - Fistful of Credits: Cad Bane Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP09-image0_2000_535x.jpg?v=1691009291', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-fistful-of-credits-cad-bane-squad-pack', 'Star Wars: Shatterpoint - Fistful of Credits: Cad Bane Squad Pack'),
    ('star-wars-shatterpoint-you-cannot-run-duel-pack', 'SWS-028', 'Star Wars: Shatterpoint - You Cannot Run Duel Pack', decimal.Decimal('89.99'), 'https://store.asmodee.com/cdn/shop/files/SWP30-image0_2000_535x.jpg?v=1691009546', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-you-cannot-run-duel-pack', 'Star Wars: Shatterpoint - You Cannot Run Duel Pack'),
    ('star-wars-shatterpoint-plans-and-preparation-squad-pack', 'SWS-029', 'Star Wars: Shatterpoint - Plans and Preparation Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP04-image0_2000_535x.jpg?v=1691008830', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-plans-and-preparation-squad-pack', 'Star Wars: Shatterpoint - Plans and Preparation Squad Pack'),
    ('star-wars-shatterpoint-take-cover-terrain-pack', 'SWS-030', 'Star Wars: Shatterpoint - Take Cover Terrain Pack', decimal.Decimal('74.99'), 'https://store.asmodee.com/cdn/shop/products/SWP17_535x.jpg?v=1691009458', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-take-cover-terrain-pack', 'Star Wars: Shatterpoint - Take Cover Terrain Pack'),
    ('star-wars-shatterpoint-secure-the-future-squad-pack', 'SWS-032', 'Star Wars: Shatterpoint - Secure the Future Squad Pack', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/SWP82-image0_2000_535x.jpg?v=1773927529', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-secure-the-future-squad-pack', 'Star Wars: Shatterpoint - Secure the Future Squad Pack'),
    ('star-wars-shatterpoint-requesting-your-surrender-squad-pack', 'SWS-033', 'Star Wars: Shatterpoint - Requesting Your Surrender Squad Pack', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/SWP37-image0_2000_9da4b812-18b7-4c70-94b7-4b72a6bdfdbd_535x.jpg?v=1737997778', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-requesting-your-surrender-squad-pack', 'Star Wars: Shatterpoint - Requesting Your Surrender Squad Pack'),
    ('star-wars-shatterpoint-wisdom-of-the-council-squad-pack', 'SWS-034', 'Star Wars: Shatterpoint - Wisdom of the Council Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP50-image0_2000_535x.jpg?v=1732718809', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-wisdom-of-the-council-squad-pack', 'Star Wars: Shatterpoint - Wisdom of the Council Squad Pack'),
    ('star-wars-shatterpoint-real-quiet-like-squad-pack', 'SWS-035', 'Star Wars: Shatterpoint - Real Quiet Like Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP35-image0_2000_535x.jpg?v=1712153561', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-real-quiet-like-squad-pack', 'Star Wars: Shatterpoint - Real Quiet Like Squad Pack'),
    ('star-wars-shatterpoint-my-loyalty-my-life-squad-pack', 'SWS-036', 'Star Wars: Shatterpoint - My Loyalty, My Life Squad Pack', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/SWP83-image0_2000_535x.jpg?v=1773927063', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-my-loyalty-my-life-squad-pack', 'Star Wars: Shatterpoint - My Loyalty, My Life Squad Pack'),
    ('star-wars-shatterpoint-terror-from-below-squad-pack', 'SWS-037', 'Star Wars: Shatterpoint - Terror From Below Squad Pack', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/SWP63-image0_2000_535x.jpg?v=1751982313', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-terror-from-below-squad-pack', 'Star Wars: Shatterpoint - Terror From Below Squad Pack'),
    ('star-wars-shatterpoint-ee-chee-wa-maa-squad-pack', 'SWS-038', 'Star Wars: Shatterpoint - Ee Chee Wa Maa! Squad Pack', decimal.Decimal('59.99'), 'https://store.asmodee.com/cdn/shop/files/SWP27-image0_2000_535x.jpg?v=1701885055', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-ee-chee-wa-maa-squad-pack', 'Star Wars: Shatterpoint - Ee Chee Wa Maa! Squad Pack'),
    ('star-wars-shatterpoint-not-accepting-surrenders-squad-pack', 'SWS-039', 'Star Wars: Shatterpoint - Not Accepting Surrenders Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP28-image0_2000_535x.jpg?v=1717170755', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-not-accepting-surrenders-squad-pack', 'Star Wars: Shatterpoint - Not Accepting Surrenders Squad Pack'),
    ('star-wars-shatterpoint-this-is-some-rescue-squad-pack', 'SWS-040', 'Star Wars: Shatterpoint - This is Some Rescue! Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP41-image0_2000_535x.jpg?v=1717170876', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-this-is-some-rescue-squad-pack', 'Star Wars: Shatterpoint - This is Some Rescue! Squad Pack'),
    ('star-wars-shatterpoint-thats-good-business-squad-pack', 'SWS-041', 'Star Wars: Shatterpoint - That\'s Good Business Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP10-image0_2000_535x.jpg?v=1706555496', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-thats-good-business-squad-pack', 'Star Wars: Shatterpoint - That\'s Good Business Squad Pack'),
    ('star-wars-shatterpoint-strategic-positions', 'SWS-042', 'Star Wars: Shatterpoint - Strategic Positions', decimal.Decimal('14.99'), 'https://store.asmodee.com/cdn/shop/files/SWP72-image0_2000_535x.jpg?v=1767990190', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-strategic-positions', 'Star Wars: Shatterpoint - Strategic Positions'),
    ('star-wars-shatterpoint-maximum-firepower-squad-pack', 'SWS-043', 'Star Wars: Shatterpoint - Maximum Firepower Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP46-image0_2000_535x.jpg?v=1724967008', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-maximum-firepower-squad-pack', 'Star Wars: Shatterpoint - Maximum Firepower Squad Pack'),
    ('star-wars-shatterpoint-core-set', 'SWS-044', 'Star Wars: Shatterpoint Core Set', decimal.Decimal('164.99'), 'https://store.asmodee.com/cdn/shop/products/SWP01EN_535x.jpg?v=1690401726', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-core-set', 'Star Wars: Shatterpoint Core Set'),
    ('star-wars-shatterpoint-dice-pack', 'SWS-045', 'Star Wars: Shatterpoint - Dice Pack', decimal.Decimal('14.99'), 'https://store.asmodee.com/cdn/shop/files/SWP19EN-image0_2000_535x.jpg?v=1691009491', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-dice-pack', 'Star Wars: Shatterpoint - Dice Pack'),
    ('star-wars-shatterpoint-good-soldiers-follow-orders-squad-pack', 'SWS-046', 'Star Wars: Shatterpoint - Good Soldiers Follow Orders Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP36-image0_2000_535x.jpg?v=1722352623', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-good-soldiers-follow-orders-squad-pack', 'Star Wars: Shatterpoint - Good Soldiers Follow Orders Squad Pack'),
    ('star-wars-shatterpoint-outer-rim-outpost-terrain-pack', 'SWS-047', 'Star Wars: Shatterpoint - Outer Rim Outpost Terrain Pack', decimal.Decimal('54.99'), 'https://store.asmodee.com/cdn/shop/files/SWP60-image0_2000_535x.jpg?v=1751982600', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-outer-rim-outpost-terrain-pack', 'Star Wars: Shatterpoint - Outer Rim Outpost Terrain Pack'),
    ('star-wars-shatterpoint-measuring-tools', 'SWS-048', 'Star Wars: Shatterpoint - Measuring Tools', decimal.Decimal('14.99'), 'https://store.asmodee.com/cdn/shop/products/SWP20-1_535x.jpg?v=1690226037', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-measuring-tools', 'Star Wars: Shatterpoint - Measuring Tools'),
    ('star-wars-shatterpoint-appetite-for-destruction-squad-pack', 'SWS-049', 'Star Wars: Shatterpoint - Appetite for Destruction Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP05-image0_2000_535x.jpg?v=1691008878', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-appetite-for-destruction-squad-pack', 'Star Wars: Shatterpoint - Appetite for Destruction Squad Pack'),
    ('star-wars-shatterpoint-what-have-we-here-squad-pack', 'SWS-050', 'Star Wars: Shatterpoint - What Have We Here Squad Pack', decimal.Decimal('49.99'), 'https://store.asmodee.com/cdn/shop/files/SWP47-image0_2000_535x.jpg?v=1724967628', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-what-have-we-here-squad-pack', 'Star Wars: Shatterpoint - What Have We Here Squad Pack'),
    ('star-wars-shatterpoint-maintenance-bay-terrain-pack', 'SWS-051', 'Star Wars: Shatterpoint - Maintenance Bay Terrain Pack', decimal.Decimal('84.99'), 'https://store.asmodee.com/cdn/shop/files/SWP18-image0_2000_535x.jpg?v=1717170621', 'https://store.asmodee.com/collections/star-wars-shatterpoint/products/star-wars-shatterpoint-maintenance-bay-terrain-pack', 'Star Wars: Shatterpoint - Maintenance Bay Terrain Pack'),
    # SWS-052/053: not yet listed on store.asmodee.com -- only on Atomic Mass
    # Games' own site (the game's designer/publisher). URLs, image, and MSRP
    # confirmed directly by the user (2026-07-22), not scraped.
    ('star-wars-shatterpoint-high-ground-terrain-pack', 'SWS-052', 'Star Wars: Shatterpoint - High Ground Terrain Pack', decimal.Decimal('74.99'), 'https://cdn.svc.asmodee.net/production-amgcom/uploads/image-converter/2023/02/2000_SWP02-image2@2000.jpg-500x500-_500_SWP02-image2@500.png-1024x1024-_SANA_SWP02-2.webp', 'https://www.atomicmassgames.com/character/high-ground-terrain-pack/', 'Star Wars: Shatterpoint - High Ground Terrain Pack'),
    ('star-wars-shatterpoint-clone-force-99-squad-pack', 'SWS-053', 'Star Wars: Shatterpoint - Clone Force 99 Squad Pack', decimal.Decimal('59.99'), 'https://cdn.svc.asmodee.net/production-amgcom/uploads/image-converter/2024/02/SWP38-Product-Image.webp', 'https://www.atomicmassgames.com/character/clone-force-99-squad-pack/', 'Star Wars: Shatterpoint - Clone Force 99 Squad Pack'),
]


class Command(BaseCommand):
    """Populate the Star Wars: Shatterpoint product line (idempotent)."""

    help = 'Populates Star Wars: Shatterpoint products (SWS-001 to SWS-051).'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='star-wars-shatterpoint',
            defaults={'name': 'Star Wars: Shatterpoint'},
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
                    'batch_tag': 'star-wars-shatterpoint',
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
