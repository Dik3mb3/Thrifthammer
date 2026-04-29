"""
Management command: populate_aeldari_phase3_products

Creates / updates all Aeldari phase-3 product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates UnitType entries so
Aeldari appears in the Army Cost Calculator.

Phase-3 covers every product on the GW en-US Aeldari shop page as of
2026-04-05.  Existing products (7 Craftworlds, 6 Drukhari) are left
untouched; only NEW slugs are added here.

Faction assignments (per user confirmation):
  - Craftworlds / Harlequins / Ynnari / Corsairs units  → Aeldari
  - Drukhari units                                       → SKIPPED (separate phase)

Dual-kit products:
  - Crimson Hunter / Hemlock Wraithfighter  → same GW URL, same SKU
  - Fire Prism / Night Spinner              → same GW URL, same SKU
  - Storm Guardians / Guardian Defenders    → same GW URL, same SKU
    (Guardian Defenders is new; Storm Guardians already in DB as
     'craftworlds-guardians')

Kill Team, Dice, and Warhammer+ exclusives are excluded.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_aeldari_phase3_products
"""

from django.core.management.base import BaseCommand

from calculators.models import UnitType
from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

from calculators.management.commands.populate_units import (
    _assign_role,
    _is_combo_box,
    _should_skip,
)

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, name, gw_sku, msrp, image_filename, gw_url, ebay_search_name)
#
# gw_sku uses GW's internal prod ID where the box catalogue number is unknown.
# msrp is USD price from the GW en-US storefront as of 2026-04-05.
# ebay_search_name is blank unless the product name alone gives poor eBay results.
PRODUCTS = [

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-aeldari',
        'Codex: Aeldari',
        '',
        60.00,
        '60030104013_AeldariHBStdEdCodex1.jpg',
        'https://www.warhammer.com/en-US/shop/codex-aeldari-2025-eng',
        'Codex Aeldari Warhammer 40k',
    ),

    # ── HQ / Characters ───────────────────────────────────────────────────────
    (
        'aeldari-avatar-of-khaine',
        'Avatar of Khaine',
        'prod4900143',
        114.00,
        '99120104072_AELAvatarofKhaineLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-avatar-of-khaine-2022',
        'Avatar of Khaine Aeldari Warhammer',
    ),
    (
        'aeldari-autarch',
        'Autarch',
        'prod4900146',
        43.50,
        '99120104077_AELAutarchLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-autarch-2022',
        '',
    ),
    (
        'aeldari-autarch-wayleaper',
        'Autarch Wayleaper',
        'prod2810200',
        33.50,
        '99070104003_ELDARAUTARCH01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Autarch',
        'Autarch Wayleaper Aeldari Warhammer',
    ),
    (
        'aeldari-eldrad-ulthran',
        'Eldrad Ulthran',
        'prod3650164',
        39.00,
        '99070104006_Eldrad01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldrad-Ulthran-2017',
        '',
    ),
    (
        'aeldari-spiritseer',
        'Spiritseer',
        'prod4240206',
        35.00,
        '99070104007_Spiritseer01.jpg',
        'https://www.warhammer.com/en-US/shop/Craftworlds-Spiritseer-2019',
        '',
    ),
    (
        'aeldari-farseer-skyrunner',
        'Farseer Skyrunner',
        'prod3650295',
        43.50,
        '99070104002_ELDARFARSEERSKYRUNNER01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Farseer-Skyrunner-2017',
        '',
    ),
    (
        'aeldari-warlock-skyrunner',
        'Warlock Skyrunner',
        'prod3660120',
        43.50,
        '99070104002_ELDARWARLOCKSKYRUNNER01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Warlock-Skyrunner-2017',
        '',
    ),
    (
        'aeldari-warlocks',
        'Warlocks',
        'prod4870187',
        60.00,
        '99120104066_AELWarlocksLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-warlocks-2022',
        '',
    ),
    (
        'aeldari-maugan-ra',
        'Maugan Ra',
        'prod4870190',
        48.00,
        '99120104069_AELMauganRaLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-maugan-ra-2022',
        'Maugan Ra Warhammer Aeldari',
    ),
    (
        'aeldari-jain-zar',
        'Jain Zar',
        'prod4390156',
        48.00,
        '99120104063_CWJainZar01.jpg',
        'https://www.warhammer.com/en-US/shop/Craftworlds-Jain-Zar-2020',
        'Jain Zar Warhammer Aeldari',
    ),
    (
        'aeldari-fuegan',
        'Fuegan',
        'P-203621',
        48.00,
        '99120104103_AELFuegan01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-phoenix-lord-fuegan-2025',
        'Fuegan Phoenix Lord Warhammer Aeldari',
    ),
    (
        'aeldari-baharroth',
        'Baharroth',
        'P-203620',
        48.00,
        '99120104099_AELBaharroth01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-phoenix-lord-baharroth-2025',
        'Baharroth Phoenix Lord Warhammer Aeldari',
    ),
    (
        'aeldari-lhykhis',
        'Lhykhis',
        'P-203618',
        48.00,
        '99120104101_AELLhykhis01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-phoenix-lord-lhykhis-2025',
        'Lhykhis Phoenix Lord Warhammer Aeldari',
    ),
    (
        'aeldari-asurmen',
        'Asurmen',
        'P-203616',
        48.00,
        '99120104089_AELAsurmen01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-asurmen-2025',
        'Asurmen Warhammer Aeldari',
    ),
    (
        'aeldari-prince-yriel',
        'Prince Yriel',
        'P-240880',
        47.00,
        '99120104113_AeldariPrinceYriel01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-prince-yriel-2026',
        'Prince Yriel Warhammer Aeldari',
    ),
    (
        'aeldari-kharseth',
        'Kharseth',
        'P-240921',
        43.50,
        '99120104114_AeldariKharseth01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-kharseth-2026',
        'Kharseth Corsair Warhammer Aeldari',
    ),

    # ── Troops / Battleline ───────────────────────────────────────────────────
    (
        'aeldari-guardian-defenders',
        'Guardian Defenders',
        'prod4870188',
        60.00,
        '99120104067_AELGuardiansLead.jpg',
        # Same physical dual-build box as Storm Guardians (craftworlds-guardians)
        'https://www.warhammer.com/en-US/shop/aeldari-guardians-2022',
        'Guardian Defenders Aeldari Warhammer',
    ),
    (
        'aeldari-rangers',
        'Rangers',
        'prod4900144',
        62.50,
        '99120104073_AELRangersLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-rangers-2022',
        '',
    ),
    (
        'aeldari-howling-banshees',
        'Howling Banshees',
        'prod4390157',
        62.50,
        '99120104064_HowlingBanshees01.jpg',
        'https://www.warhammer.com/en-US/shop/Craftworlds-Howling-Banshees-2020',
        '',
    ),
    (
        'aeldari-dark-reapers',
        'Dark Reapers',
        'prod4870189',
        62.50,
        '99120104068_AELDarkReapersLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-dark-reapers-2022',
        '',
    ),
    (
        'aeldari-swooping-hawks',
        'Swooping Hawks',
        'P-203614',
        62.50,
        '99120104098_AELSwoopingHawks01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-swooping-hawks-2025',
        '',
    ),
    (
        'aeldari-warp-spiders',
        'Warp Spiders',
        'P-203611',
        62.50,
        '99120104100_AELWarpSpiders01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-warp-spiders-2025',
        '',
    ),
    (
        'aeldari-shining-spears',
        'Shining Spears',
        'prod4900142',
        69.00,
        '99120104071_AELShiningSpearLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-shining-spears-2022',
        '',
    ),
    (
        'aeldari-windriders',
        'Windriders',
        'prod3660121',
        60.00,
        '99120104038_ELDARWINDRIDERS01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Windriders-2017',
        '',
    ),
    (
        'aeldari-shroud-runners',
        'Shroud Runners',
        'prod4900145',
        73.50,
        '99120104074_ShroudRunnersLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-shroud-runners-2022',
        '',
    ),
    (
        'aeldari-corsair-voidreavers',
        'Corsair Voidreavers',
        'P-240923',
        65.00,
        '99120104115_AeldariCorsairVoidreavers01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-corsair-voidreavers-2026',
        'Corsair Voidreavers Aeldari Warhammer',
    ),
    (
        'aeldari-corsair-skyreavers',
        'Corsair Skyreavers',
        'P-240922',
        60.00,
        '99120104111_AeldariCorsairSkyreavers01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-corsair-skyreavers-2026',
        'Corsair Skyreavers Aeldari Warhammer',
    ),

    # ── Heavy Support / Vehicles ──────────────────────────────────────────────
    (
        'aeldari-support-weapon',
        'Support Weapon',
        'prod770020a',
        32.00,
        '99120104028_HeavySupportWeaponNEW_01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Support-Weapon',
        'Aeldari Support Weapon Warhammer',
    ),
    (
        'aeldari-wraithguard',
        # NOTE: craftworlds-wraithguard already in DB (old slug).
        # This new slug adds the updated 2017-repack listing; both point to same kit.
        'Wraithguard',
        'prod3590128',
        65.00,
        '99120104031_EldarWraithguard01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Wraithguard-2017',
        'Wraithguard Wraithblades Aeldari Warhammer',
    ),
    (
        'aeldari-wraithblades',
        'Wraithblades',
        'prod3590139',
        65.00,
        '99120104031_EldarWraithblades01.jpg',
        # Same dual-build kit as Wraithguard above
        'https://www.warhammer.com/en-US/shop/Eldar-Wraithblades-2017',
        'Wraithblades Wraithguard Aeldari Warhammer',
    ),
    (
        'aeldari-wraithlord',
        'Wraithlord',
        'prod3530578',
        65.00,
        '99120104013_WraithlordsNEW_01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Wraithlord-2017',
        '',
    ),
    (
        'aeldari-wraithknight',
        'Wraithknight',
        'prod3580144',
        170.00,
        '99120104084_AELWraithknightLead.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Wraithknight-2017',
        '',
    ),
    (
        'aeldari-fire-prism',
        'Fire Prism',
        'prod770019a',
        69.00,
        '99120104029_FirePrismNEW_01.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Fire-Prism',
        'Fire Prism Aeldari Warhammer',
    ),
    (
        'aeldari-night-spinner',
        'Night Spinner',
        'prod2180123',
        69.00,
        '99120104029_FirePrismNEW_01.jpg',
        # Same dual-build kit as Fire Prism
        'https://www.warhammer.com/en-US/shop/Eldar-Night-Spinner',
        'Night Spinner Aeldari Warhammer',
    ),
    (
        'aeldari-crimson-hunter',
        'Crimson Hunter',
        'prod3600196',
        96.00,
        '99120104080_CrimsonHunterLead_a.jpg',
        'https://www.warhammer.com/en-US/shop/Eldar-Crimson-Hunter-2017',
        'Crimson Hunter Aeldari Warhammer',
    ),
    (
        'aeldari-hemlock-wraithfighter',
        'Hemlock Wraithfighter',
        'prod3600197',
        96.00,
        '99120104080_CrimsonHunterLead_a.jpg',
        # Same dual-build kit as Crimson Hunter
        'https://www.warhammer.com/en-US/shop/Eldar-Hemlock-Wraithfighter-2017',
        'Hemlock Wraithfighter Aeldari Warhammer',
    ),
    (
        'aeldari-vyper',
        'Vyper',
        'P-240924',
        65.00,
        '99120104112_AeldariVyper01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-vyper-2026',
        'Vyper Starfang Aeldari Warhammer',
    ),
    (
        'aeldari-starfang',
        'Starfang',
        'P-240924',
        65.00,
        '99120104112_AeldariVyper01.jpg',
        # Same dual-build kit as Vyper
        'https://www.warhammer.com/en-US/shop/aeldari-vyper-2026',
        'Starfang Vyper Aeldari Corsair Warhammer',
    ),
    (
        'aeldari-war-walkers',
        'War Walkers',
        'P-203606',
        85.00,
        '99120104107_AELWarWalkers01.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-war-walkers-2025',
        '',
    ),

    # ── Harlequins ────────────────────────────────────────────────────────────
    (
        'aeldari-harlequin-troupe',
        'Harlequin Troupe',
        'prod3530579',
        48.00,
        '99120111007_AELHarlequinTroupeLead.jpg',
        'https://www.warhammer.com/en-US/shop/Harlequin-Troupe-Troop-2017',
        'Harlequin Troupe Warhammer',
    ),
    (
        'aeldari-skyweavers',
        'Skyweavers',
        'prod2620124',
        60.00,
        '99120111005_AELSkyweaversLead.jpg',
        'https://www.warhammer.com/en-US/shop/Harlequin-Skyweavers',
        'Harlequin Skyweavers Warhammer',
    ),
    (
        'aeldari-starweaver',
        'Starweaver',
        'prod2600170',
        48.00,
        '99120111006_AELStarweaverLead.jpg',
        'https://www.warhammer.com/en-US/shop/Harlequin-Starweaver',
        'Harlequin Starweaver Warhammer',
    ),
    (
        'aeldari-voidweaver',
        'Voidweaver',
        'prod2780228',
        48.00,
        '99120111003_HarlequinVoidweaver01.jpg',
        'https://www.warhammer.com/en-US/shop/Voidweaver',
        'Harlequin Voidweaver Warhammer',
    ),
    (
        'aeldari-solitaire',
        'Solitaire',
        'prod2620122',
        33.50,
        '99070111003_Solitaire01.jpg',
        'https://www.warhammer.com/en-US/shop/Solitaire',
        'Harlequin Solitaire Warhammer',
    ),
    (
        'aeldari-shadowseer',
        'Shadowseer',
        'prod2620121',
        35.00,
        '99070111005_AELShadowseerLead.jpg',
        'https://www.warhammer.com/en-US/shop/Harlequin-Shadowseer',
        'Harlequin Shadowseer Warhammer',
    ),
    (
        'aeldari-death-jester',
        'Death Jester',
        'prod2620120',
        35.00,
        '99070111001_HarlequinDeathJester01.jpg',
        'https://www.warhammer.com/en-US/shop/Harlequin-Death-Jester',
        'Harlequin Death Jester Warhammer',
    ),

    # ── Ynnari ────────────────────────────────────────────────────────────────
    (
        'aeldari-yvraine',
        'Yvraine',
        'prod4870185',
        43.50,
        '99070104009_AELYvraineLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-yvraine-2022',
        'Yvraine Ynnari Warhammer',
    ),
    (
        'aeldari-the-visarch',
        'The Visarch',
        'prod4870186',
        35.00,
        '99070104010_AELVisarchLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-the-visarch-2022',
        'Visarch Ynnari Warhammer',
    ),
    (
        'aeldari-the-yncarne',
        'The Yncarne',
        'prod4870191',
        60.00,
        '99120104076_AELYncarneLead.jpg',
        'https://www.warhammer.com/en-US/shop/aeldari-the-yncarne-2022',
        'Yncarne Ynnari Warhammer',
    ),

    # ── Corsairs — Combat Patrol ───────────────────────────────────────────────
    (
        'combat-patrol-aeldari-corsairs',
        'Combat Patrol: Aeldari Corsairs',
        'P-240879',
        170.00,
        '99120104110_AeldariCorsairsCombatPatrol01.jpg',
        'https://www.warhammer.com/en-US/shop/combat-patrol-aeldari-corsairs-2026',
        'Combat Patrol Aeldari Corsairs Warhammer',
    ),
]


