"""
Tests for the partial (daily slice) refresh mode and its safeguards.

Every test here is database free (SimpleTestCase refuses database access), so
they are safe to run with .env pointed at the production database:

    python manage.py shell -c "import unittest; unittest.main(module='scrapers.tests', argv=['x'], exit=False)"
"""

from decimal import Decimal
from io import StringIO
from types import SimpleNamespace
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from scrapers.retailers import firestorm_games_uk as fs_module
from scrapers.retailers import miniature_market as mm_module
from scrapers.retailers import noble_knight as nk_module
from scrapers.safeguards import RunGuard, finish_run, parse_shard, select_slice


# ── helpers ──────────────────────────────────────────────────────────────────

class FakeResponse:
    """Just enough of a curl_cffi response."""

    def __init__(self, status=200, text='', url='', content=None):
        self.status_code = status
        self.text = text
        self.content = content if content is not None else text.encode('utf-8')
        self.url = url


class FakeSession:
    """Hands out scripted responses (or raises scripted exceptions)."""

    def __init__(self, *responses):
        self.responses = list(responses)

    def get(self, url, timeout=15):
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeEntry:
    """Stands in for a CurrentPrice row and records how it was saved."""

    _next_id = 1

    def __init__(self, price='10.00', url='https://www.nobleknight.com/P/1/Kit?awid=1576', active=True):
        self.id = FakeEntry._next_id
        FakeEntry._next_id += 1
        self.product = SimpleNamespace(is_active=active, name='Product %d' % self.id, gw_sku='SKU-%d' % self.id)
        self.price = Decimal(price) if price is not None else None
        self.in_stock = True
        self.not_available = False
        self.url = url
        self.saves = []

    def save(self, update_fields=None):
        self.saves.append(tuple(update_fields or ()))


def fake_job():
    return SimpleNamespace(products_found=0, prices_updated=0, status='running', errors='',
                           started_at=None, finished_at=None, save=lambda: None)


def padding():
    return '<!-- ' + 'x' * 6000 + ' -->'


def nk_page(price='Our Price $31.95', cart=True, title='Kit | Noble Knight Games'):
    button = '<button class="atc">Add to Cart</button>' if cart else ''
    return ('<html><head><title>%s</title></head><body><span class="price">%s</span>%s%s</body></html>'
            % (title, price, button, padding()))


def fs_page(price='Our Price: £47.96', cart=True, title='Kit | Firestorm Games'):
    button = '<a class="btnAddToBasket">ADD TO CART</a>' if cart else ''
    return ('<html><head><title>%s</title></head><body><h3 class="price orange">%s</h3>%s%s</body></html>'
            % (title, price, button, padding()))


def mm_page(price='$53.99', title='Kit | Miniature Market'):
    return ('<html><head><title>%s</title></head><body><span class="price">%s</span>'
            '<button>Add to Cart</button>%s</body></html>' % (title, price, padding()))


NK_URL = 'https://www.nobleknight.com/P/2148337824/Cygnar-Gravediggers-Command-Starter-Set'
FS_URL = 'https://www.firestormgames.co.uk/adepta-sororitas-canoness'
MM_URL = 'https://www.miniaturemarket.com/warmachine-alexia-queen-damned-sfik-mer092.html'


# ── safeguards ───────────────────────────────────────────────────────────────

class ParseShardTests(SimpleTestCase):
    def test_valid(self):
        self.assertEqual(parse_shard('3/7'), (3, 7))
        self.assertEqual(parse_shard('0/1'), (0, 1))

    def test_invalid(self):
        for bad in ('7/7', '-1/7', '3', '3/0', 'a/b', '', '3/7/9', None):
            with self.assertRaises(ValueError, msg=repr(bad)):
                parse_shard(bad)


