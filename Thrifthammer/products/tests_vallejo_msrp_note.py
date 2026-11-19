"""
Tests for the Vallejo MSRP footnote.

Vallejo prices in Euros, so the MSRPs we show for its sets are estimates taken from
online retailers. The footnote and the asterisk after each MSRP appear for Vallejo
products only, and only where an MSRP is actually shown.

Run with: python manage.py test products.tests_vallejo_msrp_note --settings=thrifthammer.test_settings
"""

import decimal
import re

from django.test import TestCase, override_settings

from products.models import Category, Faction, Product
from products.tests import _TEST_STORAGES

NOTE = '* MSRP prices originally in Euros. We used MSRP prices from online retailers as an estimate.'


def _text(response):
    """Return the page as plain text with tags removed and whitespace collapsed."""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', response.content.decode()))


@override_settings(STORAGES=_TEST_STORAGES)
class VallejoMsrpNoteTest(TestCase):
    """The footnote shows for Vallejo MSRPs and nowhere else."""

    def setUp(self):
        """Create a Vallejo set with an MSRP, one without, and a Warhammer product with an MSRP."""
        paint = Category.objects.create(name='Paint & Supplies', slug='paint-supplies')
        vallejo = Faction.objects.create(name='Vallejo', slug='vallejo', category=paint)
        other = Category.objects.create(name='Warhammer 40,000', slug='warhammer-40000')
        space_marines = Faction.objects.create(name='Space Marines', slug='space-marines', category=other)
        self.with_msrp = self._product('Vallejo Priced Set', 'vallejo-priced', paint, vallejo, '39.99')
        self.no_msrp = self._product('Vallejo Unpriced Set', 'vallejo-unpriced', paint, vallejo, None)
        self.warhammer = self._product('Space Marine Box', 'sm-box', other, space_marines, '55.00')

    @staticmethod
    def _product(name, slug, category, faction, msrp):
        """Create one active product."""
        return Product.objects.create(
            name=name, slug=slug, gw_sku=f'T-{slug}', category=category, faction=faction,
            msrp=decimal.Decimal(msrp) if msrp else None, is_active=True,
        )

    def test_vallejo_detail_page_with_msrp_shows_note_and_asterisk(self):
        """A Vallejo product page with an MSRP prints the footnote and marks the figure."""
        response = self.client.get(f'/products/{self.with_msrp.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(NOTE, _text(response))
        self.assertIn('$39.99*', _text(response))

    def test_vallejo_detail_page_without_msrp_has_no_note(self):
        """No MSRP means nothing to footnote."""
        response = self.client.get(f'/products/{self.no_msrp.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(NOTE, _text(response))

    def test_other_brands_never_show_the_note(self):
        """A Warhammer product with an MSRP has no footnote and no asterisk."""
        response = self.client.get(f'/products/{self.warhammer.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(NOTE, _text(response))
        self.assertNotIn('$55.00*', _text(response))

    def test_vallejo_list_page_shows_note_once(self):
        """The Vallejo list page shows the footnote once, under the grid."""
        response = self.client.get('/products/', {'category': 'paint-supplies', 'faction': 'vallejo'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_text(response).count(NOTE), 1)
        self.assertIn('MSRP $39.99*', _text(response))

    def test_mixed_lists_have_no_note_and_no_asterisk(self):
        """Lists of several brands that contain a Vallejo set show neither the note nor an asterisk."""
        for params in ({'category': 'paint-supplies'}, {}):
            response = self.client.get('/products/', params)
            self.assertEqual(response.status_code, 200, params)
            self.assertNotIn(NOTE, _text(response), params)
            self.assertNotIn('$39.99*', _text(response), params)

    def test_other_list_pages_have_no_note(self):
        """A list page with no Vallejo product has no footnote."""
        response = self.client.get('/products/', {'category': 'warhammer-40000'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(NOTE, _text(response))
