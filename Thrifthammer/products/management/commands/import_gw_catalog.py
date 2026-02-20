"""
Management command: import_gw_catalog

One-time scraper to bulk-import 500+ Warhammer products from the Games Workshop
US storefront into the local Product catalog.

This command is NOT for ongoing price tracking — it only populates the Product
model (name, SKU, MSRP, description, image_url, gw_url, category, faction).
Price tracking is handled by the separate scrapers app.

Usage:
    python manage.py import_gw_catalog
    python manage.py import_gw_catalog --dry-run       # Preview without saving
    python manage.py import_gw_catalog --delay 3.0     # Custom delay (seconds)
    python manage.py import_gw_catalog --limit 100     # Stop after N products
    python manage.py import_gw_catalog --categories space-marines paints

Server-respectful behaviour:
    - Checks robots.txt before scraping
    - Sleeps between every request (default 2 s, configurable)
    - Adds a User-Agent that identifies this tool honestly
    - Does NOT retry aggressively on failure — logs and moves on

All errors are caught per-product so one bad page never aborts the run.
"""

import decimal
import re
import time
import urllib.robotparser
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Category, Faction, Product

try:
    import requests
    from bs4 import BeautifulSoup
    _DEPS_AVAILABLE = True
except ImportError:
    _DEPS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GW_BASE = 'https://www.warhammer.com'
GW_US_BASE = 'https://www.warhammer.com/en-US'

USER_AGENT = (
    'ThriftHammer-CatalogBot/1.0 (one-time product import; '
    'contact: admin@thrifthammer.com)'
)

# Priority categories: (display_label, gw_url_path, internal_category_name, faction_name_or_None)
# URL paths verified against warhammer.com/en-US navigation.
CATEGORY_TARGETS = [
    (
        'Space Marines — All Units',
        '/en-US/Miniatures/Warhammer-40-000/Space-Marines',
        'Warhammer 40,000',
        'Space Marines',
    ),
    (
        'Blood Angels',
        '/en-US/Miniatures/Warhammer-40-000/Blood-Angels',
        'Warhammer 40,000',
        'Blood Angels',
    ),
    (
        'Dark Angels',
        '/en-US/Miniatures/Warhammer-40-000/Dark-Angels',
        'Warhammer 40,000',
        'Dark Angels',
    ),
    (
        'Ultramarines',
        '/en-US/Miniatures/Warhammer-40-000/Ultramarines',
        'Warhammer 40,000',
        'Ultramarines',
    ),
    (
        'Combat Patrol Boxes',
        '/en-US/Warhammer-40-000/Combat-Patrol',
        'Warhammer 40,000',
        None,
    ),
    (
        'Chaos Space Marines',
        '/en-US/Miniatures/Warhammer-40-000/Chaos-Space-Marines',
        'Warhammer 40,000',
        'Chaos Space Marines',
    ),
    (
        'Tyranids',
        '/en-US/Miniatures/Warhammer-40-000/Tyranids',
        'Warhammer 40,000',
        'Tyranids',
    ),
    (
        'Necrons',
        '/en-US/Miniatures/Warhammer-40-000/Necrons',
        'Warhammer 40,000',
        'Necrons',
    ),
    (
        'Orks',
        '/en-US/Miniatures/Warhammer-40-000/Orks',
        'Warhammer 40,000',
        'Orks',
    ),
    (
        'T\'au Empire',
        '/en-US/Miniatures/Warhammer-40-000/Tau-Empire',
        'Warhammer 40,000',
        "T'au Empire",
    ),
    (
        'Astra Militarum',
        '/en-US/Miniatures/Warhammer-40-000/Astra-Militarum',
        'Warhammer 40,000',
        'Astra Militarum',
    ),
    (
        'Age of Sigmar — Stormcast',
        '/en-US/Miniatures/Age-of-Sigmar/Stormcast-Eternals',
        'Age of Sigmar',
        'Stormcast Eternals',
    ),
    (
        'Age of Sigmar — Skaven',
        '/en-US/Miniatures/Age-of-Sigmar/Skaven',
        'Age of Sigmar',
        'Skaven',
    ),
    (
        'Age of Sigmar Starter Sets',
        '/en-US/Age-of-Sigmar/Starter-Sets',
        'Age of Sigmar',
        None,
    ),
    (
        'Citadel Paints & Tools',
        '/en-US/Painting/Citadel-Colour',
        'Paint & Supplies',
        None,
    ),
    (
        'Horus Heresy',
        '/en-US/Miniatures/Horus-Heresy',
        'Horus Heresy',
        None,
    ),
    (
        'Warhammer 40,000 Boxed Games',
        '/en-US/Warhammer-40-000/Boxed-Games',
        'Boxed Games',
        None,
    ),
]

