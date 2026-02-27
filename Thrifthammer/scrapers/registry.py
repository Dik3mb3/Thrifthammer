"""
Central registry of all retailer scrapers.
Add new scrapers here so the management command can find them.
"""

from .retailers.example_retailer import ExampleRetailerScraper
from .retailers.miniature_market import MiniatureMarketScraper

SCRAPER_REGISTRY = {
    'example-store': ExampleRetailerScraper,
    'miniature-market': MiniatureMarketScraper,
    # eBay uses the official Finding API via update_ebay_prices command,
    # not the scraper framework. Run: python manage.py update_ebay_prices
}
