"""
Management command: populate_skaven_products

Creates / updates all Skaven product entries for ThriftHammer,
seeds GW CurrentPrice records at MSRP.

Covers 36 products (SK-001 to SK-036) from the
AOS Skaven GW, NK, MM, AMAZON.xlsx spreadsheet (2026-05-15).

Category: Age of Sigmar
Faction:  Skaven

Dual-kit products (share retailer URLs — same physical box):
  - Screaming Bell / Plague Priest on Plague Furnace  (SK-007 / SK-008)
  - Acolyte Globadiers / Warp-Grinder  (SK-022 / SK-023)  — same Amazon ASIN only
  - Verminlord Warpseer / Lord Skreech Verminking / Verminlord Warbringer /
    Verminlord Deceiver / Verminlord Corruptor  (SK-028 to SK-032)
  - Warp Lightning Cannon / Plagueclaw  (SK-033 / SK-034)

Images are baked in as one-off GW CDN URLs — never auto-refreshed.

Safe to run repeatedly (idempotent via update_or_create keyed on slug).

Usage:
    python manage.py populate_skaven_products
"""

from django.core.management.base import BaseCommand

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

_IMG = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{filename}'

# ── Per-SKU eBay negative keywords ───────────────────────────────────────────
_EBAY_NEGATIVE_KEYWORDS = {
    'SK-005': 'Bell of Doom',
}

