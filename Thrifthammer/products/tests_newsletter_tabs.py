"""
Tests for the three-tab Wednesday and Friday digests: the Most Saved ranking,
the weekly Curated Picks list, the tab assembly and the rendered emails.

Run with: python manage.py test products.tests_newsletter_tabs --settings=thrifthammer.test_settings
"""

import datetime
import decimal
import re
from io import StringIO

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils import timezone

from prices.models import CurrentPrice
from products.management.commands.send_weekly_deals import Command as WednesdayUS
from products.management.commands.send_weekly_deals_uk import Command as WednesdayUK
from products.models import Category, CuratedDealItem, CuratedDealList, Product, Retailer
from products.newsletter_deals import (
    DEAL_FOOTNOTE, SAVED_TAB_MIN_PCT, build_deal_tabs, build_text_sections,
    get_curated_deals, get_curated_entries,
)

D = decimal.Decimal


class DealTabsTestBase(TestCase):
    """Create a small 40K catalogue with US and UK prices."""

    def setUp(self):
        """Five US products: 50% off, 25% off (biggest saving), 50% off (small), 15% off, above MSRP."""
        self.category = Category.objects.create(name='Warhammer 40,000', slug='warhammer-40000')
        self.ebay = Retailer.objects.create(name='eBay', slug='ebay', website='https://www.ebay.com')
        self.ebay_uk = Retailer.objects.create(
            name='eBay UK', slug='ebay-uk', website='https://www.ebay.co.uk', is_uk=True,
        )
        # name -> (msrp, best US price, msrp_gbp, best UK price)
        spec = {
            'Alpha': ('100.00', '50.00', '80.00', '40.00'),
            'Bravo': ('300.00', '225.00', '240.00', '180.00'),
            'Charlie': ('40.00', '20.00', '32.00', '16.00'),
            'Delta': ('100.00', '85.00', '80.00', '68.00'),
            'Echo': ('100.00', '103.00', '80.00', '82.00'),
        }
        self.products = {}
        for index, (name, (msrp, us_price, msrp_gbp, uk_price)) in enumerate(spec.items(), 1):
            product = Product.objects.create(
                name=name, slug=name.lower(), msrp=D(msrp), msrp_gbp=D(msrp_gbp), category=self.category,
            )
            CurrentPrice.objects.create(
                product=product, retailer=self.ebay, price=D(us_price), in_stock=True,
                url=f'https://www.ebay.com/itm/{index}',
            )
            CurrentPrice.objects.create(
                product=product, retailer=self.ebay_uk, price=D(uk_price), in_stock=True,
                url=f'https://www.ebay.co.uk/itm/{index}',
            )
            self.products[name] = product

    def make_list(self, digest, region, names):
        """Create a curated list holding the named products in order."""
        deal_list = CuratedDealList.objects.create(digest=digest, region=region)
        for position, name in enumerate(names, 1):
            CuratedDealItem.objects.create(
                deal_list=deal_list, product=self.products[name], position=position,
            )
        return deal_list


class MostSavedRankingTest(DealTabsTestBase):
    """The Most Saved tab ranks by amount saved and needs at least 20% off."""

    def test_saved_tab_orders_by_amount_saved_and_drops_small_discounts(self):
        """Bravo saves $75, Alpha $50, Charlie $20; Delta (15% off) is not eligible."""
        deals = WednesdayUS()._get_top_deals(10, category_name='Warhammer 40,000', by='saved')
        self.assertEqual([d['name'] for d in deals], ['Bravo', 'Alpha', 'Charlie'])
        self.assertEqual(SAVED_TAB_MIN_PCT, 20)
        self.assertEqual([round(d['savings']) for d in deals], [75, 50, 20])

    def test_best_discount_tab_is_still_ranked_by_percentage(self):
        """The existing tab keeps its meaning: biggest percentage first, 5% minimum."""
        deals = WednesdayUS()._get_top_deals(10, category_name='Warhammer 40,000')
        names = [d['name'] for d in deals]
        self.assertEqual(set(names[:2]), {'Alpha', 'Charlie'})
        self.assertEqual(names[2:], ['Bravo', 'Delta'])
        self.assertNotIn('Echo', names)

    def test_uk_saved_tab_uses_pounds_and_uk_prices(self):
        """UK amounts come from the UK reference and UK retailers: Bravo saves 60 pounds."""
        deals = WednesdayUK()._get_top_deals(10, category_name='Warhammer 40,000', by='saved')
        self.assertEqual([d['name'] for d in deals], ['Bravo', 'Alpha', 'Charlie'])
        self.assertEqual(round(deals[0]['savings']), 60)
        self.assertIn('region=uk', deals[0]['url'])


