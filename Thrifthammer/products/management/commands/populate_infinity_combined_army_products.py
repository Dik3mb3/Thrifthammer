"""
Management command: populate_infinity_combined_army_products

Creates Infinity's seventh faction, Combined Army, under the existing
"Infinity" Category. Same UK-first, no-pricing-yet approach as the prior
factions: only image_url and gw_url (the official Corvus Belli listing
link) are set -- no msrp, no msrp_gbp, no CurrentPrice row here
(seed_corvus_belli_infinity_links.py, which covers the whole category,
handles that).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution. "The Hungries: Gakis and Pretas" and "Raicho Armored
Brigade"/"Pneumarch" use non-default lightbox image indices (-3, -2, -2)
-- confirmed live. Two products' real lightbox filenames differ from their
own gw_url slug and were confirmed live rather than assumed: "Shasvastii
Expansion Pack Gamma" actually shares the "combined-army-booster-pack-
alpha" image asset, and "Shasvastii Action Pack"'s real filename is
"combined-army-shasvastii-action-pack" (both already hinted at correctly
by the sheet's own front/xxs reference, but verified independently here).

Cross-faction shared units: only 5 of the 42 rows in the source sheet are
the exact same Corvus Belli product as a product already created under
PanOceania or Yu Jing -- a smaller overlap than prior factions, since this
sheet leans heavily on Combined-Army-exclusive lines (Morat/Shasvastii
subfactions). Dual-tagged via Product.secondary_factions per the
user-confirmed pattern. "Betrayal Characters Pack" (YUJ-029) is a new
recurrence not seen in prior factions. They are NOT in the PRODUCTS list
below -- see SHARED_UNIT_SKUS.

gw_sku scheme: CA-001 through CA-037 (prefix confirmed unused elsewhere in
the catalog before this command was written, following the PAN-/YUJ-/
ARI-/HQQ-/NOM-/ALE- precedent; the 5 shared units keep their existing
SKU, they don't get a CA-xxx number).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-nexus-7-spec-ops-bundle', 'CA-001', 'Infinity: Nexus-7 Spec-Ops Bundle', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/nexus-7-spec-ops-bundle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/nexus-7-spec-ops-bundle'),
    ('infinity-nexus-7-spec-ops', 'CA-002', 'Infinity: Nexus-7 Spec-Ops', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/nexus-7-spec-ops-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/nexus-7-spec-ops'),
    ('infinity-combined-army-hero-the-charontids', 'CA-003', 'Infinity: Combined Army Hero, The Charontids', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/combined-army-hero-the-charontids-plasma-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/essentials/combined-army-hero-the-charontids-plasma-rifle'),
    ('infinity-combined-army-booster-pack-alpha', 'CA-004', 'Infinity: Combined Army Booster Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/combined-army-booster-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/combined-army-booster-pack-alpha'),
    ('infinity-combined-army-overdron-batroids-tag-pack', 'CA-005', 'Infinity: Combined Army Overdron Batroids TAG Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/combined-army-overdron-batroids-tag-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/combined-army-overdron-batroids-tag-pack'),
    ('infinity-combined-army-drone-remotes-pack', 'CA-006', 'Infinity: Combined Army Drone Remotes Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/combined-army-drone-remotes-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/combined-army-drone-remotes-pack'),
    ('infinity-combined-army-support-pack', 'CA-007', 'Infinity: Combined Army Support Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/combined-army-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/essentials/combined-army-support-pack'),
    ('infinity-achilles', 'CA-008', 'Infinity: Achilles', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/achilles-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/achilles'),
    ('infinity-infinity-combined-army-paint-set', 'CA-009', 'Infinity: Infinity Combined Army Paint Set', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/infinity-combined-army-paint-set-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/accesories/infinity-combined-army-paint-set'),
    ('infinity-juggernauts-armored-assault-brigade', 'CA-010', 'Infinity: Juggernauts, Armored Assault Brigade', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/juggernauts-armored-assault-brigade-multi-hmg-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/juggernauts-armored-assault-brigade-multi-hmg'),
    ('infinity-next-wave-action-pack', 'CA-011', 'Infinity: Next Wave Action Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/next-wave-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/next-wave-action-pack'),
    ('infinity-krakot-renegades', 'CA-012', 'Infinity: Krakot Renegades', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/krakot-renegades-2-smg-chest-mine-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/krakot-renegades-2-smg-chest-mine'),
    ('infinity-shasvastii-expansion-pack-beta', 'CA-013', 'Infinity: Shasvastii Expansion Pack Beta', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/shasvastii-expansion-pack-beta-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shasvastii-expansion-pack-beta'),
    ('infinity-the-anathematics', 'CA-014', 'Infinity: The Anathematics', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/the-anathematics-hacker-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/the-anathematics-hacker'),
    ('infinity-reinf-caskuda', 'CA-015', 'Infinity: Reinf. Caskuda', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinf-caskuda-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinf-caskuda'),
    ('infinity-reinforcements-combined-army-alpha', 'CA-016', 'Infinity: Reinforcements: Combined Army Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinforcements-combined-army-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinforcements-combined-army-pack-alpha'),
    ('infinity-combined-army-expansion-pack-alpha', 'CA-017', 'Infinity: Combined Army Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/combined-army-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/combined-army-expansion-pack-alpha'),
    ('infinity-morat-expansion-pack-beta', 'CA-018', 'Infinity: Morat Expansion Pack Beta', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/morat-expansion-pack-beta-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/morat-expansion-pack-beta'),
    ('infinity-the-hungries-gakis-and-pretas', 'CA-019', 'Infinity: The Hungries: Gakis and Pretas', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/the-hungries-gakis-pretas-3.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/the-hungries-gakis-pretas'),
    ('infinity-shasvastii-expansion-pack-alpha', 'CA-020', 'Infinity: Shasvastii Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/shasvastii-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shasvastii-expansion-pack-alpha'),
    ('infinity-morat-expansion-pack-alpha', 'CA-021', 'Infinity: Morat Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/morat-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/morat-expansion-pack-alpha'),
    ('infinity-kornak-gazarot', 'CA-022', 'Infinity: Kornak Gazarot', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/kornak-gazarot-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kornak-gazarot'),
    ('infinity-morat-fireteam-pack', 'CA-023', 'Infinity: Morat Fireteam Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/morat-fireteam-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/morat-fireteam-pack'),
    ('infinity-bultrak-mobile-armored-regiment', 'CA-024', 'Infinity: Bultrak Mobile Armored Regiment', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/bultrak-mobile-armored-regiment-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/bultrak-mobile-armored-regiment'),
    ('infinity-morat-tarlok-pack', 'CA-025', 'Infinity: Morat Tarlok Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/morat-tarlok-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/morat-tarlok-pack'),
    ('infinity-morat-aggression-forces-action-pack', 'CA-026', 'Infinity: Morat Aggression Forces Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/morat-aggression-forces-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/morat-aggression-forces-action-pack'),
    ('infinity-taigha-creatures', 'CA-027', 'Infinity: Taigha Creatures', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/taigha-creatures-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/taigha-creatures'),
    ('infinity-shasvastii-expansion-pack-gamma', 'CA-028', 'Infinity: Shasvastii Expansion Pack Gamma', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/combined-army-booster-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shasvastii-expansion-pack-gamma'),
    ('infinity-shasvastii-sphinx', 'CA-029', 'Infinity: Shasvastii Sphinx', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/shasvastii-sphinx-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shasvastii-sphinx'),
    ('infinity-shasvastii-action-pack', 'CA-030', 'Infinity: Shasvastii Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/combined-army-shasvastii-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/shasvastii-action-pack'),
    ('infinity-greif-operators', 'CA-031', 'Infinity: Greif Operators', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/greif-operators-2-breaker-pistols-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/greif-operators-2-breaker-pistols'),
    ('infinity-shasvastii-nox-troops', 'CA-032', 'Infinity: Shasvastii Nox Troops', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/shasvastii-nox-troops-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shasvastii-nox-troops'),
    ('infinity-raicho-armored-brigade', 'CA-033', 'Infinity: Raicho Armored Brigade', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/raicho-armored-brigade-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/raicho-armored-brigade'),
    ('infinity-bit-and-kiss', 'CA-034', 'Infinity: Bit and KISS!', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/bit-and-kiss-hacker-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/bit-and-kiss-hacker'),
    ('infinity-avatar', 'CA-035', 'Infinity: Avatar', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/avatar-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/avatar'),
    ('infinity-pneumarch', 'CA-036', 'Infinity: Pneumarch', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/pneumarch-hvt-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/pneumarch-hvt'),
    ('infinity-xeodron-batroids', 'CA-037', 'Infinity: Xeodron Batroids', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/xeodron-batroids-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/xeodron-batroids'),
]

# Products already created under PanOceania or Yu Jing that are the same
# Corvus Belli SKU as a Combined Army sheet row -- dual-tagged via
# secondary_factions instead of being duplicated. YUJ-029 is a new
# recurrence not seen in prior factions. Confirmed with user.
SHARED_UNIT_SKUS = [
    'PAN-035',  # Motorized Bounty Hunters
    'PAN-036',  # Oktavia Grímsdóttir
    'PAN-041',  # Aïda Swanson
    'YUJ-029',  # Betrayal Characters Pack
    'YUJ-030',  # Libertos
]


class Command(BaseCommand):
    """Populate the Infinity: Combined Army product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: Combined Army products (CA-001 to CA-037) and dual-tags 5 shared units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='combined-army',
            defaults={'name': 'Combined Army', 'category': category},
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
                    'batch_tag': 'infinity-combined-army-uk',
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
            f'{dual_tagged} shared units dual-tagged with Combined Army.'
        ))
