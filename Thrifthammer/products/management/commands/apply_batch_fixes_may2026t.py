"""
Phase 2 UK isolation: set is_uk=True on all UK retailers.

Marks ebay-uk, amazon-uk, and games-workshop-uk as UK retailers so
views can filter by retailer__is_uk=True instead of maintaining a
slug-based frozenset.  Idempotent — safe to re-run.
"""
from django.core.management.base import BaseCommand

from products.models import Retailer

_UK_SLUGS = ['ebay-uk', 'amazon-uk', 'games-workshop-uk']


class Command(BaseCommand):
    help = 'Set is_uk=True on all UK retailers. Idempotent.'

    def handle(self, *args, **options):
        updated = Retailer.objects.filter(slug__in=_UK_SLUGS).update(is_uk=True)
        self.stdout.write(f'Set is_uk=True on {updated} UK retailer(s).')
