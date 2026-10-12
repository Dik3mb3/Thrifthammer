"""
Tests for catalogue sharding of the scheduled eBay price-update commands.

Covers:
- parsing and validating the ``K/N`` shard spec
- the database-level split (disjoint, complete, balanced, always recomputed so
  new or re-activated products are picked up with no code or config change)
- the live coverage check that refuses to run if the slices stop adding up
- both commands end to end (eBay is mocked, nothing touches the network)
- the GitHub workflows: every scheduled cron line maps to a slice, every slice
  is covered, and the slice-picking shell step behaves as intended
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from products.ebay_sharding import (
    apply_shard,
    parse_shard,
    parse_shard_option,
    shard_counts,
    shard_products,
)
from products.models import Category, Product

try:  # PyYAML is not a runtime dependency; the workflow tests skip without it.
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def _make_products(category, count, start=0, **extra):
    """Create ``count`` active, non-book products with unique slugs and SKUs."""
    return [
        Product.objects.create(
            name=f'Test Product {i}',
            slug=f'test-product-{i}',
            gw_sku=f'TST-{i:03d}',
            category=category,
            **extra,
        )
        for i in range(start, start + count)
    ]


class ParseShardTests(SimpleTestCase):
    """The K/N spec is strict, so a typo can never become a full or empty run."""

    def test_valid_specs(self):
        """Well-formed specs parse to (K, N), tolerating spaces and leading zeros."""
        self.assertEqual(parse_shard('1/2'), (1, 2))
        self.assertEqual(parse_shard('2/2'), (2, 2))
        self.assertEqual(parse_shard(' 3 / 4 '), (3, 4))
        self.assertEqual(parse_shard('1/1'), (1, 1))
        self.assertEqual(parse_shard('01/02'), (1, 2))

    def test_blank_means_no_sharding(self):
        """None, empty and whitespace-only values mean "process everything"."""
        for blank in (None, '', '   '):
            self.assertIsNone(parse_shard(blank))

    def test_invalid_specs_raise(self):
        """Malformed or out-of-range specs raise ValueError."""
        for bad in ('0/2', '3/2', '1/0', '0/0', 'a/b', '1', '1/', '/2',
                    '1/2/3', '-1/2', '1.5/2', '1 2', '1-2'):
            with self.subTest(spec=bad):
                with self.assertRaises(ValueError):
                    parse_shard(bad)

    def test_option_wrapper_raises_command_error(self):
        """On the command line a bad value is a CommandError, a blank is None."""
        self.assertEqual(parse_shard_option('2/3'), (2, 3))
        self.assertIsNone(parse_shard_option(None))
        with self.assertRaises(CommandError):
            parse_shard_option('9/2')


class ShardQuerysetTests(TestCase):
    """The database-level split behaves as a partition and adapts to new products."""

    def setUp(self):
        """Active products, plus inactive and book products that must be left out."""
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.active = _make_products(self.category, 25)
        self.inactive = _make_products(self.category, 3, start=100, is_active=False)
        self.books = _make_products(self.category, 2, start=200, author='Some Author')

    def _base(self):
        """The queryset the commands shard: active, non-book, ordered by SKU."""
        return (
            Product.objects.filter(is_active=True)
            .order_by('gw_sku')
            .exclude(author__gt='')
        )

    def test_slices_are_disjoint_and_cover_everything(self):
        """For every N, each product lands in exactly one of the N slices."""
        all_ids = set(self._base().values_list('id', flat=True))
        for parts in range(1, 7):
            with self.subTest(parts=parts):
                seen = []
                for index in range(1, parts + 1):
                    seen.extend(apply_shard(self._base(), (index, parts))
                                .values_list('id', flat=True))
                self.assertEqual(len(seen), len(set(seen)), 'a product is in two slices')
                self.assertEqual(set(seen), all_ids, 'a product is in no slice')

    def test_membership_is_id_modulo(self):
        """Slice K holds exactly the products whose id % N == K - 1."""
        for parts in (2, 3):
            for index in range(1, parts + 1):
                ids = apply_shard(self._base(), (index, parts)).values_list('id', flat=True)
                self.assertTrue(ids)
                self.assertTrue(all(pk % parts == index - 1 for pk in ids))

    def test_slices_are_balanced(self):
        """Over consecutive ids the slice sizes differ by at most one product."""
        everything = Product.objects.all()
        _, counts = shard_counts(everything, 3)
        self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_new_products_are_picked_up_without_any_config_change(self):
        """New products are split automatically; nothing is hard-coded anywhere."""
        total_before, counts_before = shard_counts(self._base(), 2)
        added = _make_products(self.category, 7, start=300)
        total_after, counts_after = shard_counts(self._base(), 2)

        self.assertEqual(total_after, total_before + 7)
        self.assertEqual(sum(counts_after.values()), total_after)
        self.assertEqual(
            sum(counts_after.values()) - sum(counts_before.values()), 7,
        )
        for product in added:
            slices = [
                k for k in (1, 2)
                if apply_shard(self._base(), (k, 2)).filter(pk=product.pk).exists()
            ]
            self.assertEqual(len(slices), 1, f'{product.gw_sku} is in {slices}')

    def test_deactivated_and_reactivated_products_follow_is_active(self):
        """Membership is recomputed from the database, so is_active changes apply."""
        victim = self.active[0]
        total, _ = shard_counts(self._base(), 2)
        victim.is_active = False
        victim.save()
        total_off, counts_off = shard_counts(self._base(), 2)
        self.assertEqual(total_off, total - 1)
        self.assertEqual(sum(counts_off.values()), total_off)
        victim.is_active = True
        victim.save()
        self.assertEqual(shard_counts(self._base(), 2)[0], total)

    def test_books_and_inactive_products_are_never_in_a_slice(self):
        """The commands' own filters still apply inside every slice."""
        excluded = {p.pk for p in self.inactive + self.books}
        for index in (1, 2):
            ids = set(apply_shard(self._base(), (index, 2)).values_list('id', flat=True))
            self.assertFalse(ids & excluded)

    def test_shard_counts_match_the_slices_themselves(self):
        """The one-query counts equal the real size of each slice."""
        total, counts = shard_counts(self._base(), 3)
        self.assertEqual(total, self._base().count())
        for index in (1, 2, 3):
            self.assertEqual(counts[index], apply_shard(self._base(), (index, 3)).count())

    def test_composes_with_filters_ordering_and_limit(self):
        """Sharding keeps the SKU ordering and still allows [:limit] afterwards."""
        sliced = apply_shard(self._base().filter(category=self.category), (1, 2))
        skus = list(sliced.values_list('gw_sku', flat=True))
        self.assertEqual(skus, sorted(skus))
        self.assertEqual(len(sliced[:3]), 3)

    def test_single_slice_is_everything(self):
        """1/1 is equivalent to no sharding."""
        sharded, _ = shard_products(self._base(), (1, 1))
        self.assertEqual(sharded.count(), self._base().count())

    def test_shard_products_returns_summary_and_slice(self):
        """The summary names the slice, its size, and the verified total."""
        sharded, summary = shard_products(self._base(), (2, 2))
        total, counts = shard_counts(self._base(), 2)
        self.assertEqual(sharded.count(), counts[2])
        self.assertIn('Shard 2/2', summary)
        self.assertIn(f'{counts[2]} of {total} products', summary)
        self.assertIn(f'total {total}', summary)

    def test_coverage_failure_refuses_to_run(self):
        """If the slice counts do not add up to the total, the run is refused."""
        with patch('products.ebay_sharding.shard_counts', return_value=(10, {1: 4, 2: 5})):
            with self.assertRaises(CommandError):
                shard_products(self._base(), (1, 2))


