"""
One-time seed script for Adeptus Custodes (AC-001 to AC-026).
Run with: python manage.py shell < seed_custodes.py
"""
import decimal
import random

import django
django.setup()

from django.utils.text import slugify
from products.models import Product, Category, Faction, Retailer
from prices.models import CurrentPrice

# Import the URL/image dicts directly from populate_products
from products.management.commands.populate_products import (
    GW_IMAGES,
    _GW_PRODUCT_PAGE_URLS,
    _NK_PRODUCT_PAGE_URLS,
    _MM_PRODUCT_PAGE_URLS,
    _EBAY_SEARCH_OVERRIDES,
)

# ── Lookups ───────────────────────────────────────────────────────────────────
cat     = Category.objects.get(name='Warhammer 40,000')
faction = Faction.objects.get(slug='custodes')
gw      = Retailer.objects.get(slug='games-workshop')
mm      = Retailer.objects.get(slug='miniature-market')
nk      = Retailer.objects.get(slug='noble-knight-games')
ebay    = Retailer.objects.get(slug='ebay')
amazon  = Retailer.objects.get(slug='amazon')

# ── Product data (mirrors _create_extended_products) ─────────────────────────
ac_products = [
    ('Codex: Adeptus Custodes', 'AC-001', decimal.Decimal('60.00'),
     "The 10th Edition codex for the Adeptus Custodes, containing "
     "rules, lore, and datasheets for the Emperor's golden warriors."),
    ('Custodes Allarus Custodians', 'AC-002', decimal.Decimal('60.00'),
     'Three towering Allarus Custodians in Terminator plate, armed '
     'with balistus grenade launchers and castellan axes or guardian spears.'),
    ('Custodes Blade Champion', 'AC-003', decimal.Decimal('43.50'),
     'An Adeptus Custodes hero armed with the Vaultswords, three '
     'master-crafted blades for lightning-fast duelling.'),
    ('Custodes Caladius Annihilator Grav-tank', 'AC-004', decimal.Decimal('100.00'),
     'A Legio Custodes heavy grav-tank armed with twin aeonic arc '
     'cannons, designed to annihilate armoured targets.'),
    ('Custodes Caladius Grav-tank', 'AC-005', decimal.Decimal('100.00'),
     'A Legio Custodes grav-tank armed with Iliastus accelerator '
     'culverins or twin arachnus heavy blaze cannon.'),
    ('Custodes Contemptor Dreadnought', 'AC-006', decimal.Decimal('65.00'),
     'A Legiones Astartes Contemptor Dreadnought, also fielded by '
     'the Legio Custodes in the Horus Heresy.'),
    ('Custodes Coronus Grav-carrier', 'AC-007', decimal.Decimal('127.00'),
     'A Legio Custodes heavy transport armed with a twin arachnus '
     'blaze cannon, carrying Custodian warriors into battle.'),
    ('Custodes Custodian Dreadnought', 'AC-008', decimal.Decimal('77.00'),
     'A Legio Custodes Custodian Dreadnought, an ancient war machine '
     'piloted by a wounded but undying guardian of the Emperor.'),
    ('Custodes Custodian Guard Sodality', 'AC-009', decimal.Decimal('73.50'),
     'A five-model Legio Custodes infantry sodality armed with '
     'guardian spears or sentinel blades and praesidium shields.'),
    ('Custodes Prosecutor Squad', 'AC-010', decimal.Decimal('60.00'),
     'Sisters of Silence Prosecutor Squad, ranged-focused infantry '
     'armed with boltguns who suppress psykers through null aura.'),
    ('Custodes Sentinel Guard Sodality', 'AC-011', decimal.Decimal('73.50'),
     'A Legio Custodes Sentinel Guard Sodality, elite heavy infantry '
     'armed with sentinel war-lances and misericordias.'),
    ('Custodes Talons of the Emperor: Valerian and Aleya', 'AC-012', decimal.Decimal('60.00'),
     'The legendary duo of Shield-Captain Valerian and Sisters of '
     'Silence Aleya, heroes of the Gathering Storm.'),
    ('Custodes Telemon Heavy Dreadnought Iliastus Accelerator Culverin', 'AC-013', decimal.Decimal('29.00'),
     'An Iliastus Accelerator Culverin arm upgrade for the Legio '
     'Custodes Telemon Heavy Dreadnought.'),
    ('Custodes Venatari Sodality', 'AC-014', decimal.Decimal('82.00'),
     'A Legio Custodes Venatari Sodality, elite Custodian jetbike '
     'cavalry armed with venatari lances and kinetic shriek launchers.'),
    ('Custodes Vigilator Squad', 'AC-015', decimal.Decimal('60.00'),
     'Sisters of Silence Vigilator Squad, close combat specialists '
     'armed with executioner greatblades.'),
    ('Custodes Witchseeker Squad', 'AC-016', decimal.Decimal('60.00'),
     'Sisters of Silence Witchseeker Squad, armed with flamers for '
     'purging psykers and corrupted heretics.'),
    ('Legio Custodes Aquilon Terminators', 'AC-017', decimal.Decimal('104.00'),
     'Elite Custodian warriors in Aquilon Terminator plate, armed '
     'with twin adrathic destructors and solerite power talons.'),
    ('Legio Custodes Aquilon Terminators with Infernus Firepikes', 'AC-018', decimal.Decimal('104.00'),
     'Aquilon Terminators armed with Infernus firepikes and solerite '
     'power gauntlets for close-range annihilation.'),
    ('Legio Custodes Ares Gunship', 'AC-019', decimal.Decimal('575.00'),
     'A massive Forge World aircraft serving as the Legio Custodes '
     'aerial superiority and heavy bombardment platform.'),
    ('Legio Custodes Gyrfalcon Pattern Jetbike', 'AC-020', decimal.Decimal('75.00'),
     'A single Legio Custodes Gyrfalcon Pattern Jetbike, armed with '
     'an Iliastus bolter and volkite culverin.'),
    ('Legio Custodes Orion Assault Dropship', 'AC-021', decimal.Decimal('575.00'),
     'The Legio Custodes dedicated assault dropship, delivering '
     'Custodian warriors and vehicles directly into battle.'),
    ('Legio Custodes Pallas Grav-attack', 'AC-022', decimal.Decimal('128.00'),
     'A swift Legio Custodes gunboat armed with an arachnus blaze '
     'cannon for fast-attack and fire support operations.'),
    ('Legio Custodes Shield Captain', 'AC-023', decimal.Decimal('66.00'),
     'A Shield-Captain of the Legio Custodes, one of the most '
     'powerful individual warriors in the entire Imperium.'),
    ('Legio Custodes Telemon Arachnus Storm Cannon', 'AC-024', decimal.Decimal('29.00'),
     'An arachnus storm cannon arm upgrade for the Legio Custodes '
     'Telemon Heavy Dreadnought.'),
    ('Legio Custodes Telemon Caestus', 'AC-025', decimal.Decimal('29.00'),
     'A caestus power fist arm upgrade for the Legio Custodes '
     'Telemon Heavy Dreadnought.'),
    ('Legio Custodes Telemon Heavy Dreadnought Body', 'AC-026', decimal.Decimal('103.00'),
     'The main body of the Legio Custodes Telemon Heavy Dreadnought, '
     'a towering war machine of the Emperor\'s guard.'),
]

