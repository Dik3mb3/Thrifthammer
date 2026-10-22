"""Tests for the Gundam app: sitemap coverage and the main nav link."""
import re

from django.test import SimpleTestCase, TestCase, override_settings

from .models import Product, Series

_TEST_STORAGES = {
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=_TEST_STORAGES)
class GundamDiscoverabilityTest(TestCase):
    """Search engines and visitors can reach the Gundam section."""

    def setUp(self):
        """Create one active and one inactive Gundam product."""
        series = Series.objects.create(name='Mobile Suit Test Gundam')
        Product.objects.create(name='HG Test Kit', slug='hg-test-kit', series=series, is_active=True)
        Product.objects.create(name='HG Hidden Kit', slug='hg-hidden-kit', series=series, is_active=False)

    def test_sitemap_lists_gundam_pages(self):
        """The sitemap has the Gundam list page and active products only."""
        xml = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('/gundam/</loc>', xml)
        self.assertIn('/gundam/hg-test-kit/</loc>', xml)
        self.assertNotIn('hg-hidden-kit', xml)

    def test_main_nav_links_to_gundam(self):
        """Every page's main navigation links to the Gundam section."""
        html = self.client.get('/gundam/').content.decode()
        self.assertIn('<a href="/gundam/">Gundam</a>', html)


class EbaySearchNameTest(TestCase):
    """The per-product eBay search phrase drives both the query and the required title words."""

    def setUp(self):
        """Create one kit with a kit number and one without."""
        series = Series.objects.create(name='Mobile Suit Test Gundam')
        self.with_kit = Product.objects.create(
            name='HGUC MSN-06S Sinanju', slug='hguc-msn-06s-sinanju', series=series)
        self.no_kit = Product.objects.create(
            name='Mega Size 1/48 RX-0 Unicorn Gundam (Destroy Mode)', slug='mega-size-test', series=series)

    def _terms(self):
        """Return the matcher's term sets for both products."""
        from .management.commands.find_gundam_ebay_prices import _build_term_sets
        return _build_term_sets([self.with_kit, self.no_kit])

    def test_default_query_is_kit_number_or_full_name(self):
        """With no phrase set, the query is the kit number, or the full name without one."""
        terms = self._terms()
        self.assertEqual(terms[self.with_kit.pk]['query'], 'MSN-06S')
        self.assertEqual(terms[self.no_kit.pk]['query'], self.no_kit.name)

    def test_search_name_replaces_query_and_required_words(self):
        """A phrase becomes the query and its words become the required title words."""
        for product in (self.with_kit, self.no_kit):
            product.ebay_search_name = 'Mega Size Model Unicorn Destroy'
            product.save()
        after = self._terms()
        for product in (self.with_kit, self.no_kit):
            self.assertEqual(after[product.pk]['query'], 'Mega Size Model Unicorn Destroy')
            self.assertEqual(after[product.pk]['required'], {'mega', 'size', 'model', 'unicorn', 'destroy'})

    def test_search_name_keeps_negative_keywords(self):
        """Negative keywords still exclude words and block item ids when a phrase is set."""
        self.no_kit.ebay_search_name = 'Mega Size Model Unicorn Destroy'
        self.no_kit.ebay_negative_keywords = 'norn 123456789'
        self.no_kit.save()
        terms = self._terms()[self.no_kit.pk]
        self.assertIn('norn', terms['excluded'])
        self.assertEqual(terms['blocked_item_ids'], {'123456789'})

    def test_blank_search_name_keeps_name_based_required_words(self):
        """With no phrase, the required words still come from the product name."""
        self.assertIn('rx0', self._terms()[self.no_kit.pk]['required'])


def _old_title_words(title):
    """The title tokenizer as it was before BB-number handling (reference for regression tests)."""
    from .management.commands.find_gundam_ebay_prices import _collapse_dotted_acronyms, _strip_seps
    return set(re.findall(r'[a-z0-9]+', _strip_seps(_collapse_dotted_acronyms(title)).lower()))


