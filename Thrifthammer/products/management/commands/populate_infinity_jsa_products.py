"""
Management command: populate_infinity_jsa_products

Creates Infinity's tenth faction, JSA (Japanese Secessionist Army), under
the existing "Infinity" Category. Same UK-first, no-pricing-yet approach
as the prior factions: only image_url and gw_url (the official Corvus
Belli listing link) are set -- no msrp, no msrp_gbp, no CurrentPrice row
here (seed_corvus_belli_infinity_links.py, which covers the whole
category, handles that).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution.

Cross-faction shared units: 19 of the 24 rows in the source sheet are the
exact same Corvus Belli product as a product already created under Yu
Jing, PanOceania, or NA2. This sheet was built after NA2 (which itself
draws heavily on JSA units), so the large majority of JSA's own roster was
already created there -- only 5 rows are genuinely new to this faction.
Dual-tagged via Product.secondary_factions per the user-confirmed pattern.
They are NOT in the PRODUCTS list below -- see SHARED_UNIT_SKUS.

Note on sequencing: this command was written and its duplicate-detection
run only after populate_infinity_o12_products and
populate_infinity_na2_products had both already run against production --
running JSA's duplicate check earlier (against a DB that didn't yet have
NA2) would have incorrectly treated 13 NA2-owned products as "new" and
created duplicate Product rows at colliding slugs.

gw_sku scheme: JSA-001 through JSA-005 (prefix confirmed unused elsewhere
in the catalog before this command was written, following the PAN-/YUJ-/
ARI-/HQQ-/NOM-/ALE-/CA-/O12-/NA2- precedent; the 19 shared units keep
their existing SKU, they don't get a JSA-xxx number).

This is the tenth and, per the user, final Infinity faction for this
category rollout.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-infinity-jsa-paint-set', 'JSA-001', 'Infinity: Infinity JSA Paint Set', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/infinity-jsa-paint-set-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/infinity-jsa-paint-set'),
    ('infinity-jsa-aibot-remotes-pack', 'JSA-002', 'Infinity: JSA Aibot Remotes Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/jsa-aibot-remotes-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/jsa-aibot-remotes-pack'),
    ('infinity-jsa-army-pack', 'JSA-003', 'Infinity: JSA Army Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/jsa-army-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/jsa-army-pack'),
    ('infinity-shindenbutai-expansion-pack-alpha', 'JSA-004', 'Infinity: Shindenbutai Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/shindenbutai-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shindenbutai-expansion-pack-alpha'),
    ('infinity-reinforcements-jsa-pack-alpha', 'JSA-005', 'Infinity: Reinforcements: JSA Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/reinforcements-jsa-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinforcements-jsa-pack-alpha'),
]

# Products already created under Yu Jing, PanOceania, or NA2 that are the
# same Corvus Belli SKU as a JSA sheet row -- dual-tagged via
# secondary_factions instead of being duplicated. The NA2-0xx set is the
# largest share here since NA2's own sheet already carried most of JSA's
# roster. Confirmed with user.
SHARED_UNIT_SKUS = [
    'PAN-018',  # Freelance Operator Samsa
    'PAN-020',  # Warcors, War Correspondents
    'YUJ-003',  # Ninjas
    'YUJ-008',  # JSA hero, Shinobu Kitsune
    'YUJ-016',  # Yáoxiè Remotes
    'YUJ-037',  # Yáopú Pangguling
    'NA2-003',  # JSA Oban Expansion Pack Alpha
    'NA2-006',  # JSA Booster Pack Alpha
    'NA2-008',  # JSA O-Yoroi Kidobutai TAG Pack
    'NA2-009',  # JSA Support Pack
    'NA2-010',  # Reinf. Domaru Takeshi "Neko" Oyama
    'NA2-011',  # Mechazoid Sokorentai
    'NA2-014',  # JSA Expansion Pack Alpha
    'NA2-017',  # Karakuri Special Project
    'NA2-019',  # Saito Tōgan
    'NA2-021',  # Aragoto Senkenbutai
    'NA2-023',  # Tankō Zensenbutai
    'NA2-024',  # Miyamoto Mushashi Aristeia! outfit
    'NA2-026',  # Yojimbo, Mercenary Sword
]


class Command(BaseCommand):
    """Populate the Infinity: JSA product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: JSA products (JSA-001 to JSA-005) and dual-tags 19 shared units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='jsa',
            defaults={'name': 'JSA', 'category': category},
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
                    'batch_tag': 'infinity-jsa-uk',
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
            f'{dual_tagged} shared units dual-tagged with JSA.'
        ))
