"""
Central registry of all retailer scrapers.
Add new scrapers here so the management command can find them.
"""

from .retailers.amazon import AmazonScraper
from .retailers.example_retailer import ExampleRetailerScraper
from .retailers.miniature_market import MiniatureMarketScraper
from .retailers.noble_knight import NoblekKnightScraper

SCRAPER_REGISTRY = {
    'amazon': AmazonScraper,
    'example-store': ExampleRetailerScraper,
    'miniature-market': MiniatureMarketScraper,
    'noble-knight-games': NoblekKnightScraper,
    # eBay uses the official Browse API via update_ebay_prices command,
    # not the scraper framework. Run: python manage.py update_ebay_prices
}
