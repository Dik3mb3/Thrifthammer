"""
Management command: apply_batch_fixes_jun2026b

Changes:
  BOK-004  Mighty Skullcrushers
    ebay_search_name: 'Mighty Skullcrushers Blades of Khorne' → 'Mighty Skullcrushers Khorne Warhammer'

  BOK-010  Skullgrinder
    ebay_search_name: 'Skullgrinder Blades of Khorne' → 'Warhammer Blades of Khorne Skullgrinder'

  DOT-001  Warcry: The Jade Obelisk
    ebay_negative_keywords: 'legions imperialis Resin 04-113 Proxies'
                          → 'legions imperialis Resin 04-113 Proxies 18 dice set'
    Reason: eBay dry-run returned a dice set (18 six-sided dice) instead of the miniature warband.

  DOT-005  Magister
    ebay_search_name: 'Magister on Disc of Tzeentch Disciples of Tzeentch'
                    → 'Magister on Disc of Tzeentch Warhammer Age of Sigmar'

  DOT-008  Magister on Disc of Tzeentch
    ebay_search_name: 'Magister on Disc of Tzeentch Disciples of Tzeentch'
                    → 'Magister on Disc of Tzeentch Warhammer Age of Sigmar'

  DOT-012  Argent Shards
    ebay_search_name: 'Argent Shards Disciples of Tzeentch'
                    → 'Disciples of Tzeentch Argent Shards Warhammer'

  MON-002  Lord of Afflictions
    ebay_search_name: 'Pusgoyle Blightlords Maggotkin of Nurgle' → 'Pusgoyle Blightlords Warhammer'

  MON-003  Pusgoyle Blightlords
    ebay_search_name: 'Pusgoyle Blightlords Maggotkin of Nurgle' → 'Pusgoyle Blightlords Warhammer'

  MON-017  Rotmire Creed
    ebay_negative_keywords: 'legions imperialis Resin 04-113 Proxies'
                          → 'legions imperialis Resin 04-113 Proxies dice set'
    Reason: eBay dry-run returned a dice pack instead of the miniature warband.
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """eBay search name and negative keyword fixes for BOK, DOT, MON factions."""

    help = 'apply_batch_fixes_jun2026b — eBay search name and negative keyword fixes'

    def handle(self, *args, **options):
        """Run the command."""
        search_name_fixes = [
            ('BOK-004', 'Mighty Skullcrushers Khorne Warhammer'),
            ('BOK-010', 'Warhammer Blades of Khorne Skullgrinder'),
            ('DOT-005', 'Magister on Disc of Tzeentch Warhammer Age of Sigmar'),
            ('DOT-008', 'Magister on Disc of Tzeentch Warhammer Age of Sigmar'),
            ('DOT-012', 'Disciples of Tzeentch Argent Shards Warhammer'),
            ('MON-002', 'Pusgoyle Blightlords Warhammer'),
            ('MON-003', 'Pusgoyle Blightlords Warhammer'),
        ]

        for sku, value in search_name_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_search_name=value)
            if updated:
                self.stdout.write(f'  {sku}: ebay_search_name set to {repr(value)}')
            else:
                self.stdout.write(self.style.WARNING(f'  {sku}: not found'))

        neg_kw_fixes = [
            ('DOT-001', 'legions imperialis Resin 04-113 Proxies 18 dice set'),
            ('MON-017', 'legions imperialis Resin 04-113 Proxies dice set'),
        ]

        for sku, value in neg_kw_fixes:
            updated = Product.objects.filter(gw_sku=sku).update(ebay_negative_keywords=value)
            if updated:
                self.stdout.write(f'  {sku}: ebay_negative_keywords set to {repr(value)}')
            else:
                self.stdout.write(self.style.WARNING(f'  {sku}: not found'))

        self.stdout.write(self.style.SUCCESS('apply_batch_fixes_jun2026b complete.'))
