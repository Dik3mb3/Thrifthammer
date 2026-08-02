"""
Management command: seed_mm_middle_earth_prices

Seeds Miniature Market CurrentPrice records for Middle Earth (MESBG)
products.

35 of 95 products have a confirmed Miniature Market URL, matched by title
against the user-provided MM export. 4 MM listings were excluded as
dice-accessory products or multi-kit bundle boxes with no 1:1 match to a
single DB product (Garrison of Dale Dice, Dice Set - Hill Tribesmen, Dice
Set - Rohirrim, Mordor Battlehost). The remaining 60 products have no
Miniature Market listing found.

Usage:
    python manage.py seed_mm_middle_earth_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    ('wulf-high-lord-of-the-hill-tribes-and-general-targg', 'Middle-Earth SBG: Wulf, Lord of the Hill Tribes & General Targg', None, 'https://www.miniaturemarket.com/middle-earth-sbg-wulf-lord-hill-tribes-general-targg-gw-30-92.html', False, False),
    ('the-lord-of-the-rings-the-war-of-the-rohirrim', 'Middle-Earth SBG: The War of the Rohirrim', None, 'https://www.miniaturemarket.com/Middle-Earth-SBG-The-War-of-the-Rohirrim/GW-30-02', False, False),
    ('frealaf-hildeson-olwyn-lief-heroes-of-rohan', 'Middle-Earth SBG: Frealeaf Hildeson, Olwyn, & Lief, Heroes of Rohan', None, 'https://www.miniaturemarket.com/Middle-Earth-SBG-Frealeaf-Hildeson-Olwyn-Lief-Heroes-of-Rohan/GW-30-99', False, False),
    ('helm-hammerhand-king-of-rohan', 'Middle-Earth SBG: Helm Hammerhand, King of Rohan', None, 'https://www.miniaturemarket.com/Middle-Earth-SBG-Helm-Hammerhand-King-of-Rohan/GW-30-100', False, False),
    ('haleth-hama-princes-of-rohan', 'Middle-Earth SBG: Haleth & Hama, Princes of Rohan', None, 'https://www.miniaturemarket.com/middle-earth-sbg-haleth-hama-princes-rohan-gw-30-89.html', False, False),
    ('armies-of-middle-earth', 'Middle-Earth SBG: Armies of Middle-Earth', None, 'https://www.miniaturemarket.com/middle-earth-sbg-armies-middle-earth-gw-30-97.html', False, False),
    # ⚠ MM bundle listing (rulebook + character) mapped to the character SKU, per user direction.
    ('prince-imrahil-of-dol-amroth', 'Middle-Earth SBG: Armies of Middle-Earth - Prince Imrahil of Dol Amroth', None, 'https://www.miniaturemarket.com/middle-earth-sbg-armies-middle-earth-prince-imrahil-dol-amroth-gw-30-96.html', False, False),
    ('king-of-the-dead-heralds', 'Middle-Earth SBG: King of the Dead & Heralds', None, 'https://www.miniaturemarket.com/middle-earth-sbg-king-dead-heralds-gw-30-46.html', False, False),
    ('warriors-of-minas-tirith', 'Middle-Earth SBG: Warriors of Minas Tirith', None, 'https://www.miniaturemarket.com/middle-earth-sbg-warriors-minas-tirith-gw-30-21.html', False, False),
    ('rohan-stronghold', 'Middle-Earth SBG: Rohan Stronghold', None, 'https://www.miniaturemarket.com/middle-earth-sbg-rohan-stronghold-gw-30-57.html', False, False),
    ('armies-of-the-lord-of-the-rings', 'Middle-Earth Strategy Battle Game: Armies of The Lord of the Rings', None, 'https://www.miniaturemarket.com/middle-earth-strategy-battle-game-armies-lord-rings-gw-30-87.html', False, False),
    ('warriors-of-rohan', 'Middle-Earth Strategy Battle Game: Warriors of Rohan', None, 'https://www.miniaturemarket.com/middle-earth-strategy-battle-game-warriors-rohan-gw-30-86.html', False, False),
    ('great-eagles-of-the-misty-mountains', 'Middle-Earth Strategy Battle Game: Great Eagles', None, 'https://www.miniaturemarket.com/middle-earth-strategy-battle-game-great-eagles-gw-30-27-2024.html', False, False),
    ('treebeard-mighty-ent', 'Middle-Earth Strategy Battle Game: Treebeard, Mighty Ent', None, 'https://www.miniaturemarket.com/gw-30-52.html', False, False),
    ('warg-riders', 'Middle-Earth Strategy Battle Game: Warg Riders', None, 'https://www.miniaturemarket.com/gw-30-37.html', False, False),
    ('the-three-hunters', 'Middle-Earth Strategy Battle Game: The Three Hunters', None, 'https://www.miniaturemarket.com/gw-30-44.html', False, False),
    ('hera-daughter-of-helm', 'Middle-Earth SBG: The War of the Rohirrim - Hera, Daughter of Helm', None, 'https://www.miniaturemarket.com/middle-earth-sbg-war-rohirrim-hera-daughter-helm-gw-30-98.html', False, False),
    ('bolg-spawn-of-azog', 'Middle-Earth SBG: The Hobbit Motion Picture Trilogy - Bolg, Spawn of Azog', None, 'https://www.miniaturemarket.com/middle-earth-sbg-hobbit-motion-picture-trilogy-bolg-spawn-azog-gw-30-95.html', False, False),
    ('thorin-oakenshield-company', 'Middle-Earth SBG: Thorin Oakenshield & Company', None, 'https://www.miniaturemarket.com/middle-earth-sbg-thorin-oakenshield-company-gw-30-42.html', False, False),
    ('gondor-tower', 'Middle-Earth SBG: Gondor Tower', None, 'https://www.miniaturemarket.com/middle-earth-sbg-gondor-tower-gw-30-76.html', False, False),
    ('gondor-mansion', 'Middle-Earth SBG: Gondor Mansion', None, 'https://www.miniaturemarket.com/middle-earth-sbg-gondor-mansion-gw-30-75.html', False, False),
    ('the-witch-king-of-angmar', 'Middle-Earth SBG: The Witch-King of Angmar', None, 'https://www.miniaturemarket.com/middle-earth-sbg-witch-king-angmar-gw-30-55.html', False, False),
    ('gondor-ruins', 'Middle-Earth SBG: Gondor Ruins', None, 'https://www.miniaturemarket.com/middle-earth-sbg-gondor-ruins-gw-30-77.html', False, False),
    ('armies-of-the-hobbit', 'Middle-Earth Strategy Battle Game: Armies of The Hobbit', None, 'https://www.miniaturemarket.com/middle-earth-strategy-battle-game-armies-hobbit-gw-30-88.html', False, False),
    ('the-war-of-the-rohirrim-battle-of-edoras', 'Middle-Earth Strategy Battle Game: War of the Rohirrim - Battle of Edoras', None, 'https://www.miniaturemarket.com/middle-earth-strategy-battle-game-war-rohirrim-battle-edoras-gw-30-83.html', False, False),
    ('middle-earth-strategy-battle-game-rules-manual', 'Middle-Earth Strategy Battle Game: 2nd Edition Rules Manual', None, 'https://www.miniaturemarket.com/middle-earth-strategy-battle-game-2nd-edition-rules-manual-gw-30-84.html', False, False),
    ('hill-tribesmen', 'Middle-Earth Strategy Battle Game: Hill Tribesmen', None, 'https://www.miniaturemarket.com/middle-earth-strategy-battle-game-hill-tribesmen-gw-30-85.html', False, False),
    ('minas-tirith-battlehost', 'Middle-Earth Strategy Battle Game: Minas Tirith Battlehost', None, 'https://www.miniaturemarket.com/gw-30-72.html', False, False),
    ('mordor-troll', 'Middle-Earth Strategy Battle Game: Mordor Troll / Isengard Troll', None, 'https://www.miniaturemarket.com/gw-30-22.html', False, False),
    ('ruins-of-dol-guldur', 'Middle-Earth Strategy Battle Game: Ruins of Dol Guldur', None, 'https://www.miniaturemarket.com/gw-30-66.html', False, False),
    ('isengard-battlehost', 'Middle-Earth Strategy Battle Game: Isengard Battlehost', None, 'https://www.miniaturemarket.com/gw-30-71.html', False, False),
    ('elrond-master-of-rivendell', 'Middle-Earth Strategy Battle Game: Elrond, Master of Rivendell', None, 'https://www.miniaturemarket.com/gw-30-69.html', False, False),
    ('morannon-orcs', 'Middle-Earth Strategy Battle Game: Morannon Orcs', None, 'https://www.miniaturemarket.com/gw-30-34.html', False, False),
    ('eowyn-merry', 'Middle-Earth Strategy Battle Game: Eowyn & Merry', None, 'https://www.miniaturemarket.com/gw-30-45.html', False, False),
    ('uruk-hai-warriors', 'Middle-Earth Strategy Battle Game: Uruk-Hai Warriors', None, 'https://www.miniaturemarket.com/gw-30-29.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for Middle Earth (MESBG) products (idempotent)."""

    help = 'Seeds Miniature Market CurrentPrice records for Middle Earth (MESBG) products.'

    def handle(self, *args, **options):
        if not MM_PRICES:
            self.stdout.write(self.style.WARNING('MM_PRICES is empty -- nothing to seed.'))
            return

        retailer = Retailer.objects.get(slug='miniature-market')

        created = 0
        updated = 0

        for slug, listing_title, price, url, in_stock, not_available in MM_PRICES:
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Product not found for slug: {slug}'))
                continue

            _, price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                create_defaults={
                    'price': price,
                    'in_stock': in_stock,
                },
                defaults={
                    'url': url,
                    'listing_title': listing_title,
                    'not_available': not_available,
                },
            )
            if price_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Miniature Market prices: {created} created, {updated} updated.'
        ))