class CuratedListTest(DealTabsTestBase):
    """The curated list is shown in order, with no discount minimum, and never goes stale silently."""

    def test_curated_deals_follow_position_order(self):
        """Echo is above MSRP: it is still listed, with its price and no discount."""
        self.make_list('wednesday', 'us', ['Echo', 'Alpha'])
        deals, status = get_curated_deals(WednesdayUS(), 'wednesday', uk=False)
        self.assertEqual([d['name'] for d in deals], ['Echo', 'Alpha'])
        self.assertEqual(deals[0]['pct_off'], 0.0)
        self.assertEqual(deals[0]['savings'], 0.0)
        self.assertEqual(round(deals[1]['pct_off']), 50)
        self.assertIn('2 curated pick', status)

    def test_curated_list_is_per_region(self):
        """The US list never leaks into the UK digest, and the UK list uses UK prices."""
        self.make_list('wednesday', 'us', ['Alpha'])
        self.make_list('wednesday', 'uk', ['Bravo'])
        us_deals, _ = get_curated_deals(WednesdayUS(), 'wednesday', uk=False)
        uk_deals, _ = get_curated_deals(WednesdayUK(), 'wednesday', uk=True)
        self.assertEqual([d['name'] for d in us_deals], ['Alpha'])
        self.assertEqual([d['name'] for d in uk_deals], ['Bravo'])
        self.assertEqual(uk_deals[0]['price'], 180.0)

    def test_pick_without_an_in_stock_price_is_skipped_and_counted(self):
        """Charlie loses its only US price, so it drops out and the status says so."""
        self.make_list('wednesday', 'us', ['Alpha', 'Charlie'])
        CurrentPrice.objects.filter(product=self.products['Charlie'], retailer=self.ebay).update(in_stock=False)
        deals, status = get_curated_deals(WednesdayUS(), 'wednesday', uk=False)
        self.assertEqual([d['name'] for d in deals], ['Alpha'])
        self.assertIn('1 skipped', status)

    def test_inactive_product_is_left_out(self):
        """A product switched off on the site cannot be sent."""
        self.make_list('wednesday', 'us', ['Alpha', 'Bravo'])
        Product.objects.filter(pk=self.products['Alpha'].pk).update(is_active=False)
        deals, _ = get_curated_deals(WednesdayUS(), 'wednesday', uk=False)
        self.assertEqual([d['name'] for d in deals], ['Bravo'])

    def test_stale_list_is_left_out(self):
        """A list not edited for more than 6 days is skipped so last week's picks are not re-sent."""
        deal_list = self.make_list('wednesday', 'us', ['Alpha'])
        CuratedDealList.objects.filter(pk=deal_list.pk).update(
            updated_at=timezone.now() - datetime.timedelta(days=7),
        )
        entries, status = get_curated_entries('wednesday', 'us')
        self.assertEqual(entries, [])
        self.assertIn('stale', status)

    def test_recently_edited_list_is_used(self):
        """A list edited 5 days ago is still fresh."""
        deal_list = self.make_list('wednesday', 'us', ['Alpha'])
        CuratedDealList.objects.filter(pk=deal_list.pk).update(
            updated_at=timezone.now() - datetime.timedelta(days=5),
        )
        entries, _ = get_curated_entries('wednesday', 'us')
        self.assertEqual(len(entries), 1)

    def test_missing_and_empty_lists_give_no_tab(self):
        """No list, or a list with no products, means no Curated tab."""
        self.assertEqual(get_curated_entries('friday', 'us')[0], [])
        CuratedDealList.objects.create(digest='friday', region='us')
        entries, status = get_curated_entries('friday', 'us')
        self.assertEqual(entries, [])
        self.assertIn('empty', status)


