"""
Management command: populate_infinity_yu_jing_products

Creates Infinity's second faction, Yu Jing, under the existing "Infinity"
Category (created by populate_infinity_panoceania_products.py). Same
UK-first, no-pricing-yet approach as PanOceania: only image_url and gw_url
(the official Corvus Belli listing link) are set -- no msrp, no msrp_gbp,
no CurrentPrice row here (that's seed_corvus_belli_infinity_links.py's job,
and it now covers every Infinity faction, not just PanOceania).

image_url uses Corvus Belli's "lightbox/lg" size (~900x700px), individually
verified live against each product's own store.corvusbelli.com page --
never derived from the sheet's "front/xxs" thumbnail filename by string
substitution, per the same reasoning documented in
populate_infinity_panoceania_products.py (confirmed unsafe there: at least
2 of these 37 products also have a lightbox filename that doesn't match
their own front/xxs filename -- PAN-style precedent held again here for
YUJ-004 "Sun Tze" and YUJ-025 "White Banner Action Pack").

Cross-faction shared units: 10 of the 47 rows in the source sheet
("Infinity Yu Jing.xlsx") are the exact same Corvus Belli product (byte-
identical gw_url) as a product already created under PanOceania --
mercenary/generic units Corvus Belli sells as one SKU, usable by multiple
Infinity factions in the actual game rules. Confirmed with the user
2026-09-30: dual-tag these via Product.secondary_factions (same mechanism
already used for WMH-078 and Chaos Daemons mono-god units elsewhere in this
catalog) rather than creating 10 duplicate Product rows. They are NOT in
the PRODUCTS list below -- see SHARED_UNIT_SKUS.

gw_sku scheme: YUJ-001 through YUJ-037 (prefix confirmed unused elsewhere
in the catalog before this command was written; the 10 shared units keep
their existing PAN-0xx SKU, they don't get a YUJ-xxx number).

Run once on Railway startup via Procfile. Safe to re-run -- idempotent
(Product keyed by slug via update_or_create; secondary_factions .add() is
naturally idempotent on a ManyToManyField).
"""
from django.core.management.base import BaseCommand

from products.models import Category, Faction, Product

