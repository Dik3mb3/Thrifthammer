"""
Management command: seed_nk_flesh_eater_courts_prices

Seeds Noble Knight CurrentPrice records for Flesh-Eater Courts products
(FEC-001 to FEC-021) from the AOS Flesh Eater Courts - GW, NK, MM.xlsx (2026-06-10).

Only products with confirmed NK URLs are included (20 of 21).
FEC-006 (High Falconer Felgryn) has no NK listing — no record created.

Triple-kit products sharing one NK listing:
  - FEC-002 / FEC-003 / FEC-014 share /P/2147625874/Terrorgheist
  - FEC-004 / FEC-005 / FEC-015 share /P/2147625867/Crypt-Flayers

Affiliate tag ?awid=1576 appended to all NK URLs.
Uses create_defaults for price and in_stock so scraper-set values survive
Railway redeploys.

Usage:
    python manage.py seed_nk_flesh_eater_courts_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
# price=None  → scraper will populate on first run
# in_stock    → initial assumption; scraper corrects as needed
NK_PRICES = [

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'abhorrant-archregent',
        'Abhorrant Archregent',
        None,
        f'{_NK}/P/2147794801/Abhorrant-Archregent{_AFF}',
        True,
        False,
    ),
    # ⚠ Triple kit: FEC-002 / FEC-003 / FEC-014 share NK listing
    (
        'abhorrant-ghoul-king-on-royal-zombie-dragon',
        'Terrorgheist',
        None,
        f'{_NK}/P/2147625874/Terrorgheist{_AFF}',
        True,
        False,
    ),
    # ⚠ Triple kit: FEC-003 / FEC-002 / FEC-014 share NK listing
    (
        'abhorrant-ghoul-king-on-royal-terrorgheist',
        'Terrorgheist',
        None,
        f'{_NK}/P/2147625874/Terrorgheist{_AFF}',
        True,
        False,
    ),
    # ⚠ Triple kit: FEC-004 / FEC-005 / FEC-015 share NK listing
    (
        'crypt-infernal-courtier',
        'Crypt Flayers',
        None,
        f'{_NK}/P/2147625867/Crypt-Flayers{_AFF}',
        True,
        False,
    ),
    # ⚠ Triple kit: FEC-005 / FEC-004 / FEC-015 share NK listing
    (
        'crypt-haunter-courtier',
        'Crypt Flayers',
        None,
        f'{_NK}/P/2147625867/Crypt-Flayers{_AFF}',
        True,
        False,
    ),
    # FEC-006 High Falconer Felgryn — no NK listing, no record created
    (
        'marrowscroll-herald',
        'Marrowscroll Herald Webstore Edition',
        None,
        f'{_NK}/P/2148217638/Marrowscroll-Herald-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'abhorrant-gorewarden',
        'Abhorrant Gore Warden Webstore Edition',
        None,
        f'{_NK}/P/2148217560/Abhorrant-Gore-Warden-Webstore-Edition{_AFF}',
        True,
        False,
    ),
    (
        'abhorrant-cardinal',
        'Abhorrant Cardinal',
        None,
        f'{_NK}/P/2148115342/Abhorrant-Cardinal{_AFF}',
        True,
        False,
    ),
    (
        'grand-justice-gormayne',
        'Grand Justice Gormayne',
        None,
        f'{_NK}/P/2148115340/Grand-Justice-Gormayne{_AFF}',
        True,
        False,
    ),
    (
        'royal-decapitator',
        'Royal Decapitator',
        None,
        f'{_NK}/P/2148115343/Royal-Decapitator{_AFF}',
        True,
        False,
    ),
    (
        'ushoran-mortarch-of-delusion',
        'Ushoran Mortarch of Delusion',
        None,
        f'{_NK}/P/2148115322/Ushoran-Mortarch-of-Delusion{_AFF}',
        True,
        False,
    ),
    (
        'varghulf-courtier',
        'Varghulf Courtier',
        None,
        f'{_NK}/P/2148330994/Varghulf-Courtier{_AFF}',
        True,
        False,
    ),
    # ⚠ Triple kit: FEC-014 / FEC-002 / FEC-003 share NK listing
    (
        'royal-zombie-dragon',
        'Terrorgheist',
        None,
        f'{_NK}/P/2147625874/Terrorgheist{_AFF}',
        True,
        False,
    ),

    # ── Units ─────────────────────────────────────────────────────────────────
    # ⚠ Triple kit: FEC-015 / FEC-004 / FEC-005 share NK listing
    (
        'crypt-flayers',
        'Crypt Flayers',
        None,
        f'{_NK}/P/2147625867/Crypt-Flayers{_AFF}',
        True,
        False,
    ),
    (
        'morbheg-knights',
        'Morbheg Knights',
        None,
        f'{_NK}/P/2148115335/Morbheg-Knights{_AFF}',
        True,
        False,
    ),
    (
        'cryptguard',
        'Cryptguard',
        None,
        f'{_NK}/P/2148115337/Cryptguard{_AFF}',
        True,
        False,
    ),
    (
        'royal-beastflayers',
        'Warcry Royal Beastflayers',
        None,
        f'{_NK}/P/2148070753/Warcry---Royal-Beastflayers{_AFF}',
        True,
        False,
    ),

    # ── Terrain / Scenery ─────────────────────────────────────────────────────
    (
        'charnel-throne',
        'Charnel Throne',
        None,
        f'{_NK}/P/2147745002/Charnel-Throne{_AFF}',
        True,
        False,
    ),

    # ── Spells / Endless ──────────────────────────────────────────────────────
    (
        'endless-spells-flesh-eater-courts',
        'Flesh-Eater Courts Endless Spells',
        None,
        f'{_NK}/P/2147745006/Flesh-Eater-Courts---Endless-Spells{_AFF}',
        True,
        False,
    ),

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'death-battletome-flesh-eater-courts',
        'Death Battletome: Flesh-Eater Courts 2024 Edition',
        None,
        f'{_NK}/P/2148115333/Death-Battletome---Flesh-Eater-Courts-2024-Edition{_AFF}',
        True,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Flesh-Eater Courts (20 products)."""

    help = 'Seeds NK CurrentPrice records for FEC-001 to FEC-021 (20 products with NK URLs).'

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
                    f'  Product not found: {slug} — skipping'
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
            f'seed_nk_flesh_eater_courts_prices complete. '
            f'NK prices: {created_count} created, {updated_count} updated.'
        ))
