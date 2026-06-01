"""
Management command: apply_batch_fixes_may2026h

eBay search name updates and Pink Horrors 40K price sync.

Changes:
  97-11                    Pink Horrors of Tzeentch
                           ebay_search_name: 'Pink Horrors of Tzeentch Warhammer' → 'Pink Horrors Warhammer'

  P-PINK-HORRORS-40K       Pink Horrors of Tzeentch (40K)
                           ebay_search_name: 'Pink Horrors Tzeentch Daemon Warhammer' → 'Pink Horrors Warhammer'
                           ebay_negative_keywords: add 'artel'
                           eBay CurrentPrice: copy from 97-11 ($39.99, in_stock=True)
                           eBay UK CurrentPrice: copy from 97-11 ($29.50, in_stock=True)
                           Amazon CurrentPrice URL: → B0BL1KFDM5

  prod3700246-99129915062  Beast of Nurgle
                           ebay_search_name: 'Beast of Nurgle Daemon Warhammer' → 'Beasts of Nurgle Warhammer'

  P-TZEENTCH-SCREAMERS     Screamers of Tzeentch
                           ebay_search_name: → 'Screamers of Tzeentch Warhammer'

  P-TZEENTCH-FLAMERS       Flamers of Tzeentch
                           ebay_search_name: → 'Flamers of Tzeentch Warhammer'

  P-KHORNE-BLOODCRUSHERS   Bloodcrushers of Khorne
                           ebay_search_name: 'Bloodcrushers Khorne Daemon Warhammer' → 'Bloodcrushers of Khorne Warhammer'

  P-KHORNE-SKARBRAND       Skarbrand the Bloodthirster
                           ebay_search_name: 'Skarbrand Bloodthirster Khorne Daemon Warhammer' → 'Skarbrand Khorne Warhammer'

  P-TZEENTCH-KAIROS        Kairos Fateweaver
                           ebay_search_name: 'Kairos Fateweaver Tzeentch Daemon Warhammer' → 'Lord of Change Warhammer'

Idempotent — safe to re-run.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product


class Command(BaseCommand):
    """Apply batch fixes may2026h — eBay search name updates and Pink Horrors 40K price sync."""

    help = 'eBay search name updates and Pink Horrors 40K price sync.'

    def handle(self, *args, **options):
        """Run the command."""
        # ── Product field updates ──────────────────────────────────────────────

        Product.objects.filter(gw_sku='97-11').update(
            ebay_search_name='Pink Horrors Warhammer',
        )

        Product.objects.filter(gw_sku='P-PINK-HORRORS-40K').update(
            ebay_search_name='Pink Horrors Warhammer',
            ebay_negative_keywords='artel legions imperialis Resin 04-113 D&D 5e 100th 1926 TShirt Plushie Plush',
        )

        Product.objects.filter(gw_sku='prod3700246-99129915062').update(
            ebay_search_name='Beasts of Nurgle Warhammer',
        )

        Product.objects.filter(gw_sku='P-TZEENTCH-SCREAMERS').update(
            ebay_search_name='Screamers of Tzeentch Warhammer',
        )

        Product.objects.filter(gw_sku='P-TZEENTCH-FLAMERS').update(
            ebay_search_name='Flamers of Tzeentch Warhammer',
        )

        Product.objects.filter(gw_sku='P-KHORNE-BLOODCRUSHERS').update(
            ebay_search_name='Bloodcrushers of Khorne Warhammer',
        )

        Product.objects.filter(gw_sku='P-KHORNE-SKARBRAND').update(
            ebay_search_name='Skarbrand Khorne Warhammer',
        )

        Product.objects.filter(gw_sku='P-TZEENTCH-KAIROS').update(
            ebay_search_name='Lord of Change Warhammer',
        )

        # ── P-PINK-HORRORS-40K CurrentPrice sync from 97-11 ───────────────────

        pink_40k = Product.objects.get(gw_sku='P-PINK-HORRORS-40K')

        CurrentPrice.objects.filter(
            product=pink_40k,
            retailer__slug='ebay',
        ).update(
            price=Decimal('39.99'),
            url=(
                'https://www.ebay.com/itm/137338143991'
                '?_skw=Pink+Horrors+Warhammer'
                '&mkcid=1&mkrid=711-53200-19255-0&toolid=10001&mkevt=1&campid=5339151938'
            ),
            in_stock=True,
            not_available=False,
        )

        CurrentPrice.objects.filter(
            product=pink_40k,
            retailer__slug='ebay-uk',
        ).update(
            price=Decimal('29.50'),
            url=(
                'https://www.ebay.co.uk/itm/283606661979'
                '?_skw=Pink+Horrors+Warhammer'
                '&mkcid=1&mkrid=3053-169718-145421-0&toolid=10001&mkevt=1&campid=5339151938'
            ),
            in_stock=True,
            not_available=False,
        )

        CurrentPrice.objects.filter(
            product=pink_40k,
            retailer__slug='amazon',
        ).update(
            url='https://www.amazon.com/dp/B0BL1KFDM5?tag=thrifthammer7-20',
        )

        self.stdout.write(self.style.SUCCESS(
            'apply_batch_fixes_may2026h complete.'
        ))
