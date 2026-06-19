"""
Management command: populate_sons_of_behemat_products

Creates / updates all Sons of Behemat product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Sons of Behemat
faction if it does not already exist.

Covers 6 products (SON-001 to SON-006) from the
AOS Sons of Behemat - GW, NK, MM.xlsx (2026-06-18).

Category: Age of Sigmar
Faction:  Sons of Behemat (new -- created here via get_or_create)

Dual-kit products (same physical box, multiple build options):
  - SON-001 Kraken-eater Mega-Gargant / SON-002 Warstomper Mega-Gargant /
    SON-003 King Brodd / SON-004 Gatebreaker Mega-Gargant /
    SON-005 Beast-smasher Mega-Gargant
    (all from the same Mega-Gargant / King Brodd box -- same NK and MM listing)

Shared product (do NOT create here):
  - GG-009 Kragnos, the End of Empires (primary faction: Gloomspite Gitz)
    → secondary faction added by add_kragnos_secondary_factions command.

Images are baked in as one-off GW CDN URLs -- never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_sons_of_behemat_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# -- Product definitions -------------------------------------------------------
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-18.
# ebay_search_name is set directly -- single source of truth for eBay search.
#
# All five Mega-Gargant variants (SON-001 to SON-005) are built from the
# same King Brodd box. eBay search name "King Brodd Age of Sigmar" covers
# all five builds as sellers typically list the box generically.
PRODUCTS = [

    # ⚠ Dual kit: Kraken-eater, Warstomper, King Brodd, Gatebreaker, and
    #   Beast-smasher Mega-Gargants all come from the same physical box.
    #   NK listing and MM listing cover all five builds.
    (
        'kraken-eater-mega-gargant',
        'SON-001',
        'Kraken-eater Mega-Gargant',
        215.00,
        '99120299086_KrakenEaterLead.jpg',
        f'{_GW}kraken-eater-mega-gargant-2022',
        'King Brodd Age of Sigmar',
    ),
    (
        'warstomper-mega-gargant',
        'SON-002',
        'Warstomper Mega-Gargant',
        215.00,
        '99120299086_WarStomperLead.jpg',
        f'{_GW}warstomper-mega-gargant-2022',
        'King Brodd Age of Sigmar',
    ),
    (
        'king-brodd',
        'SON-003',
        'King Brodd',
        215.00,
        '99120299086_BroddLead.jpg',
        f'{_GW}sons-of-behemat-king-brodd-2022',
        'King Brodd Age of Sigmar',
    ),
    (
        'gatebreaker-mega-gargant',
        'SON-004',
        'Gatebreaker Mega-Gargant',
        215.00,
        '99120299086_GateSmasherLead.jpg',
        f'{_GW}gatebreaker-mega-gargant-2022',
        'King Brodd Age of Sigmar',
    ),
    (
        'beast-smasher-mega-gargant',
        'SON-005',
        'Beast-smasher Mega-Gargant',
        215.00,
        '99120299086_BeastSmasherLead.jpg',
        f'{_GW}beast-smasher-maga-gargant-2022',
        'King Brodd Age of Sigmar',
    ),

    # -- Units -----------------------------------------------------------------
    (
        'mancrusher-gargant',
        'SON-006',
        'Mancrusher Gargant',
        77.00,
        '99120299063_MancrusherGargantsSingle02.jpg',
        f'{_GW}sons-of-behemat-mancrusher-gargant-2022',
        'Mancrusher Gargant Age of Sigmar',
    ),
]


class Command(BaseCommand):
    """Populate Sons of Behemat products (SON-001 to SON-006)."""

    help = (
        'Creates / updates 6 Sons of Behemat products and seeds GW prices at MSRP. '
        'Creates Sons of Behemat faction if not present. Idempotent.'
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

        sob_faction, faction_created = Faction.objects.get_or_create(
            slug='sons-of-behemat',
            defaults={'name': 'Sons of Behemat', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Sons of Behemat faction.')

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
                    'faction': sob_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'sons-of-behemat',
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
            f'populate_sons_of_behemat_products complete. '
            f'Products: {products_created} created, {products_updated} updated. '
            f'GW prices: {prices_created} created, {prices_updated} updated.'
        ))