class _ShardCommandMixin:
    """
    End-to-end checks of ``--shard`` for one eBay command.

    Subclasses set ``command_name`` and ``api_target`` (the dotted path of the
    eBay client class as imported by that command). The client is mocked and
    every run is a --dry-run, so nothing touches eBay or writes prices.
    """

    command_name = ''
    api_target = ''

    def setUp(self):
        """Active products across two categories, plus books and inactive ones."""
        self.cat_a = Category.objects.create(name='Category A', slug='category-a')
        self.cat_b = Category.objects.create(name='Category B', slug='category-b')
        self.products = (
            _make_products(self.cat_a, 14)
            + _make_products(self.cat_b, 11, start=50)
        )
        _make_products(self.cat_a, 2, start=100, is_active=False)
        _make_products(self.cat_a, 2, start=200, author='Some Author')

    def _run(self, *args):
        """Run the command with a mocked eBay client; return (product ids, output)."""
        out = StringIO()
        with patch(self.api_target) as api_class:
            api = api_class.return_value
            api.api_calls_made = 0
            api.find_best_match_for_product.return_value = None
            call_command(self.command_name, '--dry-run', '--delay', '0', *args, stdout=out)
            self._api_class = api_class
            ids = [c.args[0].pk for c in api.find_best_match_for_product.call_args_list]
        return ids, out.getvalue()

    def test_without_shard_everything_is_processed(self):
        """Default behaviour is unchanged: all active non-book products, no shard line."""
        ids, output = self._run()
        self.assertEqual(sorted(ids), sorted(p.pk for p in self.products))
        self.assertNotIn('Shard', output)

    def test_two_shards_partition_the_run(self):
        """Slice 1/2 and slice 2/2 together process every product exactly once."""
        ids_1, out_1 = self._run('--shard', '1/2')
        ids_2, out_2 = self._run('--shard', '2/2')
        self.assertFalse(set(ids_1) & set(ids_2))
        self.assertEqual(sorted(ids_1 + ids_2), sorted(p.pk for p in self.products))
        self.assertTrue(ids_1 and ids_2)
        self.assertIn('Shard 1/2:', out_1)
        self.assertIn('Shard 2/2:', out_2)
        self.assertIn(f'total {len(self.products)}', out_1)
        self.assertIn(f'Processing {len(ids_1)} products', out_1)

    def test_three_shards_partition_the_run(self):
        """The split is generic in N: thirds also cover everything once."""
        collected = []
        for index in (1, 2, 3):
            ids, _ = self._run('--shard', f'{index}/3')
            collected.extend(ids)
        self.assertEqual(sorted(collected), sorted(p.pk for p in self.products))

    def test_shard_respects_limit(self):
        """--limit applies inside the slice."""
        ids, _ = self._run('--shard', '1/2', '--limit', '3')
        self.assertEqual(len(ids), 3)
        self.assertTrue(all(pk % 2 == 0 for pk in ids))

    def test_shard_composes_with_category_filter(self):
        """A category filter and a shard are both applied."""
        ids, _ = self._run('--category', 'Category B', '--shard', '2/2')
        expected = [p.pk for p in self.products
                    if p.category_id == self.cat_b.pk and p.pk % 2 == 1]
        self.assertEqual(sorted(ids), sorted(expected))

    def test_new_product_joins_exactly_one_slice_next_run(self):
        """A product added after a run is processed by exactly one slice next time."""
        self._run('--shard', '1/2')
        newcomer = _make_products(self.cat_a, 1, start=900)[0]
        ids_1, _ = self._run('--shard', '1/2')
        ids_2, _ = self._run('--shard', '2/2')
        self.assertEqual((newcomer.pk in ids_1) + (newcomer.pk in ids_2), 1)

    def test_invalid_shard_aborts_before_any_api_call(self):
        """A bad --shard fails fast and never creates the eBay client."""
        with patch(self.api_target) as api_class:
            with self.assertRaises(CommandError):
                call_command(self.command_name, '--dry-run', '--shard', '3/2',
                             stdout=StringIO())
            api_class.assert_not_called()

    def test_books_are_never_processed_in_a_slice(self):
        """Book products stay excluded from every slice."""
        book_ids = set(Product.objects.exclude(author='').values_list('id', flat=True))
        ids_1, _ = self._run('--shard', '1/2')
        ids_2, _ = self._run('--shard', '2/2')
        self.assertFalse(book_ids & set(ids_1 + ids_2))