class BbNumberTitleWordsTest(SimpleTestCase):
    """Every common way a seller writes a BB Senshi number yields the same bb### token."""

    def _words(self, title):
        """Tokenize a title with the matcher's own function."""
        from .management.commands.find_gundam_ebay_prices import _title_words
        return _title_words(title)

    def test_number_styles_all_give_one_token(self):
        """BB 390, BB #390, BB# 390, BB No. 391, BB Senshi 392, BB-394 and BB360 all normalize."""
        cases = {
            'Bandai BB #390 RX-0 Full Armor Unicorn Gundam Model Kit': 'bb390',
            'Bandai Gundam BB# 390 Full Armor': 'bb390',
            'Bandai SD BB 365 Gundam UC MSN-06S Sinanju': 'bb365',
            'Bandai BB Senshi No. 391 Unicorn Gundam 02 Banshee Norn Plastic Model Kit': 'bb391',
            'US Seller BB Senshi No392 Neo Zeong Model kit Mobile Suit Gundam Unicorn': 'bb392',
            'BANDAI MSN-001A1 Delta Plus Model Kit SD BB Senshi 379': 'bb379',
            'Bandai BB Senshi Number 380 Banshee': 'bb380',
            'Bandai BB No.367 Kshatriya': 'bb367',
            'SD Gundam BB-394 Phenex': 'bb394',
            'Bandai Gundam BB360 Unicorn': 'bb360',
            'bandai bb senshi bb390 full armor': 'bb390',
        }
        for title, token in cases.items():
            words = self._words(title)
            self.assertIn(token, words, title)
            self.assertIn('bb', words, title)

    def test_non_bb_numbers_are_not_invented(self):
        """Bike parts, car parts and numbers without the letters BB never become a BB kit number."""
        cases = {
            'FSA Afterburner 1X Modular BB392EVO Mountain Crankset': 'bb392',
            'Token Ninja BB38624P Press Fit Bottom Bracket BB386/BB392': 'bb392',
            'Bandai Mobile Suit Unicorn Gundam 02 Banshee # 380 Model Kit': 'bb380',
            'Bandai Hobby HGUC #175 RX-0[N] Unicorn Gundam 02 Banshee Norn': 'bb175',
            'Gundam 1/144 HGUC #100 Unicorn Gundam Destroy Mode': 'bb100',
            'Gundam BBQ 365 grill': 'bb365',
        }
        for title, token in cases.items():
            self.assertNotIn(token, self._words(title), title)

    def test_titles_without_bb_read_exactly_as_before(self):
        """Titles with no BB number tokenize identically to the old tokenizer (a "#100" adds only its hash token)."""
        titles = [
            'Bandai HGUC #100 RX-0 Unicorn Gundam Destroy Mode HG 1/144 Model Kit USA',
            'Bandai HGUC 1/144 MSZ-006A1 Zeta plus (Unicorn Ver.)',
            'HGUC AMX-014 Doven Wolf (Unicorn Ver.) A.E.U.G. edition',
            'MG 1/100 RX-9/C Narrative Gundam C-Packs (Ver. Ka)',
            'Bandai SD Gundam EX-Standard 015 Unicorn Gundam 02 Banshee Norn (Destroy Mode)',
            'GFFMC GUNDAM FIX FIGURATION METAL COMPOSITE BANSHEE NORN AWAKENING Ver.',
            'Premium Bandai RG 1/144 RX-0[N] Unicorn Gundam 02 Banshee Norn Final Battle Ver',
            'Bandai PG 1/60 RX-0 Unicorn Gundam',
        ]
        for title in titles:
            words = {word for word in self._words(title) if not re.fullmatch(r'hash\d{2,3}', word)}
            self.assertEqual(words, _old_title_words(title), title)


