"""
Management command: seed_nk_ossiarch_bonereapers_prices

Seeds Noble Knight CurrentPrice records for Ossiarch Bonereapers products
(OBR-001 to OBR-020) from the AOS Bonereapers - GW, NK, MM.xlsx (2026-06-10).

All 20 products have confirmed NK URLs.

Nagash, Supreme Lord of the Undead (SG-016) is a dual-tag product handled
separately -- no NK record is created here for that SKU.

Note on the Mortarchs kit (OBR-011):
  - Arkhan the Black shares the physical Deathlords Mortarchs box with
    Mannfred and Neferata; the NK listing covers all three builds.

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_ossiarch_bonereapers_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  -> scraper will populate on first run
# in_stock    -> initial assumption; scraper corrects as needed
NK_PRICES = [

    # -- Battleforces ----------------------------------------------------------
    (
        'battleforce-ossiarch-bonereapers-null-myriad-phalanx',
        'Null Myriad Phalanx',
        None,
        f'{_NK}/P/2148454218/Null-Myriad-Phalanx{_AFF}',
        True,
        False,
    ),

    # -- Regiments of Renown ---------------------------------------------------
    (
        'regiment-of-renown-heralds-of-the-bone-tithe',
        'Regiment of Renown: Heralds of the Bone-Tithe',
        None,
        f'{_NK}/P/2148418735/Regiment-of-Renown---Heralds-of-the-Bone-Tithe{_AFF}',
        True,
        False,
    ),

    # -- Heroes ----------------------------------------------------------------
    (
        'mortisan-ossifector',
        'Mortisan Ossifector',
        None,
        f'{_NK}/P/2148047465/Mortisan-Ossifector{_AFF}',
        True,
        False,
    ),
    (
        'mortisan-soulmason',
        'Mortisan Soulmason',
        None,
        f'{_NK}/P/2148084218/Mortisan-Soulmason{_AFF}',
        True,
        False,
    ),
    (
        'katakros-mortarch-of-the-necropolis',
        'Katakros, Mortarch of the Necropolis',
        None,
        f'{_NK}/P/2147773192/Katakros-Mortarch-of-the-Necropolis{_AFF}',
        True,
        False,
    ),
    (
        'arch-kavalos-zandtos',
        'Arch-Kavalos Zandtos',
        None,
        f'{_NK}/P/2148089357/Arch-Kavalos-Zandtos{_AFF}',
        True,
        False,
    ),
    # ⚠ Mortarchs kit: Arkhan the Black / Mannfred von Carstein / Neferata
    #   share one NK listing (Deathlords Mortarch); only Arkhan is in this batch.
    (
        'arkhan-the-black-mortarch-of-sacrament',
        'Deathlords Mortarch',
        None,
        f'{_NK}/P/2147612293/Deathlords-Mortarch{_AFF}',
        True,
        False,
    ),
    (
        'mortisan-soulreaper',
        'Mortisan Soulreaper',
        None,
        f'{_NK}/P/2147773146/Mortisan-Soulreaper{_AFF}',
        True,
        False,
    ),
    (
        'liege-mortek',
        'Liege-Mortek',
        None,
        f'{_NK}/P/2148418739/Liege-Mortek{_AFF}',
        True,
        False,
    ),
    (
        'liege-kavalos-on-war-chariot',
        'Liege-Kavalos on War Chariot',
        None,
        f'{_NK}/P/2148418720/Liege-Kavalos-on-War-Chariot{_AFF}',
        True,
        False,
    ),
    (
        'mortisan-boneshaper',
        'Mortisan Boneshaper',
        None,
        f'{_NK}/P/2148050309/Mortisan-Boneshaper{_AFF}',
        True,
        False,
    ),

    # -- Units -----------------------------------------------------------------
    (
        'kavalos-deathriders',
        'Kavalos Deathriders 2024 Edition',
        None,
        f'{_NK}/P/2148115357/Kavalos-Deathriders-2024-Edition{_AFF}',
        True,
        False,
    ),
    (
        'morghast-harbingers',
        'Morghasts 2017 Edition',
        None,
        f'{_NK}/P/2147963903/Morghasts-2017-Edition{_AFF}',
        True,
        False,
    ),
    (
        'morghast-archai',
        'Morghast Archai',
        None,
        f'{_NK}/P/2147557099/Morghast-Archai{_AFF}',
        True,
        False,
    ),
    (
        'mortek-triaxes',
        'Mortek Triaxes',
        None,
        f'{_NK}/P/2148418713/Mortek-Triaxes{_AFF}',
        True,
        False,
    ),
    (
        'mortek-crawler',
        'Mortek Crawler',
        None,
        f'{_NK}/P/2147773191/Mortek-Crawler{_AFF}',
        True,
        False,
    ),

    # -- Warcry ----------------------------------------------------------------
    (
        'warcry-teratic-cohort',
        'Teratic Cohort',
        None,
        f'{_NK}/P/2148200870/Teratic-Cohort{_AFF}',
        True,
        False,
    ),

    # -- Terrain / Scenery -----------------------------------------------------
    (
        'bone-tithe-nexus',
        'Bone-Tithe Nexus',
        None,
        f'{_NK}/P/2147771420/Bone-Tithe-Nexus{_AFF}',
        True,
        False,
    ),

    # -- Spells / Endless ------------------------------------------------------
    (
        'endless-spells-ossiarch-bonereapers',
        'Endless Spells: Ossiarch Bonereapers',
        None,
        f'{_NK}/P/2147771419/Endless-Spells---Ossiarch-Bonereapers{_AFF}',
        True,
        False,
    ),

    # -- Battletome ------------------------------------------------------------
    (
        'death-battletome-ossiarch-bonereapers',
        'Death Battletome: Ossiarch Bonereapers',
        None,
        f'{_NK}/P/2148418747/Death-Battletome---Ossiarch-Bonereapers{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Ossiarch Bonereapers (20 products)."""

    help = 'Seeds NK CurrentPrice records for OBR-001 to OBR-020 (all 20 products have NK URLs).'

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
            f'seed_nk_ossiarch_bonereapers_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