class SelectSliceTests(SimpleTestCase):
    class FakeQS:
        def __init__(self):
            self.calls = []

        def annotate(self, **kwargs):
            self.calls.append(('annotate', sorted(kwargs)))
            return self

        def filter(self, **kwargs):
            self.calls.append(('filter', kwargs))
            return self

        def order_by(self, *args):
            self.calls.append(('order_by', args))
            return self

        def __getitem__(self, item):
            self.calls.append(('slice', item.stop))
            return self

    def test_no_options_returns_the_queryset_untouched(self):
        qs = self.FakeQS()
        self.assertIs(select_slice(qs), qs)
        self.assertEqual(qs.calls, [])

    def test_shard_and_limit(self):
        qs = self.FakeQS()
        select_slice(qs, (3, 7), 500)
        self.assertEqual(qs.calls, [('annotate', ['shard_bucket']), ('filter', {'shard_bucket': 3}),
                                    ('order_by', ('id',)), ('slice', 500)])

    def test_limit_only_keeps_a_stable_order(self):
        qs = self.FakeQS()
        select_slice(qs, None, 25)
        self.assertEqual(qs.calls, [('order_by', ('id',)), ('slice', 25)])


class RunGuardTests(SimpleTestCase):
    def test_trips_after_consecutive_failures_only(self):
        guard = RunGuard()
        for _ in range(7):
            guard.record_failure()
        self.assertFalse(guard.tripped)
        guard.record_ok()
        for _ in range(7):
            guard.record_failure(blocked=True)
        self.assertFalse(guard.tripped)
        guard.record_failure(blocked=True)
        self.assertTrue(guard.tripped)
        self.assertIn('blocked', guard.tripped_reason)

    def test_blank_limit_scales_with_rows_checked(self):
        guard = RunGuard()
        self.assertEqual(guard.allowed_blanks(), 10)
        for _ in range(300):
            guard.record_ok(was_priced=True)
        self.assertEqual(guard.allowed_blanks(), 30)

    def test_apply_blanks_clears_price_and_stock(self):
        guard = RunGuard()
        entry = FakeEntry(price='12.50')
        guard.defer_blank(entry, 'no price')
        self.assertEqual(guard.apply_blanks(), 1)
        self.assertIsNone(entry.price)
        self.assertFalse(entry.in_stock)
        self.assertEqual(entry.saves, [('price', 'in_stock', 'last_seen')])


class FinishRunTests(SimpleTestCase):
    def test_tripped_guard_fails_and_blanks_nothing(self):
        guard = RunGuard()
        entry = FakeEntry()
        guard.defer_blank(entry, 'no price')
        for _ in range(8):
            guard.record_failure(blocked=True)
        job, errors = fake_job(), []
        self.assertEqual(finish_run(job, guard, errors, 'x'), 'failed')
        self.assertEqual(entry.saves, [])
        self.assertTrue(job.errors.startswith('ABORTED'))

    def test_believable_blanks_are_applied(self):
        guard = RunGuard()
        entries = [FakeEntry() for _ in range(3)]
        for e in entries:
            guard.defer_blank(e, 'no price')
        self.assertEqual(finish_run(fake_job(), guard, [], 'x'), 'success')
        self.assertTrue(all(e.price is None for e in entries))

    def test_too_many_blanks_apply_nothing_and_fail(self):
        guard = RunGuard()
        entries = [FakeEntry() for _ in range(40)]
        for e in entries:
            guard.record_ok(was_priced=True)
            guard.defer_blank(e, 'no price')
        job = fake_job()
        self.assertEqual(finish_run(job, guard, [], 'x'), 'failed')
        self.assertTrue(all(e.price is not None and e.saves == [] for e in entries))
        self.assertIn('NOT APPLIED', job.errors)


# ── Noble Knight ─────────────────────────────────────────────────────────────

