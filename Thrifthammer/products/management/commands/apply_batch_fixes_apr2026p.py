"""
apply_batch_fixes_apr2026p
~~~~~~~~~~~~~~~~~~~~~~~~~~
Gladiator kit consolidation — Lancer / Reaper / Valiant are the same physical
kit sold under three names.

For each Space Marines product:
  1. Copy all CurrentPrice rows from Gladiator Lancer to Gladiator Reaper
     and Gladiator Valiant (update_or_create so existing rows are updated,
     not duplicated).
  2. Set ebay_search_name = "Gladiator Lancer" on Reaper and Valiant so the
     eBay scraper queries the correct listing name.

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from prices.models import CurrentPrice
from products.models import Product


class Command(BaseCommand):
    """Copy Gladiator Lancer retailer links to Reaper and Valiant; align eBay search names."""

    help = 'Apr-2026-p: Consolidate Gladiator Lancer/Reaper/Valiant retailer links and eBay search names.'

    def handle(self, *args, **options):
        """Copy CurrentPrice rows from Lancer to Reaper/Valiant; set eBay search names."""

        lancer = Product.objects.filter(
            name='Gladiator Lancer', faction__name='Space Marines'
        ).first()
        if not lancer:
            self.stdout.write(self.style.ERROR('Gladiator Lancer (Space Marines) not found.'))
            return

        targets = Product.objects.filter(
            name__in=['Gladiator Reaper', 'Gladiator Valiant'],
            faction__name='Space Marines',
        )
        if not targets.exists():
            self.stdout.write(self.style.ERROR('Gladiator Reaper / Valiant not found.'))
            return

        lancer_prices = CurrentPrice.objects.filter(product=lancer).select_related('retailer')
        if not lancer_prices.exists():
            self.stdout.write(self.style.WARNING(
                'Gladiator Lancer has no CurrentPrice rows to copy.'
            ))

        with transaction.atomic():
            for target in targets:
                # ── Copy retailer links ───────────────────────────────────────
                for cp in lancer_prices:
                    obj, created = CurrentPrice.objects.update_or_create(
                        product=target,
                        retailer=cp.retailer,
                        defaults={
                            'price':               cp.price,
                            'url':                 cp.url,
                            'listing_title':       cp.listing_title,
                            'in_stock':            cp.in_stock,
                            'not_available':       cp.not_available,
                            'manual_url_override': cp.manual_url_override,
                        },
                    )
                    action = 'CREATED' if created else 'UPDATED'
                    self.stdout.write(
                        f'  [{action}] {target.name} @ {cp.retailer.name}'
                        f'  price=${cp.price}  url={cp.url[:60]}'
                    )

                # ── Align eBay search name ────────────────────────────────────
                target.ebay_search_name = 'Gladiator Lancer'
                target.save(update_fields=['ebay_search_name'])
                self.stdout.write(
                    f'  [EBAY]   {target.name} ebay_search_name -> "Gladiator Lancer"'
                )

        self.stdout.write(self.style.SUCCESS('\nDone.'))
