"""
Management command: seed_mm_chaos_daemons_prices

Seeds Miniature Market prices for Chaos Daemons products (CD-001 to CD-021).

Source: Chaos Demons - GW, NK, MM.xlsx (2026-05-31)

MM MATCHES (4 products):
  CD-001  Be'lakor, the Dark Master
  CD-005  The Masque
  CD-006  Skulltaker
  CD-013  Sloppity Bilepiper

NO MM LISTING (17 products):
  CD-002, CD-003, CD-004, CD-007, CD-008, CD-009, CD-010, CD-011,
  CD-012, CD-014, CD-015, CD-016, CD-017, CD-018, CD-019, CD-020, CD-021

Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)

    (
        'belakor-the-dark-master',
        "Be'lakor, the Dark Master",
        None,
        'https://www.miniaturemarket.com/gw-97-19.html',
        False,
        False,
    ),
    (
        'the-masque',
        'The Masque',
        None,
        'https://www.miniaturemarket.com/warhammer-daemons-hedonites-slaanesh-masque-gw-97-65.html',
        False,
        False,
    ),
    (
        'skulltaker',
        'Skulltaker',
        None,
        'https://www.miniaturemarket.com/gw-97-35.html',
        False,
        False,
    ),
    (
        'sloppity-bilepiper',
        'Sloppity Bilepiper',
        None,
        'https://www.miniaturemarket.com/gw-83-44.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Chaos Daemons products."""

    help = 'Seeds Miniature Market listing URLs and prices for Chaos Daemons. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stdout.write(self.style.ERROR('Miniature Market retailer not found'))
            return

        seeded = 0
        missing = 0

        for slug, title, price, url, in_stock, not_available in MM_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  [missing] {slug}'))
                missing += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
                defaults={
                    'url': url,
                    'listing_title': title,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {product.name}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Seeded={seeded}, Missing={missing}'
        ))
