"""
Management command: seed_nk_votann_prices

Seeds Noble Knight prices for Leagues of Votann products.

Source: Warhammer 40,000 - Noble Knight Gamesv3.xlsx (761 rows, Apr 2026)

NK MATCHES (2 products):
  - Brokhyr Iron-Master  $52.95
  - Codex: Leagues of Votann  $54.95

GAPS - not in NK spreadsheet:
  Kahl, Uthar the Destined, Hekaton Land Fortress, Brokhyr Thunderkyn,
  Grimnyr, Sagitaur, Cthonian Berserks, all 2025/2026 releases,
  Kill Team products, Kapricus, Earthshakers, Buri, Arkanyst, Memnyr, Ironkin

Affiliate tag ?awid=1576 appended to all URLs.
Idempotent -- safe to re-run.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    (
        'leagues-of-votann-brokhyr-iron-master',
        'Brokhyr Iron-Master',
        52.95,
        'https://www.nobleknight.com/P/2148011869/Brokhyr-Iron-Master?awid=1576',
        False,
        False,
    ),
    (
        'codex-leagues-of-votann',
        'Codex - Leagues of Votann',
        54.95,
        'https://www.nobleknight.com/P/2148375907/Codex---Leagues-of-Votann?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Leagues of Votann products."""

    help = 'Seeds Noble Knight listing URLs and prices for Leagues of Votann. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        nk = Retailer.objects.filter(name='Noble Knight Games').first()
        if not nk:
            self.stdout.write(self.style.ERROR('Noble Knight Games retailer not found'))
            return

        seeded = 0
        missing = 0

        for slug, title, price, url, in_stock, not_available in NK_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(f'  [missing] {slug}'))
                missing += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
                defaults={
                    'listing_title': title,
                    'price': price,
                    'url': url,
                    'in_stock': in_stock,
                    'not_available': not_available,
                    'last_seen': timezone.now(),
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {product.name} @ ${price}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Seeded={seeded}, Missing={missing}'
        ))