class TabAssemblyTest(DealTabsTestBase):
    """Tabs appear in the order Curated, Best Discount, Most Saved and empty ones are dropped."""

    def test_order_and_empty_tabs(self):
        """An empty curated tab is omitted; the other two keep their order."""
        a, b = {'name': 'a'}, {'name': 'b'}
        tabs = build_deal_tabs([], [a], [b])
        self.assertEqual([t['key'] for t in tabs], ['discount', 'saved'])
        tabs = build_deal_tabs([a], [a], [b])
        self.assertEqual([t['key'] for t in tabs], ['curated', 'discount', 'saved'])
        self.assertEqual(tabs[2]['label'], 'Most $ Saved')
        self.assertEqual(build_deal_tabs([a], [a], [b], '£')[2]['label'], 'Most £ Saved')


class RenderedEmailTest(DealTabsTestBase):
    """The HTML and text emails carry the tabs and the footnote."""

    def _context(self, tabs, deals):
        """Return the template context a send command builds."""
        return {
            'deals': deals, 'tabs': tabs, 'deal_footnote': DEAL_FOOTNOTE, 'today': datetime.date.today(),
            'site_url': 'https://thrifthammer.com', 'browse_url': 'https://thrifthammer.com/products/',
            'register_url': 'https://thrifthammer.com/accounts/register/', 'top_pct': 50,
            'latest_post': None, 'unsubscribe_url': 'https://thrifthammer.com/unsub/',
        }

    def _tabs(self):
        """Build real tabs from the test catalogue (curated: Echo then Alpha)."""
        self.make_list('wednesday', 'us', ['Echo', 'Alpha'])
        command = WednesdayUS()
        discount = command._get_top_deals(10, category_name='Warhammer 40,000')
        saved = command._get_top_deals(10, category_name='Warhammer 40,000', by='saved')
        curated, _ = get_curated_deals(command, 'wednesday', uk=False)
        return build_deal_tabs(curated, discount, saved), discount

    def test_footnote_wording(self):
        """The footnote says "or the listing selling out" (not "and")."""
        self.assertEqual(
            DEAL_FOOTNOTE,
            'The prices you see may not be available when you view due to changing prices or the listing selling out.',
        )

    def test_three_tabs_with_footnote_and_curated_first(self):
        """Three radio tabs in order, each list present, footnote shown."""
        tabs, discount = self._tabs()
        html = render_to_string('emails/weekly_deals.html', self._context(tabs, discount))
        self.assertEqual(html.count('class="deal-tab-radio"'), 3)
        curated_at = html.index('<div class="deal-panel deal-panel-curated"')
        discount_at = html.index('<div class="deal-panel deal-panel-discount"')
        saved_at = html.index('<div class="deal-panel deal-panel-saved"')
        self.assertLess(curated_at, discount_at)
        self.assertLess(discount_at, saved_at)
        self.assertIn(DEAL_FOOTNOTE, html)
        self.assertIn('Most $ Saved', html)
        self.assertRegex(html, r'SAVE \$75\s*</div>')
        self.assertNotIn('SAVE $75.00', html)
        self.assertNotIn('SAVE $75 (', html)
        # The first radio is pre-checked and the tab CSS ships in its own style block.
        self.assertIn('id="deal-tab-curated" class="deal-tab-radio" checked="checked"', html)
        self.assertIn('input.deal-tab-radio:checked', html)

    def test_content_is_never_hidden_by_default(self):
        """Nothing is hidden by an inline style except the tab bar and the radios (shown only via :checked)."""
        tabs, discount = self._tabs()
        html = render_to_string('emails/weekly_deals.html', self._context(tabs, discount))
        for panel in ('deal-panel-curated', 'deal-panel-discount', 'deal-panel-saved'):
            start = html.index(f'<div class="deal-panel {panel}"')
            self.assertNotIn('display:none', html[start:start + 200])

    def test_curated_pick_above_msrp_shows_no_badge(self):
        """Echo ($103 against $100) is listed without a strikethrough MSRP or savings badge."""
        tabs, discount = self._tabs()
        html = render_to_string('emails/weekly_deals.html', self._context(tabs, discount))
        curated_block = html[
            html.index('<div class="deal-panel deal-panel-curated"'):html.index('<div class="deal-panel deal-panel-discount"')
        ]
        first_row = curated_block[:curated_block.index('Alpha')]
        self.assertIn('$103.00', first_row)
        self.assertNotIn('SAVE', first_row)
        self.assertNotIn('MSRP', first_row)

    def test_curated_badge_shows_percent_and_whole_dollars(self):
        """A curated pick below MSRP reads "SAVE 50% / SAVE $50"; Best Discount stays percent-only."""
        tabs, discount = self._tabs()
        html = render_to_string('emails/weekly_deals.html', self._context(tabs, discount))
        curated_block = html[
            html.index('<div class="deal-panel deal-panel-curated"'):html.index('<div class="deal-panel deal-panel-discount"')
        ]
        discount_block = html[
            html.index('<div class="deal-panel deal-panel-discount"'):html.index('<div class="deal-panel deal-panel-saved"')
        ]
        self.assertRegex(curated_block, r'SAVE 50% / SAVE \$50\s*</div>')
        self.assertRegex(discount_block, r'SAVE 50%\s*</div>')
        self.assertNotIn(' / SAVE', discount_block)
        text = ' | '.join(build_text_sections(tabs, '$'))
        self.assertIn('save 50% / save $50 off $100.00 MSRP', text)

    def test_single_tab_draws_no_tab_bar(self):
        """With only one list the email is the plain list again (plus the footnote)."""
        _, discount = self._tabs()
        html = render_to_string(
            'emails/weekly_deals.html',
            self._context(build_deal_tabs([], discount, []), discount),
        )
        self.assertNotIn('deal-tab-radio', html)
        self.assertNotIn('deal-tabbar', html)
        self.assertIn('Alpha', html)
        self.assertIn(DEAL_FOOTNOTE, html)

    def test_email_without_tabs_still_renders_the_old_list(self):
        """The one-off apology email renders friday_deals.html with only `deals`: still works."""
        _, discount = self._tabs()
        context = self._context(None, discount)
        context.pop('tabs')
        context.pop('deal_footnote')
        html = render_to_string('emails/friday_deals.html', context)
        self.assertIn('Alpha', html)
        self.assertNotIn(DEAL_FOOTNOTE, html)
        self.assertNotIn('deal-tab-radio', html)

    def test_friday_uk_email_uses_pounds(self):
        """The shared rows show the pound sign and the pound label on the saved tab."""
        command = WednesdayUK()
        discount = command._get_top_deals(10, category_name='Warhammer 40,000')
        saved = command._get_top_deals(10, category_name='Warhammer 40,000', by='saved')
        tabs = build_deal_tabs([], discount, saved, '£')
        context = self._context(tabs, discount)
        context['currency_symbol'] = '£'
        html = render_to_string('emails/friday_deals.html', context)
        self.assertIn('Most £ Saved', html)
        self.assertIn('£180.00', html)
        self.assertRegex(html, r'SAVE £60\s*</div>')
        self.assertNotIn('£60.00 (', html)

    def test_text_body_has_every_section_and_the_footnote(self):
        """The plain-text email lists each tab with a heading and ends with the footnote."""
        tabs, _ = self._tabs()
        text = '\n'.join(build_text_sections(tabs, '$'))
        for heading in ('CURATED PICKS', 'BEST DISCOUNT', 'MOST $ SAVED'):
            self.assertIn(heading, text)
        self.assertIn('save $75 off $300.00 MSRP', text)
        # The Most Saved section shows dollars only; Best Discount keeps its percentages.
        self.assertNotIn('%', text.split('MOST $ SAVED')[1])
        self.assertIn('save 25% off $300.00', text.split('MOST $ SAVED')[0])
        self.assertTrue(text.rstrip().endswith(DEAL_FOOTNOTE))


