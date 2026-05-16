"""
Management command: seed_mm_as_prices

Seeds Miniature Market prices for Adepta Sororitas products.

Source: Adepta Soritas - GW, NK, MM, AMAZON.xlsx (2026-05-15)

MM MATCHES (27 products with MM URLs):
  AS-002 to AS-029

NO MM LISTING (3 products):
  AS-001 (Armageddon Battalion), AS-003 (Intranzia Fraye), AS-030 (Amalia Novena)

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
        'adepta-sororitas-celestian-insidiants',
        'Adepta Sororitas Celestian Insidiants',
        None,
        'https://www.miniaturemarket.com/gw-52-35.html',
        False,
        False,
    ),
    (
        'codex-adepta-sororitas',
        'Codex: Adepta Sororitas',
        None,
        'https://www.miniaturemarket.com/warhammer-40k-codex-adepta-sororitas-10th-edition-gw-52-01-2024.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-kill-team-sanctifiers',
        'Kill Team: Sanctifiers',
        None,
        'https://www.miniaturemarket.com/kill-team-sanctifiers-gw-103-90.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-aestred-thurga-reliquant-at-arms',
        'Adepta Sororitas Aestred Thurga, Reliquant at Arms',
        None,
        'https://www.miniaturemarket.com/gw-52-36.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-castigator',
        'Adepta Sororitas Castigator',
        None,
        'https://www.miniaturemarket.com/gw-52-33.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-paragon-warsuits',
        'Adepta Sororitas Paragon Warsuits',
        None,
        'https://www.miniaturemarket.com/gw-52-34.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-palatine',
        'Adepta Sororitas Palatine',
        None,
        'https://www.miniaturemarket.com/gw-52-31.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-daemonifuge-ephrael-stern-kyganil',
        'Adepta Sororitas Daemonifuge - Ephrael Stern & Kyganil',
        None,
        'https://www.miniaturemarket.com/gw-40-50.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-zephyrim-squad',
        'Adepta Sororitas Zephyrim Squad',
        None,
        'https://www.miniaturemarket.com/gw-52-27.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-rhino',
        'Adepta Sororitas Rhino',
        None,
        'https://www.miniaturemarket.com/gw-52-26.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-repentia-squad',
        'Adepta Sororitas Repentia Squad',
        None,
        'https://www.miniaturemarket.com/gw-52-23.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-canoness',
        'Adepta Sororitas Canoness',
        None,
        'https://www.miniaturemarket.com/gw-52-21.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-dialogus',
        'Adepta Sororitas Dialogus',
        None,
        'https://www.miniaturemarket.com/gw-52-16.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-imagifier',
        'Adepta Sororitas Imagifier',
        None,
        'https://www.miniaturemarket.com/gw-52-15.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-arco-flagellants',
        'Adepta Sororitas Arco-flagellants',
        None,
        'https://www.miniaturemarket.com/gw-52-19.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-junith-eruita',
        'Adepta Sororitas Junith Eruita',
        None,
        'https://www.miniaturemarket.com/gw-52-17.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-hospitaller',
        'Adepta Sororitas Hospitaller',
        None,
        'https://www.miniaturemarket.com/gw-52-18.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-the-triumph-of-saint-katherine',
        'Adepta Sororitas The Triumph of Saint Katherine',
        None,
        'https://www.miniaturemarket.com/gw-52-24.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-celestine-the-living-saint',
        'Adepta Sororitas Celestine, the Living Saint',
        None,
        'https://www.miniaturemarket.com/gw-52-58.html',
        False,
        False,
    ),
    # ⚠ Dual kit: Dominion Squad / Battle Sisters Squad share the same MM listing
    (
        'adepta-sororitas-dominion-squad',
        'Adepta Sororitas Dominion Squad',
        None,
        'https://www.miniaturemarket.com/gw-52-20.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-sisters-novitiate-squad',
        'Adepta Sororitas Sisters Novitiate Squad',
        None,
        'https://www.miniaturemarket.com/warhammer-40k-adepta-sororitas-sisters-novitiate-squad-gw-52-64.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-canoness-with-jump-pack',
        'Adepta Sororitas Canoness with Jump Pack',
        None,
        'https://www.miniaturemarket.com/warhammer-40k-adepta-sororitas-canoness-w-jump-pack-gw-52-61.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-ministorum-priest',
        'Adepta Sororitas Ministorum Priest',
        None,
        'https://www.miniaturemarket.com/warhammer-40k-adepta-sororitas-ministorum-priest-gw-57-51.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-ministorum-priest-with-vindictor',
        'Adepta Sororitas Ministorum Priest with Vindictor',
        None,
        'https://www.miniaturemarket.com/warhammer-40k-adepta-sororitas-ministorum-priest-with-vindicator-gw-52-51.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-sister-dogmata',
        'Adepta Sororitas Sister Dogmata',
        None,
        'https://www.miniaturemarket.com/gw-52-32.html',
        False,
        False,
    ),
    # ⚠ Dual kit: Mortifiers / Penitent Engines share the same MM listing
    (
        'adepta-sororitas-mortifiers',
        'Adepta Sororitas Mortifiers',
        None,
        'https://www.miniaturemarket.com/gw-52-22.html',
        False,
        False,
    ),
    (
        'adepta-sororitas-penitent-engines',
        'Adepta Sororitas Penitent Engines',
        None,
        'https://www.miniaturemarket.com/gw-52-22.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Adepta Sororitas products."""

    help = 'Seeds Miniature Market listing URLs and prices for Adepta Sororitas. Idempotent.'

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