class NobleKnightFetchTests(SimpleTestCase):
    def setUp(self):
        self.scraper = nk_module.NoblekKnightScraper()

    def fetch(self, *responses, url=NK_URL):
        self.scraper.session = FakeSession(*responses)
        return self.scraper._fetch_page(url)

    def test_normal_product_page(self):
        kind, price, in_stock = self.fetch(FakeResponse(text=nk_page(), url=NK_URL))
        self.assertEqual((kind, price, in_stock), ('ok', Decimal('31.95'), True))

    def test_sale_listing_uses_the_new_price(self):
        page = nk_page(price='Was old price: $138.95 New Price $117.95')
        self.assertEqual(self.fetch(FakeResponse(text=page, url=NK_URL))[1], Decimal('117.95'))

    def test_sold_out_page_has_no_price(self):
        self.assertEqual(self.fetch(FakeResponse(text=nk_page(price='Sold out', cart=False), url=NK_URL))[0], 'no_price')

    def test_delisted_link_that_lands_on_the_homepage_is_a_dead_link(self):
        home = nk_page(price='Our Price $58.95', title='Noble Knight Games - RPGs')
        kind, price, _ = self.fetch(FakeResponse(text=home, url='https://www.nobleknight.com/'))
        self.assertEqual((kind, price), ('dead_link', None))

    def test_slug_change_or_shared_page_is_not_a_dead_link(self):
        renamed = FakeResponse(text=nk_page(), url='https://www.nobleknight.com/P/2148337824/New-Slug')
        self.assertEqual(self.fetch(renamed)[0], 'ok')
        other_number = FakeResponse(text=nk_page(), url='https://www.nobleknight.com/P/999/Shared-Kit')
        self.assertEqual(self.fetch(other_number)[0], 'ok')

    def test_status_and_error_classification(self):
        self.assertEqual(self.fetch(FakeResponse(status=404))[0], 'not_found')
        self.assertEqual(self.fetch(FakeResponse(status=403))[0], 'blocked')
        self.assertEqual(self.fetch(FakeResponse(status=429))[0], 'blocked')
        self.assertEqual(self.fetch(FakeResponse(status=500))[0], 'error')
        self.assertEqual(self.fetch(RuntimeError('boom'))[0], 'error')
        self.assertEqual(self.fetch(FakeResponse(text='<html>tiny</html>', url=NK_URL))[0], 'blocked')
        challenge = nk_page(title='Just a moment...')
        self.assertEqual(self.fetch(FakeResponse(text=challenge, url=NK_URL))[0], 'blocked')

    def test_legacy_wrapper_keeps_its_contract(self):
        self.scraper.session = FakeSession(FakeResponse(text=nk_page(), url=NK_URL))
        self.assertEqual(self.scraper._fetch_price(NK_URL), (Decimal('31.95'), True))
        self.scraper.session = FakeSession(FakeResponse(text=nk_page(price='x', cart=False), url=NK_URL))
        self.assertIsNone(self.scraper._fetch_price(NK_URL))
        self.scraper.session = FakeSession(FakeResponse(status=404))
        self.assertIs(self.scraper._fetch_price(NK_URL), nk_module._FETCH_ERROR)
        home = FakeResponse(text=nk_page(), url='https://www.nobleknight.com/')
        self.scraper.session = FakeSession(home)
        self.assertIs(self.scraper._fetch_price(NK_URL), nk_module._FETCH_ERROR)


