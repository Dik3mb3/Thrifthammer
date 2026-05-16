"""
Management command: seed_mm_sk_prices

Seeds Miniature Market prices for Skaven products.

Source: AOS Skaven GW, NK, MM, AMAZON.xlsx (2026-05-15)

MM MATCHES (23 products with MM URLs):
  SK-001, SK-002, SK-004, SK-012, SK-015, SK-016, SK-017, SK-018, SK-019,
  SK-020, SK-021, SK-022, SK-023, SK-024, SK-025, SK-026, SK-028, SK-029,
  SK-030, SK-031, SK-032, SK-035, SK-036

NO MM LISTING (13 products):
  SK-003 (Deathmaster), SK-005 (Endless Spells), SK-006 (Gnawholes),
  SK-007 (Screaming Bell), SK-008 (Plague Furnace), SK-009 (Clawlord),
  SK-010 (Doomwheel), SK-011 (Night Runners), SK-013 (Plaguepack),
  SK-014 (Clawlord on Gnaw-beast), SK-027 (Hell Pit Abomination),
  SK-033 (Warp Lightning Cannon), SK-034 (Plagueclaw)

Dual kits sharing MM URL:
  SK-028 to SK-032  (all 5 Verminlords share gw-90-21.html)

Idempotent -- safe to re-run.
Uses create_defaults so scraper-set prices survive Railway redeploys.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Product, Retailer

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    (
        'chaos-battletome-skaven',
        'Chaos Battletome: Skaven',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-chaos-battletome-skaven-gw-90-24-2024.html',
        False,
        False,
    ),
    (
        'spearhead-city-of-ash',
        'Spearhead: City of Ash',
        None,
        'https://www.miniaturemarket.com/Warhammer-Age-of-Sigmar-Spearhead-City-of-Ash-New-Arrival/GW-70-801-2026',
        False,
        False,
    ),
    (
        'skaven-warlock-bombardier',
        'Skaven Warlock Bombardier',
        None,
        'https://www.miniaturemarket.com/gw-90-25.html',
        False,
        False,
    ),
    (
        'skaven-thanquol-and-boneripper',
        'Skaven Thanquol on Boneripper',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-thanquol-on-boneripper-gw-90-16-2024.html',
        False,
        False,
    ),
    (
        'skaven-rat-ogors',
        'Skaven Rat Ogors',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-rat-ogors-gw-90-13.html',
        False,
        False,
    ),
    (
        'skaven-arch-warlock',
        'Skaven Arch-Warlock',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-arch-warlock-gw-90-48.html',
        False,
        False,
    ),
    (
        'skaven-ratling-warpblaster',
        'Skaven Ratling Warpblaster',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-ratling-warpblaster-gw-90-54.html',
        False,
        False,
    ),
    (
        'skaven-warplock-jezzails',
        'Skaven Warplock Jezzails',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-warplock-jezzails-gw-90-53.html',
        False,
        False,
    ),
    (
        'skaven-vizzik-skour-prophet-of-the-horned-rat',
        'Skaven Vizzik Skour, Prophet of the Horned Rat',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-vizzik-skour-prophet-horned-rat-gw-90-20.html',
        False,
        False,
    ),
    (
        'skaven-brood-terror',
        'Skaven Brood Terror',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-brood-terror-gw-90-52.html',
        False,
        False,
    ),
    (
        'skaven-warlock-galvaneer',
        'Skaven Warlock Galvaneer',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-warlock-galvaneer-gw-90-51.html',
        False,
        False,
    ),
    (
        'skaven-acolyte-globadiers',
        'Skaven Acolyte Globadiers',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-acolyte-globadiers-gw-90-47.html',
        False,
        False,
    ),
    (
        'skaven-warp-grinder',
        'Skaven Warp-Grinder',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-warp-grinder-gw-90-46.html',
        False,
        False,
    ),
    (
        'skaven-warpspark-weapon-battery',
        'Skaven Warpspark Weapon Battery',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-warpspark-weapon-battery-gw-90-45.html',
        False,
        False,
    ),
    (
        'skaven-doom-flayers',
        'Skaven Doom-Flayers',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-doom-flayers-gw-90-41.html',
        False,
        False,
    ),
    (
        'skaven-master-moulder',
        'Skaven Master Moulder',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-master-moulder-gw-90-40.html',
        False,
        False,
    ),
    # ⚠ Dual kit: all 5 Verminlords share the same MM listing
    (
        'skaven-verminlord-warpseer',
        'Skaven Verminlord Warpseer',
        None,
        'https://www.miniaturemarket.com/gw-90-21.html',
        False,
        False,
    ),
    (
        'skaven-lord-skreech-verminking',
        'Skaven Lord Skreech Verminking',
        None,
        'https://www.miniaturemarket.com/gw-90-21.html',
        False,
        False,
    ),
    (
        'skaven-verminlord-warbringer',
        'Skaven Verminlord Warbringer',
        None,
        'https://www.miniaturemarket.com/gw-90-21.html',
        False,
        False,
    ),
    (
        'skaven-verminlord-deceiver',
        'Skaven Verminlord Deceiver',
        None,
        'https://www.miniaturemarket.com/gw-90-21.html',
        False,
        False,
    ),
    (
        'skaven-verminlord-corruptor',
        'Skaven Verminlord Corruptor',
        None,
        'https://www.miniaturemarket.com/gw-90-21.html',
        False,
        False,
    ),
    (
        'skaven-krittok-foulblade',
        'Skaven Krittok Foulblade',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-krittok-foulblade-gw-90-49.html',
        False,
        False,
    ),
    (
        'skaven-stormvermin',
        'Skaven Stormvermin',
        None,
        'https://www.miniaturemarket.com/warhammer-age-sigmar-skaven-stormvermin-gw-90-07-2024.html',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Skaven products."""

    help = 'Seeds Miniature Market listing URLs and prices for Skaven. Idempotent.'

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
