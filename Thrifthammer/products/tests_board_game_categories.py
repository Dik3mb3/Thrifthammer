"""
Tests for the Miniature Board Games category and its Warhammer Board Games sub-category.

Rules these tests keep in place:
  * Neither slug is part of the Friday "AoS & Warhammer" digest (WARHAMMER_CATEGORY_SLUGS).
  * Both stay out of the default selection of the Thursday customized digest
    (NON_GAME_SYSTEM_CATEGORY_SLUGS), though a subscriber can still tick them.
  * The old GW importer points at the new category name, and its --categories index
    map still lines up with its target list.

Run with: python manage.py test products.tests_board_game_categories --settings=thrifthammer.test_settings
"""

from django.test import SimpleTestCase

from products.management.commands.import_gw_catalog import CATEGORY_SLUG_MAP, CATEGORY_TARGETS
from products.models import NON_GAME_SYSTEM_CATEGORY_SLUGS, WARHAMMER_CATEGORY_SLUGS

BOARD_GAME_SLUGS = {'miniature-board-games'}


class BoardGameNewsletterScopeTest(SimpleTestCase):
    """The board game categories are a separate thing from the Warhammer digests."""

    def test_not_in_the_aos_and_warhammer_digest(self):
        """Neither slug is in the Friday digest's allowlist."""
        self.assertFalse(BOARD_GAME_SLUGS & WARHAMMER_CATEGORY_SLUGS)

    def test_left_out_of_the_default_custom_digest_selection(self):
        """The category is excluded from the default pick, and the retired slugs are gone."""
        self.assertTrue(BOARD_GAME_SLUGS <= NON_GAME_SYSTEM_CATEGORY_SLUGS)
        self.assertNotIn('boxed-games', NON_GAME_SYSTEM_CATEGORY_SLUGS)
        self.assertNotIn('warhammer-board-games', NON_GAME_SYSTEM_CATEGORY_SLUGS)


class GwImporterBoardGameTargetsTest(SimpleTestCase):
    """import_gw_catalog's board game entries."""

    def test_every_slug_in_the_map_points_at_a_real_target(self):
        """Each --categories index lands inside the target list."""
        for slug, index in CATEGORY_SLUG_MAP.items():
            self.assertLess(index, len(CATEGORY_TARGETS), slug)

    def test_board_game_entries_use_the_new_category_name(self):
        """The two GW "Other Games" pages feed the Warhammer Board Games universe of Miniature Board Games."""
        for slug in ('warhammer-quest', 'warhammer-underworlds'):
            label, path, category_name, faction = CATEGORY_TARGETS[CATEGORY_SLUG_MAP[slug]]
            self.assertEqual(category_name, 'Miniature Board Games')
            self.assertEqual(faction, 'Warhammer Board Games')
            self.assertTrue(path.startswith('/en-US/shop/other-games/'))
        self.assertNotIn('boxed-games', CATEGORY_SLUG_MAP)
        self.assertNotIn('Boxed Games', [target[2] for target in CATEGORY_TARGETS])
