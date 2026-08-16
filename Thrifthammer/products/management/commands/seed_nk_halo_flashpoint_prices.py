"""
Management command: seed_nk_halo_flashpoint_prices

Seeds Noble Knight URLs for Halo: Flashpoint products from confirmed URLs
in the user-supplied "Halo Flashpoint - Noble Knight.xlsx".

21 of 26 sheet rows matched an existing HALO-xxx product. The other 5 rows
(Recon Edition Starter Set, New Mombasa Deluxe Gaming Mat, War Games
Expansion Pack, UNSC Firebase Deluxe Gaming Mat, Banished Garrison Deluxe
Gaming Mat) don't correspond to any product created by
populate_halo_flashpoint_products -- they appear to be real Mantic products
missing from the original Mantic-sourced product sheet. Flagged to user,
not added here.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_halo_flashpoint_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('halo-flashpoint-starter-set-spartan-edition', 'Halo - Flashpoint (Spartan Edition)', 124.95, 'https://www.nobleknight.com/P/2148213626/Halo---Flashpoint-Spartan-Edition?awid=1576', True, False),
    ('odst-scenery-set', 'ODST Scenery Set', 34.95, 'https://www.nobleknight.com/P/2148472215/ODST-Scenery-Set?awid=1576', True, False),
    ('unsc-base-terrain-set', 'UNSC Base Terrain Set', 31.95, 'https://www.nobleknight.com/P/2148283568/UNSC-Base-Terrain-Set?awid=1576', True, False),
    ('halo-flashpoint-force-organizer-tray-pack', 'Force Organizer Tray Pack', 31.95, 'https://www.nobleknight.com/P/2148379026/Force-Organizer-Tray-Pack?awid=1576', True, False),
    ('new-mombasa-terrain-set', 'New Mombasa Terrain Set', 40.95, 'https://www.nobleknight.com/P/2148429633/New-Mombasa-Terrain-Set?awid=1576', True, False),
    ('feet-first-into-hell-odst-faction-set', 'Feet First Into Hell', 124.95, 'https://www.nobleknight.com/P/2148368300/Feet-First-Into-Hell?awid=1576', True, False),
    ('fireteam-hydra', 'Fireteam Hydra', 35.95, 'https://www.nobleknight.com/P/2148289780/Fireteam-Hydra?awid=1576', True, False),
    ('unsc-scenery-set', 'UNSC Scenery Set', 33.95, 'https://www.nobleknight.com/P/2148289784/UNSC-Scenery-Set?awid=1576', True, False),
    ('halo-flashpoint-fireteam-wolf', 'Fireteam Wolf', 58.95, 'https://www.nobleknight.com/P/2148473522/Fireteam-Wolf?awid=1576', True, False),
    ('reach-deluxe-gaming-mat', 'Reach Deluxe Gaming Mat', 67.95, 'https://www.nobleknight.com/P/2148473490/Reach-Deluxe-Gaming-Mat?awid=1576', True, False),
    ('rise-of-the-banished-banished-faction-set', 'Rise of the Banished', 113.95, 'https://www.nobleknight.com/P/2148324810/Rise-of-the-Banished?awid=1576', True, False),
    ('banished-garrison-scenery-set', 'Banished Garrison Scenery Set', 33.95, 'https://www.nobleknight.com/P/2148378995/Banished-Garrison-Scenery-Set?awid=1576', True, False),
    ('atriox-warmaster-of-the-banished', 'Atriox, Warmaster of the Banished', 28.95, 'https://www.nobleknight.com/P/2148378993/Atriox-Warmaster-of-the-Banished?awid=1576', True, False),
    ('halo-flashpoint-buck-and-dare', 'Buck and Dare', 35.95, 'https://www.nobleknight.com/P/2148429630/Buck-and-Dare?awid=1576', True, False),
    ('defiance-banished-expansion', 'Defiance Expansion Pack', 51.95, 'https://www.nobleknight.com/P/2148378998/Defiance-Expansion-Pack?awid=1576', True, False),
    ('banished-jiralhanae', 'Jiralhanae Fireteam', 37.95, 'https://www.nobleknight.com/P/2148379004/Jiralhanae-Fireteam?awid=1576', True, False),
    ('field-outpost-deluxe-gaming-mat', 'Field Outpost Deluxe Gaming Mat', 37.95, 'https://www.nobleknight.com/P/2148283534/Field-Outpost-Deluxe-Gaming-Mat?awid=1576', True, False),
    ('halo-flashpoint-dice-booster', 'Dice Booster (14)', 18.95, 'https://www.nobleknight.com/P/2148213651/Dice-Booster-14?awid=1576', True, False),
    ('halo-flashpoint-deluxe-buildable-3d-terrain-set', 'Deluxe Buildable 3D Terrain Set', 89.95, 'https://www.nobleknight.com/P/2148213645/Deluxe-Buildable-3D-Terrain-Set?awid=1576', True, False),
    ('fireteam-cerberus', 'Fireteam Cerberus', 35.95, 'https://www.nobleknight.com/P/2148289776/Fireteam-Cerberus?awid=1576', True, False),
    ('desperate-measures-odst-expansion', 'Desperate Measures Expansion', 62.95, 'https://www.nobleknight.com/P/2148429627/Desperate-Measures-Expansion?awid=1576', True, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Halo: Flashpoint products."""

    help = 'seed_nk_halo_flashpoint_prices — NK URLs for Halo: Flashpoint (21 of 42 SKUs confirmed)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        nk_retailer = Retailer.objects.get(slug='noble-knight-games')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(slug=slug)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            self.stdout.write(f'  seeded NK: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_halo_flashpoint_prices complete. {seeded} record(s) seeded.'
        ))
