"""
Management command: populate_infinity_ariadna_products

Creates Infinity's third faction, Ariadna, under the existing "Infinity"
Category. Same UK-first, no-pricing-yet approach as PanOceania and Yu
Jing: only image_url and gw_url (the official Corvus Belli listing link)
are set -- no msrp, no msrp_gbp, no CurrentPrice row here
(seed_corvus_belli_infinity_links.py, which covers the whole category,
handles that).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution (confirmed unsafe again here: ARI-016 "Ariadna Expansion Pack
Alpha" has a lightbox filename, "ariadna-booster-pack-alpha", that matches
neither its own gw_url slug "ariadna-expasion-pack-alpha" [sic, Corvus
Belli's own typo] nor a simple front/xxs substitution).

Two products share a display name on the source sheet ("Uxía McNeill",
rows 21 and 29) but are genuinely different weapon-loadout variants with
different gw_url values (boarding-shotgun vs assault-pistol) -- each
product's own <h1> on its Corvus Belli page was used to disambiguate:
"Uxía McNeill (Boarding Shotgun)" and "Uxía McNeill (Assault Pistol)".

Cross-faction shared units: 11 of the 44 rows in the source sheet
("Infinity Ariadna UK.xlsx") are the exact same Corvus Belli product
(byte-identical gw_url) as a product already created under PanOceania (10)
or Yu Jing (1, Libertos). Confirmed with user: dual-tagged via
Product.secondary_factions, same as the PanOceania/Yu Jing overlap. They
are NOT in the PRODUCTS list below -- see SHARED_UNIT_SKUS.

gw_sku scheme: ARI-001 through ARI-033 (prefix confirmed unused elsewhere
in the catalog before this command was written; the 11 shared units keep
their existing PAN-0xx/YUJ-0xx SKU, they don't get an ARI-xxx number).

Source sheet also has a "sku" column (Corvus Belli's own internal
reference code, e.g. "280787-1231") -- not stored anywhere; no existing
field for it and it isn't needed for image/link display.

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-ioann-bann-varangian-dog-warrior', 'ARI-001', 'Infinity: Ioann Bann, Varangian Dog-Warrior', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/ioann-bann-varangian-dog-warrior-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/ioann-bann-varangian-dog-warrior'),
    ('infinity-1st-highlander-sas', 'ARI-002', 'Infinity: 1st Highlander S.A.S.', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/1st-highlander-s-a-s-chain-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/1st-highlander-s-a-s-chain-rifle'),
    ('infinity-ariadna-support-pack', 'ARI-003', 'Infinity: Ariadna Support Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/ariadna-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/ariadna-support-pack'),
    ('infinity-vystrel-mobile-artillery-regiment', 'ARI-004', 'Infinity: Vystrel Mobile Artillery Regiment', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/vystrel-mobile-artillery-regiment-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/vystrel-mobile-artillery-regiment'),
    ('infinity-tak-expansion-pack-alpha', 'ARI-005', 'Infinity: TAK Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/tak-expansion-pack-alpha-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tak-expansion-pack-alpha'),
    ('infinity-kibervolk-patrol', 'ARI-006', 'Infinity: Kibervolk Patrol', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/kibervolk-patrol-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kibervolk-patrol'),
    ('infinity-ariadna-action-pack', 'ARI-007', 'Infinity: Ariadna Action Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/ariadna-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/ariadna-action-pack'),
    ('infinity-reinforcements-ariadna-pack-alpha', 'ARI-008', 'Infinity: Reinforcements: Ariadna Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinforcements-ariadna-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinforcements-ariadna-pack-alpha'),
    ('infinity-highlander-cateran', 'ARI-009', 'Infinity: Highlander Cateran', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/highlander-cateran-t2-sniper-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/highlander-cateran-t2-sniper-rifle'),
    ('infinity-kosmoflot-support-pack', 'ARI-010', 'Infinity: Kosmoflot Support Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/kosmoflot-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kosmoflot-support-pack'),
    ('infinity-patchers-structural-response-team', 'ARI-011', 'Infinity: Patchers, Structural Response Team', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/patchers-structural-response-team-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/patchers-structural-response-team'),
    ('infinity-kosmoflot-expansion-pack-alpha', 'ARI-012', 'Infinity: Kosmoflot Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/kosmoflot-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kosmoflot-expansion-pack-alpha'),
    ('infinity-scots-guard', 'ARI-013', 'Infinity: Scots Guard', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/scots-guard-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/scots-guard'),
    ('infinity-chernobog-armored-detachment', 'ARI-014', 'Infinity: Chernobog Armored Detachment', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/chernobog-armored-detachment-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/chernobog-armored-detachment'),
    ('infinity-uxia-mcneill-boarding-shotgun', 'ARI-015', 'Infinity: Uxía McNeill (Boarding Shotgun)', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/uxia-mcneill-boarding-shotgun-codeone-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/uxia-mcneill-boarding-shotgun'),
    ('infinity-ariadna-expansion-pack-alpha', 'ARI-016', 'Infinity: Ariadna Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/ariadna-booster-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/ariadna-expasion-pack-alpha'),
    ('infinity-polaris-team-beast-pack', 'ARI-017', 'Infinity: Polaris Team Beast Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/polaris-team-beast-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/polaris-team-beast-pack'),
    ('infinity-irmandinhos', 'ARI-018', 'Infinity: Irmandinhos', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/irmandinhos-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/irmandinhos'),
    ('infinity-tankhunters', 'ARI-019', 'Infinity: TankHunters', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tankhunters-autocannon-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tankhunters-autocannon'),
    ('infinity-uxia-mcneill-assault-pistol', 'ARI-020', 'Infinity: Uxía McNeill (Assault Pistol)', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/uxia-mcneill-assault-pistol-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/uxia-mcneill-assault-pistol'),
    ('infinity-equipe-mirage-5', 'ARI-021', 'Infinity: Equipe Mirage-5', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/equipe-mirage-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/equipe-mirage'),
    ('infinity-tartary-army-corps-action-pack', 'ARI-022', 'Infinity: Tartary Army Corps Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tartary-army-corps-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tartary-army-corps-action-pack'),
    ('infinity-intel-spec-ops', 'ARI-023', 'Infinity: Intel Spec-Ops', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/intel-spec-ops-heavy-pistol-sniper-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/intel-spec-ops-heavy-pistol-sniper'),
    ('infinity-pavel-mcmannus', 'ARI-024', 'Infinity: Pavel McMannus', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/pavel-mcmannus-ojotnik-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/pavel-mcmannus-ojotnik'),
    ('infinity-dynamo-reg', 'ARI-025', 'Infinity: Dynamo Reg', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/dynamo-reg-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/dynamo-reg'),
    ('infinity-frontoviks', 'ARI-026', 'Infinity: Frontoviks', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/frontoviks-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/frontoviks'),
    ('infinity-line-kazaks', 'ARI-027', 'Infinity: Line Kazaks', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/line-kazaks-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/line-kazaks'),
    ('infinity-kazak-spetsnazs', 'ARI-028', 'Infinity: Kazak Spetsnazs', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/kazak-spetsnazs-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kazak-spetsnazs'),
    ('infinity-col-yevgueni-voronin', 'ARI-029', 'Infinity: Col. Yevgueni Voronin', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/col-yevgueni-voronin-cossack-diplomatic-corps-ap-ccw-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/col-yevgueni-voronin-cossack-diplomatic-corps-ap-ccw'),
    ('infinity-roger-van-zant', 'ARI-030', 'Infinity: Roger Van Zant', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/roger-van-zant-capt-6th-airborne-heavy-pistol-ap-ccw-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/roger-van-zant-capt-6th-airborne-heavy-pistol-ap-ccw'),
    ('infinity-dog-warriors', 'ARI-031', 'Infinity: Dog-Warriors', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/dog-warriors-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/dog-warriors'),
    ('infinity-antipode-assault-pack', 'ARI-032', 'Infinity: Antipode Assault Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/antipode-assault-pack-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/antipode-assault-pack'),
    ('infinity-traktor-muls-regiment-of-artillery-and-support', 'ARI-033', 'Infinity: Traktor Muls. Regiment of Artillery and Support', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/traktor-muls-regiment-of-artillery-and-support-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/traktor-muls-regiment-of-artillery-and-support'),
]

# Products already created under PanOceania or Yu Jing that are the same
# Corvus Belli SKU as an Ariadna sheet row -- dual-tagged via
# secondary_factions instead of being duplicated. Confirmed with user.
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
    """Populate the Infinity: Ariadna product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: Ariadna products (ARI-001 to ARI-033) and dual-tags 11 shared units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='ariadna',
            defaults={'name': 'Ariadna', 'category': category},
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
                    'batch_tag': 'infinity-ariadna-uk',
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
            f'{dual_tagged} shared units dual-tagged with Ariadna.'
        ))
