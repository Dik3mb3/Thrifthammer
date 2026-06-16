"""
Seed Games Workshop UK prices for Chaos Space Marines.

Creates/reuses the `games-workshop-uk` Retailer, sets msrp_gbp on each
matched Product, and creates/updates a CurrentPrice record pointing at the
GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.

Note: Maulerfiend and Forgefiend share gw_sku 99120102089 but have distinct
GW UK URLs. A 6th tuple element (name_filter) disambiguates them.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url, in_stock)
# Optional 6th element: name_filter (icontains) for shared-SKU products.
_PRICES = [
    ('43-06',                    'Chaos Space Marines Legionaries',                          Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-legionaries-2025',                                True),
    ('43-09',                    'Chaos Predator',                                           Decimal('47.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Predator',                                         True),
    ('71-06',                    'Chaos Space Marines Combat Patrol',                        Decimal('105.00'), 'https://www.warhammer.com/en-GB/shop/combat-patrol-chaos-space-marines-2024',                               True),
    ('99070102015',              'Chaos Space Marines Sorcerer',                             Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Sorcerer-2019',                                    True),
    ('99120102052',              'Chaos Land Raider',                                        Decimal('58.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Land-Raider',                                      True),
    ('99120102089',              'Maulerfiend',                                              Decimal('54.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marine-Maulerfiend-2019',                                  True, 'Maulerfiend'),
    ('99120102089',              'Forgefiend',                                               Decimal('54.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Forgefiend-2019',                                  True, 'Forgefiend'),
    ('99120102090',              'Heldrake',                                                 Decimal('55.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Heldrake-2019',                                    True),
    ('99120102092',              'Chaos Rhino',                                              Decimal('36.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marine-Rhino-2019',                                        True),
    ('99120102097',              'Chaos Terminator Squad',                                   Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marine-Terminators-2019',                                  True),
    ('99120201050',              'Chaos Spawn',                                              Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Spawn-2016',                                                     True),
    ('99120201130',              'Daemon Prince',                                            Decimal('54.50'),  'https://www.warhammer.com/en-GB/shop/slaves-to-darkness-daemon-prince-2023',                                True),
    ('CSM-001',                  'Abaddon the Despoiler',                                   Decimal('44.50'),  'https://www.warhammer.com/en-GB/shop/Abaddon-the-Despoiler-2019',                                           True),
    ('CSM-002',                  'Accursed Cultists',                                       Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-accursed-cultists-2022',                           True),
    ('CSM-003',                  'Chaos Bikers',                                            Decimal('30.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marine-Bikers-2019',                                        True),
    ('CSM-004',                  'Chaos Cultists',                                          Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-chaos-cultists-2022',                               True),
    ('CSM-005',                  'Chaos Lord in Terminator Armour',                         Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marine-Chaos-Lord-2019',                                   True),
    ('CSM-006',                  'Chaos Lord with Jump Pack',                               Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-lord-with-jump-pack-2024',                         True),
    ('CSM-007',                  'Chosen',                                                  Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-chosen-2022',                                       True),
    ('CSM-008',                  'Cultist Firebrand',                                       Decimal('23.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-cultist-firebrand-2024',                           True),
    ('CSM-009',                  'Cypher',                                                  Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/Cypher-2018',                                                           True),
    ('CSM-010',                  'Dark Apostle',                                            Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Dark-Apostle-2019',                                True),
    ('CSM-011',                  'Dark Commune',                                            Decimal('35.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-dark-commune-2022',                                 True),
    ('CSM-012',                  'Fabius Bile',                                             Decimal('29.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Fabius-Bile-2020',                                 True),
    ('CSM-013',                  'Haarken Worldclaimer',                                    Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/Haarken-Worldclaimer-2018',                                            True),
    ('CSM-014',                  'Havocs',                                                  Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marine-Havocs-2019',                                        True),
    ('CSM-015',                  'Huron Blackheart and the Masters of the Maelstrom',       Decimal('57.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-huron-blackheart-2026',                            True),
    ('CSM-016',                  'Kravek Morne',                                            Decimal('29.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-kravek-morne-2026',                                 True),
    ('CSM-017',                  'Lord Discordant on Helstalker',                           Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Vex-Machinator-2019',                              True),
    ('CSM-018',                  'Master of Possession',                                    Decimal('25.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-master-of-possession-2023',                        True),
    ('CSM-019',                  'Mutilators',                                              Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-mutilators-2026',                                   True),
    ('CSM-020',                  'Noctilith Crown',                                         Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Noctilith-Crown-2019',                             True),
    ('CSM-021',                  'Possessed',                                               Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-possessed-2022',                                    True),
    ('CSM-022',                  'Red Corsairs Raiders',                                    Decimal('38.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-red-corsairs-raiders-2026',                        True),
    ('CSM-023',                  'Red Corsairs Reave-Captain',                              Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-red-corsairs-reave-captain-2026',                  True),
    ('CSM-024',                  'Traitor Enforcer',                                        Decimal('34.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-traitor-enforcer-2025',                            True),
    ('CSM-025',                  'Traitor Guardsmen Squad',                                 Decimal('32.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-traitor-guardsmen-squad-2025',                     True),
    ('CSM-026',                  'Vashtorr the Arkifane',                                   Decimal('64.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-vashtorr-the-arkifane-2023',                       True),
    ('CSM-027',                  'Venomcrawler and Obliterators',                           Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-warpforged-venomcrawler-and-obliterators-2022',    True),
    ('CSM-028',                  'Warpsmith',                                               Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-warpsmith-2022',                                    True),
    ('CSM-029',                  'Chaos Lord',                                              Decimal('27.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-chaos-lord-2024',                                   True),
    ('CSM-030',                  'Codex: Chaos Space Marines',                              Decimal('38.00'),  'https://www.warhammer.com/en-GB/shop/codex-chaos-space-marines-2024-eng',                                   True),
    ('CSM-031',                  'Iron Warriors Upgrades',                                  Decimal('20.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-iron-warriors-upgrades-2026',                     True),
    ('CSM-032',                  'Chaos Space Marines Fellgor Ravagers',                    Decimal('42.50'),  'https://www.warhammer.com/en-GB/shop/kill-team-fellgor-ravagers-2024',                                       True),
    ('CSM-033',                  'Chaos Space Marines Murderwing',                          Decimal('49.50'),  'https://www.warhammer.com/en-GB/shop/kill-team-murderwing-2026',                                             True),
    ('CSM-034',                  'Chaos Space Marines Nemesis Claw',                        Decimal('47.00'),  'https://www.warhammer.com/en-GB/shop/kill-team-nemesis-claw-2024',                                           True),
    ('CSM-035',                  'Red Corsairs Upgrades and Transfers',                     Decimal('21.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-red-corsairs-upgrades-and-transfers-2026',          True),
    ('P-CSM-DEFILER-2026',       'Chaos Defiler',                                           Decimal('88.00'),  'https://www.warhammer.com/en-GB/shop/chaos-space-marines-defiler-2026',                                      True),
    ('P-CSM-MASTER-EXEC',        'Master of Executions',                                    Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Master-Of-Executions-2019',                                             True),
    ('P-CSM-SORC-TERM',          'Chaos Sorcerer Lord in Terminator Armour',               Decimal('20.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Terminator-Sorcerer-2019',                                       True),
    ('P-CSM-VINDICATOR',         'Chaos Vindicator',                                        Decimal('47.50'),  'https://www.warhammer.com/en-GB/shop/Chaos-Space-Marines-Vindicator',                                        True),
    ('prod2430129-99120102043',  'Chaos Helbrute',                                          Decimal('40.00'),  'https://www.warhammer.com/en-GB/shop/Helbrute',                                                              True),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Chaos Space Marines. Idempotent.'

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

        for entry in _PRICES:
            sku, label, gbp_price, url, in_stock = entry[:5]
            name_filter = entry[5] if len(entry) > 5 else None

            qs = Product.objects.filter(gw_sku=sku)
            if name_filter:
                qs = qs.filter(name__icontains=name_filter)
            products = list(qs)

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

        self.stdout.write(f'Seeded {seeded} Chaos Space Marines GW UK prices. Skipped: {skipped}.')
