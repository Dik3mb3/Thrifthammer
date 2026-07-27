"""
Seed Games Workshop UK prices for Astartes Legions.

Creates the `games-workshop-uk` Retailer if it does not exist, sets
msrp_gbp on each matched Product, and creates/updates a CurrentPrice
record pointing at the GW UK product page.

Run once on Railway startup via Procfile.  Safe to re-run — idempotent.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Product, Retailer

_GW_UK_SLUG = 'games-workshop-uk'

# (gw_sku, label, gbp_price, gw_uk_url)
_PRICES = [
    ('AL-001', 'Warhammer: The Horus Heresy – Saturnine', Decimal('200.00'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-age-of-darkness-saturnine-2025-eng'),
    ('AL-002', 'Legiones Astartes: Maximus Battle Group', Decimal('134.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-maximus-battle-group-2026'),
    ('AL-003', 'Liber Astartes: Loyalist Legiones Astartes Army Book', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-liber-astartes-2025-eng'),
    ('AL-004', 'Legiones Astartes: Combat Force', Decimal('105.00'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-legiones-astartes-combat-force-2025'),
    ('AL-005', 'Whirlwind Missile Tank', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-whirlwind-missile-tank-2026'),
    ('AL-006', 'Falchion Super-heavy Tank Destroyer', Decimal('125.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-falcion-super-heavy-tank-destroyer-2026'),
    ('AL-007', 'Spartan Prometheus Assault Tank', Decimal('74.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-spartan-prometheus-assault-tank-2026'),
    ('AL-008', 'MKII Tactical Squad', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-mk2-tactical-squad-2025'),
    ('AL-009', 'Legion Praetor with Power Axe', Decimal('21.75'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-praetor-with-power-axe-2022'),
    ('AL-010', 'Legion Praetor with Power Sword', Decimal('21.75'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-praetor-with-power-sword-2022'),
    ('AL-011', 'Legion Cataphractii Praetor & Chaplain Consul', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-praetor-and-chaplain-consul-2022'),
    ('AL-012', 'Legion Tartaros Terminator Squad', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-terminator-tartaros-squad-2022'),
    ('AL-013', 'Geigor Fell-Hand', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/hh-space-wolves-geigor-fell-hand-2022'),
    ('AL-014', 'Dominion Zephon', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-blood-angels-dominion-zephon-2022'),
    ('AL-015', 'Fafnir Rann', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-imperial-fists-fafnir-rann-2022'),
    ('AL-016', 'Breacher Squad Upgrade Set', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/breacher-squad-upgrade-set-2026'),
    ('AL-017', 'MKIII Breacher Squad', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-mk3-breacher-squad-2026'),
    ('AL-018', 'Cataphractii Terminators with Combi-bolters and Power Fists', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/cataphractii-terminators-combi-bolters-and-power-fists-2026'),
    ('AL-019', 'MkII Assault Squad', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-mk2-assault-squad-2025'),
    ('AL-020', 'Saturnine Praetor', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-saturnine-praetor-2025'),
    ('AL-021', 'Saturnine Terminator Squad', Decimal('49.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-saturnine-terminators-2025'),
    ('AL-022', 'MKII Veteran Squad with Disintegrator Weapons', Decimal('38.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-mk2-veteran-squad-with-disintegrators-2025'),
    ('AL-023', 'Legion MKVI Assault Squad', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-mk6-assault-marines-2023'),
    ('AL-024', 'Legion Vindicator Siege Tank', Decimal('47.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-vindicator-siege-tank-2023'),
    ('AL-025', 'Cerberus Heavy Tank Destroyer', Decimal('77.50'),
     'https://www.warhammer.com/en-GB/shop/legion-cerberus-heavy-tank-2023'),
    ('AL-026', 'Sicaran Venator Tank Hunter', Decimal('55.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-sicaran-venator-2023'),
    ('AL-027', 'Scimitar Jetbike Squadron', Decimal('45.00'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-sky-hunter-squadron-2023'),
    ('AL-028', 'Typhon Heavy Siege Tank', Decimal('77.50'),
     'https://www.warhammer.com/en-GB/shop/legion-typhon-heavy-siege-tank-2023'),
    ('AL-029', 'Scorpius Missile Tank', Decimal('45.00'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-scorpius-missile-tank-2022'),
    ('AL-030', 'Deimos Pattern Predator Support Tank', Decimal('47.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-predator-support-tank-2022'),
    ('AL-031', 'Land Raider Explorator/Carrier', Decimal('58.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-land-raider-proteus-2022'),
    ('AL-032', 'Heavy Weapons Upgrade Set – Volkite Culverins, Lascannons, and Autocannons', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-volkite-culverins-and-lascannons-2022'),
    ('AL-033', 'Heavy Weapons Upgrade Set – Heavy Flamers, Multi-meltas, and Plasma Cannons', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-multi-meltas-and-plasma-cannons-2022'),
    ('AL-034', 'Leviathan Siege Dreadnought with Claw & Drill Weapons', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/leviathan-siege-dreadnought-with-claw-and-drill-weapons-2022'),
    ('AL-035', 'Leviathan Siege Dreadnought Ranged Weapons Frame', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/leviathan-dreadnought-ranged-weapons-frame-2022'),
    ('AL-036', 'Contemptor Dreadnought Weapons Frame 2', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/contemptor-dreadnought-weapons-frame-2-2022'),
    ('AL-037', 'Contemptor Dreadnought Weapons Frame 1', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/contemptor-dreadnought-weapons-frame-1-2022'),
    ('AL-038', 'Leviathan Siege Dreadnought with Ranged Weapons', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/leviathan-dreadnought-with-ranged-weapons-2022'),
    ('AL-039', 'Special Weapons Upgrade Set', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-special-weapons-upgrade-set-2022'),
    ('AL-040', 'Heavy Weapons Upgrade Set – Missile Launchers and Heavy Bolters', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-missile-launchers-and-heavy-bolters-2022'),
    ('AL-041', 'Kratos Assault Tank', Decimal('85.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-kratos-heavy-assault-tank-2022'),
    ('AL-042', 'Deimos Pattern Rhino', Decimal('34.75'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-deimos-pattern-rhino-2022'),
    ('AL-043', 'Glaive Super-heavy Special Weapons Tank', Decimal('125.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-glaive-super-heavy-special-weapons-tank-2026'),
    ('AL-044', 'Fellblade Super-Heavy Battle Tank', Decimal('125.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-fellblade-super-heavy-battle-tank-2025'),
    ('AL-045', 'Araknae Quad Accelerator Platform', Decimal('42.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-araknae-quad-accelerator-platform-2025'),
    ('AL-046', 'Disintegrator Weapons Upgrade Set', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-disintegrator-upgrade-set-2025'),
    ('AL-047', 'Saturnine Dreadnought Weapons – Ophion Configuration', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/saturnine-dreadnought-weapons-ophion-2025'),
    ('AL-048', 'Saturnine Dreadnought Weapons – Chiron Configuration', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/saturnine-dreadnought-weapons-chiron-2025'),
    ('AL-049', 'Legion Drop Pod', Decimal('35.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-drop-pod-2025'),
    ('AL-050', 'Saturnine Siege Dreadnought – Ophion Configuration', Decimal('69.50'),
     'https://www.warhammer.com/en-GB/shop/legion-astartes-saturnine-dreadnought-ophion-2025'),
    ('AL-051', 'Saturnine Siege Dreadnought – Chiron Configuration', Decimal('69.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-saturnine-dreadnought-chiron-2025'),
    ('AL-052', 'Tarantula Sentry Guns', Decimal('36.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-tarantula-sentry-guns-2025'),
    ('AL-053', 'Tarantula Missile Battery', Decimal('36.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-tarantula-missile-battery-2025'),
    ('AL-054', 'Rapier Quad Heavy Bolters and Graviton Cannon Battery', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-rapier-quad-heavy-bolters-2025'),
    ('AL-055', 'Rapier Laser Destroyer and Quad Launcher Battery', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-rapier-laser-destroyer-2025'),
    ('AL-056', 'Melee Weapons Upgrade Set', Decimal('30.00'),
     'https://www.warhammer.com/en-GB/shop/legion-astartes-melee-weapons-upgrade-2024'),
    ('AL-057', 'MKIII Legion Command Squad', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-mkiii-command-squad-2024'),
    ('AL-058', 'MKVI Legion Command Squad', Decimal('32.50'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-mkvi-command-squad-2024'),
    ('AL-059', 'Deredeo Dreadnought: Anvilus Configuration', Decimal('54.50'),
     'https://www.warhammer.com/en-GB/shop/deredeo-dreadnought-anvilus-configuration-2023'),
    ('AL-060', 'Centurion with Power Maul', Decimal('25.00'),
     'https://www.warhammer.com/en-GB/shop/legiones-astartes-centurion-with-power-maul-2025'),
    ('AL-061', 'Leviathan Siege Dreadnought Close Combat Weapons', Decimal('18.50'),
     'https://www.warhammer.com/en-GB/shop/leviathan-dreadnought-close-combat-weapons-frame-2022'),
    ('AL-062', 'Liber Hereticus: Traitor Legiones Astartes Army Book', Decimal('44.50'),
     'https://www.warhammer.com/en-GB/shop/horus-heresy-liber-hereticus-2025-eng'),
    ('AL-063', 'Ahzek Ahriman', Decimal('21.50'),
     'https://www.warhammer.com/en-GB/shop/hh-thousand-sons-azhek-ahriman-2022'),
]


class Command(BaseCommand):
    help = 'Seed GW UK prices and URLs for Astartes Legions. Idempotent.'

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
                f'Seeded {seeded} Astartes Legions GW UK prices. Skipped: {skipped}.'
            )
        )
