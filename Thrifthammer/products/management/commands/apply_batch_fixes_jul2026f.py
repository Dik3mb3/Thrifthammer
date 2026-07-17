from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = (
        'Jul 2026f: allow digits 1-9 in eBay titles for all Marvel Crisis '
        'Protocol SKUs (fixes false-positive rejection of PRESALE date '
        'fragments like "7/31/2026"); MCP-014 additionally allows "card" '
        '(false-positive from the global bits-filter blocklist).'
    )

    def handle(self, *args, **options):
        fixes = [
            ('ebay_allowed_title_words', 'MCP-001', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-002', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-003', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-004', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-005', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-006', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-007', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-008', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-009', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-010', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-011', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-012', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-013', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-014', 'card 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-015', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-016', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-017', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-018', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-019', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-020', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-021', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-022', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-023', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-024', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-025', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-026', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-027', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-028', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-029', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-030', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-031', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-032', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-033', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-034', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-035', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-036', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-037', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-038', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-039', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-040', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-041', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-042', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-043', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-044', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-045', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-046', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-047', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-048', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-049', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-050', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-051', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-052', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-053', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-054', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-055', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-056', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-057', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-058', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-059', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-060', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-061', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-062', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-063', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-064', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-065', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-066', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-067', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-068', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-069', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-070', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-071', '1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-072', '& 1 2 3 4 5 6 7 8 9'),
            ('ebay_allowed_title_words', 'MCP-073', '1 2 3 4 5 6 7 8 9'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026f done'))
