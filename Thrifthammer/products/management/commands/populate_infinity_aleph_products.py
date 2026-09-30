"""
Management command: populate_infinity_aleph_products

Creates Infinity's sixth faction, ALEPH, under the existing "Infinity"
Category. Same UK-first, no-pricing-yet approach as the prior factions:
only image_url and gw_url (the official Corvus Belli listing link) are
set -- no msrp, no msrp_gbp, no CurrentPrice row here
(seed_corvus_belli_infinity_links.py, which covers the whole category,
handles that).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution. Andromeda and Penthesilea Amazon Biker Special Edition use
a non-default lightbox image index (-2 instead of -1) -- confirmed live.
Dactyls' real lightbox image is "aleph-support-pack-codeone" (a shared
asset, not a "dactyls"-named file) -- the sheet's own front/xxs reference
already hinted at this and it was confirmed live, not assumed.

ALE-014 "Rebot Remotes Pack" (gw_url .../aleph-remotes-pack) is a
genuinely pre-release product ("Avail on Oct 29" on its own Corvus Belli
page as of this command's writing) with no product image uploaded yet --
image_url is intentionally left blank (Product.image_url is blank=True)
rather than guessing or faking one, per standing data-integrity rules.
Revisit and backfill once Corvus Belli publishes the real image.

Cross-faction shared units: 13 of the 35 rows in the source sheet are the
exact same Corvus Belli product (byte-identical gw_url) as a product
already created under PanOceania. The same 11-unit PanOceania/Yu Jing set
already shared with Ariadna/Haqqislam/Nomads recurs here, plus two new
PanOceania-primary recurrences: "Optimate Agent Maximus" (PAN-003) and
"Maximus" (PAN-021). Dual-tagged via Product.secondary_factions per the
user-confirmed pattern. They are NOT in the PRODUCTS list below -- see
SHARED_UNIT_SKUS.

gw_sku scheme: ALE-001 through ALE-022 (prefix confirmed unused elsewhere
in the catalog before this command was written, following the PAN-/YUJ-/
ARI-/HQQ-/NOM- precedent; the 13 shared units keep their existing SKU,
they don't get an ALE-xxx number).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-tarkshyas-interception-wing', 'ALE-001', 'Infinity: Tarkshyas Interception Wing', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/tarkshyas-interception-wing-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tarkshyas-interception-wing'),
    ('infinity-aleph-support-pack', 'ALE-002', 'Infinity: ALEPH Support Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/aleph-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/essentials/aleph-support-pack'),
    ('infinity-aleph-army-pack', 'ALE-003', 'Infinity: ALEPH Army Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/aleph-army-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/essentials/aleph-army-pack'),
    ('infinity-k2-auxiliars', 'ALE-004', 'Infinity: K2 Auxiliars', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/k2-auxiliars-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/k2-auxiliars'),
    ('infinity-posthumans', 'ALE-005', 'Infinity: Posthumans', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/posthumans-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/posthumans'),
    ('infinity-ajax-the-great', 'ALE-006', 'Infinity: Ajax the Great', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/ajax-great-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/ajax-great'),
    ('infinity-atalanta-agemas-nco-spotbot', 'ALE-007', "Infinity: Atalanta, Agêma's NCO & Spotbot", 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/atalanta-agemas-nco-and-spotbot-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/atalanta-agemas-nco-and-spotbot'),
    ('infinity-reinforcements-aleph-pack-alpha', 'ALE-008', 'Infinity: Reinforcements: ALEPH Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinforcements-aleph-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinforcements-aleph-pack-alpha'),
    ('infinity-myrmidons', 'ALE-009', 'Infinity: Myrmidons', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/myrmidons-2024-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/myrmidons'),
    ('infinity-steel-phalanx-expansion-pack-alpha', 'ALE-010', 'Infinity: Steel Phalanx Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/steel-phalanx-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/steel-phalanx-expansion-pack-alpha'),
    ('infinity-phoenix', 'ALE-011', 'Infinity: Phoenix', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/phoenix-heavy-rocket-launcher-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/phoenix-heavy-rocket-launcher'),
    ('infinity-aleph-expansion-pack-beta', 'ALE-012', 'Infinity: ALEPH Expansion Pack Beta', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/aleph-booster-pack-beta-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/aleph-booster-pack-beta'),
    ('infinity-agamemnon-the-atreides', 'ALE-013', 'Infinity: Agamemnon the Atreides', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/agamemnon-atreides-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/agamemnon-atreides'),
    ('infinity-rebot-remotes-pack', 'ALE-014', 'Infinity: Rebot Remotes Pack', '', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/aleph-remotes-pack'),
    ('infinity-dactyls', 'ALE-015', 'Infinity: Dactyls', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/aleph-support-pack-codeone-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/dactyls'),
    ('infinity-marut', 'ALE-016', 'Infinity: Marut', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/marut-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/marut'),
    ('infinity-probots', 'ALE-017', 'Infinity: Probots', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/probots-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/probots'),
    ('infinity-yadu-troops', 'ALE-018', 'Infinity: Yadu Troops', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/yadu-troops-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yadu-troops'),
    ('infinity-dart-optimate-huntress', 'ALE-019', 'Infinity: Dart, Optimate Huntress', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/dart-optimate-huntress-submachine-gun-grenades-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/dart-optimate-huntress-submachine-gun-grenades'),
    ('infinity-andromeda', 'ALE-020', 'Infinity: Andromeda', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/andromeda-submachine-gun-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/andromeda-submachine-gun'),
    ('infinity-hector', 'ALE-021', 'Infinity: Hector', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/hector-heavy-pistol-exp-ccw-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/hector-heavy-pistol-exp-ccw'),
    ('infinity-penthesilea-amazon-biker-special-edition', 'ALE-022', 'Infinity: Penthesilea Amazon Biker Special Edition', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/penthesilea-amazon-biker-special-edition-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/penthesilea-amazon-biker-special-edition'),
]

# Products already created under PanOceania that are the same Corvus Belli
# SKU as an ALEPH sheet row -- dual-tagged via secondary_factions instead
# of being duplicated. The PAN-0xx/YUJ-030 set is the same one already
# shared with Ariadna/Haqqislam/Nomads; PAN-003 and PAN-021 are new
# recurrences confirmed here. Confirmed with user.
SHARED_UNIT_SKUS = [
    'PAN-003',  # Optimate Agent Maximus
    'PAN-016',  # Beasthunters
    'PAN-017',  # Triphammers, Repurposed Industrial TAGs
    'PAN-018',  # Freelance Operator Samsa
    'PAN-020',  # Warcors, War Correspondents
    'PAN-021',  # Maximus
    'PAN-022',  # Diggers
    'PAN-035',  # Motorized Bounty Hunters
    'PAN-036',  # Oktavia Grímsdóttir
    'PAN-040',  # Monstruckers
    'PAN-041',  # Aïda Swanson
    'PAN-046',  # Miranda Ashcroft
    'YUJ-030',  # Libertos
]


class Command(BaseCommand):
    """Populate the Infinity: ALEPH product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: ALEPH products (ALE-001 to ALE-022) and dual-tags 13 shared units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='aleph',
            defaults={'name': 'ALEPH', 'category': category},
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
                    'batch_tag': 'infinity-aleph-uk',
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
            f'{dual_tagged} shared units dual-tagged with ALEPH.'
        ))
