"""
Management command: seed_nk_tau_prices

Seeds Noble Knight prices for T'au Empire products.

Source: Tau - GW, NK, MM, Amazon.xlsx (2026-05-13)

NK MATCHES (27 products with NK URLs):
  TE-001 to TE-010, TE-015 to TE-022, TE-023 to TE-029, TE-036, TE-037

NO NK LISTING (10 products):
  TE-011, TE-012, TE-013, TE-014, TE-030, TE-031, TE-032, TE-033, TE-034, TE-035

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
        'tau-empire-tidewall-shieldline',
        'Tidewall Shieldline 2022 Edition',
        None,
        f'{_NK_BASE}/P/2148287519/Tidewall-Shieldline-2022-Edition?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-kroot-hounds',
        'Kroot Hounds',
        None,
        f'{_NK_BASE}/P/2148139705/Kroot-Hounds?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-the-twin-lance',
        'Twin Lance The',
        None,
        f'{_NK_BASE}/P/2148424048/Twin-Lance-The?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-commander-farsight',
        'Commander Farsight',
        None,
        f'{_NK_BASE}/P/2148064040/Commander-Farsight?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-darkstrider',
        'Darkstrider',
        None,
        f'{_NK_BASE}/P/2147955096/Darkstrider?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-commander-shadowsun',
        'Commander Shadowsun',
        None,
        f'{_NK_BASE}/P/2147964164/Commander-Shadowsun?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Breacher Team / Strike Team — Breacher now has its own NK listing
    (
        'tau-empire-fire-warriors-breacher-team',
        'Fire Warriors',
        None,
        f'{_NK_BASE}/P/2147956210/Fire-Warriors?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-fire-warriors-strike-team',
        'Fire Warriors',
        None,
        f'{_NK_BASE}/P/2147956210/Fire-Warriors?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-commander',
        'Commander 2022 Edition',
        None,
        f'{_NK_BASE}/P/2147966366/Commander-2022-Edition?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-cadre-fireblade',
        'Cadre Fireblade',
        None,
        f'{_NK_BASE}/P/2147974289/Cadre-Fireblade?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-ghostkeel-battlesuit',
        'XV95 Ghostkeel Battlesuit 2022 Edition',
        None,
        f'{_NK_BASE}/P/2147960818/XV95-Ghostkeel-Battlesuit-2022-Edition?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-stormsurge',
        'Stormsurge',
        None,
        f'{_NK_BASE}/P/2148009800/Stormsurge?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Razorshark / Sun Shark share the same NK listing
    (
        'tau-empire-razorshark-strike-fighter',
        'Sun Shark Bomber / Razorshark Strike Fighter',
        None,
        f'{_NK_BASE}/P/2147522595/Sun-Shark-Bomber-Razorshark-Strike-Fighter?awid=1576',
        False,
        False,
    ),
    # ⚠ Dual kit: Sky Ray / Hammerhead share the same NK listing (Hammerhead = 56-10)
    (
        'tau-empire-sky-ray-gunship',
        'Hammerhead Gunship',
        None,
        f'{_NK_BASE}/P/2147956451/Hammerhead-Gunship?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-sun-shark-bomber',
        'Sun Shark Bomber / Razorshark Strike Fighter',
        None,
        f'{_NK_BASE}/P/2147522595/Sun-Shark-Bomber-Razorshark-Strike-Fighter?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-devilfish',
        'Devilfish',
        None,
        f'{_NK_BASE}/P/2147956453/Devilfish?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-farstalker-kinband',
        'Farstalker Kinband',
        None,
        f'{_NK_BASE}/P/2148239646/Farstalker-Kinband?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-vespid-stingwings',
        'Vespid Stingwings',
        None,
        f'{_NK_BASE}/P/2148239661/Vespid-Stingwings?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-kroot-lone-spear',
        'Kroot Lone-Spear',
        None,
        f'{_NK_BASE}/P/2148139697/Kroot-Lone-Spear?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-kroot-trail-shaper',
        'Kroot Trail Shaper',
        None,
        f'{_NK_BASE}/P/2148139728/Kroot-Trail-Shaper?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-kroot-flesh-shaper',
        'Kroot Flesh Shaper',
        None,
        f'{_NK_BASE}/P/2148139725/Kroot-Flesh-Shaper?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-kroot-war-shaper',
        'Kroot War Shaper',
        None,
        f'{_NK_BASE}/P/2148139706/Kroot-War-Shaper?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-krootox-rider',
        'Krootox Rider',
        None,
        f'{_NK_BASE}/P/2148139713/Krootox-Rider?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-krootox-rampagers',
        'Krootox Rampagers',
        None,
        f'{_NK_BASE}/P/2148139692/Krootox-Rampagers?awid=1576',
        False,
        False,
    ),
    (
        'codex-tau-empire',
        "Codex - Tau Empire",
        None,
        f'{_NK_BASE}/P/2148139659/Codex---Tau-Empire?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-piranha',
        'Piranha',
        None,
        f'{_NK_BASE}/P/2148278147/Piranha?awid=1576',
        False,
        False,
    ),
    (
        'tau-empire-kroot-carnivores',
        'Kroot Carnivores',
        None,
        f'{_NK_BASE}/P/2148139700/Kroot-Carnivores?awid=1576',
        False,
        False,
    ),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for T'au Empire products."""

    help = "Seeds Noble Knight listing URLs and prices for T'au Empire. Idempotent."

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
