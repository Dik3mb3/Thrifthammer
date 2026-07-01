"""
Management command: seed_nk_forces_of_the_emperor_prices

Seeds Noble Knight URLs for Forces of the Emperor products.

17 of 21 FOE SKUs have confirmed NK listings. Omitted (no NK listing):
FOE-010, FOE-011, FOE-017, FOE-021.

Note: FOE-009 (Malcador Infernus) uses the combined NK listing
"Malcador Infernus and Valdor Tank Destroyers" — the page covers both
kits. FOE-010 (Valdor) has no separate NK listing.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_forces_of_the_emperor_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('rapier-fire-support-battery', 'Rapier Fire Support Battery', None, 'https://www.nobleknight.com/P/2148460503/Rapier-Fire-Support-Battery?awid=1576', False, False),
    ('rapier-direct-fire-battery', 'Rapier Direct Fire Battery', None, 'https://www.nobleknight.com/P/2148460488/Rapier-Direct-Fire-Battery?awid=1576', False, False),
    ('liber-auxilia-solar-auxilia-army-book', 'Liber Auxilia - Solar Auxilia Army Book', None, 'https://www.nobleknight.com/P/2148327752/Liber-Auxilia---Solar-Auxilia-Army-Book?awid=1576', False, False),
    ('charonite-ogryn-section', 'Charonite Ogryn Section', None, 'https://www.nobleknight.com/P/2148460500/Charonite-Ogryn-Section?awid=1576', False, False),
    ('sentinel-guard-sodality', 'Sentinel Guard Sodality', None, 'https://www.nobleknight.com/P/2148451392/Sentinel-Guard-Sodality?awid=1576', False, False),
    ('venatari-sodality', 'Venatari Sodality', None, 'https://www.nobleknight.com/P/2148451391/Venatari-Sodality?awid=1576', False, False),
    ('custodian-guard-sodality', 'Custodian Guard Sodality', None, 'https://www.nobleknight.com/P/2148451399/Custodian-Guard-Sodality?awid=1576', False, False),
    ('solar-auxilia-combat-force', 'Combat Force - Solar Auxilia', None, 'https://www.nobleknight.com/P/2148352420/Combat-Force---Solar-Auxilia?awid=1576', False, False),
    # Combined NK listing covers both Malcador Infernus and Valdor; FOE-010 (Valdor) has no separate listing
    ('malcador-infernus', 'Malcador Infernus and Valdor Tank Destroyers', None, 'https://www.nobleknight.com/P/2148118492/Malcador-Infernus-and-Valdor-Tank-Destroyers?awid=1576', False, False),
    ('hermes-light-veletaris-sentinel-squadron', 'Solar Auxilia - Hermes Sentinel Squadron', None, 'https://www.nobleknight.com/P/2148139671/Solar-Auxilia---Hermes-Sentinel-Squadron?awid=1576', False, False),
    ('solar-auxilia-basilisk-medusa', 'Solar Auxilia - Basilisk/Medusa', None, 'https://www.nobleknight.com/P/2148139743/Solar-Auxilia---Basilisk-Medusa?awid=1576', False, False),
    ('solar-auxilia-leman-russ-assault-tank', 'Leman Russ Assault Tank', None, 'https://www.nobleknight.com/P/2148420563/Leman-Russ-Assault-Tank?awid=1576', False, False),
    ('malcador-heavy-tank', 'Solar Auxilia Malcador Heavy Tank', None, 'https://www.nobleknight.com/P/2148420564/Solar-Auxilia-Malcador-Heavy-Tank?awid=1576', False, False),
    ('veletaris-storm-section', 'Veletaris Storm Section', None, 'https://www.nobleknight.com/P/2148161550/Veletaris-Storm-Section?awid=1576', False, False),
    ('solar-auxilia-tactical-command-section', 'Tactical Command Section', None, 'https://www.nobleknight.com/P/2148161615/Tactical-Command-Section?awid=1576', False, False),
    ('solar-auxilia-lasrifle-section', 'Solar Auxilia Lasrifle Section', None, 'https://www.nobleknight.com/P/2148239207/Solar-Auxilia-Lasrifle-Section?awid=1576', False, False),
    ('solar-auxilia-leman-russ-strike-command-tank', 'Leman Russ Strike Tank', None, 'https://www.nobleknight.com/P/2148211079/Leman-Russ-Strike-Tank?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Forces of the Emperor products."""

    help = 'seed_nk_forces_of_the_emperor_prices — NK URLs for Forces of the Emperor (17 of 21 SKUs)'

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
            f'seed_nk_forces_of_the_emperor_prices complete. {seeded} record(s) seeded.'
        ))