class WednesdayCommandTest(DealTabsTestBase):
    """The real command builds all three tabs and mails them to the test recipient only."""

    def test_command_sends_tabs_to_the_recipient(self):
        """One email to the recipient: three tabs in the HTML, footnote in both bodies."""
        self.make_list('wednesday', 'us', ['Alpha'])
        mail.outbox.clear()
        out = StringIO()
        call_command('send_weekly_deals', recipient='preview@example.com', stdout=out)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['preview@example.com'])
        html = message.alternatives[0][0]
        self.assertEqual(html.count('class="deal-tab-radio"'), 3)
        self.assertIn(DEAL_FOOTNOTE, html)
        self.assertIn(DEAL_FOOTNOTE, message.body)
        self.assertIn('Curated Picks tab: 1 curated pick(s)', out.getvalue())
        self.assertIn('Most $ Saved tab', out.getvalue())

    def test_command_without_a_curated_list_sends_two_tabs(self):
        """No curated list: the email has Best Discount and Most Saved and says why in the log."""
        mail.outbox.clear()
        out = StringIO()
        call_command('send_weekly_deals', recipient='preview@example.com', stdout=out)
        html = mail.outbox[0].alternatives[0][0]
        self.assertEqual(html.count('class="deal-tab-radio"'), 2)
        self.assertNotIn('Curated Picks', html)
        self.assertIn('no curated list set up', out.getvalue())