class UsShardCommandTests(_ShardCommandMixin, TestCase):
    """--shard on update_ebay_prices."""

    command_name = 'update_ebay_prices'
    api_target = 'products.management.commands.update_ebay_prices.EbayBrowseAPI'


class UkShardCommandTests(_ShardCommandMixin, TestCase):
    """--shard on update_ebay_uk_prices."""

    command_name = 'update_ebay_uk_prices'
    api_target = 'products.management.commands.update_ebay_uk_prices.EbayBrowseAPIUK'


_WORKFLOW_DIR = Path(settings.BASE_DIR).parent / '.github' / 'workflows'
_WORKFLOWS = {
    'update-ebay-prices.yml': 'update-prices',
    'update-ebay-uk-prices.yml': 'update-uk-prices',
}


def _find_bash():
    """Return a bash executable (Git Bash on Windows), or None."""
    if os.name == 'nt':
        for candidate in (r'C:\Program Files\Git\bin\bash.exe',
                          r'C:\Program Files (x86)\Git\bin\bash.exe'):
            if os.path.exists(candidate):
                return candidate
        return None
    return shutil.which('bash')


def _load_workflow(filename):
    """Parse a workflow file into (document, crons, slice step, steps by name)."""
    with open(_WORKFLOW_DIR / filename, encoding='utf-8') as handle:
        document = yaml.safe_load(handle)
    triggers = document.get('on', document.get(True))
    crons = [entry['cron'] for entry in triggers['schedule']]
    steps = document['jobs'][_WORKFLOWS[filename]]['steps']
    slice_step = next(step for step in steps if step.get('id') == 'slice')
    return document, crons, slice_step, {step['name']: step for step in steps}


