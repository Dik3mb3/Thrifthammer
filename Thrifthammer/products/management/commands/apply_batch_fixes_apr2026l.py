"""
apply_batch_fixes_apr2026l
~~~~~~~~~~~~~~~~~~~~~~~~~~
Clear not_available=True on eBay rows for all Leagues of Votann products so
the eBay API scraper can find and populate listings for them.
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Faction, Product


class Command(BaseCommand):
    help = "Apr-2026-l: Enable eBay API scraping for all Leagues of Votann products."

    def handle(self, *args, **options):
        lov = Faction.objects.get(slug="leagues-of-votann")
        products = Product.objects.filter(faction=lov)
        cleared = 0

        for product in products:
            cp, created = CurrentPrice.objects.get_or_create(
                product=product,
                retailer_id=6,
                defaults={
                    "price": None,
                    "url": "",
                    "listing_title": "",
                    "in_stock": False,
                    "not_available": False,
                },
            )
            if not created and cp.not_available:
                cp.not_available = False
                cp.url = ""
                cp.price = None
                cp.save()
                cleared += 1
                self.stdout.write(f"  Cleared: {product.slug}")
            elif created:
                cleared += 1
                self.stdout.write(f"  Created: {product.slug}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. {cleared} LoV eBay rows enabled for scraping.")
        )
