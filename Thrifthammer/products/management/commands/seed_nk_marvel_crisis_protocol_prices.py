"""
Management command: seed_nk_marvel_crisis_protocol_prices

Seeds Noble Knight CurrentPrice records for Marvel Crisis Protocol products.

67 of 73 products have a confirmed Noble Knight URL (49 found in the Noble
Knight Excel scrape, 18 more found directly on NK's site by hand). The
remaining 6 products have no NK listing and are intentionally left out, per
the "blank row = no entry" rule.

Affiliate tag ?awid=1576 appended to all NK URLs.

Usage:
    python manage.py seed_nk_marvel_crisis_protocol_prices
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_NK = 'https://www.nobleknight.com'
_AFF = '?awid=1576'

# (slug, listing_title, price, url, in_stock, not_available)
NK_PRICES = [
    ('marvel-crisis-protocol-x-men-starter-set', 'X-Men Starter Set', None, f'{_NK}/P/2148371594/X-Men-Starter-Set{_AFF}', False, False),
    ('marvel-crisis-protocol-bastion-nimrod-omega-sentinel', 'Character Pack - Bastion, Nimrod & Omega Sentinel', None, f'{_NK}/P/2148454836/Character-Pack---Bastion-Nimrod-and-Omega-Sentinel{_AFF}', False, False),
    ('marvel-crisis-protocol-prowler-spider-man-2099-ultimate-spider-man', 'Character Pack - Prowler, Spider-Man 2099 & Ultimate Spider-Man', None, f'{_NK}/P/2148359708/Character-Pack---Prowler-Spider-Man-2099-and-Ultimate-Spider-Man{_AFF}', False, False),
    ('marvel-crisis-protocol-phoenix-phoenix-unleashed', 'Character Pack - Phoenix & Phoenix Unleashed', None, f'{_NK}/P/2148312258/Character-Pack---Phoenix-and-Phoenix-Unleashed{_AFF}', False, False),
    ('marvel-crisis-protocol-spider-foes-starter-set', 'Spider Foes Starter Set', None, f'{_NK}/P/2148371593/Spider-Foes-Starter-Set{_AFF}', False, False),
    ('marvel-crisis-protocol-silk-spider-ham-spider-man-noir', 'Character Pack - Silk, Spider-Ham & Spider-Man Noir', None, f'{_NK}/P/2148359714/Character-Pack---Silk-Spider-Ham-and-Spider-Man-Noir{_AFF}', False, False),
    ('marvel-crisis-protocol-operation-zero-tolerance-character-crisis-card-pack', 'Character Pack - Operation Zero Tolerance', None, f'{_NK}/P/2148468303/Character-Pack---Operation-Zero-Tolerance{_AFF}', False, False),
    ('marvel-crisis-protocol-bishop-nightcrawler', 'Character Pack - Bishop & Nightcrawler', None, f'{_NK}/P/2148125556/Character-Pack---Bishop-and-Nightcrawler{_AFF}', False, False),
    ('marvel-crisis-protocol-iron-lad-iron-monger-kang-the-conqueror-rescue', 'Character Pack - Iron Lad, Iron Monger, Kang the Conqueror & Rescue', None, f'{_NK}/P/2148415024/Character-Pack---Iron-Lad-Iron-Monger-Kang-the-Conqueror-and-Rescue{_AFF}', False, False),
    ('marvel-crisis-protocol-iceman-shadowcat', 'Character Pack - Iceman & Shadowcat', None, f'{_NK}/P/2148125546/Character-Pack---Iceman-and-Shadowcat{_AFF}', False, False),
    ('marvel-crisis-protocol-adam-warlock-moondragon-quasar', 'Character Pack - Adam Warlock, Moondragon, & Quasar', None, f'{_NK}/P/2148396244/Character-Pack---Adam-Warlock-Moondragon-and-Quasar{_AFF}', False, False),
    ('marvel-crisis-protocol-apocalypse', 'Character Pack - Apocalypse', None, f'{_NK}/P/2148179460/Character-Pack---Apocalypse{_AFF}', False, False),
    ('marvel-crisis-protocol-monsters-unleashed-character-pack', 'Character Pack - Monsters Unleashed', None, f'{_NK}/P/2148198737/Character-Pack---Monsters-Unleashed{_AFF}', False, False),
    ('marvel-crisis-protocol-war-of-kings-character-and-crisis-card-pack', 'Character Pack - War of Kings', None, f'{_NK}/P/2148258900/Character-Pack---War-of-Kings{_AFF}', False, False),
    ('marvel-crisis-protocol-xaviers-students-affiliation-pack', 'Affiliation Pack - Xavier\'s Students', None, f'{_NK}/P/2148397925/Affiliation-Pack---Xaviers-Students{_AFF}', False, False),
    ('marvel-crisis-protocol-web-swinging-heroes', 'Affiliation Pack - Web-Swinging Heroes', None, f'{_NK}/P/2148359705/Affiliation-Pack---Web-Swinging-Heroes{_AFF}', False, False),
    ('marvel-crisis-protocol-professor-x-shadow-king', 'Character Pack - Professor X & Shadow King', None, f'{_NK}/P/2148125552/Character-Pack---Professor-X-and-Shadow-King{_AFF}', False, False),
    ('marvel-crisis-protocol-angel-archangel', 'Character Pack - Angel & Archangel', None, f'{_NK}/P/2148179461/Character-Pack---Angel-and-Archangel{_AFF}', False, False),
    ('marvel-crisis-protocol-avalanche-exodus-lady-mastermind', 'Character Pack - Avalanche, Exodus, & Lady Mastermind', None, f'{_NK}/P/2148322555/Character-Pack---Avalanche-Exodus-and-Lady-Mastermind{_AFF}', False, False),
    ('marvel-crisis-protocol-echo-ronin-tigra', 'Character Pack - Echo, Ronin & Tigra', None, f'{_NK}/P/2148359712/Character-Pack---Echo-Ronin-and-Tigra{_AFF}', False, False),
    ('marvel-crisis-protocol-abomination-wrecking-crew', 'Character Pack - Abomination & Wrecking Crew', None, f'{_NK}/P/2148198774/Character-Pack---Abomination-and-Wrecking-Crew{_AFF}', False, False),
    ('marvel-crisis-protocol-tomb-of-dracula-terrain-pack', 'Terrain Pack - Tomb of Dracula', None, f'{_NK}/P/2148198742/Terrain-Pack---Tomb-of-Dracula{_AFF}', False, False),
    ('marvel-crisis-protocol-guardians-of-the-galaxy-starter-set', 'Starter Set - Guardians of the Galaxy', None, f'{_NK}/P/2148473517/Starter-Set---Guardians-of-the-Galaxy{_AFF}', False, False),
    ('marvel-crisis-protocol-guardians-of-the-galaxy-affiliation-pack', 'Affiliation Pack - Guardians of the Galaxy', None, f'{_NK}/P/2148258915/Affiliation-Pack---Guardians-of-the-Galaxy{_AFF}', False, False),
    ('marvel-crisis-protocol-rejuvenation-chamber-ultimate-encounter', 'Terrain Pack - Rejuvenation Chamber Ultimate Encounter', None, f'{_NK}/P/2148179464/Terrain-Pack---Rejuvenation-Chamber-Ultimate-Encounter{_AFF}', False, False),
    ('marvel-crisis-protocol-asgardians-starter-set', 'Starter Set - Asgardians', None, f'{_NK}/P/2148473529/Starter-Set---Asgardians{_AFF}', False, False),
    ('marvel-crisis-protocol-the-galaxys-deadliest-character-pack', 'Character Pack - The Galaxy\'s Deadliest', None, f'{_NK}/P/2148258914/Character-Pack---The-Galaxys-Deadliest{_AFF}', False, False),
    ('marvel-crisis-protocol-shield-affiliation-pack', 'Affiliation Pack - S.H.I.E.L.D.', None, f'{_NK}/P/2148454838/Affiliation-Pack---SHIELD{_AFF}', False, False),
    ('marvel-crisis-protocol-criminal-syndicate-affiliation-pack', 'Affiliation Pack - Criminal Syndicate', None, f'{_NK}/P/2148323106/Affiliation-Pack---Criminal-Syndicate{_AFF}', False, False),
    ('marvel-crisis-protocol-dark-future-terrain-pack', 'Terrain Pack - Dark Future', None, f'{_NK}/P/2148179463/Terrain-Pack---Dark-Future{_AFF}', False, False),
    ('marvel-crisis-protocol-shrine-to-en-sabah-nur-terrain-pack', 'Terrain Pack - Shrine to En Sabah Nur', None, f'{_NK}/P/2148179465/Terrain-Pack---Shrine-to-En-Sabah-Nur{_AFF}', False, False),
    ('marvel-crisis-protocol-convocation-affiliation-pack', 'Affiliation Pack - Convocation', None, f'{_NK}/P/2148342467/Affiliation-Pack---Convocation{_AFF}', False, False),
    ('marvel-crisis-protocol-rival-panels-battle-for-the-throne', 'Rival Panels - Battle for the Throne', None, f'{_NK}/P/2148112861/Rival-Panels---Battle-for-the-Throne{_AFF}', False, False),
    ('marvel-crisis-protocol-movement-range-tool-pack', 'Movement & Range Tool Pack', None, f'{_NK}/P/2148086998/Movement-and-Range-Tool-Pack{_AFF}', False, False),
    ('marvel-crisis-protocol-dice-pack', 'Crisis Protocol Dice Pack (10)', None, f'{_NK}/P/2147772019/Crisis-Protocol-Dice-Pack-10{_AFF}', False, False),
    ('marvel-crisis-protocol-asgardian-shrine-terrain-pack', 'Terrain Pack - Asgardian Shrine', None, f'{_NK}/P/2148175377/Terrain-Pack---Asgardian-Shrine{_AFF}', False, False),
    ('marvel-crisis-protocol-dimensional-terror-terrain-pack', 'Terrain Pack - Dimensional Terror', None, f'{_NK}/P/2148473521/Terrain-Pack---Dimensional-Terror{_AFF}', False, False),
    ('marvel-crisis-protocol-battle-for-asgard-terrain-pack', 'Terrain Pack - Battle for Asgard', None, f'{_NK}/P/2148175373/Terrain-Pack---Battle-for-Asgard{_AFF}', False, False),
    ('marvel-crisis-protocol-inhumans-affiliation-pack', 'Affiliation Pack - Inhumans', None, f'{_NK}/P/2148397926/Affiliation-Pack---Inhumans{_AFF}', False, False),
    ('marvel-crisis-protocol-dark-dimension-incursion-terrain-pack', 'Terrain Pack - Dark Dimension Incursion', None, f'{_NK}/P/2148473519/Terrain-Pack---Dark-Dimension-Incursion{_AFF}', False, False),
    ('marvel-crisis-protocol-spider-foes-affiliation-pack', 'Affiliation Pack - Spider-Foes', None, f'{_NK}/P/2148132318/Affiliation-Pack---Spider-Foes{_AFF}', False, False),
    ('marvel-crisis-protocol-dormammu-ultimate-encounter', 'Character Pack - Dormammu Ultimate Encounter (2026 Edition)', None, f'{_NK}/P/2148425733/Character-Pack---Dormammu-Ultimate-Encounter-2026-Edition{_AFF}', False, False),
    ('marvel-crisis-protocol-icons-of-bast-terrain-pack', 'Terrain Pack - Icons of Bast', None, f'{_NK}/P/2148112573/Terrain-Pack---Icons-of-Bast{_AFF}', False, False),
    ('marvel-crisis-protocol-warriors-of-asgard-affiliation-pack', 'Affiliation Pack - Warriors of Asgard', None, f'{_NK}/P/2148324806/Affiliation-Pack---Warriors-of-Asgard{_AFF}', False, False),
    ('marvel-crisis-protocol-movement-range-tools', 'Movement & Range Tool Pack', None, f'{_NK}/P/2148086998/Movement-and-Range-Tool-Pack{_AFF}', False, False),
    ('marvel-crisis-protocol-kingdom-of-wakanda-terrain-pack', 'Kingdom of Wakanda Terrain Pack', None, f'{_NK}/P/2148112574/Kingdom-of-Wakanda-Terrain-Pack{_AFF}', False, False),
    ('marvel-crisis-protocol-avengers-affiliation-pack', 'Affiliation Pack - Avengers', None, f'{_NK}/P/2148132329/Affiliation-Pack---Avengers{_AFF}', False, False),
    ('marvel-crisis-protocol-cabal-affiliation-pack', 'Affiliation Pack - Cabal', None, f'{_NK}/P/2148132328/Affiliation-Pack---Cabal{_AFF}', False, False),
    ('marvel-crisis-protocol-hydra-tank-terrain-ultimate-encounter', 'Terrain & Ultimate Encounter Pack - Hydra Tank', None, f'{_NK}/P/2148029665/Terrain-and-Ultimate-Encounter-Pack---Hydra-Tank{_AFF}', False, False),
    ('marvel-crisis-protocol-gwenom-scarlet-spider', 'Character Pack - Gwenom & Scarlet Spider', None, f'{_NK}/P/2148132356/Character-Pack---Gwenom-and-Scarlet-Spider{_AFF}', False, False),
    ('marvel-crisis-protocol-elsa-bloodstone-man-thing', 'Character Pack - Elsa Bloodstone & Man-Thing', None, f'{_NK}/P/2148252075/Character-Pack---Elsa-Bloodstone-and-Man-Thing{_AFF}', False, False),
    ('marvel-crisis-protocol-mighty-thor-lady-sif-thor-hero-of-midgard-loki-prince-of-lies', 'Character Pack - Mighty Thor, Lady Sif, Thor, Hero of Midgard, & Loki, Prince of Lies', None, f'{_NK}/P/2148175371/Character-Pack---Mighty-Thor-Lady-Sif-Thor-Hero-of-Midgard-and-Loki-Prince-of-Lies{_AFF}', False, False),
    ('marvel-crisis-protocol-valkyrie-on-elendil-warriors-three', 'Character Pack - Valkyrie on Elendil & Warriors Three', None, f'{_NK}/P/2148396245/Character-Pack---Valkyrie-on-Elendil-and-Warriors-Three{_AFF}', False, False),
    ('marvel-crisis-protocol-yondu-nova', 'Character Pack - Yondu & Nova', None, f'{_NK}/P/2148252074/Character-Pack---Yondu-and-Nova{_AFF}', False, False),
    ('marvel-crisis-protocol-earths-mightiest-core-set', 'Earth\'s Mightiest Core Set', None, f'{_NK}/P/2148077661/Earths-Mightiest-Core-Set{_AFF}', False, False),
    ('marvel-crisis-protocol-black-panther-chosen-of-bast-namor-the-sub-mariner', 'Character Pack - Black Panther, Chosen of Bast & Namor, the Sub-Mariner', None, f'{_NK}/P/2148166575/Character-Pack---Black-Panther-Chosen-of-Bast-and-Namor-the-Sub-Mariner{_AFF}', False, False),
    ('marvel-crisis-protocol-defenders-affiliation-pack', 'Affiliation Pack - Defenders', None, f'{_NK}/P/2148324805/Affiliation-Pack---Defenders{_AFF}', False, False),
    ('marvel-crisis-protocol-shang-chi-silver-sable', 'Character Pack - Shang Chi & Silver Sable', None, f'{_NK}/P/2148166573/Character-Pack---Shang-Chi-and-Silver-Sable{_AFF}', False, False),
    ('marvel-crisis-protocol-sentinels-affiliation-pack', 'Affiliation Pack - Sentinels', None, f'{_NK}/P/2148396280/Affiliation-Pack---Sentinels{_AFF}', False, False),
    ('marvel-crisis-protocol-mojo-ball-scenario-pack', 'Scenario Pack - Mojo Ball', None, f'{_NK}/P/2148169668/Scenario-Pack---Mojo-Ball{_AFF}', False, False),
    ('marvel-crisis-protocol-x-force-affiliation-pack', 'Affiliation Pack - X-Force', None, f'{_NK}/P/2148396247/Affiliation-Pack---X-Force{_AFF}', False, False),
    ('marvel-crisis-protocol-blue-marvel-spectrum', 'Character Pack - Blue Marvel & Spectrum', None, f'{_NK}/P/2148391316/Character-Pack---Blue-Marvel-and-Spectrum{_AFF}', False, False),
    ('marvel-crisis-protocol-inhuman-royal-court', 'Character Pack - Inhuman Royal Court', None, f'{_NK}/P/2148258901/Character-Pack---Inhuman-Royal-Court{_AFF}', False, False),
    ('marvel-crisis-protocol-weapon-x-maverick', 'Character Pack - Weapon X & Maverick', None, f'{_NK}/P/2148179456/Character-Pack---Weapon-X-and-Maverick{_AFF}', False, False),
    ('marvel-crisis-protocol-nyc-city-block-terrain-collection', 'NYC City Block Terrain Collection', None, f'{_NK}/P/2148362556/NYC-City-Block-Terrain-Collection{_AFF}', False, False),
    ('marvel-crisis-protocol-sunspot-warlock', 'Character Pack - Sunspot & Warlock', None, f'{_NK}/P/2148179458/Character-Pack---Sunspot-and-Warlock{_AFF}', False, False),
    ('marvel-crisis-protocol-mephisto', 'Character Pack - Mephisto', None, f'{_NK}/P/2148210140/Character-Pack---Mephisto{_AFF}', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight prices for Marvel Crisis Protocol products (idempotent)."""

    help = 'Seeds Noble Knight CurrentPrice records for Marvel Crisis Protocol products.'

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
