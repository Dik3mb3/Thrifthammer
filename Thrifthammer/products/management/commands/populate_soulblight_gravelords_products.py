"""
Management command: populate_soulblight_gravelords_products

Creates / updates all Soulblight Gravelords product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP, and creates the Soulblight Gravelords
faction if it does not yet exist.

Covers all 37 products from the AOS Soulblight - GW, NK, MM.xlsx (2026-06-08).

Category: Age of Sigmar
Faction:  Soulblight Gravelords

Dual-kit products (share retailer URLs — same physical box):
  - Vengorian Lord / Lauka Vai, Mother of Nightmares       (SG-009 / SG-012)
  - Neferata, Mortarch of Blood / Mannfred von Carstein,
    Mortarch of Night                                       (SG-014 / SG-015)
  - Mortis Engine / Coven Throne                           (SG-017 / SG-018)

Images are baked in as one-off GW CDN URLs — never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_soulblight_gravelords_products
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'
_GW = 'https://www.warhammer.com/en-US/shop/'

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-06-08.
# ebay_search_name is blank where the product name is sufficient for eBay.
PRODUCTS = [

    # ── Warhammer+ Exclusives ────────────────────────────────────────────────
    (
        'soulblight-gravelords-the-summons',
        'SG-001',
        'Soulblight Gravelords – The Summons',
        45.00,
        '99120207203_WarhammerPlusSoulblightSummons1.jpg',
        f'{_GW}warhammer-plus-soulblight-gravelords-the-summons-2025-year-5',
        '',
    ),
    (
        'soulblight-gravelords-karlina-von-carstein',
        'SG-002',
        'Soulblight Gravelords – Karlina von Carstein',
        42.00,
        '99120207145_WHKarlinaVonCarstein01.jpg',
        f'{_GW}warhammer-plus-karlina-von-carstein-year3-2023',
        '',
    ),

    # ── Spearhead ────────────────────────────────────────────────────────────
    (
        'spearhead-soulblight-gravelords-deathrattle-tomb-host',
        'SG-003',
        'Spearhead: Soulblight Gravelords – Deathrattle Tomb Host',
        150.00,
        '99120207176_SoulblightGravelordsDeathrattleTombHostSpearhead1.jpg',
        f'{_GW}spearhead-soulblight-gravelords-deathrattle-tomb-host-2025',
        '',
    ),

    # ── Heroes ────────────────────────────────────────────────────────────────
    (
        'ivya-volga-the-outcast',
        'SG-004',
        'Ivya Volga, the Outcast',
        39.00,
        '99120207101_GravelordsIvyaVolga1.jpg',
        f'{_GW}soulblight-gravelords-ivya-volga-2023',
        'Ivya Volga, the Outcast Age of Sigmar',
    ),
    (
        'lady-annika-the-thirsting-blade',
        'SG-005',
        'Lady Annika, the Thirsting Blade',
        39.00,
        '99120207108_LadyAnnikaLead.jpg',
        f'{_GW}Lady-Annika-The-Thirsting-Blade-2021',
        'Lady Annika Soulblight Gravelords',
    ),
    (
        'radukar-the-beast',
        'SG-007',
        'Radukar the Beast',
        60.00,
        '99120207089_RadukarBeastLead.jpg',
        f'{_GW}Soulblight-Gravelords-Radukar-The-Beast-2021',
        'Radukar the Beast Age of Sigmar',
    ),
    (
        'belladamma-volga-first-of-the-vyrkos',
        'SG-008',
        'Belladamma Volga, First of the Vyrkos',
        60.00,
        '99120207088_BelladonnaVolgaFirstofVyrkosLead.jpg',
        f'{_GW}Belladamma-Volga-First-Of-The-Vyrkos-2021',
        'Belladamma Volga, First of the Vyrkos Age of Sigmar',
    ),
    # ⚠ Dual kit: Vengorian Lord / Lauka Vai share the same box (SG-009 / SG-012)
    (
        'vengorian-lord',
        'SG-009',
        'Vengorian Lord',
        73.50,
        '99120207086_VangLordLead.jpg',
        f'{_GW}Vengorian-Lord-2021',
        'Lauka Vai, Mother of Nightmares Age of Sigmar',
    ),
    # ⚠ Dual kit: Lauka Vai / Vengorian Lord share the same box (SG-012 / SG-009)
    (
        'lauka-vai-mother-of-nightmares',
        'SG-012',
        'Lauka Vai, Mother of Nightmares',
        73.50,
        '99120207086_LaukaVaiMotherofNightmaresLead.jpg',
        f'{_GW}Lauka-Vai-Mother-Of-Nightmares-2021',
        'Lauka Vai, Mother of Nightmares Age of Sigmar',
    ),
    (
        'kritza-the-rat-prince',
        'SG-032',
        'Kritza, the Rat Prince',
        39.00,
        '99120207087_KritzaRatPrinceLead.jpg',
        f'{_GW}Kritza-The-Rat-Prince-2021',
        'Kritza the Rat Prince Soulblight Gravelords',
    ),
    (
        'radukar-the-wolf',
        'SG-033',
        'Radukar the Wolf',
        43.50,
        '99070207017_RadukarWolfLead.jpg',
        f'{_GW}Soulblight-Gravelords-Radukar-The-Wolf-2021',
        'Radukar the Wolf Soulblight Gravelords',
    ),
    (
        'vampire-lord',
        'SG-035',
        'Vampire Lord',
        35.00,
        '99070207014_VampireLordLead.jpg',
        f'{_GW}Soulblight-Gravelords-Vampire-Lord-2021',
        'Vampire Lord Age of Sigmar',
    ),
    (
        'vampire-lord-on-nightmare-steed',
        'SG-027',
        'Vampire Lord on Nightmare Steed',
        60.00,
        '99120207181_SoulblightGravelordsVampireLordonNightmareSteed1.jpg',
        f'{_GW}soulblight-gravelords-vampire-lord-on-nightmare-steed-2025',
        'Vampire Lord on Nightmare Steed Age of Sigmar',
    ),
    (
        'wight-lord-on-skeletal-steed',
        'SG-021',
        'Wight Lord on Skeletal Steed',
        53.00,
        '99120207180_SoulblightGravelordsWightKingonSkeletalSteed1.jpg',
        f'{_GW}soulblight-gravelords-wight-king-on-skeletal-steed-2025',
        'Wight Lord on Skeletal Steed Age of Sigmar',
    ),
    (
        'prince-vhordrai-lord-of-the-crimson-keep',
        'SG-028',
        'Prince Vhordrai, Lord of the Crimson Keep',
        195.00,
        '99120207177_SoulblightGravelordsPrinceVhordraiLordoftheCrimsonKeep1.jpg',
        f'{_GW}soulblight-gravelords-prince-vhordrai-lord-of-the-crimson-keep-2025',
        'Prince Vhordrai, Lord of the Crimson Keep Age of Sigmar',
    ),
    (
        'sekhar-fang-of-nulahmia',
        'SG-030',
        'Sekhar, Fang of Nulahmia',
        47.00,
        '99120207148_S2DSekharFangOfNulahmia01.jpg',
        f'{_GW}soulblight-gravelords-sekhar-fang-of-nulahmia-2024',
        'Sekhar, Fang of Nulahmia Age of Sigmar',
    ),

    # ── Deathlords ───────────────────────────────────────────────────────────
    # ⚠ Dual kit: Neferata / Mannfred share the same box (SG-014 / SG-015)
    (
        'neferata-mortarch-of-blood',
        'SG-014',
        'Neferata, Mortarch of Blood',
        94.00,
        '99120207031_DeathLordsMortarchsNeferata01.jpg',
        f'{_GW}Deathlords-Mortarchs-Neferata',
        'Deathlords Mortarch Age of Sigmar',
    ),
    # ⚠ Dual kit: Mannfred / Neferata share the same box (SG-015 / SG-014)
    (
        'mannfred-von-carstein-mortarch-of-night',
        'SG-015',
        'Mannfred von Carstein, Mortarch of Night',
        94.00,
        '99120207031_DeathLordsMortarchsMannfred01.jpg',
        f'{_GW}Deathlords-Mortarchs-Mannfred',
        'Deathlords Mortarch Age of Sigmar',
    ),
    (
        'nagash-supreme-lord-of-the-undead',
        'SG-016',
        'Nagash, Supreme Lord of the Undead',
        150.00,
        '99120207029_DeathLordsNagashSupremelordoftheUndead01.jpg',
        f'{_GW}Deathlords-Nagash',
        'Nagash, Supreme Lord of the Undead Age of Sigmar',
    ),

    # ── Units ────────────────────────────────────────────────────────────────
    (
        'blood-knights',
        'SG-010',
        'Blood Knights',
        73.50,
        '99120207095_SBGravelordsBloodKnightsLead.jpg',
        f'{_GW}Soulblight-Gravelords-Blood-Knights-2021',
        'Blood Knights Age of Sigmar',
    ),
    (
        'fell-bats',
        'SG-011',
        'Fell Bats',
        60.00,
        '99120207094_SBGravelordsFellBatsLead.jpg',
        f'{_GW}Soulblight-Gravelords-Fell-Bats-2021',
        'Fell Bats Age of Sigmar',
    ),
    (
        'dire-wolves',
        'SG-006',
        'Dire Wolves',
        60.00,
        '99120207142_SBGLDireWolves2.jpg',
        f'{_GW}Soulblight-Gravelords-Dire-Wolves-2021',
        'Dire Wolves Age of Sigmar',
    ),
    (
        'vargheists',
        'SG-013',
        'Vargheists',
        60.00,
        '99120207033_FleshEatersVargheists01.jpg',
        f'{_GW}Vargheists-2016',
        'Crypt Flayers Age of Sigmar Warhammer',
    ),
    (
        'deadwalker-zombies',
        'SG-034',
        'Deadwalker Zombies',
        60.00,
        '99120207234_DeadwalkerZombiesRegiment1.jpg',
        f'{_GW}Deadwalker-Zombies-2021',
        'Deadwalker Zombies Age of Sigmar',
    ),
    (
        'deathrattle-skeletons',
        'SG-024',
        'Deathrattle Skeletons',
        65.00,
        '99120207188_SoulblightGravelordsDeathrattleSkeletons1.jpg',
        f'{_GW}soulblight-gravelords-deathrattle-skeletons-2025',
        'Deathrattle Skeletons Age of Sigmar',
    ),
    (
        'barrow-knights',
        'SG-025',
        'Barrow Knights',
        65.00,
        '99120207179_SoulblightGravelordsBarrowKnights1.jpg',
        f'{_GW}soulblight-gravelords-barrow-knights-2025',
        'Barrow Knights Age of Sigmar',
    ),
    (
        'barrow-guard',
        'SG-026',
        'Barrow Guard',
        60.00,
        '99120207178_SoulblightGravelordsBarrowGuard1.jpg',
        f'{_GW}soulblight-gravelords-barrow-guard-2025',
        'Barrow Guard Age of Sigmar',
    ),
    (
        'askurgan-trueblades',
        'SG-020',
        'Askurgan Trueblades',
        60.00,
        '60010299039_Bloodhunt5.jpg',
        f'{_GW}soulblight-gravelords-askurgan-trueblades-2025',
        'Warcry Askurgan Trueblades',
    ),
    (
        'wight-king',
        'SG-036',
        'Wight King',
        20.00,
        '99120207207_SoulblightGravelordsWightKingUPDATE1.jpg',
        f'{_GW}Deathrattle-Wight-King-2018',
        'Wight King Age of Sigmar',
    ),
    (
        'necromancer',
        'SG-037',
        'Necromancer',
        20.00,
        '99120207206_SoulblightGravelordsNecromancer1.jpg',
        f'{_GW}The-Deathmages-Necromancer-2016',
        'Necromancer Age of Sigmar',
    ),

    # ── War Machines / Vehicles ───────────────────────────────────────────────
    # ⚠ Dual kit: Mortis Engine / Coven Throne share the same box (SG-017 / SG-018)
    (
        'mortis-engine',
        'SG-017',
        'Mortis Engine',
        77.00,
        '99120207019_SoulblightGravelordsMortisEngineUPDATE202601.jpg',
        f'{_GW}Mortis-Engine',
        'Mortis Engine or Coven throne Warhammer',
    ),
    # ⚠ Dual kit: Coven Throne / Mortis Engine share the same box (SG-018 / SG-017)
    (
        'coven-throne',
        'SG-018',
        'Coven Throne',
        77.00,
        '99120207019_SoulblightGravelordsCovenThroneUPDATE202601.jpg',
        f'{_GW}Coven-Throne',
        'Mortis Engine or Coven throne Warhammer',
    ),
    (
        'corpse-cart',
        'SG-019',
        'Corpse Cart',
        35.00,
        '99120207013_SoulblightGravelordsCorpseCartUPDATE202502.jpg',
        f'{_GW}Vampire-Counts-Corpse-Cart',
        'Corpse Cart Age of Sigmar',
    ),

    # ── Terrain / Objectives ─────────────────────────────────────────────────
    (
        'cursed-sepulchrenexus-of-grief',
        'SG-023',
        'Cursed Sepulchre/Nexus of Grief',
        85.00,
        '99120207193_SoulblightGravelordsCursedSepulchre1.jpg',
        f'{_GW}soulblight-gravelords-cursed-sepulchre-2025',
        'Cursed Sepulchre Age of Sigmar',
    ),

    # ── Spells / Manifestations ──────────────────────────────────────────────
    (
        'soulblight-gravelords-manifestations',
        'SG-022',
        'Soulblight Gravelords: Manifestations',
        60.00,
        '99120207194_SoulblightGravelordsManifestations1.jpg',
        f'{_GW}soulblight-gravelords-manifestations-2025',
        'Soulblight Gravelords: Manifestations Age of Sigmar',
    ),

    # ── Narrative Sets ───────────────────────────────────────────────────────
    (
        'blades-of-the-hollow-king',
        'SG-029',
        'Blades of the Hollow King',
        69.00,
        '99120207175_BLBladesoftheHollowKingNarrativeSet1.jpg',
        f'{_GW}soulblight-gravelords-blades-of-the-hollow-king-2025',
        'Blades of the Hollow King Age of Sigmar',
    ),

    # ── Battletome ───────────────────────────────────────────────────────────
    (
        'death-battletome-soulblight-gravelords',
        'SG-031',
        'Death Battletome: Soulblight Gravelords',
        60.00,
        '60030207019_ENGSoulblightGravelordsBattletomeHB1.jpg',
        f'{_GW}battletome-soulblight-gravelords-2025-eng',
        'Death Battletome: Soulblight Gravelords Age of Sigmar',
    ),
]


class Command(BaseCommand):
    """Populate Soulblight Gravelords products (SG-001 to SG-037)."""

    help = (
        'Creates / updates 37 Soulblight Gravelords products and seeds GW prices at MSRP. '
        'Creates Soulblight Gravelords faction if not present. Idempotent.'
    )

    def handle(self, *args, **options):
        """Run the command."""
        try:
            category_aos = Category.objects.get(slug='age-of-sigmar')
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Age of Sigmar category not found — run populate_products first.'
            ))
            return

        sg_faction, faction_created = Faction.objects.get_or_create(
            slug='soulblight-gravelords',
            defaults={'name': 'Soulblight Gravelords', 'category': category_aos},
        )
        if faction_created:
            self.stdout.write('  Created Soulblight Gravelords faction.')

        gw = Retailer.objects.filter(name='Games Workshop').first()
        if not gw:
            self.stderr.write(self.style.ERROR(
                'Games Workshop retailer not found — GW prices will not be seeded.'
            ))
            return

        prod_created = prod_updated = gw_created = gw_updated = 0

        for slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name in PRODUCTS:
            image_url = _IMG.format(filename=image_filename) if image_filename else ''

            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'gw_sku': gw_sku,
                    'faction': sg_faction,
                    'category': category_aos,
                    'msrp': msrp,
                    'image_url': image_url,
                    'gw_url': gw_url,
                    'ebay_search_name': ebay_search_name,
                    'batch_tag': 'soulblight-gravelords',
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
            f'\npopulate_soulblight_gravelords_products complete. '
            f'Products: {prod_created} created, {prod_updated} updated. '
            f'GW prices: {gw_created} created, {gw_updated} updated.'
        ))