class BbNumberMatchingTest(TestCase):
    """End to end: BB kits match their own listing and nothing else."""

    def setUp(self):
        """Create three BB Senshi kits that share the words Unicorn and Gundam."""
        series = Series.objects.create(name='Mobile Suit Test Gundam')
        self.series = series
        self.bb390 = Product.objects.create(
            name='BB Senshi BB390 Full Armor Unicorn Gundam', slug='bb390', series=series)
        self.bb391 = Product.objects.create(
            name='BB Senshi BB391 Unicorn Gundam 02 Banshee Norn', slug='bb391', series=series)
        self.bb360 = Product.objects.create(
            name='BB Senshi BB360 Unicorn Gundam', slug='bb360', series=series)

    def _terms(self, extra=()):
        """Return the matcher's term sets for the three kits (plus any extra products)."""
        from .management.commands.find_gundam_ebay_prices import _build_term_sets
        return _build_term_sets([self.bb390, self.bb391, self.bb360, *extra])

    def _ok(self, product, title):
        """Return True when the title would be accepted for the product."""
        from .management.commands.find_gundam_ebay_prices import _matches
        terms = self._terms()[product.pk]
        return _matches(title, terms['required'], terms['excluded'])

    def test_each_kit_matches_its_own_listing_in_any_number_style(self):
        """Hash, space, No. and glued styles all reach the right kit."""
        for title in ('Bandai BB #390 RX-0 Full Armor Unicorn Gundam Model Kit',
                      'Bandai Gundam BB 390 Full Armor Unicorn Gundam Model Kit USA',
                      'BB Senshi No. 390 Full Armor Unicorn Gundam',
                      'Bandai BB390 Full Armor Unicorn Gundam'):
            self.assertTrue(self._ok(self.bb390, title), title)
        self.assertTrue(self._ok(self.bb391, 'Bandai BB Senshi No. 391 Unicorn Gundam 02 Banshee Norn Plastic Model Kit'))

    def test_wrong_number_never_matches(self):
        """A listing for another BB number is rejected even when every other word fits."""
        self.assertFalse(self._ok(self.bb360, 'Bandai BB #390 RX-0 Full Armor Unicorn Gundam Model Kit'))
        self.assertFalse(self._ok(self.bb390, 'Bandai BB Senshi No. 391 Unicorn Gundam 02 Banshee Norn Full Armor'))
        self.assertFalse(self._ok(self.bb360, 'Bandai BB Senshi No. 391 Unicorn Gundam 02 Banshee Norn'))

    def test_two_kit_lot_is_rejected(self):
        """A listing naming two BB numbers is a lot and matches neither kit."""
        lot = 'Bandai BB 390 Full Armor Unicorn Gundam + BB 391 Unicorn Gundam 02 Banshee Norn set'
        self.assertFalse(self._ok(self.bb390, lot))
        self.assertFalse(self._ok(self.bb391, lot))

    def test_junk_listings_are_rejected(self):
        """Car and bike parts that contain the number never match."""
        for title in ('Ford FE BB 390 428 Edelbrock cylinder head bolt kit',
                      'Chrysler Mopar BB 360 383 440 High Volume Water Pump',
                      'FSA Afterburner BB392EVO Mountain Crankset'):
            for product in (self.bb390, self.bb391, self.bb360):
                self.assertFalse(self._ok(product, title), title)

    def test_phrase_keeps_the_bb_number_required(self):
        """With a plain search phrase the number is still checked, so kits cannot cross-match."""
        from .management.commands.find_gundam_ebay_prices import _matches
        self.bb360.ebay_search_name = 'BB Senshi 360 Unicorn Gundam'
        self.bb360.save()
        terms = self._terms()[self.bb360.pk]
        self.assertIn('bb360', terms['required'])
        self.assertEqual(terms['query'], 'BB Senshi 360 Unicorn Gundam')
        self.assertTrue(_matches('Bandai BB Senshi No. 360 Unicorn Gundam', terms['required'], terms['excluded']))
        self.assertFalse(_matches('Bandai BB Senshi 390 Full Armor Unicorn Gundam', terms['required'], terms['excluded']))

    def test_non_bb_product_ignores_bb_rules(self):
        """A kit with no BB number is matched exactly as before, even if the title names a BB kit."""
        from .management.commands.find_gundam_ebay_prices import _build_term_sets, _matches
        mg = Product.objects.create(name='MG RX-0 Unicorn Gundam', slug='mg-test', series=self.series)
        terms = _build_term_sets([mg])[mg.pk]
        self.assertTrue(_matches('Bandai MG RX-0 Unicorn Gundam Master Grade Plastic Model Kit', terms['required'], terms['excluded']))
        self.assertTrue(_matches('Bandai MG RX-0 Unicorn Gundam MG 1/100 bundle with BB 390', terms['required'], terms['excluded']))


