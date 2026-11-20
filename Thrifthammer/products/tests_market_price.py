"""
Tests for the Average Market Price (Product.market_price / uses_market_price).

Out-of-print products have no MSRP, so they show the median of the prices tracked
at US retailers instead. refresh_market_prices calculates it; the product pages
label it "Avg Market Price" with a footnote, and only where a category is chosen.

Run with: python manage.py test products.tests_market_price --settings=thrifthammer.test_settings
"""

import datetime
import decimal
import re
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from prices.models import CurrentPrice, PriceHistory
from products.management.commands.refresh_market_prices import median_price
from products.models import Category, Product, Retailer
from products.tests import _TEST_STORAGES

D = decimal.Decimal
NOTE = 'Average Market Price: the median of the prices we have tracked at US retailers'


def _text(response):
    """Return the page as plain text with tags removed and whitespace collapsed."""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', response.content.decode()))


class MedianPriceTest(SimpleTestCase):
    """median_price: whole cents, half a cent rounds up, empty gives None."""

    def test_empty_has_no_median(self):
        """No prices, no median."""
        self.assertIsNone(median_price([]))

    def test_odd_count_takes_the_middle_price(self):
        """The middle of three prices is the median."""
        self.assertEqual(median_price([D('60.00'), D('40.00'), D('50.00')]), D('50.00'))

    def test_even_count_averages_the_middle_two_and_rounds_half_up(self):
        """10.00 and 11.01 average 10.505, which rounds up to 10.51."""
        self.assertEqual(median_price([D('10.00'), D('11.01')]), D('10.51'))


class RefreshMarketPricesTest(TestCase):
    """The refresh_market_prices command."""

    def setUp(self):
        """Create four retailers (one UK) and one product ticked uses_market_price."""
        self.today = timezone.localdate()
        self.ebay = Retailer.objects.create(name='eBay', slug='ebay', website='https://ebay.com')
        self.amazon = Retailer.objects.create(name='Amazon', slug='amazon', website='https://amazon.com')
        self.nk = Retailer.objects.create(name='Noble Knight', slug='noble-knight-games', website='https://nobleknight.com')
        self.uk = Retailer.objects.create(name='eBay UK', slug='ebay-uk', website='https://ebay.co.uk', is_uk=True)
        category = Category.objects.create(name='Warhammer Board Games', slug='warhammer-board-games')
        self.product = Product.objects.create(
            name='Old Game', slug='old-game', gw_sku='WBG-001', category=category,
            is_active=True, uses_market_price=True,
        )

    def _price(self, retailer, price, in_stock=True, not_available=False):
        """Create today's CurrentPrice row for the product."""
        return CurrentPrice.objects.create(
            product=self.product, retailer=retailer, price=D(price), in_stock=in_stock,
            not_available=not_available, url='https://example.com/x',
        )

    def _history(self, retailer, price, days_ago, in_stock=True):
        """Create a PriceHistory record dated days_ago days before today (midday UTC)."""
        record = PriceHistory.objects.create(
            product=self.product, retailer=retailer, price=D(price), in_stock=in_stock,
        )
        when = datetime.datetime.combine(
            self.today - datetime.timedelta(days=days_ago), datetime.time(12, 0), tzinfo=datetime.timezone.utc,
        )
        PriceHistory.objects.filter(pk=record.pk).update(recorded_at=when)

    def _run(self, *args):
        """Run the command and return what it printed."""
        out = StringIO()
        call_command('refresh_market_prices', *args, stdout=out)
        return out.getvalue()

    def _market(self):
        """Return the product's stored Average Market Price, read fresh from the database."""
        return Product.objects.get(pk=self.product.pk).market_price

    def test_first_calculation_is_the_median_of_todays_us_prices(self):
        """Only priced, in-stock, available US rows count: the UK row and the out-of-stock row do not."""
        self._price(self.ebay, '40.00')
        self._price(self.amazon, '60.00')
        self._price(self.nk, '50.00')
        self._price(self.uk, '999.00')
        CurrentPrice.objects.create(
            product=self.product, retailer=Retailer.objects.create(name='Gone', slug='gone', website='https://g.com'),
            price=D('5.00'), in_stock=False, url='https://example.com/g',
        )
        output = self._run()
        self.assertEqual(self._market(), D('50.00'))
        self.assertIn('(today, 3 prices)', output)

    def test_later_calculation_is_the_time_weighted_median_of_the_history_window(self):
        """
        Ten day window. eBay: 50 (set before the window) then 80 from 4 days ago.
        Amazon: 60 from 3 days ago. Noble Knight: 40, out of stock from 2 days ago.
        That is 21 retailer-days; the 11th lowest is 50. The median of the five
        records alone would be 55, so this proves a price counts for how long it stood.
        """
        Product.objects.filter(pk=self.product.pk).update(market_price=D('1.00'))
        self._history(self.ebay, '50.00', 20)
        self._history(self.ebay, '80.00', 4)
        self._history(self.amazon, '60.00', 3)
        self._history(self.nk, '40.00', 12)
        self._history(self.nk, '40.00', 2, in_stock=False)
        output = self._run('--window-days', '10')
        self.assertEqual(self._market(), D('50.00'))
        self.assertIn('(history, 21 prices)', output)

    def test_uk_history_is_ignored(self):
        """A UK retailer's history never moves the USD median."""
        Product.objects.filter(pk=self.product.pk).update(market_price=D('1.00'))
        self._history(self.ebay, '50.00', 5)
        self._history(self.uk, '900.00', 5)
        self._run('--window-days', '10')
        self.assertEqual(self._market(), D('50.00'))

    def test_history_falls_back_to_todays_prices_when_there_is_none(self):
        """Already calculated once but no history in the window: use today's retailer prices."""
        Product.objects.filter(pk=self.product.pk).update(market_price=D('1.00'))
        self._price(self.ebay, '70.00')
        PriceHistory.objects.all().delete()  # saving a price row also writes a history record
        output = self._run()
        self.assertEqual(self._market(), D('70.00'))
        self.assertIn('(today, 1 prices)', output)

    def test_no_prices_leaves_the_value_alone_and_says_so(self):
        """With nothing to calculate from, the stored price is kept and the product is reported."""
        Product.objects.filter(pk=self.product.pk).update(market_price=D('33.00'))
        output = self._run()
        self.assertEqual(self._market(), D('33.00'))
        self.assertIn('WBG-001', output)
        self.assertIn('no data: 1', output)

    def test_dry_run_saves_nothing(self):
        """--dry-run reports the new price but does not write it."""
        self._price(self.ebay, '45.00')
        output = self._run('--dry-run')
        self.assertIsNone(self._market())
        self.assertIn('would change: 1', output)

    def test_only_ticked_products_change_and_only_market_price_is_written(self):
        """An unticked product is never touched, and the ticked one keeps every other field."""
        other = Product.objects.create(
            name='Other', slug='other', gw_sku='WBG-002', category=self.product.category,
            is_active=True, msrp=D('99.00'),
        )
        CurrentPrice.objects.create(product=other, retailer=self.ebay, price=D('20.00'), in_stock=True, url='https://e.com/o')
        self._price(self.ebay, '45.00')
        self.product.msrp = D('12.00')
        self.product.save()
        self._run()
        other.refresh_from_db()
        self.assertIsNone(other.market_price)
        refreshed = Product.objects.get(pk=self.product.pk)
        self.assertEqual((refreshed.market_price, refreshed.msrp, refreshed.name), (D('45.00'), D('12.00'), 'Old Game'))

    def test_skus_option_limits_the_run_and_warns_about_unticked_ones(self):
        """--skus refreshes only the named ticked products and warns about the others."""
        self._price(self.ebay, '45.00')
        output = self._run('--skus', 'WBG-001,WBG-404')
        self.assertEqual(self._market(), D('45.00'))
        self.assertIn('WBG-404: not found or not ticked uses_market_price', output)

    def test_window_days_must_be_positive(self):
        """A window of zero days is rejected."""
        with self.assertRaises(CommandError):
            call_command('refresh_market_prices', '--window-days', '0', stdout=StringIO())