def _slice_mapping(script):
    """Return [(cron, K, N)] parsed from the slice step's case statement."""
    return [
        (cron, int(index), int(parts))
        for cron, index, parts in re.findall(
            r"'([^']+)'\)\s+SHARD=\"([0-9]+)/([0-9]+)\"", script)
    ]


def _runs_per_day(cron):
    """Number of daily firings of a 'M H,H,H * * *' cron line."""
    return len(cron.split()[1].split(','))


@unittest.skipIf(yaml is None, 'PyYAML is not installed')
class WorkflowScheduleTests(SimpleTestCase):
    """The eBay workflows can never silently drop a slice of the catalogue."""

    def test_every_cron_is_mapped_and_every_slice_is_covered(self):
        """Cron lines and the slice mapping match one-to-one and cover 1..N."""
        for filename in _WORKFLOWS:
            with self.subTest(workflow=filename):
                _, crons, slice_step, _ = _load_workflow(filename)
                mapping = _slice_mapping(slice_step['run'])
                self.assertEqual(sorted(c for c, _, _ in mapping), sorted(crons),
                                 'schedule and slice mapping differ')
                self.assertEqual(len(crons), len(set(crons)))
                parts = {n for _, _, n in mapping}
                self.assertEqual(len(parts), 1, 'mixed N in one workflow')
                self.assertEqual({k for _, k, _ in mapping}, set(range(1, parts.pop() + 1)))

    def test_every_slice_runs_equally_often(self):
        """Each slice is scheduled the same number of times per day."""
        for filename in _WORKFLOWS:
            with self.subTest(workflow=filename):
                _, _, slice_step, _ = _load_workflow(filename)
                per_slice = {}
                for cron, index, _ in _slice_mapping(slice_step['run']):
                    per_slice[index] = per_slice.get(index, 0) + _runs_per_day(cron)
                self.assertEqual(len(set(per_slice.values())), 1, per_slice)

    def test_price_step_passes_the_shard_flag(self):
        """The price-update step feeds the chosen slice into --shard."""
        for filename, command in (('update-ebay-prices.yml', 'update_ebay_prices'),
                                  ('update-ebay-uk-prices.yml', 'update_ebay_uk_prices')):
            with self.subTest(workflow=filename):
                _, _, _, steps = _load_workflow(filename)
                step = next(s for n, s in steps.items() if 'price update' in n.lower()
                            and 'book' not in n.lower() and 'cache' not in n.lower())
                self.assertEqual(step['env']['SHARD'], '${{ steps.slice.outputs.shard }}')
                self.assertIn('--shard "$SHARD"', step['run'])
                self.assertIn(f'python manage.py {command} ', step['run'])

    def test_manual_dispatch_has_a_shard_input(self):
        """A manual run can pick a slice (blank = everything)."""
        for filename in _WORKFLOWS:
            with self.subTest(workflow=filename):
                document, _, _, _ = _load_workflow(filename)
                triggers = document.get('on', document.get(True))
                self.assertEqual(triggers['workflow_dispatch']['inputs']['shard']['default'], '')

    def test_books_step_only_runs_with_slice_one_or_unsharded(self):
        """The US books step is gated on the slice step's run_books output."""
        _, _, _, steps = _load_workflow('update-ebay-prices.yml')
        self.assertEqual(steps['Run eBay book price update']['if'],
                         "steps.slice.outputs.run_books == 'true'")


