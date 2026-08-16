"""
Management command: populate_halo_flashpoint_products

Creates the Halo: Flashpoint product line as a new top-level Category
(no Faction subdivision -- standalone game system, same pattern as
Star Wars: Legion).

MSRP/images/URLs come from Mantic Games' own store (manticgames.com), not
Games Workshop. This category has no GW retailer row at all -- product.msrp
still drives the site's MSRP/discount reference via the existing fallback in
views.py, since that fallback only looks for a not_available=False GW row
before falling back to product.msrp.

product.gw_url is populated with the Mantic Games store product URL (not a
real GW link) -- this enables the "View" button on the product detail page,
same pattern as Star Wars: Legion / Marvel Crisis Protocol.

Usage:
    python manage.py populate_halo_flashpoint_products
"""

import decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Product, Retailer

# (slug, gw_sku, name, msrp, image_url, product_url, ebay_search_name)
PRODUCTS = [
    ('atriox-warmaster-of-the-banished', 'HALO-001', 'Atriox - Warmaster of the Banished', decimal.Decimal('35.00'), 'https://www.manticgames.com/wp-content/uploads/2025/05/banished-atriox-retail-web-image-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-banished/atriox-warmaster-of-the-banished-retail-version/', 'Halo Flashpoint Atriox'),
    ('banished-garrison-scenery-set', 'HALO-002', 'Banished Garrison Scenery Set', decimal.Decimal('45.00'), 'https://www.manticgames.com/wp-content/uploads/2025/05/banished-garrison-scenery-web-image-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-accessories-terrain/banished-garrison-scenery-set/', 'Halo Flashpoint Banished Garrison Scenery Set'),
    ('banished-jiralhanae', 'HALO-003', 'Banished Jiralhanae', decimal.Decimal('55.00'), 'https://www.manticgames.com/wp-content/uploads/2025/05/banished-jiralhanae-fireteam-web-image-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-banished/jiralhanae-fireteam/', 'Halo Flashpoint Banished Jiralhanae'),
    ('banished-sangheili-mercenaries', 'HALO-004', 'Banished Sangheili Mercenaries', decimal.Decimal('45.00'), 'https://www.manticgames.com/wp-content/uploads/2025/05/halo-flashpoint-fireteam-sangheili-mercenaries-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-banished/sangheili-mercenaries/', 'Halo Flashpoint Banished Sangheili Mercenaries'),
    ('brute-force-banished-new-player-bundle', 'HALO-005', 'Brute Force - Banished New Player Bundle', decimal.Decimal('179.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/brute-force-bundle-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/getting-started/brute-force-new-player-bundle/', 'Halo Flashpoint Brute Force'),
    ('defiance-banished-expansion', 'HALO-006', 'Defiance - Banished Expansion', decimal.Decimal('70.00'), 'https://www.manticgames.com/wp-content/uploads/2025/05/halo-flashpoint-defiance-expansion-500x499.webp', 'https://www.manticgames.com/halo-flashpoint/halo-flashpoint-banished/defiance/', 'Halo Flashpoint Defiance'),
    ('desperate-measures-odst-expansion', 'HALO-007', 'Desperate Measures - ODST Expansion', decimal.Decimal('70.00'), 'https://www.manticgames.com/wp-content/uploads/2025/11/webstore-desperate-measures-webp-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/desperate-measures-expansion/', 'Halo Flashpoint Desperate Measures'),
    ('feet-first-into-hell-odst-faction-set', 'HALO-008', 'Feet First Into Hell - ODST Faction Set', decimal.Decimal('149.00'), 'https://www.manticgames.com/wp-content/uploads/2025/07/halo-flashpoint-feet-first-into-hell-odst-box-set-contents-product-shot-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/feet-first-into-hell/', 'Halo Flashpoint Feet First Into Hell'),
    ('field-outpost-deluxe-gaming-mat', 'HALO-009', 'Field Outpost Deluxe Gaming Mat', decimal.Decimal('55.00'), 'https://www.manticgames.com/wp-content/uploads/2025/01/halo-flashpoint-field-deluxe-neoprene-mat-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/field-outpost-deluxe-gaming-mat/', 'Halo Flashpoint Field Outpost Deluxe Gaming Mat'),
    ('fireteam-cerberus', 'HALO-010', 'Fireteam Cerberus', decimal.Decimal('45.00'), 'https://www.manticgames.com/wp-content/uploads/2025/01/halo-flashpoint-fireteam-cerberus-new-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/fireteam-cerberus-spartan-pack/', 'Halo Flashpoint Fireteam Cerberus'),
    ('fireteam-hydra', 'HALO-011', 'Fireteam Hydra', decimal.Decimal('45.00'), 'https://www.manticgames.com/wp-content/uploads/2025/01/halo-flashpoint-fireteam-hydra-pack-coloured-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/fireteam-hydra-spartans-pack/', 'Halo Flashpoint Fireteam Hydra'),
    ('halo-flashpoint-1-player-token-set', 'HALO-012', 'Halo: Flashpoint 1 Player Token Set', decimal.Decimal('19.50'), 'https://www.manticgames.com/wp-content/uploads/2025/01/halo-flashpoint-1-player-acrylic-token-set-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/token-set/', 'Halo Flashpoint 1 Player Token Set'),
    ('halo-flashpoint-banished-faction-bundle', 'HALO-013', 'Halo: Flashpoint Banished Faction Bundle', decimal.Decimal('259.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/banished-faction-bundle-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/latest-releases/banished-faction-bundle/', 'Halo Flashpoint Banished Faction Bundle'),
    ('halo-flashpoint-banished-reinforcements', 'HALO-014', 'Halo: Flashpoint Banished Reinforcements', decimal.Decimal('80.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/banished-reinforcements-box-isolateds-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/banished/reinforcements/', 'Halo Flashpoint Banished Reinforcements'),
    ('halo-flashpoint-banished-spartan-killers', 'HALO-015', 'Halo: Flashpoint Banished Spartan Killers', decimal.Decimal('79.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/spartan-killers-trio-isolated-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/banished/spartan-killers/', 'Halo Flashpoint Banished Spartan Killers'),
    ('halo-flashpoint-buck-and-dare', 'HALO-016', 'Halo: Flashpoint Buck and Dare', decimal.Decimal('40.00'), 'https://www.manticgames.com/wp-content/uploads/2025/11/webstore-buck-and-dare-retail-webp-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/gunnery-sergeant-buck-captain-dare/', 'Halo Flashpoint Buck and Dare'),
    ('halo-flashpoint-deluxe-buildable-3d-terrain-set', 'HALO-017', 'Halo: Flashpoint Deluxe Buildable 3D Terrain Set', decimal.Decimal('130.00'), 'https://www.manticgames.com/wp-content/uploads/2025/01/halo-flashpoint-deluxe-terrain-set-iso-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/deluxe-3d-terrain-set/', 'Halo Flashpoint Deluxe Buildable Terrain Set'),
    ('halo-flashpoint-dice-booster', 'HALO-018', 'Halo: Flashpoint Dice Booster', decimal.Decimal('25.00'), 'https://www.manticgames.com/wp-content/uploads/2025/01/halo-flashpoint-dice-booster-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/dice-booster/', 'Halo Flashpoint Dice Booster'),
    ('halo-flashpoint-fireteam-grizzly', 'HALO-019', 'Halo: Flashpoint Fireteam Grizzly', decimal.Decimal('45.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/fireteam-grizzly-box-contents-miniatures-isolated-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/fireteam-grizzly/', 'Halo Flashpoint Fireteam Grizzly'),
    ('halo-flashpoint-fireteam-phoenix', 'HALO-020', 'Halo: Flashpoint Fireteam Phoenix', decimal.Decimal('63.00'), 'https://www.manticgames.com/wp-content/uploads/2025/03/halo-flashpoint-fireteam-phoenix-squad-art-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/fireteam-phoenix-show-special-spartans-pack/', 'Halo Flashpoint Fireteam Phoenix'),
    ('halo-flashpoint-fireteam-wolf', 'HALO-021', 'Halo: Flashpoint Fireteam Wolf', decimal.Decimal('65.00'), 'https://www.manticgames.com/wp-content/uploads/2026/02/team-wolf-isolated-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/fireteam-wolf/', 'Halo Flashpoint Fireteam Wolf'),
    ('halo-flashpoint-force-organizer-tray-pack', 'HALO-022', 'Halo: Flashpoint Force Organizer Tray Pack', decimal.Decimal('35.00'), 'https://www.manticgames.com/wp-content/uploads/2025/03/halo-flashpoint-force-organizer-tray-pack-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/force-organizer-tray-pack/', 'Halo Flashpoint Force Organizer Tray Pack'),
    ('halo-flashpoint-paint-set-including-master-chief', 'HALO-023', 'Halo: Flashpoint Paint Set - including Master Chief', decimal.Decimal('60.00'), 'https://www.manticgames.com/wp-content/uploads/2025/01/halo-flashpoint-paint-set-master-chief-new-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/paint-set/', 'Halo Flashpoint Paint Set'),
    ('halo-flashpoint-rulebook-pack', 'HALO-024', 'Halo: Flashpoint Rulebook Pack', decimal.Decimal('30.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/rulebook-pack-with-new-player-banner-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/getting-started/game-rulebook-pack/', 'Halo Flashpoint Rulebook Pack'),
    ('halo-flashpoint-starter-set-spartan-edition', 'HALO-025', 'Halo: Flashpoint Starter Set - Spartan Edition', decimal.Decimal('149.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/spartan-edition-updated-v3-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/getting-started/spartan-edition-updated/', 'Halo Flashpoint Spartan Edition'),
    ('halo-flashpoint-unit-card-update-pack', 'HALO-026', 'Halo: Flashpoint Unit Card Update Pack', decimal.Decimal('15.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/halo-flashpoint-unit-card-update-pack-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/accessories-terrain/unit-card-update-pack-v15/', 'Halo Flashpoint Unit Card Update Pack'),
    ('halo-flashpoint-unsc-faction-bundle', 'HALO-027', 'Halo: Flashpoint UNSC Faction Bundle', decimal.Decimal('326.50'), 'https://www.manticgames.com/wp-content/uploads/2026/06/unsc-faction-bundle-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/faction-bundle/', 'Halo Flashpoint UNSC Faction Bundle'),
    ('halo-flashpoint-unsc-marines', 'HALO-028', 'Halo: Flashpoint UNSC Marines', decimal.Decimal('80.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/unsc-reinforcements-box-isolateds-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/marines/', 'Halo Flashpoint UNSC Marines'),
    ('jiralhanae-fireteam-new-player-bundle', 'HALO-029', 'Jiralhanae Fireteam - New Player Bundle', decimal.Decimal('125.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/jiralhanae-fireteam-bundle-v2-500x500.webp', 'https://www.manticgames.com/product/halo-flashpoint/halo-flashpoint-banished/jiralhanae-fireteam-new-player-bundle/', 'Halo Flashpoint Jiralhanae Fireteam'),
    ('new-mombasa-terrain-set', 'HALO-030', 'New Mombasa Terrain Set', decimal.Decimal('45.00'), 'https://www.manticgames.com/wp-content/uploads/2025/11/new-momasa-terrain-isolated-mock-up-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/accessories-terrain/new-mombasa-terrain-set/', 'Halo Flashpoint New Mombasa Terrain'),
    ('noble-team-expansion', 'HALO-031', 'Noble Team Expansion', decimal.Decimal('89.00'), 'https://www.manticgames.com/wp-content/uploads/2026/02/halo-flashpoint-noble-team-box-contents-product-shot-full-size-copy-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/noble-team/', 'Halo Flashpoint Noble Team Expansion'),
    ('odst-fireteam-new-player-bundle', 'HALO-032', 'ODST Fireteam - New Player Bundle', decimal.Decimal('125.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/odst-fireteam-bundle-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/odst-fireteam-new-player-bundle/', 'Halo Flashpoint ODST Fireteam'),
    ('odst-scenery-set', 'HALO-033', 'ODST Scenery Set', decimal.Decimal('39.00'), 'https://www.manticgames.com/wp-content/uploads/2026/02/odst-scenery-set-isolated-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/accessories-terrain/odst-scenery-set/', 'Halo Flashpoint ODST Scenery Set'),
    ('orbital-drop-odst-new-player-bundle', 'HALO-034', 'Orbital Drop - ODST New Player Bundle', decimal.Decimal('179.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/orbital-drop-bundle-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/getting-started/orbital-drop-new-player-bundle/', 'Halo Flashpoint Orbital Drop'),
    ('outpost-buildable-3d-terrain-set', 'HALO-035', 'Outpost Buildable 3D Terrain Set', decimal.Decimal('70.00'), 'https://www.manticgames.com/wp-content/uploads/2025/03/halo-flashpoint-3d-outpost-building-group-shot-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/outpost-3d-plastic-terrain-set/', 'Halo Flashpoint Outpost Buildable Terrain Set'),
    ('reach-deluxe-gaming-mat', 'HALO-036', 'Reach Deluxe Gaming Mat', decimal.Decimal('75.00'), 'https://www.manticgames.com/wp-content/uploads/2026/02/reach-deluxe-gaming-mat-box-and-mat-mockup-copy-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/accessories-terrain/reach-deluxe-gaming-mat/', 'Halo Flashpoint Reach Deluxe Gaming Mat'),
    ('rise-of-the-banished-banished-faction-set', 'HALO-037', 'Rise of the Banished - Banished Faction Set', decimal.Decimal('149.00'), 'https://www.manticgames.com/wp-content/uploads/2025/03/halo-flashpoint-rise-of-the-banished-product-shot-new-elites-1-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/rise-of-the-banished-boxed-set/', 'Halo Flashpoint Rise of the Banished'),
    ('sangheili-fireteam-new-player-bundle', 'HALO-038', 'Sangheili Fireteam - New Player Bundle', decimal.Decimal('100.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/sangheili-fireteam-bundle-v2-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/banished/sangheili-fireteam-new-player-bundle/', 'Halo Flashpoint Sangheili Fireteam'),
    ('spartan-fireteam-new-player-bundle', 'HALO-039', 'Spartan Fireteam - New Player Bundle', decimal.Decimal('100.00'), 'https://www.manticgames.com/wp-content/uploads/2026/06/spartan-fireteam-bundle-v3-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc/spartan-fireteam-new-player-bundle/', 'Halo Flashpoint Spartan Fireteam'),
    ('the-master-chief-humanitys-greatest-weapon', 'HALO-040', "The Master Chief, Humanity's Greatest Weapon", decimal.Decimal('22.50'), 'https://www.manticgames.com/wp-content/uploads/2025/03/halo-flashpoint-master-chief-angle-2-image-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/master-chief-humanitys-greatest-weapon/', 'Halo Flashpoint The Master Chief'),
    ('unsc-base-terrain-set', 'HALO-041', 'UNSC Base Terrain Set', decimal.Decimal('45.00'), 'https://www.manticgames.com/wp-content/uploads/2025/01/unsc-base-terrain-set-web-image-modified-copy-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc-base-terrain-set/', 'Halo Flashpoint UNSC Base Terrain Set'),
    ('unsc-scenery-set', 'HALO-042', 'UNSC Scenery Set', decimal.Decimal('45.00'), 'https://www.manticgames.com/wp-content/uploads/2025/01/halo-flashpoint-unsc-scenery-set-colour-isolated-500x500.webp', 'https://www.manticgames.com/halo-flashpoint/unsc-plastic-scenery-set/', 'Halo Flashpoint UNSC Scenery Set'),
]


class Command(BaseCommand):
    """Populate the Halo: Flashpoint product line (idempotent)."""

    help = 'Populates Halo: Flashpoint products (HALO-001 to HALO-042).'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='halo-flashpoint',
            defaults={'name': 'Halo: Flashpoint'},
        )

        mantic, _ = Retailer.objects.get_or_create(
            slug='mantic-games',
            defaults={
                'name': 'Mantic Games',
                'website': 'https://www.manticgames.com',
                'country': 'US',
                'is_active': True,
                'is_uk': False,
            },
        )

        products_created = 0
        products_updated = 0
        mantic_prices_created = 0
        mantic_prices_updated = 0

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
                    'batch_tag': 'halo-flashpoint',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

            _, mantic_price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mantic,
                defaults={
                    'price': msrp,
                    'url': product_url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            if mantic_price_created:
                mantic_prices_created += 1
            else:
                mantic_prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Mantic Games prices: {mantic_prices_created} created, {mantic_prices_updated} updated.'
        ))
