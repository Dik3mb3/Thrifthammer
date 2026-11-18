#!/usr/bin/env python3
"""
Relay logic for the "Update eBay Prices" GitHub workflow (standard library only).

Why this exists: GitHub's cron scheduler is best effort. For this repository it fires
only 2 to 5 of the 8 daily slots and starts them 1 to 3 hours late, but a run started
through workflow_dispatch begins within seconds. The relay therefore lets every run
start the NEXT slice itself, so the two catalogue halves alternate every 3 hours no
matter what the scheduler does. The cron lines stay in the workflow as a watchdog that
restarts the chain if it ever breaks.

Two sub-commands, called from two small jobs of the workflow:

  gate   runs before the price update. A scheduled run stands down when another run is
         already active (the chain is alive), so GitHub's late cron never duplicates a
         slice or wastes eBay API calls. Manual runs always go ahead.
  relay  runs after the price update (success or failure, not when cancelled). It waits
         until `gap` minutes after this run started (3 hours by default), then
         dispatches the other slice with relay=true. It never dispatches when another
         run is active, and it stops by itself when relay_hops reaches 0 (used to test).

All inputs arrive as environment variables. Nothing here touches the database or eBay.
"""

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time

WORKFLOW_FILE = 'update-ebay-prices.yml'

# cron string -> catalogue slice. Must match the "Pick catalogue slice" step of the
# workflow; products/test_ebay_relay.py checks both against the real workflow file.
SCHEDULE_SLICES = {
    '10 0,6,12,18 * * *': '1/2',
    '10 3,9,15,21 * * *': '2/2',
}
OTHER_SLICE = {'1/2': '2/2', '2/2': '1/2'}

ACTIVE_STATUSES = frozenset({'queued', 'in_progress', 'waiting', 'pending', 'requested'})
# Only runs created in the last 8 hours count as "active": a run can never legitimately
# last longer, and this ignores runs that are stuck in "queued" forever.
ACTIVE_WINDOW_SECONDS = 8 * 3600
DEFAULT_GAP_MINUTES, MIN_GAP_MINUTES, MAX_GAP_MINUTES = 180, 1, 360
# A scheduled run that stands down is over in seconds; if an "active" run is seen at hand-over
# time, look once more after this pause before concluding that a real successor exists.
BUSY_RECHECK_SECONDS = 45
# Manual filters that make a run partial; a partial run must never start a chain.
FILTER_INPUTS = ('INPUT_SKUS', 'INPUT_BATCH_TAG', 'INPUT_CATEGORY')


class GhError(RuntimeError):
    """Raised when the GitHub CLI fails."""


def run_gh(args):
    """Run the GitHub CLI with the given arguments and return its stdout."""
    done = subprocess.run(['gh', *args], capture_output=True, text=True, timeout=90, check=False)
    if done.returncode != 0:
        raise GhError(f'gh {" ".join(args[:3])} failed: {done.stderr.strip()[:300]}')
    return done.stdout


def parse_time(text):
    """Parse a GitHub ISO timestamp such as 2026-11-18T19:23:01Z into epoch seconds."""
    return dt.datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp()


def truthy(value):
    """True for the strings GitHub uses for a checked boolean input."""
    return str(value or '').strip().lower() == 'true'


def active_other_runs(runs, self_id, now):
    """Return the runs (other than this one) that are queued or running and recent."""
    return [
        run for run in runs
        if str(run['databaseId']) != str(self_id)
        and run['status'] in ACTIVE_STATUSES
        and now - parse_time(run['createdAt']) < ACTIVE_WINDOW_SECONDS
    ]


def shard_for(event, schedule, input_shard):
    """The catalogue slice this run covers ('1/2', '2/2', or '' for unsharded/unknown)."""
    if event == 'schedule':
        return SCHEDULE_SLICES.get(schedule, '')
    return (input_shard or '').strip()


def filters_empty(env):
    """True when no manual filter (skus, batch tag, category) narrows the run."""
    return not any((env.get(name) or '').strip() for name in FILTER_INPUTS)


def gate_decision(env, runs, now):
    """Decide whether the price update runs and whether this run continues the relay."""
    event = env.get('EVENT_NAME', '')
    shard = shard_for(event, env.get('SCHEDULE', ''), env.get('INPUT_SHARD', ''))
    if event == 'schedule':
        busy = active_other_runs(runs, env.get('RUN_ID', ''), now)
        if busy:
            return {'go': False, 'relay': False,
                    'reason': f'standing down: {len(busy)} other run(s) already active '
                              f'(first id {busy[0]["databaseId"]}), the relay chain is alive'}
        return {'go': True, 'relay': shard in OTHER_SLICE,
                'reason': f'watchdog: nothing active, this run (slice {shard or "?"}) '
                          'starts the relay chain'}
    relay = truthy(env.get('INPUT_RELAY')) and shard in OTHER_SLICE and filters_empty(env)
    return {'go': True, 'relay': relay,
            'reason': 'manual or relay run: always goes ahead; '
                      f'relay {"on" if relay else "off"}'}


def parse_hops(text):
    """The optional hop limit: None = unlimited, otherwise a whole number."""
    text = (text or '').strip()
    return int(text) if re.fullmatch(r'[0-9]+', text) else None


def parse_gap(text):
    """Minutes between two slice starts, clamped to a safe range."""
    text = (text or '').strip()
    gap = int(text) if re.fullmatch(r'[0-9]+', text) else DEFAULT_GAP_MINUTES
    return max(MIN_GAP_MINUTES, min(MAX_GAP_MINUTES, gap))


