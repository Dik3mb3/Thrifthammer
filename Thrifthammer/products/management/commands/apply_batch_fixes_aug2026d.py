from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Aug 2026d: eBay negative keyword additions -- "Icon"/"Despair" added to '
        'Death Guard Plague Marines (43-50); "Dice"/"Tokens" added to Marvel: '
        'Crisis Protocol X-Men Starter Set (MCP-001) and Spider Foes Starter Set '
        '(MCP-005); "Recon" added to BattleTech: Inner Sphere Heavy Lance '
        '(BT-101). Marvel: Crisis Protocol Guardians of the Galaxy Starter Set '
        '(MCP-024) already had "affiliation" -- no keyword change needed there, '
        'but its matched US eBay listing (item 198533333025) turned out to be a '
        'mislabeled Affiliation Pack, not the Starter Set -- the seller\'s title '
        'didn\'t contain "affiliation" so the existing keyword block couldn\'t '
        'catch it, so the specific item ID is blocked instead (item-ID blocking, '
        'not a seller-wide ban -- same mechanism as the apr2026 blocked-item-ID '
        'fixes).'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_negative_keywords', '43-50', 'legions imperialis Resin 04-113 Proxies Foil belcher spewer Plaguecaster "kill team" launcher magazine issue x5 5x x10 10x x2 2x 3x x3 x4 4x Icon Despair'),
            ('ebay_negative_keywords', 'MCP-001', 'legions imperialis Resin 04-113 Proxies Foil magazine issue dice tokens'),
            ('ebay_negative_keywords', 'MCP-005', 'legions imperialis Resin 04-113 Proxies Foil magazine issue dice tokens'),
            ('ebay_negative_keywords', 'BT-101', 'legions imperialis Resin 04-113 Proxies Foil Charger magazine issue recon'),
            ('ebay_negative_keywords', 'MCP-024', 'affiliation legions imperialis Resin 04-113 Proxies Foil "game 14" magazine issue 198533333025'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_aug2026d done'))
