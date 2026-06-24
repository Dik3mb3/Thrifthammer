"""
Management command: seed_mm_helsmiths_of_hashut_prices

Seeds Miniature Market CurrentPrice records for Helsmiths of Hashut products
(HOH-001 to HOH-011) from the AOS Helmishs of Hashut - GW, NK, MM.xlsx (2026-06-24).

All 11 products have confirmed MM URLs.

Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_mm_helsmiths_of_hashut_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_MM = 'https://www.miniaturemarket.com'

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    (
        'spearhead-helforge-host',
        'Spearhead: Helsmiths of Hashut – Helforge Host',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Spearhead-Helsmiths-of-Hashut-Helforge-Host/GW-70-821-2026',
        True,
        False,
    ),
    (
        'urak-taar-the-first-daemonsmith',
        'Urak Taar the First Daemonsmith',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-Urak-Taar-the-First-Daemonsmith/GW-82-05',
        True,
        False,
    ),
    (
        'war-despot',
        'War Despot',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-War-Despot/GW-82-08',
        True,
        False,
    ),
    (
        'daemonsmith',
        'Daemonsmith',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-Daemonsmith/GW-82-04',
        True,
        False,
    ),
    (
        'infernal-cohort',
        'Infernal Cohort',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-Infernal-Cohort/GW-82-12',
        True,
        False,
    ),
    (
        'infernal-razers',
        'Infernal Razers',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-Infernal-Razers/GW-82-02',
        True,
        False,
    ),
    (
        'hobgrot-vandalz',
        'Hobgrot Vandalz',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-Hobgrot-Vandalz/GW-82-09',
        True,
        False,
    ),
    (
        'bull-centaurs',
        'Bull Centaurs',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-Bull-Centaurs/GW-82-03',
        True,
        False,
    ),
    (
        'deathshrieker-rocket-battery',
        'Deathshrieker Rocket Battery',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-Deathshrieker-Rocket-Battery/GW-82-07',
        True,
        False,
    ),
    (
        'dominator-engine',
        'Dominator Engine',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Helsmiths-of-Hashut-Dominator-Engine/GW-82-06',
        True,
        False,
    ),
    (
        'chaos-battletome-helsmiths-of-hashut',
        'Chaos Battletome: Helsmiths of Hashut',
        None,
        f'{_MM}/Warhammer-Age-of-Sigmar-Chaos-Battletome-Helsmiths-of-Hashut/GW-82-01',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Helsmiths of Hashut (all 11 products have MM URLs)."""

    help = 'Seeds MM CurrentPrice records for HOH-001 to HOH-011 (11 products).'

    def handle(self, *args, **options):
        """Run the command."""
        mm = Retailer.objects.filter(name='Miniature Market').first()
        if not mm:
            self.stderr.write(self.style.ERROR('Miniature Market retailer not found.'))
            return

        created_count = 0
        updated_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stderr.write(self.style.WARNING(
                    f'  Product not found: {slug} -- skipping'
                ))
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
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_helsmiths_of_hashut_prices complete. '
            f'MM prices: {created_count} created, {updated_count} updated.'
        ))
