"""
Management command: populate_infinity_na2_products

Creates Infinity's ninth faction, NA2 (Non-Aligned Armies 2 -- a mixed
roster of JSA, mercenary, and other sectorial units), under the existing
"Infinity" Category. Same UK-first, no-pricing-yet approach as the prior
factions: only image_url and gw_url (the official Corvus Belli listing
link) are set -- no msrp, no msrp_gbp, no CurrentPrice row here
(seed_corvus_belli_infinity_links.py, which covers the whole category,
handles that).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution. Several products use non-default lightbox image indices:
CSU Corporate Security Unit (-3), Tankō Zensenbutai (-4), Avicenna,
Mercenary Doctor (-2), Yojimbo, Mercenary Sword (-5) -- each confirmed
live.

Cross-faction shared units: this is by far the largest overlap seen in
this category -- 46 of the 72 rows in the source sheet are the exact same
Corvus Belli product as a product already created under PanOceania, Yu
Jing, Ariadna, Haqqislam, Nomads, or Combined Army. This is expected: NA2
draws heavily on units already published for other sectorials (JSA units
recur from Yu Jing, Nomads sub-faction units recur from Nomads, etc.).
Dual-tagged via Product.secondary_factions per the user-confirmed pattern.
They are NOT in the PRODUCTS list below -- see SHARED_UNIT_SKUS.

gw_sku scheme: NA2-001 through NA2-026 (prefix confirmed unused elsewhere
in the catalog before this command was written, following the PAN-/YUJ-/
ARI-/HQQ-/NOM-/ALE-/CA-/O12- precedent; the 46 shared units keep their
existing SKU, they don't get an NA2-xxx number).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-rumbler-spec-ops-preorder-exclusive-miniature', 'NA2-001', 'Infinity: Rumbler Spec-Ops Preorder Exclusive Miniature', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/rumbler-spec-ops-preorder-exclusive-miniature-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/rumbler-spec-ops-preorder-exclusive-miniature'),
    ('infinity-taowu-mastermind-and-schemer', 'NA2-002', 'Infinity: Taowu, Mastermind and Schemer', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/taowu-mastermind-schemer-viral-pistol-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/taowu-mastermind-schemer-viral-pistol'),
    ('infinity-jsa-oban-expansion-pack-alpha', 'NA2-003', 'Infinity: JSA Oban Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/jsa-oban-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/jsa-oban-expansion-pack-alpha'),
    ('infinity-anaconda-mercenary-tag-squadron', 'NA2-004', 'Infinity: Anaconda, Mercenary TAG Squadron', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/anaconda-mercenary-tag-squadron-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/anaconda-mercenary-tag-squadron'),
    ('infinity-iguana-squadron', 'NA2-005', 'Infinity: "Iguana" Squadron', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/iguana-squadron-25-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/iguana-squadron'),
    ('infinity-jsa-booster-pack-alpha', 'NA2-006', 'Infinity: JSA Booster Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/jsa-booster-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/jsa-booster-pack-alpha'),
    ('infinity-imperial-service-expansion-pack-alpha', 'NA2-007', 'Infinity: Imperial Service Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/imperial-service-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/imperial-service-expansion-pack-alpha'),
    ('infinity-jsa-o-yoroi-kidobutai-tag-pack', 'NA2-008', 'Infinity: JSA O-Yoroi Kidobutai TAG Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/jsa-o-yoroi-kidobutai-tag-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/jsa-o-yoroi-kidobutai-tag-pack'),
    ('infinity-jsa-support-pack', 'NA2-009', 'Infinity: JSA Support Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/essentials-jsa-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/essentials-jsa-support-pack'),
    ('infinity-reinf-domaru-takeshi-neko-oyama', 'NA2-010', 'Infinity: Reinf. Domaru Takeshi "Neko" Oyama', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/reinf-domaru-takeshi-neko-oyama-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinf-domaru-takeshi-neko-oyama'),
    ('infinity-mechazoid-sokorentai', 'NA2-011', 'Infinity: Mechazoid Sokorentai', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/mechazoid-sokorentai-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/mechazoid-sokorentai'),
    ('infinity-druze-shock-teams', 'NA2-012', 'Infinity: Druze Shock Teams', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/druze-shock-teams-2024-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/druze-shock-teams'),
    ('infinity-father-lucien-sforza', 'NA2-013', 'Infinity: Father Lucien Sforza', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/father-lucien-sforza-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/father-lucien-sforza'),
    ('infinity-jsa-expansion-pack-alpha', 'NA2-014', 'Infinity: JSA Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/jsa-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/jsa-expansion-pack-alpha'),
    ('infinity-mcmurrough-mercenary-dog-warrior', 'NA2-015', 'Infinity: McMurrough, Mercenary Dog-Warrior', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/mcmurrough-mercenary-dog-warrior-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/mcmurrough-mercenary-dog-warrior'),
    ('infinity-valerya-gromoz', 'NA2-016', 'Infinity: Valerya Gromoz', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/valerya-gromoz-hacker-reesculpt-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/valerya-gromoz-hacker'),
    ('infinity-karakuri-special-project', 'NA2-017', 'Infinity: Karakuri Special Project', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/karakuri-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/karakuri-special-project'),
    ('infinity-soldiers-of-fortune', 'NA2-018', 'Infinity: Soldiers Of Fortune', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/infinity-soldiers-of-fortune-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/infinity-soldiers-of-fortune'),
    ('infinity-saito-togan', 'NA2-019', 'Infinity: Saito Tōgan', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/saito-togan-combi-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/saito-togan-combi-rifle'),
    ('infinity-brawlers', 'NA2-020', 'Infinity: Brawlers', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/brawlers-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/brawlers'),
    ('infinity-aragoto-senkenbutai', 'NA2-021', 'Infinity: Aragoto Senkenbutai', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/aragoto-senkenbutai-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/aragoto-senkenbutai'),
    ('infinity-csu-corporate-security-unit', 'NA2-022', 'Infinity: CSU, Corporate Security Unit', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/csu-corporate-security-unit-boarding-shotgun-3.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/csu-corporate-security-unit-boarding-shotgun'),
    ('infinity-tanko-zensenbutai', 'NA2-023', 'Infinity: Tankō Zensenbutai', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tank-zensenbutai-4.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tank-zensenbutai'),
    ('infinity-miyamoto-mushashi-aristeia-outfit', 'NA2-024', 'Infinity: Miyamoto Mushashi Aristeia! outfit', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/miyamoto-mushashi-aristeia-outfit-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/miyamoto-mushashi-aristeia-outfit'),
    ('infinity-avicenna-mercenary-doctor', 'NA2-025', 'Infinity: Avicenna, Mercenary Doctor', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/avicenna-mercenary-doctor-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/avicenna-mercenary-doctor'),
    ('infinity-yojimbo-mercenary-sword', 'NA2-026', 'Infinity: Yojimbo, Mercenary Sword', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/yojimbo-mercenary-sword-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yojimbo-mercenary-sword'),
]

# Products already created under PanOceania, Yu Jing, Ariadna, Haqqislam,
# Nomads, or Combined Army that are the same Corvus Belli SKU as an NA2
# sheet row -- dual-tagged via secondary_factions instead of being
# duplicated. By far the largest overlap seen in this category, since NA2
# draws on units already published for other sectorials. Confirmed with
# user.
SHARED_UNIT_SKUS = [
    'PAN-016',  # Beasthunters
    'PAN-017',  # Triphammers, Repurposed Industrial TAGs
    'PAN-018',  # Freelance Operator Samsa
    'PAN-020',  # Warcors, War Correspondents
    'PAN-022',  # Diggers
    'PAN-025',  # Armbots
    'PAN-028',  # Karhu Special Team
    'PAN-030',  # Nøkken
    'PAN-035',  # Motorized Bounty Hunters
    'PAN-036',  # Oktavia Grímsdóttir
    'PAN-040',  # Monstruckers
    'PAN-041',  # Aïda Swanson
    'PAN-043',  # Orc Troops
    'PAN-046',  # Miranda Ashcroft
    'PAN-048',  # Mulebots
    'YUJ-003',  # Ninjas
    'YUJ-008',  # JSA hero, Shinobu Kitsune
    'YUJ-012',  # Yu Jing Support Pack
    'YUJ-016',  # Yáoxiè Remotes
    'YUJ-018',  # Guilang
    'YUJ-023',  # Húláng Shocktroopers
    'YUJ-030',  # Libertos
    'YUJ-032',  # Tiger Soldiers
    'YUJ-035',  # Gūijiă Squadron
    'YUJ-037',  # Yáopú Pangguling
    'ARI-009',  # Highlander Cateran
    'ARI-018',  # Irmandinhos
    'ARI-033',  # Traktor Muls. Regiment of Artillery and Support
    'HQQ-003',  # Yuan Yuan
    'HQQ-007',  # Scarface & Cordelia. Mercenary Armored Team
    'HQQ-010',  # Fiddler, Aristeia!'s ex-toymaker
    'HQQ-017',  # Bashi Bazouks
    'HQQ-023',  # Maghariba Guard
    'HQQ-027',  # Kameel Remote
    'HQQ-028',  # Odalisques
    'NOM-005',  # Nomads Hero, Wolfgang Amadeus Wolff
    'NOM-009',  # Nomads Zonds Remotes Pack
    'NOM-010',  # Nomads Support Pack
    'NOM-016',  # Bakunin Überfallkommando
    'NOM-018',  # Sputniks
    'NOM-029',  # Corregidor Bandits
    'NOM-033',  # Mobile Brigada
    'NOM-034',  # Corregidor Jaguars
    'NOM-036',  # Salyut Zonds
    'CA-012',   # Krakot Renegades
    'CA-031',   # Greif Operators
]


class Command(BaseCommand):
    """Populate the Infinity: NA2 product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: NA2 products (NA2-001 to NA2-026) and dual-tags 46 shared units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='na2',
            defaults={'name': 'NA2', 'category': category},
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
                    'batch_tag': 'infinity-na2-uk',
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
            f'{dual_tagged} shared units dual-tagged with NA2.'
        ))
