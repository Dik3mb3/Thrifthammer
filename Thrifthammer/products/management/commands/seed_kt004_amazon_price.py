from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


class Command(BaseCommand):
    help = "Set KT-004 Amazon price to $62.48 if not already set"

    def handle(self, *args, **options):
        try:
            product = Product.objects.get(gw_sku="KT-004")
            amazon = Retailer.objects.get(slug="amazon")
            cp = CurrentPrice.objects.get(product=product, retailer=amazon)
        except (Product.DoesNotExist, Retailer.DoesNotExist, CurrentPrice.DoesNotExist) as e:
            self.stdout.write(self.style.WARNING(f"Skipped: {e}"))
            return

        if cp.price is None:
            cp.price = Decimal("62.48")
            cp.in_stock = True
            cp.not_available = False
            cp.save(update_fields=["price", "in_stock", "not_available"])
            self.stdout.write(self.style.SUCCESS("KT-004 Amazon price set to $62.48"))
        else:
            self.stdout.write(f"KT-004 Amazon price already set to ${cp.price} — skipped")
