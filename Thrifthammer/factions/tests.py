"""
Tests for the factions app.

Covers the wording of the faction landing page: the Warhammer 40,000 pages
must keep their exact existing text, and a faction in any other category
(A Song of Ice and Fire) must not be labelled as Warhammer.
"""

from django.test import TestCase, override_settings
from django.urls import reverse

from products.models import Category, Faction

# Plain static files storage in tests: WhiteNoise's manifest storage needs
# `collectstatic` to have been run, which is not appropriate in tests.
_TEST_STORAGES = {
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}


@override_settings(STORAGES=_TEST_STORAGES)
class FactionPageWordingTest(TestCase):
    """The category-aware wording on /factions/<slug>/."""

    @classmethod
    def setUpTestData(cls):
        """One Warhammer 40,000 faction and one A Song of Ice and Fire faction, both with a hero image."""
        cls.wh40k = Category.objects.create(slug='warhammer-40000', name='Warhammer 40,000')
        cls.asoiaf = Category.objects.create(
            slug='asoiaf', name='A Song of Ice and Fire (ASOIAF)',
        )
        Faction.objects.create(
            slug='tyranids', name='Tyranids', category=cls.wh40k,
            synopsis='The swarm.', hero_image_url='https://example.com/tyranids.jpg',
        )
        Faction.objects.create(
            slug='asoiaf-house-stark', name='House Stark', category=cls.asoiaf,
            synopsis='The north remembers.', hero_image_url='https://example.com/stark.jpg',
        )

    def _get(self, slug):
        """Fetch a faction page and return its decoded HTML."""
        response = self.client.get(reverse('factions:detail', kwargs={'slug': slug}))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_warhammer_40k_page_wording_is_unchanged(self):
        """Every Warhammer-specific string on a 40K page is exactly what it was before."""
        html = self._get('tyranids')
        self.assertIn(
            'content="Compare prices on every Tyranids kit across US Warhammer retailers. '
            'Updated daily."',
            html,
        )
        self.assertIn(
            'content="Compare prices on every Tyranids kit across US Warhammer retailers."',
            html,
        )
        self.assertIn(
            '"description": "Compare prices on every Tyranids kit across US Warhammer '
            'retailers. Updated daily."',
            html,
        )
        self.assertIn('alt="Tyranids, Warhammer 40,000"', html)
        self.assertIn('<p class="faction-hero-eyebrow">Warhammer 40,000</p>', html)

    def test_asoiaf_page_is_not_labelled_warhammer(self):
        """A non-Warhammer faction shows its own category name and no Warhammer wording."""
        html = self._get('asoiaf-house-stark')
        self.assertIn(
            '<p class="faction-hero-eyebrow">A Song of Ice and Fire (ASOIAF)</p>', html,
        )
        self.assertIn('alt="House Stark, A Song of Ice and Fire (ASOIAF)"', html)
        self.assertIn(
            'content="Compare prices on every House Stark kit across US retailers. '
            'Updated daily."',
            html,
        )
        self.assertIn(
            '"description": "Compare prices on every House Stark kit across US retailers. '
            'Updated daily."',
            html,
        )
        self.assertNotIn('US Warhammer retailers', html)
        self.assertNotIn('faction-hero-eyebrow">Warhammer 40,000', html)
        self.assertNotIn('House Stark, Warhammer 40,000', html)
