# Generated 2026-05-20
#
# Plants Amazon URLs for:
#   - All 24 Seraphon products that have Amazon listings (SR-001 to SR-028,
#     excluding SR-013 / SR-015 / SR-017 / SR-019 which have no listing)
#   - Canoptek Wraiths — corrects the URL that migration 0010 left wrong
#     (prod4390156 was shared with Jain Zar; Jain Zar's entry was last so
#     it overwrote the Wraiths URL).  Looked up by slug to avoid the
#     duplicate-gw_sku issue.
#
# Prices are left for the Amazon scraper to fill in on its next run.
# Matches the exact pattern of prices/migrations/0010_amazon_phase2_3_4_urls.py.

from django.db import migrations


# (gw_sku, amazon_url)  — Seraphon SKUs
SERAPHON_DATA = [
    ('SR-001', 'https://www.amazon.com/dp/B0C5XPQ558?tag=thrifthammer7-20'),   # Aggradon Lancers
    ('SR-002', 'https://www.amazon.com/dp/B017K7M58U?tag=thrifthammer7-20'),   # Bastiladon
    # ⚠ SR-003 / SR-025 / SR-026 Engine of the Gods / Stegadon / Stegadon Chief share one ASIN
    ('SR-003', 'https://www.amazon.com/dp/B017K7M2EW?tag=thrifthammer7-20'),   # Engine of the Gods
    ('SR-004', 'https://www.amazon.com/dp/B0BVGP6R5P?tag=thrifthammer7-20'),   # Hunters of Huanchi
    # ⚠ SR-005 / SR-006 Kroxigor / Kroxigor Warspawned share one ASIN
    ('SR-005', 'https://www.amazon.com/dp/B0C5XNZ3W4?tag=thrifthammer7-20'),   # Kroxigor
    ('SR-006', 'https://www.amazon.com/dp/B0C5XNZ3W4?tag=thrifthammer7-20'),   # Kroxigor Warspawned
    ('SR-007', 'https://www.amazon.com/dp/B0FSLDPZJL?tag=thrifthammer7-20'),   # Lord Kroak
    # ⚠ SR-008 / SR-009 Raptadon Chargers / Raptadon Hunters share one ASIN
    ('SR-008', 'https://www.amazon.com/dp/B0C5XN4TCW?tag=thrifthammer7-20'),   # Raptadon Chargers
    ('SR-009', 'https://www.amazon.com/dp/B0C5XN4TCW?tag=thrifthammer7-20'),   # Raptadon Hunters
    ('SR-010', 'https://www.amazon.com/dp/B085LR2GC5?tag=thrifthammer7-20'),   # Realmshaper Engine
    # ⚠ SR-011 / SR-027 Ripperdactyl Riders / Terradon Riders share one ASIN
    ('SR-011', 'https://www.amazon.com/dp/B017K7LW8O?tag=thrifthammer7-20'),   # Ripperdactyl Riders
    ('SR-012', 'https://www.amazon.com/dp/B0C5XND1DS?tag=thrifthammer7-20'),   # Saurus Astrolith Bearer
    # SR-013 Saurus Guard — no Amazon listing
    ('SR-014', 'https://www.amazon.com/dp/B005LVHRFY?tag=thrifthammer7-20'),   # Saurus Oldblood
    # SR-015 Saurus Oldblood on Carnosaur — no Amazon listing
    ('SR-016', 'https://www.amazon.com/dp/B0C5XNLS7W?tag=thrifthammer7-20'),   # Saurus Scar-Veteran on Aggradon
    # SR-017 Saurus Scar-Veteran on Carnosaur — no Amazon listing
    ('SR-018', 'https://www.amazon.com/dp/B0C5XQPH2C?tag=thrifthammer7-20'),   # Saurus Warriors
    # SR-019 Skink Oracle on Troglodon — no Amazon listing
    ('SR-020', 'https://www.amazon.com/dp/B017K7LIWO?tag=thrifthammer7-20'),   # Skink Starpriest
    ('SR-021', 'https://www.amazon.com/dp/B0C5XL7JLP?tag=thrifthammer7-20'),   # Skink Starseer
    ('SR-022', 'https://www.amazon.com/dp/B002EJI002?tag=thrifthammer7-20'),   # Skinks
    ('SR-023', 'https://www.amazon.com/dp/B0C5XJYCGF?tag=thrifthammer7-20'),   # Slann Starmaster
    ('SR-024', 'https://www.amazon.com/dp/B0C5XLZ5H9?tag=thrifthammer7-20'),   # Spawn of Chotec
    ('SR-025', 'https://www.amazon.com/dp/B017K7M2EW?tag=thrifthammer7-20'),   # Stegadon  ⚠ same ASIN as SR-003
    ('SR-026', 'https://www.amazon.com/dp/B017K7M2EW?tag=thrifthammer7-20'),   # Stegadon Chief  ⚠ same ASIN as SR-003
    ('SR-027', 'https://www.amazon.com/dp/B017K7LW8O?tag=thrifthammer7-20'),   # Terradon Riders  ⚠ same ASIN as SR-011
    ('SR-028', 'https://www.amazon.com/dp/B0F9YT2H9W?tag=thrifthammer7-20'),   # Spearhead: Sunblooded Prowlers
]

