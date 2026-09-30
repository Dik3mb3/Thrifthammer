"""
Management command: populate_infinity_haqqislam_products

Creates Infinity's fourth faction, Haqqislam, under the existing "Infinity"
Category. Same UK-first, no-pricing-yet approach as PanOceania, Yu Jing,
and Ariadna: only image_url and gw_url (the official Corvus Belli listing
link) are set -- no msrp, no msrp_gbp, no CurrentPrice row here
(seed_corvus_belli_infinity_links.py, which covers the whole category,
handles that).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution. Several products here use a non-default lightbox image index
(-5 instead of -1): Ramah Taskforce Expansion Pack Alpha, Hakims Special
Medical Assistance Group, Naffatûn, Ghazi Muttawi'ah, and Odalisques --
each confirmed live, never assumed.

Row 16 on the source sheet ("Infinity Haqqislam UK.xlsx") has a genuine
typo on Corvus Belli's own site: "Fiddler, Aristeia!`s ex-toymaker" uses a
literal backtick instead of an apostrophe (confirmed against the live page
<title>, which carries the same typo). Corrected to a proper apostrophe in
the display name below.

Cross-faction shared units: 11 of the 39 rows in the source sheet are the
exact same Corvus Belli product (byte-identical gw_url) as a product
already created under PanOceania (10) or Yu Jing (1, Libertos) -- the same
set already shared with Ariadna. Dual-tagged via Product.secondary_factions
per the user-confirmed pattern. They are NOT in the PRODUCTS list below --
see SHARED_UNIT_SKUS.

gw_sku scheme: HQQ-001 through HQQ-028 (prefix confirmed unused elsewhere
in the catalog before this command was written, following the PAN-/YUJ-/
ARI- precedent; the 11 shared units keep their existing PAN-0xx/YUJ-0xx
SKU, they don't get an HQQ-xxx number).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-hassassin-expansion-pack-gamma', 'HQQ-001', 'Infinity: Hassassin Expansion Pack Gamma', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/hassassin-expansion-pack-gamma-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/hassassin-expansion-pack-gamma'),
    ('infinity-haytham-aero-unit', 'HQQ-002', 'Infinity: Haytham Aero-unit', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/haytham-aero-unit-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/haytham-aero-unit'),
    ('infinity-yuan-yuan', 'HQQ-003', 'Infinity: Yuan Yuan', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/yuan-yuan-da-ccw-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yuan-yuan-da-ccw'),
    ('infinity-mukthar-active-response-unit', 'HQQ-004', 'Infinity: Mukthar, Active Response Unit', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/mukthar-active-response-unit-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/mukthar-active-response-unit'),
    ('infinity-zeybek-aero-unit', 'HQQ-005', 'Infinity: Zeybek Aero-unit', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/zeybek-aero-unit-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/zeybek-aero-unit'),
    ('infinity-ramah-taskforce-expansion-pack-alpha', 'HQQ-006', 'Infinity: Ramah Taskforce Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/ramah-taskforce-expansion-pack-alpha-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/ramah-taskforce-expansion-pack-alpha'),
    ('infinity-scarface-cordelia-mercenary-armored-team', 'HQQ-007', 'Infinity: Scarface & Cordelia. Mercenary Armored Team', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/scarface-and-cordelia-mercenary-armored-team-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/scarface-and-cordelia-mercenary-armored-team'),
    ('infinity-hassassin-expansion-pack-alpha', 'HQQ-008', 'Infinity: Hassassin Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/hassassin-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/hassassin-expansion-pack-alpha'),
    ('infinity-reinforcements-haqqislam-pack-alpha', 'HQQ-009', 'Infinity: Reinforcements: Haqqislam Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinforcements-haqqislam-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/reinforcements-haqqislam-pack-alpha'),
    ('infinity-fiddler-aristeias-ex-toymaker', 'HQQ-010', "Infinity: Fiddler, Aristeia!'s ex-toymaker", 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/fiddler-aristeia-s-ex-toymaker-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/fiddler-aristeia-s-ex-toymaker'),
    ('infinity-hassassin-fireteam-pack-alpha', 'HQQ-011', 'Infinity: Hassassin Fireteam Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/hassassin-fireteam-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/hassassin-fireteam-pack-alpha'),
    ('infinity-yara-haddad', 'HQQ-012', 'Infinity: Yara Haddad', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/yara-haddad-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yara-haddad'),
    ('infinity-shakush-light-armored-unit', 'HQQ-013', 'Infinity: Shakush Light Armored Unit', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/shakush-light-armored-unit-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shakush-light-armored-unit'),
    ('infinity-haqqislam-remotes-pack', 'HQQ-014', 'Infinity: Haqqislam Remotes Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/haqqislam-remotes-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/haqqislam-remotes-pack'),
    ('infinity-haqqislam-support-pack', 'HQQ-015', 'Infinity: Haqqislam Support Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/haqqislam-support-pack-codeone-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/haqqislam-support-pack'),
    ('infinity-saladin', 'HQQ-016', 'Infinity: Saladin', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/saladin-combi-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/saladin-combi-rifle'),
    ('infinity-bashi-bazouks', 'HQQ-017', 'Infinity: Bashi Bazouks', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/bashi-bazouks-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/bashi-bazouks'),
    ('infinity-haqqislam-action-pack', 'HQQ-018', 'Infinity: Haqqislam Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/haqqislam-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/haqqislam-action-pack'),
    ('infinity-namurr', 'HQQ-019', 'Infinity: Namurr', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/namurr-heavy-pistol-ccw-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/namurr-heavy-pistol-ccw'),
    ('infinity-zhayedan-intervention-troops', 'HQQ-020', 'Infinity: Zhayedan Intervention Troops', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/zhayedan-intervention-troops-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/zhayedan-intervention-troops'),
    ('infinity-khawarijs', 'HQQ-021', 'Infinity: Khawarijs', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/khawarijs-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/khawarijs'),
    ('infinity-hakims-special-medical-assistance-group', 'HQQ-022', 'Infinity: Hakims, Special Medical Assistance Group', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/hakims-special-medical-assistance-group-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/hakims-special-medical-assistance-group'),
    ('infinity-maghariba-guard', 'HQQ-023', 'Infinity: Maghariba Guard', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/maghariba-guard-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/maghariba-guard'),
    ('infinity-naffatun', 'HQQ-024', 'Infinity: Naffatûn', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/naffatun-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/naffatun'),
    ('infinity-the-nazarova-twins', 'HQQ-025', 'Infinity: The Nazarova Twins', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/the-nazarova-twins-kum-enforcers-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/the-nazarova-twins-kum-enforcers'),
    ('infinity-muttawiah', 'HQQ-026', "Infinity: Muttawi'ah", 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/ghazi-muttawi-ah-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/ghazi-muttawi-ah'),
    ('infinity-kameel-remote', 'HQQ-027', 'Infinity: Kameel Remote', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/kameel-remote-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kameel-remote'),
    ('infinity-odalisques', 'HQQ-028', 'Infinity: Odalisques', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/odalisques-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/odalisques'),
]

# Products already created under PanOceania or Yu Jing that are the same
# Corvus Belli SKU as a Haqqislam sheet row -- dual-tagged via
# secondary_factions instead of being duplicated. Same set already shared
# with Ariadna; confirmed with user.
SHARED_UNIT_SKUS = [
    'PAN-016',  # Beasthunters
    'PAN-017',  # Triphammers, Repurposed Industrial TAGs
    'PAN-018',  # Freelance Operator Samsa
    'PAN-020',  # Warcors, War Correspondents
    'PAN-022',  # Diggers
    'PAN-035',  # Motorized Bounty Hunters
    'PAN-036',  # Oktavia Grímsdóttir
    'PAN-040',  # Monstruckers
    'PAN-041',  # Aïda Swanson
    'PAN-046',  # Miranda Ashcroft
    'YUJ-030',  # Libertos
]


class Command(BaseCommand):
    """Populate the Infinity: Haqqislam product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: Haqqislam products (HQQ-001 to HQQ-028) and dual-tags 11 shared units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='haqqislam',
            defaults={'name': 'Haqqislam', 'category': category},
        )

        products_created = 0
        products_updated = 0

        for slug, gw_sku, name, image_url, product_url in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    'gw_sku': gw_sku,
                    'name': name,
                    'category': category,
                    'faction': faction,
                    'image_url': image_url,
                    'gw_url': product_url,
                    'batch_tag': 'infinity-haqqislam-uk',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

        dual_tagged = 0
        for gw_sku in SHARED_UNIT_SKUS:
            shared_product = Product.objects.get(gw_sku=gw_sku)
            shared_product.secondary_factions.add(faction)
            dual_tagged += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated. '
            f'{dual_tagged} shared units dual-tagged with Haqqislam.'
        ))
