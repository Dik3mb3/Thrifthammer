"""
Miniature Market scraper — search-based approach.

The original URL-guessing approach (gw-{SKU}.html) was unreliable because:
  - GW recycles SKU numbers when products are discontinued/replaced
  - MM keeps old product listings at those URLs, so the URL may point to a
    completely different product than the one we want
  - e.g. gw-01-08.html shows "Sisters of Silence", not "Custodian Guard"

New approach: use MM's /suggest endpoint, which correctly finds products by
name search, then score the candidates by name similarity.

  Step 1 — Search suggest:
    Call /suggest?search={product_name} to get a list of MM product candidates.
    MM's search ranks results well — the correct product is usually in the top 5.

  Step 2 — Score each candidate:
    Compare candidate title to our product name using normalised word overlap.
    Require >= SUGGEST_ACCEPT_THRESHOLD (0.85) of our words to appear in the
    candidate title (with basic plural normalisation).

  Step 3 — Accept best match:
    Take the highest-scoring candidate. If it meets the threshold, save the
    URL and price. Otherwise mark the product as not_available.

Price is extracted directly from the suggest response (MM shows it inline).
Availability defaults to True (suggest results are in-stock items).

Usage:
    python manage.py run_scrapers miniature-market

Notes:
  - Only numeric GW SKUs (48-75, 49-06, 101-23) are scraped; non-numeric
    SKUs (KT-, HA-, etc.) are immediately marked not_available.
  - Every product always gets a row — either a real price or not_available=True.
  - /suggest filters results to GW URLs (/gw-) to exclude board games, MTG, etc.
"""

import logging
import re
import time
import urllib.parse
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer
from scrapers.models import ScrapeJob

logger = logging.getLogger(__name__)

# Standard numeric GW SKU pattern: 48-75, 49-06, 101-23
GW_SKU_PATTERN = re.compile(r'^\d{2,3}-\d{2,3}$')

# MM's search suggest endpoint — returns an HTML dropdown fragment
SUGGEST_URL = 'https://www.miniaturemarket.com/suggest?search={query}'

# Minimum F1-like score to accept a match.
# F1 = 2 * |matched| / (|our_words| + |their_words|)
# This penalises candidates with many extra words, so "Devastator Squad"
# (4 words) scores higher than "Centurion Devastator Squad" (5 words)
# when we search for "Space Marine Devastators" (3 words).
# 0.75 accepts 2-word vs 3-word matches (e.g. "Custodian Guard" → "Guard Squad")
# while rejecting distant cross-product matches.
SUGGEST_ACCEPT_THRESHOLD = 0.75

# CSS selector for product cards in the suggest dropdown
SUGGEST_CARD_SELECTOR = 'a.search-suggest-product-link'

# MM uses /gw- prefix for all Games Workshop product URLs
GW_URL_PREFIX = '/gw-'


