"""
One-time command to write the 39 verified Amazon prices into the database.

All price/URL data was extracted from the Octoparse Amazon spreadsheet and
manually verified via import_amazon_prices.py (dry-run confirmed correct).

Usage:
    python manage.py apply_amazon_prices
    python manage.py apply_amazon_prices --dry-run
"""

import decimal

from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ---------------------------------------------------------------------------
# Verified Amazon prices  (sku → (price_str, url))
# Extracted from Amazon.com _ warhammer.xlsx via import_amazon_prices --dry-run
# ---------------------------------------------------------------------------
AMAZON_PRICES = {
    "31-06": ("165.00", "https://www.amazon.com/Games-Workshop-Heresy-CERASTUS-Knight/dp/B0CD7HZXX4/"),
    "40-01": ("58.65",  "https://www.amazon.com/GAMES-WORKSHOP-Warhammer-CORE-HARDBACK/dp/1804571784/"),
    "41-09": ("35.70",  "https://www.amazon.com/Sanguinary-Priest-Blood-Angels-Warhammer/dp/B0DJFF6QGY/"),
    "41-25": ("139.00", "https://www.amazon.com/Warhammer-40-000-Combat-Patrol/dp/B0DK3T1QSG/"),
    "43-50": ("51.00",  "https://www.amazon.com/Death-Guard-Plague-Marines-Warhammer/dp/B08T54H49C/"),
    "43-60": ("57.45",  "https://www.amazon.com/Games-Workshop-Warhammer-Eaters-43-10-99-12-01-02-153/dp/B0BTDHL1MH/"),
    "43-62": ("55.25",  "https://www.amazon.com/Games-Workshop-Warhammer-Exalted-Eightbound/dp/B0BTDD6Z24/"),
    "43-80": ("142.90", "https://www.amazon.com/Warhammer-40-000-Combat-Patrol/dp/B0F5X9MJ5B/"),
    "43-95": ("134.82", "https://www.amazon.com/Warhammer-40k-Combat-Patrol-Eaters/dp/B0F5X8GV4B/"),
    "44-06": ("62.48",  "https://www.amazon.com/Warhammer-40-000-Angels-ElJonson/dp/B0CB1BFQCZ/"),
    "44-10": ("59.48",  "https://www.amazon.com/WARHAMMER-40K-Angels-DEATHWING-Knights/dp/B0CVXNHD3P/"),
    "47-25": ("138.00", "https://www.amazon.com/Warhammer-40k-Combat-Patrol-Militarum/dp/B0DVT8JDQ6/"),
    "47-30": ("45.05",  "https://www.amazon.com/Games-Workshop-Warhammer-40K-Militarum-Cadian/dp/B0BSFPT9VX/"),
    "48-07": ("51.00",  "https://www.amazon.com/Warhammer-40000-Space-Marine-Tactical/dp/B08L6CLYR7/"),
    "48-37": ("57.45",  "https://www.amazon.com/Games-Workshop-Warhammer-Marines-Company/dp/B0CJS1GK5P/"),
    "48-41": ("55.25",  "https://www.amazon.com/Warhammer-Space-Marines-Primaris-Infiltrators/dp/B08GC37WBR/"),
    "48-43": ("55.25",  "https://www.amazon.com/Warhammer-40-000-Marines-Sternguard/dp/B0CJS1VS6C/"),
    "48-75": ("55.25",  "https://www.amazon.com/Warhammer-40-000-Primaris-Intercessors/dp/B08HSRFFFC/"),
    "48-76": ("55.25",  "https://www.amazon.com/Warhammer-40k-Primaris-Intercessors-dAssaut/dp/B08P7XNWPG/"),
    "48-93": ("69.70",  "https://www.amazon.com/Warhammer-Marines-Primaris-Redemptor-Dreadnought/dp/B08HSRX6Z3/"),
    "49-17": ("51.00",  "https://www.amazon.com/Warhammer-40k-Necrons-Flayed-Ones/dp/B095J8FYZP/"),
    "52-12": ("55.25",  "https://www.amazon.com/Games-Workshop-Warhammer-000-Sororitas/dp/B085Q29R7P/"),
    "52-20": ("55.25",  "https://www.amazon.com/Games-Workshop-Warhammer-000-Sororitas/dp/B083P7M8TF/"),
    "53-08": ("58.65",  "https://www.amazon.com/Games-Workshop-Warhammer-Wolves-Terminators/dp/B0FF4X73N1/"),
    "54-20": ("85.00",  "https://www.amazon.com/Games-Workshop-54-20-Knight-Armigers/dp/B0B116QHMG/"),
    "55-12": ("47.18",  "https://www.amazon.com/Games-Workshop-Warhammer-40K-Ultramarines/dp/B0FX34N7PR/"),
    "55-20": ("55.25",  "https://www.amazon.com/Games-Workshop-Warhammer-Black-Templars/dp/B09LG7HSLY/"),
    "55-22": ("36.98",  "https://www.amazon.com/Emperors-Champion-Templars-Warhammer-Marines/dp/B09LG7MHBR/"),
    "55-23": ("53.47",  "https://www.amazon.com/Games-Workshop-Warhammer-Templars-Brethren/dp/B09LG1SKWF/"),
    "55-25": ("33.15",  "https://www.amazon.com/Castellan-Black-Templars-Warhammer-Marines/dp/B09LG7FH94/"),
    "55-30": ("144.50", "https://www.amazon.com/Games-Workshop-Warhammer-Combat-Templars/dp/B0FJ91WF8T/"),
    "57-14": ("69.34",  "https://www.amazon.com/Warhammer-40K-Knights-Nemesis-Dreadknight/dp/B0FPDMT27L/"),
    "57-20": ("142.03", "https://www.amazon.com/Games-Workshop-Warhammer-Combat-Knights/dp/B0FJ915PXJ/"),
    "71-19": ("141.35", "https://www.amazon.com/Warhammer-40K-COMBAT-TYRANID-ASSAULT/dp/B0FJ8RTK8P/"),
    "80-01": ("51.08",  "https://www.amazon.com/Games-Workshop-Warhammer-Sigmar-Core/dp/1839063920/"),
    "KT-003": ("96.90", "https://www.amazon.com/Kill-Team-Starter-Set-Warhammer/dp/B0DKNXNTKS/"),
    "KT-100": ("96.90", "https://www.amazon.com/Kill-Team-Starter-Set-Warhammer/dp/B0DKNXNTKS/"),
    "PH-001": ("13.67", "https://www.amazon.com/Citadel-Outils-Poignee-peintre-mk2/dp/B08MC88KWZ/"),
    "PH-002": ("17.95", "https://www.amazon.com/Citadel-Painting-Handle-XL-2021/dp/B09KHBPRVL/"),
}


