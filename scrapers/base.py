"""
Base scraper class. Each retailer gets its own subclass.
"""

import logging
import time
from decimal import Decimal

import requests
from django.conf import settings
from django.utils import timezone

from prices.models import CurrentPrice, PriceHistory
from products.models import Product, Retailer

from .models import ScrapeJob

logger = logging.getLogger(__name__)


class BaseScraper:
    """
    Override `retailer_slug` and `scrape_products()` in subclasses.

    scrape_products() should yield dicts:
        {
            'name': str,
            'sku': str,       # optional, for matching existing products
            'price': Decimal,
            'url': str,
            'in_stock': bool,
        }
    """
    retailer_slug: str = ''

    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = getattr(
            settings, 'SCRAPER_USER_AGENT', 'Thrifthammer/1.0'
        )
        self.delay = getattr(settings, 'SCRAPER_REQUEST_DELAY', 2)

    def get_retailer(self):
        return Retailer.objects.get(slug=self.retailer_slug)

    def run(self):
        """Execute a full scrape job."""
        retailer = self.get_retailer()
        job = ScrapeJob.objects.create(retailer=retailer, status='running', started_at=timezone.now())
        errors = []

        try:
            for item in self.scrape_products():
                job.products_found += 1
                try:
                    self._update_price(retailer, item)
                    job.prices_updated += 1
                except Exception as exc:
                    errors.append(f"{item.get('name', '?')}: {exc}")
                    logger.exception("Error updating price for %s", item.get('name'))
                time.sleep(self.delay)

            job.status = 'success'
        except Exception as exc:
            job.status = 'failed'
            errors.append(str(exc))
            logger.exception("Scrape job failed for %s", retailer.name)
        finally:
            job.errors = '\n'.join(errors)
            job.finished_at = timezone.now()
            job.save()

        return job

    def scrape_products(self):
        """Yield product dicts. Override in subclasses."""
        raise NotImplementedError

    @staticmethod
    def _update_price(retailer, item):
        """Upsert CurrentPrice and append PriceHistory."""
        price = Decimal(str(item['price']))

        # Try matching by SKU first, then name
        product = None
        if item.get('sku'):
            product = Product.objects.filter(gw_sku=item['sku']).first()
        if not product:
            product = Product.objects.filter(name__iexact=item['name']).first()
        if not product:
            # Auto-create if not found
            from django.utils.text import slugify
            product = Product.objects.create(
                name=item['name'],
                slug=slugify(item['name'])[:300],
                gw_sku=item.get('sku', ''),
            )

        CurrentPrice.objects.update_or_create(
            product=product,
            retailer=retailer,
            defaults={
                'price': price,
                'url': item['url'],
                'in_stock': item.get('in_stock', True),
            },
        )

        PriceHistory.objects.create(
            product=product,
            retailer=retailer,
            price=price,
            in_stock=item.get('in_stock', True),
        )