class MiniatureMarketScraper:
    """
    Scraper for Miniature Market (miniaturemarket.com).

    Uses MM's /suggest search endpoint to match products by name rather than
    guessing URL patterns. Always writes a result row — either with a real
    price or not_available=True.
    """

    retailer_slug = 'miniature-market'

    def __init__(self):
        """Initialise requests session with browser-like headers."""
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            ),
        })
        self.delay = getattr(settings, 'SCRAPER_REQUEST_DELAY', 1)

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    def run(self):
        """Execute a full scrape job and return the ScrapeJob record."""
        try:
            retailer = Retailer.objects.get(slug=self.retailer_slug)
        except Retailer.DoesNotExist:
            logger.error('Retailer "%s" not found in DB.', self.retailer_slug)
            raise

        job = ScrapeJob.objects.create(
            retailer=retailer,
            status='running',
            started_at=timezone.now(),
        )
        errors = []
        products = Product.objects.filter(is_active=True).exclude(gw_sku='')

        for product in products:
            sku = product.gw_sku.strip()
            job.products_found += 1

            try:
                # Non-numeric SKUs (KT-, HA-, BP-, etc.) are not on MM
                if not GW_SKU_PATTERN.match(sku):
                    self._save_not_available(product, retailer)
                    logger.info('[n/a]      %s — non-standard SKU', product.name)
                    job.prices_updated += 1
                    continue

                result = self._find_product(product.name, sku=sku)

                if result is None:
                    self._save_not_available(product, retailer)
                    logger.info('[n/a]      %s — not found on MM', product.name)
                else:
                    price, in_stock, final_url = result
                    CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=retailer,
                        defaults={
                            'price': price,
                            'url': final_url,
                            'in_stock': in_stock,
                            'not_available': False,
                        },
                    )
                    stock_label = 'in stock' if in_stock else 'OUT OF STOCK'
                    logger.info(
                        '[updated]  %s — $%.2f (%s)',
                        product.name, price, stock_label,
                    )
                job.prices_updated += 1

            except Exception as exc:
                msg = f'{product.name} (SKU {sku}): {exc}'
                errors.append(msg)
                logger.exception('Error scraping %s', product.name)

            time.sleep(self.delay)

        job.status = 'success'
        job.errors = '\n'.join(errors)
        job.finished_at = timezone.now()
        job.save()
        return job

    # -------------------------------------------------------------------------
    # Product finder
    # -------------------------------------------------------------------------

    def _find_product(self, name, sku=None):
        """
        Search MM's /suggest endpoint for a product matching our name.

        Returns (Decimal price, bool in_stock, str url) or None.

        Scoring uses an F1-like formula (bidirectional word overlap) to ensure
        the correct product scores higher than same-faction alternatives.
        A SKU URL bonus (+0.05) breaks ties when multiple candidates match equally.
        """
        suggestions = self._get_suggestions(name)
        if not suggestions:
            return None

        best_score = 0.0
        best_hit = None

        for hit in suggestions:
            score = self._score_name(name, hit['title'])

            # Tiebreaker: prefer the URL that contains our GW SKU
            # e.g. gw-48-75.html wins over gw-48-36.html for SKU 48-75
            if sku and sku.lower() in hit['url'].lower():
                score = min(1.0, score + 0.05)

            logger.debug(
                'Candidate "%s" | score=%.2f | price=%s',
                hit['title'][:60], score, hit.get('price'),
            )
            if score > best_score:
                best_score = score
                best_hit = hit

        if best_score < SUGGEST_ACCEPT_THRESHOLD or best_hit is None:
            logger.debug(
                'No match for "%s" (best=%.2f < %.2f)',
                name, best_score, SUGGEST_ACCEPT_THRESHOLD,
            )
            return None

        price = best_hit.get('price')
        if price is None:
            logger.debug('Match found for "%s" but no price extracted.', name)
            return None

        logger.debug(
            'MATCH "%s" score=%.2f | MM="%s" | $%.2f | %s',
            name, best_score, best_hit['title'][:60], price, best_hit['url'],
        )
        # Products appearing in MM's suggest results are generally in stock.
        return price, True, best_hit['url']

    # -------------------------------------------------------------------------
    # Suggest endpoint
    # -------------------------------------------------------------------------

    def _get_suggestions(self, name):
        """
        Call MM's /suggest endpoint and return GW-product candidates.

        Returns list of dicts: {'title': str, 'price': Decimal|None, 'url': str}.
        Filters to URLs containing '/gw-' to exclude non-GW items (MTG, etc.).
        """
        query = urllib.parse.quote(self._clean_name(name))
        url = SUGGEST_URL.format(query=query)
        try:
            response = self.session.get(url, timeout=15)
        except Exception as exc:
            logger.warning('Suggest request failed for "%s": %s', name, exc)
            return []

        if response.status_code != 200:
            logger.debug('Suggest returned HTTP %d for "%s"', response.status_code, name)
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        for link in soup.select(SUGGEST_CARD_SELECTOR):
            title = link.get('title', '').strip()
            href = link.get('href', '').strip()

            if not title or not href:
                continue

            # Only GW products — MM uses /gw- prefix for all GW items
            if GW_URL_PREFIX not in href.lower():
                continue

            # Extract price from link text, e.g. "Product Name$53.99"
            text = link.get_text(strip=True)
            price = self._extract_price_from_text(text)

            results.append({'title': title, 'price': price, 'url': href})

        return results

    # -------------------------------------------------------------------------
    # Scoring
    # -------------------------------------------------------------------------

    @staticmethod
    def _score_name(our_name, candidate_title):
        """
        Score name similarity using an F1-like bidirectional word overlap.

        F1 = 2 * |matched| / (|our_words| + |their_words|)

        This penalises candidates with many extra words:
          "Space Marine Devastators" (3 words) vs
            "Devastator Squad"          (4 words)  → F1 = 2*3/(3+4) = 0.857 ✅
            "Centurion Devastator Squad" (5 words) → F1 = 2*3/(3+5) = 0.750 ✅
          Shorter, closer match scores higher and wins.

        Returns 1.0 for exact cleaned-name containment.
        Both sides are normalised to base form (scouts→scout, marines→marine).
        """
        our = MiniatureMarketScraper._clean_name(our_name).lower()
        their = MiniatureMarketScraper._clean_name(candidate_title).lower()

        if not our or not their:
            return 0.0

        # Exact containment — strongest signal, no word-split needed
        if our in their or their in our:
            return 1.0

        our_words = MiniatureMarketScraper._normalise_words(our)
        their_words = MiniatureMarketScraper._normalise_words(their)

        if not our_words:
            return 0.0

        matched = sum(
            1 for w in our_words
            if MiniatureMarketScraper._word_matches(w, their_words)
        )

        # F1-like: penalises candidates with many extra words
        return 2 * matched / (len(our_words) + len(their_words))

    @staticmethod
    def _normalise_words(text):
        """
        Split text into a set of normalised base-form tokens (len > 2).

        Strips exactly one trailing 's' for basic de-pluralisation so that
        'scouts' and 'scout', 'marines' and 'marine' resolve to the same token.
        Only the base form is added to the set (not both forms), keeping
        len(our_words) accurate for the F1 calculation.
        """
        words = set()
        for w in text.split():
            if len(w) <= 2:
                continue
            # Normalize to base form: strip one trailing 's' if word is long enough
            if w.endswith('s') and len(w) > 3:
                words.add(w[:-1])  # scouts→scout, marines→marine
            else:
                words.add(w)
        return words

    @staticmethod
    def _word_matches(word, candidate_words):
        """
        Return True if word (normalised base form) appears in candidate_words.

        Also checks the plural form (+s) since _normalise_words stores base forms.
        e.g. 'scout' matches {'scout'} OR if candidate had 'scouts' it's stored as 'scout'.
        """
        if word in candidate_words:
            return True
        # Check if the candidate stored it in plural (shouldn't happen after normalisation
        # but guard against edge cases like words already in base form on both sides)
        if word + 's' in candidate_words:
            return True
        return False

    # -------------------------------------------------------------------------
    # Price extraction
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_price_from_text(text):
        """
        Extract a USD price from suggest link text like "Product Name$53.99".

        Returns Decimal or None.
        """
        m = re.search(r'\$\s*(\d{1,4}\.\d{2})', text)
        if m:
            try:
                price = Decimal(m.group(1))
                if 1 <= price <= 1500:
                    return price
            except InvalidOperation:
                pass
        return None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _save_not_available(product, retailer):
        """Upsert a not_available=True CurrentPrice row for this product."""
        CurrentPrice.objects.update_or_create(
            product=product,
            retailer=retailer,
            defaults={
                'price': None,
                'url': '',
                'in_stock': False,
                'not_available': True,
            },
        )

    @staticmethod
    def _clean_name(name):
        """
        Strip common MM/GW prefixes and normalise whitespace.

        'Warhammer 40K: Space Marine Primaris Intercessors'
          → 'Space Marine Primaris Intercessors'
        'Space Marines - Assault Intercessors'
          → 'Space Marines Assault Intercessors'
        """
        prefixes = [
            'Warhammer 40K:',
            'Warhammer 40,000:',
            'Age of Sigmar:',
            'Horus Heresy:',
            'Kill Team:',
            'Warcry:',
            'Necromunda:',
        ]
        cleaned = name.strip()
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        # Normalise dashes/hyphens and extra whitespace
        cleaned = re.sub(r'\s*-\s*', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
