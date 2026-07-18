from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026l: eBay negative keyword addition for Marvel: Crisis '
        'Protocol - Guardians of the Galaxy Starter Set (MCP-024) to block '
        'a mismatched listing titled "...Miniatures Game 14+" (item '
        '136361046636, seller toyz_tt_fun_5427).'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', 'MCP-024', 'affiliation legions imperialis Resin 04-113 Proxies Foil "game 14"'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026l done'))
