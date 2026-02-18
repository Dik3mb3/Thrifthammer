"""
Tests for the calculators app.

Covers:
- UnitType model methods (get_cost, get_retail_cost)
- SavedArmy model (slug generation, calculate_totals, get_absolute_url)
- ArmyCalculatorView (GET returns correct context)
- CalculateArmyCostView (POST returns correct totals)
- SaveArmyView (requires login, validates input, persists army)
- ViewSavedArmyView (public/private visibility rules)
- UserArmiesListView (requires login, lists own armies)
"""

import decimal
import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from products.models import Category, Faction, Product, Retailer
from prices.models import CurrentPrice

from .models import PrebuiltArmy, SavedArmy, UnitType

User = get_user_model()

_TEST_STORAGES = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def _make_user(username='testuser', password='testpass123'):
    """Create and return a test user."""
    return User.objects.create_user(username=username, password=password)


def _make_product(name='Test Product', msrp='40.00'):
    """Create a minimal Product for testing."""
    cat, _ = Category.objects.get_or_create(name='Test Category', defaults={'slug': 'test-category'})
    return Product.objects.create(
        name=name, slug=name.lower().replace(' ', '-'), msrp=decimal.Decimal(msrp),
        category=cat,
    )


def _make_retailer(name='Test Retailer'):
    """Create a minimal Retailer for testing."""
    return Retailer.objects.create(
        name=name, slug=name.lower().replace(' ', '-'),
        website='https://example.com', country='US',
    )


def _make_faction(name='Space Marines'):
    """Create or return a Space Marines Faction."""
    cat, _ = Category.objects.get_or_create(name='Warhammer 40,000', defaults={'slug': 'warhammer-40000'})
    faction, _ = Faction.objects.get_or_create(
        name=name, defaults={'slug': name.lower().replace(' ', '-'), 'category': cat},
    )
    return faction


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

@override_settings(STORAGES=_TEST_STORAGES)
class UnitTypeModelTest(TestCase):
    """Tests for UnitType model methods."""

    def setUp(self):
        """Set up a product with a current price and a linked unit type."""
        self.product = _make_product('Space Marine Intercessors', msrp='40.00')
        self.retailer = _make_retailer()
        self.price = CurrentPrice.objects.create(
            product=self.product,
            retailer=self.retailer,
            price=decimal.Decimal('34.00'),
            url='https://example.com/buy',
            in_stock=True,
        )
        self.unit = UnitType.objects.create(
            name='Intercessors',
            category='troops',
            product=self.product,
            points_cost=20,
            typical_quantity=5,
        )

    def test_get_cost_returns_cheapest_price(self):
        """get_cost() returns the cheapest current price for the linked product."""
        self.assertEqual(self.unit.get_cost(), decimal.Decimal('34.00'))

    def test_get_retail_cost_returns_msrp(self):
        """get_retail_cost() returns the product MSRP."""
        self.assertEqual(self.unit.get_retail_cost(), decimal.Decimal('40.00'))

    def test_get_cost_no_product(self):
        """get_cost() returns None when no product is linked."""
        unit = UnitType.objects.create(name='Librarian', category='hq', points_cost=75, typical_quantity=1)
        self.assertIsNone(unit.get_cost())

    def test_get_retail_cost_no_product(self):
        """get_retail_cost() returns None when no product is linked."""
        unit = UnitType.objects.create(name='Chaplain', category='hq', points_cost=65, typical_quantity=1)
        self.assertIsNone(unit.get_retail_cost())

    def test_str(self):
        """__str__ includes name and category display."""
        self.assertIn('Intercessors', str(self.unit))
        self.assertIn('Troops', str(self.unit))


