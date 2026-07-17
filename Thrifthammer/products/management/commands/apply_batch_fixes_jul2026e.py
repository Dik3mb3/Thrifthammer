from django.core.management.base import BaseCommand
from products.models import Product


class Command(BaseCommand):
    help = 'Jul 2026e: eBay search name corrections for Marvel Crisis Protocol no-match SKUs'

    def handle(self, *args, **options):
        fixes = [
            ('ebay_search_name', 'MCP-001', 'Marvel: Crisis Protocol - X-Men Starter Set'),
            ('ebay_search_name', 'MCP-005', 'Marvel: Crisis Protocol - Spider-Foes Starter Set'),
            ('ebay_search_name', 'MCP-006', 'Marvel: Crisis Protocol - Silk, Spider-Ham & Spider-Man Noir'),
            ('ebay_search_name', 'MCP-014', 'Marvel: Crisis Protocol War of Kings Character and Crisis Card Pack'),
            ('ebay_search_name', 'MCP-016', 'Marvel Crisis Protocol: Web-Swinging Heroes Affiliation Pack'),
            ('ebay_search_name', 'MCP-023', 'Marvel Crisis Protocol Uncanny Telepaths & Telekinetics'),
            ('ebay_search_name', 'MCP-027', 'Marvel Crisis Protocol Asgardians Starter Set'),
            ('ebay_search_name', 'MCP-035', 'Marvel Crisis Protocol Hard to Hit'),
            ('ebay_search_name', 'MCP-039', 'Marvel Crisis Protocol Dimensional Terror Terrain Pack'),
            ('ebay_search_name', 'MCP-042', 'Marvel: Crisis Protocol - Dark Dimension Incursion Terrain Pack'),
            ('ebay_search_name', 'MCP-043', 'Spider-Foes Affiliation Pack Marvel Crisis Protocol'),
            ('ebay_search_name', 'MCP-046', 'Marvel Crisis Protocol Winter Guard'),
            ('ebay_search_name', 'MCP-047', 'Marvel: Crisis Protocol - Warriors of Asgard Affiliation Pack'),
            ('ebay_search_name', 'MCP-050', 'Marvel Crisis Protocol Cosmic Motherlode Terrain Pack'),
            ('ebay_search_name', 'MCP-055', 'Elsa Bloodstone & Man-Thing Marvel Crisis Protocol'),
            ('ebay_search_name', 'MCP-066', 'Marvel: Crisis Protocol X-Force Affiliation Pack'),
            ('ebay_search_name', 'MCP-067', 'marvel crisis protocol Onslaught character pack'),
        ]

        for field, sku, value in fixes:
            updated = Product.objects.filter(gw_sku=sku).update(**{field: value})
            self.stdout.write(f'{sku} {field}=[{value}] rows={updated}')

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jul2026e done'))