# Canoptek Wraiths — looked up by slug (not gw_sku) because migrations run
# before populate_necrons_phase3_products, which is the command that migrates
# the product's gw_sku from prod4390156 to 49-18.
CANOPTEK_WRAITHS_SLUG = 'necron-canoptek-wraiths'
CANOPTEK_WRAITHS_URL = 'https://www.amazon.com/dp/B08GBYFKSC?tag=thrifthammer7-20'


def apply(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')
    Retailer = apps.get_model('products', 'Retailer')

    amazon, _ = Retailer.objects.get_or_create(
        slug='amazon',
        defaults={'name': 'Amazon', 'base_url': 'https://www.amazon.com'},
    )

    updated = created = skipped = 0

    # ── Seraphon (lookup by gw_sku, same as migration 0010) ──────────────────
    for gw_sku, url in SERAPHON_DATA:
        products = Product.objects.filter(gw_sku=gw_sku)
        if not products.exists():
            print(f'  [skip] No product for SKU: {gw_sku}')
            skipped += 1
            continue
        for product in products:
            _, was_created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=amazon,
                defaults={
                    'url': url,
                    'in_stock': True,
                    'not_available': False,
                    'manual_url_override': False,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

    # ── Canoptek Wraiths (lookup by slug to avoid duplicate gw_sku) ──────────
    product = Product.objects.filter(slug=CANOPTEK_WRAITHS_SLUG).first()
    if product:
        _, was_created = CurrentPrice.objects.update_or_create(
            product=product,
            retailer=amazon,
            defaults={
                'url': CANOPTEK_WRAITHS_URL,
                'in_stock': True,
                'not_available': False,
                'manual_url_override': False,
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1
        print(f'  [ok] Canoptek Wraiths Amazon URL set')
    else:
        print(f'  [skip] {CANOPTEK_WRAITHS_SLUG} not found')
        skipped += 1

    print(f'  Amazon import: {created} created, {updated} updated, {skipped} SKUs not found')


def reverse(apps, schema_editor):
    """Clear URLs added by this migration (leaves rows, blanks the URL)."""
    Product = apps.get_model('products', 'Product')
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')
    Retailer = apps.get_model('products', 'Retailer')

    amazon = Retailer.objects.filter(slug='amazon').first()
    if not amazon:
        return

    urls = {url for _, url in SERAPHON_DATA} | {CANOPTEK_WRAITHS_URL}
    CurrentPrice.objects.filter(retailer=amazon, url__in=urls).update(url='')


class Migration(migrations.Migration):

    dependencies = [
        ('prices', '0010_amazon_phase2_3_4_urls'),
        ('products', '0056_add_global_neg_keywords_may2026c'),
    ]

    operations = [
        migrations.RunPython(apply, reverse),
    ]