class NobleKnightRunTests(SimpleTestCase):
    def run_scraper(self, entries, outcomes):
        """Run the scraper over fake rows; outcomes are scripted _fetch_page results."""
        scraper = nk_module.NoblekKnightScraper()
        scraper._fetch_page = mock.Mock(side_effect=list(outcomes))
        job = fake_job()
        with mock.patch.object(nk_module, 'Retailer'), \
                mock.patch.object(nk_module, 'ScrapeJob') as job_cls, \
                mock.patch.object(nk_module.NoblekKnightScraper, '_base_entries', return_value=entries), \
                mock.patch('time.sleep'):
            job_cls.objects.create.return_value = job
            scraper.run()
        return job

    def ok(self, price='20.00'):
        return ('ok', Decimal(price), True)

    def test_normal_run_updates_prices_and_saves_last_seen(self):
        entries = [FakeEntry('10.00') for _ in range(3)]
        job = self.run_scraper(entries, [self.ok('11.00'), self.ok('12.00'), self.ok('13.00')])
        self.assertEqual((job.status, job.prices_updated), ('success', 3))
        self.assertEqual(entries[0].price, Decimal('11.00'))
        self.assertEqual(entries[0].saves, [('price', 'in_stock', 'not_available', 'last_seen')])

    def test_blocked_run_stops_early_and_changes_nothing_further(self):
        entries = [FakeEntry('10.00') for _ in range(12)]
        job = self.run_scraper(entries, [('blocked', None, False)] * 12)
        self.assertEqual(job.status, 'failed')
        self.assertIn('ABORTED', job.errors)
        self.assertEqual(job.products_found, 8)
        self.assertTrue(all(e.saves == [] for e in entries))

    def test_sold_out_rows_are_blanked_at_the_end_when_few(self):
        entries = [FakeEntry('10.00') for _ in range(30)]
        outcomes = [('no_price', None, False), ('no_price', None, False)] + [self.ok()] * 28
        job = self.run_scraper(entries, outcomes)
        self.assertEqual(job.status, 'success')
        self.assertIsNone(entries[0].price)
        self.assertFalse(entries[0].in_stock)
        self.assertEqual(entries[2].price, Decimal('20.00'))

    def test_mass_no_price_means_nothing_is_blanked(self):
        entries = [FakeEntry('10.00') for _ in range(60)]
        outcomes = [('no_price', None, False)] * 40 + [self.ok()] * 20
        job = self.run_scraper(entries, outcomes)
        self.assertEqual(job.status, 'failed')
        self.assertIn('NOT APPLIED', job.errors)
        self.assertTrue(all(e.price == Decimal('10.00') for e in entries[:40]))

    def test_dead_link_blanks_a_priced_row_and_is_reported(self):
        entries = [FakeEntry('58.95'), FakeEntry('10.00')]
        job = self.run_scraper(entries, [('dead_link', None, False), ('dead_link', None, False), self.ok()])
        self.assertEqual(job.status, 'success')
        self.assertIsNone(entries[0].price)
        self.assertIn('[dead-link]', job.errors)

    def test_dead_link_that_is_fine_on_the_second_look_is_updated(self):
        entries = [FakeEntry('10.00')]
        job = self.run_scraper(entries, [('dead_link', None, False), self.ok('21.00')])
        self.assertEqual(entries[0].price, Decimal('21.00'))
        self.assertEqual(job.errors, '')

    def test_not_found_leaves_the_row_alone_and_is_listed(self):
        entries = [FakeEntry('10.00')]
        job = self.run_scraper(entries, [('not_found', None, False)])
        self.assertEqual((job.status, entries[0].price, entries[0].saves), ('success', Decimal('10.00'), []))
        self.assertIn('[stale-link]', job.errors)

    def test_no_price_on_an_already_blank_row_is_only_touched(self):
        entries = [FakeEntry(None)]
        self.run_scraper(entries, [('no_price', None, False)])
        self.assertEqual(entries[0].saves, [('last_seen',)])

    def test_inactive_and_non_nk_rows_are_skipped(self):
        entries = [FakeEntry(active=False), FakeEntry(url='https://example.com/x')]
        job = self.run_scraper(entries, [])
        self.assertEqual(job.products_found, 0)

    def run_with_crashing_rows(self, entries, side_effect):
        """Run over fake rows where _refresh_entry itself raises (for example a lost database)."""
        scraper = nk_module.NoblekKnightScraper()
        job = fake_job()
        with mock.patch.object(nk_module, 'Retailer'), \
                mock.patch.object(nk_module, 'ScrapeJob') as job_cls, \
                mock.patch.object(nk_module.NoblekKnightScraper, '_base_entries', return_value=entries), \
                mock.patch.object(nk_module.NoblekKnightScraper, '_refresh_entry', side_effect=side_effect), \
                mock.patch('scrapers.safeguards.close_old_connections') as reconnect, \
                mock.patch('time.sleep'):
            job_cls.objects.create.return_value = job
            scraper.run()
        return job, reconnect

    def test_a_run_that_crashes_on_every_row_stops_after_eight(self):
        entries = [FakeEntry('10.00') for _ in range(20)]
        job, reconnect = self.run_with_crashing_rows(entries, RuntimeError('connection lost'))
        self.assertEqual((job.status, job.products_found), ('failed', 8))
        self.assertIn('ABORTED', job.errors)
        self.assertEqual(reconnect.call_count, 8)

    def test_one_crashing_row_does_not_stop_the_run(self):
        entries = [FakeEntry('10.00') for _ in range(3)]
        job, reconnect = self.run_with_crashing_rows(entries, [RuntimeError('odd page'), None, None])
        self.assertEqual((job.status, job.products_found), ('success', 3))
        self.assertEqual(reconnect.call_count, 1)
        self.assertIn('odd page', job.errors)


# ── Firestorm ────────────────────────────────────────────────────────────────