class Command(BaseCommand):
    """Populate Aeldari phase-3 products, GW prices, and UnitType entries."""

    help = (
        'Creates Aeldari phase-3 products (Craftworlds, Harlequins, Ynnari, Corsairs). '
        'Skips existing slugs already in DB. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        if not category_40k:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        aeldari_faction = Faction.objects.filter(name='Aeldari').first()
        if not aeldari_faction:
            self.stderr.write(self.style.ERROR(
                'Aeldari faction not found — run populate_products first.'
            ))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        unit_created = 0
        unit_updated = 0
        price_created = 0
        price_updated = 0
        product_created = 0
        product_updated = 0

        for (slug, name, gw_sku, msrp, img_filename, gw_url, ebay_name) in PRODUCTS:
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
                    'faction': aeldari_faction,
                    'is_active': True,
                    'batch_tag': 'phase-3',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name}'))
            if created:
                product_created += 1
            else:
                product_updated += 1

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

            # ── Seed UnitType for Army Calculator ─────────────────────────────
            if _should_skip(name):
                continue

            role = 'combo_box' if _is_combo_box(name) else _assign_role(name)
            _, u_created = UnitType.objects.update_or_create(
                name=name,
                faction=aeldari_faction,
                defaults={
                    # Key on (name, faction) — not (product, faction) — so that
                    # existing UnitTypes created with product=NULL (e.g. Ynnari
                    # characters seeded by populate_units before phase-3 existed)
                    # are found and updated rather than triggering an IntegrityError
                    # on the unique (name, faction) constraint.
                    'product': product,
                    'category': role,
                    # points_cost excluded — preserved on update so GitHub Actions
                    # seeded values (seed_aeldari_stats) are not wiped on every
                    # Procfile deploy. New entries start at 0 via model default.
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
            f'\npopulate_aeldari_phase3_products complete.\n'
            f'  Products : {product_created} created, {product_updated} updated\n'
            f'  GW prices: {price_created} created, {price_updated} updated\n'
            f'  UnitTypes: {unit_created} created, {unit_updated} updated'
        ))