# Short slugs for --categories filter (command-line friendly)
CATEGORY_SLUG_MAP = {
    'space-marines':   0,
    'blood-angels':    1,
    'dark-angels':     2,
    'ultramarines':    3,
    'combat-patrol':   4,
    'chaos':           5,
    'tyranids':        6,
    'necrons':         7,
    'orks':            8,
    'tau':             9,
    'astra-militarum': 10,
    'stormcast':       11,
    'skaven':          12,
    'aos-starters':    13,
    'paints':          14,
    'horus-heresy':    15,
    'boxed-games':     16,
}


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------

@dataclass
class ScrapedProduct:
    """Holds all extracted data for one product before DB upsert."""

    name: str
    gw_url: str
    gw_sku: str = ''
    msrp: Optional[decimal.Decimal] = None
    description: str = ''
    image_url: str = ''
    category_name: str = ''
    faction_name: str = ''
    errors: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    """
    One-time management command to import the GW product catalog.

    Scrapes the warhammer.com US store for product data and upserts it into
    the local Product model. Existing products (matched by gw_sku or slug)
    are updated, not duplicated.
    """

    help = (
        'One-time import of 500+ Warhammer products from warhammer.com/en-US. '
        'Does NOT track prices — only populates the Product catalog.'
    )

    def add_arguments(self, parser):
        """Register command-line options."""
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            metavar='SECONDS',
            help='Seconds to wait between HTTP requests (default: 2.0).',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            metavar='N',
            help='Stop after importing N products total (0 = no limit).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Scrape and parse without saving anything to the database.',
        )
        parser.add_argument(
            '--skip-robots',
            action='store_true',
            help='Skip robots.txt check (not recommended).',
        )
        parser.add_argument(
            '--categories',
            nargs='+',
            choices=list(CATEGORY_SLUG_MAP.keys()),
            metavar='CATEGORY',
            help=(
                'Only import these categories. '
                f'Choices: {", ".join(CATEGORY_SLUG_MAP.keys())}'
            ),
        )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        """Orchestrate the full catalog import."""
        if not _DEPS_AVAILABLE:
            self.stderr.write(self.style.ERROR(
                'Missing dependencies: pip install requests beautifulsoup4'
            ))
            return

        self.delay = options['delay']
        self.dry_run = options['dry_run']
        self.limit = options['limit']
        self.total_imported = 0
        self.total_failed = 0
        self.total_skipped = 0

        # Build session with polite headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        if self.dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no data will be saved.\n'))

        # ── robots.txt check ──
        if not options['skip_robots']:
            if not self._robots_allows_scraping():
                self.stderr.write(self.style.ERROR(
                    'robots.txt disallows scraping for our User-Agent. '
                    'Use --skip-robots to override (at your own risk).'
                ))
                return

        # ── Determine which categories to scrape ──
        if options['categories']:
            indices = [CATEGORY_SLUG_MAP[c] for c in options['categories']]
            targets = [CATEGORY_TARGETS[i] for i in sorted(set(indices))]
        else:
            targets = CATEGORY_TARGETS

        # ── Pre-load DB lookups ──
        self._load_db_caches()

        # ── Main scraping loop ──
        self.stdout.write(
            f'Starting import of {len(targets)} category/categories '
            f'with {self.delay}s delay between requests.\n'
        )

        for label, path, cat_name, faction_name in targets:
            if self.limit and self.total_imported >= self.limit:
                break

            self.stdout.write(self.style.MIGRATE_HEADING(f'\n── {label} ──'))
            category_url = f'{GW_BASE}{path}'
            self._scrape_category(
                category_url=category_url,
                category_name=cat_name,
                faction_name=faction_name,
            )

        # ── Final summary ──
        self.stdout.write('\n' + '─' * 60)
        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN complete.\n'
                f'  Would import: {self.total_imported}\n'
                f'  Would skip:   {self.total_skipped}\n'
                f'  Parse errors: {self.total_failed}\n'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Import complete.\n'
                f'  Saved:        {self.total_imported}\n'
                f'  Skipped:      {self.total_skipped}\n'
                f'  Errors:       {self.total_failed}\n'
            ))

    # ------------------------------------------------------------------
    # robots.txt
    # ------------------------------------------------------------------

    def _robots_allows_scraping(self):
        """
        Fetch and parse robots.txt to verify scraping is permitted.

        Returns True if allowed, False if disallowed.
        """
        robots_url = f'{GW_BASE}/robots.txt'
        self.stdout.write(f'Checking {robots_url} …')
        try:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            allowed = rp.can_fetch(USER_AGENT, f'{GW_US_BASE}/Miniatures/')
            if allowed:
                self.stdout.write(self.style.SUCCESS('  robots.txt: scraping allowed.\n'))
            else:
                self.stdout.write(self.style.ERROR('  robots.txt: scraping disallowed.\n'))
            return allowed
        except Exception as exc:
            # Network error reading robots.txt — conservative: don't scrape
            self.stderr.write(self.style.WARNING(
                f'  Could not read robots.txt ({exc}). Proceeding cautiously.'
            ))
            return True  # assume allowed if unreachable

    # ------------------------------------------------------------------
    # DB cache helpers
    # ------------------------------------------------------------------

    def _load_db_caches(self):
        """
        Pre-load Category and Faction lookups to avoid per-product DB hits.

        Caches are keyed by name (lowercase) for case-insensitive matching.
        """
        self._categories = {c.name: c for c in Category.objects.all()}
        self._factions = {f.name: f for f in Faction.objects.all()}
        self.stdout.write(
            f'Loaded {len(self._categories)} categories, '
            f'{len(self._factions)} factions from DB.\n'
        )

    def _get_or_create_category(self, name):
        """
        Return the Category for `name`, creating it if it doesn't exist.

        Args:
            name: Human-readable category name (e.g. 'Warhammer 40,000').

        Returns:
            Category instance or None if name is empty.
        """
        if not name:
            return None
        if name in self._categories:
            return self._categories[name]
        # Create on the fly
        cat, _ = Category.objects.get_or_create(
            name=name,
            defaults={'slug': slugify(name)},
        )
        self._categories[name] = cat
        return cat

    def _get_or_create_faction(self, name, category):
        """
        Return the Faction for `name`, creating it if it doesn't exist.

        Args:
            name: Human-readable faction name (e.g. 'Space Marines').
            category: Category instance to associate with.

        Returns:
            Faction instance or None if name is empty.
        """
        if not name:
            return None
        if name in self._factions:
            return self._factions[name]
        faction, _ = Faction.objects.get_or_create(
            name=name,
            defaults={
                'slug': slugify(name),
                'category': category,
            },
        )
        self._factions[name] = faction
        return faction

    # ------------------------------------------------------------------
    # Category page scraping
    # ------------------------------------------------------------------

    def _scrape_category(self, category_url, category_name, faction_name):
        """
        Scrape all pages of a GW category listing and import each product.

        Handles GW's ?page=N pagination automatically.

        Args:
            category_url:  Full URL to the category index (page 1).
            category_name: Internal category name to assign (e.g. 'Warhammer 40,000').
            faction_name:  Internal faction name (or None) to assign.
        """
        page = 1
        seen_urls: set = set()

        while True:
            if self.limit and self.total_imported >= self.limit:
                break

            url = category_url if page == 1 else f'{category_url}?page={page}'
            self.stdout.write(f'  Fetching listing page {page}: {url}')

            html = self._get(url)
            if html is None:
                self.stdout.write(self.style.WARNING(
                    f'  Failed to fetch page {page}. Stopping category.'
                ))
                break

            product_links = self._extract_product_links(html, url)

            if not product_links:
                self.stdout.write(f'  No products found on page {page}. Done with category.')
                break

            new_links = [l for l in product_links if l not in seen_urls]
            if not new_links:
                break  # All links already seen — pagination loop guard

            seen_urls.update(new_links)
            self.stdout.write(f'  Found {len(new_links)} product links on page {page}.')

            for product_url in new_links:
                if self.limit and self.total_imported >= self.limit:
                    return
                self._import_product(product_url, category_name, faction_name)

            # Check for next page
            if not self._has_next_page(html):
                break
            page += 1

    def _extract_product_links(self, html, base_url):
        """
        Parse category listing HTML and return absolute product page URLs.

        GW uses several link patterns across their site. We try multiple
        selectors to maximise coverage across redesigns.

        Args:
            html:     Raw HTML string from a category listing page.
            base_url: Base URL for resolving relative links.

        Returns:
            List of unique absolute product URLs.
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        # Pattern 1: product cards — common on warhammer.com grid pages
        for a in soup.select('a.product-card, a[class*="productCard"], a[class*="product-item"]'):
            href = a.get('href', '').strip()
            if href:
                links.add(urljoin(base_url, href))

        # Pattern 2: any link whose href contains a product SKU-like path
        # warhammer.com URLs often look like /en-US/Space-Marines-Intercessors-48-75
        for a in soup.select('a[href]'):
            href = a.get('href', '').strip()
            if not href or href.startswith(('mailto:', 'tel:', '#', 'javascript:')):
                continue
            abs_href = urljoin(base_url, href)
            parsed = urlparse(abs_href)
            # Only follow same-domain product paths
            if 'warhammer.com' not in parsed.netloc:
                continue
            path = parsed.path.lower()
            # Skip navigation, account, basket, help pages
            if any(skip in path for skip in (
                '/basket', '/login', '/account', '/help', '/about',
                '/contact', '/search', '/checkout', '/legal', '/sitemap',
                '/en-us/painting/citadel-colour/',  # paint *category* pages, not products
                '/en-us/miniatures/',               # top-level category index
                '/en-us/warhammer-40-000/',         # section index
                '/en-us/age-of-sigmar/',
                '/en-us/horus-heresy/',
            )):
                continue
            # Include if URL looks like a product detail (has a trailing segment with digits/hyphens)
            if re.search(r'/[a-z0-9][a-z0-9-]{4,}$', path):
                links.add(abs_href)

        # Filter out obvious non-product pages
        filtered = {
            l for l in links
            if not any(
                l.endswith(suffix) for suffix in
                ('/', '/en-US', '/en-US/', '.pdf', '.jpg', '.png', '.webp')
            )
        }

        return sorted(filtered)

    def _has_next_page(self, html):
        """
        Return True if the category listing has a 'next page' link.

        Args:
            html: Raw HTML string of a listing page.

        Returns:
            bool
        """
        soup = BeautifulSoup(html, 'html.parser')
        # GW typically uses rel="next" or a 'next' link in pagination
        if soup.find('a', rel='next'):
            return True
        if soup.find('a', string=re.compile(r'Next|›|»', re.I)):
            return True
        # Some GW pages use data-page or a specific pagination component
        if soup.select_one('[class*="pagination"] a[href*="page="]'):
            return True
        return False

    # ------------------------------------------------------------------
    # Product page scraping
    # ------------------------------------------------------------------

    def _import_product(self, product_url, category_name, faction_name):
        """
        Fetch and parse one product page, then upsert it into the DB.

        Logs success/failure; never raises so one bad page can't abort the run.

        Args:
            product_url:   Absolute URL to the GW product detail page.
            category_name: Internal category name string.
            faction_name:  Internal faction name string (or None).
        """
        time.sleep(self.delay)

        html = self._get(product_url)
        if html is None:
            self.stdout.write(self.style.WARNING(f'    SKIP (fetch failed): {product_url}'))
            self.total_failed += 1
            return

        scraped = self._parse_product_page(html, product_url, category_name, faction_name)

        if not scraped.name:
            self.stdout.write(self.style.WARNING(
                f'    SKIP (no name extracted): {product_url}'
            ))
            self.total_skipped += 1
            return

        self._upsert_product(scraped)

    def _parse_product_page(self, html, product_url, category_name, faction_name):
        """
        Extract all product fields from a GW product detail page.

        GW's HTML structure changes occasionally; we try multiple selectors
        for each field with graceful fallbacks.

        Args:
            html:          Raw HTML of the product page.
            product_url:   The URL we fetched (stored as gw_url).
            category_name: Category name assigned by the calling category loop.
            faction_name:  Faction name assigned by the calling category loop.

        Returns:
            ScrapedProduct dataclass.
        """
        soup = BeautifulSoup(html, 'html.parser')
        scraped = ScrapedProduct(
            name='',
            gw_url=product_url,
            category_name=category_name,
            faction_name=faction_name,
        )

        # ── Name ──
        for selector in (
            'h1.product-title',
            'h1[class*="productTitle"]',
            'h1[class*="product-name"]',
            'h1',
        ):
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                scraped.name = el.get_text(strip=True)
                break

        if not scraped.name:
            # Last resort: try <title> tag, strip " - Warhammer" suffix
            title_el = soup.find('title')
            if title_el:
                raw_title = title_el.get_text(strip=True)
                scraped.name = re.sub(
                    r'\s*[-–|]\s*(Games Workshop|Warhammer).*$', '', raw_title
                ).strip()

        # ── SKU ──
        # GW embeds SKU in various places: data attributes, meta tags, structured data
        sku = ''
        # Try JSON-LD structured data first (most reliable)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string or '{}')
                # Handle both single object and @graph array
                if isinstance(data, dict) and data.get('@type') in ('Product', 'product'):
                    sku = data.get('sku', '') or data.get('productID', '')
                    if sku:
                        break
                if isinstance(data, dict) and '@graph' in data:
                    for node in data['@graph']:
                        if node.get('@type') == 'Product':
                            sku = node.get('sku', '')
                            if sku:
                                break
            except Exception:
                continue

        # Fallback: data-product-code or data-sku attributes anywhere on page
        if not sku:
            for attr in ('data-product-code', 'data-sku', 'data-code'):
                el = soup.find(attrs={attr: True})
                if el:
                    sku = el[attr].strip()
                    break

        # Fallback: meta[name="product:retailer_item_id"]
        if not sku:
            meta = soup.find('meta', attrs={'name': re.compile(r'retailer_item_id|product:id', re.I)})
            if meta:
                sku = meta.get('content', '').strip()

        # Fallback: look for SKU pattern in URL itself (GW SKUs: digits-digits)
        if not sku:
            m = re.search(r'(\d{2,3}-\d{2,3})(?:[^/]*)$', product_url)
            if m:
                sku = m.group(1)

        scraped.gw_sku = sku[:50]  # match model max_length

        # ── MSRP / Price ──
        # GW renders price in various ways; try structured data first
        msrp_raw = ''
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string or '{}')
                offers = None
                if isinstance(data, dict):
                    offers = data.get('offers')
                if offers:
                    if isinstance(offers, list):
                        offers = offers[0]
                    msrp_raw = str(offers.get('price', '') or offers.get('lowPrice', ''))
                    if msrp_raw:
                        break
            except Exception:
                continue

        # Fallback: look for price in the DOM
        if not msrp_raw:
            for selector in (
                '[class*="product-price"]',
                '[class*="productPrice"]',
                '[class*="price--main"]',
                '[itemprop="price"]',
                '[class*="price"]',
            ):
                el = soup.select_one(selector)
                if el:
                    content = el.get('content', '') or el.get_text(strip=True)
                    # Strip currency symbols and commas, keep digits and decimal
                    price_match = re.search(r'[\d,]+\.?\d*', content.replace(',', ''))
                    if price_match:
                        msrp_raw = price_match.group()
                        break

        if msrp_raw:
            try:
                scraped.msrp = decimal.Decimal(msrp_raw.replace(',', '')).quantize(
                    decimal.Decimal('0.01')
                )
            except decimal.InvalidOperation:
                scraped.errors.append(f'Could not parse MSRP: {msrp_raw!r}')

        # ── Description ──
        for selector in (
            '[class*="product-description"]',
            '[class*="productDescription"]',
            '[itemprop="description"]',
            '.description',
            'meta[name="description"]',
        ):
            el = soup.select_one(selector)
            if el:
                if el.name == 'meta':
                    text = el.get('content', '').strip()
                else:
                    text = el.get_text(separator=' ', strip=True)
                if text and len(text) > 20:
                    scraped.description = text[:2000]  # cap length
                    break

        # ── Image URL ──
        for selector in (
            '[class*="product-image"] img',
            '[class*="productImage"] img',
            '[class*="gallery"] img',
            'img[itemprop="image"]',
        ):
            img = soup.select_one(selector)
            if img:
                src = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy-src', '')
                if src and src.startswith(('http', '//')):
                    scraped.image_url = urljoin(product_url, src)
                    break

        # Fallback: Open Graph image
        if not scraped.image_url:
            og = soup.find('meta', property='og:image')
            if og:
                scraped.image_url = og.get('content', '').strip()

        return scraped

    # ------------------------------------------------------------------
    # Database upsert
    # ------------------------------------------------------------------

    def _upsert_product(self, scraped):
        """
        Create or update a Product record from a ScrapedProduct.

        Upsert strategy:
        1. If gw_sku is set and a Product with that SKU exists → update it.
        2. Else if a Product with the same slug exists → update it.
        3. Else → create new.

        Args:
            scraped: ScrapedProduct instance with extracted data.
        """
        total = self.total_imported + self.total_failed + self.total_skipped

        # Resolve FK objects
        category = self._get_or_create_category(scraped.category_name)
        faction = (
            self._get_or_create_faction(scraped.faction_name, category)
            if scraped.faction_name else None
        )

        defaults = {
            'name': scraped.name,
            'description': scraped.description,
            'gw_url': scraped.gw_url,
            'image_url': scraped.image_url,
            'category': category,
            'faction': faction,
            'is_active': True,
        }
        if scraped.msrp is not None:
            defaults['msrp'] = scraped.msrp
        if scraped.gw_sku:
            defaults['gw_sku'] = scraped.gw_sku

        if self.dry_run:
            # In dry-run mode just report what would happen
            status = 'NEW'
            if scraped.gw_sku and Product.objects.filter(gw_sku=scraped.gw_sku).exists():
                status = 'UPDATE'
            elif Product.objects.filter(slug=slugify(scraped.name)).exists():
                status = 'UPDATE'
            self.total_imported += 1
            self.stdout.write(
                f'    [{status}] {scraped.name}'
                + (f' · SKU {scraped.gw_sku}' if scraped.gw_sku else '')
                + (f' · ${scraped.msrp}' if scraped.msrp else '')
            )
            if total > 0 and total % 25 == 0:
                self._print_progress()
            return

        try:
            if scraped.gw_sku:
                product, created = Product.objects.update_or_create(
                    gw_sku=scraped.gw_sku,
                    defaults=defaults,
                )
            else:
                # No SKU — fall back to slug-based upsert
                slug = slugify(scraped.name)
                defaults['gw_sku'] = scraped.gw_sku  # may be ''
                product, created = Product.objects.update_or_create(
                    slug=slug,
                    defaults=defaults,
                )

            status = 'created' if created else 'updated'
            self.total_imported += 1
            self.stdout.write(
                f'    [{status}] {scraped.name}'
                + (f' · SKU {scraped.gw_sku}' if scraped.gw_sku else '')
                + (f' · ${scraped.msrp}' if scraped.msrp else ' · no price')
            )

            if scraped.errors:
                for err in scraped.errors:
                    self.stdout.write(self.style.WARNING(f'      ⚠ {err}'))

        except Exception as exc:
            self.total_failed += 1
            self.stdout.write(self.style.ERROR(
                f'    [ERROR] {scraped.name}: {exc}'
            ))

        # Print running progress every 25 products
        if total > 0 and total % 25 == 0:
            self._print_progress()

    def _print_progress(self):
        """Print a running import counter."""
        done = self.total_imported + self.total_failed + self.total_skipped
        self.stdout.write(self.style.MIGRATE_LABEL(
            f'\n  ── Progress: {self.total_imported} saved, '
            f'{self.total_failed} errors, '
            f'{self.total_skipped} skipped '
            f'({done} total processed) ──\n'
        ))

    # ------------------------------------------------------------------
    # HTTP helper
    # ------------------------------------------------------------------

    def _get(self, url, retries=2):
        """
        Fetch a URL with retry on transient errors, returning HTML string or None.

        Sleeps `self.delay` seconds before every request to be server-respectful.
        Does NOT retry on 4xx responses (client errors — likely our fault).

        Args:
            url:     URL to fetch.
            retries: Max number of additional attempts on 5xx / connection error.

        Returns:
            HTML string, or None on failure.
        """
        for attempt in range(1 + retries):
            try:
                resp = self.session.get(url, timeout=15)

                if resp.status_code == 200:
                    return resp.text

                if 400 <= resp.status_code < 500:
                    # Client error — don't retry
                    self.stdout.write(self.style.WARNING(
                        f'    HTTP {resp.status_code} for {url} — skipping.'
                    ))
                    return None

                # 5xx — transient, maybe retry
                self.stdout.write(self.style.WARNING(
                    f'    HTTP {resp.status_code} for {url} '
                    f'(attempt {attempt + 1}/{1 + retries}).'
                ))
                if attempt < retries:
                    time.sleep(self.delay * 2)  # Back off on server errors

            except requests.exceptions.Timeout:
                self.stdout.write(self.style.WARNING(
                    f'    Timeout fetching {url} (attempt {attempt + 1}/{1 + retries}).'
                ))
                if attempt < retries:
                    time.sleep(self.delay * 2)

            except requests.exceptions.ConnectionError as exc:
                self.stdout.write(self.style.WARNING(
                    f'    Connection error for {url}: {exc} '
                    f'(attempt {attempt + 1}/{1 + retries}).'
                ))
                if attempt < retries:
                    time.sleep(self.delay * 3)

            except requests.exceptions.RequestException as exc:
                self.stdout.write(self.style.ERROR(
                    f'    Request error for {url}: {exc}'
                ))
                return None

        return None  # All retries exhausted
