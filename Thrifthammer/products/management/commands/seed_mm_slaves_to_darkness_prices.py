"""
Management command: seed_mm_slaves_to_darkness_prices

Seeds Miniature Market prices for Slaves to Darkness products (S2D-001 to S2D-035).

Source: AOS Slaves to Darkness - GW, NK, MM.xlsx (2026-06-03)

MM MATCHES (15 products):
  S2D-004, S2D-005, S2D-007, S2D-010, S2D-011, S2D-014,
  S2D-015, S2D-016, S2D-018, S2D-019, S2D-028,
  S2D-029, S2D-030, S2D-032, S2D-033
  (S2D-001/017/026 removed — use pre-existing 70-04/83-18/83-14)

NO MM LISTING (17 products):
  S2D-002  Warcry: Centaurion Marshal
  S2D-003  Chaos Lord on Daemonic Mount
  S2D-006  Chaos Lord on Karkadrak
  S2D-008  Darkoath Warqueen
  S2D-009  Gaunt Summoner
  S2D-012  Chaos Lord
  S2D-013  Centaurion Marshal
  S2D-020  Mindstealer Sphiranx
  S2D-021  Fomoroid Crusher
  S2D-022  Chaotic Beasts
  S2D-023  Gorebeast Chariot
  S2D-024  Endless Spells: Slaves to Darkness
  S2D-025  Chaos Chariot
  S2D-027  Slaughterbrute
  S2D-031  Chaos Battletome: Slaves to Darkness
  S2D-034  Chaos Legionnaires
  S2D-035  Darkoath Wilderfiend

Shared kit notes:
  S2D-007 / S2D-018  Ogroid Myrmidon / Ogroid Theridons share MM listing
  S2D-010 / S2D-032  Darkoath Chieftain / Darkoath Chieftain on Warsteed
                     share MM listing

Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'exalted-hero-of-chaos',
        'Exalted Hero of Chaos',
        None,
        'https://www.miniaturemarket.com/warhammer-age-of-sigmar-slaves-to-darkness-exalted-hero-of-chaos-gw-83-67.html',
        False,
        False,
    ),
    (
        'eternus-blade-of-the-first-prince',
        'Eternus, Blade of The First Prince',
        None,
        'https://www.miniaturemarket.com/warhammer-age-of-sigmar-slaves-to-darkness-eternus-blade-of-the-first-prince-gw-83-66.html',
        False,
        False,
    ),
    # ⚠ Shared kit (dual): Ogroid Myrmidon / Ogroid Theridons share MM listing
    (
        'ogroid-myrmidon',
        'Ogroid Myrmidon / Ogroid Theridons',
        None,
        'https://www.miniaturemarket.com/warhammer-age-of-sigmar-slaves-to-darkness-ogroid-theridons-gw-83-63.html',
        False,
        False,
    ),
    # ⚠ Shared kit (dual): Darkoath Chieftain / Darkoath Chieftain on Warsteed
    #   share MM listing
    (
        'darkoath-chieftain',
        'Darkoath Chieftain / Darkoath Chieftain on Warsteed',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-slaves-to-darkness-darkoath-chieftain-warsteed-gw-83-53-2024.html',
        False,
        False,
    ),
    (
        'archaon-everchosen',
        'Archaon Everchosen',
        None,
        'https://www.miniaturemarket.com/gw-83-50.html',
        False,
        False,
    ),
    (
        'chaos-sorcerer-lord',
        'Chaos Sorcerer Lord',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-slaves-to-darkness-chaos-sorcerer-lord-gw-83-100.html',
        False,
        False,
    ),
    (
        'abraxia-spear-of-the-everchosen',
        'Abraxia, Spear of the Everchosen',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-slaves-to-darkness-abraxia-spear-everchosen-gw-83-57.html',
        False,
        False,
    ),
    (
        'brands-oathbound',
        "Brand's Oathbound",
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-darkoath-brands-oathbound-gw-83-56-2024.html',
        False,
        False,
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    # ⚠ Shared kit (dual): see Ogroid Myrmidon note
    (
        'ogroid-theridons',
        'Ogroid Myrmidon / Ogroid Theridons',
        None,
        'https://www.miniaturemarket.com/warhammer-age-of-sigmar-slaves-to-darkness-ogroid-theridons-gw-83-63.html',
        False,
        False,
    ),
    (
        'chaos-knights',
        'Chaos Knights',
        None,
        'https://www.miniaturemarket.com/warhammer-age-of-sigmar-slaves-to-darkness-chaos-knights-gw-83-09-2023.html',
        False,
        False,
    ),

    # ── Terrain ───────────────────────────────────────────────────────────────
    (
        'nexus-chaotica',
        'Nexus Chaotica',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-slaves-to-darkness-nexus-chaotica-gw-80-54.html',
        False,
        False,
    ),

    # ── Cavalry / Infantry (Darkoath) ─────────────────────────────────────────
    (
        'darkoath-fellriders',
        'Darkoath Fellriders',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-slaves-to-darkness-darkoath-fellriders-gw-83-54-2024.html',
        False,
        False,
    ),
    (
        'darkoath-marauders',
        'Darkoath Marauders',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-slaves-to-darkness-darkoath-marauders-gw-83-52-2024.html',
        False,
        False,
    ),

    # ⚠ Shared kit (dual): see Darkoath Chieftain note
    (
        'darkoath-chieftain-on-warsteed',
        'Darkoath Chieftain / Darkoath Chieftain on Warsteed',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-slaves-to-darkness-darkoath-chieftain-warsteed-gw-83-53-2024.html',
        False,
        False,
    ),

    # ── Infantry (cont.) ──────────────────────────────────────────────────────
    (
        'chaos-chosen',
        'Chaos Chosen',
        None,
        'https://www.miniaturemarket.com/warhammer-age-of-sigmar-slaves-to-darkness-chaos-chosen-gw-83-93.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Slaves to Darkness products."""

    help = 'Seeds Miniature Market listing URLs and prices for Slaves to Darkness. Idempotent.'

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