class BaselineExclusionTest(TestCase):
    """Accessory sheets never stand in for a kit; kits can still opt a word back in."""

    def setUp(self):
        """Create one kit with a kit number and one without."""
        series = Series.objects.create(name='Mobile Suit Test Gundam')
        self.with_kit = Product.objects.create(name='HGUC MSN-06S Sinanju', slug='sinanju-t', series=series)
        self.no_kit = Product.objects.create(name='HGUC Test Kit Alpha', slug='alpha-t', series=series)

    def _terms(self, products):
        """Return the matcher's term sets for the given products."""
        from .management.commands.find_gundam_ebay_prices import _build_term_sets
        return _build_term_sets(products)

    def test_baseline_words_are_excluded_for_every_kit(self):
        """Decal, sticker and etched words are excluded whether or not the kit has a kit number."""
        for product in (self.with_kit, self.no_kit):
            excluded = self._terms([self.with_kit, self.no_kit])[product.pk]['excluded']
            self.assertTrue({'decal', 'decals', 'waterslide', 'sticker', 'stickers', 'etched'} <= excluded)

    def test_decal_and_etched_sheets_are_rejected(self):
        """Titles for accessory sheets that name the kit do not match it."""
        from .management.commands.find_gundam_ebay_prices import _matches
        terms = self._terms([self.no_kit])[self.no_kit.pk]
        self.assertTrue(_matches('Bandai HGUC 1/144 Test Kit Alpha Model Kit', terms['required'], terms['excluded']))
        for title in ('Water Decal for HG 1/144 Test Kit Alpha UV Light-React',
                      'for HGUC Test Kit Alpha Etched PE Sheet Details Parts',
                      'Test Kit Alpha WaterSlide Decal HG', 'HGUC Test Kit Alpha sticker set'):
            self.assertFalse(_matches(title, terms['required'], terms['excluded']), title)

    def test_kit_whose_own_name_has_a_baseline_word_keeps_it_allowed(self):
        """A kit literally named with one of the words is not blocked by it."""
        series = Series.objects.get(name='Mobile Suit Test Gundam')
        odd = Product.objects.create(name='HGUC Sticker Edition Beta', slug='beta-t', series=series)
        terms = self._terms([odd])[odd.pk]
        self.assertNotIn('sticker', terms['excluded'])
        self.assertIn('decal', terms['excluded'])


def _listing(item_id='111', price='90.00', country='US', title='NXEDGE STYLE Xi Gundam Action Figure'):
    """Build a parsed eBay listing dict like EbayBrowseAPI._parse_item returns."""
    from decimal import Decimal
    return {'title': title, 'url': f'https://www.ebay.com/itm/{item_id}?x=1', 'item_id': f'v1|{item_id}|0',
            'price': Decimal(price), 'shipping': Decimal('0'), 'total_cost': Decimal(price), 'ships_from': country}


class HashNumberTest(TestCase):
    """A "#NNN" catalog number tells two releases of one suit apart (HGUC #79 vs #210)."""

    def setUp(self):
        """Create the plain HGUC Ground Type with its siblings' kit number."""
        series = Series.objects.create(name='Mobile Suit Test Gundam')
        self.kit = Product.objects.create(name='HGUC RX-79G Gundam Ground Type', slug='hguc-gt', series=series)

    def _terms(self, phrase='', negative=''):
        """Return the kit's matcher term set with the given phrase and negative keywords."""
        from .management.commands.find_gundam_ebay_prices import _build_term_sets
        self.kit.ebay_search_name = phrase
        self.kit.ebay_negative_keywords = negative
        return _build_term_sets([self.kit])[self.kit.pk]

    def test_title_tokens_only_for_an_explicit_hash_number(self):
        """"#79", "# 79" and "#210" give hash tokens; "RX-79", "1/144" and "No. 79" do not."""
        from .management.commands.find_gundam_ebay_prices import _title_words
        self.assertIn('hash79', _title_words('Bandai Hobby #79 RX-79(G) Gundam Ground Type'))
        self.assertIn('hash79', _title_words('Gundam Ground Type # 79 New'))
        self.assertIn('hash210', _title_words('HGUC 1/144 #210 RX-79[G]'))
        plain = _title_words('Bandai HGUC 1/144 RX-79[G] Ground Type No. 79')
        self.assertFalse({word for word in plain if word.startswith('hash')})

    def test_phrase_requires_the_hash_number(self):
        """A phrase containing "#79" makes the number a required title word."""
        terms = self._terms(phrase='HGUC #79 Gundam Ground Type')
        self.assertEqual(terms['required'], {'hguc', 'hash79', 'ground', 'type'})

    def test_hash_number_picks_the_right_release(self):
        """#79 listings pass the #79 phrase; #210 listings and unnumbered ones do not."""
        from .management.commands.find_gundam_ebay_prices import _matches
        terms = self._terms(phrase='HGUC #79 Gundam Ground Type')
        ok = 'Bandai Hobby #79 RX-79(G) Gundam Ground Type, Bandai HGUC'
        self.assertTrue(_matches(ok, terms['required'], terms['excluded']))
        for title in ('Bandai Hobby HGUC 1/144 #210 RX-79[G] Ground Gundam Type',
                      'Bandai HGUC 1/144 Gundam Ground Type'):
            self.assertFalse(_matches(title, terms['required'], terms['excluded']))

    def test_hash_negative_keyword_excludes_that_number_only(self):
        """"#210" as a negative keyword rejects titles writing #210; plain digits stay item ids."""
        from .management.commands.find_gundam_ebay_prices import _matches
        terms = self._terms(negative='#210 123456789')
        self.assertEqual(terms['blocked_item_ids'], {'123456789'})
        self.assertIn('hash210', terms['excluded'])
        self.assertFalse(_matches('Bandai HGUC #210 Gundam Ground Type', {'ground'}, terms['excluded']))
        self.assertTrue(_matches('Bandai HGUC #79 Gundam Ground Type', {'ground'}, terms['excluded']))

    def test_names_and_titles_without_a_hash_read_exactly_as_before(self):
        """No "#" in the text means no new tokens, so every existing match is unchanged."""
        from .management.commands.find_gundam_ebay_prices import _clean_words, _title_words
        self.assertEqual(_clean_words('HGUC MS-07B-3 Gouf Custom'), {'hguc', 'ms07b3', 'gouf', 'custom'})
        title = 'BANDAI HG /144 HGUC MS-07B-3 Gouf Custom Mobile Suit Gundam 081 Model Kit'
        self.assertEqual(_title_words(title), _old_title_words(title))