class FirestormTests(SimpleTestCase):
    def setUp(self):
        self.scraper = fs_module.FirestormGamesUKScraper()

    def fetch(self, *responses):
        self.scraper.session = FakeSession(*responses)
        return self.scraper._fetch_page(FS_URL)

    def test_classification(self):
        self.assertEqual(self.fetch(FakeResponse(text=fs_page()))[:2], ('ok', Decimal('47.96')))
        self.assertEqual(self.fetch(FakeResponse(text=fs_page(price='Sold out', cart=False)))[0], 'no_price')
        self.assertEqual(self.fetch(FakeResponse(status=404))[0], 'not_found')
        self.assertEqual(self.fetch(FakeResponse(status=403, text='Just a moment'))[0], 'blocked')
        self.assertEqual(self.fetch(FakeResponse(text=fs_page(title='Just a moment...')))[0], 'blocked')
        self.assertEqual(self.fetch(FakeResponse(text='<html>tiny</html>'))[0], 'blocked')
        self.assertEqual(self.fetch(RuntimeError('boom'))[0], 'error')

    def test_notify_me_page_is_out_of_stock(self):
        page = fs_page().replace('ADD TO CART', 'Notify me when back')
        self.assertFalse(self.fetch(FakeResponse(text=page))[2])

    def test_a_404_is_not_retried(self):
        self.scraper._fetch_page = mock.Mock(return_value=('not_found', None, False))
        with mock.patch('time.sleep'):
            self.scraper._fetch_with_retries(FS_URL)
        self.assertEqual(self.scraper._fetch_page.call_count, 1)

    def test_a_network_error_is_retried_twice(self):
        self.scraper._fetch_page = mock.Mock(return_value=('error', None, False))
        with mock.patch('time.sleep'):
            self.scraper._fetch_with_retries(FS_URL)
        self.assertEqual(self.scraper._fetch_page.call_count, 3)

    def test_blocked_run_stops_after_eight_rows(self):
        entries = [FakeEntry('10.00', url=FS_URL + '?aff=x') for _ in range(12)]
        self.scraper._fetch_page = mock.Mock(return_value=('blocked', None, False))
        job = fake_job()
        with mock.patch.object(fs_module, 'Retailer'), mock.patch.object(fs_module, 'ScrapeJob') as job_cls, \
                mock.patch.object(fs_module.FirestormGamesUKScraper, '_base_entries', return_value=entries), \
                mock.patch('time.sleep'):
            job_cls.objects.create.return_value = job
            self.scraper.run()
        self.assertEqual((job.status, job.products_found), ('failed', 8))
        self.assertTrue(all(e.saves == [] for e in entries))
        self.assertEqual(self.scraper._fetch_page.call_count, 8)


# ── Miniature Market ─────────────────────────────────────────────────────────

