"""
Seed Games Workshop UK prices for Middle Earth (MESBG).

Creates the `games-workshop-uk` Retailer if it does not exist, sets
msrp_gbp on each matched Product, and creates/updates a CurrentPrice
record pointing at the GW UK product page.

All 95 plastic-only MESBG products matched cleanly against the source UK
sheet (298 rows, includes non-plastic items outside our catalog scope) --
no ambiguous or missing items.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url)
_PRICES = [
    ('MESBG-001', 'The War of the Rohirrim – Battle of Edoras', Decimal('140.00'),
     'https://www.warhammer.com/en-GB/shop/war-of-the-rohirrim-battle-of-edoras-eng-2024'),
    ('MESBG-002', 'Middle-earth Strategy Battle Game: The Treachery of Gollum', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-journal-the-treachery-of-gollum-sb-eng-2026'),
    ('MESBG-003', 'Middle-earth Strategy Battle Game: The Burning of the Westfold', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-burning-of-the-westfold-2026-eng'),
    ('MESBG-004', 'The Lord of the Rings: The War of the Rohirrim', Decimal('17.00'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-the-war-of-the-rohirrim-eng-sb-2025'),
    ('MESBG-005', 'Middle-earth Strategy Battle Game: Matched Play Guide', Decimal('20.00'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-matched-play-guide-sb-eng-2025'),
    ('MESBG-006', 'Armies of Middle-earth', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/armies-of-middle-earth-hb-eng-2025'),
    ('MESBG-007', 'Armies of The Hobbit', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/armies-of-the-hobbit-eng-hb-2024'),
    ('MESBG-008', 'Armies of The Lord of The Rings', Decimal('40.00'),
     'https://www.warhammer.com/en-GB/shop/armies-of-the-lord-of-the-rings-eng-hb-2024'),
    ('MESBG-009', 'Middle-earth Strategy Battle Game Rules Manual', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-strategy-battle-game-rules-manual-eng-2024'),
    ('MESBG-010', 'Hill Tribesmen Commanders', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-hill-tribesmen-commanders-2026'),
    ('MESBG-011', 'Warriors of Rohan Commanders', Decimal('29.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-warriors-of-rohan-commanders-2026'),
    ('MESBG-012', 'Minas Tirith Battlehost', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/minas-tirith-battlehost-2022'),
    ('MESBG-013', 'Gondor Tower', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-gondor-tower-2023'),
    ('MESBG-014', 'Gondor Mansion', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-gondor-mansion-2023'),
    ('MESBG-015', 'Gondor Ruins', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-gondor-ruins-2023'),
    ('MESBG-016', 'Gothmog, Lieutenant of Sauron', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/gothmog-lieutenant-of-sauron-2023'),
    ('MESBG-017', 'Ruins of Middle-earth', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/ruins-of-middle-earth-2022'),
    ('MESBG-018', 'Isengard Battlehost', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/isengard-battlehost-2022'),
    ('MESBG-019', 'Elrond, Master of Rivendell', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-elrond-master-of-rivendell-2022'),
    ('MESBG-020', 'Ruins of Dol Guldur', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/ruins-of-dol-guldur-2021'),
    ('MESBG-021', 'Treebeard, Mighty Ent', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/Treebeard-Mighty-Ent-2021'),
    ('MESBG-022', 'Mines of Moria', Decimal('19.00'),
     'https://www.warhammer.com/en-GB/shop/Mines-of-Moria-Terrain-2020'),
    ('MESBG-023', 'Saruman the White & Gríma', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Saruman-The-White-and-Grima-2019'),
    ('MESBG-024', 'Mounted Rohan Command', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/Mounted-Rohan-Command-2019'),
    ('MESBG-025', 'Rohan Royal Knights', Decimal('38.50'),
     'https://www.warhammer.com/en-GB/shop/Rohan-Royal-Knights-2019'),
    ('MESBG-026', 'King of the Dead & Heralds', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/King-Of-The-Dead-And-Heralds-2019'),
    ('MESBG-027', 'Éowyn & Merry', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Eowyn-and-Merry-2019'),
    ('MESBG-028', 'The Three Hunters', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/The-Three-Hunters-2019'),
    ('MESBG-029', 'Thorin Oakenshield & Company', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Thorin-Oakenshield-And-Company-2018'),
    ('MESBG-030', 'Gandalf the White and Peregrin Took', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Gandalf-The-White-and-Peregrin-Took-2018'),
    ('MESBG-031', 'Grim Hammers', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Grim-Hammers-2018'),
    ('MESBG-032', 'Warriors of Erebor', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Warriors-Of-Erebor-2018'),
    ('MESBG-033', 'Palace Guards', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Palace-Guards-2018'),
    ('MESBG-034', 'Mirkwood Rangers', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Mirkwood-Rangers-2018'),
    ('MESBG-035', 'Goblin Warriors', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Goblin-Warriors-2018'),
    ('MESBG-036', 'Hunter Orcs', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Hunter-Orcs-2018'),
    ('MESBG-037', 'Warriors of the Last Alliance', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Warriors-Of-The-Last-Alliance-2018'),
    ('MESBG-038', 'Wild Wargs', Decimal('13.50'),
     'https://www.warhammer.com/en-GB/shop/Wild-Wargs-2018'),
    ('MESBG-039', 'Fellowship Of The Ring', Decimal('38.00'),
     'https://www.warhammer.com/en-GB/shop/Fellowship-Of-The-Ring-2018'),
    ('MESBG-040', 'Winged Nazgûl', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Winged-Nazgul-2018'),
    ('MESBG-041', 'The Balrog', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/The-Balrog-2018'),
    ('MESBG-042', 'Mordor Troll', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Mordor-Troll-2018'),
    ('MESBG-043', 'Dwarf Rangers', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Dwarf-Rangers-2018'),
    ('MESBG-044', 'Dwarf Warriors (Middle-earth)', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Dwarf-Warriors-2018'),
    ('MESBG-045', 'Knights Of Dol Amroth', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Knights-Of-Dol-amroth-2018'),
    ('MESBG-046', 'Morgul Knights', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Morgul-Knights-2018'),
    ('MESBG-047', 'Haradrim Warriors', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Haradrim-Warriors-2018'),
    ('MESBG-048', 'Rangers of Middle-earth', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Rangers-Of-Middle-earth-2018'),
    ('MESBG-049', 'Easterling Kataphracts', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Easterling-Kataphracts-2018'),
    ('MESBG-050', 'Easterling Warriors', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Easterling-Warriors-2018'),
    ('MESBG-051', 'Warriors of Minas Tirith', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Warriors-Of-Minas-Tirith-2018'),
    ('MESBG-052', 'Galadhrim Knights', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Galadhrim-Knights-2018'),
    ('MESBG-053', 'Galadhrim Warriors', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Galadhrim-Warriors-2018'),
    ('MESBG-054', 'LOTHLÓRIEN Wood Elf Warriors', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Wood-Elf-Warriors-2018'),
    ('MESBG-055', 'Moria Goblins', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Moria-Goblins-2018'),
    ('MESBG-056', 'Warg Riders', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Warg-Riders-2018'),
    ('MESBG-057', 'Morannon Orcs', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Morannon-Orcs-2018'),
    ('MESBG-058', 'Mordor Orcs', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Mordor-Orcs-2018'),
    ('MESBG-059', 'Uruk-hai Warriors', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Uruk-hai-Warriors-2018'),
    ('MESBG-060', 'Knights of Rivendell', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Knights-of-Rivendell'),
    ('MESBG-061', 'Hunter Orcs on Fell Wargs', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Hunter-Orcs-on-Fell-Wargs'),
    ('MESBG-062', 'The Path of Cirith Ungol: Shelob & Gollum', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/the-path-of-cirith-ungol-shelob-and-gollum-2026'),
    ('MESBG-063', 'Fréaláf Hildeson, Olwyn & Lief, Heroes of Rohan', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-frealeaf-hildeson-and-olwyn-and-lief-2025'),
    ('MESBG-064', 'Helm Hammerhand, King of Rohan', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-helm-hammerhand-king-of-rohan-2025'),
    ('MESBG-065', 'Héra Daughter of Helm', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/hera-daughter-of-helm-2025'),
    ('MESBG-066', 'Rohan House', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/rohan-house-2025'),
    ('MESBG-067', 'Rohan Watchtower & Palisades', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/rohan-watchtower-and-palisades-2025'),
    ('MESBG-068', 'Rohan Stronghold', Decimal('200.00'),
     'https://www.warhammer.com/en-GB/shop/rohan-stronghold-2025'),
    ('MESBG-069', 'Tom, Bill, and Bert – The Trolls', Decimal('57.00'),
     'https://www.warhammer.com/en-GB/shop/the-trolls-2025'),
    ('MESBG-070', 'The Goblin King & Retinue', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/goblin-king-and-retinue-2025'),
    ('MESBG-071', 'Uruk-Hai Demolition Team', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/uruk-hai-demolition-team-2025'),
    ('MESBG-072', 'Wulf, High Lord of the Hill Tribes and General Targg', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/wulf-high-lord-of-the-hill-tribes-and-general-targg-2025'),
    ('MESBG-073', 'Haleth & Háma, Princes of Rohan', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/haleth-and-hama-princes-of-rohan-2025'),
    ('MESBG-074', 'Great Eagles of the Misty Mountains', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/great-eagles-2024'),
    ('MESBG-075', 'Warriors of Rohan', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/warriors-of-rohan-2024'),
    ('MESBG-076', 'Riders of Rohan', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/middle-earth-riders-of-rohan-2026'),
    ('MESBG-077', 'Faramir, Madril and Damrod, Rangers of Ithilien', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/faramir-madril-and-damrod-2023'),
    ('MESBG-078', 'The Witch-king of Angmar', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/m-e-sbg-the-witch-king-of-angmar-2021'),
    ('MESBG-079', 'Éomer, Marshal of the Riddermark', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/Eomer-Marshal-Of-The-Riddermark-2020'),
    ('MESBG-080', 'Warriors of Dale', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Warriors-Of-Dale-2018'),
    ('MESBG-081', 'Théoden, King of Rohan', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/Theoden-King-Of-Rohan-2018'),
    ('MESBG-082', 'Legolas Greenleaf & Tauriel', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/Legolas-Greenleaf-And-tauriel-2018'),
    ('MESBG-083', 'Ent', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Ent-2018'),
    ('MESBG-084', 'Warriors of the Dead', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Warriors-Of-The-Dead-2018'),
    ('MESBG-085', 'War Mûmak Of Harad', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/War-Mumak-Of-Harad-2018'),
    ('MESBG-086', 'Corsairs of Umbar', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Corsairs-Of-Umbar-2018'),
    ('MESBG-087', 'Haradrim Raiders', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Haradrim-Raiders-2018'),
    ('MESBG-088', 'Knights of Minas Tirith', Decimal('28.50'),
     'https://www.warhammer.com/en-GB/shop/Knights-Of-Minas-Tirith-2018'),
    ('MESBG-089', 'Uruk-hai Scouts', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Uruk-hai-Scouts-2018'),
    ('MESBG-090', 'Lake-town House', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/Lake-Town-House'),
    ('MESBG-091', 'Fell Wargs', Decimal('22.00'),
     'https://www.warhammer.com/en-GB/shop/Fell-Wargs'),
    ('MESBG-092', 'Goblin Town', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/Goblin-Town'),
    ('MESBG-093', 'Bolg, Spawn of Azog', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/bolg-spawn-of-azog-2025'),
    ('MESBG-288', 'Prince Imrahil of Dol Amroth', Decimal('23.50'),
     'https://www.warhammer.com/en-GB/shop/prince-imrahil-of-dol-amroth-2025'),
    ('MESBG-295', 'Hill Tribesmen', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/hill-tribesmen-2024'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Middle Earth (MESBG). Idempotent.'

    def handle(self, *args, **options):
        retailer, created = Retailer.objects.get_or_create(
            slug=_GW_UK_SLUG,
            defaults={
                'name': 'Games Workshop UK',
                'website': 'https://www.warhammer.com/en-GB/',
                'country': 'UK',
                'is_active': True,
                'is_uk': True,
            },
        )
        if created:
            self.stdout.write(f'Created retailer: {retailer.name}')

        seeded = 0
        skipped = 0
        for gw_sku, label, gbp_price, url in _PRICES:
            try:
                product = Product.objects.get(gw_sku=gw_sku)
            except Product.DoesNotExist:
                self.stderr.write(f'SKIP — SKU {gw_sku} ({label}) not in DB')
                skipped += 1
                continue

            if product.msrp_gbp != gbp_price:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])

            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailer,
                defaults={
                    'price': gbp_price,
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                },
            )
            seeded += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded {seeded} Middle Earth (MESBG) GW UK prices. Skipped: {skipped}.'
            )
        )
