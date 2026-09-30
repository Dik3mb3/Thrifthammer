"""
Management command: populate_infinity_panoceania_products

Creates the Infinity product line's first faction, PanOceania, as a new
Category ("Infinity") with a Faction ("PanOceania") underneath it -- same
per-faction structure as Warhammer 40,000, since Infinity will get more
factions added the same way over time (this batch is "Pt. 1").

Infinity is published by Corvus Belli. Their own store (store.corvusbelli.com)
only shows prices in EUR, which this catalog doesn't track as a currency, so
this command intentionally sets ONLY image_url and gw_url (the official
listing link) for each product -- no msrp, no msrp_gbp, no CurrentPrice row
at all. MSRP will be added later from Firestorm Games UK once that phase of
the rollout starts; until then these 48 products show no price anywhere
(expected -- product_detail's "No price data yet" state, same honest-gap
handling used for any product with zero retailer coverage).

Name cleanup applied uniformly (cosmetic only, no facts changed):
  - Every product prefixed "Infinity: " for consistency with how every
    other category is displayed (e.g. "Halo: Flashpoint", "Warmachine: ...").
  - PAN-009's sheet title already started with "Infinity " ("Infinity
    PanOcenia Paint Set") -- the leading word was dropped before adding the
    prefix to avoid "Infinity: Infinity PanOcenia Paint Set". Its "PanOcenia"
    spelling (not "PanOceania") is kept as-is -- confirmed as Corvus Belli's
    own product URL slug, not a spreadsheet typo.

Two products needed a manual Unicode fix during prep -- the accented
characters looked different from what the source file's raw codepoints
actually were (confirmed via ord() on the raw title strings before writing
this file):
  - PAN-030 "Nøkken" uses U+00F8 (o with stroke), not o-umlaut. This letter
    has no ASCII-compatible NFKD decomposition, so slugify() would silently
    DROP it entirely rather than transliterate it (producing "infinity-
    nkken") -- replaced o-with-stroke -> "o" manually before slugifying, so
    the product's slug reads "infinity-nokken".
  - PAN-041 "Aïda Swanson" uses U+00EF (i with diaeresis), not i-acute.
    This one does have a standard decomposition, so slugify() already
    produced the correct "infinity-aida-swanson" without a manual fix.

gw_sku scheme: PAN-001 through PAN-048 (prefix confirmed unused elsewhere
in the catalog before this command was written).

Source: user-supplied "Infinity Panoceania Pt. 1.xlsx" (Title/Title_URL/
Image columns, 48 rows). gw_url is taken directly from that sheet,
unmodified. image_url is NOT the sheet's own Image column -- that column
pointed at Corvus Belli's "front/xxs" thumbnail (148x148px, the same tiny
icon asset their own category grid uses), which rendered visibly blurry at
product-page size. Replaced with each product's "lightbox/lg" image
(~900x700px) instead, individually verified live against each product's
own store.corvusbelli.com page rather than derived by string substitution
-- that substitution was tested and confirmed UNSAFE (PAN-031's lightbox
filename doesn't match its own front/xxs filename at all, and several
products use a lightbox image index other than the default -1).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
#
# image_url uses Corvus Belli's "lightbox/lg" size (verified ~900x700px per
# product via live JS extraction against store.corvusbelli.com -- never
# guessed from the "front/xxs" filename by string substitution, since that
# was confirmed UNSAFE: at least one product (PAN-031) has a lightbox
# filename stem that doesn't match its own front/xxs thumbnail filename at
# all, and several others use a different image number suffix (-2, -3) than
# the default -1. The original sheet's images were all "front/xxs" (148x148,
# the same asset Corvus Belli uses for tiny category-grid icons) -- too small
# for a full-size product image, hence the visible blurriness this replaces.
PRODUCTS = [
    ('infinity-indigo-spec-ops-bundle', 'PAN-001', 'Infinity: Indigo Spec-Ops Bundle', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/indigo-spec-ops-bundle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/indigo-spec-ops-bundle'),
    ('infinity-indigo-spec-ops', 'PAN-002', 'Infinity: Indigo Spec-Ops', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/indigo-spec-ops-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/indigo-spec-ops'),
    ('infinity-optimate-agent-maximus', 'PAN-003', 'Infinity: Optimate Agent Maximus', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/optimate-agent-maximus-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/optimate-agent-maximus'),
    ('infinity-kestrel-expansion-pack-delta', 'PAN-004', 'Infinity: Kestrel Expansion Pack Delta', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/kestrel-expansion-pack-delta-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kestrel-expansion-pack-delta'),
    ('infinity-panoceania-hero-jeanne-darc-20', 'PAN-005', "Infinity: PanOceania Hero, Jeanne d'Arc 2.0", 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/panoceania-hero-jeanne-d-arc-2-0-mobility-armor-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/panoceania-hero-jeanne-d-arc-2-0-mobility-armor'),
    ('infinity-panoceania-booster-pack-alpha', 'PAN-006', 'Infinity: PanOceania Booster Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/panoceania-booster-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/panoceania-booster-pack-alpha'),
    ('infinity-drummers', 'PAN-007', 'Infinity: Drummers', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/drummers-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/drummers'),
    ('infinity-panoceania-cutters-tag-pack', 'PAN-008', 'Infinity: PanOceania Cutters TAG Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/panoceania-cutters-tag-pack-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/panoceania-cutters-tag-pack'),
    ('infinity-panocenia-paint-set', 'PAN-009', 'Infinity: PanOcenia Paint Set', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/infinity-panocenia-paint-set-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/infinity-panocenia-paint-set'),
    ('infinity-kestrel-expansion-pack-gamma', 'PAN-010', 'Infinity: Kestrel Expansion Pack Gamma', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/kestrel-expansion-pack-gamma-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kestrel-expansion-pack-gamma'),
    ('infinity-panoceania-dronbot-remotes-pack', 'PAN-011', 'Infinity: PanOceania Dronbot Remotes Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/panoceania-dronbot-remotes-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/panoceania-dronbot-remotes-pack'),
    ('infinity-panoceania-support-pack', 'PAN-012', 'Infinity: PanOceania Support Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/essentials-panoceania-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/essentials-panoceania-support-pack'),
    ('infinity-kestrel-expansion-pack-beta', 'PAN-013', 'Infinity: Kestrel Expansion Pack Beta', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/kestrel-expansion-pack-beta-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/kestrel-expansion-pack-beta'),
    ('infinity-dr-priya-harper', 'PAN-014', 'Infinity: Dr. Priya Harper', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/dr-priya-harper-plasma-carbine-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/dr-priya-harper-plasma-carbine'),
    ('infinity-panoceania-army-pack', 'PAN-015', 'Infinity: PanOceania Army Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/essentials-panoceania-army-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/panoceania-army-pack'),
    ('infinity-beasthunters', 'PAN-016', 'Infinity: Beasthunters', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/beasthunters-tactical-bow-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/beasthunters-tactical-bow'),
    ('infinity-triphammers-repurposed-industrial-tags', 'PAN-017', 'Infinity: Triphammers, Repurposed Industrial TAGs', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/triphammers-repurposed-industrial-tags-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/triphammers-repurposed-industrial-tags'),
    ('infinity-freelance-operator-samsa', 'PAN-018', 'Infinity: Freelance Operator Samsa', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/freelance-operator-samsa-plasma-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/freelance-operator-samsa-plasma-rifle'),
    ('infinity-tikbalangs', 'PAN-019', 'Infinity: Tikbalangs', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tikbalangs-armored-chasseurs-regiment-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tikbalangs-armored-chasseurs-regiment'),
    ('infinity-warcors-war-correspondents', 'PAN-020', 'Infinity: Warcors, War Correspondents', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/warcors-war-correspondents-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/warcors-war-correspondents'),
    ('infinity-maximus', 'PAN-021', 'Infinity: Maximus', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/maximus-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/maximus'),
    ('infinity-diggers', 'PAN-022', 'Infinity: Diggers', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/diggers-chain-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/diggers-chain-rifle'),
    ('infinity-reinforcements-panoceania-pack-alpha', 'PAN-023', 'Infinity: Reinforcements: PanOceania Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinforcements-panoceania-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinforcements-panoceania-pack-alpha'),
    ('infinity-military-orders-expansion-pack-alpha', 'PAN-024', 'Infinity: Military Orders Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/military-orders-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/military-orders-expansion-pack-alpha'),
    ('infinity-armbots', 'PAN-025', 'Infinity: Armbots', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/armbots-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/armbots'),
    ('infinity-dire-foes-12-troubled-theft', 'PAN-026', 'Infinity: Dire Foes 12: Troubled Theft', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/dire-foes-12-troubled-theft-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/dire-foes-12-troubled-theft'),
    ('infinity-military-order-hospitaller-action-pack', 'PAN-027', 'Infinity: Military Order Hospitaller Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/military-order-hospitaller-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/military-order-hospitaller-action-pack'),
    ('infinity-karhu-special-team', 'PAN-028', 'Infinity: Karhu Special Team', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/karhu-special-team-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/karhu-special-team'),
    ('infinity-panoceania-headquarters-pack', 'PAN-029', 'Infinity: PanOceania Headquarters Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/panoceania-headquarters-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/panoceania-headquarters-pack'),
    ('infinity-nokken', 'PAN-030', 'Infinity: Nøkken', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/nokken-spitfire-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/nokken-spitfire'),
    ('infinity-winterfor-action-pack', 'PAN-031', 'Infinity: WinterFor Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/panoceania-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/winterfor-action-pack'),
    ('infinity-vargar-maximum-security-team', 'PAN-032', 'Infinity: Vargar Maximum Security Team', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/vargar-maximum-security-team-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/vargar-maximum-security-team'),
    ('infinity-knight-of-santiago', 'PAN-033', 'Infinity: Knight of Santiago', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/knight-santiago-spitfire-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/knight-santiago-spitfire'),
    ('infinity-knight-of-montesa', 'PAN-034', 'Infinity: Knight of Montesa', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/knight-montesa-red-fury-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/knight-montesa-red-fury'),
    ('infinity-motorized-bounty-hunters', 'PAN-035', 'Infinity: Motorized Bounty Hunters', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/motorized-bounty-hunters-boarding-shotgun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/motorized-bounty-hunters-boarding-shotgun'),
    ('infinity-oktavia-grimsdottir', 'PAN-036', 'Infinity: Oktavia Grímsdóttir', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/oktavia-grimsdottir-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/oktavia-grimsdottir'),
    ('infinity-trinitarian-tertiaries', 'PAN-037', 'Infinity: Trinitarian Tertiaries', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/trinitarian-tertiaries-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/trinitarian-tertiaries'),
    ('infinity-teutonic-knights', 'PAN-038', 'Infinity: Teutonic Knights', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/teutonic-knights-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/teutonic-knights'),
    ('infinity-military-orders-action-pack', 'PAN-039', 'Infinity: Military Orders Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/military-orders-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/military-orders-action-pack'),
    ('infinity-monstruckers', 'PAN-040', 'Infinity: Monstruckers', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/monstruckers-boarding-shotgun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/monstruckers-boarding-shotgun'),
    ('infinity-aida-swanson', 'PAN-041', 'Infinity: Aïda Swanson', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/aida-swanson-submachine-gun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/aida-swanson-submachine-gun'),
    ('infinity-helot-militia', 'PAN-042', 'Infinity: Helot Militia', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/helot-militia-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/helot-militia'),
    ('infinity-orc-troops', 'PAN-043', 'Infinity: Orc Troops', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/orc-troops-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/orc-troops'),
    ('infinity-patsy-garnett', 'PAN-044', 'Infinity: Patsy Garnett', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/patsy-garnett-submachine-gun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/patsy-garnett-submachine-gun'),
    ('infinity-tech-bee-crabbot-ancillary', 'PAN-045', 'Infinity: Tech Bee & Crabbot Ancillary', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tech-bee-and-crabbot-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tech-bee-and-crabbot'),
    ('infinity-miranda-ashcroft', 'PAN-046', 'Infinity: Miranda Ashcroft', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/miranda-ashcroft-combi-rifle-3.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/miranda-ashcroft-combi-rifle'),
    ('infinity-seraphs', 'PAN-047', 'Infinity: Seraphs', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/seraphs-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/seraphs'),
    ('infinity-mulebots', 'PAN-048', 'Infinity: Mulebots', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/mulebots-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/mulebots'),
]


class Command(BaseCommand):
    """Populate the Infinity: PanOceania product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: PanOceania products (PAN-001 to PAN-048). No pricing -- MSRP added later from Firestorm.'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='infinity',
            defaults={'name': 'Infinity'},
        )
        faction, _ = Faction.objects.get_or_create(
            slug='panoceania',
            defaults={'name': 'PanOceania', 'category': category},
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
                    'batch_tag': 'infinity-panoceania-pt1',
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
            else:
                products_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Products: {products_created} created, {products_updated} updated.'
        ))
