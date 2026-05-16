"""
Management command: seed_nk_as_prices

Seeds Noble Knight prices for Adepta Sororitas products.

Source: Adepta Soritas - GW, NK, MM, AMAZON.xlsx (2026-05-15)

NK MATCHES (28 products with NK URLs):
  AS-001, AS-003, AS-005 to AS-030

NO NK LISTING (2 products):
  AS-002 (Celestian Insidiants), AS-004 (Codex)

Affiliate tag ?awid=1576 appended to all URLs.
Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK_BASE = 'https://www.nobleknight.com'

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    (
        'armageddon-battalion-adepta-sororitas',
        'Armageddon Battalion - Adepta Sororitas',
        None,
        f'{_NK_BASE}/P/2148457415/Armageddon-Battalion---Adepta-Sororitas?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-intranzia-fraye-dogmata-superior',
        'Intranzia Fraye - Dogmata Superior',
        None,
        f'{_NK_BASE}/P/2148457451/Intranzia-Fraye--Dogmata-Superior?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-kill-team-sanctifiers',
        'Sanctifiers',
        None,
        f'{_NK_BASE}/P/2148317259/Sanctifiers?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-aestred-thurga-reliquant-at-arms',
        'Aestred Thurga - Reliquant at Arms',
        None,
        f'{_NK_BASE}/P/2147915834/Aestred-Thurga----Reliquant-at-Arms?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-castigator',
        'Castigator',
        None,
        f'{_NK_BASE}/P/2147915829/Castigator?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-paragon-warsuits',
        'Paragon Warsuits',
        None,
        f'{_NK_BASE}/P/2147892304/Paragon-Warsuits?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-palatine',
        'Palatine',
        None,
        f'{_NK_BASE}/P/2147892307/Palatine?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-daemonifuge-ephrael-stern-kyganil',
        'Daemonifuge - Ephrael Stern and Kyganil',
        None,
        f'{_NK_BASE}/P/2147810150/Daemonifuge---Ephrael-Stern-and-Kyganil?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Zephyrim Squad / Seraphim Squad share the same NK listing
    (
        'adepta-sororitas-zephyrim-squad',
        'Seraphim Squad',
        None,
        f'{_NK_BASE}/P/2147936765/Seraphim-Squad?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-rhino',
        'Adepta Sororitas Rhino',
        None,
        f'{_NK_BASE}/P/2147797670/Adeptas-Soroitas-Rhino?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-repentia-squad',
        'Repentia Squad 2021 Edition',
        None,
        f'{_NK_BASE}/P/2147797665/Repentia-Squad-2021-Edition?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-canoness',
        'Canoness 2021 Edition',
        None,
        f'{_NK_BASE}/P/2147936453/Canoness-2021-Edition?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-dialogus',
        'Dialogus',
        None,
        f'{_NK_BASE}/P/2147974196/Dialogus?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-imagifier',
        'Imagifier',
        None,
        f'{_NK_BASE}/P/2148061182/Imagifier?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-arco-flagellants',
        'Arco-Flagellants',
        None,
        f'{_NK_BASE}/P/2148090336/Arco-Flagellants?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-junith-eruita',
        'Junith Eruita',
        None,
        f'{_NK_BASE}/P/2147974197/Junith-Eruita?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-hospitaller',
        'Hospitaller',
        None,
        f'{_NK_BASE}/P/2147790573/Hospitaller?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-the-triumph-of-saint-katherine',
        'Triumph of St. Katherine The 2020 Edition',
        None,
        f'{_NK_BASE}/P/2147790558/Triumph-of-St-Katherine-The-2020-Edition?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-celestine-the-living-saint',
        'Celestine - The Living Saint',
        None,
        f'{_NK_BASE}/P/2148176668/Celestine---The-Living-Saint?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Dominion Squad / Battle Sisters Squad share the same NK listing
    (
        'adepta-sororitas-dominion-squad',
        'Battle Sisters Squad',
        None,
        f'{_NK_BASE}/P/2147790556/Battle-Sisters-Squad?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-sisters-novitiate-squad',
        'Novitiates',
        None,
        f'{_NK_BASE}/P/2148239664/Novitiates?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-canoness-with-jump-pack',
        'Canoness w/ Jump Pack',
        None,
        f'{_NK_BASE}/P/2148203604/Canoness-w-Jump-Pack?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-ministorum-priest',
        'Ministorum Priest',
        None,
        f'{_NK_BASE}/P/2148183382/Ministorum-Priest?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-ministorum-priest-with-vindictor',
        'Ministorum Priest w/ Vindictor',
        None,
        f'{_NK_BASE}/P/2148164280/Ministorum-Priest-w-Vindictor?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-sister-dogmata',
        'Sister Dogmata',
        None,
        f'{_NK_BASE}/P/2147892308/Sister-Dogmata?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Mortifiers / Penitent Engines share the same NK listing
    (
        'adepta-sororitas-mortifiers',
        'Penitent Engines / Engines of Redemption',
        None,
        f'{_NK_BASE}/P/2147924548/Penitent-Engines-Engines-of-Redemption?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-penitent-engines',
        'Penitent Engines / Engines of Redemption',
        None,
        f'{_NK_BASE}/P/2147924548/Penitent-Engines-Engines-of-Redemption?awid=1576',
        False,
        False,
    ),
    (
        'adepta-sororitas-sister-superior-amalia-novena',
        'Sister Superior Amalia Novena',
        None,
        f'{_NK_BASE}/P/2147756018/Sister-Superior-Amalia-Novena?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Adepta Sororitas products."""

    help = 'Seeds Noble Knight listing URLs and prices for Adepta Sororitas. Idempotent.'

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
