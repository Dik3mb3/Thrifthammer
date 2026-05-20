"""
Management command: populate_necrons_phase3_products

Creates / updates all Necrons phase-3 product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates UnitType entries so
Necrons appears fully in the Army Cost Calculator.

Phase-3 covers every NEW product on the GW en-US Necrons shop page as of
2026-04-05 that is NOT already in the database.

Existing products already in DB (skipped by slug):
  necron-canoptek-spyder, necron-combat-patrol, necron-ctan-shard-of-the-void-dragon,
  necron-doom-scythe, necron-doomsday-ark, necron-flayed-ones, necron-immortals,
  necron-lychguard, necron-monolith, necron-overlord (Overlord w/ Translocation Shroud),
  necron-psychomancer, necron-royal-warden, necron-warriors

Kill Team boxes excluded (Kill Team: Hierotek Circle, Kill Team: Canoptek Circle).

Dual-kit products:
  - Night Scythe / Doom Scythe        → same GW URL; Doom Scythe in DB, Night Scythe new
  - Catacomb Command Barge /
    Annihilation Barge                 → same physical dual-build kit; both new slugs
  - Ghost Ark / Doomsday Ark          → same dual-build kit; Doomsday Ark in DB, Ghost Ark new
  - Obelisk & Transcendent C'tan /
    Tesseract Vault                    → same dual-build kit; both new slugs

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_necrons_phase3_products
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
PRODUCTS = [

    # ── Codex ─────────────────────────────────────────────────────────────────
    (
        'codex-necrons',
        'Codex: Necrons',
        '',
        60.00,
        '60030110008_NECCodex1.jpg',
        'https://www.warhammer.com/en-US/shop/codex-necrons-hb-eng-2023',
        'Codex Necrons Warhammer 40k',
    ),

    # ── HQ / Characters ───────────────────────────────────────────────────────
    (
        'necron-chronomancer',
        'Chronomancer',
        'prod4900148',
        43.50,
        '99070110003_NECChronomancerLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necrons-Chronomancer-2021',
        'Necron Chronomancer Warhammer 40k',
    ),
    (
        'necron-cryptek',
        'Cryptek',
        'prod4390141',
        39.00,
        '99070110005_NECCryptekLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Cryptek-2020',
        '',
    ),
    (
        'necron-hexmark-destroyer',
        'Hexmark Destroyer',
        'prod4390148',
        39.00,
        '99120110048_HexmarkDestroyerLead.jpg',
        'https://www.warhammer.com/en-US/shop/Hexmark-Destroyer-2020',
        '',
    ),
    (
        'necron-lokhust-heavy-destroyer',
        'Lokhust Heavy Destroyer',
        'prod4390145',
        39.00,
        '99120110044_LokhustHeavyDestroyerLead.jpg',
        'https://www.warhammer.com/en-US/shop/Lokhust-Heavy-Destroyer-2020',
        '',
    ),
    (
        'necron-szarekh-the-silent-king',
        'Szarekh, The Silent King',
        'prod4390152',
        175.00,
        '99120110047_NECSzarekhSilentKingLead.jpg',
        'https://www.warhammer.com/en-US/shop/Szarekh-The-Silent-King-2020',
        'Szarekh Silent King Necrons Warhammer',
    ),
    (
        'necron-illuminor-szeras',
        'Illuminor Szeras',
        'prod4390160',
        60.00,
        '99120110049_IlluminorSzerasLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necrons-Illuminor-Szeras-2020',
        'Illuminor Szeras Necrons Warhammer',
    ),
    (
        'necron-orikan-the-diviner',
        'Orikan the Diviner',
        'prod4900151',
        48.00,
        '99120110081_OrikanDiviner1.jpg',
        'https://www.warhammer.com/en-US/shop/necrons-orikan-the-diviner-2023',
        'Orikan Diviner Necrons Warhammer',
    ),
    (
        'necron-imotekh-the-stormlord',
        'Imotekh the Stormlord',
        'prod4900149',
        48.00,
        '99120110078_NECImotekhTheStormlord01.jpg',
        'https://www.warhammer.com/en-US/shop/necrons-imotekh-the-stormlord-2023',
        'Imotekh Stormlord Necrons Warhammer',
    ),
    (
        'necron-trazyn-the-infinite',
        'Trazyn the Infinite',
        'prod2791068',
        33.50,
        '99800110009_TrazynTheInfiniteNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Trazyn-the-Infinite',
        'Trazyn the Infinite Necrons Warhammer',
    ),
    (
        'necron-overlord-with-tachyon-arrow',
        'Overlord with Tachyon Arrow',
        'prod4900150',
        42.00,
        '99070110006_OverlordTachyonArrow1.jpg',
        'https://www.warhammer.com/en-US/shop/necrons-overlord-2023',
        'Necron Overlord Tachyon Arrow Warhammer',
    ),
    (
        'necron-nekrosor-ammentar',
        'Nekrosor Ammentar',
        'P-241017',
        65.00,
        '99120110089_NecronsNekrosorAmmentar01.jpg',
        'https://www.warhammer.com/en-US/shop/necrons-nekrosor-ammentar-2026',
        'Nekrosor Ammentar Necrons Warhammer',
    ),

    # ── Troops / Battleline ───────────────────────────────────────────────────
    (
        'necron-deathmarks',
        'Deathmarks',
        'prod4390142',
        48.00,
        '99120110057_NECImmortalsGroup2.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Deathmarks-2020',
        'Necron Deathmarks Warhammer',
    ),
    (
        'necron-triarch-praetorians',
        'Triarch Praetorians',
        'prod4390144',
        60.00,
        '99120110058_NecronsTriarchPraetoriansLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Triarch-Praetorians-2020',
        '',
    ),
    (
        'necron-lokhust-destroyer-squadron',
        'Lokhust Destroyer Squadron',
        'prod4390155',
        60.00,
        '99120110071_NecronDestroyerretoolGroup.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Destroyer-Squadron-2020',
        'Necron Lokhust Destroyers Warhammer',
    ),
    (
        'necron-ophydian-destroyers',
        'Ophydian Destroyers',
        'prod4390154',
        65.00,
        '99120110053_NECOphydianDestroyersLead.jpg',
        'https://www.warhammer.com/en-US/shop/Ophydian-Destroyers-2020',
        '',
    ),
    (
        'necron-skorpekh-destroyers',
        'Skorpekh Destroyers',
        'prod4390150',
        65.00,
        '99120110051_SkorpekhDestroyersLead.jpg',
        'https://www.warhammer.com/en-US/shop/Skorpekh-Destroyers-2020',
        '',
    ),
    (
        'necron-royal-court',
        'Necrons Royal Court',
        'prod4900147',
        130.00,
        '99120110072_NECRoyalCourtLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necrons-Royal-Court-2021',
        'Necrons Royal Court Warhammer',
    ),
    (
        'necron-tomb-blades',
        'Tomb Blades',
        'prod3940162',
        60.00,
        '99120110059_NECTombBladesLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Tomb-Blades-2020',
        '',
    ),

    # ── Elites / Fast Attack ──────────────────────────────────────────────────
    (
        'necron-canoptek-wraiths',
        'Canoptek Wraiths',
        '49-18',
        65.00,
        '99120110060_NECCanoptekWraithsLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Canoptek-Wraiths-2020',
        '',
    ),

    # ── Heavy Support ─────────────────────────────────────────────────────────
    (
        'necron-canoptek-doomstalker',
        'Canoptek Doomstalker',
        'prod4390146',
        53.00,
        '99120110045_CanoptekDoomstalkerLead.jpg',
        'https://www.warhammer.com/en-US/shop/Canoptek-Doomstalker-2020',
        '',
    ),
    (
        'necron-convergence-of-dominion',
        'Convergence of Dominion',
        'prod4390153',
        69.00,
        '99120110066_ConvergenceofDominionLead.jpg',
        'https://www.warhammer.com/en-US/shop/Convergence-of-Dominion-2020',
        'Convergence of Dominion Necrons Warhammer',
    ),
    (
        'necron-triarch-stalker',
        'Triarch Stalker',
        'prod4390143',
        65.00,
        '99120110058_NecronTriarchStalkerLead.jpg',
        'https://www.warhammer.com/en-US/shop/Triarch-Stalker-2020',
        '',
    ),

    # ── Vehicles / Flyers ─────────────────────────────────────────────────────
    (
        'necron-catacomb-command-barge',
        'Necron Catacomb Command Barge',
        'prod4390158',
        60.00,
        '99120110064_CatacombCommandBargeLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Catacomb-Command-Barge-2020',
        'Necron Catacomb Command Barge Warhammer',
    ),
    (
        'necron-annihilation-barge',
        'Annihilation Barge',
        'prod4390158',
        60.00,
        '99120110064_CatacombAnnihilationBargeLead.jpg',
        # Same dual-build kit as Catacomb Command Barge
        'https://www.warhammer.com/en-US/shop/Necron-Annihilation-Barge-2020',
        'Necron Annihilation Barge Warhammer',
    ),
    (
        'necron-ghost-ark',
        'Ghost Ark',
        'prod4390157',
        69.00,
        '99120110063_NECGhostArkLead.jpg',
        'https://www.warhammer.com/en-US/shop/Ghost%20Ark-2020',
        'Necron Ghost Ark Warhammer',
    ),
    (
        'necron-night-scythe',
        'Night Scythe',
        'prod4390159',
        77.00,
        '99120110065_DoomScytheLead.jpg',
        # Same dual-build kit as Doom Scythe (necron-doom-scythe already in DB)
        'https://www.warhammer.com/en-US/shop/Necron-Doom-Scythe-2020',
        'Necron Night Scythe Warhammer',
    ),

    # ── Lords of War / Fortifications ─────────────────────────────────────────
    (
        'necron-obelisk',
        'Obelisk & Transcendent C\'tan',
        'prod3590140',
        197.00,
        '99120110026_NecronObeliskLead.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-Obelisk',
        'Necron Obelisk Transcendent Ctan Warhammer',
    ),
    (
        'necron-tesseract-vault',
        'Tesseract Vault',
        'prod3590140',
        197.00,
        '99120110026_NecronTesseract01.jpg',
        # Same dual-build kit as Obelisk
        'https://www.warhammer.com/en-US/shop/NecronsTesseract-Vault',
        'Necron Tesseract Vault Warhammer',
    ),
    (
        'necron-seraptek-heavy-construct',
        'Seraptek Heavy Construct with Synaptic Obliterators',
        'P-203538',
        400.00,
        '99860110022_SeraptekHeavyConstructSynapticObliteratorsVehicle1.jpg',
        'https://www.warhammer.com/en-US/shop/seraptek-heavy-construct-with-synaptic-obliterators-2025',
        'Seraptek Heavy Construct Necrons Warhammer',
    ),

    # ── C'tan Shards ──────────────────────────────────────────────────────────
    (
        'necron-ctan-shard-of-the-deceiver',
        "C'tan Shard of The Deceiver",
        'prod2901178',
        53.00,
        '99810110003_TheDeceiverNEW01.jpg',
        'https://www.warhammer.com/en-US/shop/Necron-C-tan-Shard-of-The-Deceiver',
        "C'tan Deceiver Necrons Warhammer",
    ),
    (
        'necron-ctan-shard-of-the-nightbringer',
        "C'tan Shard of the Nightbringer",
        'P-241016',
        130.00,
        '99120110088_NecronsCtanShardOfTheNightbringer01.jpg',
        'https://www.warhammer.com/en-US/shop/necrons-ctan-shard-of-the-nightbringer-2026',
        "C'tan Nightbringer Necrons Warhammer",
    ),
]


class Command(BaseCommand):
    """Populate Necrons phase-3 products, GW prices, and UnitType entries."""

    help = (
        'Creates Necrons phase-3 products for all new kits on the GW Necrons page. '
        'Skips the 13 existing DB slugs. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        category_40k = Category.objects.filter(name='Warhammer 40,000').first()
        if not category_40k:
            self.stderr.write(self.style.ERROR(
                'Warhammer 40,000 category not found — run populate_products first.'
            ))
            return

        necrons_faction = Faction.objects.filter(name='Necrons').first()
        if not necrons_faction:
            self.stderr.write(self.style.ERROR(
                'Necrons faction not found — run populate_products first.'
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
                    'faction': necrons_faction,
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
                product=product,
                faction=necrons_faction,
                defaults={
                    'name': name,
                    'category': role,
                    # points_cost excluded — preserved on update so GitHub Actions
                    # seeded values (seed_necrons_stats) are not wiped on every
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
            f'\npopulate_necrons_phase3_products complete.\n'
            f'  Products : {product_created} created, {product_updated} updated\n'
            f'  GW prices: {price_created} created, {price_updated} updated\n'
            f'  UnitTypes: {unit_created} created, {unit_updated} updated'
        ))
