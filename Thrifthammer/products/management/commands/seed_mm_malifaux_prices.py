"""
Management command: seed_mm_malifaux_prices

Seeds Miniature Market CurrentPrice records for Malifaux products.

MM's Malifaux catalog is overwhelmingly 3rd Edition (a different product
line from our 4th Edition products). Only 5 of 51 products have a confirmed
4th Edition Miniature Market listing so far -- the rest are intentionally
left out, per the "no match = no entry" rule. More links to be added in a
future session as MM's 4E catalog grows.

Usage:
    python manage.py seed_mm_malifaux_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    ('malifaux-fourth-edition-two-player-starter', 'Malifaux 4E: Two-Player Starter (Preorder)', None, 'https://www.miniaturemarket.com/Malifaux-4E-Two-Player-Starter-Preorder/WYR24901', False, False),
    ('malifaux-fourth-edition-pandora-tyrant-torn', 'Malifaux 4E: Neverborn - Pandora, Tyrant Torn (Preorder)', None, 'https://www.miniaturemarket.com/Malifaux-4E-Neverborn-Pandora-Tyrant-Torn-Preorder/WYR24402', False, False),
    ('malifaux-fourth-edition-jakob-lynch-wild-card', 'Malifaux 4E: Ten Thunders - Jakob Lynch, Wild Card (Preorder)', None, 'https://www.miniaturemarket.com/Malifaux-4E-Ten-Thunders-Jakob-Lynch-Wild-Card-Preorder/WYR24703', False, False),
    ('malifaux-fourth-edition-damian-ravencroft-aspirant', 'Malifaux 4E: Arcanists - Damian Ravencroft, Aspirant (Preorder)', None, 'https://www.miniaturemarket.com/Malifaux-4E-Arcanists-Damian-Ravencroft-Aspirant-Preorder/WYR24307', False, False),
    ('malifaux-fourth-edition-index-of-the-untold-campaign-book', 'Malifaux 4E: Index of the Untold Campaign Book (Preorder)', None, 'https://www.miniaturemarket.com/Malifaux-4E-Index-of-the-Untold-Campaign-Book-Preorder/WYR24019', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Malifaux products (idempotent)."""

    help = 'Seeds Miniature Market CurrentPrice records for Malifaux products.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write(self.style.WARNING('MM_PRICES is empty -- nothing to seed.'))
            return

        retailer = Retailer.objects.get(slug='miniature-market')

        created = 0
        updated = 0

        for slug, listing_title, price, url, in_stock, not_available in MM_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Product not found for slug: {slug}'))
                continue

            _, price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': not_available,
                },
            )
            if price_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Miniature Market prices: {created} created, {updated} updated.'
        ))
