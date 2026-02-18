"""
Example retailer scraper — use as a template for new scrapers.

To add a new retailer:
1. Copy this file and rename it (e.g. my_store.py)
2. Set retailer_slug to match the Retailer.slug in your DB
3. Implement scrape_products() to yield product dicts
4. Register the scraper in SCRAPER_REGISTRY (scrapers/registry.py)
"""

from scrapers.base import BaseScraper


class ExampleRetailerScraper(BaseScraper):
    retailer_slug = 'example-store'

    def scrape_products(self):
        # Example: scrape a product listing page
        # response = self.session.get('https://example-store.com/warhammer')
        # soup = BeautifulSoup(response.text, 'html.parser')
        # for card in soup.select('.product-card'):
        #     yield {
        #         'name': card.select_one('.title').text.strip(),
        #         'price': card.select_one('.price').text.strip('$'),
        #         'url': card.select_one('a')['href'],
        #         'in_stock': 'out-of-stock' not in card.get('class', []),
        #     }
        return iter([])  # placeholder — yields nothing
