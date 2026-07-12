"""
Management command: seed_nk_battletech_prices

Seeds Noble Knight CurrentPrice records for BattleTech products.

90 of 114 products have a confirmed Noble Knight URL (52 from the original
Battletech - Noble Knight Games.xlsx sheet, 38 more found directly on NK's
site afterward). The remaining 24 products have no NK listing and are
intentionally left out, per the "blank row = no entry" rule.

Affiliate tag ?awid=1576 appended to all NK URLs.

Usage:
    python manage.py seed_nk_battletech_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    ('battletech-battle-of-tukayyid', 'Battle of Tukayyid', None, f'{_NK}/P/2147885068/Battle-of-Tukayyid{_AFF}', False, False),
    ('battletech-forcepack-black-remnant-command-lance', 'Forcepack - Black Remnant Command Lance', None, f'{_NK}/P/2148457182/Forcepack---Black-Remnant-Command-Lance{_AFF}', False, False),
    ('battletech-forcepack-second-star-league-assault-lance', 'Second Star League Assault Lance', None, f'{_NK}/P/2148279862/Second-Star-League-Assault-Lance{_AFF}', False, False),
    ('battletech-forcepack-house-davion-heavy-battle-lance', 'House Davion Heavy Battle Lance', None, f'{_NK}/P/2148279817/House-Davion-Heavy-Battle-Lance{_AFF}', False, False),
    ('battletech-salvage-box-urbanmech-lam', 'Salvage Box - Urbanmech Lam', None, f'{_NK}/P/2148165694/Salvage-Box---Urbanmech-Lam{_AFF}', False, False),
    ('battletech-mappack-grasslands', 'Map Set Grassland', None, f'{_NK}/P/2147749343/Map-Set-Grassland{_AFF}', False, False),
    ('battletech-forcepack-3rd-star-league-strike-team', 'Third Star League Strike Team Force Pack', None, f'{_NK}/P/2148276000/Third-Star-League-Strike-Team-Force-Pack{_AFF}', False, False),
    ('battletech-forcepack-urbanmech-lance', 'Forcepack - UrbanMech Lance', None, f'{_NK}/P/2148061852/Forcepack---UrbanMech-Lance{_AFF}', False, False),
    ('battletech-mappack-alien-worlds', 'Map Pack - Alien Worlds', None, f'{_NK}/P/2147963734/Map-Pack---Alien-Worlds{_AFF}', False, False),
    ('battletech-house-kurita-command-lance-forcepack', 'House Kurita Command Lance', None, f'{_NK}/P/2148414106/House-Kurita-Command-Lance{_AFF}', False, False),
    ('battletech-forcepack-proliferation-cycle', 'Forcepack - Proliferation Cycle', None, f'{_NK}/P/2148061851/Forcepack---Proliferation-Cycle{_AFF}', False, False),
    ('battletech-overlord-class-map-scale-dropship', 'Overlord Class Map Scale Dropship', None, f'{_NK}/P/2148280301/Overlord-Class-Map-Scale-Dropship{_AFF}', False, False),
    ('battletech-mappack-battle-of-tukayyid', 'Map Pack - Battle of Tukayyid', None, f'{_NK}/P/2147802336/Battle-of-Tukayyid-Map-Pack{_AFF}', False, False),
    ('battletech-kell-hounds-striker-lance', 'Kell Hounds Striker Lance', None, f'{_NK}/P/2148094861/Kell-Hounds-Striker-Lance{_AFF}', False, False),
    ('battletech-forcepack-gray-death-legion-heavy-battle-lance', 'Forcepack - Gray Death Legion Heavy Battle Lance', None, f'{_NK}/P/2148354345/Forcepack---Gray-Death-Legion-Heavy-Battle-Lance{_AFF}', False, False),
    ('battletech-forcepack-third-star-league-battle-group', 'Forcepack - Third Star League Battle Group', None, f'{_NK}/P/2148346589/Forcepack---Third-Star-League-Battle-Group{_AFF}', False, False),
    ('battletech-forcepack-recon-hunter-lances', 'Battlefield Support - Recon & Hunter Lances', None, f'{_NK}/P/2148203601/Battlefield-Support---Recon-and-Hunter-Lances{_AFF}', False, False),
    ('battletech-northwind-highlanders-command-lance', 'Northwind Highlanders Command Lance', None, f'{_NK}/P/2148037366/Northwind-Highlanders-Command-Lance{_AFF}', False, False),
    ('battletech-overlord-c-class-map-scale-dropship', 'Overlord C-Class Map Scale Dropship', None, f'{_NK}/P/2148280290/Overlord-C-Class-Map-Scale-Dropship{_AFF}', False, False),
    ('battletech-legendary-mechwarriors-iii-forcepack', 'Legendary Mechwarriors III', None, f'{_NK}/P/2148203606/Legendary-Mechwarriors-III{_AFF}', False, False),
    ('battletech-forcepack-clan-direct-fire-star', 'Mercenaries Pack - Clan Direct Fire Star', None, f'{_NK}/P/2148248808/Mercenaries-Pack---Clan-Direct-Fire-Star{_AFF}', False, False),
    ('battletech-house-kurita-ranger-lance-forcepack', 'House Kurita Ranger Lance', None, f'{_NK}/P/2148411534/House-Kurita-Ranger-Lance{_AFF}', False, False),
    ('battletech-forcepack-inner-sphere-recon-lance', 'Forcepack - Inner Sphere Recon Lance', None, f'{_NK}/P/2148254538/Forcepack---Inner-Sphere-Recon-Lance{_AFF}', False, False),
    ('battletech-forcepack-inner-sphere-security-lance', 'Inner Sphere Security Lance', None, f'{_NK}/P/2148203615/Inner-Sphere-Security-Lance{_AFF}', False, False),
    ('battletech-forcepack-assault-cavalry-lances', 'Battlefield Support - Assault & Cavalry Lances', None, f'{_NK}/P/2148203816/Battlefield-Support---Assault-and-Cavalry-Lances{_AFF}', False, False),
    ('battletech-battlefield-support-deck-revised', 'Battlefield Support Deck (Revised)', None, f'{_NK}/P/2148244268/Battlefield-Support-Deck-Revised{_AFF}', False, False),
    ('battletech-forcepack-support-emplacements', 'Battlefield Support - Emplacements', None, f'{_NK}/P/2148346586/Battlefield-Support---Emplacements{_AFF}', False, False),
    ('battletech-forcepack-eridani-light-horse-hunter-lance', 'Forcepack - Eridiani Light Horse Hunter Lance', None, f'{_NK}/P/2148094864/Forcepack---Eridiani-Light-Horse-Hunter-Lance{_AFF}', False, False),
    ('battletech-forcepack-inner-sphere-pursuit-lance', 'Inner Sphere Pursuit Lance', None, f'{_NK}/P/2148275995/Inner-Sphere-Pursuit-Lance{_AFF}', False, False),
    ('battletech-inner-sphere-heavy-recon-lance', 'Inner Sphere Heavy Recon Lance', None, f'{_NK}/P/2148275997/Inner-Sphere-Heavy-Recon-Lance{_AFF}', False, False),
    ('battletech-forcepack-inner-sphere-battle-armor-platoon', 'Inner Sphere Battle Armor Platoon', None, f'{_NK}/P/2148203613/Inner-Sphere-Battle-Armor-Platoon{_AFF}', False, False),
    ('battletech-legendary-mechwarriors-ii-forcepack', 'Legendary Mechwarriors II', None, f'{_NK}/P/2148289995/Legendary-Mechwarriors-II{_AFF}', False, False),
    ('battletech-forcepack-heavy-battle-sweep-lances', 'Battlefield Support - Heavy Battle & Sweep Lances', None, f'{_NK}/P/2148203603/Battlefield-Support---Heavy-Battle-and-Sweep-Lances{_AFF}', False, False),
    ('battletech-forcepack-inner-sphere-assault-lance', 'Inner Sphere Assault Lance', None, f'{_NK}/P/2148275996/Inner-Sphere-Assault-Lance{_AFF}', False, False),
    ('battletech-timber-wolf-c-scale', 'Timber Wolf C-Scale', None, f'{_NK}/P/2148453696/Timber-Wolf-C-Scale{_AFF}', False, False),
    ('battletech-mappack-volcanic', 'Map Pack - Volcanic', None, f'{_NK}/P/2148469696/Map-Pack---Volcanic{_AFF}', False, False),
    ('battletech-inner-sphere-command-lance', 'Forcepack - Inner Sphere Command Lance', None, f'{_NK}/P/2147852965/Miniature-Force-Pack---Inner-Sphere-Command-Lance{_AFF}', False, False),
    ('battletech-inner-sphere-battle-lance', 'Forcepack - Inner Sphere Battle Lance', None, f'{_NK}/P/2147852964/Miniature-Force-Pack---Inner-Sphere-Battle-Lance{_AFF}', False, False),
    ('battletech-inner-sphere-direct-fire-lance', 'Forcepack - Inner Sphere Direct Fire Lance', None, f'{_NK}/P/2147931638/Miniature-Force-Pack---Inner-Sphere-Direct-Fire-Lance{_AFF}', False, False),
    ('battletech-inner-sphere-heavy-lance', 'Forcepack - Inner Sphere Heavy Lance', None, f'{_NK}/P/2147950234/Miniature-Force-Pack---Inner-Sphere-Heavy-Lance{_AFF}', False, False),
    ('battletech-inner-sphere-fire-lance', 'Forcepack - Inner Sphere Fire Lance', None, f'{_NK}/P/2147950250/Miniature-Force-Pack---Inner-Sphere-Fire-Lance{_AFF}', False, False),
    ('battletech-inner-sphere-heavy-battle-lance', 'Forcepack - Inner Sphere Heavy Battle Lance', None, f'{_NK}/P/2147950259/Miniature-Force-Pack---Inner-Sphere-Heavy-Battle-Lance{_AFF}', False, False),
    ('battletech-inner-sphere-urban-lance', 'Forcepack - Inner Sphere Urban Lance', None, f'{_NK}/P/2147959636/Forcepack---Inner-Sphere-Urban-Lance{_AFF}', False, False),
    ('battletech-inner-sphere-support-lance', 'Forcepack - Inner Sphere Support Lance', None, f'{_NK}/P/2147961156/Forcepack---Inner-Sphere-Support-Lance{_AFF}', False, False),
    ('battletech-clan-command-star', 'Forcepack - Clan Command Star', None, f'{_NK}/P/2147852960/Miniature-Force-Pack---Clan-Command-Star{_AFF}', False, False),
    ('battletech-clan-heavy-striker-star', 'Forcepack - Clan Heavy Striker Star', None, f'{_NK}/P/2147852961/Miniature-Force-Pack---Clan-Heacy-Striker-Star{_AFF}', False, False),
    ('battletech-clan-heavy-star', 'Forcepack - Clan Heavy Star', None, f'{_NK}/P/2147950239/Miniature-Force-Pack---Clan-Heavy-Star{_AFF}', False, False),
    ('battletech-clan-support-star', 'Forcepack - Clan Support Star', None, f'{_NK}/P/2147952321/Forcepack---Clan-Suooprt-Star{_AFF}', False, False),
    ('battletech-clan-striker-star', 'Forcepack - Clan Striker Star', None, f'{_NK}/P/2147950244/Miniature-Force-Pack---Clan-Striker-Star{_AFF}', False, False),
    ('battletech-clan-ad-hoc-star', 'Forcepack - Clan Ad Hoc Star', None, f'{_NK}/P/2147959626/Forcepack---Clan-Ad-Hoc-Star{_AFF}', False, False),
    ('battletech-comstar-command-level-ii', 'Forcepack - ComStar Command Level II', None, f'{_NK}/P/2147950275/Miniature-Force-Pack---ComStar-Command-Level-II{_AFF}', False, False),
    ('battletech-mercenaries-snords-irregulars-assault-lance', 'Forcepack - Snord\'s Irregulars Assault Lance', None, f'{_NK}/P/2148061853/Forcepack---Snords-Irregulars-Assault-Lance{_AFF}', False, False),
    ('battletech-beginner-box', 'Battletech - Beginner Box (40th Anniversary Edition)', None, f'{_NK}/P/2148164786/Battletech---Beginner-Box-40th-Anniversary-Edition{_AFF}', False, False),
    ('battletech-campaign-operations', 'Campaign Operations (2021 Edition)', None, f'{_NK}/P/2147886587/Campaign-Operations-2021-Edition{_AFF}', False, False),
    ('battletech-a-game-of-armored-combat', 'Battletech - A Game of Armored Combat (2018 Edition)', None, f'{_NK}/P/2147742763/Battletech---A-Game-of-Armored-Combat-2018-Edition{_AFF}', False, False),
    ('battletech-mechwarrior-destiny', 'Mechwarrior - Destiny', None, f'{_NK}/P/2147812884/Mechwarrior---Destiny{_AFF}', False, False),
    ('battletech-tactical-operations-advanced-units-equipment', 'Tactical Operations - Advanced Units and Equipment (2023 Edition)', None, f'{_NK}/P/2148244229/Tactical-Operations---Advanced-Units-and-Equipment-2023-Edition{_AFF}', False, False),
    ('battletech-tactical-operations-advanced-rules', 'Tactical Operations - Advanced Rules (2023 Edition)', None, f'{_NK}/P/2148244224/Tactical-Operations---Advanced-Rules-2023-Edition{_AFF}', False, False),
    ('battletech-strategic-operations', 'Strategic Operations - Advanced Aerospace Rules (5th Printing)', None, f'{_NK}/P/2148244192/Strategic-Operations---Advanced-Aerospace-Rules-5th-Printing{_AFF}', False, False),
    ('battletech-hot-spots-hinterlands', 'Hot Spots - Hinterlands', None, f'{_NK}/P/2148220449/Hot-Spots---Hinterlands{_AFF}', False, False),
    ('battletech-star-league-command-lance', 'Star League Command Lance', None, f'{_NK}/P/2148455651/Star-League-Command-Lance{_AFF}', False, False),
    ('battletech-interstellar-operations-alternate-eras', 'Battletech Interstellar Operations - Alternate Eras (3rd Corrected Printing)', None, f'{_NK}/P/2148056022/Battletech-Interstellar-Operations---Alternate-Eras-3rd-Corrected-Printing{_AFF}', False, False),
    ('battletech-alpha-strike-box-set', 'Alpha Strike Box Set', None, f'{_NK}/P/2148006496/Alpha-Strike-Box-Set{_AFF}', False, False),
    ('battletech-interstellar-operations-battleforce', 'Battletech Interstellar Operations - Battleforce (2022 Printing)', None, f'{_NK}/P/2148209755/Battletech-Interstellar-Operations---Battleforce-2022-Printing{_AFF}', False, False),
    ('battletech-essentials', 'Battletech Essentials', None, f'{_NK}/P/2148169648/Battletech-Essentials{_AFF}', False, False),
    ('battletech-aces-scouring-sands', 'Aces - Scouring Sands (Campaign Box)', None, f'{_NK}/P/2148251072/Aces---Scouring-Sands-Campaign-Box{_AFF}', False, False),
    ('battletech-alpha-strike-clan-invasion-cards', 'Alpha Strike - Clan Invasion Cards', None, f'{_NK}/P/2147852245/Alpha-Strike---Clan-Invasion-Cards{_AFF}', False, False),
    ('battletech-counterspack-alpha-strike', 'Alpha Strike - Counters Pack', None, f'{_NK}/P/2148059945/Alpha-Strike---Counters-Pack{_AFF}', False, False),
    ('battletech-union-class-map-scale-dropship', 'Union-Class Map Scale Dropship', None, f'{_NK}/P/2148279787/Union-Class-Map-Scale-Dropship{_AFF}', False, False),
    ('battletech-house-davion-cavalry-lance-forcepack', 'House Davion Cavalry Lance Force Pack', None, f'{_NK}/P/2148273392/House-Davion-Cavalry-Lance-Force-Pack{_AFF}', False, False),
    ('battletech-counterspack-battleforce', 'Counters Pack - Battleforce', None, f'{_NK}/P/2147996526/Counters-Pack---Battleforce{_AFF}', False, False),
    ('battletech-gothic', 'BattleTech - Gothic', None, f'{_NK}/P/2148351462/BattleTech---Gothic{_AFF}', False, False),
    ('battletech-forcepack-rifle-command-lances', 'Battlefield Support - Rifle and Command Lances', None, f'{_NK}/P/2148203812/Battlefield-Support---Rifle-and-Command-Lances{_AFF}', False, False),
    ('battletech-forcepack-hansens-rough-riders-battle-lance', 'Hansens Roughriders Battle Lance', None, f'{_NK}/P/2148034485/Hansens-Roughriders-Battle-Lance{_AFF}', False, False),
    ('battletech-forcepack-clan-cavalry-star', 'Forcepack - Clan Cavalry Star', None, f'{_NK}/P/2148254536/Forcepack---Clan-Cavalry-Star{_AFF}', False, False),
    ('battletech-battlemat-twycross-plain-of-curtains-great-gash', 'Battle Mat - Legendary Battles - Twycross Plain of Curtains Great Gash', None, f'{_NK}/P/2148346540/Battle-Mat---Legendary-Battles---Twycross-Plain-of-Curtains-Great-Gash{_AFF}', False, False),
    ('battletech-map-pack-savannahs', 'Map Pack - Savannah', None, f'{_NK}/P/2148188344/Map-Pack---Savannah{_AFF}', False, False),
    ('battletech-map-pack-city', 'Map Pack - Cities', None, f'{_NK}/P/2148275992/Map-Pack---Cities{_AFF}', False, False),
    ('battletech-salvagebox-legendary-warriors-individual', 'Salvage Box - Legendary Warriors', None, f'{_NK}/P/2148457411/Salvage-Box---Legendary-Warriors{_AFF}', False, False),
    ('battletech-battlefield-support-objectives-forcepack', 'Battlefield Support - Objectives', None, f'{_NK}/P/2148203815/Battlefield-Support---Objectives{_AFF}', False, False),
    ('battletech-battlemat-legendary-battles-thunder-rift-misery', 'Battle Mat - Legendary Battles - Thunder Rift Misery', None, f'{_NK}/P/2148336021/Battle-Mat---Legendary-Battles---Thunder-Rift-Misery{_AFF}', False, False),
    ('battletech-somerset-strikers-forcepack', 'Mercenaries Force Pack - Somerset Strikers', None, f'{_NK}/P/2148279120/Mercenaries-Force-Pack---Somerset-Strikers{_AFF}', False, False),
    ('battletech-encounters', 'Encounters - Battletech', None, f'{_NK}/P/2148180096/Encounters---Battletech{_AFF}', False, False),
    ('battletech-battlemat-fire-and-ice-01-erupting-canyon', 'Battle Mat - Fire and Ice 01 - Erupting Canyon', None, f'{_NK}/P/2148469539/Battle-Mat---Fire-and-Ice-01---Erupting-Canyon{_AFF}', False, False),
    ('battletech-battlemat-savannah-large-lakes', 'Battle Mat - Savannah - Large Lakes Box Canyon', None, f'{_NK}/P/2148218033/Battle-Mat---Savannah---Large-Lakes-Box-Canyon{_AFF}', False, False),
    ('battletech-battlemat-savannah-desert-sinkholes', 'Battle Mat - Savannah - Sinkholes Battlemat', None, f'{_NK}/P/2148316224/Battle-Mat---Savannah---Sinkholes-Battlemat{_AFF}', False, False),
    ('battletech-gothic-salvage-box-individual-blind-box', 'Salvage Box - Gothic', None, f'{_NK}/P/2148351472/Salvage-Box---Gothic{_AFF}', False, False),
    ('battletech-battlemat-fire-and-ice-02-magma-fjords', 'Battle Mat - Fire and Ice 02 - Magma Fjords', None, f'{_NK}/P/2148484246/Battle-Mat---Fire-and-Ice-02---Magma-Fjords{_AFF}', False, False),
    ('battletech-inner-sphere-striker-lance', 'Miniatures Force Pack - Inner Sphere Striker Lance', None, f'{_NK}/P/2147934468/Miniatures-Force-Pack---Inner-Sphere-Striker-Lance{_AFF}', False, False),
    ('battletech-clan-elementals', 'Forcepack - Clan Elemental Star', None, f'{_NK}/P/2147876198/Forcepack---Clan-Elemental-Star{_AFF}', False, False),
    ('battletech-alpha-strike-commanders-edition', 'Alpha Strike - Commanders Edition (2023 Edition)', None, f'{_NK}/P/2148244067/Alpha-Strike---Commanders-Edition-2023-Edition{_AFF}', False, False),
    ('battletech-comstar-battle-level-ii', 'Forcepack - ComStar Battle Level II', None, f'{_NK}/P/2147959640/Forcepack---ComStar-Battle-Level-II{_AFF}', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for BattleTech products (idempotent)."""

    help = 'Seeds Noble Knight CurrentPrice records for BattleTech products.'

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
