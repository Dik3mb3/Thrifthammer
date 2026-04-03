"""
Management command: populate_ec_products

Creates the Emperor's Children faction and all EC-range product entries,
seeds GW CurrentPrice records at MSRP, and creates UnitType entries so
Emperor's Children appears in the Army Cost Calculator.

Product names match Games Workshop's official website titles exactly.
GW URLs come from the en-US storefront (no queryID tracking params).

Also sets parent_faction on EC, Death Guard, World Eaters, and Thousand Sons
to Chaos Space Marines so those factions inherit CSM shared kits on their
faction pages and the Army Calculator.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_ec_products
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

# Import role-assignment helpers from populate_units to stay consistent
from calculators.management.commands.populate_units import (
    _assign_role,
    _is_combo_box,
    _should_skip,
)

# ── Image URL base ────────────────────────────────────────────────────────────
_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# Each tuple:
#   (slug, name, gw_sku, msrp, image_filename, gw_url, ebay_search_name, faction_key)
#
# name    — matches GW website title exactly
# gw_url  — en-US storefront URL, no queryID params
# faction_key: 'ec' = Emperor's Children, 'csm' = Chaos Space Marines
PRODUCTS = [
    # ── Emperor's Children — EC-specific kits ────────────────────────────────
    (
        'combat-patrol-emperors-children',
        "Combat Patrol: Emperor's Children",
        '99120102207',
        170.00,
        '99120102207_ECCombatPatrol01.jpg',
        'https://www.warhammer.com/en-US/shop/combat-patrol-emperors-children-2025',
        '',
        'ec',
    ),
    (
        'fulgrim-daemon-primarch-of-slaanesh',
        'Fulgrim \u2013 Daemon Primarch of Slaanesh',
        '99120102200',
        175.00,
        '99120102200_ECFulgrim01.jpg',
        'https://www.warhammer.com/en-US/shop/emperors-children-fulgrim-2025',
        'Fulgrim Daemon Primarch Slaanesh Warhammer',
        'ec',
    ),
    (
        'emperors-children-tormentors',
        'Tormentors',
        '99120102203',
        70.00,
        '99120102203_ECTormentors01.jpg',
        'https://www.warhammer.com/en-US/shop/emperors-children-tormentors-2025',
        '',
        'ec',
    ),
    (
        'emperors-children-flawless-blades',
        'Flawless Blades',
        '99120102202',
        60.00,
        '99120102202_ECFlawlessBlades01.jpg',
        'https://www.warhammer.com/en-US/shop/emperors-children-flawless-blades-2025',
        '',
        'ec',
    ),
    (
        'lucius-the-eternal',
        'Lucius the Eternal',
        '99120102201',
        48.00,
        '99120102201_ECLuciusTheEternal01.jpg',
        'https://www.warhammer.com/en-US/shop/emperors-children-lucius-the-eternal-2025',
        '',
        'ec',
    ),
    (
        'emperors-children-noise-marines',
        'Noise Marines',
        '99120102204',
        69.00,
        '99120102204_ECNoiseMarines01.jpg',
        'https://www.warhammer.com/en-US/shop/emperors-children-noise-marines-2025',
        '',
        'ec',
    ),
    (
        'emperors-children-lord-exultant',
        'Lord Exultant',
        '99120102206',
        43.50,
        '99120102206_ECLordExultant01.jpg',
        'https://www.warhammer.com/en-US/shop/emperors-children-lord-exultant-2025',
        '',
        'ec',
    ),
    (
        'emperors-children-lord-kakophonist',
        'Lord Kakophonist',
        '99120102205',
        42.00,
        '99120102205_ECLordKakophonist01.jpg',
        'https://www.warhammer.com/en-US/shop/emperors-children-lord-kakophonist-2025',
        '',
        'ec',
    ),
    # ── Slaanesh Daemon kits (tagged EC — EC is primary Slaanesh army) ────────
    (
        'daemonettes-of-slaanesh',
        'Daemonettes of Slaanesh',
        '99129915036',
        43.50,
        '99129915036_Daemonettes01.jpg',
        'https://www.warhammer.com/en-US/shop/Daemonettes-of-Slaanesh-2021',
        '',
        'ec',
    ),
    (
        'keeper-of-secrets',
        'Keeper of Secrets',
        '99129915056',
        170.00,
        '99129915056_DoSKeeperofSecrets02.jpg',
        'https://www.warhammer.com/en-US/shop/Keeper-of-Secrets-2019',
        'Keeper of Secrets Warhammer Chaos',
        'ec',
    ),
    (
        'shalaxi-helbane',
        'Shalaxi Helbane',
        '99129915056',
        170.00,
        '99129915056_DoSKeeperofSecrets01.jpg',
        'https://www.warhammer.com/en-US/shop/Shalaxi-Hellbane-2019',
        'Shalaxi Helbane Warhammer Chaos',
        'ec',
    ),
    (
        'fiends-of-slaanesh',
        'Fiends',
        '99129915052',
        60.00,
        '99129915052_DoSFiends01.jpg',
        'https://www.warhammer.com/en-US/shop/Fiends-of-Slaanesh-2019',
        '',
        'ec',
    ),
    (
        'seekers-of-slaanesh',
        'Seekers of Slaanesh',
        '99129915005',
        35.00,
        '99129915005_SeekersLeadNEW.jpg',
        'https://www.warhammer.com/en-US/shop/Seekers-of-Slaanesh',
        '',
        'ec',
    ),
    (
        'codex-emperors-children',
        "Codex: Emperor's Children",
        '',
        60.00,
        '60030102035_ENGFREGERITASPAEmperorsChildrenStdEdHBCodex.jpg',
        'https://www.warhammer.com/en-US/shop/codex-emperors-children-2025-eng',
        '',
        'ec',
    ),
    # ── Shared Chaos Space Marines kits (tagged CSM — inherited by EC etc.) ───
    (
        'chaos-space-marines-sorcerer',
        'Chaos Space Marines Sorcerer',
        '99070102015',
        35.00,
        '99070102015_CSMSorcerer01.jpg',
        'https://www.warhammer.com/en-US/shop/Chaos-Space-Marines-Sorcerer-2019',
        '',
        'csm',
    ),
    (
        'chaos-terminator-squad',
        'Chaos Terminator Squad',
        '99120102097',
        65.00,
        '99120102097_CSMTerminators01.jpg',
        'https://www.warhammer.com/en-US/shop/Chaos-Space-Marine-Terminators-2019',
        '',
        'csm',
    ),
    (
        'chaos-rhino',
        'Chaos Rhino',
        '99120102092',
        60.00,
        '99120102092_CSMRhino01.jpg',
        'https://www.warhammer.com/en-US/shop/Chaos-Space-Marine-Rhino-2019',
        '',
        'csm',
    ),
    (
        'chaos-land-raider',
        'Chaos Land Raider',
        '99120102052',
        96.00,
        '99120102052_CSMLandRaiderRepack01.jpg',
        'https://www.warhammer.com/en-US/shop/Chaos-Space-Marines-Land-Raider',
        '',
        'csm',
    ),
    (
        'maulerfiend',
        'Maulerfiend',
        '99120102089',
        89.00,
        '99120102089_CSMForgefiend02.jpg',
        'https://www.warhammer.com/en-US/shop/Chaos-Space-Marine-Maulerfiend-2019',
        'Maulerfiend Forgefiend Warhammer Chaos',
        'csm',
    ),
    (
        'forgefiend',
        'Forgefiend',
        '99120102089',
        89.00,
        '99120102089_CSMForgefiend02.jpg',
        # Forgefiend and Maulerfiend are the same physical dual-build kit on GW
        'https://www.warhammer.com/en-US/shop/Chaos-Space-Marine-Maulerfiend-2019',
        'Forgefiend Maulerfiend Warhammer Chaos',
        'csm',
    ),
    (
        'heldrake',
        'Heldrake',
        '99120102090',
        89.00,
        '99120102090_CSMHeldrake01.jpg',
        'https://www.warhammer.com/en-US/shop/Chaos-Space-Marines-Heldrake-2019',
        '',
        'csm',
    ),
    (
        'daemon-prince-of-chaos',
        'Daemon Prince',
        '99120201130',
        89.00,
        '99120201130_S2DDaemonPrince01.jpg',
        'https://www.warhammer.com/en-US/shop/slaves-to-darkness-daemon-prince-2023',
        'Daemon Prince Warhammer Chaos',
        'csm',
    ),
    (
        'chaos-spawn',
        'Chaos Spawn',
        '99120201050',
        60.00,
        '99120201050_ChaosSpawn01.jpg',
        'https://www.warhammer.com/en-US/shop/Chaos-Spawn-2016',
        '',
        'csm',
    ),
]

# Sub-factions that should inherit CSM products
_CSM_CHILDREN = ["Emperor's Children", 'Death Guard', 'World Eaters', 'Thousand Sons']


class Command(BaseCommand):
    """Create Emperor's Children faction, products, GW prices, and UnitType entries."""

    help = (
        "Populates Emperor's Children faction, EC-range products with GW prices, "
        "and UnitType entries for the Army Calculator. Product names match GW website "
        "titles exactly. Also links EC/DG/WE/TS to CSM as parent. Idempotent."
    )

    def handle(self, *args, **options):
        """Run the command."""
        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        if not category_40k:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        # ── Resolve factions ──────────────────────────────────────────────────
        csm_faction = Faction.objects.filter(name='Chaos Space Marines').first()
        if not csm_faction:
            self.stderr.write(self.style.ERROR(
                'Chaos Space Marines faction not found — run populate_products first.'
            ))
            return

        ec_faction, ec_created = Faction.objects.get_or_create(
            name="Emperor's Children",
            defaults={
                'slug': 'emperors-children',
                'category': category_40k,
                'display_name': "Emperor's Children",
                'hero_tagline': 'The III Legion: Perfection Through Excess',
                'synopsis': (
                    "The Emperor's Children are one of the most feared Chaos Space Marine "
                    "legions, devoted to Slaanesh, the Chaos God of excess and sensation. "
                    "Led by the daemon primarch Fulgrim, the III Legion pursues perfection "
                    "in all things: art, combat, and sensory experience taken to their "
                    "most extreme conclusion. On the battlefield, Emperor's Children armies "
                    "combine elite Noise Marines wielding sonic weapons, swift Slaanesh "
                    "daemon allies, and powerful elite infantry capable of devastating "
                    "close-range firepower. Their playstyle rewards aggressive forward "
                    "pressure and a high-quality model collection. As one of the newer "
                    "Warhammer 40K factions with a fresh 2025 model range, the Emperor's "
                    "Children are an exciting choice for both collectors and competitive players."
                ),
                'difficulty': 'Intermediate',
                'model_count_rating': 'Low-Medium (20-40 models)',
                'painting_complexity': 'Medium-Hard',
                'playstyle': 'Aggressive Elite',
                'price_range_display': '$$$',
                'parent_faction': csm_faction,
            },
        )
        if ec_created:
            self.stdout.write(self.style.SUCCESS("Created faction: Emperor's Children"))
        else:
            if ec_faction.parent_faction != csm_faction:
                ec_faction.parent_faction = csm_faction
                ec_faction.save()
            self.stdout.write(f"Found faction: Emperor's Children (pk={ec_faction.pk})")

        # ── Set parent_faction on other chaos sub-factions ────────────────────
        for child_name in _CSM_CHILDREN:
            child = Faction.objects.filter(name=child_name).first()
            if not child:
                self.stdout.write(self.style.WARNING(
                    f'  Faction not found, skipping parent link: {child_name}'
                ))
                continue
            if child.parent_faction != csm_faction:
                child.parent_faction = csm_faction
                child.save()
                self.stdout.write(
                    self.style.SUCCESS(f'  Set parent_faction → CSM for: {child_name}')
                )
            else:
                self.stdout.write(f'  Parent already set for: {child_name}')

        # ── Resolve GW retailer ───────────────────────────────────────────────
        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded. '
                'Run populate_products first.'
            ))

        # ── Create / update products, GW prices, and UnitTypes ───────────────
        faction_map = {'ec': ec_faction, 'csm': csm_faction}
        unit_created = 0
        unit_updated = 0
        price_created = 0
        price_updated = 0

        for (slug, name, gw_sku, msrp, img_filename, gw_url, ebay_name, faction_key) in PRODUCTS:
            faction = faction_map[faction_key]
            image_url = _IMG.format(filename=img_filename) if img_filename else ''

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_name,
                    'category': category_40k,
                    'faction': faction,
                    'is_active': True,
                    'batch_tag': 'phase-2',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'  {status}: {name} [{faction.name}]')
            )

            # ── Seed GW CurrentPrice at MSRP ──────────────────────────────────
            if gw_retailer and gw_url:
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
                    price_created += 1
                else:
                    price_updated += 1

            # ── Seed UnitType so this faction appears in the Army Calculator ──
            if _should_skip(name):
                continue

            role = 'combo_box' if _is_combo_box(name) else _assign_role(name)
            unit, u_created = UnitType.objects.update_or_create(
                product=product,
                faction=faction,
                defaults={
                    'name': name,
                    'category': role,
                    'points_cost': 0,
                    'typical_quantity': 1,
                    'description': '',
                    'is_active': True,
                },
            )
            if u_created:
                unit_created += 1
            else:
                unit_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"\npopulate_ec_products complete.\n"
            f"  {len(PRODUCTS)} products processed.\n"
            f"  GW prices: {price_created} created, {price_updated} updated.\n"
            f"  UnitTypes: {unit_created} created, {unit_updated} updated."
        ))
