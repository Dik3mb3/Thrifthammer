"""
One-time seed script for Drukhari (DR-001 to DR-018).
Run with: python manage.py shell -c "exec(open('seed_drukhari.py').read())"
"""
import decimal
import django
django.setup()

from django.utils.text import slugify
from products.models import Product, Category, Faction, Retailer
from prices.models import CurrentPrice
from products.management.commands.populate_products import (
    GW_IMAGES,
    _GW_PRODUCT_PAGE_URLS,
    _NK_PRODUCT_PAGE_URLS,
    _MM_PRODUCT_PAGE_URLS,
    _EBAY_SEARCH_OVERRIDES,
)

cat     = Category.objects.get(name='Warhammer 40,000')
faction = Faction.objects.get(slug='drukhari')
gw      = Retailer.objects.get(slug='games-workshop')
mm      = Retailer.objects.get(slug='miniature-market')
nk      = Retailer.objects.get(slug='noble-knight-games')

dr_products = [
    ('Drukhari Lelith Hesperax', 'DR-001', decimal.Decimal('48.00'),
     "The Queen of Knives herself, Lelith Hesperax is a supreme Wych "
     "fighter who tears through enemies with blinding speed and lethal grace."),
    ('Drukhari Drazhar', 'DR-002', decimal.Decimal('48.00'),
     "The Master of Blades and living embodiment of the Incubi martial "
     "art, Drazhar cuts down even the mightiest foes with his executioner's demiklaives."),
    ('Drukhari Haemonculus', 'DR-003', decimal.Decimal('32.00'),
     "A twisted flesh-sculptor of the Haemonculus Covens, this macabre "
     "HQ choice experiments on victims and bolsters Wrack infantry with dark science."),
    ('Drukhari Succubus', 'DR-004', decimal.Decimal('32.00'),
     "A deadly Wych cult leader who fights with acrobatic ferocity, "
     "leading her Wyches into the arena and onto the battlefield with equal flair."),
    ('Drukhari Wracks', 'DR-005', decimal.Decimal('60.00'),
     "Grotesquely altered servants of the Haemonculus Covens, Wracks "
     "are resilient infantry armed with a variety of agonising close-combat tools."),
    ('Codex: Drukhari', 'DR-006', decimal.Decimal('60.00'),
     "The 10th Edition codex for the Drukhari, containing rules, lore, "
     "and datasheets for the raiders of Commorragh."),
    ('Drukhari Incubi', 'DR-007', decimal.Decimal('62.50'),
     "Elite Kabalite bodyguards and warriors of the Incubi shrines, "
     "armed with klaives and clad in baroque armour."),
    ('Drukhari Talos', 'DR-008', decimal.Decimal('65.00'),
     "A Haemonculus Coven pain engine that glides across the battlefield "
     "on anti-gravity suspensors, lashing out with a host of surgical and arcane weapons."),
    ('Drukhari Cronos', 'DR-009', decimal.Decimal('65.00'),
     "A Haemonculus Coven parasite engine that feeds on the psychic "
     "residue of pain and suffering, empowering nearby Coven units."),
    ('Drukhari Venom', 'DR-010', decimal.Decimal('43.50'),
     "A swift Drukhari skimmer transport armed with twin splinter rifles, "
     "carrying a small squad of warriors into the heart of the enemy."),
    ('Drukhari Voidraven Bomber', 'DR-011', decimal.Decimal('96.00'),
     "A sleek and deadly Drukhari aircraft that delivers void lances "
     "and shatterfield missiles to devastating effect against armoured targets."),
    ('Drukhari Razorwing Jetfighter', 'DR-012', decimal.Decimal('65.00'),
     "A fast attack Drukhari aircraft armed with dark lances and "
     "razorwing missiles, strafing enemy lines with lethal precision."),
    ('Drukhari Scourges', 'DR-013', decimal.Decimal('39.00'),
     "Drukhari warriors who have surgically grafted wings, soaring above "
     "the battlefield and unleashing heavy weapons fire from above."),
    ('Drukhari Hand of the Archon', 'DR-014', decimal.Decimal('60.00'),
     "A Kill Team set featuring elite Drukhari agents who serve as the "
     "Archon's personal enforcers, specialists in assassination and terror."),
    ('Drukhari Mandrakes', 'DR-015', decimal.Decimal('82.00'),
     "A Kill Team set of shadow-dwelling Drukhari warriors who phase "
     "between darkness and reality, striking from impossible angles."),
    ('Drukhari Lady Malys', 'DR-016', decimal.Decimal('48.00'),
     "The enigmatic Lady Malys, a Drukhari Archon of supreme cunning "
     "who has made a pact with the Laughing God himself."),
    ('Drukhari Reavers', 'DR-017', decimal.Decimal('48.00'),
     "Jetbike-riding Wych cult daredevils who race across the battlefield "
     "slicing through enemy ranks with bladevanes and cluster caltrops."),
    ('Drukhari Hellions', 'DR-018', decimal.Decimal('35.00'),
     "Skyboard-riding Drukhari outcasts who swoop and slash through "
     "enemy lines, armed with hellglaives and stunclaw weapons."),
]

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

print(f'Creating {len(dr_products)} Drukhari products...')

for name, gw_sku, msrp, description in dr_products:
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
            'gw_url': _GW_PRODUCT_PAGE_URLS.get(gw_sku, ''),
            'ebay_search_name': _EBAY_SEARCH_OVERRIDES.get(gw_sku, ''),
        },
    )
    status = 'created' if created else 'updated'

    # GW — full MSRP
    gw_url = _GW_PRODUCT_PAGE_URLS.get(gw_sku, '')
    upsert_price(product, gw, msrp, True, gw_url)

    # MM — only if confirmed URL exists
    mm_url = _MM_PRODUCT_PAGE_URLS.get(gw_sku)
    if mm_url:
        upsert_price(product, mm, None, False, mm_url)
    else:
        upsert_price(product, mm, None, False, '', not_available=True)

    # NK — only if confirmed URL exists
    nk_url = _NK_PRODUCT_PAGE_URLS.get(gw_sku)
    if nk_url:
        upsert_price(product, nk, None, False, nk_url)
    else:
        upsert_price(product, nk, None, False, '', not_available=True)

    print(f'  [{status}] {gw_sku}  {name}')

print('Done.')
