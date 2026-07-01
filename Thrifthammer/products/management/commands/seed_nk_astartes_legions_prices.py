"""
Management command: seed_nk_astartes_legions_prices

Seeds Noble Knight URLs for Astartes Legions products.

51 of 63 AL SKUs have confirmed NK listings. Omitted (no NK listing):
AL-002, AL-005, AL-021, AL-022, AL-045, AL-046, AL-047, AL-048,
AL-050, AL-051, AL-056, AL-060.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_nk_astartes_legions_prices
"""

from django.core.management.base import BaseCommand

NK_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('warhammer-the-horus-heresy-saturnine', 'Age of Darkness - Saturnine', None, 'https://www.nobleknight.com/P/2148327794/Age-of-Darkness---Saturnine?awid=1576', False, False),
    ('liber-astartes-loyalist-legiones-astartes-army-book', 'Liber Astartes - Loyalist Legiones Astartes Army Book', None, 'https://www.nobleknight.com/P/2148327749/Liber-Astartes---Loyalist-Legiones-Astartes-Army-Book?awid=1576', False, False),
    ('legiones-astartes-combat-force', 'Legiones Astartes Combat Force', None, 'https://www.nobleknight.com/P/2148356741/Legiones-Astartes-Combat-Force?awid=1576', False, False),
    ('falchion-super-heavy-tank-destroyer', 'Falchion Super-Heavy Tank Destroyer', None, 'https://www.nobleknight.com/P/2148472864/Falchion-Super-Heavy-Tank-Destroyer?awid=1576', False, False),
    ('spartan-prometheus-assault-tank', 'Spartan Prometheus Assault Tank', None, 'https://www.nobleknight.com/P/2148472866/Spartan-Prometheus-Assault-Tank?awid=1576', False, False),
    ('mkii-tactical-squad', 'Mark II Tactical Squad', None, 'https://www.nobleknight.com/P/2148327807/Mark-II-Tactical-Squad?awid=1576', False, False),
    ('legion-praetor-with-power-axe', 'Legiones Astartes Praetor w/ Power Axe', None, 'https://www.nobleknight.com/P/2147996303/Legiones-Astartes-Praetor-w-Power-Axe?awid=1576', False, False),
    ('legion-praetor-with-power-sword', 'Legiones Astartes Praetor w/ Power Sword', None, 'https://www.nobleknight.com/P/2147996302/Legiones-Astartes-Praetor-w-Power-Sword?awid=1576', False, False),
    ('legion-cataphractii-praetor-and-chaplain-consul', 'Legion Praetor and Chaplain Consul', None, 'https://www.nobleknight.com/P/2147988721/Legion-Praetor-and-Chaplain-Consul?awid=1576', False, False),
    ('legion-tartaros-terminator-squad', 'Legion Tartaros Terminator Squad', None, 'https://www.nobleknight.com/P/2147996293/Legion-Tartaros-Terminator-Squad?awid=1576', False, False),
    ('geigor-fell-hand', 'Geigor Fell-Hand', None, 'https://www.nobleknight.com/P/2147988720/Geigor-Fell-Hand?awid=1576', False, False),
    ('dominion-zephon', 'Dominion Zephon', None, 'https://www.nobleknight.com/P/2147961109/Dominion-Zephon?awid=1576', False, False),
    ('fafnir-rann', 'Fafnir Rann', None, 'https://www.nobleknight.com/P/2147961108/Fafnir-Rann?awid=1576', False, False),
    ('breacher-squad-upgrade-set', 'Breacher Squad Upgrade Set', None, 'https://www.nobleknight.com/P/2148407523/Breacher-Squad-Upgrade-Set?awid=1576', False, False),
    ('mkiii-breacher-squad', 'MKIII Breacher Squad', None, 'https://www.nobleknight.com/P/2148407520/MKIII-Breacher-Squad?awid=1576', False, False),
    ('cataphractii-terminators-with-combi-bolters-and-power-fists', 'Cataphracti Terminators w/ Combi-Bolters and Power Fists', None, 'https://www.nobleknight.com/P/2148407516/Cataphracti-Terminators-w-Combi-Bolters-and-Power-Fists?awid=1576', False, False),
    ('mkii-assault-squad', 'Legiones Astartes MKII Assault Squad', None, 'https://www.nobleknight.com/P/2148352468/Legiones-Astartes-MKII-Assault-Squad?awid=1576', False, False),
    ('saturnine-praetor', 'Saturnine Praetor', None, 'https://www.nobleknight.com/P/2148455181/Saturnine-Praetor?awid=1576', False, False),
    ('legion-mkvi-assault-squad', 'MKVI Assault Squad', None, 'https://www.nobleknight.com/P/2148101253/MKVI-Assault-Squad?awid=1576', False, False),
    ('legion-vindicator-siege-tank', 'Legion Vindicator Siege Tank', None, 'https://www.nobleknight.com/P/2148055309/Legion-Vindicator-Siege-Tank?awid=1576', False, False),
    ('cerberus-heavy-tank-destroyer', 'Legiones Astartes Cerberus Heavy Tank Destroyer', None, 'https://www.nobleknight.com/P/2148048494/Legiones-Astartes-Cerberus-Heavy-Tank-Destroyer?awid=1576', False, False),
    ('sicaran-venator-tank-hunter', 'Legiones Astartes Sicaran Venator Tank Hunter', None, 'https://www.nobleknight.com/P/2148048492/Legiones-Astartes-Sicaran-Venator-Tank-Hunter?awid=1576', False, False),
    # NK listing title uses "Sky-Hunter Squadron" — same product as Scimitar Jetbike Squadron
    ('scimitar-jetbike-squadron', 'Legiones Astartes Sky-Hunter Squadron', None, 'https://www.nobleknight.com/P/2148036064/Legiones-Astartes-Sky-Hunter-Squadron?awid=1576', False, False),
    ('typhon-heavy-siege-tank', 'Legion Typhon Heavy Siege Tank', None, 'https://www.nobleknight.com/P/2148040492/Legion-Typhon-Heavy-Siege-Tank?awid=1576', False, False),
    ('scorpius-missile-tank', 'Legiones Astartes Scorpius Missile Tank', None, 'https://www.nobleknight.com/P/2148025611/Legiones-Astartes-Scorpius-Missile-Tank?awid=1576', False, False),
    ('deimos-pattern-predator-support-tank', 'Deimos Pattern Predator Support Tank', None, 'https://www.nobleknight.com/P/2148011894/Deimos-Pattern-Predator-Support-Tank?awid=1576', False, False),
    # NK listing title uses "Land Rover" — same product as Land Raider Explorator/Carrier
    ('land-raider-explorator-carrier', 'Land Rover Proteus Explorator Squadron', None, 'https://www.nobleknight.com/P/2148132730/Land-Rover-Proteus-Explorator-Squadron?awid=1576', False, False),
    ('heavy-weapons-upgrade-set-volkite-culverins-lascannons-and-autocannons', 'Heavy Weapons Upgrade Set - Volkite Culverins, Lascannons and Autocannons', None, 'https://www.nobleknight.com/P/2148002468/Heavy-Weapons-Upgrade-Set---Volkite-Culverins-Lascannons-and-Autocannons?awid=1576', False, False),
    ('heavy-weapons-upgrade-set-heavy-flamers-multi-meltas-and-plasma-cannons', 'Heavy Weapons Upgrade Set - Heavy Flamers, Multi-Meltas and Plasma Cannon', None, 'https://www.nobleknight.com/P/2148002461/Heavy-Weapons-Upgrade-Set---Heavy-Flamers-Multi-Meltas-and-Plasma-Cannon?awid=1576', False, False),
    ('leviathan-siege-dreadnought-with-claw-and-drill-weapons', 'Leviathan Siege Dreadnought w/ Claw and Drill Weapons', None, 'https://www.nobleknight.com/P/2147993200/Leviathan-Siege-Dreadnought-w--Claw-and-Drill-Weapons?awid=1576', False, False),
    ('leviathan-siege-dreadnought-ranged-weapons-frame', 'Leviathan Siege Dreadnought Ranged Weapons Frame', None, 'https://www.nobleknight.com/P/2148070236/Leviathan-Siege-Dreadnought-Ranged-Weapons-Frame?awid=1576', False, False),
    ('contemptor-dreadnought-weapons-frame-2', 'Contemptor Dreadnought Weapons Frame 2', None, 'https://www.nobleknight.com/P/2148070454/Contemptor-Dreadnought-Weapons-Frame-2?awid=1576', False, False),
    ('contemptor-dreadnought-weapons-frame-1', 'Contemptor Dreadnought Weapons Frame 1', None, 'https://www.nobleknight.com/P/2148187816/Contemptor-Dreadnought-Weapons-Frame-1?awid=1576', False, False),
    ('leviathan-siege-dreadnought-with-ranged-weapons', 'Leviathan Siege Dreadnought w/ Ranged Weapons', None, 'https://www.nobleknight.com/P/2147996270/Leviathan-Siege-Dreadnought-w-Ranged-Weapons?awid=1576', False, False),
    ('special-weapons-upgrade-set', 'Special Weapons Upgrade Set', None, 'https://www.nobleknight.com/P/2147984753/Special-Weapons-Upgrade-Set?awid=1576', False, False),
    # NK listing title uses generic "Heavy Weapons Upgrade Set" — confirmed for Missile Launchers and Heavy Bolters
    ('heavy-weapons-upgrade-set-missile-launchers-and-heavy-bolters', 'Heavy Weapons Upgrade Set', None, 'https://www.nobleknight.com/P/2147984755/Heavy-Weapons-Upgrade-Set?awid=1576', False, False),
    ('kratos-assault-tank', 'Kratos Heavy Assault Tank', None, 'https://www.nobleknight.com/P/2147984752/Kratos-Heavy-Assault-Tank?awid=1576', False, False),
    ('deimos-pattern-rhino', 'Deimos Pattern Rhino', None, 'https://www.nobleknight.com/P/2147984750/Deimos-Pattern-Rhino?awid=1576', False, False),
    ('glaive-super-heavy-special-weapons-tank', 'Glaive Super-Heavy Special Weapons Tank', None, 'https://www.nobleknight.com/P/2148457369/Glaive-Super-Heavy-Special-Weapons-Tank?awid=1576', False, False),
    ('fellblade-super-heavy-battle-tank', 'Fellblade Super-Heavy Battle Tank', None, 'https://www.nobleknight.com/P/2148352416/Fellblade-Super-Heavy-Battle-Tank?awid=1576', False, False),
    ('legion-drop-pod', 'Drop Pods', None, 'https://www.nobleknight.com/P/2148132709/Drop-Pods?awid=1576', False, False),
    ('tarantula-sentry-guns', 'Legiones Astartes - Tarantula Sentry Guns', None, 'https://www.nobleknight.com/P/2148317371/Legiones-Astartes---Tarantula-Sentry-Guns?awid=1576', False, False),
    ('tarantula-missile-battery', 'Legiones Astartes - Tarantula Missile Battery', None, 'https://www.nobleknight.com/P/2148317543/Legiones-Astartes---Tarantula-Missile-Battery?awid=1576', False, False),
    ('rapier-quad-heavy-bolters-and-graviton-cannon-battery', 'Legiones Astartes - Rapier Quad Heavy Bolters and Graviton Cannon Battery', None, 'https://www.nobleknight.com/P/2148317544/Legiones-Astartes---Rapier-Quad-Heavy-Bolters-and-Graviton-Cannon-Battery?awid=1576', False, False),
    ('rapier-laser-destroyer-and-quad-launcher-battery', 'Legiones Astartes - Rapier Laser Destroyer and Quad Launcher Battery', None, 'https://www.nobleknight.com/P/2148317546/Legiones-Astartes---Rapier-Laser-Destroyer-and-Quad-Launcher-Battery?awid=1576', False, False),
    ('mkiii-legion-command-squad', 'MKIII Legion Command Squad', None, 'https://www.nobleknight.com/P/2148165785/MKIII-Legion-Command-Squad?awid=1576', False, False),
    ('mkvi-legion-command-squad', 'MKVI Legion Command Squad', None, 'https://www.nobleknight.com/P/2148165751/MKVI-Legion-Command-Squad?awid=1576', False, False),
    ('deredeo-dreadnought-anvilus-configuration', 'Deredeo Dreadnought - Anvilus Configuration', None, 'https://www.nobleknight.com/P/2148089267/Deredeo-Dreadnought---Anvilus-Configuration?awid=1576', False, False),
    ('leviathan-siege-dreadnought-close-combat-weapons', 'Leviathan Siege Dreadnought Close Combat Weapons Frame', None, 'https://www.nobleknight.com/P/2148070235/Leviathan-Siege-Dreadnought-Close-Combat-Weapons-Frame?awid=1576', False, False),
    ('liber-hereticus-traitor-legiones-astartes-army-book', 'Liber Hereticus - Traitor Legiones Astartes Army Book', None, 'https://www.nobleknight.com/P/2148327744/Liber-Hereticus---Traitor-Legiones-Astartes-Army-Book?awid=1576', False, False),
    ('ahzek-ahriman', 'Ahzek Ahriman', None, 'https://www.nobleknight.com/P/2147984756/Ahzek-Ahriman?awid=1576', False, False),
]


class Command(BaseCommand):
    """Seed Noble Knight URLs for Astartes Legions products."""

    help = 'seed_nk_astartes_legions_prices — NK URLs for Astartes Legions (51 of 63 SKUs)'

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
            f'seed_nk_astartes_legions_prices complete. {seeded} record(s) seeded.'
        ))
