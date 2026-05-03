"""
Amazon price scraper — uses your real Chrome browser via Playwright.

Pulls Amazon URLs directly from the database so new products are picked up
automatically without editing this file.

Three batches split alphabetically by product name (~192 products each):
  Batch 1 — A through C  (~171 products)
  Batch 2 — D through N  (~202 products)
  Batch 3 — O through Z  (~203 products)

Usage:
  python scrape_amazon_browser.py --batch 1
  python scrape_amazon_browser.py --batch 2
  python scrape_amazon_browser.py --batch 3
  python scrape_amazon_browser.py --batch 2 --resume
  python scrape_amazon_browser.py --sku 43-04   (no batch needed)

Output: amazon_prices_batch{N}.json  (or amazon_prices_sku_{SKU}.json for --sku)
"""

import argparse
import json
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ---------------------------------------------------------------------------
# Django is set up inside __main__ after arg parsing, so DATABASE_URL (set
# by the PS1 wrapper from .env.production) is already in the environment.
# ---------------------------------------------------------------------------
DJANGO_PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Thrifthammer')
sys.path.insert(0, DJANGO_PROJECT_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thrifthammer.settings')

# ---------------------------------------------------------------------------
# Batch letter ranges — edit these if you want different splits
# ---------------------------------------------------------------------------
BATCH_RANGES = {
    1: ('a', 'c'),   # A–C (~171 products)
    2: ('d', 'n'),   # D–N (~202 products)
    3: ('o', 'z'),   # O–Z (~203 products)
}
BATCH_LABELS = {
    1: 'A–C',
    2: 'D–N',
    3: 'O–Z',
}


def load_products(batch_num=None, sku_filter=None):
    """
    Query the DB for active Amazon CurrentPrice rows and return a list of
    (gw_sku, product_name, amazon_url) tuples sorted alphabetically.

    If sku_filter is given, returns only that SKU (batch_num ignored).
    If batch_num is given, filters by the corresponding letter range.
    """
    from prices.models import CurrentPrice  # import after django.setup()
    qs = (
        CurrentPrice.objects
        .filter(retailer__slug='amazon')
        .exclude(url='')
        .select_related('product')
        .filter(product__is_active=True)
        .order_by('product__name')
    )

    if sku_filter:
        qs = qs.filter(product__gw_sku=sku_filter)
    elif batch_num is not None:
        lo, hi = BATCH_RANGES[batch_num]
        qs = qs.filter(product__name__iregex=f'^[{lo}-{hi}]')

    products = [(cp.product.gw_sku, cp.product.name, cp.url) for cp in qs]

    if not products:
        if sku_filter:
            print(f'No active Amazon URL found for SKU {sku_filter!r}.')
        else:
            print(f'No products found for batch {batch_num} ({BATCH_LABELS[batch_num]}).')
    return products


# ---------------------------------------------------------------------------
# Price extraction
# ---------------------------------------------------------------------------
PRICE_SELECTORS = [
    # Standard price containers (most specific first)
    '#corePrice_feature_div .a-price .a-offscreen',
    '#apex_offerDisplay_desktop .a-price .a-offscreen',
    '#price_inside_buybox',
    '#priceblock_ourprice',
    # Accessibility label for the final "price to pay" — present on many listing
    # layouts including the Riptide-style pages where standard containers are absent.
    # inner_text() returns e.g. " $103.70 "; regex extracts the dollar amount.
    '#apex-pricetopay-accessibility-label',
    # Installment-payment layout pages (e.g. Angron, Bloodletters):
    # The main offer section may expose price without a .a-price wrapper.
    '#apex_offerDisplay_desktop .a-offscreen',
    # "One-time payment $X.XX" panel shown when Amazon offers monthly installments.
    # inner_text() returns "One-time payment $144.50"; regex pulls the dollar amount.
    '#monthlyPaymentInfo0',
    # Broad fallback — catches remaining cases but may grab installment amounts
    # on pages where none of the specific selectors above match.
    '.a-price .a-offscreen',
]
UNAVAILABLE_MARKERS = ['currently unavailable', 'this item is not available', 'out of stock', 'sign in to purchase']
BLOCKED_MARKERS     = ['robot check', 'ap/signin', 'verify you are a human', 'automated access']


def extract_price(page):
    """Try each CSS selector in order and return the first dollar amount found."""
    for selector in PRICE_SELECTORS:
        try:
            el = page.query_selector(selector)
            if el:
                text  = el.inner_text().strip()
                match = re.search(r'\$[\d,]+\.?\d*', text)
                if match:
                    return match.group().replace(',', '').replace('$', '')
        except Exception:
            continue
    return None


def check_page_status(page):
    """Return 'blocked', 'unavailable', or 'ok' based on page body text."""
    try:
        body = page.inner_text('body').lower()
    except Exception:
        return 'error'
    for m in BLOCKED_MARKERS:
        if m in body:
            return 'blocked'
    for m in UNAVAILABLE_MARKERS:
        if m in body:
            return 'unavailable'
    return 'ok'


# ---------------------------------------------------------------------------
# Main scrape loop
# ---------------------------------------------------------------------------
def scrape(products, output_file, resume):
    """
    Open Chrome via Playwright and visit each Amazon URL to extract prices.

    Results are written to output_file as JSON after every product so a
    partial run can be resumed with --resume.
    """
    existing = {}
    if resume and os.path.exists(output_file):
        with open(output_file) as f:
            existing = json.load(f)
        print(f'Resuming — {len(existing)} SKUs already scraped.')

    results = dict(existing)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            ),
        )
        page    = context.new_page()
        total   = len(products)
        blocked = unavail = no_price = skipped = 0

        for i, (sku, name, url) in enumerate(products, 1):
            if resume and sku in existing:
                skipped += 1
                continue

            print(f'[{i:3d}/{total}] {sku:12s}  {name}', end=' ... ', flush=True)
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=20_000)
                time.sleep(2)
                status = check_page_status(page)
                if status == 'blocked':
                    print('BLOCKED')
                    blocked += 1
                    results[sku] = {'name': name, 'url': url, 'status': 'blocked', 'price': None}
                elif status == 'unavailable':
                    print('unavailable')
                    unavail += 1
                    results[sku] = {'name': name, 'url': url, 'status': 'unavailable', 'price': None}
                else:
                    price = extract_price(page)
                    if price:
                        print(f'${price}')
                        results[sku] = {'name': name, 'url': url, 'status': 'ok', 'price': price}
                    else:
                        print('no price found')
                        no_price += 1
                        results[sku] = {'name': name, 'url': url, 'status': 'no_price', 'price': None}
            except PlaywrightTimeout:
                print('TIMEOUT')
                results[sku] = {'name': name, 'url': url, 'status': 'timeout', 'price': None}
            except Exception as exc:
                print(f'ERROR: {exc}')
                results[sku] = {'name': name, 'url': url, 'status': 'error', 'price': None}

            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            time.sleep(2.5)

        context.close()
        browser.close()

    ok = sum(1 for v in results.values() if v['status'] == 'ok')
    print(
        f'\nDone.  Found: {ok}  Unavailable: {unavail}  '
        f'Blocked: {blocked}  No price: {no_price}  Skipped: {skipped}'
    )
    print(f'Results saved to {output_file}')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Scrape Amazon prices via Playwright (pulls URLs from DB).'
    )
    parser.add_argument(
        '--batch', type=int, choices=[1, 2, 3], default=None,
        help='Letter range to scrape: 1=A-C, 2=D-N, 3=O-Z',
    )
    parser.add_argument(
        '--resume', action='store_true',
        help='Skip SKUs already in the output JSON and continue from where you left off.',
    )
    parser.add_argument(
        '--sku', type=str, default=None,
        help='Scrape a single SKU regardless of batch (e.g. --sku 43-04).',
    )
    args = parser.parse_args()

    if not args.sku and args.batch is None:
        parser.error('Provide --batch (1/2/3) or --sku <gw_sku>.')

    # Set up Django now — DATABASE_URL must already be in the environment
    # (the run_amazon_browser_scrape.ps1 wrapper loads it from .env.production).
    import django
    django.setup()

    script_dir = os.path.dirname(os.path.abspath(__file__))

    if args.sku:
        products    = load_products(sku_filter=args.sku)
        safe_sku    = args.sku.replace('/', '_')
        output_file = os.path.join(script_dir, f'amazon_prices_sku_{safe_sku}.json')
    else:
        products    = load_products(batch_num=args.batch)
        label       = BATCH_LABELS[args.batch]
        print(f'Batch {args.batch} ({label}) — {len(products)} products loaded from DB.')
        output_file = os.path.join(script_dir, f'amazon_prices_batch{args.batch}.json')

    if products:
        scrape(products, output_file, resume=args.resume)
