"""
Management command: populate_slaves_to_darkness_products

Seeds 32 Slaves to Darkness products under the Age of Sigmar category
with GW MSRP prices. (S2D-001 Spearhead, S2D-017 Chaos Warriors, and
S2D-026 Varanguard removed — pre-existing products 70-04 / 83-18 / 83-14
are the canonical records for those kits.)

Source: AOS Slaves to Darkness - GW, NK, MM.xlsx (2026-06-03)

Dual-tagged products (NOT created here — handled by
add_slaves_to_darkness_secondary_faction):
  99120201130  Daemon Prince            (primary: Chaos Space Marines 40K)
  CD-001       Be'lakor, the Dark Master (primary: Chaos Daemons 40K)
  99120201050  Chaos Spawn              (primary: Chaos Space Marines 40K)
  P-MUTALITH-VB Mutalith Vortex Beast  (primary: Thousand Sons 40K)

Shared kit notes:
  S2D-003 / S2D-006 / S2D-012  Chaos Lord on Daemonic Mount / Chaos Lord on
                                Karkadrak / Chaos Lord  share NK listing
  S2D-002 / S2D-013             Warcry: Centaurion Marshal / Centaurion Marshal
                                share NK listing
  S2D-010 / S2D-032             Darkoath Chieftain / Darkoath Chieftain on
                                Warsteed  share NK + MM listing
  S2D-023 / S2D-025             Gorebeast Chariot / Chaos Chariot share NK listing
  S2D-007 / S2D-018             Ogroid Myrmidon / Ogroid Theridons share MM listing

Idempotent — safe to re-run.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

PRODUCTS = [
    # (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)

    # ── Warcry ────────────────────────────────────────────────────────────────
    (
        'warcry-centaurion-marshal',
        'S2D-002',
        'Warcry: Centaurion Marshal',
        47.00,
        '99120201137_WCMarshallLead.jpg',
        f'{_GW}warcry-centaurion-marshal-2022',
        'Warcry: Centaurion Marshal',
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    # ⚠ Shared kit (triple): Chaos Lord on Daemonic Mount / Chaos Lord on
    #   Karkadrak / Chaos Lord  share the same NK listing (S2D-003, S2D-006, S2D-012)
    (
        'chaos-lord-on-daemonic-mount',
        'S2D-003',
        'Chaos Lord on Daemonic Mount',
        65.00,
        '99120201127_EternusMtdLordAlt1.jpg',
        f'{_GW}slaves-to-darkness-chaos-lord-on-daemonic-mount-2023',
        'Slaves to Darkness: Eternus Blade of The First Prince',
    ),
    (
        'exalted-hero-of-chaos',
        'S2D-004',
        'Exalted Hero of Chaos',
        39.00,
        '99120201132_S2DExaltedHeroofChaos01.jpg',
        f'{_GW}slaves-to-darkness-exalted-hero-of-chaos-2023',
        'Exalted Hero of Chaos Age of Sigmar',
    ),
    (
        'eternus-blade-of-the-first-prince',
        'S2D-005',
        'Eternus, Blade of The First Prince',
        65.00,
        '99120201127_Eternus1.jpg',
        f'{_GW}slaves-to-darkness-eternus-blade-of-the-first-prince-2023',
        'Eternus, Blade of The First Prince Age of Sigmar',
    ),
    # ⚠ Shared kit (triple): see S2D-003 note
    (
        'chaos-lord-on-karkadrak',
        'S2D-006',
        'Chaos Lord on Karkadrak',
        53.00,
        '99120201124_S2DLordonKarkadrak01.jpg',
        f'{_GW}slaves-to-darkness-lord-on-karkadrak-2023',
        'Chaos Lord on Karkadrak Age of Sigmar',
    ),
    # ⚠ Shared kit (dual): Ogroid Myrmidon / Ogroid Theridons share MM listing
    #   (S2D-007, S2D-018)
    (
        'ogroid-myrmidon',
        'S2D-007',
        'Ogroid Myrmidon',
        48.00,
        '99120201097_OgroidMyrmidon01.jpg',
        f'{_GW}ogroid-myrmidon-champion-2022',
        'Ogroid Myrmidon Age of Sigmar',
    ),
    (
        'darkoath-warqueen',
        'S2D-008',
        'Darkoath Warqueen',
        39.00,
        '99120201076_DrakoathWarqueen01.jpg',
        f'{_GW}Darkoath-Warqueen-Marakarr-Blood-Sky-2018',
        'Darkoath Warqueen Age of Sigmar',
    ),
    (
        'gaunt-summoner',
        'S2D-009',
        'Gaunt Summoner',
        35.00,
        '99070201020_GauntSummoner01.jpg',
        f'{_GW}Gaunt-Summoner',
        'Gaunt Summoner Age of Sigmar',
    ),
    # ⚠ Shared kit (dual): Darkoath Chieftain / Darkoath Chieftain on Warsteed
    #   share NK + MM listing (S2D-010, S2D-032)
    (
        'darkoath-chieftain',
        'S2D-010',
        'Darkoath Chieftain',
        35.00,
        '99070201023_DarkoathCheiftain01.jpg',
        f'{_GW}darkoath-chieftain',
        'Darkoath Chieftain Age of Sigmar',
    ),
    (
        'archaon-everchosen',
        'S2D-011',
        'Archaon Everchosen',
        195.00,
        '99120201045_ArchaonEverchosen01.jpg',
        f'{_GW}Archaon-Exalted',
        'Archaon Everchosen Age of Sigmar',
    ),
    # ⚠ Shared kit (triple): see S2D-003 note
    (
        'chaos-lord',
        'S2D-012',
        'Chaos Lord',
        33.50,
        '99070201004_WoCChaosLord01.jpg',
        f'{_GW}Chaos-Lord',
        'Chaos Lord Age of Sigmar',
    ),
    # ⚠ Shared kit (dual): Warcry: Centaurion Marshal / Centaurion Marshal
    #   share NK listing (S2D-002, S2D-013)
    (
        'centaurion-marshal',
        'S2D-013',
        'Centaurion Marshal',
        43.50,
        '99120201137_WCMarshallGroup.jpg',
        f'{_GW}slaves-to-darkness-centaurion-marshal-2025',
        'Centaurion Marshal Age of Sigmar',
    ),
    (
        'chaos-sorcerer-lord',
        'S2D-014',
        'Chaos Sorcerer Lord',
        40.00,
        '99120201192_S2DSorcererLord1.jpg',
        f'{_GW}slaves-to-darkness-chaos-sorcerer-lord-2024',
        'Chaos Sorcerer Lord Age of Sigmar',
    ),
    (
        'abraxia-spear-of-the-everchosen',
        'S2D-015',
        'Abraxia, Spear of the Everchosen',
        114.00,
        '99120201179_S2DAbraxiaSpearEverchosen1.jpg',
        f'{_GW}slaves-to-darkness-abraxia-spear-of-the-everchosen-2024',
        'Abraxia, Spear of the Everchosen Age of Sigmar',
    ),
    (
        'brands-oathbound',
        'S2D-016',
        "Brand's Oathbound",
        82.00,
        '99120201178_S2DBrandsOathband01.jpg',
        f'{_GW}darkoath-brands-oathbound-2024',
        "Brand's Oathbound Age of Sigmar",
    ),

    # ── Infantry ──────────────────────────────────────────────────────────────
    # ⚠ Shared kit (dual): see S2D-007 note
    (
        'ogroid-theridons',
        'S2D-018',
        'Ogroid Theridons',
        69.00,
        '99120201129_S2DOgroidTheridons01.jpg',
        f'{_GW}slaves-to-darkness-ogroid-theridons-2023',
        'Ogroid Theridons Age of Sigmar',
    ),
    (
        'chaos-knights',
        'S2D-019',
        'Chaos Knights',
        69.00,
        '99120201125_S2DChaosKnights01.jpg',
        f'{_GW}slaves-to-darkness-chaos-knights-2023',
        'Chaos Knights Age of Sigmar',
    ),

    # ── Monsters ──────────────────────────────────────────────────────────────
    (
        'mindstealer-sphiranx',
        'S2D-020',
        'Mindstealer Sphiranx',
        48.00,
        '99120201109_MindstalkerSphiranx01.jpg',
        f'{_GW}mindstealer-sphiranx-2022',
        'Mindstealer Sphiranx Age of Sigmar',
    ),
    (
        'fomoroid-crusher',
        'S2D-021',
        'Fomoroid Crusher',
        48.00,
        '99120201108_FomoroidCrusher01.jpg',
        f'{_GW}fomoroid-crusher-2022',
        'Fomoroid Crusher Age of Sigmar',
    ),
    (
        'chaotic-beasts',
        'S2D-022',
        'Chaotic Beasts',
        60.00,
        '99120201170_ChaoticBeastsUpdateLEAD.jpg',
        f'{_GW}chaotic-beasts-2022',
        'Chaotic Beasts Age of Sigmar',
    ),

    # ── War machines ──────────────────────────────────────────────────────────
    # ⚠ Shared kit (dual): Gorebeast Chariot / Chaos Chariot share NK listing
    #   (S2D-023, S2D-025)
    (
        'gorebeast-chariot',
        'S2D-023',
        'Gorebeast Chariot',
        48.00,
        '99120201051_ChaosChariot02.jpg',
        f'{_GW}Gorebeast-Chariot-2019',
        'Chaos Chariot Age of Sigmar',
    ),

    # ── Endless Spells ────────────────────────────────────────────────────────
    (
        'endless-spells-slaves-to-darkness',
        'S2D-024',
        'Endless Spells: Slaves to Darkness',
        53.00,
        '99120201111_S2DEndlessSpells01.jpg',
        f'{_GW}Endless-Spells-Slaves-To-Darkness-2019',
        'Endless Spells: Slaves to Darkness Age of Sigmar',
    ),

    # ⚠ Shared kit (dual): see S2D-023 note
    (
        'chaos-chariot',
        'S2D-025',
        'Chaos Chariot',
        48.00,
        '99120201051_ChaosChariot01.jpg',
        f'{_GW}Chaos-Chariot-2016',
        'Chaos Chariot Age of Sigmar',
    ),

    # ── Monsters (cont.) ──────────────────────────────────────────────────────
    # S2D-027: Slaughterbrute — new standalone Slaves to Darkness entry.
    # Same physical kit as Mutalith Vortex Beast (P-MUTALITH-VB in Thousand Sons).
    # No NK or MM listing (P-MUTALITH-VB has empty NK + MM URLs in DB).
    (
        'slaughterbrute',
        'S2D-027',
        'Slaughterbrute',
        96.00,
        '99120201021_Slaughterbrute01.jpg',
        f'{_GW}slaughterbrute-2025',
        'Slaughterbrute Age of Sigmar',
    ),

    # ── Terrain ───────────────────────────────────────────────────────────────
    (
        'nexus-chaotica',
        'S2D-028',
        'Nexus Chaotica',
        60.00,
        '99120299112_S2DNexusChaotica01.jpg',
        f'{_GW}slaves-to-darkness-nexus-chaotica-2024',
        'Nexus Chaotica Age of Sigmar',
    ),

    # ── Cavalry / Infantry (Darkoath) ─────────────────────────────────────────
    (
        'darkoath-fellriders',
        'S2D-029',
        'Darkoath Fellriders',
        65.00,
        '99120201183_S2DDarkoathFellriders01.jpg',
        f'{_GW}slaves-to-darkness-darkoath-fellriders-2024',
        'Darkoath Fellriders Age of Sigmar',
    ),
    (
        'darkoath-marauders',
        'S2D-030',
        'Darkoath Marauders',
        60.00,
        '99120201182_S2DDarkoathMarauders01.jpg',
        f'{_GW}slaves-to-darkness-darkoath-marauders-2024',
        'Darkoath Marauders Age of Sigmar',
    ),

    # ── Battletome ────────────────────────────────────────────────────────────
    (
        'chaos-battletome-slaves-to-darkness',
        'S2D-031',
        'Chaos Battletome: Slaves to Darkness',
        60.00,
        '60030201030_S2DBattletomeSTDED1.jpg',
        f'{_GW}battletome-slaves-to-darkness-2024-eng',
        'Chaos Battletome: Slaves to Darkness',
    ),

    # ⚠ Shared kit (dual): see S2D-010 note
    (
        'darkoath-chieftain-on-warsteed',
        'S2D-032',
        'Darkoath Chieftain on Warsteed',
        53.00,
        '99120201181_S2DChieftainOnWarsteed01.jpg',
        f'{_GW}slaves-to-darkness-darkoath-chieftain-on-warsteed-2024',
        'Darkoath Chieftain on Warsteed Age of Sigmar',
    ),

    # ── Infantry (cont.) ──────────────────────────────────────────────────────
    (
        'chaos-chosen',
        'S2D-033',
        'Chaos Chosen',
        62.50,
        '99120201128_S2DChaosChosen01.jpg',
        f'{_GW}slaves-to-darkness-chaos-chosen-2023',
        'Chaos Chosen Age of Sigmar',
    ),

    # ── Warcry (cont.) ────────────────────────────────────────────────────────
    (
        'chaos-legionnaires',
        'S2D-034',
        'Chaos Legionnaires',
        60.00,
        '99120201138_WCLegionsGroup.jpg',
        f'{_GW}slaves-to-darkness-chaos-legionaires-2025',
        'Chaos Legionnaires Warcry',
    ),

    # ── Heroes (cont.) ────────────────────────────────────────────────────────
    (
        'darkoath-wilderfiend',
        'S2D-035',
        'Darkoath Wilderfiend',
        60.00,
        '99120201180_S2DWilderfiend01.jpg',
        f'{_GW}slaves-to-darkness-darkoath-wilderfiend-2024',
        'Darkoath Wilderfiend Age of Sigmar',
    ),
]


class Command(BaseCommand):
    """Seed Slaves to Darkness faction products and GW MSRP prices."""

    help = 'Seeds Slaves to Darkness products (32 records, S2D-002 through S2D-035) and GW prices. Idempotent.'

    def handle(self, *args, **options):
        """Run the command."""
        category_aos = Category.objects.get(slug='age-of-sigmar')

        std_faction, faction_created = Faction.objects.get_or_create(
            slug='slaves-to-darkness',
            defaults={'name': 'Slaves to Darkness', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Slaves to Darkness faction.')

        gw = Retailer.objects.filter(name='Games Workshop').first()
        if not gw:
            self.stdout.write(self.style.ERROR('Games Workshop retailer not found'))
            return

        prod_created = prod_updated = gw_created = gw_updated = 0

        for slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name in PRODUCTS:
            image_url = _IMG.format(filename=image_filename) if image_filename else ''

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'faction': std_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'slaves-to-darkness',
                    'is_active': True,
                },
            )
            if created:
                prod_created += 1
            else:
                prod_updated += 1
            self.stdout.write(f'  {"Created" if created else "Updated"}: {name} ({gw_sku})')

            _, price_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=gw,
                defaults={
                    'price': msrp,
                    'url': gw_url,
                    'listing_title': name,
                    'in_stock': True,
                    'not_available': False,
                    'last_seen': timezone.now(),
                },
            )
            if price_created:
                gw_created += 1
            else:
                gw_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_slaves_to_darkness_products complete. '
            f'Products: {prod_created} created, {prod_updated} updated. '
            f'GW prices: {gw_created} created, {gw_updated} updated.'
        ))
