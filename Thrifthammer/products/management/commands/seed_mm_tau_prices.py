"""
Management command: seed_mm_tau_prices

Seeds Miniature Market prices for T'au Empire products.

Source: Tau - GW, NK, MM, Amazon.xlsx (2026-05-13)

MM MATCHES (25 products with MM URLs):
  TE-001 to TE-010, TE-015, TE-016, TE-018, TE-020 to TE-029, TE-036, TE-037

NO MM LISTING (12 products):
  TE-011, TE-012, TE-013, TE-014, TE-017, TE-019, TE-030, TE-031,
  TE-032, TE-033, TE-034, TE-035

Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com/'

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    (
        'tau-empire-tidewall-shieldline',
        '',
        None,
        f'{_MM}gw-56-51.html',
        False,
        False,
    ),
    (
        'tau-empire-kroot-hounds',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-kroot-hounds-gw-56-58.html',
        False,
        False,
    ),
    (
        'tau-empire-the-twin-lance',
        '',
        None,
        f'{_MM}Warhammer-40K-T-au-Empire-The-Twin-Lance/GW-56-69-2026',
        False,
        False,
    ),
    (
        'tau-empire-commander-farsight',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-commander-farsight-gw-56-41.html',
        False,
        False,
    ),
    (
        'tau-empire-darkstrider',
        '',
        None,
        f'{_MM}gw-56-32.html',
        False,
        False,
    ),
    (
        'tau-empire-commander-shadowsun',
        '',
        None,
        f'{_MM}gw-56-29.html',
        False,
        False,
    ),
    # ⚠ Dual kit: Breacher Team / Strike Team share the same MM listing
    (
        'tau-empire-fire-warriors-breacher-team',
        '',
        None,
        f'{_MM}gw-56-06.html',
        False,
        False,
    ),
    (
        'tau-empire-fire-warriors-strike-team',
        '',
        None,
        f'{_MM}gw-56-06.html',
        False,
        False,
    ),
    (
        'tau-empire-commander',
        '',
        None,
        f'{_MM}gw-56-22.html',
        False,
        False,
    ),
    (
        'tau-empire-cadre-fireblade',
        '',
        None,
        f'{_MM}gw-56-16.html',
        False,
        False,
    ),
    (
        'tau-empire-ghostkeel-battlesuit',
        '',
        None,
        f'{_MM}gw-56-20.html',
        False,
        False,
    ),
    (
        'tau-empire-stormsurge',
        '',
        None,
        f'{_MM}gw-56-18.html',
        False,
        False,
    ),
    # ⚠ Dual kit: Sky Ray / Hammerhead share the same MM listing (Hammerhead = 56-10)
    (
        'tau-empire-sky-ray-gunship',
        '',
        None,
        f'{_MM}gw-56-11.html',
        False,
        False,
    ),
    (
        'tau-empire-devilfish',
        '',
        None,
        f'{_MM}gw-56-10.html',
        False,
        False,
    ),
    (
        'tau-empire-farstalker-kinband',
        '',
        None,
        f'{_MM}kill-team-farstalker-kinband-gw-103-08-2024.html',
        False,
        False,
    ),
    (
        'tau-empire-vespid-stingwings',
        '',
        None,
        f'{_MM}kill-team-vespid-stingwings-gw-103-51.html',
        False,
        False,
    ),
    (
        'tau-empire-kroot-lone-spear',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-kroot-lone-spear-gw-56-59.html',
        False,
        False,
    ),
    (
        'tau-empire-kroot-trail-shaper',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-kroot-trail-shaper-gw-56-57.html',
        False,
        False,
    ),
    (
        'tau-empire-kroot-flesh-shaper',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-kroot-flesh-shaper-gw-56-56.html',
        False,
        False,
    ),
    (
        'tau-empire-kroot-war-shaper',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-kroot-war-shaper-gw-56-55.html',
        False,
        False,
    ),
    (
        'tau-empire-krootox-rider',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-krootox-rider-gw-56-54.html',
        False,
        False,
    ),
    (
        'tau-empire-krootox-rampagers',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-krootox-rampagers-gw-56-49.html',
        False,
        False,
    ),
    (
        'codex-tau-empire',
        '',
        None,
        f'{_MM}warhammer-40k-codex-tau-empire-10th-edition-gw-56-01-2024.html',
        False,
        False,
    ),
    (
        'tau-empire-piranha',
        '',
        None,
        f'{_MM}gw-56-19.html',
        False,
        False,
    ),
    (
        'tau-empire-kroot-carnivores',
        '',
        None,
        f'{_MM}warhammer-40k-tau-empire-kroot-carnivores-gw-56-48.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for T'au Empire products."""

    help = "Seeds Miniature Market listing URLs and prices for T'au Empire. Idempotent."

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stdout.write(self.style.ERROR('Miniature Market retailer not found'))
            return

        seeded = 0
        missing = 0

        for slug, listing_title, price, url, in_stock, not_available in MM_PRICES:
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
                    'listing_title': listing_title,
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
