from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026n: eBay negative keyword additions per user request '
        '2026-08-09. (1) 48-32 "Space Marine Chaplain": add "Jump" '
        '"Pack". (2) 48-40 "Space Marine Outriders": add "(B)". (3) all '
        'active Space Marines-faction products (79 SKUs): add '
        '"Armageddon" -- verified via non-saving shadow tests against an '
        '8-SKU spread before writing; no existing eBay match changed. '
        'All three use .update() with the complete new string appended '
        'to each row\'s existing value, not a fixed replacement, since '
        'every SKU\'s starting keywords differ.'
    )

    def handle(self, *args, **options):
        updated = Product.objects.filter(gw_sku='48-32').update(
            ebay_negative_keywords=(
                '1x honoured legions imperialis Resin 04-113 Proxies Foil '
                'magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Jump Pack'
            )
        )
        self.stdout.write(f'48-32 ebay_negative_keywords updated, rows={updated}')

        updated = Product.objects.filter(gw_sku='48-40').update(
            ebay_negative_keywords=(
                'legions imperialis Resin 04-113 Proxies Foil magazine '
                'issue x5 5x x10 10x x2 2x 3x x3 x4 4x (B)'
            )
        )
        self.stdout.write(f'48-40 ebay_negative_keywords updated, rows={updated}')

        sm_products = Product.objects.filter(
            faction__name='Space Marines', is_active=True
        )
        touched = 0
        for p in sm_products:
            if 'armageddon' in p.ebay_negative_keywords.lower():
                continue
            p.ebay_negative_keywords = (p.ebay_negative_keywords + ' Armageddon').strip()
            p.save(update_fields=['ebay_negative_keywords'])
            touched += 1
        self.stdout.write(
            f'Space Marines faction: added "Armageddon" to {touched}/{sm_products.count()} products'
        )

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026n done'))