@override_settings(STORAGES=_TEST_STORAGES)
class SavedArmyModelTest(TestCase):
    """Tests for SavedArmy model."""

    def setUp(self):
        """Create a user for army ownership."""
        self.user = _make_user()

    def test_slug_auto_generated(self):
        """Saving an army without a slug generates one from user and army name."""
        army = SavedArmy.objects.create(
            user=self.user,
            name='My Test Army',
            units_data=[],
        )
        self.assertTrue(army.slug)
        self.assertIn('testuser', army.slug)

    def test_slug_unique_collision(self):
        """Duplicate names get a numeric suffix to keep slugs unique."""
        army1 = SavedArmy.objects.create(user=self.user, name='Duplicate', units_data=[])
        army2 = SavedArmy.objects.create(user=self.user, name='Duplicate', units_data=[])
        self.assertNotEqual(army1.slug, army2.slug)

    def test_calculate_totals(self):
        """calculate_totals() correctly sums points, cost, retail, and savings."""
        army = SavedArmy(
            user=self.user,
            name='Calc Test',
            units_data=[
                {'name': 'Intercessors', 'quantity': 2, 'points': 100, 'price': '34.00', 'msrp': '40.00'},
                {'name': 'Captain', 'quantity': 1, 'points': 80, 'price': '22.00', 'msrp': '22.50'},
            ],
        )
        army.calculate_totals()
        self.assertEqual(army.points_total, (100 * 2) + (80 * 1))
        self.assertAlmostEqual(float(army.total_cost), 34.0 * 2 + 22.0)
        self.assertAlmostEqual(float(army.total_retail), 40.0 * 2 + 22.50)
        self.assertAlmostEqual(float(army.total_savings), float(army.total_retail) - float(army.total_cost))

    def test_get_absolute_url(self):
        """get_absolute_url() returns the shareable URL."""
        army = SavedArmy.objects.create(user=self.user, name='URL Test', units_data=[])
        url = army.get_absolute_url()
        self.assertIn(army.slug, url)

    def test_str(self):
        """__str__ includes username, army name, and points."""
        army = SavedArmy.objects.create(user=self.user, name='My Army', units_data=[], points_total=500)
        self.assertIn('testuser', str(army))
        self.assertIn('My Army', str(army))


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------

