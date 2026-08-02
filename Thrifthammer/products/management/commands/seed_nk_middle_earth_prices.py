"""
Management command: seed_nk_middle_earth_prices

Seeds Noble Knight CurrentPrice records for Middle Earth (MESBG) products.

40 of 95 products have a confirmed Noble Knight URL, matched by title
against the user-provided NK export. NK carries several listings that
don't correspond to a single DB product (dice sets, individual metal/resin
characters not in our plastic-only catalog) -- those were excluded. Four
products had two competing NK listings (different print editions); the
user chose which listing to keep in each case:
  - King of the Dead & Heralds: kept the "(2019 Edition)" listing.
  - Prince Imrahil of Dol Amroth: kept the plain listing over the
    "Mounted and on Foot" variant.
  - Great Eagles of the Misty Mountains: kept the exact-title listing over
    the "(2018 Edition)" one.
  - War Mumak Of Harad: kept the plain listing over the "(2004 Edition)"
    one.
"Trolls, The" maps to "Tom, Bill, and Bert -- The Trolls" (MESBG-069), not
Mordor Troll -- confirmed by the user. The remaining 55 products have no
Noble Knight listing.

Affiliate tag ?awid=1576 appended to all NK URLs.

Usage:
    python manage.py seed_nk_middle_earth_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    ('warriors-of-rohan-commanders', 'Warriors of Rohan Commanders', None, f'{_NK}/P/2148493228/Warriors-of-Rohan-Commanders{_AFF}', False, False),
    ('the-path-of-cirith-ungol-shelob-gollum', 'Path of Cirith Ungol, The - Shelob & Gollum', None, f'{_NK}/P/2148400901/Path-of-Cirith-Ungol-The---Shelob-and-Gollum{_AFF}', False, False),
    ('prince-imrahil-of-dol-amroth', 'Prince Imrahil of Dol-Amroth', None, f'{_NK}/P/2148312262/Prince-Imrahil-of-Dol-Amroth{_AFF}', False, False),
    ('hera-daughter-of-helm', 'Hera, Daughter of Helm', None, f'{_NK}/P/2148312294/Hera-Daughter-of-Helm{_AFF}', False, False),
    ('hill-tribesmen', 'Hill Tribesmen', None, f'{_NK}/P/2148236853/Hill-Tribesmen{_AFF}', False, False),
    ('bolg-spawn-of-azog', 'Bolg, Spawn of Azog', None, f'{_NK}/P/2148312323/Bolg-Spawn-of-Azog{_AFF}', False, False),
    ('lake-town-house', 'Lake-Town House (Webstore Edition)', None, f'{_NK}/P/2147800160/Lake-Town-House-Webstore-Edition{_AFF}', False, False),
    ('the-war-of-the-rohirrim-battle-of-edoras', 'Starter Set - The Battle of Edoras', None, f'{_NK}/P/2148237300/Starter-Set---The-Battle-of-Edoras{_AFF}', False, False),
    ('wulf-high-lord-of-the-hill-tribes-and-general-targg', 'Wulf, High Lord of the Hill Tribes & General Targg', None, f'{_NK}/P/2148249809/Wulf-High-Lord-of-the-Hill-Tribes-and-General-Targg{_AFF}', False, False),
    ('rohan-watchtower-palisades', 'Rohan Watchtower & Palisades', None, f'{_NK}/P/2147775644/Rohan-Watchtower-and-Palisades{_AFF}', False, False),
    ('rohan-house', 'Rohan House', None, f'{_NK}/P/2147775643/Rohan-House{_AFF}', False, False),
    ('galadhrim-knights', 'Galadhrim Knights', None, f'{_NK}/P/2147402199/Galadhrim-Knights{_AFF}', False, False),
    ('tom-bill-and-bert-the-trolls', 'Trolls, The', None, f'{_NK}/P/2147482892/Trolls-The{_AFF}', False, False),
    ('knights-of-minas-tirith', 'Knights of Minas Tirith (2007 Edition)', None, f'{_NK}/P/2147374261/Knights-of-Minas-Tirith-2007-Edition{_AFF}', False, False),
    ('hill-tribesmen-commanders', 'Hill Tribesmen Commanders', None, f'{_NK}/P/2148493231/Hill-Tribesmen-Commanders{_AFF}', False, False),
    ('the-three-hunters', 'Three Hunters, The', None, f'{_NK}/P/2147742905/Three-Hunters-The{_AFF}', False, False),
    ('ruins-of-dol-guldur', 'Ruins of Dol Guldur', None, f'{_NK}/P/2147934891/Ruins-of-Dol-Guldur{_AFF}', False, False),
    ('thorin-oakenshield-company', 'Thorin Oakenshield & Company', None, f'{_NK}/P/2147767590/Thorin-Oakenshield-and-Company{_AFF}', False, False),
    ('warriors-of-minas-tirith', 'Warriors of Minas Tirith', None, f'{_NK}/P/2147729181/Warriors-of-Minas-Tirith{_AFF}', False, False),
    ('haleth-hama-princes-of-rohan', 'Haleth & Hama, Princes of Rohan', None, f'{_NK}/P/2148249812/Haleth-and-Hama-Princes-of-Rohan{_AFF}', False, False),
    ('great-eagles-of-the-misty-mountains', 'Great Eagles of the Misty Mountains', None, f'{_NK}/P/2148236852/Great-Eagles-of-the-Misty-Mountains{_AFF}', False, False),
    ('gandalf-the-white-and-peregrin-took', 'Gandalf the White & Peregrin Took', None, f'{_NK}/P/2147738824/Gandalf-the-White-and-Peregrin-Took{_AFF}', False, False),
    ('minas-tirith-battlehost', 'Minas Tirith Battlehost', None, f'{_NK}/P/2148002506/Minas-Tirith-Battlehost{_AFF}', False, False),
    ('warg-riders', 'Warg Riders (2018 Edition)', None, f'{_NK}/P/2147767585/Warg-Riders-2018-Edition{_AFF}', False, False),
    ('fellowship-of-the-ring', 'Fellowship of the Ring, The', None, f'{_NK}/P/2147767534/Fellowship-of-the-Ring-The{_AFF}', False, False),
    ('wild-wargs', 'Wild Wargs', None, f'{_NK}/P/2147469162/Wild-Wargs{_AFF}', False, False),
    ('easterling-warriors', 'Easterling Warriors', None, f'{_NK}/P/2147767574/Easterling-Warriors{_AFF}', False, False),
    ('elrond-master-of-rivendell', 'Elrond, Master of Rivendell', None, f'{_NK}/P/2148002379/Elrond-Master-of-Rivendell{_AFF}', False, False),
    ('treebeard-mighty-ent', 'Treebeard - Mighty Ent', None, f'{_NK}/P/2147871724/Treebeard---Mighty-Ent{_AFF}', False, False),
    ('war-mumak-of-harad', 'War Mumak of Harad', None, f'{_NK}/P/2147729188/War-Mumak-of-Harad{_AFF}', False, False),
    ('gondor-ruins', 'Gondor Ruins', None, f'{_NK}/P/2148046732/Gondor-Ruins{_AFF}', False, False),
    ('gondor-tower', 'Gondor Tower', None, f'{_NK}/P/2148046730/Gondor-Tower{_AFF}', False, False),
    ('winged-nazgul', 'Winged Nazgul (2018 Edition)', None, f'{_NK}/P/2147767586/Winged-Nazgul-2018-Edition{_AFF}', False, False),
    ('the-witch-king-of-angmar', 'Witch-king of Angmar, The', None, f'{_NK}/P/2147934905/Witch-king-of-Angmar-The{_AFF}', False, False),
    ('mordor-troll', 'Mordor Troll/Isengard Troll', None, f'{_NK}/P/2147729177/Mordor-Troll-Isengard-Troll{_AFF}', False, False),
    ('eowyn-merry', 'Eowyn & Merry', None, f'{_NK}/P/2147748742/Eowyn-and-Merry{_AFF}', False, False),
    ('king-of-the-dead-heralds', 'King of the Dead & Heralds (2019 Edition)', None, f'{_NK}/P/2147769605/King-of-the-Dead-and-Heralds-2019-Edition{_AFF}', False, False),
    ('warriors-of-rohan', 'Warriors of Rohan (2002 Edition)', None, f'{_NK}/P/152297910/Warriors-of-Rohan-2002-Edition{_AFF}', False, False),
    ('eomer-marshal-of-the-riddermark', 'Eomer - Marshal of the Riddermark', None, f'{_NK}/P/2147820004/Eomer---Marshal-of-the-Riddermark{_AFF}', False, False),
    ('saruman-the-white-grima', 'Saruman the White & Grima Wormtongue', None, f'{_NK}/P/2147775645/Saruman-the-White-and-Grima{_AFF}', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Middle Earth (MESBG) products (idempotent)."""

    help = 'Seeds Noble Knight CurrentPrice records for Middle Earth (MESBG) products.'

    def handle(self, *args, **options):
        if not NK_PRICES:
            self.stdout.write(self.style.WARNING('NK_PRICES is empty -- nothing to seed.'))
            return

        retailer = Retailer.objects.get(slug='noble-knight-games')

        created = 0
        updated = 0

        for slug, listing_title, price, url, in_stock, not_available in NK_PRICES:
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
            f'Noble Knight prices: {created} created, {updated} updated.'
        ))
