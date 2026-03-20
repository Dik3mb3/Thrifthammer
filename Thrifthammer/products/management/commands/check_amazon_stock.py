"""
Management command: check_amazon_stock
=======================================
Fetches each Amazon product URL stored in CurrentPrice and updates the
in_stock flag based on whether the listing shows "Add to Cart" (in stock)
or "Currently unavailable" / "Currently Unavailable" (out of stock).

Uses a realistic browser User-Agent to avoid trivial bot-detection blocks.
Respects a short delay between requests to reduce the chance of throttling.

Usage:
    python manage.py check_amazon_stock
    python manage.py check_amazon_stock --dry-run       # print results, no DB writes
    python manage.py check_amazon_stock --delay 2.0     # seconds between requests
    python manage.py check_amazon_stock --sku 48-75     # single product by GW SKU
"""

import time

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Retailer


# Realistic desktop Chrome header — reduces Amazon bot-detection false positives
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

# Strings that indicate a listing is OUT OF STOCK on Amazon
_OOS_STRINGS = [
    "Currently unavailable",
    "currently unavailable",
    "This item is currently unavailable",
    "We don't know when or if this item will be back in stock",
    "out of stock",
    "Out of Stock",
]

# The HTML id of the "Add to Cart" button — present when the item IS in stock
_ADD_TO_CART_ID = "add-to-cart-button"


def _check_url(url: str, timeout: int = 12) -> bool | None:
    """
    Fetch an Amazon product URL and return:
        True   — item appears to be In Stock
        False  — item appears to be Out of Stock / Unavailable
        None   — result is indeterminate (CAPTCHA, network error, etc.)
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
    except requests.RequestException:
        return None

    if resp.status_code != 200:
        return None

    text = resp.text

    # Bail out if Amazon is showing a CAPTCHA / robot-check page
    if (
        "api.whsites.net/captcha" in text
        or 'id="captchacharacters"' in text
        or "Enter the characters you see below" in text
        or "Sorry, we just need to make sure you're not a robot" in text
    ):
        return None

    # Definitive out-of-stock signals
    for phrase in _OOS_STRINGS:
        if phrase in text:
            return False

    # Definitive in-stock signal
    soup = BeautifulSoup(text, "html.parser")
    if soup.find(id=_ADD_TO_CART_ID):
        return True

    # Fallback: look for "Add to Cart" text in any button
    buttons = soup.find_all("input", {"type": "submit"})
    for btn in buttons:
        val = btn.get("value", "")
        if "Add to Cart" in val or "add to cart" in val.lower():
            return True

    return None  # Cannot determine


class Command(BaseCommand):
    """Check live Amazon pages and update the in_stock flag on CurrentPrice."""

    help = "Checks Amazon product URLs for stock status and updates the DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print results without writing to the database.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=1.5,
            help="Seconds to wait between Amazon requests (default: 1.5).",
        )
        parser.add_argument(
            "--sku",
            type=str,
            default="",
            help="Only check the product with this GW SKU (e.g. 48-75).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        delay = options["delay"]
        sku_filter = options["sku"].strip()

        try:
            amazon = Retailer.objects.get(slug="amazon")
        except Retailer.DoesNotExist:
            self.stderr.write(self.style.ERROR("Retailer 'amazon' not found in DB."))
            return

        qs = CurrentPrice.objects.filter(
            retailer=amazon,
            not_available=False,
        ).select_related("product")

        if sku_filter:
            qs = qs.filter(product__gw_sku=sku_filter)

        entries = list(qs)
        total = len(entries)

        if total == 0:
            self.stdout.write("No Amazon CurrentPrice entries to check.")
            return

        mode = "DRY-RUN " if dry_run else ""
        self.stdout.write(f"{mode}Checking {total} Amazon listing(s)…\n")

        in_stock_count = 0
        oos_count = 0
        unknown_count = 0
        changed_count = 0

        for i, cp in enumerate(entries, start=1):
            product_name = cp.product.name
            sku = cp.product.gw_sku or "—"
            url = cp.url

            if not url or "amazon.com" not in url:
                self.stdout.write(
                    f"  [{i}/{total}] SKIP  {product_name} ({sku}) — no valid Amazon URL"
                )
                unknown_count += 1
                continue

            result = _check_url(url)

            if result is True:
                status_str = self.style.SUCCESS("IN STOCK ")
                in_stock_count += 1
                if cp.in_stock != True:
                    changed_count += 1
                    if not dry_run:
                        cp.in_stock = True
                        # avoid touching last_seen (auto_now) by using update()
                        CurrentPrice.objects.filter(pk=cp.pk).update(in_stock=True)
            elif result is False:
                status_str = self.style.ERROR("OUT OF STOCK")
                oos_count += 1
                if cp.in_stock != False:
                    changed_count += 1
                    if not dry_run:
                        CurrentPrice.objects.filter(pk=cp.pk).update(in_stock=False)
            else:
                status_str = self.style.WARNING("UNKNOWN     ")
                unknown_count += 1

            self.stdout.write(
                f"  [{i}/{total}] {status_str}  {product_name} ({sku})"
            )

            # Polite delay — avoid hammering Amazon
            if i < total:
                time.sleep(delay)

        self.stdout.write(
            f"\n{'[DRY-RUN] ' if dry_run else ''}"
            f"Done — In Stock: {in_stock_count}  |  "
            f"Out of Stock: {oos_count}  |  "
            f"Unknown/Blocked: {unknown_count}  |  "
            f"DB changes: {changed_count if not dry_run else '(dry-run)'}"
        )