class CheapestListingTest(TestCase):
    """Same rule as Warhammer: Best Match #1 decides the kit, the cheapest valid listing wins if 10% cheaper."""

    def setUp(self):
        """Create one kit priced $100 at Gundam Planet and the eBay retailer."""
        from decimal import Decimal
        from products.models import Retailer
        series = Series.objects.create(name='Mobile Suit Test Gundam')
        self.product = Product.objects.create(
            name='NXEDGE Style Xi Gundam', slug='nx-xi', series=series, batch_tag='test', msrp=Decimal('100.00'))
        self.ebay = Retailer.objects.create(name='eBay', slug='ebay')

    def _run(self, us_items, abroad_items=(), shipping=None):
        """Run the command with --apply and a fake client; return (price row, abroad mock)."""
        from decimal import Decimal
        from io import StringIO
        from unittest import mock
        from django.core.management import call_command
        from .management.commands import find_gundam_ebay_prices as cmd
        from .models import CurrentPrice as GundamPrice
        fake = mock.MagicMock()
        fake.search_items.return_value = list(us_items)
        fake._fetch_item_shipping.side_effect = shipping or (lambda item_id: Decimal('10.00'))
        with mock.patch.object(cmd, 'EbayBrowseAPI', return_value=fake), \
                mock.patch.object(cmd, '_search_outside_us', return_value=list(abroad_items)) as abroad, \
                mock.patch.object(cmd.time, 'sleep'):
            call_command('find_gundam_ebay_prices', '--batch-tag', 'test', '--apply', stdout=StringIO())
        return GundamPrice.objects.filter(product=self.product, retailer=self.ebay).first(), abroad

    def test_cheapest_wins_when_at_least_ten_percent_cheaper_delivered(self):
        """A listing 36% cheaper delivered beats Best Match #1."""
        from decimal import Decimal
        row, _ = self._run([_listing('111', '100.00'), _listing('222', '60.00')])
        self.assertIn('/itm/222', row.url)
        self.assertEqual(row.price, Decimal('70.00'))

    def test_best_match_kept_when_the_gap_is_under_ten_percent(self):
        """A listing only 5% cheaper is not worth the identity risk, so Best Match #1 stays."""
        row, _ = self._run([_listing('111', '100.00'), _listing('222', '95.00')])
        self.assertIn('/itm/111', row.url)

    def test_comparison_uses_real_shipping(self):
        """A cheaper-looking listing with $40 real shipping loses to Best Match #1."""
        from decimal import Decimal
        row, _ = self._run([_listing('111', '100.00'), _listing('222', '60.00')],
                           shipping=lambda item_id: Decimal('40.00') if '|222|' in item_id else Decimal('10.00'))
        self.assertIn('/itm/111', row.url)

    def test_spare_part_never_wins_even_when_cheapest(self):
        """A "Replacement Parts" listing above the price floor is dropped, whatever it costs."""
        parts = _listing('222', '55.00', title='NXEDGE Style Xi Gundam Genuine Replacement Parts')
        row, _ = self._run([_listing('111', '100.00'), parts])
        self.assertIn('/itm/111', row.url)

    def test_implausibly_cheap_listing_is_ignored(self):
        """A $45 listing for a $100 kit (under 50% of the Gundam Planet price) is not the kit."""
        row, _ = self._run([_listing('111', '100.00'), _listing('222', '45.00')])
        self.assertIn('/itm/111', row.url)

    def test_listing_at_half_the_gundam_planet_price_can_win(self):
        """At exactly 50% of the Gundam Planet price the floor lets a cheaper listing win."""
        row, _ = self._run([_listing('111', '100.00'), _listing('222', '50.00')])
        self.assertIn('/itm/222', row.url)

    def test_accessory_set_never_wins_even_when_cheapest(self):
        """An "Option Set" or "Expansion" listing is an add-on, not the kit."""
        for word in ('Option Set', 'Expansion Unit', 'Hyper Launcher'):
            row, _ = self._run([_listing('111', '100.00'), _listing('222', '55.00', title=f'NXEDGE Style Xi Gundam {word}')])
            self.assertIn('/itm/111', row.url, word)

    def test_cheaper_listing_outside_the_first_ten_results_is_ignored(self):
        """Like Warhammer, a cheaper listing must come from the first 10 Best Match results."""
        filler = [_listing(str(300 + n), '99.00') for n in range(10)]
        row, _ = self._run([_listing('111', '100.00')] + filler + [_listing('222', '60.00')])
        self.assertIn('/itm/111', row.url)

    def test_cheaper_listing_inside_the_first_ten_results_is_taken(self):
        """The 10th result is still inside the window."""
        filler = [_listing(str(300 + n), '99.00') for n in range(8)]
        row, _ = self._run([_listing('111', '100.00')] + filler + [_listing('222', '60.00')])
        self.assertIn('/itm/222', row.url)

    def test_cheaper_listing_missing_a_kit_name_word_is_ignored(self):
        """"Metal Build Freedom Gundam" never replaces "Metal Build Zeta Gundam" just for being cheaper."""
        self.product.name = 'Metal Build Zeta Gundam'
        self.product.save()
        row, _ = self._run([_listing('111', '100.00', title='Metal Build Zeta Gundam Bandai'),
                            _listing('222', '60.00', title='METAL BUILD Freedom Gundam Bandai')])
        self.assertIn('/itm/111', row.url)

    def test_kit_named_with_a_parts_word_still_matches(self):
        """A kit whose own name says "Parts Set" is not rejected for that word."""
        self.product.name = 'SD Cross Silhouette Banshee Parts Set'
        self.product.save()
        item = _listing('333', '70.00', title='SD Cross Silhouette Banshee Parts Set')
        row, _ = self._run([item])
        self.assertIn('/itm/333', row.url)

    def test_us_listing_beats_a_worldwide_one_under_25_percent_cheaper(self):
        """A worldwide listing 14% cheaper delivered is not worth the duties and the wait."""
        row, abroad = self._run([_listing('111', '100.00')], [_listing('222', '85.00', 'JP')])
        self.assertIn('/itm/111', row.url)
        abroad.assert_called_once()

    def test_worldwide_listing_wins_when_25_percent_cheaper_delivered(self):
        """A worldwide listing 36% cheaper delivered replaces the best US listing."""
        row, _ = self._run([_listing('111', '100.00')], [_listing('222', '60.00', 'JP')])
        self.assertIn('/itm/222', row.url)

    def test_worldwide_listing_exactly_at_the_margin_wins(self):
        """$82.50 delivered against $110 delivered is exactly 25% cheaper, so it wins."""
        row, _ = self._run([_listing('111', '100.00')], [_listing('222', '72.50', 'JP')])
        self.assertIn('/itm/222', row.url)

    def test_us_listing_from_the_worldwide_search_needs_only_ten_percent(self):
        """The worldwide search also returns US-located listings; those only need the usual 10% gap."""
        row, _ = self._run([_listing('111', '100.00')], [_listing('222', '85.00', 'US')])
        self.assertIn('/itm/222', row.url)

    def test_cheaper_sri_lanka_listing_never_wins(self):
        """A 40% cheaper listing from a Sri Lanka seller is skipped and the US listing stays."""
        row, _ = self._run([_listing('111', '100.00')], [_listing('222', '60.00', 'LK')])
        self.assertIn('/itm/111', row.url)

    def test_cheaper_china_listing_never_wins(self):
        """A 40% cheaper listing from a China seller is skipped and the US listing stays."""
        row, _ = self._run([_listing('111', '100.00')], [_listing('222', '60.00', 'CN')])
        self.assertIn('/itm/111', row.url)

    def test_avoided_country_is_skipped_when_no_us_listing_passes(self):
        """With no US listing, the next worldwide listing is used instead of the avoided seller's."""
        row, _ = self._run([], [_listing('222', '60.00', 'CN'), _listing('333', '95.00', 'JP')])
        self.assertIn('/itm/333', row.url)

    def test_other_countries_are_still_allowed(self):
        """Only the avoided countries are filtered: a 40% cheaper Hong Kong listing still wins."""
        row, _ = self._run([_listing('111', '100.00')], [_listing('222', '60.00', 'HK')])
        self.assertIn('/itm/222', row.url)

    def test_abroad_pool_also_takes_the_cheapest(self):
        """With no US listing, the abroad pool follows the same cheapest rule."""
        row, _ = self._run([], [_listing('222', '100.00', 'JP'), _listing('333', '60.00', 'JP')])
        self.assertIn('/itm/333', row.url)

    def test_falls_back_to_best_match_when_the_cheapest_cannot_be_priced(self):
        """If the cheapest has no resolvable shipping, Best Match #1 is used instead of nothing."""
        from decimal import Decimal
        row, _ = self._run([_listing('111', '100.00'), _listing('222', '60.00')],
                           shipping=lambda item_id: None if '|222|' in item_id else Decimal('10.00'))
        self.assertIn('/itm/111', row.url)


