"""
Management command: seed_mm_astartes_legions_prices

Seeds Miniature Market URLs for Astartes Legions products.

43 of 63 AL SKUs have confirmed MM listings. Omitted (no MM listing):
AL-002, AL-005, AL-014, AL-015, AL-020, AL-021, AL-022, AL-027,
AL-035, AL-036, AL-037, AL-045, AL-046, AL-047, AL-048, AL-049,
AL-050, AL-051, AL-060, AL-061.

create_defaults pattern: price, in_stock, last_seen are set only on
creation so scraper-set prices survive Railway redeploys.
url, listing_title, not_available are in defaults and always updated.

Usage:
    python manage.py seed_mm_astartes_legions_prices
"""

from django.core.management.base import BaseCommand

MM_PRICES = [
    # (slug, listing_title, price, url, in_stock, not_available)
    ('warhammer-the-horus-heresy-saturnine', 'Warhammer: The Horus Heresy - Saturnine', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-saturnine-gw-31-112.html', False, False),
    ('liber-astartes-loyalist-legiones-astartes-army-book', 'Liber Astartes: Loyalist Legiones Astartes Army Book', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-liber-astartes-loyalist-legiones-astartes-army-book-gw-31-30.html', False, False),
    ('legiones-astartes-combat-force', 'Legiones Astartes: Combat Force', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Combat-Force-Legiones-Astartes/GW-31-140', False, False),
    ('falchion-super-heavy-tank-destroyer', 'Falchion Super-heavy Tank Destroyer', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legiones-Astartes-Falcion-Super-Heavy-Tank-Destroyer-New-Arrival/GW-31-160-2026', False, False),
    ('spartan-prometheus-assault-tank', 'Spartan Prometheus Assault Tank', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legiones-Astartes-Spartan-Prometheus-Assault-Tank-New-Arrival/GW-31-155-2026', False, False),
    ('mkii-tactical-squad', 'MKII Tactical Squad', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-mkii-tactical-squad-gw-31-123.html', False, False),
    ('legion-praetor-with-power-axe', 'Legion Praetor with Power Axe', None, 'https://www.miniaturemarket.com/gw-31-11.html', False, False),
    ('legion-praetor-with-power-sword', 'Legion Praetor with Power Sword', None, 'https://www.miniaturemarket.com/gw-31-24.html', False, False),
    ('legion-cataphractii-praetor-and-chaplain-consul', 'Legion Cataphractii Praetor & Chaplain Consul', None, 'https://www.miniaturemarket.com/gw-31-08.html', False, False),
    ('legion-tartaros-terminator-squad', 'Legion Tartaros Terminator Squad', None, 'https://www.miniaturemarket.com/gw-31-07.html', False, False),
    ('geigor-fell-hand', 'Geigor Fell-Hand', None, 'https://www.miniaturemarket.com/gw-31-10.html', False, False),
    ('breacher-squad-upgrade-set', 'Breacher Squad Upgrade Set', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legiones-Astartes-Breacher-Squad-Upgrade-Set/GW-31-151-2026', False, False),
    ('mkiii-breacher-squad', 'MKIII Breacher Squad', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legiones-Astartes-MKIII-Breacher-Squad/GW-31-141-2026', False, False),
    ('cataphractii-terminators-with-combi-bolters-and-power-fists', 'Cataphractii Terminators with Combi-bolters and Power Fists', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legiones-Astartes-Cataphractii-Terminators-Power-Fists/GW-31-143-2026', False, False),
    ('mkii-assault-squad', 'MkII Assault Squad', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legiones-Astartes-MKII-Assault-Squad/GW-31-135', False, False),
    ('legion-mkvi-assault-squad', 'Legion MKVI Assault Squad', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-mkvi-assault-squad-gw-31-70.html', False, False),
    ('legion-vindicator-siege-tank', 'Legion Vindicator Siege Tank', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-vindicator-siege-tank-gw-31-61.html', False, False),
    ('cerberus-heavy-tank-destroyer', 'Cerberus Heavy Tank Destroyer', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-cerberus-heavy-tank-gw-31-62.html', False, False),
    ('sicaran-venator-tank-hunter', 'Sicaran Venator Tank Hunter', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-sicaran-venator-gw-31-63.html', False, False),
    ('typhon-heavy-siege-tank', 'Typhon Heavy Siege Tank', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-typhon-heavy-siege-tank-gw-31-15.html', False, False),
    ('scorpius-missile-tank', 'Scorpius Missile Tank', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-scorpius-missile-tank-gw-31-60.html', False, False),
    ('deimos-pattern-predator-support-tank', 'Deimos Pattern Predator Support Tank', None, 'https://www.miniaturemarket.com/gw-31-59.html', False, False),
    ('land-raider-explorator-carrier', 'Land Raider Explorator/Carrier', None, 'https://www.miniaturemarket.com/gw-31-33.html', False, False),
    ('heavy-weapons-upgrade-set-volkite-culverins-lascannons-and-autocannons', 'Heavy Weapons Upgrade Set - Volkite Culverins, Lascannons, and Autocannons', None, 'https://www.miniaturemarket.com/gw-31-13.html', False, False),
    ('heavy-weapons-upgrade-set-heavy-flamers-multi-meltas-and-plasma-cannons', 'Heavy Weapons Upgrade Set - Heavy Flamers, Multi-meltas, and Plasma Cannons', None, 'https://www.miniaturemarket.com/gw-31-12.html', False, False),
    ('leviathan-siege-dreadnought-with-claw-and-drill-weapons', 'Leviathan Siege Dreadnought with Claw & Drill Weapons', None, 'https://www.miniaturemarket.com/gw-31-29.html', False, False),
    ('leviathan-siege-dreadnought-with-ranged-weapons', 'Leviathan Siege Dreadnought with Ranged Weapons', None, 'https://www.miniaturemarket.com/gw-31-28.html', False, False),
    ('special-weapons-upgrade-set', 'Special Weapons Upgrade Set', None, 'https://www.miniaturemarket.com/gw-31-05.html', False, False),
    ('heavy-weapons-upgrade-set-missile-launchers-and-heavy-bolters', 'Heavy Weapons Upgrade Set - Missile Launchers and Heavy Bolters', None, 'https://www.miniaturemarket.com/gw-31-04.html', False, False),
    ('kratos-assault-tank', 'Kratos Assault Tank', None, 'https://www.miniaturemarket.com/gw-31-20.html', False, False),
    ('deimos-pattern-rhino', 'Deimos Pattern Rhino', None, 'https://www.miniaturemarket.com/gw-31-02.html', False, False),
    ('glaive-super-heavy-special-weapons-tank', 'Glaive Super-heavy Special Weapons Tank', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legiones-Astartes-Glaive-Super-Heavy-Special-Weapons-Tank/GW-31-158-2026', False, False),
    ('fellblade-super-heavy-battle-tank', 'Fellblade Super-Heavy Battle Tank', None, 'https://www.miniaturemarket.com/Warhammer-Horus-Heresy-Legiones-Astartes-Fellblade-Super-Heavy-Battle-Tank/GW-31-142', False, False),
    ('tarantula-sentry-guns', 'Tarantula Sentry Guns', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-tarantula-sentry-guns-gw-31-109.html', False, False),
    ('tarantula-missile-battery', 'Tarantula Missile Battery', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-tarantula-missile-battery-gw-31-108.html', False, False),
    ('rapier-quad-heavy-bolters-and-graviton-cannon-battery', 'Rapier Quad Heavy Bolters and Graviton Cannon Battery', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-rapier-quad-heavy-bolters-and-graviton-cannon-battery-gw-31-105.html', False, False),
    ('rapier-laser-destroyer-and-quad-launcher-battery', 'Rapier Laser Destroyer and Quad Launcher Battery', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-rapier-laser-destroyer-and-quad-launcher-battery-gw-31-104.html', False, False),
    ('melee-weapons-upgrade-set', 'Melee Weapons Upgrade Set', None, 'https://www.miniaturemarket.com/horus-heresy-legiones-astartes-melee-weapons-upgrade-gw-31-99.html', False, False),
    ('mkiii-legion-command-squad', 'MKIII Legion Command Squad', None, 'https://www.miniaturemarket.com/legiones-astartes-mkiii-command-squad-gw-31-86.html', False, False),
    ('mkvi-legion-command-squad', 'MKVI Legion Command Squad', None, 'https://www.miniaturemarket.com/legiones-astartes-mkvi-command-squad-gw-31-85.html', False, False),
    ('deredeo-dreadnought-anvilus-configuration', 'Deredeo Dreadnought: Anvilus Configuration', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-deredeo-dreadnought-anvilus-configuratn-gw-31-36.html', False, False),
    ('liber-hereticus-traitor-legiones-astartes-army-book', 'Liber Hereticus: Traitor Legiones Astartes Army Book', None, 'https://www.miniaturemarket.com/warhammer-horus-heresy-liber-hereticus-traitor-legiones-astartes-army-book-gw-31-31.html', False, False),
    ('ahzek-ahriman', 'Ahzek Ahriman', None, 'https://www.miniaturemarket.com/gw-31-09.html', False, False),
]


class Command(BaseCommand):
    """Seed Miniature Market URLs for Astartes Legions products."""

    help = 'seed_mm_astartes_legions_prices — MM URLs for Astartes Legions (43 of 63 SKUs)'

    def handle(self, *args, **options):
        """Run the command."""
        from django.utils import timezone

        from prices.models import CurrentPrice
        from products.models import Product, Retailer

        mm_retailer = Retailer.objects.get(slug='miniature-market')
        seeded = 0

        for (slug, listing_title, price, url, in_stock, not_available) in MM_PRICES:
            product = Product.objects.get(slug=slug)
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm_retailer,
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
            self.stdout.write(f'  seeded MM: {slug}')
            seeded += 1

        self.stdout.write(self.style.SUCCESS(
            f'seed_mm_astartes_legions_prices complete. {seeded} record(s) seeded.'
        ))
