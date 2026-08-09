from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026f: fix ebay_search_name for Chaos Space Marine Cypher '
        '(CSM-009) -- was "Cypher Dark Angels Chaos Space Marine" (singular '
        '"Marine", plus "Dark Angels"). Confirmed adding any negative '
        'keyword to an eBay query collapses the candidate pool sharply, '
        'and only listings matching the query wording closely survive; '
        'real listings almost universally say "Chaos Space Marines" '
        '(plural) and rarely mention "Dark Angels", so the search was '
        'only finding one overpriced listing ($74.99). Confirmed the fix '
        'restores a full, valid candidate pool and the automated matcher '
        'picks a real $39.00 listing on its own (2026-08-07).'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='CSM-009').update(
            ebay_search_name='Cypher Chaos Space Marines'
        )
        self.stdout.write(f'CSM-009 ebay_search_name updated, rows={updated}')
        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026f done'))
