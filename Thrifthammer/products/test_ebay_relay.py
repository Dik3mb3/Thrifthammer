"""
Tests for the eBay US relay: .github/scripts/ebay_relay.py and the jobs of
.github/workflows/update-ebay-prices.yml that call it.

Everything runs offline. The GitHub CLI and time.sleep are replaced by fakes, so the
tests prove the decisions (stand down, wait, hand over, stop) without touching GitHub.
"""

import datetime as dt
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase

from products.test_ebay_sharding import _load_workflow, _slice_mapping

try:  # PyYAML is not a runtime dependency; the workflow tests skip without it.
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

_ROOT = Path(settings.BASE_DIR).parent
_SCRIPT = _ROOT / '.github' / 'scripts' / 'ebay_relay.py'
_WORKFLOW = _ROOT / '.github' / 'workflows' / 'update-ebay-prices.yml'
NOW = dt.datetime(2026, 11, 18, 20, 0, 0, tzinfo=dt.timezone.utc).timestamp()


def _load_script():
    """Import the relay script from its file (it lives outside the Python path)."""
    spec = importlib.util.spec_from_file_location('ebay_relay', _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(run_id, status, age_seconds):
    """A run record as `gh run list --json` returns it, created `age_seconds` ago."""
    created = dt.datetime.fromtimestamp(NOW - age_seconds, dt.timezone.utc)
    return {'databaseId': run_id, 'status': status,
            'createdAt': created.strftime('%Y-%m-%dT%H:%M:%SZ')}


class _FakeGh:
    """Records the gh dispatch calls and can fail the first N of them."""

    def __init__(self, error_class, failures=0):
        self.calls = []
        self.error_class = error_class
        self.failures = failures

    def __call__(self, args):
        self.calls.append(list(args))
        if self.failures:
            self.failures -= 1
            raise self.error_class('simulated failure')
        return ''


class GateDecisionTests(SimpleTestCase):
    """A scheduled run stands down only when another recent run is active."""

    def setUp(self):
        self.script = _load_script()
        self.cron = '10 0,6,12,18 * * *'

    def _gate(self, runs, event='schedule', **env):
        base = {'EVENT_NAME': event, 'SCHEDULE': self.cron if event == 'schedule' else '', 'RUN_ID': '500'}
        base.update(env)
        return self.script.gate_decision(base, runs, NOW)

    def test_schedule_with_nothing_active_starts_the_chain(self):
        """The watchdog case: no active run, so this run goes ahead and relays."""
        decision = self._gate([_run(1, 'completed', 3600)])
        self.assertEqual((decision['go'], decision['relay']), (True, True))

    def test_schedule_stands_down_when_a_run_is_active(self):
        """GitHub's late cron must not duplicate a slice while the chain is alive."""
        for status in ('in_progress', 'queued', 'waiting', 'pending', 'requested'):
            with self.subTest(status=status):
                decision = self._gate([_run(1, status, 600)])
                self.assertEqual((decision['go'], decision['relay']), (False, False))

    def test_stale_or_own_runs_do_not_count_as_active(self):
        """A run stuck in "queued" for months, an 8h+ old run, and this run itself are ignored."""
        runs = [_run(1, 'queued', 100 * 86400), _run(2, 'in_progress', 9 * 3600), _run(500, 'in_progress', 5)]
        decision = self._gate(runs)
        self.assertEqual((decision['go'], decision['relay']), (True, True))

    def test_manual_runs_always_go_ahead_and_do_not_relay_by_default(self):
        """A hand-started run is never blocked, and only relays when asked to."""
        decision = self._gate([_run(1, 'in_progress', 60)], event='workflow_dispatch', INPUT_SHARD='1/2')
        self.assertEqual((decision['go'], decision['relay']), (True, False))

    def test_manual_relay_needs_a_real_slice_and_no_filters(self):
        """relay=true works only for slice 1/2 or 2/2 and never for a filtered (partial) run."""
        cases = [({'INPUT_SHARD': '1/2'}, True), ({'INPUT_SHARD': '2/2'}, True), ({'INPUT_SHARD': ''}, False),
                 ({'INPUT_SHARD': '3/4'}, False), ({'INPUT_SHARD': '1/2', 'INPUT_SKUS': 'ARMY-001'}, False),
                 ({'INPUT_SHARD': '1/2', 'INPUT_CATEGORY': 'Kill-Team'}, False),
                 ({'INPUT_SHARD': '1/2', 'INPUT_BATCH_TAG': 'phase-2'}, False)]
        for extra, expected in cases:
            with self.subTest(extra=extra):
                decision = self._gate([], event='workflow_dispatch', INPUT_RELAY='true', **extra)
                self.assertEqual((decision['go'], decision['relay']), (True, expected))

    def test_unmapped_cron_still_goes_ahead_but_never_relays(self):
        """An unknown cron string keeps the old behaviour: the update step fails loudly."""
        decision = self._gate([], SCHEDULE='0 1 * * *')
        self.assertEqual((decision['go'], decision['relay']), (True, False))

    def test_lookup_failure_falls_back_to_the_old_behaviour(self):
        """If GitHub cannot list runs, a scheduled run still runs (no relay), never silently skipped."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            out.write_text('', encoding='utf-8')
            env = {'EVENT_NAME': 'schedule', 'SCHEDULE': self.cron, 'RUN_ID': '1', 'GH_REPO': 'x/y'}

            def boom():
                raise self.script.GhError('api down')

            with mock.patch.dict('os.environ', {'GITHUB_OUTPUT': str(out)}):
                self.script.cmd_gate(env=env, now=NOW, runs_fn=boom)
            self.assertEqual(out.read_text(encoding='utf-8').split(), ['go=true', 'relay=false'])


class RelayHelpersTests(SimpleTestCase):
    """Waiting, clamping and the arguments of the next dispatch."""

    def setUp(self):
        self.script = _load_script()

    def test_wait_is_the_time_left_until_the_gap(self):
        """The next slice starts `gap` minutes after this run began, never later than the gap."""
        wait = self.script.relay_wait_seconds
        self.assertEqual(wait(NOW - 600, NOW, 180), 170 * 60)
        self.assertEqual(wait(NOW - 200 * 60, NOW, 180), 0)
        self.assertEqual(wait(NOW + 99999, NOW, 180), 180 * 60)
        self.assertEqual(wait(NOW, NOW, 1), 60)

    def test_gap_and_hops_parsing_is_safe(self):
        """Junk input falls back to 3 hours / unlimited; the gap is clamped."""
        self.assertEqual(self.script.parse_gap(''), 180)
        self.assertEqual(self.script.parse_gap('abc'), 180)
        self.assertEqual(self.script.parse_gap('0'), 1)
        self.assertEqual(self.script.parse_gap('99999'), 360)
        self.assertEqual(self.script.parse_gap('1'), 1)
        self.assertIsNone(self.script.parse_hops(''))
        self.assertIsNone(self.script.parse_hops('x; rm -rf'))
        self.assertEqual(self.script.parse_hops('2'), 2)

    def test_dispatch_arguments_alternate_the_slice_and_inherit_test_settings(self):
        """A real run passes only shard and relay; a test run also passes its dry-run settings."""
        real = self.script.relay_dispatch_args({'REF_NAME': 'main'}, '2/2', None)
        self.assertEqual(real, ['workflow', 'run', 'update-ebay-prices.yml', '--ref', 'main',
                                '-f', 'shard=2/2', '-f', 'relay=true'])
        test = self.script.relay_dispatch_args(
            {'REF_NAME': 'main', 'INPUT_DRY_RUN': 'true', 'INPUT_BOOK_DRY_RUN': 'true', 'INPUT_LIMIT': '1',
             'INPUT_BOOK_LIMIT': '1', 'INPUT_GAP': '1', 'INPUT_SKUS': 'ARMY-001'}, '1/2', 2)
        for pair in ('dry_run=true', 'book_dry_run=true', 'limit=1', 'book_limit=1', 'relay_gap_minutes=1',
                     'relay_hops=1', 'shard=1/2', 'relay=true'):
            self.assertIn(pair, test)
        self.assertFalse([a for a in test if a.startswith(('skus', 'batch_tag', 'category'))])

    def test_junk_numeric_inputs_are_never_passed_on(self):
        """limit and gap values must be digits, so nothing odd can be injected into the dispatch."""
        args = self.script.relay_dispatch_args(
            {'REF_NAME': 'main', 'INPUT_LIMIT': '1; echo hi', 'INPUT_BOOK_LIMIT': '$(x)', 'INPUT_GAP': 'abc'}, '2/2', None)
        self.assertFalse([a for a in args if a.startswith(('limit=', 'book_limit=', 'relay_gap_minutes='))])


class RelayCommandTests(SimpleTestCase):
    """The relay sub-command end to end, with a fake GitHub CLI and a fake sleep."""

    def setUp(self):
        self.script = _load_script()
        self.sleeps = []
        self.gh = _FakeGh(self.script.GhError)

    def _relay(self, env, runs=None, started=NOW - 600, runs_error=None):
        base = {'GH_REPO': 'x/y', 'RUN_ID': '500', 'REF_NAME': 'main', 'EVENT_NAME': 'workflow_dispatch'}
        base.update(env)

        def runs_fn():
            if runs_error:
                raise runs_error
            return runs or []

        with mock.patch.object(self.script, 'run_gh', self.gh):
            return self.script.cmd_relay(env=base, runs_fn=runs_fn, started_fn=lambda: started,
                                         sleep=self.sleeps.append, now_fn=lambda: NOW)

    def test_waits_for_the_three_hour_mark_then_starts_the_other_slice(self):
        """Started 10 minutes ago: sleep 170 minutes, then dispatch slice 2/2 with relay on."""
        self._relay({'INPUT_SHARD': '1/2'})
        self.assertEqual(self.sleeps, [170 * 60])
        self.assertEqual(len(self.gh.calls), 1)
        self.assertEqual(self.gh.calls[0][:3], ['workflow', 'run', 'update-ebay-prices.yml'])
        self.assertIn('shard=2/2', self.gh.calls[0])
        self.assertIn('relay=true', self.gh.calls[0])

    def test_a_scheduled_run_uses_its_cron_to_find_its_slice(self):
        """The watchdog's own slice comes from the cron string, so slice 2/2 hands over to 1/2."""
        self._relay({'EVENT_NAME': 'schedule', 'SCHEDULE': '10 3,9,15,21 * * *'}, started=NOW - 200 * 60)
        self.assertEqual(self.sleeps, [])
        self.assertIn('shard=1/2', self.gh.calls[0])

    def test_no_wait_when_the_update_already_took_longer_than_the_gap(self):
        """The chain never waits needlessly: a long run hands over immediately."""
        self._relay({'INPUT_SHARD': '1/2'}, started=NOW - 190 * 60)
        self.assertEqual(self.sleeps, [])
        self.assertEqual(len(self.gh.calls), 1)

    def test_does_not_start_a_successor_when_another_run_is_active(self):
        """No double chains: a run still active after the re-check means a successor already exists."""
        self._relay({'INPUT_SHARD': '2/2'}, runs=[_run(7, 'in_progress', 30)])
        self.assertEqual(self.gh.calls, [])
        self.assertEqual(self.sleeps[-1], self.script.BUSY_RECHECK_SECONDS)

    def test_a_standing_down_watchdog_seen_once_does_not_break_the_chain(self):
        """A short-lived scheduled run that is gone at the re-check must not stop the hand-over."""
        snapshots = iter([[_run(7, 'in_progress', 5)], []])
        base = {'GH_REPO': 'x/y', 'RUN_ID': '500', 'REF_NAME': 'main', 'EVENT_NAME': 'workflow_dispatch',
                'INPUT_SHARD': '1/2'}
        with mock.patch.object(self.script, 'run_gh', self.gh):
            self.script.cmd_relay(env=base, runs_fn=lambda: next(snapshots), started_fn=lambda: NOW - 200 * 60,
                                  sleep=self.sleeps.append, now_fn=lambda: NOW)
        self.assertEqual(self.sleeps, [self.script.BUSY_RECHECK_SECONDS])
        self.assertEqual(len(self.gh.calls), 1)
        self.assertIn('shard=2/2', self.gh.calls[0])

    def test_does_nothing_for_an_unsharded_run(self):
        """A manual run of the whole catalogue never starts a chain."""
        self._relay({'INPUT_SHARD': ''})
        self.assertEqual((self.gh.calls, self.sleeps), ([], []))

    def test_stops_when_the_hop_limit_is_used_up(self):
        """relay_hops=0 ends the chain without waiting or dispatching."""
        self._relay({'INPUT_SHARD': '1/2', 'INPUT_HOPS': '0'})
        self.assertEqual((self.gh.calls, self.sleeps), ([], []))

    def test_lookup_failure_skips_the_handover_safely(self):
        """If runs cannot be listed, nothing is dispatched; the watchdog repairs the chain."""
        self._relay({'INPUT_SHARD': '1/2'}, runs_error=self.script.GhError('down'))
        self.assertEqual(self.gh.calls, [])

    def test_one_failed_dispatch_is_retried(self):
        """A transient dispatch error is retried once after a short pause."""
        self.gh.failures = 1
        self._relay({'INPUT_SHARD': '1/2'})
        self.assertEqual(len(self.gh.calls), 2)
        self.assertEqual(self.sleeps[-1], 20)

    def test_two_failed_dispatches_fail_the_job(self):
        """A second failure raises, so the job goes red and the watchdog takes over."""
        self.gh.failures = 2
        with self.assertRaises(self.script.GhError):
            self._relay({'INPUT_SHARD': '1/2'})

    def test_a_test_chain_alternates_and_stops_after_its_hops(self):
        """relay_hops=2 produces exactly two hand-overs (1/2 -> 2/2 -> 1/2) and then stops."""
        env = {'INPUT_SHARD': '1/2', 'INPUT_HOPS': '2', 'INPUT_GAP': '1', 'INPUT_DRY_RUN': 'true'}
        dispatched = []
        for _ in range(5):  # more rounds than needed: the chain must stop by itself
            self.gh.calls.clear()
            self._relay(env, started=NOW - 60)
            if not self.gh.calls:
                break
            args = self.gh.calls[0]
            dispatched.append(next(a for a in args if a.startswith('shard=')))
            env = {'INPUT_SHARD': dispatched[-1].split('=')[1], 'INPUT_DRY_RUN': 'true', 'INPUT_GAP': '1',
                   'INPUT_HOPS': next(a for a in args if a.startswith('relay_hops=')).split('=')[1]}
        self.assertEqual(dispatched, ['shard=2/2', 'shard=1/2'])


@unittest.skipIf(yaml is None, 'PyYAML is not installed')
class WorkflowRelayStructureTests(SimpleTestCase):
    """The workflow file wires the gate, the update and the relay together correctly."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document, cls.crons, cls.slice_step, cls.steps = _load_workflow('update-ebay-prices.yml')
        cls.triggers = cls.document.get('on', cls.document.get(True))
        cls.jobs = cls.document['jobs']
        cls.script = _load_script()

    def test_python_cron_mapping_equals_the_bash_slice_step(self):
        """The script and the workflow's slice step can never disagree about a cron's slice."""
        bash = {cron: f'{k}/{n}' for cron, k, n in _slice_mapping(self.slice_step['run'])}
        self.assertEqual(bash, self.script.SCHEDULE_SLICES)
        self.assertEqual(sorted(bash), sorted(self.crons))

    def test_the_three_jobs_are_chained_in_order(self):
        """gate -> update-prices -> relay."""
        self.assertEqual(set(self.jobs), {'gate', 'update-prices', 'relay'})
        self.assertEqual(self.jobs['update-prices']['needs'], 'gate')
        self.assertEqual(self.jobs['update-prices']['if'], "needs.gate.outputs.go == 'true'")
        self.assertEqual(sorted(self.jobs['relay']['needs']), ['gate', 'update-prices'])

    def test_a_slice_can_never_outlast_the_relay_spacing(self):
        """The update cap leaves headroom over today's 126-minute worst case yet stays under the 180-minute gap."""
        cap = self.jobs['update-prices']['timeout-minutes']
        self.assertGreaterEqual(cap, 150)
        self.assertLess(cap, self.script.DEFAULT_GAP_MINUTES)

    def test_relay_runs_after_a_failure_but_not_after_a_cancel(self):
        """!cancelled() continues the chain after a failed slice; cancelling is the stop button."""
        condition = self.jobs['relay']['if']
        self.assertIn('!cancelled()', condition)
        self.assertNotIn('always()', condition)
        self.assertIn("needs.gate.outputs.relay == 'true'", condition)
        self.assertIn("needs.gate.outputs.go == 'true'", condition)

    def test_relay_job_can_wait_long_enough_but_not_forever(self):
        """The relay job outlives the longest wait (180 min) and stays under GitHub's 6 h limit."""
        self.assertGreaterEqual(self.jobs['relay']['timeout-minutes'], 190)
        self.assertLessEqual(self.jobs['relay']['timeout-minutes'], 330)
        self.assertLessEqual(self.jobs['gate']['timeout-minutes'], 10)

    def test_token_may_start_workflows_but_not_write_code(self):
        """actions: write (to dispatch) and contents: read only."""
        self.assertEqual(self.document['permissions'], {'contents': 'read', 'actions': 'write'})

    def test_new_inputs_exist_and_are_off_by_default(self):
        """relay is off for hand-started runs unless asked; test knobs default to blank."""
        inputs = self.triggers['workflow_dispatch']['inputs']
        self.assertIs(inputs['relay']['default'], False)
        self.assertEqual(inputs['relay_gap_minutes']['default'], '')
        self.assertEqual(inputs['relay_hops']['default'], '')

    def test_every_env_var_the_script_reads_is_passed_by_the_workflow(self):
        """No silent mismatch between the script's inputs and the steps' env blocks."""
        source = _SCRIPT.read_text(encoding='utf-8')
        needed = set(re.findall(r"env(?:\.get\(|\[)'([A-Z_]+)'", source)) | set(self.script.FILTER_INPUTS)
        needed -= {'GITHUB_OUTPUT'}  # read from os.environ by GitHub itself
        passed = set()
        for job in ('gate', 'relay'):
            for step in self.jobs[job]['steps']:
                passed |= set(step.get('env', {}))
        self.assertEqual(needed - passed, set())

    def test_cron_lines_are_unchanged(self):
        """The watchdog keeps the original two cron lines."""
        self.assertEqual(self.crons, ['10 0,6,12,18 * * *', '10 3,9,15,21 * * *'])

    def test_relay_dispatches_this_workflow_file(self):
        """The script starts the same file the workflow lives in."""
        self.assertEqual(self.script.WORKFLOW_FILE, _WORKFLOW.name)
