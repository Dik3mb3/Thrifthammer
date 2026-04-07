"""
fill_missing_retailer_rows
~~~~~~~~~~~~~~~~~~~~~~~~~~
Ensures every phase-2 and phase-3 product has a CurrentPrice row for each of
the five standard retailers (GW=1, MM=2, NK=3, Amazon=5, eBay=6).  Missing
rows are created with not_available=True and no URL/price so the retailer
column shows up in the product detail chart.

Uses bulk_create for speed (493 rows × 6 cache queries per .save() = ~3000
cache DB hits is too slow).  Price is None on all inserts so track_price_history
would no-op anyway; we bust the relevant caches once at the end instead.

Idempotent — safe to run multiple times.
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


RETAILER_IDS = [1, 2, 3, 5, 6]  # GW, MM, NK, Amazon, eBay


class Command(BaseCommand):
    help = "Add not_available placeholder rows for any retailer missing from phase-2/3 products."

    def handle(self, *args, **options):
        retailers = {r.id: r for r in Retailer.objects.filter(id__in=RETAILER_IDS)}
        products = list(Product.objects.filter(batch_tag__in=["phase-2", "phase-3"]))

        # Build a set of (product_id, retailer_id) pairs that already exist.
        existing_pairs = set(
            CurrentPrice.objects.filter(
                product__in=products, retailer_id__in=RETAILER_IDS
            ).values_list("product_id", "retailer_id")
        )

        to_create = []
        for product in products:
            for rid in RETAILER_IDS:
                if (product.pk, rid) not in existing_pairs:
                    to_create.append(
                        CurrentPrice(
                            product=product,
                            retailer=retailers[rid],
                            price=None,
                            url="",
                            listing_title="",
                            in_stock=False,
                            not_available=True,
                        )
                    )

        if to_create:
            CurrentPrice.objects.bulk_create(to_create, batch_size=200)

        # Bust caches once for all affected products.
        for product in products:
            cache.delete(f"product_detail|{product.slug}")
            cache.delete(f"cheapest_price_{product.pk}")
        cache.delete("home_page_data_v6")
        cache.delete("site_last_price_update")
        cache.add("product_list_generation", 0, timeout=None)
        cache.incr("product_list_generation")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created {len(to_create)} placeholder rows across {len(products)} products."
            )
        )
