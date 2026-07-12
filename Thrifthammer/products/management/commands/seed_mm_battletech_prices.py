"""
Management command: seed_mm_battletech_prices

Seeds Miniature Market CurrentPrice records for BattleTech products.

91 of 114 products have a confirmed Miniature Market URL (source: Battletech
- Miniatures Games _ Miniature Market.xlsx, matched by hand against the DB
product names -- the sheet has no SKU column). The remaining 23 products
have no MM listing and are intentionally left out.

Usage:
    python manage.py seed_mm_battletech_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

# (slug, listing_title, price, url, in_stock, not_available)
MM_PRICES = [
    ('battletech-alpha-strike-commanders-edition', 'BattleTech: Alpha Strike - Commander\'s Edition', None, 'https://www.miniaturemarket.com/cat35680.html', False, False),
    ('battletech-battle-of-tukayyid', 'BattleTech: Battle of Tukayyid (Hardcover)', None, 'https://www.miniaturemarket.com/cat35410.html', False, False),
    ('battletech-beginner-box', 'BattleTech: Beginner Box (2022)', None, 'https://www.miniaturemarket.com/cat35020m.html', False, False),
    ('battletech-campaign-operations', 'BattleTech: Campaign Operations (2021)', None, 'https://www.miniaturemarket.com/cat35007v.html', False, False),
    ('battletech-clan-invasion-salvage-box-93-designs', 'BattleTech: Clan Invasion Salvage Blind Box', None, 'https://www.miniaturemarket.com/cat36005.html', False, False),
    ('battletech-a-game-of-armored-combat', 'BattleTech: A Game of Armored Combat', None, 'https://www.miniaturemarket.com/cat3500d.html', False, False),
    ('battletech-mechwarrior-destiny', 'BattleTech: Mechwarrior - Destiny (Hardcover)', None, 'https://www.miniaturemarket.com/cat35185.html', False, False),
    ('battletech-tactical-operations-advanced-units-equipment', 'BattleTech: Tactical Operations - Advanced Units & Equipment (Hardcover)', None, 'https://www.miniaturemarket.com/cat35003vb.html', False, False),
    ('battletech-hot-spots-hinterlands', 'BattleTech: Hot Spots - Hinterlands', None, 'https://www.miniaturemarket.com/battletech-hot-spots-hinterlands-cat35450.html', False, False),
    ('battletech-star-league-command-lance', 'Battletech: Star League Command Lance', None, 'https://www.miniaturemarket.com/battletech-star-league-command-lance-cat35780.html', False, False),
    ('battletech-interstellar-operations-alternate-eras', 'BattleTech: Interstellar Operations - Alternate Eras', None, 'https://www.miniaturemarket.com/cat35006va.html', False, False),
    ('battletech-alpha-strike-box-set', 'BattleTech: Alpha Strike Box Set', None, 'https://www.miniaturemarket.com/cat35690.html', False, False),
    ('battletech-interstellar-operations-battleforce', 'BattleTech: Interstellar Operations - Battleforce', None, 'https://www.miniaturemarket.com/cat35006vb.html', False, False),
    ('battletech-forcepack-second-star-league-assault-lance', 'BattleTech: Second League Assault Lances', None, 'https://www.miniaturemarket.com/battletech-second-league-assault-lances-cat35781.html', False, False),
    ('battletech-aces-scouring-sands', 'BattleTech: Aces - Scouring Sands', None, 'https://www.miniaturemarket.com/BattleTech-Aces-Scouring-Sands/CAT35490', False, False),
    ('battletech-forcepack-house-davion-heavy-battle-lance', 'BattleTech: Miniature Force Pack - House Davion Heavy Battle Lance', None, 'https://www.miniaturemarket.com/battletech-miniature-force-pack-house-davion-heavy-battle-lance-cat35782.html', False, False),
    ('battletech-salvage-box-urbanmech-lam', 'BattleTech Salvage Box: UrbanMech LAM', None, 'https://www.miniaturemarket.com/battletech-salvage-box-urbanmech-lam-cat36012.html', False, False),
    ('battletech-mappack-grasslands', 'Battletech: Grasslands Map Set', None, 'https://www.miniaturemarket.com/cat35150.html', False, False),
    ('battletech-forcepack-3rd-star-league-strike-team', 'BattleTech: Miniature Force Pack - Third Star League Striker Team', None, 'https://www.miniaturemarket.com/battletech-miniature-force-pack-third-star-league-striker-team-cat35784.html', False, False),
    ('battletech-alpha-strike-clan-invasion-cards', 'BattleTech: Alpha - Clan Invasion Cards', None, 'https://www.miniaturemarket.com/cat35686.html', False, False),
    ('battletech-forcepack-urbanmech-lance', 'BattleTech: UrbanMech Lance', None, 'https://www.miniaturemarket.com/battletech-urbanmech-lance-cat35776.html', False, False),
    ('battletech-counterspack-alpha-strike', 'BattleTech: Counters Pack Alpha Strike', None, 'https://www.miniaturemarket.com/battletech-counters-pack-alpha-strike-cat35191.html', False, False),
    ('battletech-mercenaries-box-set', 'BattleTech: Mercenaries Box Set', None, 'https://www.miniaturemarket.com/battletech-mercenaries-box-set-cat35031.html', False, False),
    ('battletech-mappack-alien-worlds', 'BattleTech Map Pack: Alien Worlds', None, 'https://www.miniaturemarket.com/cat35153.html', False, False),
    ('battletech-union-class-map-scale-dropship', 'BattleTech: Union-Class Map-Scale DropShip', None, 'https://www.miniaturemarket.com/battletech-union-class-map-scale-dropship-cat357un.html', False, False),
    ('battletech-mappack-deserts', 'BattleTech Map Pack: Deserts', None, 'https://www.miniaturemarket.com/cat35154.html', False, False),
    ('battletech-initiative-deck', 'BattleTech: Initiative Deck', None, 'https://www.miniaturemarket.com/cat35885.html', False, False),
    ('battletech-house-davion-cavalry-lance-forcepack', 'BattleTech: Miniature Force Pack - House Davion Cavalry Lance', None, 'https://www.miniaturemarket.com/battletech-miniature-force-pack-house-davion-cavalry-lance-cat35783.html', False, False),
    ('battletech-battlemat-aerospace', 'BattleTech: Aerospace Mat', None, 'https://www.miniaturemarket.com/battletech-aerospace-mat-cat35800l.html', False, False),
    ('battletech-overlord-class-map-scale-dropship', 'BattleTech: Overlord-Class Map-Scale DropShip', None, 'https://www.miniaturemarket.com/battletech-overlord-class-map-scale-dropship-cat357ov.html', False, False),
    ('battletech-mappack-battle-of-tukayyid', 'BattleTech Map Pack: Battle of Tukayyid', None, 'https://www.miniaturemarket.com/cat35152.html', False, False),
    ('battletech-kell-hounds-striker-lance', 'BattleTech: Kell Hounds Striker Lance', None, 'https://www.miniaturemarket.com/battletech-kell-hounds-striker-lance-cat35766.html', False, False),
    ('battletech-counterspack-battleforce', 'BattleTech: Counters Pack - Battleforce', None, 'https://www.miniaturemarket.com/cat35190.html', False, False),
    ('battletech-forcepack-gray-death-legion-heavy-battle-lance', 'BattleTech: Gray Death Legion Heavy Battle Lance Pack', None, 'https://www.miniaturemarket.com/battletech-gray-death-legion-heavy-battle-lance-pack-cat35765.html', False, False),
    ('battletech-gothic', 'BattleTech Gothic', None, 'https://www.miniaturemarket.com/battletech-gothic-cat400000.html', False, False),
    ('battletech-forcepack-third-star-league-battle-group', 'BattleTech: Third Star League Battle Group', None, 'https://www.miniaturemarket.com/battletech-third-star-league-battle-group-cat35787.html', False, False),
    ('battletech-forcepack-recon-hunter-lances', 'BattleTech: Battlefield Support - Recon & Hunter Lances', None, 'https://www.miniaturemarket.com/battletech-battlefield-support-recon-hunter-lances-cat35753.html', False, False),
    ('battletech-northwind-highlanders-command-lance', 'BattleTech: Northwind Highlanders Command Lance', None, 'https://www.miniaturemarket.com/battletech-northwind-highlanders-command-lance-cat35767-284638.html', False, False),
    ('battletech-overlord-c-class-map-scale-dropship', 'BattleTech: Overlord C-Class Map-Scale DropShip', None, 'https://www.miniaturemarket.com/battletech-overlord-c-class-map-scale-dropship-cat357oc.html', False, False),
    ('battletech-legendary-mechwarriors-iii-forcepack', 'BattleTech: Legendary MechWarriors III', None, 'https://www.miniaturemarket.com/battletech-legendary-mechwarriors-iii-cat35769.html', False, False),
    ('battletech-forcepack-clan-direct-fire-star', 'BattleTech: The Clans Direct Fire Star', None, 'https://www.miniaturemarket.com/battletech-clans-direct-fire-star-cat35760.html', False, False),
    ('battletech-house-kurita-ranger-lance-forcepack', 'BattleTech: Miniature Force Pack - House Kurita Ranger Lance', None, 'https://www.miniaturemarket.com/battletech-miniature-force-pack-house-kurita-ranger-lance-cat35785.html', False, False),
    ('battletech-forcepack-inner-sphere-recon-lance', 'BattleTech: Inner Sphere Recon Lance', None, 'https://www.miniaturemarket.com/battletech-inner-sphere-recon-lance-cat35751.html', False, False),
    ('battletech-forcepack-inner-sphere-security-lance', 'BattleTech: Inner Sphere Security Lance', None, 'https://www.miniaturemarket.com/battletech-inner-sphere-security-lance-cat35754.html', False, False),
    ('battletech-forcepack-mccarrons-armored-cavalry-assault-lance', 'BattleTech: McCarron\'s Armored Cavalry Assault Lance Force Pack (Preorder)', None, 'https://www.miniaturemarket.com/BattleTech-McCarron-s-Armored-Cavalry-Assault-Lance-Force-Pack-Preorder/CAT35771', False, False),
    ('battletech-forcepack-rifle-command-lances', 'BattleTech: Battlefield Support - RIfle & Command Lances', None, 'https://www.miniaturemarket.com/battletech-battlefield-support-rifle-command-lances-cat35777.html', False, False),
    ('battletech-forcepack-hansens-rough-riders-battle-lance', 'BattleTech: Miniature Force Pack - Hansen\'s Roughriders Battle Lance', None, 'https://www.miniaturemarket.com/battletech-miniature-force-pack-hansens-roughriders-battle-lance-cat35764.html', False, False),
    ('battletech-forcepack-clan-cavalry-star', 'BattleTech: Clan Cavalry Star', None, 'https://www.miniaturemarket.com/battletech-clan-cavalry-star-cat35755.html', False, False),
    ('battletech-forcepack-assault-cavalry-lances', 'BattleTech: Battlefield Support - Assault & Cavalry Lances', None, 'https://www.miniaturemarket.com/battletech-battlefield-support-assault-cavalry-lances-cat35756.html', False, False),
    ('battletech-battlemat-twycross-plain-of-curtains-great-gash', 'BattleTech BattleMat: Legendary Battles - Twycross (Plain of Curtains & Great Gash)', None, 'https://www.miniaturemarket.com/battletech-battlemat-legendary-battles-twycross-cat35801h.html', False, False),
    ('battletech-battlefield-support-deck-revised', 'BattleTech: Battlefield Support Deck (Revised)', None, 'https://www.miniaturemarket.com/battletech-battlefield-support-deck-revised-cat35888r.html', False, False),
    ('battletech-map-pack-city', 'BattleTech Map Pack: City', None, 'https://www.miniaturemarket.com/battletech-map-pack-city-cat35155.html', False, False),
    ('battletech-forcepack-eridani-light-horse-hunter-lance', 'BattleTech: Miniature Force Pack - Eridani Light Horse Hunter Lance', None, 'https://www.miniaturemarket.com/battletech-miniature-force-pack-eridani-light-horse-hunter-lance-cat35763.html', False, False),
    ('battletech-forcepack-inner-sphere-pursuit-lance', 'BattleTech: Inner Sphere Pursuit Lance', None, 'https://www.miniaturemarket.com/battletech-inner-sphere-pursuit-lance-cat35752.html', False, False),
    ('battletech-inner-sphere-heavy-recon-lance', 'BattleTech: Inner Sphere Heavy Recon Lance', None, 'https://www.miniaturemarket.com/battletech-inner-sphere-heavy-recon-lance-cat35758.html', False, False),
    ('battletech-forcepack-inner-sphere-battle-armor-platoon', 'BattleTech: Inner Sphere Battle Armor Platoon', None, 'https://www.miniaturemarket.com/battletech-inner-sphere-battle-armor-platoon-cat35761.html', False, False),
    ('battletech-battlefield-support-objectives-forcepack', 'BattleTech: Battlefield Support - Objectives', None, 'https://www.miniaturemarket.com/battletech-battlefield-support-objectives-cat35762.html', False, False),
    ('battletech-legendary-mechwarriors-ii-forcepack', 'BattleTech: Legendary MechWarriors II', None, 'https://www.miniaturemarket.com/battletech-legendary-mechwarriors-ii-cat35768.html', False, False),
    ('battletech-forcepack-heavy-battle-sweep-lances', 'BattleTech: Battlefield Support - Heavy Battle & Sweep Lances', None, 'https://www.miniaturemarket.com/battletech-battlefield-support-heavy-battle-sweep-lances-cat35778.html', False, False),
    ('battletech-forcepack-inner-sphere-assault-lance', 'BattleTech: Inner Sphere Assault Lance', None, 'https://www.miniaturemarket.com/battletech-inner-sphere-assault-lance-cat35757.html', False, False),
    ('battletech-timber-wolf-c-scale', 'BattleTech: Timber Wolf C- Scale', None, 'https://www.miniaturemarket.com/BattleTech-Timber-Wolf-C-Scale/CAT37801C', False, False),
    ('battletech-mappack-volcanic', 'BattleTech Map Pack: Volcanic', None, 'https://www.miniaturemarket.com/BattleTech-Map-Pack-Volcanic/CAT35157', False, False),
    ('battletech-somerset-strikers-forcepack', 'BattleTech: 1st Somerset Strikers', None, 'https://www.miniaturemarket.com/battletech-1st-somerset-strikers-cat35779.html', False, False),
    ('battletech-battlemat-fire-and-ice-01-erupting-canyon', 'BattleTech BattleMat: Fire & Ice 01 - Erupting Canyon', None, 'https://www.miniaturemarket.com/BattleTech-BattleMat-Fire-Ice-01-Erupting-Canyon/CAT35801J', False, False),
    ('battletech-battlemat-savannah-large-lakes', 'BattleTech BattleMat: Savannah - Large Lakes/Box Canyon', None, 'https://www.miniaturemarket.com/battletech-battlemat-savannah-large-lakesbox-canyon-cat35801a.html', False, False),
    ('battletech-battlemat-savannah-desert-sinkholes', 'BattleTech BattleMat: Savannah - Sinkholes/Mountain Lake', None, 'https://www.miniaturemarket.com/battletech-battlemat-savannah-sinkholesmountain-lake-cat35801c.html', False, False),
    ('battletech-gothic-salvage-box-individual-blind-box', 'BattleTech Gothic: Salvage Box', None, 'https://www.miniaturemarket.com/BattleTech-Gothic-Salvage-Box/CAT40002', False, False),
    ('battletech-battlemat-fire-and-ice-02-magma-fjords', 'BattleTech BattleMat: Fire & Ice 02 - Magma Fjords (New Arrival)', None, 'https://www.miniaturemarket.com/BattleTech-BattleMat-Fire-Ice-02-Magma-Fjords-New-Arrival/CAT35801K', False, False),
    ('battletech-inner-sphere-command-lance', 'BattleTech: Miniature Force Pack - Inner Sphere Command Lance', None, 'https://www.miniaturemarket.com/cat35721.html', False, False),
    ('battletech-inner-sphere-battle-lance', 'BattleTech: Miniature Force Pack - Inner Sphere Battle Lance', None, 'https://www.miniaturemarket.com/cat35723.html', False, False),
    ('battletech-inner-sphere-direct-fire-lance', 'BattleTech: Miniature Force Pack - Inner Sphere Direct Fire Lance', None, 'https://www.miniaturemarket.com/cat35725.html', False, False),
    ('battletech-inner-sphere-heavy-lance', 'BattleTech: Miniature Force Pack - Inner Sphere Heavy Lance', None, 'https://www.miniaturemarket.com/cat35727.html', False, False),
    ('battletech-inner-sphere-striker-lance', 'BattleTech: Miniature Force Pack - Inner Sphere Striker Lance', None, 'https://www.miniaturemarket.com/cat35729.html', False, False),
    ('battletech-inner-sphere-fire-lance', 'BattleTech: Miniature Force Pack - Inner Sphere Fire Lance', None, 'https://www.miniaturemarket.com/cat35731.html', False, False),
    ('battletech-inner-sphere-heavy-battle-lance', 'Battletech: Inner Sphere - Heavy Battle Lance', None, 'https://www.miniaturemarket.com/cat35733.html', False, False),
    ('battletech-inner-sphere-urban-lance', 'BattleTech: Miniature Force Pack - Inner Sphere Urban Lance', None, 'https://www.miniaturemarket.com/cat35735.html', False, False),
    ('battletech-inner-sphere-support-lance', 'BattleTech: Miniature Force Pack - Inner Sphere Support Lance', None, 'https://www.miniaturemarket.com/cat35736.html', False, False),
    ('battletech-clan-command-star', 'BattleTech: Miniature Force Pack - Clan Command Star', None, 'https://www.miniaturemarket.com/cat35720.html', False, False),
    ('battletech-clan-heavy-striker-star', 'BattleTech: Miniature Force Pack - Clan Heavy Striker Star', None, 'https://www.miniaturemarket.com/cat35722.html', False, False),
    ('battletech-clan-fire-star', 'BattleTech: Miniature Force Pack - Clan Fire Star', None, 'https://www.miniaturemarket.com/cat35724.html', False, False),
    ('battletech-clan-heavy-star', 'BattleTech: Miniature Force Pack - Clan Heavy Star', None, 'https://www.miniaturemarket.com/cat35730.html', False, False),
    ('battletech-clan-support-star', 'BattleTech: Miniature Force Pack - Clan Support Star', None, 'https://www.miniaturemarket.com/cat35726.html', False, False),
    ('battletech-clan-striker-star', 'BattleTech: Miniature Force Pack - Clan Striker Star', None, 'https://www.miniaturemarket.com/cat35732.html', False, False),
    ('battletech-clan-ad-hoc-star', 'BattleTech: Miniature Force Pack - Clan Ad Hoc Star', None, 'https://www.miniaturemarket.com/cat35734.html', False, False),
    ('battletech-comstar-command-level-ii', 'BattleTech: ComStar Command Level II', None, 'https://www.miniaturemarket.com/cat35737.html', False, False),
    ('battletech-comstar-battle-level-ii', 'BattleTech: Comstar Battle Level II', None, 'https://www.miniaturemarket.com/cat35738.html', False, False),
    ('battletech-mercenaries-wolf-dragoons-assault-star', 'BattleTech: Miniature Force Pack - Wolf\'s Dragoons Assault Star', None, 'https://www.miniaturemarket.com/battletech-miniature-force-pack-wolfs-dragoons-assault-star-cat35741.html', False, False),
    ('battletech-mercenaries-snords-irregulars-assault-lance', 'BattleTech: Snord\'s Irregulars Assault Lance', None, 'https://www.miniaturemarket.com/battletech-snords-irregulars-assault-lance-cat35770.html', False, False),
    ('battletech-battlemat-grasslands', 'BattleTech BattleMat: FieldTech - BattleTech Grasslands/Desert', None, 'https://www.miniaturemarket.com/battletech-battlemat-fieldtech-battletech-grasslandsdesert-cat35801f.html', False, False),
    ('battletech-battlemat-alpha-strike', 'BattleTech BattleMat: FieldTech - Alpha Strike Lunar/ Alpha Strike City', None, 'https://www.miniaturemarket.com/battletech-battlemat-fieldtech-alpha-strike-lunar-alpha-strike-city-cat35801e.html', False, False),
    ('battletech-forcepack-proliferation-cycle', 'BattleTech: Proliferation Cycle Miniatures Box', None, 'https://www.miniaturemarket.com/battletech-proliferation-cycle-miniatures-box-cat35775.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market prices for BattleTech products (idempotent)."""

    help = 'Seeds Miniature Market CurrentPrice records for BattleTech products.'

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