class CuratedAdminTest(DealTabsTestBase):
    """The admin can open and edit the lists."""

    def setUp(self):
        """Log in as a superuser."""
        super().setUp()
        admin_user = get_user_model().objects.create_superuser('boss', 'boss@example.com', 'pw-for-tests-only')
        self.client.force_login(admin_user)

    def test_changelist_and_change_page_open(self):
        """Both pages load, and the change page offers the 10 product slots."""
        deal_list = CuratedDealList.objects.create(digest='friday', region='uk')
        response = self.client.get('/admin/products/curateddeallist/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f'/admin/products/curateddeallist/{deal_list.pk}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'items-TOTAL_FORMS')

    def test_saving_an_item_refreshes_the_list(self):
        """Editing the products through the admin form counts as a fresh edit."""
        deal_list = CuratedDealList.objects.create(digest='friday', region='us')
        CuratedDealList.objects.filter(pk=deal_list.pk).update(
            updated_at=timezone.now() - datetime.timedelta(days=30),
        )
        data = {
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0', 'items-MAX_NUM_FORMS': '10',
            'items-0-position': '1', 'items-0-product': str(self.products['Alpha'].pk),
            'digest': 'friday', 'region': 'us',
        }
        response = self.client.post(f'/admin/products/curateddeallist/{deal_list.pk}/change/', data)
        self.assertEqual(response.status_code, 302)
        deal_list.refresh_from_db()
        self.assertGreater(deal_list.updated_at, timezone.now() - datetime.timedelta(minutes=1))
        self.assertEqual(deal_list.items.count(), 1)