class MiniatureMarketRefreshTests(SimpleTestCase):
    def setUp(self):
        self.scraper = mm_module.MiniatureMarketScraper()

    def fetch(self, *responses):
        self.scraper.session = FakeSession(*responses)
        return self.scraper._fetch_for_refresh(MM_URL)

    def test_classification(self):
        self.assertEqual(self.fetch(FakeResponse(text=mm_page(), url=MM_URL))[:2], ('ok', Decimal('53.99')))
        self.assertEqual(self.fetch(FakeResponse(text=mm_page(price='n/a'), url=MM_URL))[0], 'no_price')
        self.assertEqual(self.fetch(FakeResponse(status=404))[0], 'not_found')
        self.assertEqual(self.fetch(FakeResponse(text=mm_page(), url='https://www.miniaturemarket.com/'))[0], 'not_found')
        self.assertEqual(self.fetch(FakeResponse(status=403))[0], 'blocked')
        self.assertEqual(self.fetch(FakeResponse(text=mm_page(title='Just a moment...'), url=MM_URL))[0], 'blocked')
        self.assertEqual(self.fetch(FakeResponse(text='<html>tiny</html>', url=MM_URL))[0], 'blocked')
        self.assertEqual(self.fetch(RuntimeError('boom'))[0], 'error')

    @staticmethod
    def stock_page(main_button='', main_text='', tile_text=''):
        """A product page: optional main buy button, optional text in the main box, one related-product tile."""
        return (
            '<html><head><title>Kit | Miniature Market</title></head><body>'
            '<div class="product-detail-form-container"><span class="price">$53.99</span>%s%s</div>'
            '<div class="card product-box"><span>%s</span><button class="btn btn-buy">Add to cart</button></div>%s'
            '</body></html>' % (main_button, main_text, tile_text, padding())
        )

    LIVE_BUTTON = '<button class="btn btn-primary btn-buy product-detail-btn">Add to cart</button>'

    def stock(self, page):
        return self.fetch(FakeResponse(text=page, url=MM_URL))[2]

    def test_in_stock_when_the_main_button_is_live_even_if_a_related_tile_says_out_of_stock(self):
        self.assertTrue(self.stock(self.stock_page(self.LIVE_BUTTON, tile_text='Out of stock')))

    def test_out_of_stock_when_there_is_no_main_button_and_the_main_box_says_so(self):
        self.assertFalse(self.stock(self.stock_page(main_text='Out of stock')))

    def test_out_of_stock_when_the_main_button_is_disabled(self):
        disabled = '<button class="btn product-detail-btn" disabled>Out of stock</button>'
        self.assertFalse(self.stock(self.stock_page(disabled, main_text='Out of stock')))

    def test_a_related_tile_button_alone_does_not_count_as_in_stock(self):
        page = self.stock_page(main_text='Out of stock', tile_text='Out of stock')
        self.assertFalse(self.stock(page))

    def test_old_logic_still_applies_when_there_is_no_main_button_and_no_phrase(self):
        self.assertTrue(self.stock(self.stock_page()))

    def test_the_search_path_uses_the_same_rule(self):
        self.scraper.session = FakeSession(FakeResponse(text=self.stock_page(self.LIVE_BUTTON, tile_text='Out of stock')))
        self.assertTrue(self.scraper._check_stock(MM_URL))
        self.scraper.session = FakeSession(FakeResponse(text=self.stock_page(main_text='Out of stock')))
        self.assertFalse(self.scraper._check_stock(MM_URL))

    def refresh(self, entries, outcomes):
        self.scraper._fetch_for_refresh = mock.Mock(side_effect=list(outcomes))
        job = fake_job()
        with mock.patch.object(mm_module, 'Retailer'), mock.patch.object(mm_module, 'ScrapeJob') as job_cls, \
                mock.patch.object(mm_module.MiniatureMarketScraper, '_refresh_entries', return_value=entries), \
                mock.patch.object(mm_module, 'select_slice', side_effect=lambda qs, shard, limit: qs), \
                mock.patch('time.sleep'):
            job_cls.objects.create.return_value = job
            self.scraper.run(shard=(1, 7))
        return job

    def test_ok_rows_are_updated_and_problem_rows_are_left_alone(self):
        entries = [FakeEntry('10.00', url=MM_URL) for _ in range(3)]
        outcomes = [('ok', Decimal('11.99'), False), ('not_found', None, False), ('no_price', None, False)]
        job = self.refresh(entries, outcomes)
        self.assertEqual((job.status, job.prices_updated), ('success', 1))
        self.assertEqual((entries[0].price, entries[0].in_stock), (Decimal('11.99'), False))
        self.assertTrue(all(e.price == Decimal('10.00') and e.saves == [] for e in entries[1:]))
        self.assertIn('[check-link]', job.errors)

    def test_blocked_run_does_nothing_and_fails(self):
        entries = [FakeEntry('10.00', url=MM_URL) for _ in range(12)]
        job = self.refresh(entries, [('blocked', None, False)] * 12)
        self.assertEqual(job.status, 'failed')
        self.assertTrue(all(e.saves == [] and e.price == Decimal('10.00') for e in entries))

    def test_a_run_that_crashes_on_every_row_stops_after_eight(self):
        entries = [FakeEntry('10.00', url=MM_URL) for _ in range(20)]
        job = fake_job()
        with mock.patch.object(mm_module, 'Retailer'), mock.patch.object(mm_module, 'ScrapeJob') as job_cls, \
                mock.patch.object(mm_module.MiniatureMarketScraper, '_refresh_entries', return_value=entries), \
                mock.patch.object(mm_module, 'select_slice', side_effect=lambda qs, shard, limit: qs), \
                mock.patch.object(mm_module.MiniatureMarketScraper, '_refresh_one', side_effect=RuntimeError('lost')), \
                mock.patch('scrapers.safeguards.close_old_connections'), mock.patch('time.sleep'):
            job_cls.objects.create.return_value = job
            self.scraper.run(shard=(1, 7))
        self.assertEqual((job.status, job.products_found), ('failed', 8))
        self.assertTrue(all(e.saves == [] for e in entries))

    def test_full_run_signature_is_unchanged_without_options(self):
        class Boom(Exception):
            pass

        with mock.patch.object(mm_module.MiniatureMarketScraper, '_run_refresh') as refresh,                 mock.patch.object(mm_module.Retailer.objects, 'get', side_effect=Boom('legacy path reached')):
            with self.assertRaises(Boom):
                self.scraper.run()
        refresh.assert_not_called()


