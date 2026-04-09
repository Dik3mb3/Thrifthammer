"""
Management command: seed_aeldari_corsair_links

Adds retailer links for the 6 new 2026 Aeldari Corsair release products:
  - Corsair Skyreavers
  - Corsair Voidreavers
  - Prince Yriel
  - Kharseth
  - Vyper
  - Combat Patrol: Aeldari Corsairs

Retailers seeded:
  - Amazon          — clean /dp/ASIN URLs with ?tag=thrifthammer7-20 affiliate
  - Miniature Market — direct product page URLs
  - Noble Knight Games — product/search URLs with ?awid=1576 affiliate

Also updates batch_tag to 'phase-1' on all 6 products.

Prices are left as None — scrapers will populate actual prices.
Stock status defaults to not_available=False, in_stock=False until scrapers run.

Safe to run repeatedly (idempotent via update_or_create).

Usage:
    python manage.py seed_aeldari_corsair_links
    python manage.py seed_aeldari_corsair_links --dry-run
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer


# ---------------------------------------------------------------------------
# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> price unknown; scraper will populate
# in_stock=False, not_available=False -> listed but stock unconfirmed
# ---------------------------------------------------------------------------

AMAZON_TAG = 'thrifthammer7-20'
NK_AWID = '1576'

AMAZON_LINKS = [
    (
        'aeldari-corsair-skyreavers',
        'Games Workshop Warhammer 40K Aeldari Corsair Skyreavers',
        None,
        f'https://www.amazon.com/dp/B0GQVFMVP9?tag={AMAZON_TAG}',
        False, False,
    ),
    (
        'aeldari-corsair-voidreavers',
        'Games Workshop Warhammer 40K Aeldari Corsair Voidreavers',
        None,
        f'https://www.amazon.com/dp/B0GQVJ47WM?tag={AMAZON_TAG}',
        False, False,
    ),
    (
        'aeldari-prince-yriel',
        'Games Workshop Warhammer 40K Aeldari Prince Yriel',
        None,
        f'https://www.amazon.com/dp/B0GQVBRTVG?tag={AMAZON_TAG}',
        False, False,
    ),
    (
        'aeldari-kharseth',
        'Games Workshop Warhammer 40K Aeldari Kharseth',
        None,
        f'https://www.amazon.com/dp/B0GQVTVXSD?tag={AMAZON_TAG}',
        False, False,
    ),
    (
        'aeldari-vyper',
        'Games Workshop Warhammer 40K Aeldari Vyper',
        None,
        f'https://www.amazon.com/dp/B0GQVQPS9G?tag={AMAZON_TAG}',
        False, False,
    ),
    (
        'combat-patrol-aeldari-corsairs',
        'Games Workshop Warhammer 40K Combat Patrol Aeldari Corsairs',
        None,
        f'https://www.amazon.com/dp/B0GQVG5S6K?tag={AMAZON_TAG}',
        False, False,
    ),
]

MM_LINKS = [
    (
        'aeldari-corsair-skyreavers',
        'Warhammer 40K: Aeldari Corsair Skyreavers',
        None,
        'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Corsair-Skyreavers-New-Arrival/GW-46-80-2026',
        False, False,
    ),
    (
        'aeldari-corsair-voidreavers',
        'Warhammer 40K: Aeldari Corsair Voidreavers',
        None,
        'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Corsair-Voidreavers-New-Arrival/GW-46-84-2026',
        False, False,
    ),
    (
        'aeldari-prince-yriel',
        'Warhammer 40K: Aeldari Prince Yriel',
        None,
        'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Prince-Yriel-New-Arrival/GW-46-82-2026',
        False, False,
    ),
    (
        'aeldari-kharseth',
        'Warhammer 40K: Aeldari Kharseth',
        None,
        'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Kharseth-New-Arrival/GW-46-81-2026',
        False, False,
    ),
    (
        'aeldari-vyper',
        'Warhammer 40K: Aeldari Vyper',
        None,
        'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Vyper-New-Arrival/GW-46-83-2026',
        False, False,
    ),
    (
        'combat-patrol-aeldari-corsairs',
        'Warhammer 40K: Combat Patrol - Aeldari Corsairs',
        None,
        'https://www.miniaturemarket.com/Warhammer-40K-Combat-Patrol-Aeldari-Corsairs-New-Arrival/GW-73-463-2026',
        False, False,
    ),
]

NK_LINKS = [
    (
        'aeldari-corsair-skyreavers',
        'Corsair Skyreavers',
        None,
        f'https://www.nobleknight.com/P/2148424027/Corsair-Skyreavers?awid={NK_AWID}',
        False, False,
    ),
    (
        'aeldari-corsair-voidreavers',
        'Corsair Voidreavers',
        None,
        f'https://www.nobleknight.com/P/2148424024/Corsair-Voidreavers?awid={NK_AWID}',
        False, False,
    ),
    (
        'aeldari-prince-yriel',
        'Prince Yriel',
        None,
        f'https://www.nobleknight.com/P/2148424076/Prince-Yriel?awid={NK_AWID}',
        False, False,
    ),
    (
        'aeldari-kharseth',
        'Kharseth',
        None,
        f'https://www.nobleknight.com/P/2148424077/Kharseth?awid={NK_AWID}',
        False, False,
    ),
    (
        'aeldari-vyper',
        'Vyper',
        None,
        f'https://www.nobleknight.com/P/2148424056/Vyper?awid={NK_AWID}',
        False, False,
    ),
    (
        'combat-patrol-aeldari-corsairs',
        'Combat Patrol - Aeldari Corsairs',
        None,
        f'https://www.nobleknight.com/P/2148424016/Combat-Patrol---Aeldari-Corsairs?awid={NK_AWID}',
        False, False,
    ),
]

PHASE_1_SLUGS = [
    'aeldari-corsair-skyreavers',
    'aeldari-corsair-voidreavers',
    'aeldari-prince-yriel',
    'aeldari-kharseth',
    'aeldari-vyper',
    'combat-patrol-aeldari-corsairs',
]


def _seed_retailer(command, retailer_name, data, dry_run):
    """Seed CurrentPrice entries for one retailer."""
    retailer = Retailer.objects.filter(name=retailer_name).first()
    if not retailer:
        command.stderr.write(f'  MISSING retailer: {retailer_name}')
        return 0, 0

    created_count = updated_count = 0
    for slug, listing_title, price, url, in_stock, not_available in data:
        product = Product.objects.filter(slug=slug, is_active=True).first()
        if not product:
            command.stderr.write(f'  MISSING Product not found: {slug}')
            continue

        if dry_run:
            command.stdout.write(f'  [DRY RUN] {slug} -> {url}')
            continue

        _, created = CurrentPrice.objects.update_or_create(
            product=product,
            retailer=retailer,
            defaults={
                'price': price,
                'url': url,
                'listing_title': listing_title,
                'in_stock': in_stock,
                'not_available': not_available,
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    return created_count, updated_count


class Command(BaseCommand):
    """Seed retailer links for 2026 Aeldari Corsair release products."""

    help = (
        'Seeds Amazon, Miniature Market, and Noble Knight links for the 6 new '
        '2026 Aeldari Corsair products, and tags them batch_tag=phase-1.'
    )

    def add_arguments(self, parser):
        """Add --dry-run flag."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print actions without writing to the database.',
        )

    def handle(self, *args, **options):
        """Execute the seed command."""
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write('=== DRY RUN — no database changes ===')

        retailers = [
            ('Amazon', AMAZON_LINKS),
            ('Miniature Market', MM_LINKS),
            ('Noble Knight Games', NK_LINKS),
        ]

        total_created = total_updated = 0
        for retailer_name, data in retailers:
            self.stdout.write(f'\n{retailer_name}:')
            created, updated = _seed_retailer(self, retailer_name, data, dry_run)
            self.stdout.write(f'  created={created}  updated={updated}')
            total_created += created
            total_updated += updated

        # ── Tag all 6 products as phase-1 ───────────────────────────────────
        self.stdout.write('\nTagging products batch_tag=phase-1:')
        for slug in PHASE_1_SLUGS:
            product = Product.objects.filter(slug=slug, is_active=True).first()
            if not product:
                self.stderr.write(f'  MISSING Product not found: {slug}')
                continue
            if dry_run:
                self.stdout.write(f'  [DRY RUN] {slug} -> batch_tag=phase-1')
            else:
                product.batch_tag = 'phase-1'
                product.save(update_fields=['batch_tag'])
                self.stdout.write(f'  OK {slug}')

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDone. CurrentPrice: {total_created} created, '
                    f'{total_updated} updated.'
                )
            )
