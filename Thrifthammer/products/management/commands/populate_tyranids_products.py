"""
Management command: populate_tyranids_products

Seeds 44 Tyranids products (TY-001 to TY-044) with GW, Amazon,
Miniature Market, and Noble Knight price rows.

Idempotent — safe to re-run.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from prices.models import CurrentPrice
from products.models import Category, Faction, Product, Retailer

AMAZON_TAG = 'thrifthammer7-20'
NK_AWID = '1576'
_GW_CDN = 'https://www.warhammer.com/app/resources/catalog/product/920x950/{}'

# Images verified from GW product pages via browser (Image URL column in spreadsheet).
_IMAGES = {
    'TY-001': '60010199057_LeviathanEXTRA15.jpg',
    'TY-002': '99120106065_Biovore1.jpg',
    'TY-003': '99120106059_BroodlordLead.jpg',
    'TY-004': '60030106010_ENGTYRCodex1.jpg',
    'TY-005': '99120106067_Deathleaper1.jpg',
    'TY-006': '99120106056_ExocreneLead.jpg',
    'TY-007': '99120106052_TYRGargoylesLead.jpg',
    'TY-008': '99120106068_Genestealers2.jpg',
    'TY-009': '99120106026_Haruspex01.jpg',
    'TY-010': '99120106024_HiveCrone01.jpg',
    'TY-011': '99120106055_TYRHiveGuardLead.jpg',
    'TY-012': '99120106060_HiveTyrantLead.jpg',
    'TY-013': '99120106073_Hormagaunts2.jpg',
    'TY-014': '99120106076_HorrorsHive2.jpg',
    'TY-015': '99120106083_ENGKillTeamTyphonCoreGame3.jpg',
    'TY-016': '99120106069_Lictor1.jpg',
    'TY-017': '99120106033_Maleceptor01.jpg',
    'TY-018': '99120106019_MawlocNEW01.jpg',
    'TY-019': '60010199057_LeviathanEXTRA16.jpg',
    'TY-020': '99120106072_Neurolictor1.jpg',
    'TY-021': '99120106064_NornAssimilator1.jpg',
    'TY-022': '99120106064_NornEmissary1.jpg',
    'TY-023': '99120106031_OldOneEyeBrood01.jpg',
    'TY-024': '99120106050_TYRParasiteofMortrexLead.jpg',
    'TY-025': '99120106074_Psychophage1.jpg',
    'TY-026': '99120106065_Pyrovore1.jpg',
    'TY-027': '99120106031_ScreamerKillerBrood01.jpg',
    'TY-028': '99120106034_Sporocyst01.jpg',
    'TY-029': '99120106054_TYRTyrannofexLeadALT.jpg',
    'TY-030': '99120106060_SwarmlordLead.jpg',
    'TY-031': '99120106033_Toxicrene01.jpg',
    'TY-032': '99120106019_TrygonNEW01.jpg',
    'TY-033': '99120106024_Harpies01.jpg',
    'TY-034': '99590106024_TyranidHarridanGargoyleClusters02.jpg',
    'TY-035': '99590106012_TyranidHierophantBioTitan02.jpg',
    'TY-036': '99120106075_Prime1.jpg',
    'TY-037': '99120106084_TyranidPrimewithLashWhip01.jpg',
    'TY-038': '99120106034_Tyrannocyte01.jpg',
    'TY-039': '99120106054_TYRTyrannofexLead.jpg',
    'TY-040': '99120106055_TYRHiveGuardLeadALT.jpg',
    'TY-041': '99120106057_VenomthropesLead.jpg',
    'TY-042': '60010199057_LeviathanEXTRA13.jpg',
    'TY-043': '99120106060_WingedHiveTyrantLead.jpg',
    'TY-044': '99120106057_NeurothropesLead.jpg',
}

# Per-SKU eBay search name overrides.
# Used when the product name gives poor eBay results (e.g. Kill Team reboxes).
_EBAY_SEARCH_NAMES = {
    # TY-015 "Tyranid Raveners" — sold as a Kill Team box; eBay sellers list it
    # as "Kill Team Raveners" rather than the full Tyranid unit name.
    'TY-015': 'Kill Team Raveners',
}


def _amazon_url(asin):
    if not asin:
        return ''
    return f'https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}'


def _nk_url(base_url):
    if not base_url:
        return ''
    return f'{base_url}?awid={NK_AWID}'


# (gw_sku, name, msrp, gw_url, amazon_asin, mm_url, nk_base_url)
# Notes on shared retailer URLs — intentional for dual-kit products:
#   TY-006/TY-009  (Exocrine/Haruspex)       — same NK listing
#   TY-010/TY-033  (Hive Crone/Harpy)        — same NK listing
#   TY-018/TY-032  (Mawloc/Trygon)           — same NK listing
#   TY-023/TY-027  (Old One Eye/Screamer)     — same NK listing
#   TY-028/TY-038  (Sporocyst/Tyrannocyte)    — same NK and MM listing
#   TY-029/TY-039  (Tervigon/Tyrannofex)      — same NK and MM listing
#   TY-011/TY-040  (Hive Guard/Tyrant Guard)  — same NK and MM listing
#   TY-041/TY-044  (Venomthropes/Zoanthropes) — same NK and MM listing
# Notes on blanked retailer URLs — bad data in source spreadsheet:
#   TY-012/TY-030/TY-043 (Hive Tyrant/Swarmlord/Winged Hive Tyrant): MM column
#     contained a GW URL — MM left blank pending correct URL.
#   TY-026 (Pyrovore): all retailer URLs pointed to Biovore — left blank.
PRODUCTS = [
    ('TY-001', 'Tyranid Barbgaunts', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-barbgaunts-2023',
     'B0CBKK9CQH',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-barbgaunts-gw-51-28.html',
     'https://www.nobleknight.com/P/2148065647/Barbgaunts'),

    ('TY-002', 'Tyranid Biovore', Decimal('53.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-biovore-2023',
     'B0CGV799H7',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-biovore-gw-51-41.html',
     'https://www.nobleknight.com/P/2148078721/Biovore'),

    ('TY-003', 'Tyranid Broodlord', Decimal('48.00'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Broodlord',
     'B09XBLQ5NM',
     'https://www.miniaturemarket.com/gw-51-23.html',
     'https://www.nobleknight.com/P/2147974194/Broodlord'),

    ('TY-004', 'Codex: Tyranids', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/codex-tyranids-2023-eng',
     '1839066156',
     'https://www.miniaturemarket.com/warhammer-40k-codex-tyranids-gw-51-01-2023.html',
     'https://www.nobleknight.com/P/2148078672/Codex-Tyranids-10th-Edition'),

    ('TY-005', 'Tyranid Deathleaper', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-deathleaper-2023',
     'B0CGV6YKNK',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-deathleaper-gw-51-30.html',
     'https://www.nobleknight.com/P/2148078714/Deathleaper'),

    ('TY-006', 'Tyranid Exocrine', Decimal('89.00'),
     'https://www.warhammer.com/en-US/shop/Exocrine',
     'B00HSS3RHA',
     '',
     'https://www.nobleknight.com/P/2147538740/Haruspex-Exocrine'),

    ('TY-007', 'Tyranid Gargoyle Brood', Decimal('48.50'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Gargoyle-Brood',
     'B09WKTJQYF',
     'https://www.miniaturemarket.com/gw-51-12.html',
     'https://www.nobleknight.com/P/2148009783/Gargoyles'),

    ('TY-008', 'Tyranid Genestealers', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-genestealers-2023',
     'B0CGV7GF6V',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-genestealers-gw-51-06-2023.html',
     'https://www.nobleknight.com/P/2148078728/Genestealers'),

    ('TY-009', 'Tyranid Haruspex', Decimal('89.00'),
     'https://www.warhammer.com/en-US/shop/Haruspex',
     'B00HSS3RHA',
     '',
     'https://www.nobleknight.com/P/2147538740/Haruspex-Exocrine'),

    ('TY-010', 'Tyranid Hive Crone', Decimal('92.00'),
     'https://www.warhammer.com/en-US/shop/Hive-Crone',
     '',
     '',
     'https://www.nobleknight.com/P/2147538741/Harpy-Hive-Crone'),

    ('TY-011', 'Tyranid Hive Guard', Decimal('85.00'),
     'https://www.warhammer.com/en-US/shop/Hive-Guard',
     'B09Z5ZTGTD',
     'https://www.miniaturemarket.com/gw-51-07.html',
     'https://www.nobleknight.com/P/2147974208/Hive-Guard'),

    ('TY-012', 'Tyranid Hive Tyrant', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-hive-tyrant-no-wings-2022',
     'B09TBGXFRN',
     'https://www.miniaturemarket.com/gw-51-08.html',
     'https://www.nobleknight.com/P/2147970048/Hive-Tyrant'),

    ('TY-013', 'Tyranid Hormagaunts', Decimal('53.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-hormagaunts-2023',
     'B0CGV72YXS',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-hormagaunts-gw-51-17-2023.html',
     'https://www.nobleknight.com/P/2148078729/Hormagaunts'),

    ('TY-014', 'Tyranid Horrors of the Hive', Decimal('114.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-horrors-of-the-hive-2023',
     '',
     '',
     ''),

    ('TY-015', 'Tyranid Raveners', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/kill-team-raveners-2025',
     'B0FNR75WNM',
     'https://www.miniaturemarket.com/kill-team-raveners-gw-103-98.html',
     'https://www.nobleknight.com/P/2148344143/Raveners'),

    ('TY-016', 'Tyranid Lictor', Decimal('53.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-lictor-2023',
     '',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-lictor-gw-51-29.html',
     ''),

    ('TY-017', 'Tyranid Maleceptor', Decimal('89.00'),
     'https://www.warhammer.com/en-US/shop/Maleceptor',
     '',
     '',
     'https://www.nobleknight.com/P/2147563076/Toxicrene'),

    ('TY-018', 'Tyranid Mawloc', Decimal('96.00'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Mawloc',
     'B0033B654S',
     '',
     'https://www.nobleknight.com/P/2147460064/Tyranid-Trygon-Mawloc'),

    ('TY-019', 'Tyranid Neurogaunts', Decimal('43.50'),
     'https://www.warhammer.com/en-US/shop/tyranids-neurogaunts-2023',
     'B0CQ3FJRQQ',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-neurogaunts-gw-51-33.html',
     'https://www.nobleknight.com/P/2148107876/Neurogants'),

    ('TY-020', 'Tyranid Neurolictor', Decimal('43.50'),
     'https://www.warhammer.com/en-US/shop/tyranids-neurolictor-2023',
     'B0CGV545FB',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-neurolictor-gw-51-32.html',
     'https://www.nobleknight.com/P/2148078703/Neurolictor'),

    ('TY-021', 'Tyranid Norn Assimilator', Decimal('122.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-norn-assimilator-2023',
     'B0CGV6WDHX',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-norn-emissary-gw-51-31.html',
     'https://www.nobleknight.com/P/2148078731/Norn-Emissary'),

    ('TY-022', 'Tyranid Norn Emissary', Decimal('122.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-norn-emissary-2023',
     'B0CGV6WDHX',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-norn-emissary-gw-51-31.html',
     'https://www.nobleknight.com/P/2148078731/Norn-Emissary'),

    ('TY-023', "Tyranid Old One Eye's Carnifex Brood", Decimal('106.00'),
     'https://www.warhammer.com/en-US/shop/Old-One-Eyes-Carnifex-Brood-2017',
     'B00HSS263G',
     '',
     'https://www.nobleknight.com/P/2147538732/Carnifex-Brood-2014-Edition'),

    ('TY-024', 'Tyranid Parasite of Mortrex', Decimal('43.50'),
     'https://www.warhammer.com/en-US/shop/tyranids-parasite-of-mortrex-2022',
     'B09X5ZQCQZ',
     'https://www.miniaturemarket.com/gw-51-27.html',
     'https://www.nobleknight.com/P/2147970795/Parasite-of-Mortrex'),

    ('TY-025', 'Tyranid Psychophage', Decimal('60.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-psychophage-2023',
     'B0CQ3NQ8B4',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-psychophage-gw-51-75.html',
     'https://www.nobleknight.com/P/2148112902/Psychophage'),

    ('TY-026', 'Tyranid Pyrovore', Decimal('53.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-pyrovore-2023',
     'B0CGV799H7',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-biovore-gw-51-41.html',
     'https://www.nobleknight.com/P/2148078721/Biovore'),

    ('TY-027', 'Tyranid Screamer-Killer Brood', Decimal('106.00'),
     'https://www.warhammer.com/en-US/shop/Screamer-Killer-Brood-2017',
     'B00HSS263G',
     '',
     'https://www.nobleknight.com/P/2147538732/Carnifex-Brood-2014-Edition'),

    ('TY-028', 'Tyranid Sporocyst and Mucolid Spore', Decimal('82.00'),
     'https://www.warhammer.com/en-US/shop/Sporocyst',
     'B00PM9R87W',
     'https://www.miniaturemarket.com/gw-51-21.html',
     'https://www.nobleknight.com/P/2147563699/Tyrannocyte'),

    ('TY-029', 'Tyranid Tervigon', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Tervigon',
     'B09YQFCYT5',
     'https://www.miniaturemarket.com/gw-51-09.html',
     'https://www.nobleknight.com/P/2147974212/Tyrannofex-Tervigon'),

    ('TY-030', 'Tyranid The Swarmlord', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/The-Swarmlord-2019',
     'B09TBGXFRN',
     'https://www.miniaturemarket.com/gw-51-08.html',
     'https://www.nobleknight.com/P/2147970048/Hive-Tyrant'),

    ('TY-031', 'Tyranid Toxicrene', Decimal('89.00'),
     'https://www.warhammer.com/en-US/shop/Toxicrene',
     '',
     '',
     'https://www.nobleknight.com/P/2147563076/Toxicrene'),

    ('TY-032', 'Tyranid Trygon', Decimal('96.00'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Trygon',
     'B0033B654S',
     '',
     'https://www.nobleknight.com/P/2147460064/Tyranid-Trygon-Mawloc'),

    ('TY-033', 'Tyranid Harpy', Decimal('92.00'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Harpy',
     '',
     '',
     'https://www.nobleknight.com/P/2147538741/Harpy-Hive-Crone'),

    ('TY-034', 'Tyranid Harridan', Decimal('535.00'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Harridan',
     '',
     '',
     ''),

    ('TY-035', 'Tyranid Hierophant Bio-Titan', Decimal('535.00'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Hierophant-Bio-Titan',
     '',
     '',
     ''),

    ('TY-036', 'Tyranid Prime', Decimal('43.50'),
     'https://www.warhammer.com/en-US/shop/tyranids-prime-2023',
     '',
     '',
     ''),

    ('TY-037', 'Tyranid Prime with Lash Whip', Decimal('43.50'),
     'https://www.warhammer.com/en-US/shop/tyranid-prime-with-lash-whip-2026',
     '',
     'https://www.miniaturemarket.com/Warhammer-40K-Tyranids-Tyranid-Prime-With-Lash-Whip/GW-51-35-2026',
     ''),

    ('TY-038', 'Tyranid Tyrannocyte', Decimal('82.00'),
     'https://www.warhammer.com/en-US/shop/Tyrannocyte',
     'B00PM9R87W',
     'https://www.miniaturemarket.com/gw-51-21.html',
     'https://www.nobleknight.com/P/2147563699/Tyrannocyte'),

    ('TY-039', 'Tyranid Tyrannofex', Decimal('69.00'),
     'https://www.warhammer.com/en-US/shop/Tyranid-Tyrannofex',
     'B09YQFCYT5',
     'https://www.miniaturemarket.com/gw-51-09.html',
     'https://www.nobleknight.com/P/2147974212/Tyrannofex-Tervigon'),

    ('TY-040', 'Tyranid Tyrant Guard', Decimal('85.00'),
     'https://www.warhammer.com/en-US/shop/Tyrant-Guard',
     'B09Z5ZTGTD',
     'https://www.miniaturemarket.com/gw-51-07.html',
     'https://www.nobleknight.com/P/2147974208/Hive-Guard'),

    ('TY-041', 'Tyranid Venomthropes', Decimal('82.00'),
     'https://www.warhammer.com/en-US/shop/Venomthropes',
     'B00PQJ59GU',
     'https://www.miniaturemarket.com/gw-51-22.html',
     'https://www.nobleknight.com/P/2147974073/Venomthropes'),

    ('TY-042', "Tyranid Von Ryan's Leapers", Decimal('53.00'),
     'https://www.warhammer.com/en-US/shop/tyranids-von-ryans-leapers-2023',
     'B0CQ3D2BH3',
     'https://www.miniaturemarket.com/warhammer-40k-tyranids-von-ryans-leapers-gw-51-37.html',
     'https://www.nobleknight.com/P/2148107883/Von-Ryans-Leapers'),

    ('TY-043', 'Tyranid Winged Hive Tyrant', Decimal('65.00'),
     'https://www.warhammer.com/en-US/shop/Tyranids-Hive-Tyrant-2019',
     'B09TBGXFRN',
     'https://www.miniaturemarket.com/gw-51-08.html',
     'https://www.nobleknight.com/P/2147466184/Hive-Tyrant-The-Swarmlord'),

    ('TY-044', 'Tyranid Zoanthropes', Decimal('82.00'),
     'https://www.warhammer.com/en-US/shop/Zoanthropes',
     'B00PQJ59GU',
     'https://www.miniaturemarket.com/gw-51-22.html',
     'https://www.nobleknight.com/P/2147974073/Venomthropes'),
]


class Command(BaseCommand):
    """Seed 44 Tyranids products (TY-001 to TY-044) with retailer price rows."""

    help = 'Seed Tyranids products and their GW, Amazon, MM, and NK price rows.'

    def handle(self, *args, **options):
        """Run the seed."""
        try:
            category = Category.objects.get(name='Warhammer 40,000')
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Category "Warhammer 40,000" not found — run populate_products first.'
            ))
            return

        faction = Faction.objects.filter(name='Tyranids').first()
        if not faction:
            self.stdout.write(self.style.ERROR(
                'Faction "Tyranids" not found — create it in admin first.'
            ))
            return

        retailers = {
            slug: Retailer.objects.get(slug=slug)
            for slug in ['games-workshop', 'amazon', 'miniature-market', 'noble-knight-games']
        }

        created_count = 0
        updated_count = 0

        for gw_sku, name, msrp, gw_url, amazon_asin, mm_url, nk_base_url in PRODUCTS:
            image_url = _GW_CDN.format(_IMAGES.get(gw_sku, ''))
            slug = slugify(name)
            # If this slug is already taken by a different product (e.g. pre-existing
            # 51-04 "Tyranid Hive Tyrant"), update that original product rather than
            # creating a duplicate. This attaches our retailer URLs to the canonical page.
            existing_with_slug = Product.objects.filter(slug=slug).exclude(gw_sku=gw_sku).first()
            if existing_with_slug:
                product = existing_with_slug
                Product.objects.filter(pk=product.pk).update(
                    image_url=image_url,
                    msrp=msrp,
                    gw_url=gw_url,
                    category=category,
                    faction=faction,
                    is_active=True,
                    batch_tag='tyranids',
                )
                created = False
                self.stdout.write(f'  [merged] {gw_sku} -> {existing_with_slug.gw_sku} — {name}')
            else:
                product, created = Product.objects.update_or_create(
                    gw_sku=gw_sku,
                    defaults={
                        'name': name,
                        'slug': slug,
                        'msrp': msrp,
                        'gw_url': gw_url,
                        'image_url': image_url,
                        'category': category,
                        'faction': faction,
                        'is_active': True,
                        'batch_tag': 'tyranids',
                        'ebay_search_name': _EBAY_SEARCH_NAMES.get(gw_sku, ''),
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                self.stdout.write(f'  [{"new" if created else "upd"}] {gw_sku} — {name}')

            # GW — seed at MSRP
            CurrentPrice.objects.update_or_create(
                product=product,
                retailer=retailers['games-workshop'],
                defaults={
                    'price': msrp,
                    'url': gw_url,
                    'in_stock': True,
                    'not_available': False,
                    'listing_title': name,
                },
            )

            # Amazon — create placeholder only; never overwrite a scraped price
            amazon_url = _amazon_url(amazon_asin)
            if amazon_url:
                cp, cp_created = CurrentPrice.objects.get_or_create(
                    product=product,
                    retailer=retailers['amazon'],
                    defaults={
                        'price': None,
                        'url': amazon_url,
                        'in_stock': False,
                        'not_available': False,
                        'listing_title': '',
                    },
                )
                if not cp_created and cp.url != amazon_url:
                    cp.url = amazon_url
                    cp.save(update_fields=['url'])

            # Miniature Market — only create row if URL exists
            if mm_url:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailers['miniature-market'],
                    defaults={
                        'price': None,
                        'url': mm_url,
                        'in_stock': False,
                        'not_available': False,
                        'listing_title': '',
                    },
                )

            # Noble Knight — only create row if URL exists
            nk_url = _nk_url(nk_base_url)
            if nk_url:
                CurrentPrice.objects.update_or_create(
                    product=product,
                    retailer=retailers['noble-knight-games'],
                    defaults={
                        'price': None,
                        'url': nk_url,
                        'in_stock': False,
                        'not_available': False,
                        'listing_title': '',
                    },
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {created_count}  Updated: {updated_count}'
        ))
