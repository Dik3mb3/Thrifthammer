"""
Management command: seed_mm_cult_mechanicum_prices

Seeds Miniature Market URLs for Cult Mechanicum products.

15 of 18 CM SKUs have confirmed MM listings. Omitted (no MM listing):
CM-014, CM-015, CM-016.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_cult_mechanicum_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('mechanicum-combat-force', 'Mechanicum: Combat Force', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Combat-Force-Mechanicum/GW-31-132', False, False),
    ('skitarii-battle-pilgrym-marshal', 'Skitarii Battle-Pilgrym Marshal', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Mechanicum-Skitarii-Battle-Pilgrym-Marshal/GW-31-150-2026', False, False),
    ('vultarax-stratos-automata', 'Vultarax Stratos-Automata', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Mechanicum-Vultarax-Stratos-Automata/GW-31-147-2026', False, False),
    ('skitarii-battle-pilgrym-corpus', 'Skitarii Battle-Pilgrym Corpus', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Mechanicum-Skitarii-Battle-Pilgrym-Corpus/GW-31-134-2026', False, False),
    ('ursarax-cohort', 'Ursarax Cohort', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-mechanicum-ursarax-cohort-gw-31-107.html', False, False),
    ('krios-battle-tank-venator', 'Krios Battle Tank/Venator', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-mechanicum-krios-battle-tankvenator-gw-31-118.html', False, False),
    ('karacnos-assault-tank', 'Karacnos Assault Tank', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-mechanicum-karacnos-assault-tank-gw-31-114.html', False, False),
    ('thanatar-calix-siege-automata', 'Thanatar Calix Siege-automata', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-mechanicum-thanatar-calix-siege-automata-gw-31-113.html', False, False),
    ('archmagos-prime', 'Archmagos Prime', None, 'https://www.miniaturemarket.com/horus-heresy-mechanicum-archmagos-prime-gw-31-98.html', False, False),
    ('thallax-cohort', 'Thallax Cohort', None, 'https://www.miniaturemarket.com/horus-heresy-mechanicum-thallax-cohort-gw-31-97.html', False, False),
    ('triaros-armoured-conveyor', 'Triaros Armoured Conveyor', None, 'https://www.miniaturemarket.com/horus-heresy-mechanicum-triaros-armoured-conveyor-gw-31-92.html', False, False),
    ('tech-thralls-covenant', 'Tech-thralls Covenant', None, 'https://www.miniaturemarket.com/horus-heresy-mechanicum-tech-thralls-covenant-gw-31-90.html', False, False),
    ('castellax-battle-automata-maniple', 'Castellax Battle-automata Maniple', None, 'https://www.miniaturemarket.com/horus-heresy-mechanicum-castellax-battle-automata-maniple-gw-31-89.html', False, False),
    ('myrmidon-destructor-host', 'Myrmidon Destructor Host', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Mechanicum-Myrmidon-Destructor-Host/GW-31-157-2026', False, False),
    ('thanatar-cavas-siege-automata', 'Thanatar Cavas Siege-automata', None, 'https://www.miniaturemarket.com/horus-heresy-mechanicum-thanatar-cavas-siege-automata-gw-31-91.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Cult Mechanicum products."""

    help = 'seed_mm_cult_mechanicum_prices — MM URLs for Cult Mechanicum (15 of 18 SKUs)'

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
            f'seed_mm_cult_mechanicum_prices complete. {seeded} record(s) seeded.'
        ))
