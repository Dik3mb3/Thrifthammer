"""
One-time fix: apply correct GW CDN image URLs for 44 SKUs that had duplicate/wrong
images, and delete 15 unauthorised dormant products that were swept in on 2026-05-22.

Safe to re-run — uses update() for images and gracefully skips missing SKUs.
Run once on production then never again.

Usage:
    python manage.py fix_image_urls_may2026 --dry-run
    python manage.py fix_image_urls_may2026
"""

from django.core.management.base import BaseCommand

from products.models import Product


# Correct verified GW CDN URLs sourced directly from warhammer.com product pages.
_IMAGE_FIXES = {
    '39-01': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99070109002_CPTArtemisMTO2.jpg',
    '39-02': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99070109003_DeathwatchWatchmaster01.jpg',
    '39-04': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120109002_CorvusBlackstar01.jpg',
    '41-04': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101395_BACommanderDante01.jpg',
    '41-05': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101418_BALemartes01.jpg',
    '41-08': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101414_BATheSanguinor01.jpg',
    '41-09': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101415_BASanguinaryPriest01.jpg',
    '41-10': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101086_BaalPredatorNEW_01.jpg',
    '44-03': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101403_DAAsmodaiALT.jpg',
    '44-04': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101379_Azrael1.jpg',
    '44-05': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101404_DABelialGrandMasteroftheDeathwing1.jpg',
    '44-06': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101410_LionsRetinue1.jpg',
    '44-07': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101267_MasterLazarus01.jpg',
    '44-08': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99810101020_SammaelCorvex01.jpg',
    '44-13': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101407_DAInnerCircleCompanions2.jpg',
    '44-14': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101095_DarkTalon01.jpg',
    '44-15': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101098_DADarkshroud01.jpg',
    '44-16': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101098_LandspeederVengeance01.jpg',
    '44-17': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101095_NephilimJet01.jpg',
    '46-06': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120104033_DireAvengers01.jpg',
    '48-15': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101127_SMDevastatorSquadUltra01.jpg',
    '48-38': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101284_SMBladeguardVeteransLeadUltramarines.jpg',
    '48-39': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101286_SMPrimarisEradicatorsLead.jpg',
    '48-41': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101263_SMPrimarisInfiltrators01.jpg',
    '48-76': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101283_SMAssaultIntercessorsLead.jpg',
    '48-92': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101184_SpaceMarineAggressors01.jpg',
    '48-96': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101263_SMPrimarisIncursors01.jpg',
    '51-40': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120117004_GenestealerNeophytes01.jpg',
    '51-41': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120117003_GenestealerAcolyteHybrids01.jpg',
    '51-43': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99070117005_GSCMagus01.jpg',
    '51-44': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120117012_GSCAberrants01.jpg',
    '52-08': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120108023_SoBExorcist01.jpg',
    '52-09': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120108025_SoBImmolatorLead.jpg',
    '52-15': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120108038_SoBRetributorSquad01.jpg',
    '55-23': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101357_BTSwordBrethrenLead.jpg',
    '55-24': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101364_BTChaplainGrimaldusandRetinueLead.jpg',
    '55-25': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101367_CastellanLead.jpg',
    '55-26': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101443_BlackTemplarsExecrator1Update.jpg',
    '55-27': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101442_BlackTemplarsCrusadeAncient1Update.jpg',
    '55-28': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101368_BTMarshalLead.jpg',
    '91-06': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120207045_Hexwraiths01.jpg',
    '91-07': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120207033_FleshEaterCryptHorrors01.jpg',
    '91-32': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120207035_FleshEatersTerrorgheist01.jpg',
    '91-35': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120207171_FECCryptsGhouls02.jpg',
    # Imperial Knights — GW retired old CDN paths
    '31-06': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99123008004_HHCerastusKnightLancer01.jpg',
    '31-66': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99123008005_HHCerastusKnightCastigator01.jpg',
    '31-67': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99123008006_HHCerastusKnightAcheron01.jpg',
    '54-15': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120108106_ImperialKnightPreceptorCanisRex1upd.jpg',
    '54-22': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120108105_IKKnightQuestorisLEADDefender.jpg',
    # Space Marines — wrong image (was showing heads upgrade sprue)
    '48-75': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101190_PrimarisIntercessors01.jpg',
    # Death Guard — wrong image (was showing old resin Mortarion 99560…)
    '43-03': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120102072_DaemonPrimarchMortarion01.jpg',
    # World Eaters — wrong image (was showing old resin Angron 99560…)
    '43-04': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120102152_AngronDaemonPrimarch1.jpg',
    # Space Marines — wrong image (was showing Kill Team Scout Squad)
    '48-29': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60010199064_KTSalvation3.jpg',
    # Space Marines — wrong image (was showing HH Praetor and Chaplain Consul)
    'HA-051': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101399_SMChaplainTermArmour1.jpg',
    # Chaos Space Marines — wrong image (was showing CSM Combat Patrol box)
    '43-06': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120102218_CSMLegionaries1.jpg',
    # Drukhari — wrong image (was showing Drukhari Combat Patrol box)
    '45-06': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120112008_WychesNEW01.jpg',
    # Space Marines — wrong image (was showing Chaos Vindicator)
    '48-26': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101058_SpaceMarinesVindicatorNEW01.jpg',
    # AoS — Maggotkin Putrid Blightkings (was showing Spearhead Bubonic Cells box)
    '83-22': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120201210_WEBMaggotkinNurgleBlightKings1.jpg',
    # AoS — Blades of Khorne Bloodreavers (was showing Spearhead Fangs of the Blood God box)
    '83-30': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120201037_KhorneBloodboundBloodreavers.jpg',
    # AoS — Disciples of Tzeentch Tzaangors (was showing Spearhead Tzaangor Warflock box)
    '83-40': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120201065_TzaangorWarriors01.jpg',
    # AoS — Stormcast Eternals Lord-Celestant (was showing Lord-Celestant on Stardrake)
    '96-14': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120218090_LordCelestant2.jpg',
    # AoS — Slaves to Darkness Varanguard (was showing S2D Spearhead box image)
    '83-14': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120201046_EverchosenVaranguard01.jpg',
    # Citadel Munitorum Varnish — was showing wrong image (60mm round base)
    'SP-020': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99209999058_sprayMunitorumVarnish.svg',
    # Kill Team — restore correct GW CDN images (were overwritten with placeholder)
    'KT-100': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60010199071_ENGKTStarterSet1.jpg',
    'KT-102': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120104103_HarlequinsLead.jpg',
    'KT-103': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60020105008_CadianShockTroopsLead.jpg',
    'KT-104': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60050102024_KTChaosCultDatacards1.jpg',
    'KT-105': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120101190_PrimarisIntercessors01.jpg',
    'KT-107': 'https://www.warhammer.com/app/resources/catalog/product/920x950/99120108109_KTExactionSquad2.jpg',
    'KT-108': 'https://www.warhammer.com/app/resources/catalog/product/920x950/60010199064_KTSalvation3.jpg',
}