class Command(BaseCommand):
    """Apply 39 verified Amazon prices to the database (no xlsx needed)."""

    help = (
        "Write the 39 manually verified Amazon prices into CurrentPrice. "
        "All other active products are marked not_available for Amazon. "
        "Safe to re-run (idempotent)."
    )

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Print actions without writing to the database.",
        )

    def handle(self, *args, **options):
        """Execute the price update."""
        dry_run = options["dry_run"]

        try:
            amazon_retailer = Retailer.objects.get(name="Amazon")
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Amazon' not found in the database.")

        products = list(
            Product.objects
            .filter(is_active=True)
            .only("id", "gw_sku", "name")
        )
        self.stdout.write(f"Active products: {len(products)}")

        sku_to_product = {p.gw_sku: p for p in products}

        updated = 0
        marked_na = 0

        # --- Apply confirmed Amazon prices ---
        self.stdout.write("\n--- APPLYING AMAZON PRICES ---")
        for sku, (price_str, url) in sorted(AMAZON_PRICES.items()):
            product = sku_to_product.get(sku)
            if not product:
                self.stdout.write(
                    self.style.WARNING(f"  [skip] [{sku}] not found in active products")
                )
                continue

            price = decimal.Decimal(price_str)
            self.stdout.write(f"  [set] [{sku}] {product.name} → ${price}")

            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=amazon_retailer,
                    defaults={
                        "price":         price,
                        "url":           url,
                        "in_stock":      True,
                        "not_available": False,
                    },
                )
            updated += 1

        # --- Mark everything else not_available ---
        self.stdout.write("\n--- MARKING OTHER PRODUCTS NOT AVAILABLE ---")
        confirmed_skus = set(AMAZON_PRICES.keys())
        for product in products:
            if product.gw_sku in confirmed_skus:
                continue
            if not dry_run:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=amazon_retailer,
                    defaults={
                        "price":         None,
                        "url":           "",
                        "in_stock":      False,
                        "not_available": True,
                    },
                )
            marked_na += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'[DRY RUN] ' if dry_run else ''}Done!\n"
                f"  Prices applied:        {updated}\n"
                f"  Marked not_available:  {marked_na}"
            )
        )
