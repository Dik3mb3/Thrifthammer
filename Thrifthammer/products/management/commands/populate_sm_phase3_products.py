"""
Management command: populate_sm_phase3_products

Adds faction-specific Space Marine products for existing factions that were
missing after the phase-2 generic SM seeding. Covers:

  Blood Angels  —  4 products (Chaplain Jump Pack, Librarian Terminator, Captain, Codex)
  Black Templars — 1 product  (Codex Supplement)
  Dark Angels    — 3 products (Interrogator-Chaplain, Ravenwing Bike Squadron, Codex)
  Grey Knights   — 7 products (Crowe, Purifiers, Purgation, Interceptors, Paladins,
                                Grand Master NDK, Codex)
  Space Wolves   — 16 products (Ulrik, Iron Priest, Wulfen, SW Venerable Dread,
                                 Fenrisian Wolves, Murderfang, Bjorn, Wulfen Dread,
                                 Wolf Priest, Wolf Guard Battle Leader, Blood Claws,
                                 Arjac, Njal, Wolf Guard Headtakers, Logan Grimnar,
                                 Codex Supplement)

ALREADY IN DB (skipped):
  BA:  Dante, Mephiston, Astorath, Lemartes, Sanguinor, Sanguinary Guard/Priest,
       Baal Predator, Death Company, Combat Patrol
  BT:  Marshal, Castellan, Emperor's Champion, Grimaldus, Helbrecht, Sword Brethren,
       Crusader Squad, Execrator, Crusade Ancient, Combat Patrol
  DA:  Azrael, Belial, Asmodai, Lazarus, Lion El'Jonson, Ezekiel, Deathwing Knights,
       Ravenwing Black Knights, Inner Circle Companions, Nephilim/Dark Talon, Sammael,
       Darkshroud, Land Speeder Vengeance, Combat Patrol
  GK:  Strike Squad, Terminators, Grand Master Voldus, (old) Dreadknight, Combat Patrol
  SW:  Ragnar Blackmane, Thunderwolf Cavalry, Grey Hunters (old), Wolf Guard Terminators
       (old), Combat Patrol

SKIPPED:
  - All faction upgrade/transfer sprues
  - Logan Grimnar (not currently listed on GW site)
  - Wolf Guard Terminators 2025 / Grey Hunters 2025 (old versions already in DB)
  - Kill Team products, bundles, starter sets

Sourced from GW en-US all-SM scrape — 2026-04-04. Tagged batch_tag='phase-2'.
Seeds GW CurrentPrice at MSRP. Idempotent (update_or_create keyed on slug).

Usage:
    python manage.py populate_sm_phase3_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# {faction_name: [(slug, name, msrp, img_filename, gw_url), ...]}
PRODUCTS_BY_FACTION = {
    'Blood Angels': [
        (
            'blood-angels-chaplain-jump-pack',
            'Blood Angels Chaplain With Jump Pack',
            39.00,
            '99070101017_BloodAngelsChaplainJumpack01.jpg',
            'https://www.warhammer.com/en-US/shop/Blood-Angels-Chaplain-with-Jump-Pack-2020',
        ),
        (
            'blood-angels-librarian-terminator-armour',
            'Blood Angels Librarian in Terminator Armour',
            35.00,
            '99070101007_BATerminatorLib01.jpg',
            'https://www.warhammer.com/en-US/shop/Blood-Angels-Terminator-Librarian-2014',
        ),
        (
            'blood-angels-captain',
            'Blood Angels Captain',
            43.50,
            '99120101416_BACaptain01.jpg',
            'https://www.warhammer.com/en-US/shop/blood-angels-captain-2024',
        ),
        (
            'codex-supplement-blood-angels',
            'Codex Supplement: Blood Angels',
            35.00,
            '60030101063_EngBACodex01.jpg',
            'https://www.warhammer.com/en-US/shop/codex-supplement-blood-angels-2024-eng',
        ),
    ],
    'Black Templars': [
        (
            'codex-supplement-black-templars',
            'Codex Supplement: Black Templars',
            35.00,
            '60030101065_ENGBlackTemplarsCodexHB1.jpg',
            'https://www.warhammer.com/en-US/shop/codex-supplement-black-templars-2025-eng',
        ),
    ],
    'Dark Angels': [
        (
            'dark-angels-interrogator-chaplain',
            'Dark Angels Interrogator-Chaplain',
            35.00,
            '99070101011_DarkAngelsInterrogatorChaplain01.jpg',
            'https://www.warhammer.com/en-US/shop/Dark-Angels-Interrogator-Chaplain-2017',
        ),
        (
            'dark-angels-ravenwing-bike-squadron',
            'Ravenwing Bike Squadron',
            60.00,
            '99120101050_BikeSquadNEW_01.jpg',
            'https://www.warhammer.com/en-US/shop/Dark-Angels-Ravenwing-Bike-Squadron',
        ),
        (
            'codex-supplement-dark-angels',
            'Codex Supplement: Dark Angels',
            35.00,
            '60030101062_ENGDACodex1.jpg',
            'https://www.warhammer.com/en-US/shop/codex-supplement-dark-angels-eng-2024',
        ),
    ],
    'Grey Knights': [
        (
            'grey-knights-castellan-crowe',
            'Castellan Crowe',
            48.00,
            '99120107015_GKCastellanCroweLead.jpg',
            'https://www.warhammer.com/en-US/shop/grey-knights-castellan-crowe-2022',
        ),
        (
            'grey-knights-purifier-squad',
            'Grey Knights Purifier Squad',
            69.00,
            '99120107018_PurifierLead.jpg',
            'https://www.warhammer.com/en-US/shop/Grey-Knights-Purifier-Squad-2022',
        ),
        (
            'grey-knights-purgation-squad',
            'Grey Knights Purgation Squad',
            69.00,
            '99120107018_PurgationLead.jpg',
            'https://www.warhammer.com/en-US/shop/Grey-Knights-Purgation-Squad-2022',
        ),
        (
            'grey-knights-interceptor-squad',
            'Grey Knights Interceptor Squad',
            69.00,
            '99120107018_InceptorLead.jpg',
            'https://www.warhammer.com/en-US/shop/Grey-Knights-Interceptor-Squad-2022',
        ),
        (
            'grey-knights-paladins',
            'Grey Knights Paladins',
            60.00,
            '99120107001_PaladinsSquadNEW01.jpg',
            'https://www.warhammer.com/en-US/shop/Grey-Knights-Paladins-2017',
        ),
        (
            'grey-knights-grand-master-nemesis-dreadknight',
            'Grand Master in Nemesis Dreadknight',
            82.00,
            '99120107023_GreyKnightsGrandmasterinNemesisDreadknightVehicle01.jpg',
            'https://www.warhammer.com/en-US/shop/grey-knights-grandmaster-in-nemesis-dreadknight-2025',
        ),
        (
            'codex-grey-knights',
            'Codex: Grey Knights',
            60.00,
            '60030107008_INTGreyKnightsBattletome01.jpg',
            'https://www.warhammer.com/en-US/shop/codex-grey-knights-2025-eng',
        ),
    ],
    'Space Wolves': [
        (
            'space-wolves-ulrik-the-slayer',
            'Ulrik the Slayer',
            39.00,
            '99070101019_UlrikTheSlayer01.jpg',
            'https://www.warhammer.com/en-US/shop/Space-Wolves-Ulrik-the-Slayer-2020',
        ),
        (
            'space-wolves-iron-priest',
            'Iron Priest',
            39.00,
            '99070101018_SpaceWolvesIronPriest01.jpg',
            'https://www.warhammer.com/en-US/shop/Space-Wolves-Iron-Priest-2020',
        ),
        (
            'space-wolves-wulfen',
            'Wulfen',
            65.00,
            '99120101140_SpaceWolvesWulfen01.jpg',
            'https://www.warhammer.com/en-US/shop/Space-Wolves-Wulfen-2020',
        ),
        (
            'space-wolves-venerable-dreadnought',
            'Space Wolves Venerable Dreadnought',
            65.00,
            '99120101116_SWVenerableDread01.jpg',
            'https://www.warhammer.com/en-US/shop/Space-Wolves-Venerable-Dreadnought-2020',
        ),
        (
            'space-wolves-fenrisian-wolves',
            'Fenrisian Wolves',
            43.50,
            '99120101252_FenrisianWolvesLead.jpg',
            'https://www.warhammer.com/en-US/shop/Fenrisian-Wolves-2020',
        ),
        (
            'space-wolves-murderfang',
            'Murderfang',
            65.00,
            '99120101116_Murderfang01.jpg',
            'https://www.warhammer.com/en-US/shop/Murderfang-2020',
        ),
        (
            'space-wolves-bjorn-fell-handed',
            'Bjorn the Fell-handed',
            65.00,
            '99120101116_BornFellhanded01.jpg',
            'https://www.warhammer.com/en-US/shop/Bjorn-the-Fellhanded-2020',
        ),
        (
            'space-wolves-wulfen-dreadnought',
            'Wulfen Dreadnought',
            65.00,
            '99120101116_Murderfang01.jpg',
            'https://www.warhammer.com/en-US/shop/wulfen-dreadnought-2025',
        ),
        (
            'space-wolves-wolf-priest',
            'Wolf Priest',
            42.00,
            '99120101435_SpaceWolvesWolfPriest1.jpg',
            'https://www.warhammer.com/en-US/shop/space-wolves-wolf-priest-2025',
        ),
        (
            'space-wolves-wolf-guard-battle-leader',
            'Wolf Guard Battle Leader',
            43.50,
            '99120101436_SpaceWolvesWolfGuardBattleLeader1.jpg',
            'https://www.warhammer.com/en-US/shop/space-wolves-wolf-guard-battle-leader-2025',
        ),
        (
            'space-wolves-blood-claws',
            'Blood Claws',
            65.00,
            '99120101434_SpaceWolvesBloodClaws1.jpg',
            'https://www.warhammer.com/en-US/shop/space-wolves-blood-claws-2025',
        ),
        (
            'space-wolves-arjac-rockfist',
            'Arjac Rockfist',
            47.00,
            '99120101439_SpaceWolvesArjacRockfist1.jpg',
            'https://www.warhammer.com/en-US/shop/space-wolves-arjac-rockfist-2025',
        ),
        (
            'space-wolves-njal-stormcaller',
            'Njal Stormcaller',
            47.00,
            '99120101440_SpaceWolvesNjalStormcaller1.jpg',
            'https://www.warhammer.com/en-US/shop/space-wolves-njal-stormcaller-2025',
        ),
        (
            'space-wolves-wolf-guard-headtakers',
            'Wolf Guard Headtakers',
            69.00,
            '99120101437_SpaceWolvesWolfGuardHeadtakers1.jpg',
            'https://www.warhammer.com/en-US/shop/space-wolves-wolf-guard-headtakers-2025',
        ),
        (
            'space-wolves-logan-grimnar',
            'Logan Grimnar',
            73.50,
            '99120101438_SpaceWolvesLoganGrimnar1.jpg',
            'https://www.warhammer.com/en-US/shop/space-wolves-logan-grimnar-2025',
        ),
        (
            'codex-supplement-space-wolves',
            'Codex Supplement: Space Wolves',
            35.00,
            '60030101064_EngSWCodex01.jpg',
            'https://www.warhammer.com/en-US/shop/codex-supplement-space-wolves-2025-eng',
        ),
    ],
}


class Command(BaseCommand):
    """Add faction-specific SM products for BA, BT, DA, GK, and SW (phase-3 pass)."""

    help = (
        'Adds 30 faction-specific Space Marine products for Blood Angels, Black Templars, '
        'Dark Angels, Grey Knights, and Space Wolves. These were missing after the original '
        'seed and phase-2 generic SM pass. Tagged phase-2. Seeds GW CurrentPrice. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        if not category_40k:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        total_created = 0
        total_updated = 0
        total_price_created = 0
        total_price_updated = 0

        for faction_name, products in PRODUCTS_BY_FACTION.items():
            faction = Faction.objects.filter(name=faction_name).first()
            if not faction:
                self.stderr.write(self.style.ERROR(
                    f'Faction "{faction_name}" not found — run populate_products first.'
                ))
                continue

            self.stdout.write(self.style.MIGRATE_HEADING(f'\n  ── {faction_name} ──'))

            for (slug, name, msrp, img_filename, gw_url) in products:
                image_url = _IMG.format(filename=img_filename)

                product, created = Product.objects.update_or_create(
                    slug=slug,
                    defaults={
                        'name': name,
                        'gw_sku': '',
                        'msrp': msrp,
                        'image_url': image_url,
                        'gw_url': gw_url,
                        'category': category_40k,
                        'faction': faction,
                        'is_active': True,
                        'batch_tag': 'phase-2',
                    },
                )
                status = 'Created' if created else 'Updated'
                self.stdout.write(self.style.SUCCESS(f'    {status}: {name} — ${msrp:.2f}'))
                if created:
                    total_created += 1
                else:
                    total_updated += 1

                if gw_retailer:
                    _, p_created = CurrentPrice.objects.update_or_create(
                        product=product,
                        retailer=gw_retailer,
                        defaults={
                            'price': msrp,
                            'url': gw_url,
                            'in_stock': True,
                            'not_available': False,
                            'listing_title': name,
                        },
                    )
                    if p_created:
                        total_price_created += 1
                    else:
                        total_price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_sm_phase3_products complete.\n'
            f'  Products: {total_created} created, {total_updated} updated.\n'
            f'  GW prices: {total_price_created} created, {total_price_updated} updated.'
        ))