def apply_discount(msrp, pct):
    return (msrp * (1 - pct)).quantize(decimal.Decimal('0.01'))

def upsert_price(product, retailer, price, in_stock, url, not_available=False):
    CurrentPrice.objects.update_or_create(
        product=product,
        retailer=retailer,
        defaults={
            'price': price,
            'in_stock': in_stock,
            'url': url,
            'not_available': not_available,
        },
    )

print(f'Creating {len(ac_products)} Custodes products...')

for name, gw_sku, msrp, description in ac_products:
    slug = slugify(name)
    product, created = Product.objects.update_or_create(
        gw_sku=gw_sku,
        defaults={
            'name': name,
            'slug': slug,
            'category': cat,
            'faction': faction,
            'description': description,
            'msrp': msrp,
            'is_active': True,
            'image_url': GW_IMAGES.get(gw_sku, ''),
            'ebay_search_name': _EBAY_SEARCH_OVERRIDES.get(gw_sku, ''),
        },
    )
    status = 'created' if created else 'updated'

    # GW — always full MSRP
    gw_url = _GW_PRODUCT_PAGE_URLS.get(gw_sku, '')
    upsert_price(product, gw, msrp, True, gw_url)

    # MM — only if confirmed URL exists
    mm_url = _MM_PRODUCT_PAGE_URLS.get(gw_sku)
    if mm_url:
        disc = decimal.Decimal(str(round(random.uniform(0.15, 0.25), 2)))
        upsert_price(product, mm, apply_discount(msrp, disc), random.random() > 0.1, mm_url)
    else:
        upsert_price(product, mm, None, False, '', not_available=True)

    # NK — only if confirmed URL exists
    nk_url = _NK_PRODUCT_PAGE_URLS.get(gw_sku)
    if nk_url:
        disc = decimal.Decimal(str(round(random.uniform(0.10, 0.18), 2)))
        upsert_price(product, nk, apply_discount(msrp, disc), random.random() > 0.15, nk_url)
    else:
        upsert_price(product, nk, None, False, '', not_available=True)

    # eBay — placeholder
    import urllib.parse
    search_term = urllib.parse.quote_plus(f'{name} warhammer games workshop')
    disc = decimal.Decimal(str(round(random.uniform(0.05, 0.25), 2)))
    upsert_price(product, ebay, apply_discount(msrp, disc), random.random() > 0.25,
                 f'https://www.ebay.com/sch/i.html?_nkw={search_term}&LH_BIN=1&_sop=15')

    # Amazon — placeholder (will be set properly by find_amazon_asins)
    disc = decimal.Decimal(str(round(random.uniform(0.05, 0.15), 2)))
    upsert_price(product, amazon, apply_discount(msrp, disc), random.random() > 0.3, '')

    print(f'  [{status}] {gw_sku}  {name}')

print('Done.')