# eBay search name corrections.
# Format: 'GW_SKU': 'corrected ebay_search_name'
_EBAY_SEARCH_FIXES = {
    # MC-006 Fulgurite Electro-Priests — blank name gave poor results;
    # eBay listings use "Electro-Priests" (shared listing with Corpuscarii).
    'MC-006': 'Adeptus Mechanicus Electro-Priests',
}

# Dormant products swept into the DB on 2026-05-22 without authorisation.
# All had 0 price records — safe to hard-delete.
_DELETE_SKUS = [
    '39-03', '39-05', '39-07', '39-08', '39-09', '39-11',
    '40-10', '40-21',
    '41-11', '41-12', '41-15',
    '44-11',
    '46-26',
    '48-36',
    '83-10',
    '91-10',
    'KT-106',
    '71-55',
    '87-06',
    'WC-100',
    'WC-101',
    'WC-102',
    '48-21',
    '39-06',
    '41-07',
    '50-05',
    '55-16',
    'NM-020',
    # 40K Core — zero-price, no retailer data
    '40-01',
    '40-02',
    '40-03',
    '40-20',
    # Kill Team — zero-price dormant
    'KT-101',
    'KT-109',
    'KT-110',
    # Age of Sigmar — zero-price dormant
    '80-15',
    '80-20',
    # Horus Heresy — zero-price dormant
    'HA-011',
    'HA-050',
    'HH-001',
]


class Command(BaseCommand):
    """One-time image URL corrections and dormant product cleanup (May 2026)."""

    help = 'Fix duplicate/wrong image URLs for 44 SKUs and delete 15 dormant products.'

    def add_arguments(self, parser):
        """Register CLI arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would change without writing to the database.',
        )

    def handle(self, *args, **options):
        """Apply image fixes and deletions."""
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        # ── 1. Image URL updates ──────────────────────────────────────────────
        updated = 0
        skipped = 0
        for sku, url in _IMAGE_FIXES.items():
            try:
                product = Product.objects.get(gw_sku=sku)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  [skip ] {sku} — not in DB'))
                skipped += 1
                continue

            if product.image_url == url:
                self.stdout.write(f'  [same ] {sku} — already correct, no change')
                skipped += 1
                continue

            self.stdout.write(
                self.style.SUCCESS(f'  [image] {sku}  {product.name[:50]}')
            )
            self.stdout.write(f'           old: {(product.image_url or "")[-60:]}')
            self.stdout.write(f'           new: {url[-60:]}')

            if not dry_run:
                Product.objects.filter(gw_sku=sku).update(image_url=url)
            updated += 1

        # ── 2. eBay search name corrections ──────────────────────────────────
        ebay_fixed = 0
        for sku, name in _EBAY_SEARCH_FIXES.items():
            try:
                product = Product.objects.get(gw_sku=sku)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  [skip ] {sku} — not in DB'))
                continue

            if product.ebay_search_name == name:
                self.stdout.write(f'  [same ] {sku} — eBay name already correct, no change')
                continue

            self.stdout.write(
                self.style.SUCCESS(f'  [ebay ] {sku}  {product.name[:50]}')
            )
            self.stdout.write(f'           old: {repr(product.ebay_search_name)}')
            self.stdout.write(f'           new: {repr(name)}')

            if not dry_run:
                Product.objects.filter(gw_sku=sku).update(ebay_search_name=name)
            ebay_fixed += 1

        # ── 3. Dormant product deletions ──────────────────────────────────────
        deleted = 0
        for sku in _DELETE_SKUS:
            try:
                product = Product.objects.get(gw_sku=sku)
            except Product.DoesNotExist:
                self.stdout.write(f'  [gone ] {sku} — already deleted')
                continue

            self.stdout.write(
                self.style.WARNING(f'  [del  ] {sku}  {product.name}')
            )
            if not dry_run:
                product.delete()
            deleted += 1

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f'\nDone.  Images updated: {updated}  |  eBay names fixed: {ebay_fixed}'
            f'  |  Skipped: {skipped}  |  Deleted: {deleted}'
        ))
