"""
Management command: seed_mm_halo_flashpoint_prices

Seeds Miniature Market URLs for Halo: Flashpoint products from confirmed
URLs in the user-supplied "Halo Flashpoint - Miniature Market.xlsx".

19 of 25 sheet rows matched an existing HALO-xxx product with a confirmed
price. "Rise of the Banished" also matched a product but its Price cell
was blank in the source sheet, so it's covered by NK only, not here (a
missing MM price is not a confirmed listing). 5 further rows (UNSC
Firebase Playmat, Recon Edition Starter Set, Banished Dice Booster,
Banished Garrison Terrain (Preorder), Banished Garrison Deluxe Gaming
Mat) don't correspond to any product created by
populate_halo_flashpoint_products -- they appear to be real Mantic
products missing from the original Mantic-sourced product sheet. Flagged
to user, not added here.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_halo_flashpoint_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('field-outpost-deluxe-gaming-mat', 'Halo Flashpoint Field Outpost playmat', 43.99, 'https://www.miniaturemarket.com/halo-flashpoint-field-outpost-playmat-mgha108.html', True, False),
    ('banished-jiralhanae', 'Halo: Flashpoint - Jiralhanae Pack', 46.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Jiralhanae-Pack/MGHAB301', True, False),
    ('banished-sangheili-mercenaries', 'Halo: Flashpoint - Sangheili Mercenaries (Preorder)', 35.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Sangheili-Mercenaries-Preorder/MGHAB302', True, False),
    ('halo-flashpoint-dice-booster', 'Halo: Flashpoint - Dice Booster (14)', 17.99, 'https://www.miniaturemarket.com/halo-flashpoint-dice-booster-14-mgha104.html', True, False),
    ('defiance-banished-expansion', 'Halo: Flashpoint - Defiance Expansion Pack', 59.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Defiance-Expansion-Pack/MGHAB101', True, False),
    ('feet-first-into-hell-odst-faction-set', 'Halo: Flashpoint - Feet First Into Hell', 119.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Feet-First-Into-Hell/MGHAU102', True, False),
    ('halo-flashpoint-starter-set-spartan-edition', 'Halo: Flashpoint - Spartan Edition Starter Set', 119.99, 'https://www.miniaturemarket.com/halo-flashpoint-spartan-edition-mgha102.html', True, False),
    ('desperate-measures-odst-expansion', 'Halo: Flashpoint - Desperate Measures (Preorder)', 55.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Desperate-Measures-Preorder/MGHAU103', True, False),
    ('banished-garrison-scenery-set', 'Halo: Flashpoint - Banished Garrison Scenery Set', 38.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Banished-Garrison-Scenery-Set/MGHAB104', True, False),
    ('unsc-base-terrain-set', 'Halo: Flashpoint - UNSC Base Terrain Set', 38.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-UNSC-Base-Terrain-Set/MGHA109', True, False),
    ('fireteam-hydra', 'Halo: Flashpoint - UNSC Fireteam Hydra', 35.99, 'https://www.miniaturemarket.com/halo-unsc-fireteam-hydra-mghau302.html', True, False),
    ('fireteam-cerberus', 'Halo: Flashpoint - UNSC Fireteam Cerberus', 35.99, 'https://www.miniaturemarket.com/halo-unsc-fireteam-cerberus-mghau301.html', True, False),
    ('unsc-scenery-set', 'Halo: Flashpoint - UNSC Scenery Set', 36.99, 'https://www.miniaturemarket.com/halo-unsc-scenery-set-mghau101.html', True, False),
    ('new-mombasa-terrain-set', 'Halo: Flashpoint - New Mombasa Terrain (Preorder)', 35.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-New-Mombasa-Terrain-Preorder/MGHAU105', True, False),
    ('halo-flashpoint-force-organizer-tray-pack', 'Halo: Flashpoint - Force Organizer Tray Pack (Preorder)', 27.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Force-Organizer-Tray-Pack-Preorder/MGHAM101', True, False),
    ('halo-flashpoint-deluxe-buildable-3d-terrain-set', 'Halo: Flashpoint - Deluxe Buildable 3D Terrain Set', 89.99, 'https://www.miniaturemarket.com/halo-flashpoint-deluxe-buildable-3d-terrain-set-mgha103.html', True, False),
    ('outpost-buildable-3d-terrain-set', 'Halo: Flashpoint - Outpost Buildable 3D Terrain Set (Preorder)', 55.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Outpost-Buildable-3D-Terrain-Set-Preorder/MGHA111', True, False),
    ('atriox-warmaster-of-the-banished', 'Halo: Flashpoint - Atriox, Warmaster of the Banished (Standard Version) (Preorder)', 27.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Atriox-Warmaster-of-the-Banished-Standard-Version-Preorder/MGHAB201', True, False),
    ('halo-flashpoint-buck-and-dare', 'Halo: Flashpoint - Buck & Dare (Retail Versions) (Preorder)', 31.99, 'https://www.miniaturemarket.com/Halo-Flashpoint-Buck-Dare-Retail-Versions-Preorder/MGHAU201', True, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Halo: Flashpoint products."""

    help = 'seed_mm_halo_flashpoint_prices — MM URLs for Halo: Flashpoint (19 of 42 SKUs confirmed)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        mm_retailer = Retailer.objects.get(slug='miniature-market')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(slug=slug)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm_retailer,
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
            self.stdout.write(f'  seeded MM: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_halo_flashpoint_prices complete. {seeded} record(s) seeded.'
        ))
