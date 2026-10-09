"""
Shared helpers for the partial (daily slice) refresh mode of the retailer scrapers.

Used by the Noble Knight, Miniature Market and Firestorm scrapers.  Nothing in
here touches the database by itself except ``select_slice`` (which only builds a
queryset) and ``RunGuard.apply_blanks`` (which saves the rows it was given).

Why this exists
---------------
A full pass over a retailer takes hours, gets cut off by the GitHub job timeout
and, for Firestorm, trips Cloudflare.  The partial mode refreshes only one
slice per run (rows whose ``id % count == index``), so every row is visited once
per ``count`` runs and a missed day only delays one slice.  The guard makes sure
a bad day (the site blocks us, goes down or changes its markup) changes nothing
instead of blanking prices by accident.
"""

import logging
import math

from django.db import close_old_connections
from django.db.models import Value
from django.db.models.functions import Mod
from django.utils import timezone

logger = logging.getLogger(__name__)

# Stop the run after this many failed rows in a row (blocked, network error,
# server error).  404s do not count: a stale link is not a sign of trouble.
MAX_CONSECUTIVE_FAILURES = 8

# A run may blank at most this many prices that were previously set, or this
# share of the priced rows it checked, whichever is larger.  Real sell-outs and
# delistings happen a few at a time; anything bigger means the site changed or
# is misbehaving, so no blanking is applied at all.
MAX_NEW_BLANKS = 10
MAX_NEW_BLANK_RATIO = 0.10


def parse_shard(value):
    """
    Parse a shard spec such as ``'3/7'`` into ``(3, 7)``.

    ``index`` must be in ``0 .. count - 1``.  Raises ``ValueError`` otherwise so
    a typo in a workflow fails loudly instead of silently scraping everything.
    """
    try:
        index_text, count_text = str(value).split('/')
        index, count = int(index_text), int(count_text)
    except (ValueError, TypeError):
        raise ValueError('shard must look like INDEX/COUNT, for example 3/7')
    if count < 1 or not 0 <= index < count:
        raise ValueError('shard INDEX must be between 0 and COUNT-1')
    return index, count


def select_slice(queryset, shard=None, limit=None):
    """
    Narrow ``queryset`` to today's slice.

    With neither ``shard`` nor ``limit`` the queryset is returned untouched, so
    the default behavior (and ordering) of a full run does not change.  Otherwise
    the rows are put in a stable ``id`` order, filtered to ``id % count == index``
    and capped at ``limit`` rows.
    """
    if shard is None and not limit:
        return queryset
    if shard is not None:
        index, count = shard
        queryset = queryset.annotate(shard_bucket=Mod('id', Value(count))).filter(shard_bucket=index)
    queryset = queryset.order_by('id')
    if limit:
        queryset = queryset[:limit]
    return queryset


class RunGuard:
    """
    Tracks the health of one scrape run and holds back risky writes.

    * ``record_ok`` / ``record_failure``: consecutive failures trip the guard and
      the run loop stops early.
    * ``defer_blank``: price blanking is collected, not applied immediately.
    * ``blanks_ok`` / ``apply_blanks``: at the end of the run the blanks are only
      applied when their number is believable (see MAX_NEW_BLANKS).
    """

    def __init__(self, max_consecutive_failures=MAX_CONSECUTIVE_FAILURES,
                 max_new_blanks=MAX_NEW_BLANKS, max_blank_ratio=MAX_NEW_BLANK_RATIO):
        self.max_consecutive_failures = max_consecutive_failures
        self.max_new_blanks = max_new_blanks
        self.max_blank_ratio = max_blank_ratio
        self.consecutive_failures = 0
        self.tripped_reason = ''
        self.priced_checked = 0
        self.blank_candidates = []

    @property
    def tripped(self):
        """True once the run has hit too many failures in a row."""
        return bool(self.tripped_reason)

    def record_ok(self, was_priced=False):
        """Note a row that got a normal answer from the site."""
        self.consecutive_failures = 0
        if was_priced:
            self.priced_checked += 1

    def record_failure(self, blocked=False):
        """Note a row that failed; trip the guard after too many in a row."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_consecutive_failures and not self.tripped:
            kind = 'blocked or challenged' if blocked else 'failing'
            self.tripped_reason = (
                f'{self.consecutive_failures} rows in a row were {kind}; '
                'the run stopped without changing anything further'
            )

    def defer_blank(self, entry, reason):
        """Remember a row that looks sold out or delisted; nothing is saved yet."""
        self.blank_candidates.append((entry, reason))

    def allowed_blanks(self):
        """How many previously priced rows this run may blank."""
        return max(self.max_new_blanks, math.ceil(self.max_blank_ratio * self.priced_checked))

    def blanks_ok(self):
        """True when the number of pending blanks is believable."""
        return len(self.blank_candidates) <= self.allowed_blanks()

    def apply_blanks(self):
        """Blank every deferred row (price None, out of stock). Returns the count."""
        for entry, reason in self.blank_candidates:
            entry.price = None
            entry.in_stock = False
            entry.save(update_fields=['price', 'in_stock', 'last_seen'])
            logger.warning('[guard] blanked %s (%s)', entry.id, reason)
        return len(self.blank_candidates)


def note_crash(guard):
    """
    Handle a row whose processing raised an unexpected error.

    The row counts as a failure, so a run that crashes on every row (for example
    because the database went away) stops after a few rows instead of grinding
    through the whole slice.  ``close_old_connections`` drops a broken database
    connection so the next row can open a fresh one; it leaves a healthy
    connection alone.
    """
    guard.record_failure()
    close_old_connections()


def finish_run(job, guard, errors, label):
    """
    Close a ScrapeJob once the run loop has ended.

    A tripped guard marks the job failed and applies nothing that was held
    back.  Otherwise the held-back blanks are applied only when their number is
    believable.  A failed job makes ``run_scrapers`` exit with an error, which
    turns the scheduled GitHub run red and sends the owner an email.  Returns
    the final status.
    """
    status = 'success'
    blanked = 0
    if guard.tripped:
        status = 'failed'
        errors.append('ABORTED: ' + guard.tripped_reason)
    elif guard.blank_candidates:
        if guard.blanks_ok():
            blanked = guard.apply_blanks()
        else:
            status = 'failed'
            errors.append(
                'NOT APPLIED: %d prices looked sold out or delisted, more than the %d a '
                'normal run has, so nothing was blanked'
                % (len(guard.blank_candidates), guard.allowed_blanks())
            )
    logger.warning(
        '[%s] run summary: %s | rows %d, updated %d, blanked %d, held back %d, problems %d',
        label, status, job.products_found, job.prices_updated, blanked,
        len(guard.blank_candidates) - blanked, len(errors),
    )
    job.status = status
    job.errors = '\n'.join(errors)
    job.finished_at = timezone.now()
    job.save()
    return status
