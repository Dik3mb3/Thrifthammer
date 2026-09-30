"""
Management command: populate_infinity_nomads_products

Creates Infinity's fifth faction, Nomads, under the existing "Infinity"
Category. Same UK-first, no-pricing-yet approach as PanOceania, Yu Jing,
Ariadna, and Haqqislam: only image_url and gw_url (the official Corvus
Belli listing link) are set -- no msrp, no msrp_gbp, no CurrentPrice row
here (seed_corvus_belli_infinity_links.py, which covers the whole
category, handles that).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution. Several products here use a non-default lightbox image index:
Nomads Szalamandra Squadron TAG Pack (-4), Bakunin Expansion Pack Beta
(-2), Mobile Brigada / Corregidor Jaguars / Tunguska Interventors (-5) --
each confirmed live, never assumed. Bakunin Überfallkommando's own gw_url
slug spells it "ueberfallkommando" (German transliteration) but its actual
lightbox filename is "bakunin-uberfallkommando" -- confirmed live, not
derived from the slug.

Cross-faction shared units: 13 of the 49 rows in the source sheet are the
exact same Corvus Belli product (byte-identical gw_url) as a product
already created under PanOceania (11), Yu Jing (1, Libertos), or
Haqqislam (1, Fiddler). The PanOceania/Yu Jing set is the same 11 already
shared with Ariadna and Haqqislam; "Dire Foes 12: Troubled Theft" (already
PAN-026) and "Fiddler, Aristeia!'s ex-toymaker" (already HQQ-010) are new
recurrences here. Dual-tagged via Product.secondary_factions per the
user-confirmed pattern. They are NOT in the PRODUCTS list below -- see
SHARED_UNIT_SKUS.

gw_sku scheme: NOM-001 through NOM-036 (prefix confirmed unused elsewhere
in the catalog before this command was written, following the PAN-/YUJ-/
ARI-/HQQ- precedent; the 13 shared units keep their existing SKU, they
don't get a NOM-xxx number).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-gecko-squadron', 'NOM-001', 'Infinity: Gecko Squadron', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/gecko-squadron-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/gecko-squadron'),
    ('infinity-nomads-army-pack', 'NOM-002', 'Infinity: Nomads Army Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/nomads-army-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/essentials/nomads-army-pack'),
    ('infinity-tunguska-triggermen', 'NOM-003', 'Infinity: Tunguska Triggermen', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/tunguska-triggermen-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/tunguska-triggermen'),
    ('infinity-switchers-gruppa', 'NOM-004', 'Infinity: Switchers Gruppa', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/switchers-gruppa-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/switchers-gruppa'),
    ('infinity-nomads-hero-wolfgang-amadeus-wolff', 'NOM-005', 'Infinity: Nomads Hero, Wolfgang Amadeus Wolff', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/nomads-hero-wolfgang-amadeus-wolff-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/essentials/nomads-hero-wolfgang-amadeus-wolff'),
    ('infinity-nomads-booster-pack-alpha', 'NOM-006', 'Infinity: Nomads Booster Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/nomads-booster-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/nomads-booster-pack-alpha'),
    ('infinity-go-pods', 'NOM-007', 'Infinity: Go-Pods', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/go-pods-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/go-pods'),
    ('infinity-nomads-szalamandra-squadron-tag-pack', 'NOM-008', 'Infinity: Nomads Szalamandra Squadron TAG Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/nomads-szalamandra-squadron-tag-pack-4.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/nomads-szalamandra-squadron-tag-pack'),
    ('infinity-nomads-zonds-remotes-pack', 'NOM-009', 'Infinity: Nomads Zonds Remotes Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/nomads-zonds-remotes-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/nomads-zonds-remotes-pack'),
    ('infinity-nomads-support-pack', 'NOM-010', 'Infinity: Nomads Support Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/essentials-nomads-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/essentials-nomads-support-pack'),
    ('infinity-moran-maasai-hunters', 'NOM-011', 'Infinity: Moran, Maasai Hunters', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/moran-maasai-hunters-ck-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/moran-maasai-hunters'),
    ('infinity-zeros', 'NOM-012', 'Infinity: Zeros', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/zeros-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/zeros'),
    ('infinity-reinf-lizard-squadron', 'NOM-013', 'Infinity: Reinf. Lizard Squadron', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinf-lizard-squadron-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinf-lizard-squadron'),
    ('infinity-reinforcements-nomads-pack-alpha', 'NOM-014', 'Infinity: Reinforcements: Nomads Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinforcements-nomads-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinforcements-nomads-pack-alpha'),
    ('infinity-bakunin-expansion-pack-beta', 'NOM-015', 'Infinity: Bakunin Expansion Pack Beta', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/bakunin-expansion-pack-beta-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/bakunin-expansion-pack-beta'),
    ('infinity-bakunin-uberfallkommando', 'NOM-016', 'Infinity: Bakunin Überfallkommando', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/bakunin-uberfallkommando-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/bakunin-ueberfallkommando'),
    ('infinity-bakunin-expansion-pack-alpha', 'NOM-017', 'Infinity: Bakunin Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/bakunin-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/bakunin-expansion-pack-alpha'),
    ('infinity-sputniks', 'NOM-018', 'Infinity: Sputniks', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/sputniks-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/sputniks'),
    ('infinity-stigmata', 'NOM-019', 'Infinity: Stigmata', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/stigmata-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/stigmata'),
    ('infinity-meteor-zond', 'NOM-020', 'Infinity: Meteor Zond', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/meteor-zond-boarding-shotgun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/meteor-zond-boarding-shotgun'),
    ('infinity-corregidor-fireteam-pack-beta', 'NOM-021', 'Infinity: Corregidor Fireteam Pack Beta', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/corregidor-fireteam-pack-beta-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/corregidor-fireteam-pack-beta'),
    ('infinity-tomcats', 'NOM-022', 'Infinity: Tomcats', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tomcats-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tomcats'),
    ('infinity-corregidor-fireteam-pack-alpha', 'NOM-023', 'Infinity: Corregidor Fireteam Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/corregidor-fireteam-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/corregidor-fireteam-pack-alpha'),
    ('infinity-gator-squadron', 'NOM-024', 'Infinity: Gator Squadron', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/gator-squadron-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/gator-squadron'),
    ('infinity-cassandra-kusanagi', 'NOM-025', 'Infinity: Cassandra Kusanagi', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/cassandra-kusanagi-spitfire-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/cassandra-kusanagi-spitfire'),
    ('infinity-tunguska-cheerkillers', 'NOM-026', 'Infinity: Tunguska Cheerkillers', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tunguska-cheerkillers-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tunguska-cheerkillers'),
    ('infinity-puppetactica-company', 'NOM-027', 'Infinity: Puppetactica Company', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/puppetactica-company-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/puppetactica-company'),
    ('infinity-fast-offensive-unit-zondnautica', 'NOM-028', 'Infinity: Fast Offensive Unit Zondnautica', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/fast-offensive-unit-zondnautica-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/fast-offensive-unit-zondnautica'),
    ('infinity-corregidor-bandits', 'NOM-029', 'Infinity: Corregidor Bandits', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/corregidor-bandits-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/corregidor-bandits'),
    ('infinity-the-hollow-men', 'NOM-030', 'Infinity: The Hollow Men', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/the-hollow-men-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/the-hollow-men'),
    ('infinity-hecklers', 'NOM-031', 'Infinity: Hecklers', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/hecklers-combi-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/hecklers-combi-rifle'),
    ('infinity-zoe-and-pi-well', 'NOM-032', 'Infinity: Zoe and Pi-Well', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/zoe-and-pi-well-engineer-and-remote-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/zoe-and-pi-well-engineer-and-remote'),
    ('infinity-mobile-brigada', 'NOM-033', 'Infinity: Mobile Brigada', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/mobile-brigada-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/mobile-brigada'),
    ('infinity-corregidor-jaguars', 'NOM-034', 'Infinity: Corregidor Jaguars', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/corregidor-jaguars-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/corregidor-jaguars'),
    ('infinity-tunguska-interventors', 'NOM-035', 'Infinity: Tunguska Interventors', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tunguska-interventors-5.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tunguska-interventors'),
    ('infinity-salyut-zonds', 'NOM-036', 'Infinity: Salyut Zonds', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/salyut-zonds-evo-repeater-combi-rifle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/salyut-zonds-evo-repeater-combi-rifle'),
]

# Products already created under PanOceania, Yu Jing, or Haqqislam that
# are the same Corvus Belli SKU as a Nomads sheet row -- dual-tagged via
# secondary_factions instead of being duplicated. The PAN-0xx/YUJ-030 set
# is the same one already shared with Ariadna and Haqqislam; PAN-026 and
# HQQ-010 are new recurrences confirmed here. Confirmed with user.
SHARED_UNIT_SKUS = [
    'PAN-016',  # Beasthunters
    'PAN-017',  # Triphammers, Repurposed Industrial TAGs
    'PAN-018',  # Freelance Operator Samsa
    'PAN-020',  # Warcors, War Correspondents
    'PAN-022',  # Diggers
    'PAN-026',  # Dire Foes 12: Troubled Theft
    'PAN-035',  # Motorized Bounty Hunters
    'PAN-036',  # Oktavia Grímsdóttir
    'PAN-040',  # Monstruckers
    'PAN-041',  # Aïda Swanson
    'PAN-046',  # Miranda Ashcroft
    'YUJ-030',  # Libertos
    'HQQ-010',  # Fiddler, Aristeia!'s ex-toymaker
]


class Command(BaseCommand):
    """Populate the Infinity: Nomads product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: Nomads products (NOM-001 to NOM-036) and dual-tags 13 shared units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='nomads',
            defaults={'name': 'Nomads', 'category': category},
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
                    'batch_tag': 'infinity-nomads-uk',
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
            f'{dual_tagged} shared units dual-tagged with Nomads.'
        ))
