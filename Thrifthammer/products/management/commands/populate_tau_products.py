"""
Management command: populate_tau_products

Creates / updates all T'au Empire product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 37 products from the Tau - GW, NK, MM, Amazon.xlsx spreadsheet (2026-05-13).

Category: Warhammer 40,000
Faction:  T'au Empire

Dual-kit products (share retailer URLs — same physical box):
  - Fire Warriors Breacher Team / Fire Warriors Strike Team  (TE-007 / TE-008)
  - Razorshark Strike Fighter / Sun Shark Bomber             (TE-017 / TE-019)
  - Sky Ray Gunship / Hammerhead Gunship                    (TE-018 / existing 56-10)
  - Farstalker Kinband / Vespid Stingwings                  (TE-021 / TE-022)
    also exist as KT-023 / KT-024 under Kill Team category

Images are baked in as one-off GW CDN URLs — never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_tau_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-13.
# ebay_search_name is blank unless the default name gives poor eBay results.
PRODUCTS = [

    # ── Terrain ──────────────────────────────────────────────────────────────
    (
        'tau-empire-tidewall-shieldline',
        'TE-001',
        "T'au Empire Tidewall Shieldline",
        85.00,
        '99120113075_TidewallShieldlineLead.jpg',
        'https://www.warhammer.com/en-US/shop/Tidewall-Shieldline',
        '',
    ),
    (
        'tau-empire-tidewall-droneport',
        'TE-013',
        "T'au Empire Tidewall Droneport",
        69.00,
        '99120113049_TauDroneport01.jpg',
        'https://www.warhammer.com/en-US/shop/Tidewall-Droneport',
        '',
    ),

    # ── Kroot units ──────────────────────────────────────────────────────────
    (
        'tau-empire-kroot-hounds',
        'TE-002',
        "T'au Empire Kroot Hounds",
        43.50,
        '99120113090_KrootHounds1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-kroot-hounds-2024',
        '',
    ),
    (
        'tau-empire-kroot-lone-spear',
        'TE-023',
        "T'au Empire Kroot Lone-Spear",
        60.00,
        '99120113092_KrootLoneSpear1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-kroot-lone-spear-2024',
        '',
    ),
    (
        'tau-empire-kroot-trail-shaper',
        'TE-024',
        "T'au Empire Kroot Trail Shaper",
        35.00,
        '99070113007_KrootTrailShaper1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-kroot-trail-shaper-2024',
        '',
    ),
    (
        'tau-empire-kroot-flesh-shaper',
        'TE-025',
        "T'au Empire Kroot Flesh Shaper",
        35.00,
        '99070113008_KrootFleshShaper1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-kroot-flesh-shaper-2024',
        '',
    ),
    (
        'tau-empire-kroot-war-shaper',
        'TE-026',
        "T'au Empire Kroot War Shaper",
        39.00,
        '99120113093_KrootWarShaper1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-kroot-war-shaper-2024',
        '',
    ),
    (
        'tau-empire-krootox-rider',
        'TE-027',
        "T'au Empire Krootox Rider",
        48.00,
        '99120113087_KrootRider1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-krootox-rider-2024',
        '',
    ),
    (
        'tau-empire-krootox-rampagers',
        'TE-028',
        "T'au Empire Krootox Rampagers",
        65.00,
        '99120113088_KrootRampagers1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-krootox-rampagers-2024',
        '',
    ),
    (
        'tau-empire-kroot-carnivores',
        'TE-037',
        "T'au Empire Kroot Carnivores",
        60.00,
        '99120113089_KrootCarnivores1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-kroot-carnivore-squad-2024',
        '',
    ),

    # ── Characters ───────────────────────────────────────────────────────────
    (
        'tau-empire-the-twin-lance',
        'TE-003',
        "T'au Empire The Twin Lance",
        111.00,
        '99120113101_TAUTwinLance1.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-the-twin-lance-2026',
        '',
    ),
    (
        'tau-empire-commander-farsight',
        'TE-004',
        "T'au Empire Commander Farsight",
        69.00,
        '99120113094_TAUBoardingPatrol01.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-commander-farsight-2023',
        '',
    ),
    (
        'tau-empire-darkstrider',
        'TE-005',
        "T'au Empire Darkstrider",
        39.00,
        '99070113005_TauDarkstriderLead.jpg',
        'https://www.warhammer.com/en-US/shop/tau-empire-darkstrider-2022',
        '',
    ),
    (
        'tau-empire-commander-shadowsun',
        'TE-006',
        "T'au Empire Commander Shadowsun",
        60.00,
        '99120113066_ComShadowsun01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-Commander-Shadowsun-2020',
        '',
    ),
    (
        'tau-empire-cadre-fireblade',
        'TE-010',
        "T'au Empire Cadre Fireblade",
        35.00,
        '99070113006_CadreFirebladeLead.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-Cadre-Fireblade-2017',
        '',
    ),

    # ── Infantry ─────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Fire Warriors Breacher Team / Strike Team share the same box
    (
        'tau-empire-fire-warriors-breacher-team',
        'TE-007',
        "T'au Empire Fire Warriors Breacher Team",
        60.00,
        '99120113039_TauBreacherTeam01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Fire-Warriors-Breacher-Team-2017',
        '',
    ),
    (
        'tau-empire-fire-warriors-strike-team',
        'TE-008',
        "T'au Empire Fire Warriors Strike Team",
        60.00,
        '99120113039_TauFirewarriorTeam01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-Fire-Warriors-2017',
        '',
    ),
    (
        'tau-empire-tactical-drones',
        'TE-014',
        "T'au Empire Tactical Drones",
        20.00,
        '99070113002_TauEmpireDrones01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Drones-2015',
        '',
    ),

    # ── Battlesuits ──────────────────────────────────────────────────────────
    (
        'tau-empire-commander',
        'TE-009',
        "T'au Empire Commander",
        65.00,
        '99120113037_TauEmpireCommanderColdStar01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-Commander-2017',
        'Tau Empire Commander Coldstar',
    ),
    (
        'tau-empire-ghostkeel-battlesuit',
        'TE-015',
        "T'au Empire XV95 Ghostkeel Battlesuit",
        96.00,
        '99120113035_TauEmpireGhostkeel01.jpg',
        'https://www.warhammer.com/en-US/shop/XV95-Ghostkeel-Battlesuit',
        'Tau Ghostkeel Battlesuit',
    ),
    (
        'tau-empire-stormsurge',
        'TE-016',
        "T'au Empire KV128 Stormsurge",
        195.00,
        '99120113036_TauKV128Stormsurge01.jpg',
        'https://www.warhammer.com/en-US/shop/KV128-Stormsurge',
        '',
    ),
    (
        'tau-empire-firesight-team',
        'TE-035',
        "T'au Empire Firesight Team",
        53.00,
        '99810113001_SniperDroneTeamNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-Sniper-Drone-Team',
        '',
    ),

    # ── Forge World battlesuits ───────────────────────────────────────────────
    (
        'tau-empire-taunar-supremacy-armour-heavy-rail-cannon-array',
        'TE-011',
        "T'au Empire Ta'unar Supremacy Armour Heavy Rail Cannon Array",
        124.00,
        '99560113054_KX139TaunarSupremacyRailCannon01.jpg',
        "https://www.warhammer.com/en-US/shop/Tau-KX139-Taunar-Heavy-Rail-Cannon-Array",
        '',
    ),
    (
        'tau-empire-taunar-nexus-missile-system',
        'TE-012',
        "T'au Empire Ta'unar Nexus Missile System",
        124.00,
        '99560113052_TauNexusMissile01.jpg',
        'https://www.warhammer.com/en-US/shop/KX139-Nexus-Meteor',
        '',
    ),
    (
        'tau-empire-taunar-fusion-eradicator',
        'TE-031',
        "T'au Empire Ta'unar Supremacy Armour Fusion Eradicator",
        64.00,
        '99020187141_Supremacysuitfusioneradicator01.jpg',
        "https://www.warhammer.com/en-US/shop/KX139-Ta'unar-Supremacy-Armour-Fusion-Eradicator",
        '',
    ),
    (
        'tau-empire-taunar-pulse-ordnance-multi-driver',
        'TE-032',
        "T'au Empire Ta'unar Supremacy Armour Pulse Ordnance Multi-driver",
        124.00,
        '99020187139_KX139TaunarSupremacyArmourPulseOrdnanceMultidriver01.jpg',
        "https://www.warhammer.com/en-US/shop/KX139-Ta'unar-Supremacy-Armour-Pulse-Ordnance-Multi-driver",
        '',
    ),
    (
        'tau-empire-taunar-tri-axis-ion-cannon',
        'TE-033',
        "T'au Empire Ta'unar Supremacy Armour Tri-axis Ion Cannon",
        64.00,
        '99020187138_KX139TaunarSupremacyArmourTriaxisIonCannon02.jpg',
        "https://www.warhammer.com/en-US/shop/KX139-Ta'unar-Supremacy-Armour-Tri-axis-Ion-Cannon",
        '',
    ),

    # ── Aircraft ─────────────────────────────────────────────────────────────
    # ⚠ Dual kit: Razorshark Strike Fighter / Sun Shark Bomber share the same box
    (
        'tau-empire-razorshark-strike-fighter',
        'TE-017',
        "T'au Empire Razorshark Strike Fighter",
        89.00,
        '99120113029_RazorsharkFighter01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-Razorshark-Strike-Fighter',
        'Tau Sun Shark Razorshark',
    ),
    (
        'tau-empire-sun-shark-bomber',
        'TE-019',
        "T'au Empire Sun Shark Bomber",
        89.00,
        '99120113029_SunsharkBomber01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-Sun-Shark-Bomber',
        'Tau Sun Shark Razorshark',
    ),
    # ⚠ Dual kit: Sky Ray Gunship / Hammerhead Gunship share the same box
    #   Hammerhead already exists in DB as 56-10
    (
        'tau-empire-sky-ray-gunship',
        'TE-018',
        "T'au Empire Sky Ray Gunship",
        80.00,
        '99120113028_TauSkyray01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-Sky-Ray-Missile-Defence-Gunship',
        '',
    ),
    (
        'tau-empire-tiger-shark',
        'TE-030',
        "T'au Empire Tiger Shark AX-1-0",
        330.00,
        '99560113055_TauAX1Tigershark01NEW.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Tigershark-AX-1-0-2017',
        '',
    ),
    (
        'tau-empire-manta',
        'TE-034',
        "T'au Empire Manta",
        2080.00,
        '99590113031_TauManta01NEW.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Manta',
        '',
    ),

    # ── Vehicles ─────────────────────────────────────────────────────────────
    (
        'tau-empire-devilfish',
        'TE-020',
        "T'au Empire Devilfish",
        65.00,
        '99120113074_TAUDevilfishLead.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-TY7-Devilfish-2015',
        '',
    ),
    (
        'tau-empire-piranha',
        'TE-036',
        "T'au Empire Piranha",
        43.50,
        '99120113042_TauPirahna01.jpg',
        'https://www.warhammer.com/en-US/shop/Tau-Empire-TX4-Piranha-2015',
        '',
    ),

    # ── Kill Team (dual-system — also KT-023 / KT-024 under Kill Team) ───────
    (
        'tau-empire-farstalker-kinband',
        'TE-021',
        'Kill Team: Farstalker Kinband',
        69.00,
        '99120114003_KTFarstalkerKinband2.jpg',
        'https://www.warhammer.com/en-US/shop/kill-team-farstalker-kinband-2024',
        '',
    ),
    (
        'tau-empire-vespid-stingwings',
        'TE-022',
        'Kill Team: Vespid Stingwings',
        69.00,
        '60010199070_KTHivestorm3New.jpg',
        'https://www.warhammer.com/en-US/shop/kill-team-tau-empire-vespid-stingwings-2024',
        '',
    ),

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-tau-empire',
        'TE-029',
        "Codex: T'au Empire",
        60.00,
        '60030113014_EngTAUCodex01.jpg',
        'https://www.warhammer.com/en-US/shop/codex-tau-empire-2024-eng',
        '',
    ),
]


class Command(BaseCommand):
    """Populate T'au Empire products (TE-001 to TE-037)."""

    help = (
        "Creates / updates 37 T'au Empire products and seeds GW prices at MSRP. "
        'Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_40k = Category.objects.get(slug='warhammer-40000')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        try:
            tau_faction = Faction.objects.get(slug='tau-empire')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                "T'au Empire faction not found — run populate_products first."
            ))
            return

        gw_retailer = Retailer.objects.filter(name='Games Workshop').first()
        if not gw_retailer:
            self.stdout.write(self.style.WARNING(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))

        product_created = product_updated = price_created = price_updated = 0

        for (slug, gw_sku, name, msrp, img_filename, gw_url, ebay_name) in PRODUCTS:
            image_url = _IMG.format(filename=img_filename)

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
                    'faction': tau_faction,
                    'is_active': True,
                    'batch_tag': 'tau-empire',
                },
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {status}: {name} ({gw_sku})'))
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
                    },
                )
                if p_created:
                    price_created += 1
                else:
                    price_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_tau_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
