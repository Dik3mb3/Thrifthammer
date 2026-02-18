"""
Management command to run price scrapers.

Usage:
    python manage.py run_scrapers                 # run all active scrapers
    python manage.py run_scrapers example-store    # run a specific scraper
"""

from django.core.management.base import BaseCommand

from scrapers.registry import SCRAPER_REGISTRY


class Command(BaseCommand):
    help = 'Run price scrapers for Warhammer retailers'

    def add_arguments(self, parser):
        parser.add_argument(
            'retailer',
            nargs='?',
            help='Retailer slug to scrape (omit to run all)',
        )

    def handle(self, *args, **options):
        retailer_slug = options.get('retailer')

        if retailer_slug:
            scrapers = {retailer_slug: SCRAPER_REGISTRY.get(retailer_slug)}
            if not scrapers[retailer_slug]:
                self.stderr.write(self.style.ERROR(f'Unknown retailer: {retailer_slug}'))
                self.stderr.write(f'Available: {", ".join(SCRAPER_REGISTRY.keys())}')
                return
        else:
            scrapers = SCRAPER_REGISTRY

        for slug, scraper_class in scrapers.items():
            self.stdout.write(f'Running scraper: {slug}...')
            try:
                scraper = scraper_class()
                job = scraper.run()
                self.stdout.write(self.style.SUCCESS(
                    f'  {slug}: {job.status} — '
                    f'{job.products_found} found, {job.prices_updated} updated'
                ))
                if job.errors:
                    self.stderr.write(f'  Errors:\n{job.errors}')
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  {slug} failed: {exc}'))
