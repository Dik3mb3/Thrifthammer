"""
Management command: populate_sm_phase2_products

Adds generic Space Marines products missing from the database after initial
seeding. These are generic SM kits usable by all Space Marine chapters
(Ultramarines, Blood Angels, Black Templars, Dark Angels, etc.).

Sourced from GW en-US Ultramarines filter scrape — 2026-04-03.
Tagged batch_tag='phase-2'. Seeds GW CurrentPrice at MSRP.

ALREADY IN DB (skipped — handled by original populate_products):
  Aggressors, Ancient, Apothecary, Assault Intercessors, Ballistus
  Dreadnought, Bladeguard Veterans, Brutalis Dreadnought, Chaplain,
  Chaplain in Terminator Armour, Combat Patrol, Company Heroes,
  Devastator Squad, Eradicators, Firestrike Servo-Turrets, Hammerfall
  Bunker, Impulsor, Inceptors, Incursors, Infernus Squad, Infiltrators,
  Intercessors, Invader ATV, Land Raider, Land Raider Crusader, Librarian,
  Outriders, Predator (Annihilator), Primaris Captain, Eliminators,
  Lieutenant, Redemptor Dreadnought, Repulsor, Repulsor Executioner,
  Scouts, Sternguard, Tactical Squad, Terminator Squad, Vanguard Veterans,
  Vindicator, Whirlwind.

SHARED KITS (both variants added, same physical box):
  - Centurion Devastator Squad + Centurion Assault Squad (same kit)
  - Storm Speeder Thunderstrike / Hammerstrike / Hailstrike (same kit)
  - Gladiator Lancer / Reaper / Valiant (same kit)
  - Stormtalon Gunship + Stormhawk Interceptor (same kit)
  - Predator Destructor (same kit as existing Predator/Annihilator)

SKIPPED (not mainline SM units):
  - Space Marine Heads ($26 upgrade sprue)
  - Kill Team: Scout Squad (Kill Team product)
  - Space Marines: Honoured of the Chapter ($170 bundle)
  - Heroes of the Chapter ($114 bundle)
  - Vanguard Task Force ($150 battleforce)
  - Starter sets, paint sets, books
  - Blood Angels Chaplain With Jump Pack (wrong faction)
  - Legion Thunderhawk Gunship, Astraeus Super-heavy Tank (Forge World)

Safe to run repeatedly (idempotent via update_or_create keyed on gw_sku).

Usage:
    python manage.py populate_sm_phase2_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# (slug, name, msrp, image_filename, gw_url, gw_sku)
PRODUCTS = [
    # ── Characters ────────────────────────────────────────────────────────────
    (
        'space-marine-techmarine',
        'Techmarine',
        43.50,
        '99120101278_SMPrimarisTechmarineLead.jpg',
        'https://www.warhammer.com/en-US/shop/Primaris-Techmarine-2020',
        '48-135',
    ),
    (
        'space-marine-captain-in-gravis-armour',
        'Captain in Gravis Armour',
        43.50,
        '99070101077_SMCPTGravisArmourLead.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-captain-in-gravis-armour-2022',
        '48-101',
    ),
    # Captain in Gravis Armour with Master-crafted Heavy Bolt Rifle removed 2026-04-04
    # (product discontinued / not stocked — user requested deletion)
    (
        'space-marine-captain-in-phobos-armour',
        'Captain in Phobos Armour',
        43.50,
        '99070101046_SMPrimarisCaptainPhobosArmour01.jpg',
        'https://www.warhammer.com/en-US/shop/Primaris-Captain-In-Phobos-Armour-2020',
        '48-102',
    ),
    (
        'space-marine-captain-with-jump-pack',
        'Captain with Jump Pack',
        43.50,
        '99120101394_SMJumpPkCpt1.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-captain-with-jump-pack-2023',
        '48-104',
    ),
    (
        'space-marine-captain-jump-pack-relic-shield',
        'Captain with Jump Pack and Relic Shield',
        43.50,
        '99120101492_SpaceMarinesCaptainwithJumpPackandRelicShield01.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-captain-with-jump-pack-and-relic-shield-2025',
        '48-105',
    ),
    (
        'space-marine-captain-with-relic-shield',
        'Captain with Relic Shield',
        43.50,
        '99120101396_SMCaptainStormShield1.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-captain-with-storm-shield-2023',
        '48-106',
    ),
    (
        'space-marine-captain-in-terminator-armour',
        'Captain in Terminator Armour',
        47.00,
        '99120101400_SMCptTermArmour1.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-captain-in-terminator-armour-2023',
        '48-103',
    ),
    (
        'space-marine-lieutenant-in-phobos-armour',
        'Lieutenant in Reiver Armour',
        39.00,
        '99070101045_SMPrimarisLieutenantinPhobosArmour01.jpg',
        'https://www.warhammer.com/en-US/shop/Primaris-Lieutenant-In-Phobos-Armour-2020',
        '48-121',
    ),
    (
        'space-marine-lieutenant-with-power-sword',
        'Lieutenant with Power Sword',
        39.00,
        '99070101032_SMPrimarisLieutenantPowerSword01.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marine-Primaris-Lieutenant-With-Power-Sword-2020',
        '48-122',
    ),
    (
        'space-marine-lieutenant-with-storm-shield',
        'Lieutenant with Storm Shield',
        39.00,
        '99070101080_SMLtStormShield1.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-lieutenant-with-storm-shield-2023',
        '48-123',
    ),
    (
        'space-marine-librarian-in-phobos-armour',
        'Primaris Librarian in Phobos Armour',
        39.00,
        '99070101046_SMPrimarisLibrarianPhobosArmour01.jpg',
        'https://www.warhammer.com/en-US/shop/Primaris-Librarian-In-Phobos-Armour-2020',
        '48-125',
    ),
    (
        'space-marine-librarian-in-terminator-armour',
        'Librarian in Terminator Armour',
        42.00,
        '60010199057_LeviathanEXTRA3.jpg',
        'https://www.warhammer.com/en-US/shop/space-marine-librarian-in-terminator-armour-2023',
        '48-120',
    ),
    (
        'space-marine-ancient-in-terminator-armour',
        'Ancient in Terminator Armour',
        47.00,
        '99120101455_SPACEMARINESAncientInTerminatorArmour01.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-ancient-in-terminator-armour-2025',
        '48-99',
    ),
    # ── Infantry ──────────────────────────────────────────────────────────────
    (
        'space-marine-hellblaster-squad',
        'Hellblaster Squad',
        65.00,
        '99120101189_PrimarisHellblasters01.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Primaris-Hellblasters-2020',
        '48-117',
    ),
    (
        'space-marine-reiver-squad',
        'Reiver Squad',
        65.00,
        '99120101186_SpaceMarineRievers01.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Primaris-Reivers-2020',
        '48-127',
    ),
    (
        'space-marine-heavy-intercessor-squad',
        'Heavy Intercessor Squad',
        65.00,
        '99120101288_SMHeavyIntercessorsLead.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Heavy-Intercessors-2021',
        '48-116',
    ),
    (
        'space-marine-terminator-assault-squad',
        'Terminator Assault Squad',
        69.00,
        '99120101454_SPACEMARINESTerminatorAssaultSquad01.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-terminator-assault-squad-2025',
        '48-136',
    ),
    (
        'space-marine-centurion-devastator-squad',
        'Centurion Devastator Squad',
        80.00,
        '99120101106_CenturionDevastatorSquadNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Centurion-Devastator-Squad-2020',
        '48-108',
    ),
    (
        'space-marine-centurion-assault-squad',
        'Centurion Assault Squad',
        80.00,
        '99120101106_CenturionAssaultSquadNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Centurion-Assault-Squad-2020',
        '48-107',
    ),
    (
        'space-marine-assault-intercessors-jump-packs',
        'Assault Intercessors with Jump Packs',
        60.00,
        '99120101392_SMJumpPkIntercessors2.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-jump-pack-intercessors-2023',
        '48-100',
    ),
    (
        'space-marine-desolation-squad',
        'Desolation Squad',
        60.00,
        '99120101377_SMDesolationSquad2.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-desolation-squad-2023',
        '48-111',
    ),
    # ── Vehicles ──────────────────────────────────────────────────────────────
    (
        'space-marine-chaplain-on-bike',
        'Chaplain on Bike',
        60.00,
        '99120101273_SMPrimarisChaplainBikeLead.jpg',
        'https://www.warhammer.com/en-US/shop/Primaris-Chaplain-on-Bike-2020',
        '48-109',
    ),
    (
        'space-marine-venerable-dreadnought',
        'Venerable Dreadnought',
        65.00,
        '99120101083_VenerableDreadnoughtNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marine-Venerable-Dreadnought-2020',
        '48-137',
    ),
    (
        'space-marine-invictor-tactical-warsuit',
        'Invictor Tactical Warsuit',
        73.50,
        '99120101264_SMPrimarisInvictusTacticalWarsuit01.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marine-Primaris-Invictor-Tactical-Warsuit-2020',
        '48-118',
    ),
    (
        'space-marine-rhino',
        'Rhino',
        60.00,
        '99120101063_SpaceMarineRhinoNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Rhino-2020',
        '48-128',
    ),
    (
        'space-marine-razorback',
        'Razorback',
        60.00,
        '99120101245_SMRazorback01.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Razorback-2020',
        '48-126',
    ),
    (
        'space-marine-drop-pods',
        'Drop Pods',
        85.00,
        '99120101423_SpaceMarinesDropPods1.jpg',
        'https://www.warhammer.com/en-US/shop/space-marines-drop-pods-2025',
        '48-112',
    ),
    (
        'space-marine-land-raider-redeemer',
        'Land Raider Redeemer',
        115.00,
        '99120101344_SMLandRaiderCrusaderandRedeemerLead.jpg',
        'https://www.warhammer.com/en-US/shop/Landraider-Redeemer-2020',
        '48-119',
    ),
    (
        'space-marine-predator-destructor',
        'Predator Destructor',
        80.00,
        '99120101247_SMPredator01Alt.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Predator-2020',
        '48-124',
    ),
    # ── Storm Speeders (same physical kit — 3 build options) ──────────────────
    (
        'space-marine-storm-speeder-thunderstrike',
        'Storm Speeder Thunderstrike',
        82.00,
        '99120101274_SMThunderstrikeLead.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Storm-Speeder-Thunderstrike',
        '48-133',
    ),
    (
        'space-marine-storm-speeder-hammerstrike',
        'Storm Speeder Hammerstrike',
        82.00,
        '99120101274_SMHammerstrikeLead.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Storm-Speeder-Hammerstrike',
        '48-132',
    ),
    (
        'space-marine-storm-speeder-hailstrike',
        'Storm Speeder Hailstrike',
        82.00,
        '99120101274_SMStormspeederLead.jpg',
        'https://www.warhammer.com/en-US/shop/Space-Marines-Storm-Speeder-2020',
        '48-131',
    ),
    # ── Gladiators (same physical kit — 3 build options) ──────────────────────
    (
        'space-marine-gladiator-lancer',
        'Gladiator Lancer',
        96.00,
        '99120101282_SMGladiatorLancerTankLead.jpg',
        'https://www.warhammer.com/en-US/shop/Gladiator-Lancer-2020',
        '48-113',
    ),
    (
        'space-marine-gladiator-reaper',
        'Gladiator Reaper',
        96.00,
        '99120101282_SMGladiatorReaperTankLead.jpg',
        'https://www.warhammer.com/en-US/shop/Gladiator-Reaper-2020',
        '48-114',
    ),
    (
        'space-marine-gladiator-valiant',
        'Gladiator Valiant',
        96.00,
        '99120101282_SMGladiatorLancerReaperTankLead.jpg',
        'https://www.warhammer.com/en-US/shop/Gladiator-2020',
        '48-115',
    ),
    # ── Aircraft (same kit — Stormtalon/Stormhawk dual build) ─────────────────
    (
        'space-marine-stormtalon-gunship',
        'Stormtalon Gunship',
        69.00,
        '99120101315_StormhawkTalonInterceptorLead.jpg',
        'https://www.warhammer.com/en-US/shop/Stormtalon-Gunship-2020',
        '48-134',
    ),
    (
        'space-marine-stormhawk-interceptor',
        'Stormhawk Interceptor',
        69.00,
        '99120101315_SMStormhawkInterceptorLeadNew.jpg',
        'https://www.warhammer.com/en-US/shop/Stormhawk-Interceptor-2020',
        '48-129',
    ),
    (
        'space-marine-stormraven-gunship',
        'Stormraven Gunship',
        127.00,
        '99120101339_SMStormravenGunshipLead.jpg',
        'https://www.warhammer.com/en-US/shop/Stormraven-Gunship-2020',
        '48-130',
    ),
    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-space-marines',
        'Codex: Space Marines',
        60.00,
        '60030101061_ENGSMCodex01.jpg',
        'https://www.warhammer.com/en-US/shop/codex-space-marines-hb-2023-eng',
        '48-110',
    ),
]


class Command(BaseCommand):
    """Add generic Space Marines products missing after initial seeding."""

    help = (
        'Adds 40 generic Space Marines products missing from the DB (scraped from GW '
        'Ultramarines filter page 2026-04-03). Tagged phase-2. Seeds GW CurrentPrice. '
        'Skips upgrade sprues, bundles, starter sets, Kill Team, and Forge World. '
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        if not category_40k:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        sm_faction = Faction.objects.filter(name='Space Marines').first()
        if not sm_faction:
            self.stderr.write(self.style.ERROR(
                'Space Marines faction not found — run populate_products first.'
            ))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        created_count = 0
        updated_count = 0
        price_created = 0
        price_updated = 0

        for (slug, name, msrp, img_filename, gw_url, gw_sku) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

            product, created = Product.objects.update_or_create(
                gw_sku=gw_sku,
                defaults={
                    'name': name,
                    'slug': slug,
                    'gw_sku': gw_sku,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'category': category_40k,
                    'faction': sm_faction,
                    'is_active': True,
                    'batch_tag': 'phase-2',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} — ${msrp:.2f}'))
            if created:
                created_count += 1
            else:
                updated_count += 1

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
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_sm_phase2_products complete.\n'
            f'  Products: {created_count} created, {updated_count} updated.\n'
            f'  GW prices: {price_created} created, {price_updated} updated.'
        ))
