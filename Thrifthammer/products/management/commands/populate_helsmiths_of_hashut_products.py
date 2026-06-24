"""
Management command: populate_helsmiths_of_hashut_products

Creates / updates all Helsmiths of Hashut product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Helsmiths of Hashut
faction if it does not already exist.

Covers 11 products (HOH-001 to HOH-011) from the
AOS Helmishs of Hashut - GW, NK, MM.xlsx (2026-06-24).

Category: Age of Sigmar
Faction:  Helsmiths of Hashut (created here via get_or_create)

No dual-tag products -- all 11 are unique to this faction.
All 11 products have confirmed NK and MM URLs.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_helsmiths_of_hashut_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# -- Product definitions -------------------------------------------------------
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-24.
# ebay_search_name is set directly -- single source of truth for eBay search.
PRODUCTS = [

    # -- Spearhead -------------------------------------------------------------
    (
        'spearhead-helforge-host',
        'HOH-001',
        'Spearhead: Helsmiths of Hashut – Helforge Host',
        150.00,
        '99120211002_HelsmithsOfHashutHelforgeHostSpearhead01.jpg',
        f'{_GW}spearhead-hellsmiths-of-hashut-helforge-host-2026',
        'Spearhead: Helsmiths of Hashut – Helforge Host',
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'urak-taar-the-first-daemonsmith',
        'HOH-002',
        'Urak Taar the First Daemonsmith',
        165.00,
        '99120211011_HelsmithsofHashutUrakTaartheFirstDaemonsmith1.jpg',
        f'{_GW}helsmiths-of-hashut-urak-taar-the-first-daemonsmith-2025',
        'Urak Taar the First Daemonsmith Helsmiths of Hashut',
    ),
    (
        'war-despot',
        'HOH-008',
        'War Despot',
        38.00,
        '99120211010_HelsmithsofHashutWarDespot1.jpg',
        f'{_GW}helsmiths-of-hashut-war-despot-2025',
        'War Despot Helsmiths of Hashut',
    ),
    (
        'daemonsmith',
        'HOH-011',
        'Daemonsmith',
        40.00,
        '99120211005_HelsmithsofHashutDaemonsmith01.jpg',
        f'{_GW}helsmiths-of-hashut-daemonsmith-2025',
        'Daemonsmith Helsmiths of Hashut',
    ),

    # -- Units -----------------------------------------------------------------
    (
        'infernal-cohort',
        'HOH-006',
        'Infernal Cohort',
        55.50,
        '99120211003_HelsmithsofHashutInfernalCohort01.jpg',
        f'{_GW}helsmiths-of-hashut-infernal-cohort-2025',
        'Infernal Cohort Helsmiths of Hashut',
    ),
    (
        'infernal-razers',
        'HOH-007',
        'Infernal Razers',
        48.00,
        '99120211008_HelsmithsofHashutInfernalRazers1.jpg',
        f'{_GW}helsmiths-of-hashut-infernal-razers-2025',
        'Infernal Razers Helsmiths of Hashut',
    ),
    (
        'hobgrot-vandalz',
        'HOH-005',
        'Hobgrot Vandalz',
        65.00,
        '99120211009_HelsmithsofHashutHobgrotVandalz1.jpg',
        f'{_GW}helsmiths-of-hashut-hobgrot-vandalz-2025',
        'Hobgrot Vandalz Helsmiths of Hashut',
    ),
    (
        'bull-centaurs',
        'HOH-010',
        'Bull Centaurs',
        65.00,
        '99120211007_HelsmithsofHashutBullCentaurs01.jpg',
        f'{_GW}helsmiths-of-hashut-bull-centaurs-2025',
        'Bull Centaurs Helsmiths of Hashut',
    ),

    # -- War Machines ----------------------------------------------------------
    (
        'deathshrieker-rocket-battery',
        'HOH-003',
        'Deathshrieker Rocket Battery',
        60.00,
        '99120211006_HelsmithsofHashutDeathshriekerRocketBattery01.jpg',
        f'{_GW}helsmiths-of-hashut-deathshrieker-rocket-battery-2025',
        'Deathshrieker Rocket Battery Helsmiths of Hashut',
    ),
    (
        'dominator-engine',
        'HOH-004',
        'Dominator Engine',
        77.00,
        '99120211004_HelsmithsofHashutDominatorEngine01.jpg',
        f'{_GW}helsmiths-of-hashut-dominator-engine-2025',
        'Dominator Engine Helsmiths of Hashut',
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'chaos-battletome-helsmiths-of-hashut',
        'HOH-009',
        'Chaos Battletome: Helsmiths of Hashut',
        60.00,
        '60030211001_EngHelsmithsOfHashutBattletome01.jpg',
        f'{_GW}battletome-helsmiths-of-hashut-2025-eng',
        'Chaos Battletome: Helsmiths of Hashut',
    ),
]


class Command(BaseCommand):
    """Populate Helsmiths of Hashut products (HOH-001 to HOH-011)."""

    help = (
        'Creates / updates 11 Helsmiths of Hashut products and seeds GW prices at MSRP. '
        'Creates Helsmiths of Hashut faction if not present. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_aos = Category.objects.get(slug='age-of-sigmar')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Age of Sigmar category not found -- run populate_products first.'
            ))
            return

        hoh_faction, faction_created = Faction.objects.get_or_create(
            slug='helsmiths-of-hashut',
            defaults={'name': 'Helsmiths of Hashut', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Helsmiths of Hashut faction.')

        gw = Retailer.objects.filter(name='Games Workshop').first()

        products_created = 0
        products_updated = 0
        prices_created = 0
        prices_updated = 0

        for (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name) in PRODUCTS:
            image_url = _IMG.format(filename=image_filename)

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'faction': hoh_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'helsmiths-of-hashut',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
                self.stdout.write(f'  Created: {name} ({gw_sku})')
            else:
                products_updated += 1
                self.stdout.write(f'  Updated: {name} ({gw_sku})')

            if gw:
                _, price_created = CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=gw,
                    defaults={'price': msrp, 'url': gw_url, 'in_stock': True, 'not_available': False},
                )
                if price_created:
                    prices_created += 1
                else:
                    prices_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'populate_helsmiths_of_hashut_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
