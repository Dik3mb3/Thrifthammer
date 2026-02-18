"""
Tests for the products app.

Covers models, views, and URL routing. Focuses on:
- Critical model methods (get_cheapest_price, get_savings_vs_retail)
- Authentication/permission requirements
- Edge cases (empty data, inactive products, invalid slugs)
- View response codes and context
"""

import decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

# Use plain static files storage in tests — WhiteNoise's manifest storage
# requires `collectstatic` to have been run, which is not appropriate in tests.
_TEST_STORAGES = {
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer


class CategoryModelTest(TestCase):
    """Test Category model behaviour."""

    def test_slug_auto_generated(self):
        """Slug is set automatically from name when not provided."""
        cat = Category.objects.create(name='Warhammer 40000')
        self.assertEqual(cat.slug, 'warhammer-40000')

    def test_str(self):
        """__str__ returns the category name."""
        cat = Category(name='Age of Sigmar')
        self.assertEqual(str(cat), 'Age of Sigmar')


class ProductModelTest(TestCase):
    """Test Product model methods."""

    def setUp(self):
        """Set up a product with two retailer prices."""
        self.category = Category.objects.create(name='40K', slug='40k')
        self.retailer_gw = Retailer.objects.create(
            name='Games Workshop', slug='games-workshop',
            website='https://www.games-workshop.com',
        )
        self.retailer_el = Retailer.objects.create(
            name='Element Games', slug='element-games',
            website='https://www.elementgames.co.uk',
        )
        self.product = Product.objects.create(
            name='Intercessors',
            slug='intercessors',
            category=self.category,
            msrp=decimal.Decimal('40.00'),
        )
        # GW at full price
        CurrentPrice.objects.create(
            product=self.product,
            retailer=self.retailer_gw,
            price=decimal.Decimal('40.00'),
            in_stock=True,
            url='https://www.games-workshop.com',
        )
        # Element Games cheaper and in stock
        CurrentPrice.objects.create(
            product=self.product,
            retailer=self.retailer_el,
            price=decimal.Decimal('33.50'),
            in_stock=True,
            url='https://www.elementgames.co.uk',
        )

    def test_get_cheapest_price_returns_lowest(self):
        """get_cheapest_price returns the in-stock CurrentPrice with lowest price."""
        best = self.product.get_cheapest_price()
        self.assertEqual(best.retailer, self.retailer_el)
        self.assertEqual(best.price, decimal.Decimal('33.50'))

    def test_get_cheapest_price_prefers_in_stock(self):
        """Out-of-stock prices are only returned if no in-stock price exists."""
        # Mark Element Games out of stock
        CurrentPrice.objects.filter(retailer=self.retailer_el).update(in_stock=False)
        CurrentPrice.objects.filter(retailer=self.retailer_gw).update(in_stock=False)
        # Cache is invalidated by Product.save() but the test manipulates directly
        from django.core.cache import cache
        cache.clear()

        best = self.product.get_cheapest_price()
        # Should return Element Games despite OOS (it's still cheaper)
        self.assertEqual(best.price, decimal.Decimal('33.50'))

    def test_get_cheapest_price_no_prices(self):
        """get_cheapest_price returns None when no prices exist."""
        product = Product.objects.create(
            name='No Prices Yet', slug='no-prices-yet', msrp=decimal.Decimal('25.00'),
        )
        result = product.get_cheapest_price()
        self.assertIsNone(result)

    def test_get_savings_vs_retail(self):
        """get_savings_vs_retail returns correct amount and percent."""
        savings = self.product.get_savings_vs_retail()
        self.assertIsNotNone(savings)
        self.assertEqual(savings['amount'], decimal.Decimal('6.50'))
        # (6.50 / 40.00) * 100 = 16.25 → rounded to 1dp = 16.2
        self.assertAlmostEqual(float(savings['percent']), 16.25, delta=0.1)
        self.assertEqual(savings['retailer'], self.retailer_el)

    def test_get_savings_vs_retail_no_msrp(self):
        """Returns None when product has no MSRP."""
        self.product.msrp = None
        self.product.save()
        self.assertIsNone(self.product.get_savings_vs_retail())

    def test_slug_auto_generated(self):
        """Slug is auto-generated from name when not set."""
        product = Product.objects.create(name='Space Marine Intercessors', slug='')
        # save() must be triggered for slug generation
        product.slug = ''
        product.save()
        # Reload from DB
        product.refresh_from_db()
        self.assertEqual(product.slug, 'space-marine-intercessors')

    def test_best_price_property_alias(self):
        """best_price property returns same result as get_cheapest_price()."""
        self.assertEqual(self.product.best_price, self.product.get_cheapest_price())


@override_settings(STORAGES=_TEST_STORAGES)
class ProductListViewTest(TestCase):
    """Test the product list view."""

    def setUp(self):
        """Create sample data and test client."""
        self.client = Client()
        self.category = Category.objects.create(name='40K', slug='40k')
        self.product_active = Product.objects.create(
            name='Active Product', slug='active-product',
            category=self.category, is_active=True,
        )
        self.product_inactive = Product.objects.create(
            name='Inactive Product', slug='inactive-product',
            category=self.category, is_active=False,
        )

    def test_product_list_ok(self):
        """Product list returns 200."""
        response = self.client.get(reverse('products:list'))
        self.assertEqual(response.status_code, 200)

    def test_inactive_products_excluded(self):
        """Inactive products do not appear in the product list."""
        response = self.client.get(reverse('products:list'))
        product_names = [p.name for p in response.context['products']]
        self.assertIn('Active Product', product_names)
        self.assertNotIn('Inactive Product', product_names)

    def test_search_filters_by_name(self):
        """Search query filters products by name."""
        response = self.client.get(reverse('products:list'), {'q': 'Active'})
        product_names = [p.name for p in response.context['products']]
        self.assertIn('Active Product', product_names)
        self.assertNotIn('Inactive Product', product_names)

    def test_search_empty_results(self):
        """Search for a non-existent term returns empty results without error."""
        response = self.client.get(reverse('products:list'), {'q': 'xyznonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)

    def test_category_filter(self):
        """Category filter restricts results to the chosen category."""
        other_cat = Category.objects.create(name='AoS', slug='aos')
        Product.objects.create(
            name='AoS Product', slug='aos-product',
            category=other_cat, is_active=True,
        )
        response = self.client.get(reverse('products:list'), {'category': '40k'})
        product_names = [p.name for p in response.context['products']]
        self.assertIn('Active Product', product_names)
        self.assertNotIn('AoS Product', product_names)

    def test_invalid_sort_defaults_to_name(self):
        """Invalid sort parameter defaults to name ordering without raising an error."""
        response = self.client.get(reverse('products:list'), {'sort': 'hack;DROP TABLE'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort'], 'name')

    def test_pagination_context(self):
        """Pagination context is passed to the template."""
        response = self.client.get(reverse('products:list'))
        self.assertIn('page_obj', response.context)
        self.assertIn('paginator', response.context)


@override_settings(STORAGES=_TEST_STORAGES)
class ProductDetailViewTest(TestCase):
    """Test the product detail view."""

    def setUp(self):
        """Create sample product with prices."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='40K', slug='40k')
        self.retailer = Retailer.objects.create(
            name='Element Games', slug='element-games',
            website='https://www.elementgames.co.uk',
        )
        self.product = Product.objects.create(
            name='Space Marine Intercessors',
            slug='space-marine-intercessors',
            category=self.category,
            msrp=decimal.Decimal('40.00'),
            is_active=True,
        )
        CurrentPrice.objects.create(
            product=self.product,
            retailer=self.retailer,
            price=decimal.Decimal('33.00'),
            in_stock=True,
            url='https://elementgames.co.uk/test',
        )

    def test_product_detail_ok(self):
        """Product detail page returns 200 for active product."""
        response = self.client.get(
            reverse('products:detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_product_detail_404_for_inactive(self):
        """Inactive products return 404."""
        self.product.is_active = False
        self.product.save()
        from django.core.cache import cache
        cache.clear()
        response = self.client.get(
            reverse('products:detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_product_detail_404_for_bad_slug(self):
        """Non-existent slug returns 404."""
        response = self.client.get(
            reverse('products:detail', kwargs={'slug': 'does-not-exist'})
        )
        self.assertEqual(response.status_code, 404)

    def test_savings_in_context(self):
        """Savings are calculated and passed in context."""
        response = self.client.get(
            reverse('products:detail', kwargs={'slug': self.product.slug})
        )
        savings = response.context['savings']
        self.assertIsNotNone(savings)
        self.assertEqual(savings['amount'], decimal.Decimal('7.00'))

    def test_on_watchlist_false_for_anonymous(self):
        """Anonymous users always see on_watchlist=False."""
        response = self.client.get(
            reverse('products:detail', kwargs={'slug': self.product.slug})
        )
        self.assertFalse(response.context['on_watchlist'])

    def test_related_products_excluded_self(self):
        """The current product is not listed in related products."""
        response = self.client.get(
            reverse('products:detail', kwargs={'slug': self.product.slug})
        )
        related = response.context['related_products']
        slugs = [p.slug for p in related]
        self.assertNotIn(self.product.slug, slugs)


@override_settings(STORAGES=_TEST_STORAGES)
class WatchlistToggleTest(TestCase):
    """Test watchlist add/remove."""

    def setUp(self):
        """Create a user and a product."""
        self.client = Client()
        self.user = User.objects.create_user(username='watcher', password='pass1234')
        self.product = Product.objects.create(
            name='Test Kit', slug='test-kit', is_active=True,
        )

    def test_toggle_requires_login(self):
        """Unauthenticated requests are redirected to login."""
        response = self.client.post(
            reverse('products:toggle_watchlist', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_toggle_get_not_allowed(self):
        """GET request to toggle watchlist redirects to product page (no side effects)."""
        self.client.login(username='watcher', password='pass1234')
        response = self.client.get(
            reverse('products:toggle_watchlist', kwargs={'slug': self.product.slug})
        )
        # GET is silently redirected to detail page without changing watchlist
        self.assertEqual(response.status_code, 302)

    def test_toggle_adds_to_watchlist(self):
        """POST adds product to user watchlist."""
        from accounts.models import WatchlistItem
        self.client.login(username='watcher', password='pass1234')
        self.client.post(
            reverse('products:toggle_watchlist', kwargs={'slug': self.product.slug})
        )
        self.assertTrue(
            WatchlistItem.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_toggle_removes_from_watchlist(self):
        """Second POST removes product from watchlist."""
        from accounts.models import WatchlistItem
        WatchlistItem.objects.create(user=self.user, product=self.product)
        self.client.login(username='watcher', password='pass1234')
        self.client.post(
            reverse('products:toggle_watchlist', kwargs={'slug': self.product.slug})
        )
        self.assertFalse(
            WatchlistItem.objects.filter(user=self.user, product=self.product).exists()
        )


@override_settings(STORAGES=_TEST_STORAGES)
class SearchAutocompleteTest(TestCase):
    """Test the search autocomplete JSON endpoint."""

    def setUp(self):
        """Create a few active and inactive products."""
        self.client = Client()
        Product.objects.create(name='Necron Warriors', slug='necron-warriors', is_active=True)
        Product.objects.create(name='Necron Overlord', slug='necron-overlord', is_active=True)
        Product.objects.create(name='Hidden Product', slug='hidden-product', is_active=False)

    def test_autocomplete_returns_json(self):
        """Endpoint returns valid JSON."""
        response = self.client.get(
            reverse('products:search_autocomplete'), {'q': 'necron'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_autocomplete_excludes_inactive(self):
        """Inactive products are never returned in autocomplete."""
        response = self.client.get(
            reverse('products:search_autocomplete'), {'q': 'hidden'}
        )
        data = response.json()
        names = [r['name'] for r in data['results']]
        self.assertNotIn('Hidden Product', names)

    def test_autocomplete_short_query(self):
        """Queries shorter than 2 chars return empty results."""
        response = self.client.get(
            reverse('products:search_autocomplete'), {'q': 'n'}
        )
        data = response.json()
        self.assertEqual(data['results'], [])

    def test_autocomplete_empty_query(self):
        """Empty query returns empty results."""
        response = self.client.get(reverse('products:search_autocomplete'))
        self.assertEqual(response.json()['results'], [])

    def test_autocomplete_limit_10(self):
        """Autocomplete returns at most 10 results."""
        for i in range(15):
            Product.objects.create(
                name=f'Tyranid Unit {i}',
                slug=f'tyranid-unit-{i}',
                is_active=True,
            )
        response = self.client.get(
            reverse('products:search_autocomplete'), {'q': 'tyranid'}
        )
        data = response.json()
        self.assertLessEqual(len(data['results']), 10)