@override_settings(STORAGES=_TEST_STORAGES)
class ArmyCalculatorViewTest(TestCase):
    """Tests for the main ArmyCalculatorView."""

    def setUp(self):
        """Create sample unit types for the calculator page."""
        self.client = Client()
        self.faction = _make_faction()
        self.unit = UnitType.objects.create(
            name='Intercessors', category='troops', faction=self.faction,
            points_cost=20, typical_quantity=5, is_active=True,
        )
        self.url = reverse('calculators:space_marines')

    def test_get_anonymous(self):
        """Anonymous users can view the calculator page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_has_ordered_categories(self):
        """Context includes ordered_categories with at least one category."""
        response = self.client.get(self.url)
        self.assertIn('ordered_categories', response.context)
        self.assertTrue(len(response.context['ordered_categories']) > 0)

    def test_inactive_units_excluded(self):
        """Inactive units are not shown on the calculator page."""
        self.unit.is_active = False
        self.unit.save()
        response = self.client.get(self.url)
        for _, cat_data in response.context['ordered_categories']:
            for u in cat_data['units']:
                self.assertNotEqual(u.pk, self.unit.pk)

    def test_context_has_prebuilt_armies(self):
        """Context includes prebuilt_armies (may be empty)."""
        response = self.client.get(self.url)
        self.assertIn('prebuilt_armies', response.context)


@override_settings(STORAGES=_TEST_STORAGES)
class CalculateArmyCostViewTest(TestCase):
    """Tests for the AJAX cost-calculation endpoint."""

    def setUp(self):
        """Set up a unit with a price for calculation tests."""
        self.client = Client()
        self.product = _make_product(msrp='40.00')
        self.retailer = _make_retailer()
        CurrentPrice.objects.create(
            product=self.product, retailer=self.retailer,
            price=decimal.Decimal('34.00'), url='https://example.com', in_stock=True,
        )
        self.unit = UnitType.objects.create(
            name='Intercessors', category='troops',
            product=self.product, points_cost=20, typical_quantity=5, is_active=True,
        )
        self.url = reverse('calculators:api_calculate')

    def test_valid_post_returns_totals(self):
        """POST with valid unit IDs returns correct JSON totals."""
        payload = {'units': [{'id': self.unit.pk, 'quantity': 2}]}
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('points_total', data)
        self.assertIn('total_cost', data)
        self.assertIn('units', data)
        self.assertEqual(len(data['units']), 1)
        self.assertEqual(data['units'][0]['quantity'], 2)

    def test_invalid_json_returns_400(self):
        """POST with invalid JSON returns a 400 error."""
        response = self.client.post(self.url, data='not-json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_empty_units_returns_zeros(self):
        """POST with empty unit list returns zero totals."""
        payload = {'units': []}
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['points_total'], 0)

    def test_quantity_clamped(self):
        """Quantity is clamped to max 20."""
        payload = {'units': [{'id': self.unit.pk, 'quantity': 999}]}
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type='application/json',
        )
        data = response.json()
        self.assertEqual(data['units'][0]['quantity'], 20)


@override_settings(STORAGES=_TEST_STORAGES)
class SaveArmyViewTest(TestCase):
    """Tests for the AJAX SaveArmyView endpoint."""

    def setUp(self):
        """Set up user and unit for save tests."""
        self.client = Client()
        self.user = _make_user()
        self.unit = UnitType.objects.create(
            name='Intercessors', category='troops',
            points_cost=20, typical_quantity=5, is_active=True,
        )
        self.url = reverse('calculators:save_army')

    def _post(self, payload):
        """Helper to POST JSON to the save endpoint."""
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        response = self._post({'name': 'Test', 'units': []})
        self.assertIn(response.status_code, [302, 403])

    def test_save_creates_army(self):
        """Authenticated POST with valid data creates a SavedArmy."""
        self.client.force_login(self.user)
        payload = {
            'name': 'My 1000pt Army',
            'units': [{'id': self.unit.pk, 'quantity': 2}],
            'is_public': False,
        }
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertTrue(SavedArmy.objects.filter(user=self.user, name='My 1000pt Army').exists())

    def test_save_requires_name(self):
        """POST without an army name returns an error."""
        self.client.force_login(self.user)
        response = self._post({'name': '', 'units': [{'id': self.unit.pk, 'quantity': 1}]})
        self.assertEqual(response.status_code, 400)

    def test_save_public_flag(self):
        """The is_public flag is saved correctly on the army."""
        self.client.force_login(self.user)
        payload = {
            'name': 'Public Army',
            'units': [{'id': self.unit.pk, 'quantity': 1}],
            'is_public': True,
        }
        self._post(payload)
        army = SavedArmy.objects.get(name='Public Army')
        self.assertTrue(army.is_public)


@override_settings(STORAGES=_TEST_STORAGES)
class ViewSavedArmyViewTest(TestCase):
    """Tests for the army detail / share view."""

    def setUp(self):
        """Create an owner, a visitor, and armies."""
        self.client = Client()
        self.owner = _make_user('owner')
        self.visitor = _make_user('visitor', password='visitorpass')
        self.public_army = SavedArmy.objects.create(
            user=self.owner, name='Public', units_data=[], is_public=True,
        )
        self.private_army = SavedArmy.objects.create(
            user=self.owner, name='Private', units_data=[], is_public=False,
        )

    def test_public_army_visible_to_anonymous(self):
        """Public armies are visible to anonymous users."""
        url = self.public_army.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_private_army_hidden_from_anonymous(self):
        """Private armies return 404 for anonymous users."""
        url = self.private_army.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_private_army_visible_to_owner(self):
        """Private armies are visible to their owner."""
        self.client.force_login(self.owner)
        url = self.private_army.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_private_army_hidden_from_other_user(self):
        """Private armies return 404 to users who don't own them."""
        self.client.force_login(self.visitor)
        url = self.private_army.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


@override_settings(STORAGES=_TEST_STORAGES)
class UserArmiesListViewTest(TestCase):
    """Tests for the user's saved armies dashboard."""

    def setUp(self):
        """Create a user with two saved armies."""
        self.client = Client()
        self.user = _make_user()
        self.army1 = SavedArmy.objects.create(user=self.user, name='Army One', units_data=[])
        self.army2 = SavedArmy.objects.create(user=self.user, name='Army Two', units_data=[])
        self.url = reverse('calculators:my_armies')

    def test_anonymous_redirects_to_login(self):
        """Anonymous users are redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_authenticated_sees_own_armies(self):
        """Logged-in users see their own saved armies."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        armies = list(response.context['armies'])
        pks = [a.pk for a in armies]
        self.assertIn(self.army1.pk, pks)
        self.assertIn(self.army2.pk, pks)

    def test_user_does_not_see_others_armies(self):
        """Users cannot see armies belonging to other users."""
        other = _make_user('other')
        other_army = SavedArmy.objects.create(user=other, name='Other Army', units_data=[])
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        armies = list(response.context['armies'])
        pks = [a.pk for a in armies]
        self.assertNotIn(other_army.pk, pks)
