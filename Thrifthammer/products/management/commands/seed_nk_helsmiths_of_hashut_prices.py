"""
Management command: seed_nk_helsmiths_of_hashut_prices

Seeds Noble Knight CurrentPrice records for Helsmiths of Hashut products
(HOH-001 to HOH-011) from the AOS Helmishs of Hashut - GW, NK, MM.xlsx (2026-06-24).

All 11 products have confirmed NK URLs.

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_helsmiths_of_hashut_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    (
        'spearhead-helforge-host',
        'Spearhead - Helforge Host',
        None,
        f'{_NK}/P/2148395196/Spearhead---Helforge-Host{_AFF}',
        True,
        False,
    ),
    (
        'urak-taar-the-first-daemonsmith',
        'Urak Taar - The First Daemonsmith',
        None,
        f'{_NK}/P/2148362606/Urak-Taar---The-First-Daemonsmith{_AFF}',
        True,
        False,
    ),
    (
        'war-despot',
        'War Despot',
        None,
        f'{_NK}/P/2148362608/War-Despot{_AFF}',
        True,
        False,
    ),
    (
        'daemonsmith',
        'Daemonsmith Ashen Elder',
        None,
        f'{_NK}/P/2148362599/Daemonsmith-Ashen-Elder{_AFF}',
        True,
        False,
    ),
    (
        'infernal-cohort',
        'Infernal Cohort',
        None,
        f'{_NK}/P/2148362591/Infernal-Cohort{_AFF}',
        True,
        False,
    ),
    (
        'infernal-razers',
        'Infernal Razers',
        None,
        f'{_NK}/P/2148362573/Infernal-Razers{_AFF}',
        True,
        False,
    ),
    (
        'hobgrot-vandalz',
        'Hobgrot Vandalz',
        None,
        f'{_NK}/P/2148362579/Hobgrot-Vandalz{_AFF}',
        True,
        False,
    ),
    (
        'bull-centaurs',
        'Bull Centaurs',
        None,
        f'{_NK}/P/2148362585/Bull-Centaurs{_AFF}',
        True,
        False,
    ),
    (
        'deathshrieker-rocket-battery',
        'Deathstriker Rocket Battery',
        None,
        f'{_NK}/P/2148362586/Deathstriker-Rocket-Battery{_AFF}',
        True,
        False,
    ),
    (
        'dominator-engine',
        'Dominator Engine',
        None,
        f'{_NK}/P/2148362575/Dominator-Engine{_AFF}',
        True,
        False,
    ),
    (
        'chaos-battletome-helsmiths-of-hashut',
        'Chaos Battletome - Helsmiths of Hashut',
        None,
        f'{_NK}/P/2148362607/Chaos-Battletome---Helsmiths-of-Hashut{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Helsmiths of Hashut (all 11 products have NK URLs)."""

    help = 'Seeds NK CurrentPrice records for HOH-001 to HOH-011 (11 products).'

    def handle(self, *args, **options):
        """Run the command."""
        nk = Retailer.objects.filter(name='Noble Knight Games').first()
        if not nk:
            self.stderr.write(self.style.ERROR('Noble Knight Games retailer not found.'))
            return

        created_count = 0
        updated_count = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stderr.write(self.style.WARNING(
                    f'  Product not found: {slug} -- skipping'
                ))
                continue

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk,
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
            f'seed_nk_helsmiths_of_hashut_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
