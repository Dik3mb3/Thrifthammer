"""
Tests for the category-aware wording of the sub-group list on the product list.

Paint & Supplies and The Army Painter call their sub-groups "Brands"; Warhammer and
every other game category keep "Factions". The Army Painter is a single flat list
of sets and bundles, so while it has no brands the whole box is hidden (every other
category without factions keeps showing "No factions in this category.").

Run with: python manage.py test products.tests_brand_wording --settings=thrifthammer.test_settings
"""

import decimal

from django.test import TestCase, override_settings

from products.models import Category, Faction, Product
from products.tests import _TEST_STORAGES

_HEADING = r'data-target="facs-body"[^>]*>\s*{label}\s*<span'


def _product(name, slug, category, faction):
    """Create one active product in a faction."""
    return Product.objects.create(
        name=name, slug=slug, gw_sku=f'T-{slug}', msrp=decimal.Decimal('10.00'),
        category=category, faction=faction, is_active=True,
    )


@override_settings(STORAGES=_TEST_STORAGES)
class SubGroupWordingTest(TestCase):
    """The heading and the "All ..." link follow the category."""

    def setUp(self):
        """Create one category, faction and product for each wording case."""
        for slug, name in (
            ('paint-supplies', 'Paint & Supplies'),
            ('warhammer-40000', 'Warhammer 40,000'),
        ):
            category = Category.objects.create(name=name, slug=slug)
            faction = Faction.objects.create(name=f'{name} Group', slug=f'{slug}-group', category=category)
            _product(f'{name} Item', f'{slug}-item', category, faction)

    def _page(self, slug):
        """Return the HTML of the product list for one category."""
        response = self.client.get('/products/', {'category': slug})
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_game_categories_still_say_factions(self):
        """Warhammer keeps Factions."""
        html = self._page('warhammer-40000')
        self.assertRegex(html, _HEADING.format(label='Factions'))
        self.assertIn('All Factions', html)
        self.assertNotIn('Sub-Categories', html)

    def test_paint_supplies_still_says_brands(self):
        """The existing Paint & Supplies wording is unchanged."""
        html = self._page('paint-supplies')
        self.assertRegex(html, _HEADING.format(label='Brands'))
        self.assertIn('All Brands', html)


@override_settings(STORAGES=_TEST_STORAGES)
class ArmyPainterSidebarTest(TestCase):
    """The Army Painter hides the empty box and says Brands if it ever gets some."""

    def setUp(self):
        """Create The Army Painter with one product and no faction, plus Kill Team (no factions)."""
        self.army = Category.objects.create(name='The Army Painter', slug='army-painter')
        _product('Set One', 'ap-set-one', self.army, None)
        kill_team = Category.objects.create(name='Kill Team', slug='kill-team')
        _product('Kill Team Box', 'kt-box', kill_team, None)

    def _page(self, slug):
        """Return the HTML of the product list for one category."""
        response = self.client.get('/products/', {'category': slug})
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_empty_box_is_hidden_for_the_army_painter(self):
        """No factions: no heading, no empty message, and the products still list."""
        html = self._page('army-painter')
        self.assertNotIn('data-target="facs-body"', html)
        self.assertNotIn('No factions in this category', html)
        self.assertIn('Set One', html)

    def test_box_says_brands_once_it_has_brands(self):
        """With a faction the Army Painter box shows, titled Brands with an All Brands link."""
        faction = Faction.objects.create(name='Speedpaint Brand', slug='ap-brand', category=self.army)
        _product('Branded Set', 'ap-branded', self.army, faction)
        html = self._page('army-painter')
        self.assertRegex(html, _HEADING.format(label='Brands'))
        self.assertIn('All Brands', html)

    def test_other_categories_without_factions_are_unchanged(self):
        """Kill Team (no factions) still shows its heading and the empty message."""
        html = self._page('kill-team')
        self.assertRegex(html, _HEADING.format(label='Factions'))
        self.assertIn('No factions in this category', html)
