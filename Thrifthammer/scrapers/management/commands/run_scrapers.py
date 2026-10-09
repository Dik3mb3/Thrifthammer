"""
Management command to run price scrapers.

Usage:
    python manage.py run_scrapers                 # run all active scrapers
    python manage.py run_scrapers example-store    # run a specific scraper

Partial (daily slice) runs, for the retailers that support them:
    python manage.py run_scrapers noble-knight-games --shard 3/7 --limit 500
    python manage.py run_scrapers noble-knight-games --shard 3/7 --dry-run

``--shard INDEX/COUNT`` visits only the rows whose id % COUNT == INDEX, so each
row is refreshed once every COUNT runs.  For the scrapers that have the run
guard (Noble Knight, Miniature Market, Firestorm) the command exits with an
error when a job fails or the scraper crashes, so a scheduled run that was
blocked or aborted shows up as a failed GitHub job instead of passing silently.
Other scrapers (Amazon, example-store) behave exactly as before.
"""

import inspect

from django.core.management.base import BaseCommand, CommandError

from scrapers.registry import SCRAPER_REGISTRY
from scrapers.safeguards import parse_shard


class Command(BaseCommand):
    help = 'Run price scrapers for Warhammer retailers'

    def add_arguments(self, parser):
        parser.add_argument(
            'retailer',
            nargs='?',
            help='Retailer slug to scrape (omit to run all)',
        )
        parser.add_argument(
            '--batch-tag',
            type=str,
            default=None,
            metavar='TAG',
            help='Only scrape products with this batch_tag (e.g. blood-bowl, phase-2).',
        )
        parser.add_argument(
            '--shard',
            type=str,
            default=None,
            metavar='INDEX/COUNT',
            help='Only visit rows whose id %% COUNT == INDEX (for example 3/7).',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            metavar='N',
            help='Visit at most N rows (a safety cap, used with --shard).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List how many rows would be visited and show a few; fetch nothing.',
        )

    def handle(self, *args, **options):
        retailer_slug = options.get('retailer')
        batch_tag = options.get('batch_tag')
        limit = options.get('limit')
        shard = self._parse_shard_option(options.get('shard'))

        if retailer_slug:
            scrapers = {retailer_slug: SCRAPER_REGISTRY.get(retailer_slug)}
            if not scrapers[retailer_slug]:
                self.stderr.write(self.style.ERROR(f'Unknown retailer: {retailer_slug}'))
                self.stderr.write(f'Available: {", ".join(SCRAPER_REGISTRY.keys())}')
                return
        else:
            scrapers = SCRAPER_REGISTRY

        kwargs = {}
        if shard is not None:
            kwargs['shard'] = shard
        if limit:
            kwargs['limit'] = limit

        failures = []
        for slug, scraper_class in scrapers.items():
            self.stdout.write(f'Running scraper: {slug}...')
            try:
                scraper = scraper_class()
                if kwargs and not self._supports(scraper, kwargs):
                    raise CommandError(f'{slug} does not support --shard / --limit yet.')
                if options.get('dry_run'):
                    self._dry_run(slug, scraper, batch_tag, shard, limit)
                    continue
                job = scraper.run(batch_tag=batch_tag, **kwargs)
                self.stdout.write(self.style.SUCCESS(
                    f'  {slug}: {job.status} — '
                    f'{job.products_found} found, {job.prices_updated} updated'
                ))
                if job.errors:
                    self.stderr.write(f'  Errors:\n{job.errors}')
                if job.status == 'failed':
                    failures.append(slug)
            except CommandError:
                raise
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  {slug} failed: {exc}'))
                # Only the scrapers with the run guard fail the command; the
                # others keep their old behavior of reporting and moving on.
                if hasattr(scraper_class, 'select_entries'):
                    failures.append(slug)

        if failures:
            raise CommandError('Scrape did not complete cleanly: ' + ', '.join(failures))

    @staticmethod
    def _parse_shard_option(value):
        """Turn the --shard text into (index, count), or None when not given."""
        if not value:
            return None
        try:
            return parse_shard(value)
        except ValueError as exc:
            raise CommandError(f'--shard: {exc}')

    @staticmethod
    def _supports(scraper, kwargs):
        """True when the scraper's run() accepts every option in kwargs."""
        params = inspect.signature(scraper.run).parameters
        return all(name in params for name in kwargs)

    def _dry_run(self, slug, scraper, batch_tag, shard, limit):
        """Print how many rows a real run would visit, without fetching anything."""
        if not hasattr(scraper, 'select_entries'):
            raise CommandError(f'{slug} does not support --dry-run yet.')
        entries = list(scraper.select_entries(batch_tag=batch_tag, shard=shard, limit=limit))
        self.stdout.write(f'  {slug}: {len(entries)} rows would be visited (nothing fetched).')
        for entry in entries[:10]:
            self.stdout.write(f'    {entry.product.gw_sku} | {entry.product.name[:50]} | {entry.url[:70]}')
