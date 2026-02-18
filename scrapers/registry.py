"""
Central registry of all retailer scrapers.
Add new scrapers here so the management command can find them.
"""

from .retailers.example_retailer import ExampleRetailerScraper

SCRAPER_REGISTRY = {
    'example-store': ExampleRetailerScraper,
    # 'miniature-market': MiniatureMarketScraper,
    # 'element-games': ElementGamesScraper,
    # Add more scrapers here...
}
