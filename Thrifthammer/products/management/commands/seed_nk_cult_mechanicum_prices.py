"""
Management command: seed_nk_cult_mechanicum_prices

Seeds Noble Knight URLs for Cult Mechanicum products.

14 of 18 CM SKUs have confirmed NK listings. Omitted (no NK listing):
CM-005, CM-006, CM-007, CM-008.

Note: CM-014 (Armiger Helverins) and CM-015 (Armiger Warglaives) share
the same NK listing — both link to the combined Armiger kit page.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_cult_mechanicum_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('mechanicum-combat-force', 'Combat Force - Mechanicum', None, 'https://www.nobleknight.com/P/2148352430/Combat-Force---Mechanicum?awid=1576', False, False),
    ('skitarii-battle-pilgrym-marshal', 'Skitarii Battle Pilgrym Marshal', None, 'https://www.nobleknight.com/P/2148421612/Skitarii-Battle-Pilgrym-Marshal?awid=1576', False, False),
    ('vultarax-stratos-automata', 'Vultarax Stratos-Automata', None, 'https://www.nobleknight.com/P/2148421604/Vultarax-Stratos-Automata?awid=1576', False, False),
    ('skitarii-battle-pilgrym-corpus', 'Skitarii Battle Pilgrym Corpus', None, 'https://www.nobleknight.com/P/2148421599/Skitarii-Battle-Pilgrym-Corpus?awid=1576', False, False),
    ('archmagos-prime', 'Mechanicum - Archmagos Prime', None, 'https://www.nobleknight.com/P/2148192434/Mechanicum---Archmagos-Prime?awid=1576', False, False),
    ('thallax-cohort', 'Mechanicum - Thallax Cohort', None, 'https://www.nobleknight.com/P/2148192421/Mechanicum---Thallax-Cohort?awid=1576', False, False),
    ('triaros-armoured-conveyor', 'Mechanicum - Triaros Armoured Conveyor', None, 'https://www.nobleknight.com/P/2148192415/Mechanicum---Triaros-Armoured-Conveyor?awid=1576', False, False),
    ('tech-thralls-covenant', 'Mechanicum - Tech-Thralls Covenant', None, 'https://www.nobleknight.com/P/2148192428/Mechanicum---Tech-Thralls-Covenant?awid=1576', False, False),
    ('castellax-battle-automata-maniple', 'Castellax Battle Automata Maniple', None, 'https://www.nobleknight.com/P/2148192430/Castellax-Battle-Automata-Maniple?awid=1576', False, False),
    # CM-014 and CM-015 share the same NK combined kit listing
    ('age-of-darkness-armiger-helverins', 'Age of Darkness Armiger Warglaives/Helverins', None, 'https://www.nobleknight.com/P/2148021895/Age-of-Darkness-Armiger-Warglaives-Helverins?awid=1576', False, False),
    ('age-of-darkness-armiger-warglaives', 'Age of Darkness Armiger Warglaives/Helverins', None, 'https://www.nobleknight.com/P/2148021895/Age-of-Darkness-Armiger-Warglaives-Helverins?awid=1576', False, False),
    ('age-of-darkness-knight-questoris', 'Questoris Knights', None, 'https://www.nobleknight.com/P/2147771427/Questoris-Knights?awid=1576', False, False),
    ('myrmidon-destructor-host', 'Myrmidon Destructor Host', None, 'https://www.nobleknight.com/P/2148421609/Myrmidon-Destructor-Host?awid=1576', False, False),
    ('thanatar-cavas-siege-automata', 'Mechanicum - Thanatar Cavas Siege Automata', None, 'https://www.nobleknight.com/P/2148192401/Mechanicum---Thanatar-Cavas-Siege-Automata?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Cult Mechanicum products."""

    help = 'seed_nk_cult_mechanicum_prices — NK URLs for Cult Mechanicum (14 of 18 SKUs)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        nk_retailer = Retailer.objects.get(slug='noble-knight-games')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in NK_PRICES:
            product = Product.objects.get(slug=slug)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=nk_retailer,
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
            self.stdout.write(f'  seeded NK: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_nk_cult_mechanicum_prices complete. {seeded} record(s) seeded.'
        ))
