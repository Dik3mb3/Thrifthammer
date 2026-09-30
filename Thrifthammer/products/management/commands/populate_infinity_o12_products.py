"""
Management command: populate_infinity_o12_products

Creates Infinity's eighth faction, O-12, under the existing "Infinity"
Category. Same UK-first, no-pricing-yet approach as the prior factions:
only image_url and gw_url (the official Corvus Belli listing link) are
set -- no msrp, no msrp_gbp, no CurrentPrice row here
(seed_corvus_belli_infinity_links.py, which covers the whole category,
handles that).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution. O-12 Expansion Pack Beta/Alpha's real lightbox filenames
are "o-12-booster-pack-beta"/"o-12-booster-pack-alpha" (differ from their
own gw_url slug "o-12-expansion-pack-..."), already hinted at correctly
by the sheet's own front/xxs reference but confirmed live here regardless.

Cross-faction shared units: 12 of the 35 rows in the source sheet are the
exact same Corvus Belli product as a product already created under
PanOceania, Haqqislam, or ALEPH. The usual PanOceania set recurs (minus
Freelance Operator Samsa and Libertos, not present in this sheet), plus
three new recurrences: "Saladin" (HQQ-016), "Andromeda" (ALE-020), and
"Hector" (ALE-021). Dual-tagged via Product.secondary_factions per the
user-confirmed pattern. They are NOT in the PRODUCTS list below -- see
SHARED_UNIT_SKUS.

gw_sku scheme: O12-001 through O12-023 (prefix confirmed unused elsewhere
in the catalog before this command was written, following the PAN-/YUJ-/
ARI-/HQQ-/NOM-/ALE-/CA- precedent; the 12 shared units keep their existing
SKU, they don't get an O12-xxx number).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-infinity-o-12-paint-set-kappa-missile-launcher-exclusive', 'O12-001', 'Infinity: Infinity O-12 Paint Set Kappa Missile Launcher exclusive', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/infinity-o-12-paint-set-kappa-missile-launcher-exclusive-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/accesories/infinity-o-12-paint-set-kappa-missile-launcher-exclusive'),
    ('infinity-tinker-and-zetbot-remote', 'O12-002', 'Infinity: Tinker and Zetbot Remote', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/tinker-zetbot-remote-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tinker-zetbot-remote'),
    ('infinity-jamie-arantes', 'O12-003', 'Infinity: Jamie Arantes', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/jamie-arantes-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/jamie-arantes'),
    ('infinity-torchlight-expansion-pack-beta', 'O12-004', 'Infinity: Torchlight Expansion Pack Beta', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/torchlight-expansion-pack-beta-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/torchlight-expansion-pack-beta'),
    ('infinity-raveneye-officer', 'O12-005', 'Infinity: Raveneye Officer', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/raveneye-officer-submachine-gun-e-marat-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/raveneye-officer-submachine-gun-e-marat'),
    ('infinity-wreckers-fire-recon-armored-squad', 'O12-006', 'Infinity: Wreckers, Fire Recon Armored Squad', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/wreckers-fire-recon-armored-squad-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/wreckers-fire-recon-armored-squad'),
    ('infinity-o-12-torchlight-brigade-action-pack', 'O12-007', 'Infinity: O-12 Torchlight Brigade Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/o-12-torchlight-brigade-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/o-12-torchlight-brigade-action-pack'),
    ('infinity-reinforcements-o-12-pack-alpha', 'O12-008', 'Infinity: Reinforcements: O-12 Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinforcements-o-12-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinforcements-o-12-pack-alpha'),
    ('infinity-starmada-expansion-pack-alpha', 'O12-009', 'Infinity: Starmada Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/starmada-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/starmada-expansion-pack-alpha'),
    ('infinity-roadbots-highway-patrol', 'O12-010', 'Infinity: RoadBots Highway Patrol', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/roadbots-highway-patrol-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/roadbots-highway-patrol'),
    ('infinity-fuzzbots', 'O12-011', 'Infinity: Fuzzbots', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/fuzzbots-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/fuzzbots'),
    ('infinity-cyberghost', 'O12-012', 'Infinity: Cyberghost', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/cyberghost-hacker-pitcher-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/cyberghost-hacker-pitcher'),
    ('infinity-raptor-boarding-squad', 'O12-013', 'Infinity: Raptor Boarding Squad', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/raptor-boarding-squad-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/raptor-boarding-squad'),
    ('infinity-nyoka-assault-troops', 'O12-014', 'Infinity: Nyoka Assault Troops', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/nyoka-assault-troops-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/nyoka-assault-troops'),
    ('infinity-o-12-expansion-pack-beta', 'O12-015', 'Infinity: O-12 Expansion Pack Beta', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/o-12-booster-pack-beta-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/o-12-expansion-pack-beta'),
    ('infinity-o-12-expansion-pack-alpha', 'O12-016', 'Infinity: O-12 Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/o-12-booster-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/o-12-expansion-pack-alpha'),
    ('infinity-zeta-unit', 'O12-017', 'Infinity: Zeta Unit', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/zeta-unit-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/zeta-unit'),
    ('infinity-starmada-action-pack', 'O12-018', 'Infinity: Starmada Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/starmada-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/starmada-action-pack'),
    ('infinity-copperbot-remotes-pack', 'O12-019', 'Infinity: Copperbot Remotes Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/copperbot-remotes-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/copperbot-remotes-pack'),
    ('infinity-o-12-support-pack', 'O12-020', 'Infinity: O-12 Support Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/o-12-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/o-12-support-pack'),
    ('infinity-o-12-action-pack', 'O12-021', 'Infinity: O-12 Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/o-12-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/o-12-action-pack'),
    ('infinity-alpha-unit', 'O12-022', 'Infinity: Alpha Unit', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/alpha-unit-light-shotgun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/alpha-unit-light-shotgun'),
    ('infinity-team-sirius', 'O12-023', 'Infinity: Team Sirius', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/team-sirius-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/team-sirius'),
]

# Products already created under PanOceania, Haqqislam, or ALEPH that are
# the same Corvus Belli SKU as an O-12 sheet row -- dual-tagged via
# secondary_factions instead of being duplicated. HQQ-016, ALE-020, and
# ALE-021 are new recurrences not seen in prior factions. Confirmed with
# user.
SHARED_UNIT_SKUS = [
    'PAN-016',  # Beasthunters
    'PAN-017',  # Triphammers, Repurposed Industrial TAGs
    'PAN-020',  # Warcors, War Correspondents
    'PAN-022',  # Diggers
    'PAN-035',  # Motorized Bounty Hunters
    'PAN-036',  # Oktavia Grímsdóttir
    'PAN-040',  # Monstruckers
    'PAN-041',  # Aïda Swanson
    'PAN-046',  # Miranda Ashcroft
    'HQQ-016',  # Saladin
    'ALE-020',  # Andromeda
    'ALE-021',  # Hector
]


class Command(BaseCommand):
    """Populate the Infinity: O-12 product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: O-12 products (O12-001 to O12-023) and dual-tags 12 shared units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='o-12',
            defaults={'name': 'O-12', 'category': category},
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
                    'batch_tag': 'infinity-o12-uk',
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
            f'{dual_tagged} shared units dual-tagged with O-12.'
        ))