@override_settings(STORAGES=_TEST_STORAGES)
class MarketPricePagesTest(TestCase):
    """Product and list pages: the Avg Market Price label, asterisk and footnote."""

    def setUp(self):
        """Create an out-of-print product (Avg Market Price) and one with an MSRP, both with a US price."""
        self.retailer = Retailer.objects.create(name='eBay', slug='ebay', website='https://ebay.com')
        self.category = Category.objects.create(name='Warhammer Board Games', slug='warhammer-board-games')
        self.oop = Product.objects.create(
            name='Old Game', slug='old-game', gw_sku='WBG-001', category=self.category,
            is_active=True, uses_market_price=True, market_price=D('55.00'),
        )
        self.current = Product.objects.create(
            name='New Game', slug='new-game', gw_sku='WBG-002', category=self.category,
            is_active=True, msrp=D('50.00'),
        )
        for product, price in ((self.oop, '48.00'), (self.current, '40.00')):
            CurrentPrice.objects.create(
                product=product, retailer=self.retailer, price=D(price), in_stock=True, url='https://e.com/x',
            )

    def test_detail_page_shows_the_average_market_price_and_the_footnote(self):
        """The out-of-print product says Avg Market Price with an asterisk, never MSRP."""
        text = _text(self.client.get('/products/old-game/'))
        self.assertIn('Avg Market Price: $55.00*', text)
        self.assertIn(NOTE, text)
        self.assertNotIn('MSRP:', text)

    def test_detail_page_of_a_product_with_an_msrp_is_unchanged(self):
        """A product with an MSRP shows the MSRP and no Average Market Price or footnote."""
        text = _text(self.client.get('/products/new-game/'))
        self.assertIn('MSRP: $50.00', text)
        self.assertNotIn('Avg Market Price', text)
        self.assertNotIn(NOTE, text)

    def test_category_page_marks_only_the_average_market_price_card_and_prints_the_note_once(self):
        """On a category page: the out-of-print card carries the label, the MSRP card keeps its MSRP."""
        text = _text(self.client.get('/products/', {'category': 'warhammer-board-games'}))
        self.assertIn('Avg Market Price $55.00*', text)
        self.assertIn('MSRP $50', text)
        self.assertEqual(text.count(NOTE), 1)

    def test_pages_that_are_not_filtered_to_a_category_show_nothing(self):
        """The all-products list shows neither the label, the asterisk nor the footnote."""
        text = _text(self.client.get('/products/'))
        self.assertNotIn('Avg Market Price', text)
        self.assertNotIn(NOTE, text)

    def test_a_ticked_product_without_a_market_price_shows_nothing(self):
        """No calculated price yet means no label and no footnote."""
        Product.objects.filter(pk=self.oop.pk).update(market_price=None)
        self.assertNotIn('Avg Market Price', _text(self.client.get('/products/old-game/')))
        self.assertNotIn(NOTE, _text(self.client.get('/products/', {'category': 'warhammer-board-games'})))
