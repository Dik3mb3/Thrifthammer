"""
Management command: seed_nk_sk_prices

Seeds Noble Knight prices for Skaven products.

Source: AOS Skaven GW, NK, MM, AMAZON.xlsx (2026-05-15)

NK MATCHES (30 products with NK URLs):
  SK-001 to SK-010, SK-012, SK-014 to SK-016, SK-019 to SK-022, SK-024 to SK-032,
  SK-033, SK-034, SK-035, SK-036

NO NK LISTING (6 products):
  SK-011 (Night Runners), SK-013 (Plaguepack), SK-017 (Ratling Warpblaster),
  SK-018 (Warplock Jezzails), SK-023 (Warp-Grinder — has own listing, see below),
  (SK-023 does have its own NK listing — included)

Dual kits sharing NK URL:
  SK-007 / SK-008  (Screaming Bell / Plague Furnace)
  SK-028 to SK-032  (all 5 Verminlords)
  SK-033 / SK-034  (Warp Lightning Cannon / Plagueclaw)

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
        'chaos-battletome-skaven',
        'Chaos Battletome - Skaven 2024 Edition',
        None,
        f'{_NK_BASE}/P/2148304083/Chaos-Battletome---Skaven-2024-Edition?awid=1576',
        False,
        False,
    ),
    (
        'spearhead-city-of-ash',
        'Spearhead - City of Ash',
        None,
        f'{_NK_BASE}/P/2148454219/Spearhead---City-of-Ash?awid=1576',
        False,
        False,
    ),
    (
        'skaven-deathmaster',
        'Skaven Deathmaster',
        None,
        f'{_NK_BASE}/P/2148042036/Skaven-Deathmaster?awid=1576',
        False,
        False,
    ),
    (
        'skaven-warlock-bombardier',
        'Warlock Bombardier',
        None,
        f'{_NK_BASE}/P/2148040633/Warlock-Bombardier?awid=1576',
        False,
        False,
    ),
    (
        'skaven-endless-spells',
        'Skaven - Endless Spells',
        None,
        f'{_NK_BASE}/P/2147744991/Skaven---Endless-Spells?awid=1576',
        False,
        False,
    ),
    (
        'skaven-gnawholes',
        'Gnawholes',
        None,
        f'{_NK_BASE}/P/2147744992/Gnawholes?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Screaming Bell / Plague Furnace share the same NK listing
    (
        'skaven-screaming-bell',
        'Screaming Bell / Plague Furnace',
        None,
        f'{_NK_BASE}/P/2147418475/Screaming-Bell---Plague-Furnace?awid=1576',
        False,
        False,
    ),
    (
        'skaven-plague-priest-on-plague-furnace',
        'Screaming Bell / Plague Furnace',
        None,
        f'{_NK_BASE}/P/2147418475/Screaming-Bell---Plague-Furnace?awid=1576',
        False,
        False,
    ),
    (
        'skaven-clawlord',
        'Skaven Warlord / Clawlord Webstore Edition',
        None,
        f'{_NK_BASE}/P/2148217619/Skaven-Warlord-Clawlord-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'skaven-doomwheel',
        'Doomwheel 2009 Edition',
        None,
        f'{_NK_BASE}/P/2147418010/Doomwheel-2009-Edition?awid=1576',
        False,
        False,
    ),
    (
        'skaven-thanquol-and-boneripper',
        'Thanquol and Boneripper',
        None,
        f'{_NK_BASE}/P/2147568837/Thanquol-and-Boneripper?awid=1576',
        False,
        False,
    ),
    (
        'skaven-clawlord-on-gnaw-beast',
        'Clawlord on Gnaw-Beast Webstore Edition',
        None,
        f'{_NK_BASE}/P/2148217540/Clawlord-on-Gnaw-Beast-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'skaven-rat-ogors',
        'Rat Ogors',
        None,
        f'{_NK_BASE}/P/2148318256/Rat-Ogors?awid=1576',
        False,
        False,
    ),
    (
        'skaven-arch-warlock',
        'Arch-Warlock',
        None,
        f'{_NK_BASE}/P/2148276671/Arch-Warlock?awid=1576',
        False,
        False,
    ),
    (
        'skaven-vizzik-skour-prophet-of-the-horned-rat',
        'Vizzik Skour, Prophet of the Horned Rat',
        None,
        f'{_NK_BASE}/P/2148276676/Vizzik-Skour-Prophet-of-the-Horned-Rat?awid=1576',
        False,
        False,
    ),
    (
        'skaven-brood-terror',
        'Brood Terror',
        None,
        f'{_NK_BASE}/P/2148276662/Brood-Terror?awid=1576',
        False,
        False,
    ),
    (
        'skaven-warlock-galvaneer',
        'Warlock Galvaneer',
        None,
        f'{_NK_BASE}/P/2148276722/Warlock-Galvaneer?awid=1576',
        False,
        False,
    ),
    (
        'skaven-acolyte-globadiers',
        'Acolyte Globadiers',
        None,
        f'{_NK_BASE}/P/2148276654/Acolyte-Globadiers?awid=1576',
        False,
        False,
    ),
    (
        'skaven-warp-grinder',
        'Warp-Grinder',
        None,
        f'{_NK_BASE}/P/2148276667/Warp-Grinder?awid=1576',
        False,
        False,
    ),
    (
        'skaven-warpspark-weapon-battery',
        'Warpspark Weapon Battery',
        None,
        f'{_NK_BASE}/P/2148276665/Warpspark-Weapon-Battery?awid=1576',
        False,
        False,
    ),
    (
        'skaven-doom-flayers',
        'Doom-Flayers',
        None,
        f'{_NK_BASE}/P/2148276694/Doom-Flayers?awid=1576',
        False,
        False,
    ),
    (
        'skaven-master-moulder',
        'Master Moulder',
        None,
        f'{_NK_BASE}/P/2148322496/Master-Moulder?awid=1576',
        False,
        False,
    ),
    (
        'skaven-hell-pit-abomination',
        'Hell Pit Abomination',
        None,
        f'{_NK_BASE}/P/2147441808/Hell-Pit-Abomination?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: all 5 Verminlords build from the same box / NK listing
    (
        'skaven-verminlord-warpseer',
        'Verminlord',
        None,
        f'{_NK_BASE}/P/2147567989/Verminlord?awid=1576',
        False,
        False,
    ),
    (
        'skaven-lord-skreech-verminking',
        'Verminlord',
        None,
        f'{_NK_BASE}/P/2147567989/Verminlord?awid=1576',
        False,
        False,
    ),
    (
        'skaven-verminlord-warbringer',
        'Verminlord',
        None,
        f'{_NK_BASE}/P/2147567989/Verminlord?awid=1576',
        False,
        False,
    ),
    (
        'skaven-verminlord-deceiver',
        'Verminlord',
        None,
        f'{_NK_BASE}/P/2147567989/Verminlord?awid=1576',
        False,
        False,
    ),
    (
        'skaven-verminlord-corruptor',
        'Verminlord',
        None,
        f'{_NK_BASE}/P/2147567989/Verminlord?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Warp Lightning Cannon / Plagueclaw share the same NK listing
    (
        'skaven-warp-lightning-cannon',
        'Plagueclaw / Warp Lightning Cannon Webstore Edition',
        None,
        f'{_NK_BASE}/P/2148118189/Plagueclaw-Warp-Lightning-Cannon-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'skaven-plagueclaw',
        'Plagueclaw / Warp Lightning Cannon Webstore Edition',
        None,
        f'{_NK_BASE}/P/2148118189/Plagueclaw-Warp-Lightning-Cannon-Webstore-Edition?awid=1576',
        False,
        False,
    ),
    (
        'skaven-krittok-foulblade',
        'Krittok Foulblade',
        None,
        f'{_NK_BASE}/P/2148276701/Krittok-Foulblade?awid=1576',
        False,
        False,
    ),
    (
        'skaven-stormvermin',
        'Stormvermin 2024 Edition',
        None,
        f'{_NK_BASE}/P/2148276658/Stormvermin-2024-Edition?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Skaven products."""

    help = 'Seeds Noble Knight listing URLs and prices for Skaven. Idempotent.'

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
