"""
Tests for Warhammer Board Games becoming a universe (faction) of Miniature Board Games.

Miniature Board Games calls its sub-group list "Universe" (like Paint & Supplies says "Brands" and Books say "Book Series");
every other game category keeps "Factions". The old Warhammer Board Games category URL permanently redirects to the new
filter, keeping the other parameters, so old links never land on an empty page.

Run with: python manage.py test products.tests_miniature_board_games_universe --settings=thrifthammer.test_settings
"""

import decimal

from django.test import TestCase, override_settings

from products.models import Category, Faction, Product
from products.tests import _TEST_STORAGES

_HEADING = r'data-target="facs-body"[^>]*>\s*{label}\s*<span'


@override_settings(STORAGES=_TEST_STORAGES)
class UniverseWordingAndRedirectTest(TestCase):
    """The Miniature Board Games page and the old category link."""

    def setUp(self):
        """One board game in the Warhammer Board Games universe, one 40K unit in a faction."""
        mbg = Category.objects.create(name='Miniature Board Games', slug='miniature-board-games')
        universe = Faction.objects.create(name='Warhammer Board Games', slug='warhammer-board-games', category=mbg)
        Product.objects.create(
            name='Test Board Game', slug='test-board-game', gw_sku='WBG-T1', msrp=decimal.Decimal('50.00'),
            category=mbg, faction=universe, is_active=True,
        )
        wh = Category.objects.create(name='Warhammer 40,000', slug='warhammer-40000')
        faction = Faction.objects.create(name='Orks', slug='orks', category=wh)
        Product.objects.create(
            name='Test Boyz', slug='test-boyz', gw_sku='T-boyz', msrp=decimal.Decimal('30.00'),
            category=wh, faction=faction, is_active=True,
        )

    def _page(self, slug, **extra):
        """Return the HTML of the product list for one category."""
        response = self.client.get('/products/', {'category': slug, **extra})
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_miniature_board_games_says_universe(self):
        """The heading and the all-link use Universe, and the board game shows once under its universe."""
        html = self._page('miniature-board-games')
        self.assertRegex(html, _HEADING.format(label='Universe'))
        self.assertIn('All Universes', html)
        self.assertNotIn('All Factions', html)
        self.assertIn('Test Board Game', html)
        self.assertIn('faction=warhammer-board-games', html)   # the universe is a filter link in the list

    def test_warhammer_keeps_factions(self):
        """The 40K category still says Factions."""
        html = self._page('warhammer-40000')
        self.assertRegex(html, _HEADING.format(label='Factions'))
        self.assertIn('All Factions', html)

    def test_old_category_link_redirects_to_the_universe_filter(self):
        """A permanent redirect to the new category plus faction filter, other parameters kept."""
        response = self.client.get('/products/', {'category': 'warhammer-board-games', 'sort': 'price_asc'})
        self.assertEqual(response.status_code, 301)
        location = response['Location']
        self.assertIn('category=miniature-board-games', location)
        self.assertIn('faction=warhammer-board-games', location)
        self.assertIn('sort=price_asc', location)
        self.assertTrue(location.startswith('/products/'))
        self.assertNotIn('category=warhammer-board-games', location)