# (slug, gw_sku, name, image_url, gw_url)
PRODUCTS = [
    ('infinity-gui-feng-spec-ops-bundle', 'YUJ-001', 'Infinity: Gui Feng Spec-Ops Bundle', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/gui-feng-spec-ops-bundle-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/gui-feng-spec-ops-bundle'),
    ('infinity-gui-feng-spec-ops', 'YUJ-002', 'Infinity: Gui Feng Spec-Ops', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/gui-feng-spec-ops-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/gui-feng-spec-ops'),
    ('infinity-ninjas', 'YUJ-003', 'Infinity: Ninjas', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/ninjas-multi-sniper-hacker-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/ninjas-multi-sniper-hacker'),
    ('infinity-sun-tze', 'YUJ-004', 'Infinity: Sun Tze', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/sun-tze-vulkan-shotgun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/sun-tze-thunderbolt-light-shotgun'),
    ('infinity-kuang-shi', 'YUJ-005', 'Infinity: Kuang Shi', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/kuang-shi-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/kuang-shi'),
    ('infinity-feiquan-imperial-tactical-wing', 'YUJ-006', 'Infinity: Fēiquán Imperial Tactical Wing', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/feiquan-imperial-tactical-wing-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/feiquan-imperial-tactical-wing'),
    ('infinity-yu-jing-hero-lei-gong-invincibles-lord-of-thunder', 'YUJ-007', 'Infinity: Yu Jing Hero, Léi Gōng, Invincibles Lord of Thunder', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/yu-jing-hero-lei-g-ng-invincibles-lord-thunder-4.png', 'https://store.corvusbelli.com/en/infinity/wargame/essentials/yu-jing-hero-lei-g-ng-invincibles-lord-thunder'),
    ('infinity-jsa-hero-shinobu-kitsune', 'YUJ-008', 'Infinity: JSA hero, Shinobu Kitsune', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/jsa-hero-shinobu-kitsune-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/jsa-hero-shinobu-kitsune'),
    ('infinity-yu-jing-booster-pack-alpha', 'YUJ-009', 'Infinity: Yu Jing Booster Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/yu-jing-booster-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yu-jing-booster-pack-alpha'),
    ('infinity-yu-jing-blue-wolf-mongol-cavalry', 'YUJ-010', 'Infinity: Yu Jing Blue Wolf Mongol Cavalry', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/yu-jing-blue-wolf-mongol-cavalry-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yu-jing-blue-wolf-mongol-cavalry'),
    ('infinity-longwang-imperial-tag-police', 'YUJ-011', 'Infinity: Lóngwáng, Imperial TAG Police', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/longwang-imperial-tag-police-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/longwang-imperial-tag-police'),
    ('infinity-yu-jing-support-pack', 'YUJ-012', 'Infinity: Yu Jing Support Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/essentials-yu-jing-support-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/essentials-yu-jing-support-pack'),
    ('infinity-white-banner-expansion-pack-beta', 'YUJ-013', 'Infinity: White Banner Expansion Pack Beta', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/white-banner-expansion-pack-beta-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/white-banner-expansion-pack-beta'),
    ('infinity-yu-jing-action-pack', 'YUJ-014', 'Infinity: Yu Jing Action Pack', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/essentials-yu-jing-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/essentials-yu-jing-action-pack'),
    ('infinity-white-banner-expansion-pack-alpha', 'YUJ-015', 'Infinity: White Banner Expansion Pack Alpha', 'https://assets.corvusbelli.net/store/products/infinity/wargame/lightbox/lg/white-banner-expansion-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/white-banner-expansion-pack-alpha'),
    ('infinity-yaoxie-remotes', 'YUJ-016', 'Infinity: Yáoxiè Remotes', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/yaoxie-remotes-lu-duan-rui-shi-2-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yaoxie-remotes-lu-duan-rui-shi'),
    ('infinity-invincible-army-expansion-pack', 'YUJ-017', 'Infinity: Invincible Army Expansion Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/invincible-army-expansion-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/invincible-army-expansion-pack'),
    ('infinity-guilang', 'YUJ-018', 'Infinity: Guilang', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/guilang-hacker-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/guilang-hacker'),
    ('infinity-zuyong-invincibles', 'YUJ-019', 'Infinity: Zúyong Invincibles', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/zuyong-invincibles-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/zuyong-invincibles'),
    ('infinity-reinforcements-yu-jing-pack-alpha', 'YUJ-020', 'Infinity: Reinforcements: Yu Jing Pack Alpha', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/reinforcements-yu-jing-pack-alpha-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/reinforcements-yu-jing-pack-alpha'),
    ('infinity-bixie-the-jade-champion', 'YUJ-021', 'Infinity: Bixie, the Jade Champion', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/bixie-jade-champion-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/bixie-jade-champion'),
    ('infinity-shaolin-warrior-monks', 'YUJ-022', 'Infinity: Shaolin Warrior Monks', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/shaolin-warrior-monks-23-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shaolin-warrior-monks'),
    ('infinity-hulang-shocktroopers', 'YUJ-023', 'Infinity: Húláng Shocktroopers', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/hulang-shocktroopers-submachine-gun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/hulang-shocktroopers-submachine-gun'),
    ('infinity-tiangou-orbital-activity-squad', 'YUJ-024', 'Infinity: Tiāngǒu Orbital Activity Squad', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tiang-u-orbital-activity-squad-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tiang-u-orbital-activity-squad'),
    ('infinity-white-banner-action-pack', 'YUJ-025', 'Infinity: White Banner Action Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/yu-jing-action-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/packs/white-banner-action-pack'),
    ('infinity-yaofang-long-ya', 'YUJ-026', 'Infinity: Yaofang Long Ya', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/yaofang-long-ya-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yaofang-long-ya'),
    ('infinity-jujak-regiment', 'YUJ-027', 'Infinity: Jujak Regiment', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/jujak-regiment-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/jujak-regiment'),
    ('infinity-shang-ji-invincibles', 'YUJ-028', 'Infinity: Shang Ji Invincibles', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/shang-ji-invincibles-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/shang-ji-invincibles'),
    ('infinity-betrayal-characters-pack', 'YUJ-029', 'Infinity: Betrayal Characters Pack', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/betrayal-characters-pack-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/betrayal-characters-pack'),
    ('infinity-libertos', 'YUJ-030', 'Infinity: Libertos', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/libertos-light-shotgun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/libertos-light-shotgun'),
    ('infinity-mowang-troops', 'YUJ-031', 'Infinity: Mówáng Troops', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/mowang-troops-multi-rifle-red-fury-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/mowang-troops-multi-rifle-red-fury'),
    ('infinity-tiger-soldiers', 'YUJ-032', 'Infinity: Tiger Soldiers', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/tiger-soldiers-spitfire-boarding-shotgun-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/tiger-soldiers-spitfire-boarding-shotgun'),
    ('infinity-dragon-lady', 'YUJ-033', 'Infinity: Dragon Lady', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/dragon-lady-3.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/dragon-lady'),
    ('infinity-su-jian-immediate-action-unit', 'YUJ-034', 'Infinity: Sù-Jiàn Immediate Action Unit', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/su-jian-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/su-jian'),
    ('infinity-guijia-squadron', 'YUJ-035', 'Infinity: Gūijiă Squadron', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/guijia-squadrons-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/guijia-squadrons'),
    ('infinity-yan-huo-invincible', 'YUJ-036', 'Infinity: Yān Huǒ Invincible', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/invincibles-yan-huo-hmc-2.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/invincibles-yan-huo-hmc'),
    ('infinity-yaopu-pangguling', 'YUJ-037', 'Infinity: Yáopú Pangguling', 'https://assets.corvusbelli.net/store/products/wargames/infinity/lightbox/lg/yaopu-pangguling-1.png', 'https://store.corvusbelli.com/en/infinity/wargame/miniatures/yaopu-pangguling'),
]

# Products already created under PanOceania that are the same Corvus Belli
# SKU as a Yu Jing sheet row -- dual-tagged via secondary_factions instead
# of being duplicated. Confirmed with user 2026-09-30.
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
]


class Command(BaseCommand):
    """Populate the Infinity: Yu Jing product line (idempotent). Image + official-listing URL only, no pricing."""

    help = 'Populates Infinity: Yu Jing products (YUJ-001 to YUJ-037) and dual-tags 10 shared PanOceania units.'

    def handle(self, *args, **options):
        category = Category.objects.get(slug='infinity')
        faction, _ = Faction.objects.get_or_create(
            slug='yu-jing',
            defaults={'name': 'Yu Jing', 'category': category},
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
                    'batch_tag': 'infinity-yu-jing-pt1',
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
            f'{dual_tagged} shared units dual-tagged with Yu Jing.'
        ))