# ── Product definitions ───────────────────────────────────────────────────────
# (slug, gw_sku, name, msrp, image_filename, gw_url, ebay_search_name)
#
# msrp is USD price from GW en-US storefront as of 2026-05-15.
# ebay_search_name is blank unless the default name gives poor eBay results.
PRODUCTS = [

    # ── Rulebook ──────────────────────────────────────────────────────────────
    (
        'chaos-battletome-skaven',
        'SK-001',
        'Chaos Battletome: Skaven',
        60.00,
        '60030206009_EngSKABattletome01.jpg',
        'https://www.warhammer.com/en-US/shop/battletome-skaven-2024-eng',
        '',
    ),

    # ── Bundles ───────────────────────────────────────────────────────────────
    (
        'spearhead-city-of-ash',
        'SK-002',
        'Spearhead: City of Ash',
        220.00,
        '60010299051_ENGCityofAshSpearheadGame1a.jpg',
        'https://www.warhammer.com/en-US/shop/spearhead-city-of-ash-2026-eng',
        '',
    ),

    # ── Characters ───────────────────────────────────────────────────────────
    (
        'skaven-deathmaster',
        'SK-003',
        'Skaven Deathmaster',
        39.00,
        '99070206004_SKADeathmasterLead.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-deathmaster-2022',
        '',
    ),
    (
        'skaven-warlock-bombardier',
        'SK-004',
        'Skaven Warlock Bombardier',
        35.00,
        '99070206003_WarplockBombardier01.jpg',
        'https://www.warhammer.com/en-US/shop/Skaven-Warlock-Bombardier-2020',
        '',
    ),
    (
        'skaven-clawlord',
        'SK-009',
        'Skaven Clawlord',
        32.00,
        '99070206002_SKAClawlordwithBanner01.jpg',
        'https://www.warhammer.com/en-US/shop/Skaven-Warlord-2014',
        '',
    ),
    (
        'skaven-thanquol-and-boneripper',
        'SK-012',
        'Skaven Thanquol and Boneripper',
        96.00,
        '99120206059_SKAThanqoulOnBoneripper01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-thanquol-on-boneripper-2024',
        '',
    ),
    (
        'skaven-clawlord-on-gnaw-beast',
        'SK-014',
        'Skaven Clawlord on Gnaw-beast',
        65.00,
        '99120206055_ClawlordonGnawbeast1.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-clawlord-on-gnaw-beast-2024',
        '',
    ),
    (
        'skaven-arch-warlock',
        'SK-016',
        'Skaven Arch-Warlock',
        40.00,
        '99120206049_SKAArchWarlock01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-arch-warlock-2024',
        '',
    ),
    (
        'skaven-vizzik-skour-prophet-of-the-horned-rat',
        'SK-019',
        'Skaven Vizzik Skour, Prophet of the Horned Rat',
        165.00,
        '99120206042_SKAVizzikSkourProphetOfTheHornedRat01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-vizzik-skour-prophet-horned-rat-2024',
        '',
    ),
    (
        'skaven-warlock-galvaneer',
        'SK-021',
        'Skaven Warlock Galvaneer',
        35.00,
        '99070206007_SKAWarlockGalvaneer01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-warlock-galvaneer-2024',
        '',
    ),
    (
        'skaven-master-moulder',
        'SK-026',
        'Skaven Master Moulder',
        35.00,
        '99070206006_SKAMasterMoulder01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-master-moulder-2024',
        '',
    ),
    (
        'skaven-krittok-foulblade',
        'SK-035',
        'Skaven Krittok Foulblade',
        42.00,
        '99120206052_SKAKrittokFoulblade01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-krittok-foulblade-2024',
        '',
    ),

    # ── Infantry / Troops ─────────────────────────────────────────────────────
    (
        'skaven-plaguepack',
        'SK-013',
        'Skaven Plaguepack',
        43.50,
        '99120206062_SKAPlaguepack01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-plaguepack-2024',
        '',
    ),
    (
        'skaven-acolyte-globadiers',
        'SK-022',
        'Skaven Acolyte Globadiers',
        60.00,
        '99120206046_SKAAcolyteGlobadiers01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-acolyte-globadiers-2024',
        '',
    ),
    # ⚠ Dual kit: Acolyte Globadiers / Warp-Grinder share the same Amazon listing
    (
        'skaven-warp-grinder',
        'SK-023',
        'Skaven Warp-Grinder',
        48.00,
        '99120206047_SKAWarpGrinder01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-warp-grinder-2024',
        '',
    ),
    (
        'skaven-night-runners',
        'SK-011',
        'Skaven Night Runners',
        43.50,
        '99120206002_SKANightrunners01.jpg',
        'https://www.warhammer.com/en-US/shop/Skaven-Night-Runners',
        '',
    ),
    (
        'skaven-stormvermin',
        'SK-036',
        'Skaven Stormvermin',
        60.00,
        '99120206045_SKAStormvermin01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-stormvermin-2024',
        '',
    ),

    # ── Monsters / Beasts ─────────────────────────────────────────────────────
    (
        'skaven-rat-ogors',
        'SK-015',
        'Skaven Rat Ogors',
        60.00,
        '99120206043_RatOgors1.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-rat-ogors-2024',
        '',
    ),
    (
        'skaven-brood-terror',
        'SK-020',
        'Skaven Brood Terror',
        73.50,
        '99120206056_SKABroodTerror01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-brood-terror-2024',
        '',
    ),
    (
        'skaven-hell-pit-abomination',
        'SK-027',
        'Skaven Hell Pit Abomination',
        73.50,
        '99120206012_SkavenHellPitAbominationUPDATE01.jpg',
        'https://www.warhammer.com/en-US/shop/Skaven-Hell-Pit-Abomination',
        '',
    ),
    # ⚠ Dual kit: all 5 Verminlords build from the same box
    # ⚠ Dual kit: all 5 Verminlords build from the same box
    # SK-028, SK-030, SK-031 use ebay_search_name='Skaven Verminlord Corruptor'
    # because that name returns results; Warpseer, Warbringer, Deceiver do not.
    (
        'skaven-verminlord-warpseer',
        'SK-028',
        'Skaven Verminlord Warpseer',
        122.00,
        '99120206018_VerminLordWarpseer01.jpg',
        'https://www.warhammer.com/en-US/shop/Warpseer-2018',
        'Skaven Verminlord Corruptor',
    ),
    (
        'skaven-lord-skreech-verminking',
        'SK-029',
        'Skaven Lord Skreech Verminking',
        122.00,
        '99120206018_VerminLordSkreech01.jpg',
        'https://www.warhammer.com/en-US/shop/Lord-Skreech-2018',
        '',
    ),
    (
        'skaven-verminlord-warbringer',
        'SK-030',
        'Skaven Verminlord Warbringer',
        122.00,
        '99120206018_VerminLordWarbringer01.jpg',
        'https://www.warhammer.com/en-US/shop/Warbringer-2018',
        'Skaven Verminlord Corruptor',
    ),
    (
        'skaven-verminlord-deceiver',
        'SK-031',
        'Skaven Verminlord Deceiver',
        122.00,
        '99120206018_VerminLordDeceiver01.jpg',
        'https://www.warhammer.com/en-US/shop/Deciever-2018',
        'Skaven Verminlord Corruptor',
    ),
    (
        'skaven-verminlord-corruptor',
        'SK-032',
        'Skaven Verminlord Corruptor',
        122.00,
        '99120206018_VerminLordCorruptor01.jpg',
        'https://www.warhammer.com/en-US/shop/Skaven-Pestilens-Verminlord-Corruptor',
        '',
    ),

    # ── Warmachines / Artillery ───────────────────────────────────────────────
    (
        'skaven-doom-flayers',
        'SK-025',
        'Skaven Doom-Flayers',
        60.00,
        '99120206044_SKADoomFlyer01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-doom-flayers-2024',
        '',
    ),
    (
        'skaven-doomwheel',
        'SK-010',
        'Skaven Doomwheel',
        43.50,
        '99120206009_SKADoomwheel01.jpg',
        'https://www.warhammer.com/en-US/shop/Skaven-Doomwheel',
        '',
    ),
    (
        'skaven-ratling-warpblaster',
        'SK-017',
        'Skaven Ratling Warpblaster',
        60.00,
        '99120206054_RatlingWarpblaster1.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-ratling-warpblaster-2024',
        '',
    ),
    (
        'skaven-warplock-jezzails',
        'SK-018',
        'Skaven Warplock Jezzails',
        53.00,
        '99120206051_WarplockJezzails1.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-warplock-jezzails-2024',
        '',
    ),
    (
        'skaven-warpspark-weapon-battery',
        'SK-024',
        'Skaven Warpspark Weapon Battery',
        53.00,
        '99120206048_SKAWarsparkWeaponBattery01.jpg',
        'https://www.warhammer.com/en-US/shop/skaven-warpspark-weapon-battery-2024',
        '',
    ),
    # ⚠ Dual kit: Warp Lightning Cannon / Plagueclaw share the same box
    (
        'skaven-warp-lightning-cannon',
        'SK-033',
        'Skaven Warp Lightning Cannon',
        43.50,
        '99120206020_SkavenPestilensPlagueClawLCannon01.jpg',
        'https://www.warhammer.com/en-US/shop/Skaven-Warp-Lightning-Cannon-2015',
        '',
    ),
    (
        'skaven-plagueclaw',
        'SK-034',
        'Skaven Plagueclaw',
        43.50,
        '99120206020_SkavenPestilensPlagueClawCatapult01.jpg',
        'https://www.warhammer.com/en-US/shop/Pestilens-Plague-Claw-Catapult',
        '',
    ),
    # ⚠ Dual kit: Screaming Bell / Plague Priest on Plague Furnace share the same box
    (
        'skaven-screaming-bell',
        'SK-007',
        'Skaven Screaming Bell',
        82.00,
        '99120206022_PestilensScreamingBell01.jpg',
        'https://www.warhammer.com/en-US/shop/Screaming-Bell-2015',
        '',
    ),
    (
        'skaven-plague-priest-on-plague-furnace',
        'SK-008',
        'Skaven Plague Priest on Plague Furnace',
        82.00,
        '99120206022_PestilensPlagueFurnace01.jpg',
        'https://www.warhammer.com/en-US/shop/Pestilens-Plague-Furnace',
        '',
    ),

    # ── Terrain / Endless Spells ──────────────────────────────────────────────
    (
        'skaven-endless-spells',
        'SK-005',
        'Skaven Endless Spells: Skaven',
        48.00,
        '99120206029_SKAEndlessSpells01.jpg',
        'https://www.warhammer.com/en-US/shop/Endless-Spells-Skaven-2019',
        '',
    ),
    (
        'skaven-gnawholes',
        'SK-006',
        'Skaven Gnawholes',
        65.00,
        '99120206028_SKAGnawhole1.jpg',
        'https://www.warhammer.com/en-US/shop/Skaven-Gnawhole-2019',
        '',
    ),
]


class Command(BaseCommand):
    """Populate Skaven products (SK-001 to SK-036)."""

    help = (
        'Creates / updates 36 Skaven products and seeds GW prices at MSRP. '
        'Idempotent.'
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

        try:
            skaven_faction = Faction.objects.get(slug='skaven')
        except Faction.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'Skaven faction not found — run populate_products first.'
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
                    'category': category_aos,
                    'faction': skaven_faction,
                    'is_active': True,
                    'batch_tag': 'skaven',
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

        # ── Apply per-SKU eBay negative keywords ──────────────────────────────
        for gw_sku, neg_kw in _EBAY_NEGATIVE_KEYWORDS.items():
            rows = Product.objects.filter(gw_sku=gw_sku).update(ebay_negative_keywords=neg_kw)
            if rows:
                self.stdout.write(f'  [neg_kw] {gw_sku}: {neg_kw}')
            else:
                self.stdout.write(self.style.WARNING(f'  [neg_kw skip] {gw_sku} not found'))

        self.stdout.write(self.style.SUCCESS(
            f'\npopulate_skaven_products complete. '
            f'Products: {product_created} created, {product_updated} updated. '
            f'GW prices: {price_created} created, {price_updated} updated.'
        ))
