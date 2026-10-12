"""
Catalogue sharding for the scheduled eBay price-update commands.

A full eBay pass walks every active product (about 3,250 today, in gw_sku
order) and can run longer than the GitHub Actions timeout. A cancelled run
leaves the tail of the catalogue un-refreshed, so sharding splits the
catalogue into N disjoint slices and lets each scheduled run cover one slice.

A slice is chosen from the product's database id (``id % N``) and evaluated
inside the database every time a command runs. No catalogue size, SKU range or
product list is stored anywhere: a product added tomorrow gets the next id and
falls into exactly one slice automatically, with no code or workflow change.

Shard spec ``K/N``: N is the number of slices and K (1-based) is the slice a
run covers. Slice K holds the products whose ``id % N == K - 1``.

Shared by update_ebay_prices and update_ebay_uk_prices.
"""

import re

from django.core.management.base import CommandError
from django.db.models import Count, IntegerField, Q, Value
from django.db.models.functions import Mod

_SHARD_PATTERN = re.compile(r'^\s*([0-9]+)\s*/\s*([0-9]+)\s*$')
_RESIDUE_ALIAS = 'ebay_shard_residue'


def parse_shard(raw):
    """Parse a ``K/N`` shard spec into an ``(K, N)`` tuple.

    Returns None when ``raw`` is None or blank, meaning "no sharding".
    Raises ValueError for anything malformed or out of range, so a typo can
    never silently turn into a full-catalogue run or an empty run.
    """
    if raw is None or not str(raw).strip():
        return None
    match = _SHARD_PATTERN.match(str(raw))
    if not match:
        raise ValueError(f'Invalid shard "{raw}": expected K/N, for example 1/2.')
    index, parts = int(match.group(1)), int(match.group(2))
    if parts < 1 or not 1 <= index <= parts:
        raise ValueError(
            f'Invalid shard "{raw}": N must be at least 1 and K must be between 1 and N.'
        )
    return index, parts


def parse_shard_option(raw):
    """Command-line wrapper around parse_shard: a bad value becomes a CommandError."""
    try:
        return parse_shard(raw)
    except ValueError as exc:
        raise CommandError(str(exc)) from exc


def _residue(parts):
    """Database expression for ``id % parts`` (an integer)."""
    return Mod('id', Value(parts), output_field=IntegerField())


def apply_shard(queryset, shard):
    """Restrict ``queryset`` to the products in slice K of N.

    ``shard`` is the ``(K, N)`` tuple from parse_shard. Call this before any
    ``[:limit]`` slicing, because a sliced queryset cannot be filtered.
    """
    index, parts = shard
    return (
        queryset
        .annotate(**{_RESIDUE_ALIAS: _residue(parts)})
        .filter(**{_RESIDUE_ALIAS: index - 1})
    )


def shard_counts(queryset, parts):
    """Count ``queryset`` and each of its slices 1..parts in a single query.

    One SELECT gives a consistent snapshot, so a product inserted while the
    check runs cannot make the counts disagree with each other.
    Returns ``(total, {K: count_in_slice_K})``.
    """
    slice_keys = {k: f'slice_{k}' for k in range(1, parts + 1)}
    aggregates = {
        key: Count('id', filter=Q(**{_RESIDUE_ALIAS: k - 1}))
        for k, key in slice_keys.items()
    }
    row = (
        queryset
        .annotate(**{_RESIDUE_ALIAS: _residue(parts)})
        .aggregate(total=Count('id'), **aggregates)
    )
    return row['total'], {k: row[key] for k, key in slice_keys.items()}


def shard_products(queryset, shard):
    """Slice ``queryset`` to ``shard`` and verify the slices cover it exactly.

    The coverage check runs against the live database on every run: it counts
    the catalogue and every slice together and requires the slice counts to
    add up to the catalogue total. The split therefore always reflects the
    catalogue as it is right now, and a run refuses to start if the slicing
    ever stopped covering every product exactly once.

    Returns ``(sharded_queryset, summary_line)``. Raises CommandError when the
    slice counts do not add up to the total.
    """
    index, parts = shard
    total, counts = shard_counts(queryset, parts)
    covered = sum(counts.values())
    if covered != total:
        raise CommandError(
            f'Shard coverage check failed: slices add up to {covered} but the '
            f'catalogue has {total} products ({counts}). Refusing to run so no '
            'product is silently skipped or processed twice.'
        )
    breakdown = ', '.join(f'{k}/{parts}={n}' for k, n in counts.items())
    summary = (
        f'Shard {index}/{parts}: {counts[index]} of {total} products '
        f'(slices: {breakdown}; total {total})'
    )
    return apply_shard(queryset, shard), summary
