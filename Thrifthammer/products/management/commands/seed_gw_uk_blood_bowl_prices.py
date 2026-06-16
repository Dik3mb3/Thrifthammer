"""
Seed Games Workshop UK prices for Blood Bowl.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
_PRICES = [
    ('BB-001', 'Blood Bowl Third Season Edition Starter Set',       Decimal('88.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-third-season-edition-2025-eng',                        True),
    ('BB-002', 'Blood Bowl: The Official Rulebook Third Season',     Decimal('36.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-official-rulebook-3rd-2025-eng',                       True),
    ('BB-003', 'Amazon Blood Bowl Team',                             Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-amazon-team-2022',                                      True),
    ('BB-004', 'Norse Blood Bowl Team',                              Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-norse-team-2022',                                       True),
    ('BB-005', 'Khorne Blood Bowl Team',                             Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-khorne-team-2021',                                      True),
    ('BB-006', 'Lizardmen Blood Bowl Team',                          Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Lizardmen-Team-2020',                                   True),
    ('BB-007', 'Necromantic Horror Blood Bowl Team',                 Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Necromantic-Horror-Team-2020',                          True),
    ('BB-008', 'Nurgle Blood Bowl Team',                             Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Nurgles-Rotters-Team-2018',                             True),
    ('BB-009', 'Gnome Blood Bowl Team',                              Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-gnome-team-2024',                                       True),
    ('BB-010', 'Old World Alliance Blood Bowl Team',                 Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-old-world-alliance-team-2023',                         True),
    ('BB-011', 'Imperial Nobility Blood Bowl Team',                  Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Imperial-Nobility-Team-2021',                           True),
    ('BB-012', 'Human Blood Bowl Team',                              Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Reikland-Reavers-Blood-Bowl-Team-2020',                            True),
    ('BB-013', 'Ogre Blood Bowl Team',                               Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Ogre-Team-2020',                                        True),
    ('BB-014', 'Dark Elf Blood Bowl Team',                           Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Dark-Elf-Team-2020',                                    True),
    ('BB-015', 'Shambling Undead Blood Bowl Team',                   Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Champions-of-Death-Team-2020',                          True),
    ('BB-016', 'Skaven Blood Bowl Team',                             Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Skaven-Team-2020',                                      True),
    ('BB-017', 'Chaos Chosen Blood Bowl Team',                       Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Chaos-Chosen-Team-2020',                                True),
    ('BB-018', 'Snotling Blood Bowl Team',                           Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Crud-Creek-Nosepickers-Team-2020',                      True),
    ('BB-019', 'Wood Elf Blood Bowl Team',                           Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-The-Athelorn-Avengers-2019',                            True),
    ('BB-020', 'Halfling Blood Bowl Team',                           Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Greenfield-Grasshuggers-2019',                          True),
    ('BB-021', 'Elven Union Blood Bowl Team',                        Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Elfheim-Eagles-Blood-Bowl-Team-2017',                              True),
    ('BB-022', 'Dwarf Blood Bowl Team',                              Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-The-Dwarf-Giants',                                      True),
    ('BB-023', 'High Elf Blood Bowl Team',                           Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-high-elf-blood-bowl-team-2026',                         True),
    ('BB-024', 'Tomb Kings Blood Bowl Team',                         Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-tomb-kings-team-2025',                                  True),
    ('BB-025', 'Bretonnian Blood Bowl Team',                         Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-bretonnian-team-2025',                                  True),
    ('BB-026', 'Chaos Dwarf Blood Bowl Team',                        Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-chaos-dwarf-team-2024',                                 True),
    ('BB-027', 'Vampire Blood Bowl Team',                            Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-vampire-team-2023',                                     True),
    ('BB-028', 'Skrorg Snowpelt',                                    Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-skrorg-snowpelt-2022',                                  True),
    ('BB-029', 'Blood Bowl Yhetee',                                  Decimal('28.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-yhetee-2022',                                           True),
    ('BB-030', 'Blood Bowl Rat Ogre',                                Decimal('28.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-rat-ogre-2022',                                         True),
    ('BB-031', 'Blood Bowl Kroxigor',                                Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-kroxigor-2021',                                         True),
    ('BB-032', 'Blood Bowl Khorne Bloodspawn',                       Decimal('30.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-khorne-bloodspawn-2021',                                True),
    ('BB-033', 'Blood Bowl Ogre',                                    Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Ogre-2020',                                             True),
    ('BB-034', 'Blood Bowl Treeman',                                 Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Treeman-2020',                                          True),
    ('BB-035', 'Blood Bowl Minotaur',                                Decimal('28.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Minotaur-2017',                                         True),
    ('BB-036', 'Blood Bowl Goblin Secret Weapons',                   Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Goblin-secret-weapons-2017',                                       True),
    ('BB-037', 'Blood Bowl Dwarf Deathroller',                       Decimal('57.50'),  'https://www.warhammer.com/en-GB/shop/Dwarf-Deathroller',                                                True),
    ('BB-038', 'Blood Bowl Troll',                                   Decimal('21.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Troll',                                                 True),
    ('BB-039', 'Blood Bowl Kiroth Krakeneye',                        Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-kiroth-krakeneye-2023',                                 True),
    ('BB-040', 'Blood Bowl Vargheist',                               Decimal('28.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-vargheist-2023',                                        True),
    ("BB-041", "Ivan 'the Animal' Deathshroud",                      Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-ivan-the-animal-deathshroud-2023',                      True),
    ('BB-042', 'Ripper Bolgrot',                                     Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-ripper-bolgrot-2023',                                   True),
    ('BB-043', 'Dribl & Drull',                                      Decimal('28.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-dribl-and-drull-2023',                                  True),
    ('BB-044', 'Cindy Piewhistle & Puggy Baconbreath',               Decimal('28.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-puggy-baconbreath-and-cindy-piewhistle-2023',           True),
    ('BB-045', 'Glotl Stop',                                         Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-glotl-stop-2022',                                       True),
    ("BB-046", "Boa Kon'ssstriktr",                                  Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-boa-konssstriktr-2022',                                 True),
    ('BB-047', 'Estelle La Veneaux',                                 Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-estelle-la-veneaux-2022',                               True),
    ('BB-048', 'Rumbelow Sheepskin',                                 Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-rumbelow-sheepskin-2022',                               True),
    ('BB-049', 'Thorsson Stoutmead',                                 Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-thorsson-stoutmead-2022',                               True),
    ('BB-050', 'Ivar Eriksson',                                      Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-ivar-eriksson-2022',                                    True),
    ('BB-051', 'Fungus The Loon and Bomber Dribblesnot',             Decimal('28.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-fungus-the-loon-and-bomber-dribblesnot-2022',           True),
    ('BB-052', 'Barik Farblast',                                     Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-barik-farblast-2021',                                   True),
    ('BB-053', 'Scyla Anfingrimm',                                   Decimal('48.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-scylla-anfingrimm-2021',                                True),
    ("BB-054", "Kreek 'the Verminator' Rustgouger",                  Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-kreek-the-verminator-rustgouger-2021',                  True),
    ('BB-055', 'Wilhelm Chaney',                                     Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-wilhelm-chaney-2021',                                   True),
    ('BB-056', 'Elf and Dwarf Biased Referees',                      Decimal('14.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Elf-And-Dwarf-Biased-Referees-2021',                    True),
    ('BB-057', 'Varag Ghoul-Chewer',                                 Decimal('14.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Varag-Ghoul-chewer-2021',                               True),
    ('BB-058', 'Gretchen Wachter',                                   Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Gretchen-Wachter-2021',                                 True),
    ('BB-059', 'Skrull Halfheight',                                  Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Skrull-Halfheight-2020',                                True),
    ('BB-060', 'Willow Rosebark',                                    Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Willow-Rosebark-2019',                                             True),
    ('BB-061', 'Deeproot Strongbranch',                              Decimal('54.50'),  'https://www.warhammer.com/en-GB/shop/Deeproot-Strongbranch-2019',                                       True),
    ('BB-062', 'Lord Borak the Despoiler',                           Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Lord-Borak-the-Despoiler-2019',                                    True),
    ('BB-063', 'Blood Bowl Nurgle Rotspawn',                         Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Nurgle-Rotspawn-2019',                                             True),
    ('BB-064', 'Helmut Wulf',                                        Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Helmut-Wulf-2019',                                      True),
    ('BB-065', 'Karla von Kill',                                     Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Karla-Von-Kill-2019',                                   True),
    ('BB-066', 'The Swift Twins',                                    Decimal('37.50'),  'https://www.warhammer.com/en-GB/shop/The-Swift-Twins-2018',                                             True),
    ('BB-067', 'Roxanna Darknail',                                   Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Roxanna-Darknail-2018',                                            True),
    ('BB-068', 'Eldril Sidewinder',                                  Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Eldril-Sidewinder-2018',                                True),
    ('BB-069', 'Josef Bugman, Coach & Star Player',                  Decimal('30.50'),  'https://www.warhammer.com/en-GB/shop/Bb-Josef-Bugman-Coach-Star-Player-2018',                           True),
    ('BB-070', 'Glart Smashrip',                                     Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Glart-Smashrip-2017',                                             True),
    ('BB-071', 'Grombrindal And The Black Gobbo',                    Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Blood-bowl-grombrindal-the-black-gobbo-2017',                      True),
    ('BB-072', 'Grim Ironjaw',                                       Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Blood-bowl-grim-ironjaw-2017',                                     True),
    ('BB-073', 'Hakflem Skuttlespike',                               Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Hakflem-Skuttlespike-2017',                             True),
    ("BB-074", "Morg 'n' Thorg",                                     Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Morg-N-Thorg',                                                     True),
    ('BB-075', 'The Mighty Zug',                                     Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/The-Mighty-Zug',                                                   True),
    ('BB-076', 'Maple Highgrove & Swiftvine Glimmershard',           Decimal('52.50'),  'https://www.warhammer.com/en-GB/shop/maple-highgrove-and-swiftvine-glimmershard-2025',                  True),
    ('BB-077', 'Jeremiah Kool',                                      Decimal('24.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-jeremiah-kool-2025',                                    True),
    ('BB-078', 'Rowana Forestfoot',                                  Decimal('24.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-rowana-forestfoot-2025',                                True),
    ('BB-079', 'Guffle Pusmaw',                                      Decimal('24.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-guffle-pusmaw-2025',                                    True),
    ('BB-080', 'Anqi Panqi',                                         Decimal('24.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-anqi-panqi-2025',                                       True),
    ('BB-081', 'Rashnak Backstabber',                                Decimal('24.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-rashnak-backstabber-2025',                              True),
    ('BB-082', 'Zzharg Madeye',                                      Decimal('24.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-zzharg-madeye-2024',                                    True),
    ("BB-083", "H'thark the Unstoppable",                            Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-hthark-the-unstoppable-2024',                          True),
    ('BB-084', 'Jordell Freshbreeze',                                Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-jordell-freshbreeze-2024',                              True),
    ('BB-085', 'Rodney Roachbait',                                   Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-rodney-roachbait-2024',                                 True),
    ('BB-086', 'Skitter Stab-Stab',                                  Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-skitter-stab-stab-2024',                                True),
    ('BB-087', 'Bilerot Vomitflesh',                                 Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-bilerot-vomitflesh-2023',                               True),
    ('BB-088', 'Count Luthor von Drakenborg',                        Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-count-luthor-von-drakenborg-2023',                      True),
    ('BB-089', 'Grashnak Blackhoof',                                 Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-grashnak-blackhoof-2024',                               True),
    ("BB-090", "'Captain' Karina von Riesz",                         Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-captain-karina-von-riesz-2023',                         True),
    ('BB-091', 'Underworld Denizens Blood Bowl Team',                Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-underworld-denizens-team-2023',                         True),
    ('BB-092', 'Black Orc Blood Bowl Team',                          Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Black-Orc-Team-2021',                                   True),
    ('BB-093', 'Goblin Blood Bowl Team',                             Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Goblin-Team-2020',                                      True),
    ('BB-094', 'Orc Blood Bowl Team',                                Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Orc-Team-2020',                                         True),
    ('BB-095', 'Zolcath The Zoat',                                   Decimal('48.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Zolcath-The-Zoat-2020',                                 True),
    ('BB-096', 'Withergrasp Doubledrool',                            Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-withergrasp-doubledrool-2023',                          True),
    ('BB-097', 'Nobbla Blackwart & Scrappa Sorehead',                Decimal('28.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-nobbla-blackwart-and-scrappa-sorehead-2023',            True),
    ('BB-098', 'Max Spleenripper',                                   Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/blood-bowl-max-spleenripper-2021',                                 True),
    ('BB-099', 'Griff Oberwald',                                     Decimal('14.00'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Griff-Oberwald-2021',                                   True),
    ('BB-100', 'Gloriel Summerbloom',                                Decimal('25.50'),  'https://www.warhammer.com/en-GB/shop/Blood-Bowl-Gloriel-Summerbloom-2019',                              True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices for Blood Bowl. Idempotent.'

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

        for sku, label, gbp_price, url, in_stock in _PRICES:
            products = list(Product.objects.filter(gw_sku=sku))
            if not products:
                self.stdout.write(f'  SKIP {sku} ({label}) — not found in DB')
                skipped += 1
                continue
            for product in products:
                product.msrp_gbp = gbp_price
                product.save(update_fields=['msrp_gbp'])
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailer,
                    defaults={
                        'price': gbp_price,
                        'url': url,
                        'in_stock': in_stock,
                        'not_available': False,
                    },
                )
                seeded += 1

        self.stdout.write(f'Seeded {seeded} Blood Bowl GW UK prices. Skipped: {skipped}.')
