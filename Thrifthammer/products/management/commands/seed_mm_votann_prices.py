"""
Management command: seed_mm_votann_prices

Seeds Miniature Market prices for Leagues of Votann products.

Source: Miniature Market - Warhammer 40K ALL SKUS.xlsx (Apr 2026)

MM MATCHES (9 products):
  - Uthar the Destined        gw-69-03  $35.99  In Stock
  - Einhyr Hearthguard        gw-69-04  $53.99  In Stock  (already in DB)
  - Cthonian Berserks         gw-69-05  $53.99  OOS
  - Sagitaur                  gw-69-06  $55.99  OOS
  - Grimnyr                   gw-69-07  $38.99  OOS
  - Brokhyr Thunderkyn        gw-69-08  $51.00  OOS
  - Hekaton Land Fortress     gw-69-09  $100.99 OOS
  - Hearthkyn Warriors        gw-69-10  $51.00  OOS  (already in DB)
  - Hernkyn Pioneers          gw-69-11  $55.99  In Stock  (already in DB)
  - Brokhyr Iron-Master       gw-69-12  $49.99  OOS
  - Einhyr Champion           gw-69-14  $35.99  In Stock  (already in DB)
  - Berehk Stornbrow          non-std   $39.99  OOS
  - Kill Team: Hernkyn Yaegirs gw-103-35 $55.99 OOS

GAPS - no MM listing found:
  Kahl (Online Only on GW), Kapricus, Cthonian Earthshakers, Buri Aegnirssen,
  Arkanyst Evaluator, Memnyr Strategist, Ironkin Steeljacks,
  Kill Team: Hearthkyn Salvagers, Codex (not found in MM data)

Safe to run repeatedly (idempotent via update_or_create).
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

MM_BASE = 'https://www.miniaturemarket.com/'

# (slug, listing_title, price, url, in_stock)
MM_PRICES = [
    # ── New phase-3 products ─────────────────────────────────────────────────
    (
        'leagues-of-votann-uthar-the-destined',
        'Leagues of Votann - Uthar the Destined',
        35.99,
        MM_BASE + 'gw-69-03.html',
        True,
    ),
    (
        'leagues-of-votann-cthonian-berserks',
        'Leagues of Votann - Cthonian Berserks',
        53.99,
        MM_BASE + 'gw-69-05.html',
        False,
    ),
    (
        'leagues-of-votann-sagitaur',
        'Leagues of Votann - Sagitaur',
        55.99,
        MM_BASE + 'gw-69-06.html',
        False,
    ),
    (
        'leagues-of-votann-grimnyr',
        'Leagues of Votann - Grimnyr',
        38.99,
        MM_BASE + 'gw-69-07.html',
        False,
    ),
    (
        'leagues-of-votann-brokhyr-thunderkyn',
        'Leagues of Votann - Brokhyr Thunderkyn',
        51.00,
        MM_BASE + 'gw-69-08.html',
        False,
    ),
    (
        'leagues-of-votann-hekaton-land-fortress',
        'Leagues of Votann - Hekaton Land Fortress',
        100.99,
        MM_BASE + 'gw-69-09.html',
        False,
    ),
    (
        'leagues-of-votann-brokhyr-iron-master',
        'Leagues of Votann - Brokhyr Iron-Master',
        49.99,
        MM_BASE + 'gw-69-12.html',
        False,
    ),
    (
        'leagues-of-votann-berehk-stornbrow',
        'Leagues of Votann - Berehk Stornbrow (New Arrival)',
        39.99,
        MM_BASE + 'Warhammer-40K-Leagues-of-Votann-Berehk-Stornbrow-New-Arrival/GW-69-27-2026',
        False,
    ),
    # Kill Team product -- on LOV GW page, has MM listing
    (
        'leagues-of-votann-kill-team-hernkyn-yaegirs',
        'Warhammer 40K Kill Team: Leagues of Votann - Hernkyn Yaegirs',
        55.99,
        MM_BASE + 'warhammer-40k-kill-team-leagues-votann-hernkyn-yaegirs-gw-103-35.html',
        False,
    ),
    # ── Already in DB products (updating MM price) ───────────────────────────
    (
        'leagues-of-votann-einhyr-hearthguard',
        'Leagues of Votann - Einhyr Hearthguard',
        53.99,
        MM_BASE + 'gw-69-04.html',
        True,
    ),
    (
        'leagues-of-votann-hearthkyn-warriors',
        'Leagues of Votann - Hearthkyn Warriors',
        51.00,
        MM_BASE + 'gw-69-10.html',
        False,
    ),
    (
        'leagues-of-votann-hernkyn-pioneers',
        'Leagues of Votann - Hernkyn Pioneers',
        55.99,
        MM_BASE + 'gw-69-11.html',
        True,
    ),
    (
        'leagues-of-votann-einhyr-champion',
        'Leagues of Votann - Einhyr Champion',
        35.99,
        MM_BASE + 'gw-69-14.html',
        True,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Leagues of Votann products."""

    help = 'Seeds Miniature Market listing URLs and prices for Leagues of Votann. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stderr.write(self.style.ERROR(
                'Miniature Market retailer not found -- run populate_products first.'
            ))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for (slug, listing_title, price, url, in_stock) in MM_PRICES:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stdout.write(self.style.WARNING(
                    f'  Skipped (product not found): {slug}'
                ))
                skipped_count += 1
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm,
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': False,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
            )
            status = 'Created' if created else 'Updated'
            stock_label = 'In Stock' if in_stock else 'Out of Stock'
            self.stdout.write(
                self.style.SUCCESS(
                    f'  {status}: {product.name} -- ${price:.2f} ({stock_label})'
                )
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created={created_count}, Updated={updated_count}, '
            f'Skipped={skipped_count}'
        ))
