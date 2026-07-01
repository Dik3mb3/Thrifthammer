"""
Management command: seed_mm_forces_of_the_emperor_prices

Seeds Miniature Market URLs for Forces of the Emperor products.

All 21 FOE SKUs have confirmed MM listings.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_forces_of_the_emperor_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('rapier-fire-support-battery', 'Rapier Fire Support Battery', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Solar-Auxilia-Rapier-Fire-Support-Battery/GW-31-171-2026', False, False),
    ('rapier-direct-fire-battery', 'Rapier Direct Fire Battery', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Solar-Auxilia-Rapier-Direct-Fire-Battery/GW-31-170-2026', False, False),
    ('liber-auxilia-solar-auxilia-army-book', 'Liber Auxilia: Solar Auxilia Army Book', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-liber-auxilia-solar-auxilia-army-book-gw-31-122.html', False, False),
    ('charonite-ogryn-section', 'Charonite Ogryn Section', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Solar-Auxilia-Charonite-Ogryn-Section/GW-31-169-2026', False, False),
    ('sentinel-guard-sodality', 'Sentinel Guard Sodality', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legio-Custodes-Sentinel-Guard-Sodality/GW-31-164-2026', False, False),
    ('venatari-sodality', 'Venatari Sodality', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legio-Custodes-Venatari-Sodality/GW-31-162-2026', False, False),
    ('custodian-guard-sodality', 'Custodian Guard Sodality', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legio-Custodes-Custodian-Guard-Sodality/GW-31-161-2026', False, False),
    ('solar-auxilia-combat-force', 'Solar Auxilia: Combat Force', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Combat-Force-Solar-Auxilia/GW-31-137', False, False),
    ('malcador-infernus', 'Malcador Infernus', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-malcador-infernus-gw-31-111.html', False, False),
    ('valdor-tank-destroyer', 'Valdor Tank Destroyer', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-valdor-tank-destroyer-gw-31-110.html', False, False),
    ('arvus-lighter', 'Arvus Lighter', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-arvus-lighter-gw-31-106.html', False, False),
    ('hermes-light-veletaris-sentinel-squadron', 'Hermes Light/Veletaris Sentinel Squadron', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-hermes-sentinel-squadron-gw-31-80.html', False, False),
    ('solar-auxilia-basilisk-medusa', 'Solar Auxilia Basilisk/Medusa', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-basiliskmedusa-gw-31-79.html', False, False),
    ('solar-auxilia-leman-russ-assault-tank', 'Solar Auxilia Leman Russ Assault Tank', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-leman-russ-assault-tank-gw-31-78.html', False, False),
    ('malcador-heavy-tank', 'Malcador Heavy Tank', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-malcador-heavy-tank-gw-31-77.html', False, False),
    ('veletaris-storm-section', 'Veletaris Storm Section', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-veletaris-storm-section-gw-31-76.html', False, False),
    ('aethon-heavy-sentinel', 'Aethon Heavy Sentinel', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-aethon-heavy-sentinel-gw-31-75.html', False, False),
    ('solar-auxilia-tactical-command-section', 'Solar Auxilia Tactical Command Section', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-tactical-command-section-gw-31-74.html', False, False),
    ('solar-auxilia-lasrifle-section', 'Solar Auxilia Lasrifle Section', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-lasrifle-section-gw-31-73.html', False, False),
    ('solar-auxilia-leman-russ-strike-command-tank', 'Solar Auxilia Leman Russ Strike/Command Tank', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-leman-russ-strike-tank-gw-31-72.html', False, False),
    ('dracosan-armoured-transport', 'Dracosan Armoured Transport', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-dracosan-armoured-transport-gw-31-71.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Forces of the Emperor products."""

    help = 'seed_mm_forces_of_the_emperor_prices — MM URLs for Forces of the Emperor (all 21 SKUs)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        mm_retailer = Retailer.objects.get(slug='miniature-market')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(slug=slug)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm_retailer,
                defaults={
                    'listing_title': listing_title,
                    'url': url,
                    'not_available': not_available,
                },
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                    'last_seen': timezone.now(),
                },
            )
            self.stdout.write(f'  seeded MM: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_forces_of_the_emperor_prices complete. {seeded} record(s) seeded.'
        ))