def relay_wait_seconds(started, now, gap_minutes):
    """Seconds still to wait so the next slice starts `gap_minutes` after this one began."""
    return max(0, min(gap_minutes * 60, started + gap_minutes * 60 - now))


def relay_dispatch_args(env, next_shard, hops):
    """The `gh workflow run` arguments for the next slice (test settings are inherited)."""
    args = ['workflow', 'run', WORKFLOW_FILE, '--ref', env.get('REF_NAME') or 'main',
            '-f', f'shard={next_shard}', '-f', 'relay=true']
    if truthy(env.get('INPUT_DRY_RUN')):
        args += ['-f', 'dry_run=true']
    if truthy(env.get('INPUT_BOOK_DRY_RUN')):
        args += ['-f', 'book_dry_run=true']
    for name, key in (('INPUT_LIMIT', 'limit'), ('INPUT_BOOK_LIMIT', 'book_limit')):
        value = (env.get(name) or '').strip()
        if re.fullmatch(r'[0-9]+', value):
            args += ['-f', f'{key}={value}']
    gap = (env.get('INPUT_GAP') or '').strip()
    if re.fullmatch(r'[0-9]+', gap):
        args += ['-f', f'relay_gap_minutes={parse_gap(gap)}']
    if hops is not None:
        args += ['-f', f'relay_hops={hops - 1}']
    return args


def list_runs(repo):
    """Recent runs of the workflow: id, status, created time."""
    out = run_gh(['run', 'list', '--repo', repo, '--workflow', WORKFLOW_FILE, '--limit', '60',
                  '--json', 'databaseId,status,createdAt'])
    return json.loads(out)


def run_started_at(repo, run_id):
    """When this run started, from the GitHub API (epoch seconds)."""
    out = run_gh(['api', f'repos/{repo}/actions/runs/{run_id}', '--jq', '.run_started_at'])
    return parse_time(out.strip())


def write_outputs(pairs):
    """Append key=value lines to the step output file, when GitHub provides one."""
    path = os.environ.get('GITHUB_OUTPUT')
    if path:
        with open(path, 'a', encoding='utf-8') as handle:
            handle.writelines(f'{key}={value}\n' for key, value in pairs.items())


def cmd_gate(env=None, now=None, runs_fn=None):
    """The `gate` sub-command: print the decision and publish it as step outputs."""
    env = os.environ if env is None else env
    now = time.time() if now is None else now
    runs = []
    try:
        runs = (runs_fn or (lambda: list_runs(env['GH_REPO'])))()
    except (GhError, ValueError, KeyError) as error:
        # Never lose a scheduled run because of a lookup problem: behave like before the relay.
        print(f'Could not list runs ({error}); falling back to the old behaviour (run, no relay).')
        write_outputs({'go': 'true', 'relay': 'false'})
        return 0
    decision = gate_decision(env, runs, now)
    print(decision['reason'])
    write_outputs({'go': str(decision['go']).lower(), 'relay': str(decision['relay']).lower()})
    return 0


def cmd_relay(env=None, runs_fn=None, started_fn=None, sleep=time.sleep, now_fn=time.time):
    """The `relay` sub-command: wait for the 3-hour mark, then start the other slice."""
    env = os.environ if env is None else env
    repo, run_id = env['GH_REPO'], env['RUN_ID']
    shard = shard_for(env.get('EVENT_NAME', ''), env.get('SCHEDULE', ''), env.get('INPUT_SHARD', ''))
    if shard not in OTHER_SLICE:
        print(f'Relay skipped: slice "{shard}" is not one of 1/2 or 2/2.')
        return 0
    hops = parse_hops(env.get('INPUT_HOPS'))
    if hops is not None and hops <= 0:
        print('Relay stops here: the hop limit is used up (test run).')
        return 0
    gap = parse_gap(env.get('INPUT_GAP'))
    started = (started_fn or (lambda: run_started_at(repo, run_id)))()
    wait = relay_wait_seconds(started, now_fn(), gap)
    print(f'This run is slice {shard}; the next slice ({OTHER_SLICE[shard]}) is due '
          f'{gap} min after this run started, i.e. in {wait // 60} min {wait % 60} s.')
    if wait:
        sleep(wait)
    try:
        fetch = runs_fn or (lambda: list_runs(repo))
        busy = active_other_runs(fetch(), run_id, now_fn())
        if busy:
            sleep(BUSY_RECHECK_SECONDS)  # a standing-down watchdog is gone by now
            busy = active_other_runs(fetch(), run_id, now_fn())
    except (GhError, ValueError) as error:
        print(f'Could not check for active runs ({error}); not starting a successor (the watchdog will).')
        return 0
    if busy:
        print(f'Not starting the next slice: {len(busy)} other run(s) already active '
              f'(first id {busy[0]["databaseId"]}), so the chain already has a successor or a manual run is going.')
        return 0
    args = relay_dispatch_args(env, OTHER_SLICE[shard], hops)
    print('Starting the next slice: gh ' + ' '.join(args))
    try:
        run_gh(args)
    except GhError:
        sleep(20)
        run_gh(args)  # one retry; a second failure fails the job and the watchdog takes over
    return 0


def main(argv):
    """CLI entry point: `ebay_relay.py gate` or `ebay_relay.py relay`."""
    if len(argv) != 2 or argv[1] not in ('gate', 'relay'):
        print('usage: ebay_relay.py gate|relay', file=sys.stderr)
        return 2
    return cmd_gate() if argv[1] == 'gate' else cmd_relay()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