@unittest.skipIf(yaml is None, 'PyYAML is not installed')
@unittest.skipIf(_find_bash() is None, 'bash is not available')
class SliceStepScriptTests(SimpleTestCase):
    """Run the workflows' real "Pick catalogue slice" shell script under bash."""

    def _run_script(self, filename, event, schedule='', input_shard=''):
        """Execute the slice step; return (exit code, outputs dict, stdout)."""
        _, _, slice_step, _ = _load_workflow(filename)
        with tempfile.TemporaryDirectory() as tmp:
            output_file = Path(tmp) / 'github_output'
            output_file.write_text('', encoding='utf-8')
            env = dict(os.environ, EVENT_NAME=event, SCHEDULE=schedule,
                       INPUT_SHARD=input_shard, GITHUB_OUTPUT=output_file.as_posix())
            done = subprocess.run([_find_bash(), '-c', slice_step['run']], env=env,
                                  capture_output=True, text=True, timeout=60)
            lines = output_file.read_text(encoding='utf-8').splitlines()
        outputs = dict(line.split('=', 1) for line in lines if '=' in line)
        return done.returncode, outputs, done.stdout

    def test_each_scheduled_cron_selects_its_slice(self):
        """Every cron string selects exactly the slice the mapping declares."""
        for filename in _WORKFLOWS:
            _, crons, slice_step, _ = _load_workflow(filename)
            for cron, index, parts in _slice_mapping(slice_step['run']):
                with self.subTest(workflow=filename, cron=cron):
                    code, outputs, _ = self._run_script(filename, 'schedule', cron)
                    self.assertEqual(code, 0)
                    self.assertEqual(outputs['shard'], f'{index}/{parts}')

    def test_unmapped_schedule_fails_loudly(self):
        """An unknown cron string fails the job instead of silently running everything."""
        for filename in _WORKFLOWS:
            with self.subTest(workflow=filename):
                code, outputs, stdout = self._run_script(filename, 'schedule', '0 1 * * *')
                self.assertNotEqual(code, 0)
                self.assertIn('No catalogue slice', stdout)
                self.assertNotIn('shard', outputs)

    def test_manual_run_defaults_to_everything_or_uses_the_input(self):
        """Manual runs: blank input = no sharding, otherwise the typed value."""
        for filename in _WORKFLOWS:
            with self.subTest(workflow=filename):
                code, outputs, _ = self._run_script(filename, 'workflow_dispatch')
                self.assertEqual((code, outputs['shard']), (0, ''))
                code, outputs, _ = self._run_script(
                    filename, 'workflow_dispatch', input_shard='2/2')
                self.assertEqual((code, outputs['shard']), (0, '2/2'))

    def test_us_books_step_runs_for_slice_one_and_manual_runs_only(self):
        """Slice 1/2 and manual runs run books; slice 2/2 skips them."""
        filename = 'update-ebay-prices.yml'
        _, crons, slice_step, _ = _load_workflow(filename)
        for cron, index, _ in _slice_mapping(slice_step['run']):
            with self.subTest(cron=cron):
                _, outputs, _ = self._run_script(filename, 'schedule', cron)
                self.assertEqual(outputs['run_books'], 'true' if index == 1 else 'false')
        _, outputs, _ = self._run_script(filename, 'workflow_dispatch')
        self.assertEqual(outputs['run_books'], 'true')