class AbroadFallbackTest(TestCase):
    """US listings win; sellers abroad are used only when no US listing passes (Gundam only)."""

    def setUp(self):
        """Create one kit, the eBay retailer, and an empty eBay price row."""
        from products.models import Retailer
        series = Series.objects.create(name='Mobile Suit Test Gundam')
        self.product = Product.objects.create(name='NXEDGE Style Xi Gundam', slug='nx-xi', series=series, batch_tag='test')
        self.ebay = Retailer.objects.create(name='eBay', slug='ebay')

    def _run(self, us_items, abroad_items, apply=False):
        """Run the command with a fake eBay client; return (output, abroad mock)."""
        from decimal import Decimal
        from io import StringIO
        from unittest import mock
        from django.core.management import call_command
        from .management.commands import find_gundam_ebay_prices as cmd
        fake = mock.MagicMock()
        fake.search_items.return_value = us_items
        fake._fetch_item_shipping.return_value = Decimal('10.00')
        out = StringIO()
        args = ['--batch-tag', 'test'] + (['--apply'] if apply else [])
        with mock.patch.object(cmd, 'EbayBrowseAPI', return_value=fake), \
                mock.patch.object(cmd, '_search_outside_us', return_value=abroad_items) as abroad, \
                mock.patch.object(cmd.time, 'sleep'):
            call_command('find_gundam_ebay_prices', *args, stdout=out)
        return out.getvalue(), abroad

    def test_us_listing_wins_over_a_slightly_cheaper_worldwide_one(self):
        """A worldwide listing only 20% cheaper delivered does not displace the US listing."""
        out, abroad = self._run([_listing('111', '90.00', 'US')], [_listing('222', '70.00', 'JP')])
        abroad.assert_called_once()
        self.assertNotIn('ABROAD', out)

    def test_abroad_used_only_when_no_us_listing_passes(self):
        """With no US match the fallback runs, is tagged, and the price adds US shipping."""
        from decimal import Decimal
        from .models import CurrentPrice as GundamPrice
        out, abroad = self._run([], [_listing('222', '90.00', 'JP')], apply=True)
        abroad.assert_called_once()
        self.assertIn('[ABROAD JP]', out)
        row = GundamPrice.objects.get(product=self.product, retailer=self.ebay)
        self.assertEqual(row.price, Decimal('100.00'))
        self.assertTrue(row.url.startswith('https://www.ebay.com/itm/222'))
        self.assertTrue(row.in_stock and not row.not_available)

    def test_nothing_written_when_neither_search_matches(self):
        """A wrong-kit listing abroad does not match, and no row is written."""
        from .models import CurrentPrice as GundamPrice
        out, abroad = self._run([], [_listing('333', '50.00', 'JP', title='NXEDGE Style Exia Gundam')], apply=True)
        self.assertFalse(GundamPrice.objects.filter(product=self.product).exists())
        self.assertIn('Matched      : 0', out)

    def test_worldwide_request_filter_and_parsing(self):
        """The abroad request ships-to-US, has no US-location filter, keeps the seller country, drops non-USD."""
        from unittest import mock
        from products.ebay_api_client import EbayBrowseAPI
        from .management.commands.find_gundam_ebay_prices import _search_outside_us
        client = mock.MagicMock()
        client.api_calls_made = 0
        client._get_access_token.return_value = 'tok'
        client._parse_item = EbayBrowseAPI._parse_item
        raw = [
            {'itemId': 'v1|1|0', 'title': 'Xi Gundam', 'itemWebUrl': 'https://www.ebay.com/itm/1', 'price': {'value': '80', 'currency': 'USD'}, 'itemLocation': {'country': 'JP'}},
            {'itemId': 'v1|2|0', 'title': 'Xi Gundam gbp', 'itemWebUrl': 'https://www.ebay.com/itm/2', 'price': {'value': '60', 'currency': 'GBP'}, 'itemLocation': {'country': 'GB'}},
        ]
        client.session.get.return_value = mock.MagicMock(ok=True, **{'json.return_value': {'itemSummaries': raw}})
        listings = _search_outside_us(client, 'xi gundam')
        params = client.session.get.call_args.kwargs['params']
        self.assertIn('deliveryCountry:US', params['filter'])
        self.assertIn('conditions:{NEW}', params['filter'])
        self.assertNotIn('itemLocationCountry', params['filter'])
        self.assertEqual([(x['item_id'], x['ships_from']) for x in listings], [('v1|1|0', 'JP')])
        self.assertEqual(client.api_calls_made, 1)

    def _link(self, item_id='111'):
        """Give the kit a stored eBay link and return the price row."""
        from decimal import Decimal
        from .models import CurrentPrice as GundamPrice
        return GundamPrice.objects.create(
            product=self.product, retailer=self.ebay, price=Decimal('50.00'),
            url=f'https://www.ebay.com/itm/{item_id}?old=1', in_stock=True)

    def _run_rematch(self, us_items, apply=True):
        """Run the command with --rematch for the test kit and a fake eBay client."""
        from decimal import Decimal
        from io import StringIO
        from unittest import mock
        from django.core.management import call_command
        from .management.commands import find_gundam_ebay_prices as cmd
        fake = mock.MagicMock()
        fake.search_items.return_value = us_items
        fake._fetch_item_shipping.return_value = Decimal('10.00')
        out = StringIO()
        args = ['--batch-tag', 'test', '--rematch', str(self.product.pk)] + (['--apply'] if apply else [])
        with mock.patch.object(cmd, 'EbayBrowseAPI', return_value=fake), \
                mock.patch.object(cmd, '_search_outside_us', return_value=[]), \
                mock.patch.object(cmd.time, 'sleep'):
            call_command('find_gundam_ebay_prices', *args, stdout=out)
        return out.getvalue()

    def test_linked_kit_is_left_alone_without_rematch(self):
        """A kit that already has a link is not searched unless --rematch names it."""
        row = self._link()
        out, abroad = self._run([_listing('222', '70.00', 'US')], [], apply=True)
        row.refresh_from_db()
        self.assertIn('/itm/111', row.url)
        self.assertIn('Have URL : 1', out)

    def test_rematch_replaces_the_link_when_a_match_is_found(self):
        """--rematch searches a linked kit and a new match replaces its link and price."""
        from decimal import Decimal
        row = self._link()
        self._run_rematch([_listing('222', '70.00', 'US')])
        row.refresh_from_db()
        self.assertIn('/itm/222', row.url)
        self.assertEqual(row.price, Decimal('80.00'))

    def test_rematch_never_empties_a_link_when_nothing_matches(self):
        """With no match the stored link and price stay exactly as they were."""
        from decimal import Decimal
        row = self._link()
        out = self._run_rematch([_listing('333', '50.00', 'US', title='NXEDGE Style Exia Gundam')])
        row.refresh_from_db()
        self.assertIn('/itm/111', row.url)
        self.assertEqual(row.price, Decimal('50.00'))
        self.assertIn('existing link kept', out)

    def test_shared_client_still_searches_us_listings_only(self):
        """The shared client (used by Warhammer) is unchanged: it still filters to US-located listings."""
        import inspect
        from products.ebay_api_client import EbayBrowseAPI
        source = inspect.getsource(EbayBrowseAPI.search_items)
        self.assertIn('itemLocationCountry:US', source)
        self.assertNotIn('deliveryCountry', source)