# ── run_scrapers command ─────────────────────────────────────────────────────

class FakeShardScraper:
    calls = []

    def run(self, batch_tag=None, shard=None, limit=None):
        FakeShardScraper.calls.append((batch_tag, shard, limit))
        return SimpleNamespace(status='success', products_found=1, prices_updated=1, errors='')

    def select_entries(self, batch_tag=None, shard=None, limit=None):
        return [FakeEntry()]


class FakeOldScraper:
    calls = []

    def run(self, batch_tag=None):
        FakeOldScraper.calls.append(batch_tag)
        return SimpleNamespace(status='success', products_found=1, prices_updated=1, errors='')


class FakeFailingScraper:
    def run(self, batch_tag=None, shard=None, limit=None):
        return SimpleNamespace(status='failed', products_found=8, prices_updated=0, errors='ABORTED: blocked')


class FakeCrashingOldScraper:
    """A scraper without the run guard (like Amazon) whose run() raises."""

    def run(self, batch_tag=None):
        raise RuntimeError('boom')


class FakeCrashingGuardedScraper:
    """A scraper with the run guard whose run() raises."""

    def run(self, batch_tag=None, shard=None, limit=None):
        raise RuntimeError('boom')

    def select_entries(self, batch_tag=None, shard=None, limit=None):
        return []


class RunScrapersCommandTests(SimpleTestCase):
    REGISTRY = {
        'shardy': FakeShardScraper, 'old': FakeOldScraper, 'failing': FakeFailingScraper,
        'crash-old': FakeCrashingOldScraper, 'crash-guarded': FakeCrashingGuardedScraper,
    }

    def call(self, *args, **options):
        FakeShardScraper.calls = []
        FakeOldScraper.calls = []
        out, err = StringIO(), StringIO()
        with mock.patch('scrapers.management.commands.run_scrapers.SCRAPER_REGISTRY', self.REGISTRY):
            call_command('run_scrapers', *args, stdout=out, stderr=err, **options)
        return out.getvalue(), err.getvalue()

    def test_shard_and_limit_are_passed_through(self):
        self.call('shardy', shard='3/7', limit=500)
        self.assertEqual(FakeShardScraper.calls, [(None, (3, 7), 500)])

    def test_default_call_is_unchanged(self):
        self.call('old')
        self.assertEqual(FakeOldScraper.calls, [None])

    def test_bad_shard_is_rejected(self):
        for bad in ('9/7', 'x', '3'):
            with self.assertRaises(CommandError):
                self.call('shardy', shard=bad)

    def test_scraper_without_shard_support_is_rejected_not_run_in_full(self):
        with self.assertRaises(CommandError):
            self.call('old', shard='3/7')
        self.assertEqual(FakeOldScraper.calls, [])

    def test_failed_job_makes_the_command_fail(self):
        with self.assertRaises(CommandError):
            self.call('failing')

    def test_crash_in_a_scraper_without_the_guard_is_reported_but_not_fatal(self):
        _, err = self.call('crash-old')
        self.assertIn('boom', err)

    def test_crash_in_a_guarded_scraper_makes_the_command_fail(self):
        with self.assertRaises(CommandError):
            self.call('crash-guarded')

    def test_dry_run_lists_rows_and_fetches_nothing(self):
        out, _ = self.call('shardy', shard='3/7', dry_run=True)
        self.assertIn('1 rows would be visited', out)
        self.assertEqual(FakeShardScraper.calls, [])
