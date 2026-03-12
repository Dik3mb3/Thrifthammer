"""
Management command to import real Amazon prices from the Octoparse spreadsheet.

Usage:
    python manage.py import_amazon_prices --xlsx "path/to/Amazon.xlsx"

Strategy
--------
1. Read all Amazon rows (Title, Price_URL, Price) from the spreadsheet.
2. Match each to a ThriftHammer product using a curated whitelist of confirmed
   matches plus an automated best-match pass for any remaining products.
3. Products with confirmed matches → update price + URL, mark available.
4. Products with no match → mark not_available=True, price=None.

The command is idempotent — safe to re-run.  It only touches Amazon prices.
"""

import decimal
import re
from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand, CommandError

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_price(raw: str) -> decimal.Decimal | None:
    """Extract a Decimal from a string like '$55.25' or '55.25'."""
    raw = raw.strip().replace(",", "")
    m = re.search(r"\d+\.\d+", raw)
    if not m:
        return None
    val = decimal.Decimal(m.group())
    return val if val > 0 else None


def _normalise(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[''`]", "'", s)
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


STOP = {"warhammer", "40k", "40000", "the", "a", "an", "of", "and", "set",
        "games", "workshop", "miniatures", "models", "combat", "patrol"}


def _coverage(search: str, az_title: str) -> float:
    """Fraction of search-name tokens found in az_title (ignoring stopwords)."""
    ts = set(_normalise(search).split()) - STOP
    ta = set(_normalise(az_title).split()) - STOP
    if not ts:
        return 0.0
    return len(ts & ta) / len(ts)


# ---------------------------------------------------------------------------
# Curated whitelist  (sku → (amazon_title_fragment, for verification))
# Every entry here was manually verified against the Amazon spreadsheet.
# ---------------------------------------------------------------------------

CONFIRMED_SKUS = {
    # SKU: fragment checked against _normalise(az_title).
    # _normalise lowercases and replaces all punctuation/symbols with spaces (collapsed).
    # So use plain lowercase words only — no hyphens, colons, apostrophes.
    "31-06":   "cerastus knight lancer",
    "40-01":   "core book",
    # [40-03] Warhammer 40,000 Starter Set is NOT in this Amazon spreadsheet.
    "41-09":   "sanguinary priest",
    "41-25":   "combat patrol blood angels",
    "43-50":   "death guard plague marines",
    "43-60":   "berzerkers",
    "43-62":   "eightbound",
    "43-80":   "death guard combat patrol",
    "43-95":   "combat patrol world eaters",
    "44-06":   "lion el",
    "44-10":   "deathwing knights",
    "46-25":   "aeldari combat patrol",
    "47-25":   "combat patrol astra militarum",
    "47-30":   "cadian shock troops",
    "48-07":   "space marines tactical squad",
    "48-37":   "company heroes",
    "48-41":   "primaris infiltrators",
    "48-43":   "sternguard veteran squad",
    "48-75":   "primaris intercessors",          # NOT assault intercessors
    "48-76":   "assault intercessors",
    "48-93":   "redemptor dreadnought",
    "49-17":   "necrons flayed ones",
    "52-12":   "seraphim squad",
    "52-20":   "battle sisters squad",
    "53-08":   "wolf guard terminators",
    "54-20":   "knight armigers",
    "55-12":   "marneus calgar",
    "55-20":   "primaris crusader squad",
    "55-22":   "black templars emperor",
    "55-23":   "sword brethren",
    "55-25":   "black templars castellan",
    "55-30":   "combat patrol black templars",
    "56-15":   "crisis battlesuit",
    "56-19":   "pathfinder team",
    "57-14":   "dreadknight",
    "57-20":   "combat patrol grey knights",
    "71-19":   "tyranid assault brood",
    "71-20":   "combat patrol necrons",
    "80-01":   "age of sigmar core book",
    "KT-003":  "kill team starter set",
    "KT-100":  "kill team starter set",
    "PH-001":  "painting handle mk2",
    "PH-002":  "painting handle xl",
}


class Command(BaseCommand):
    """Import real Amazon prices from an Octoparse XLSX spreadsheet."""

    help = (
        "Import Amazon prices from ThriftHammer_Octoparse_Amazon.xlsx. "
        "Matched products get real prices; unmatched are marked not_available."
    )

    def add_arguments(self, parser):
        """Add --xlsx argument for the spreadsheet path."""
        parser.add_argument(
            "--xlsx",
            required=True,
            help="Path to the Amazon price XLSX file (Title, Price_URL, Price columns).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Print actions without writing to the database.",
        )

    def handle(self, *args, **options):
        """Execute the import."""
        xlsx_path = Path(options["xlsx"])
        dry_run = options["dry_run"]

        if not xlsx_path.exists():
            raise CommandError(f"File not found: {xlsx_path}")

        # ── 1. Load Amazon rows ────────────────────────────────────────────
        wb = openpyxl.load_workbook(str(xlsx_path))
        ws = wb.active
        amazon_rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if len(row) < 3:
                continue
            title, url, price = row[0], row[1], row[2]
            if title and url and price:
                amazon_rows.append({
                    "title": str(title).strip(),
                    "url":   str(url).strip(),
                    "price": str(price).strip(),
                    "norm":  set(_normalise(str(title)).split()) - STOP,
                })

        self.stdout.write(f"Amazon rows loaded: {len(amazon_rows)}")

        # ── 2. Load our products + search names from DB ────────────────────
        try:
            amazon_retailer = Retailer.objects.get(name="Amazon")
        except Retailer.DoesNotExist:
            raise CommandError("Retailer 'Amazon' not found in the database.")

        products = list(
            Product.objects
            .filter(is_active=True)
            .only("id", "gw_sku", "name", "gw_search_name")
        )
        self.stdout.write(f"Products to process: {len(products)}")

        # Build sku → search_name map (fall back to product name)
        sku_to_search = {
            p.gw_sku: (p.gw_search_name.strip() or p.name)
            for p in products
        }

        # ── 3. Match each product ──────────────────────────────────────────
        matched   = {}   # sku → az_row
        unmatched = []   # sku

        for prod in products:
            sku    = prod.gw_sku
            search = sku_to_search[sku]

            # Only attempt matching for confirmed SKUs
            if sku not in CONFIRMED_SKUS:
                unmatched.append(sku)
                continue

            required_frag = CONFIRMED_SKUS[sku]
            best_score = 0.0
            best_az    = None

            for az in amazon_rows:
                # The Amazon title must contain the required verification fragment
                if required_frag not in _normalise(az["title"]):
                    continue
                score = _coverage(search, az["title"])
                if score > best_score:
                    best_score = score
                    best_az    = az

            if best_az and best_score >= 0.60:
                matched[sku] = best_az
            else:
                unmatched.append(sku)

        self.stdout.write(f"\nMatched: {len(matched)} | Not found: {len(unmatched)}")

        # ── 4. Apply to database ───────────────────────────────────────────
        updated = skipped_no_price = marked_unavailable = 0

        sku_to_product = {p.gw_sku: p for p in products}

        # --- Matched products: real price + URL ---
        self.stdout.write("\n--- MATCHED (importing real prices) ---")
        for sku, az in sorted(matched.items()):
            price = _parse_price(az["price"])
            if price is None:
                self.stdout.write(f"  [skip-no-price] [{sku}]  {az['title']}")
                skipped_no_price += 1
                continue

            product = sku_to_product[sku]
            self.stdout.write(
                f"  [match] [{sku}] {product.name}\n"
                f"          -> {az['title']}  |  ${price}"
            )

            if not dry_run:
                cp, _ = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=amazon_retailer,
                    defaults={
                        "price":         price,
                        "url":           az["url"],
                        "in_stock":      True,
                        "not_available": False,
                    },
                )
            updated += 1

        # --- Unmatched products: mark not_available ---
        self.stdout.write("\n--- NOT FOUND (marking not_available) ---")
        for sku in sorted(unmatched):
            product = sku_to_product[sku]
            self.stdout.write(f"  [n/a] [{sku}] {product.name}")

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
            marked_unavailable += 1

        # ── 5. Summary ────────────────────────────────────────────────────
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'[DRY RUN] ' if dry_run else ''}Done!\n"
                f"  Real prices imported:   {updated}\n"
                f"  Skipped (price=$0):     {skipped_no_price}\n"
                f"  Marked not_available:   {marked_unavailable}"
            )
        )
