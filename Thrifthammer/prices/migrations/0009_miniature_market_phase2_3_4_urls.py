# Generated 2026-05-02
#
# Imports Miniature Market URLs and prices for Phase 2/3/4 products.
# Data sourced from mm_import_template.csv filled in manually.
#
# Rows with a URL but no price are saved with price=None so the
# Miniature Market scraper can visit the URL and fill in the price
# on its next run.
#
# Idempotent — uses update_or_create, safe to re-run.

from decimal import Decimal
from django.db import migrations


# (gw_sku, mm_url, price_str)  — price_str is 'None' when not available yet
MM_DATA = [
    ('97-08', 'https://www.miniaturemarket.com/gw-97-08.html', '35.99'),
    ('85-02', 'https://www.miniaturemarket.com/gw-85-18.html', '142.99'),
    ('85-06', 'https://www.miniaturemarket.com/gw-85-10.html', '53.99'),
    ('97-11', 'https://www.miniaturemarket.com/gw-97-12.html', '38.99'),
    ('91-07', 'https://www.miniaturemarket.com/gw-91-13.html', '51'),
    ('89-10', 'https://www.miniaturemarket.com/gw-89-48.html', '49.99'),
    ('89-11', 'https://www.miniaturemarket.com/gw-89-44.html', '51'),
    ('83-20', 'https://www.miniaturemarket.com/gw-97-10.html', '35.99'),
    ('83-22', 'https://www.miniaturemarket.com/Warhammer-Age-of-Sigmar-Maggotkin-of-Nurgle-Putrid-Blightkings/GW-83-28-2026', '55.99'),
    ('91-14', 'https://www.miniaturemarket.com/gw-91-27.html', '49.99'),
    ('91-28', 'https://www.miniaturemarket.com/gw-71-14.html', '38.99'),
    ('91-12', 'https://www.miniaturemarket.com/gw-91-26.html', '49.99'),
    ('91-02', 'https://www.miniaturemarket.com/gw-91-25.html', '49.99'),
    ('70-10', 'https://www.miniaturemarket.com/warhammer-age-sigmar-spearhead-nighthaunt-cursed-shacklehorde-gw-70-914.html', '123.99'),
    ('89-30', 'https://www.miniaturemarket.com/warhammer-age-sigmar-orruk-warclans-orruk-ardboyz-gw-89-61.html', '53.99'),
    ('89-22', 'https://www.miniaturemarket.com/gw-89-70.html', '51'),
    ('89-20', 'https://www.miniaturemarket.com/gw-89-29.html', '53.99'),
    ('94-10', 'https://www.miniaturemarket.com/gw-94-25.html', '53.99'),
    ('94-12', 'https://www.miniaturemarket.com/gw-94-23.html', '51'),
    ('83-18', 'https://www.miniaturemarket.com/warhammer-age-of-sigmar-slaves-to-darkness-chaos-warriors-gw-83-06-2023.html', '53.99'),
    ('83-14', 'https://www.miniaturemarket.com/gw-83-51.html', '93.99'),
    ('70-17', 'https://www.miniaturemarket.com/warhammer-age-of-sigmar-spearhead-blades-of-khorne-gw-70-833.html', '123.99'),
    ('70-11', 'https://www.miniaturemarket.com/gw-70-872.html', '123.99'),
    ('70-892', 'https://www.miniaturemarket.com/warhammer-age-sigmar-spearhead-orruk-warclans-ironjawz-bigmob-gw-70-893.html', '123.99'),
    ('70-09', 'https://www.miniaturemarket.com/warhammer-age-of-sigmar-spearhead-ossiarch-bonereapers-gw-70-941.html', '123.99'),
    ('70-04', 'https://www.miniaturemarket.com/warhammer-age-sigmar-spearhead-slaves-to-darkness-darkoath-raiders-gw-70-836.html', '123.99'),
    ('96-14', 'https://www.miniaturemarket.com/warhammer-age-sigmar-stormcast-eternals-lord-celestant-gw-96-68.html', '38.99'),
    ('96-50', 'https://www.miniaturemarket.com/gw-96-57.html', '51'),
    ('HA-002', 'https://www.miniaturemarket.com/gw-31-25.html', '53.99'),
    ('HA-030', 'https://www.miniaturemarket.com/gw-31-26.html', '78.99'),
    ('HA-021', 'https://www.miniaturemarket.com/gw-31-29.html', '71.99'),
    ('HA-010', 'https://www.miniaturemarket.com/warhammer-horus-heresy-legiones-astartes-mkiii-tactical-squad-gw-31-68.html', '67.99'),
    ('HA-041', 'https://www.miniaturemarket.com/gw-31-27.html', '71.99'),
    ('HA-040', 'https://www.miniaturemarket.com/gw-31-35.html', '100.99'),
    ('HA-012', 'https://www.miniaturemarket.com/gw-31-14.html', '62.99'),
    ('HA-001', 'https://www.miniaturemarket.com/gw-31-23.html', '71.99'),
    ('HA-020', 'https://www.miniaturemarket.com/warhammer-horus-heresy-solar-auxilia-lasrifle-section-gw-31-73.html', '67.99'),
    ('KT-003', 'https://www.miniaturemarket.com/kill-team-starter-set-gw-103-54.html', '95.99'),
    ('52-02', 'https://www.miniaturemarket.com/gw-52-37.html', '53.99'),
    ('59-20', 'https://www.miniaturemarket.com/gw-59-15.html', '49.99'),
    ('59-14', 'https://www.miniaturemarket.com/gw-59-12.html', '53.99'),
    ('59-18', 'https://www.miniaturemarket.com/gw-59-14.html', '53.99'),
    ('46-06', 'https://www.miniaturemarket.com/gw-46-15.html', '38.99'),
    ('P-203616', 'https://www.miniaturemarket.com/warhammer-40k-aeldari-asurmen-gw-46-50.html', '38.99'),
    ('prod4900146', 'https://www.miniaturemarket.com/gw-46-30.html', '35.99'),
    ('prod2810200', 'https://www.miniaturemarket.com/gw-46-30.html', '35.99'),
    ('prod4900143', 'https://www.miniaturemarket.com/gw-46-62.html', '95.99'),
    ('P-203620', 'https://www.miniaturemarket.com/warhammer-40k-aeldari-baharroth-gw-46-52.html', '38.99'),
    ('50-24', 'https://www.miniaturemarket.com/gw-50-55.html', '51'),
    ('50-27', 'https://www.miniaturemarket.com/warhammer-40k-orks-big-mek-gw-50-68.html', '44.99'),
    ('55-24', 'https://www.miniaturemarket.com/gw-55-44.html', '49.99'),
    ('41-28', 'https://www.miniaturemarket.com/warhammer-40k-space-marines-librarian-in-terminator-armour-gw-48-06.html', '33.99'),
    ('P-TZEENTCH-BLUEHORRORS', 'https://www.miniaturemarket.com/gw-97-30.html', '38.99'),
    ('48-105', 'https://www.miniaturemarket.com/warhammer-40k-space-marines-captain-with-jump-pack-gw-48-17-2023.html', '35.99'),
    ('48-106', 'https://www.miniaturemarket.com/warhammer-40k-blood-angels-captain-gw-41-23-2024.html', '35.99'),
    ('31-67', 'https://www.miniaturemarket.com/legions-imperialis-knight-households-cerastus-knights-acheron-castigator-gw-03-30.html', '67.99'),
    ('31-66', 'https://www.miniaturemarket.com/legions-imperialis-knight-households-cerastus-knights-acheron-castigator-gw-03-30.html', '67.99'),
    ('P-CSM-DEFILER-2026', 'https://www.miniaturemarket.com/Warhammer-40K-Chaos-Space-Marines-Defiler-New-Arrival/GW-43-22-2026', None),
    ('99120102052', 'https://www.miniaturemarket.com/gw-48-30.html', '97.99'),
    ('43-09', 'https://www.miniaturemarket.com/gw-48-23.html', '63.99'),
    ('99120102092', 'https://www.miniaturemarket.com/gw-52-26.html', '55.99'),
    ('P-CSM-SORC-TERM', 'https://www.miniaturemarket.com/gw-43-69.html', '29.99'),
    ('43-06', 'https://www.miniaturemarket.com/kill-team-legionaries-gw-102-97-2024.html', '63.99'),
    ('99070102015', 'https://www.miniaturemarket.com/gw-43-69.html', '29.99'),
    ('99120201050', 'https://www.miniaturemarket.com/gw-83-10.html', '49.99'),
    ('99120102097', 'https://www.miniaturemarket.com/gw-43-19-new.html', '53.99'),
    ('P-CSM-VINDICATOR', 'https://www.miniaturemarket.com/gw-48-25.html', '63.99'),
    ('P-213409-60030102032', 'https://www.miniaturemarket.com/gw-43-03.html', None),
    ('P-TS-CODEX-2023', 'https://www.miniaturemarket.com/warhammer-40k-codex-thousand-sons-gw-36-01.html', None),
    ('P-240879', 'https://www.miniaturemarket.com/Warhammer-40K-Combat-Patrol-Aeldari-Corsairs/GW-73-463-2026', None),
    ('P-240922', 'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Corsair-Skyreavers/GW-46-80-2026', None),
    ('P-240923', 'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Corsair-Voidreavers/GW-46-84-2026', None),
    ('prod3600196', 'https://www.miniaturemarket.com/gw-46-14.html', '78.99'),
    ('P-241016', 'https://www.miniaturemarket.com/Warhammer-40K-Necrons-C-tan-Shard-of-the-Nightbringer/GW-49-50-2026', '110.99'),
    ('99129915036', 'https://www.miniaturemarket.com/gw-97-09.html', '35.99'),
    ('44-04', 'https://www.miniaturemarket.com/warhammer-40k-dark-angels-azrael-supreme-grand-master-gw-44-18.html', '38.99'),
    ('44-05', 'https://www.miniaturemarket.com/warhammer-40k-dark-angels-belial-grand-master-deathwing-gw-44-23.html', '37.99'),
    ('44-12', 'https://www.miniaturemarket.com/gw-44-11.html', '53.99'),
    ('44-09', 'https://www.miniaturemarket.com/gw-44-11.html', '53.99'),
    ('prod4870189', 'https://www.miniaturemarket.com/gw-46-22.html', '53.99'),
    ('prod4570149-99120102114', 'https://www.miniaturemarket.com/gw-43-49.html', '144.99'),
    ('prod4650190-99120102150', 'https://www.miniaturemarket.com/gw-43-51.html', '53.99'),
    ('prod2620120', 'https://www.miniaturemarket.com/gw-58-15.html', '29.99'),
    ('45-02', 'https://www.miniaturemarket.com/gw-45-22.html', '29.99'),
    ('45-07', 'https://www.miniaturemarket.com/gw-45-07.html', None),
    ('prod3650164', 'https://www.miniaturemarket.com/gw-46-60.html', None),
    ('prod3650295', 'https://www.miniaturemarket.com/gw-46-19.html', None),
    ('99120102089', 'https://www.miniaturemarket.com/gw-43-14.html', '71.99'),
    ('P-203621', 'https://www.miniaturemarket.com/warhammer-40k-aeldari-fuegan-gw-46-53.html', '38.99'),
    ('prod4870188', 'https://www.miniaturemarket.com/gw-46-09-2022.html', '51'),
    ('prod3530579', 'https://www.miniaturemarket.com/gw-58-10.html', '38.99'),
    ('99120102090', 'https://www.miniaturemarket.com/gw-43-15.html', '71.99'),
    ('prod3600197', 'https://www.miniaturemarket.com/gw-46-14.html', '78.99'),
    ('prod4390157', 'https://www.miniaturemarket.com/gw-46-45.html', '53.99'),
    ('50-41', 'https://www.miniaturemarket.com/gw-50-46.html', '123.99'),
    ('54-21', 'https://www.miniaturemarket.com/gw-54-21.html', '164.99'),
    ('prod4390156', 'https://www.miniaturemarket.com/gw-46-49.html', '38.99'),
    ('P-TZEENTCH-KAIROS', 'https://www.miniaturemarket.com/gw-97-26.html', '142.99'),
    ('99129915056', 'https://www.miniaturemarket.com/gw-97-06.html', '142.99'),
    ('P-240921', 'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Kharseth/GW-46-81-2026', None),
    ('P-WE-KT-GOREMONGERS-2025', 'https://www.miniaturemarket.com/kill-team-goremongers-gw-103-89.html', '55.99'),
    ('P-198770-99120118023', 'https://www.miniaturemarket.com/kill-team-hearthkyn-salvagers-gw-103-33-2024.html', '55.99'),
    ('P-203618', 'https://www.miniaturemarket.com/warhammer-40k-aeldari-lhykhis-gw-46-51.html', '38.99'),
    ('48-123', 'https://www.miniaturemarket.com/warhammer-40k-space-marines-lieutenant-gw-48-73-2023.html', '31.99'),
    ('prod4390155', 'https://www.miniaturemarket.com/gw-49-28.html', '31.99'),
    ('P-CSM-MASTER-EXEC', 'https://www.miniaturemarket.com/gw-43-44.html', '29.99'),
    ('prod4870190', 'https://www.miniaturemarket.com/gw-46-42-2022.html', '38.99'),
    ('50-50', 'https://www.miniaturemarket.com/gw-50-19.html', None),
    ('NM-010', 'https://www.miniaturemarket.com/gw-300-11.html', None),
    ('NM-011', 'https://www.miniaturemarket.com/gw-300-10.html', None),
    ('NM-012', 'https://www.miniaturemarket.com/gw-300-29.html', None),
    ('49-20', 'https://www.miniaturemarket.com/gw-49-30.html', '108.99'),
    ('P-241017', 'https://www.miniaturemarket.com/Warhammer-40K-Necrons-Nekrosor-Ammentar/GW-49-52-2026', '55.99'),
    ('prod3550127-99129915060', 'https://www.miniaturemarket.com/gw-97-18.html', '31.99'),
    ('50-53', 'https://www.miniaturemarket.com/gw-50-22.html', '33.99'),
    ('50-55', 'https://www.miniaturemarket.com/warhammer-40k-orks-big-mek-gw-50-68.html', '44.99'),
    ('prod4900150', 'https://www.miniaturemarket.com/warhammer-40k-necrons-overlord-with-translocation-shroud-gw-49-70.html', '33.99'),
    ('P-240880', 'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Prince-Yriel/GW-46-82-2026', None),
    ('prod4900144', 'https://www.miniaturemarket.com/gw-46-29-2022.html', '53.99'),
    ('44-23', 'https://www.miniaturemarket.com/gw-44-11.html', '53.99'),
    ('prod2620121', 'https://www.miniaturemarket.com/gw-58-14.html', None),
    ('prod4900142', 'https://www.miniaturemarket.com/gw-46-28.html', '55.99'),
    ('prod4900145', 'https://www.miniaturemarket.com/gw-46-68.html', '59.99'),
    ('P-KHORNE-SKARBRAND', 'https://www.miniaturemarket.com/gw-97-28.html', None),
    ('prod2620124', 'https://www.miniaturemarket.com/gw-58-11.html', '49.99'),
    ('HA-051', 'https://www.miniaturemarket.com/warhammer-40k-space-marines-chaplain-terminator-armour-gw-48-91.html', '37.99'),
    ('48-29', 'https://www.miniaturemarket.com/warhammer-40k-kill-team-space-marines-scout-squad-gw-103-44-2024.html', '68'),
    ('prod4240206', 'https://www.miniaturemarket.com/gw-46-61.html', None),
    ('P-240924', 'https://www.miniaturemarket.com/Warhammer-40K-Aeldari-Vyper/GW-46-83-2026', None),
    ('prod2600170', 'https://www.miniaturemarket.com/gw-58-12.html', '38.99'),
    ('P-203614', 'https://www.miniaturemarket.com/warhammer-40k-aeldari-swooping-hawks-gw-46-47-2025.html', '53.99'),
    ('56-13', 'https://www.miniaturemarket.com/gw-56-15.html', '53.99'),
    ('56-25', 'https://www.miniaturemarket.com/warhammer-40k-combat-patrol-tau-empire-gw-73-561.html', '142.99'),
    ('56-15', 'https://www.miniaturemarket.com/gw-56-07.html', None),
    ('56-22', 'https://www.miniaturemarket.com/gw-56-24.html', '29.99'),
    ('56-06', 'https://www.miniaturemarket.com/gw-56-06.html', '51'),
    ('56-10', 'https://www.miniaturemarket.com/gw-56-11.html', '63.99'),
    ('56-19', 'https://www.miniaturemarket.com/gw-56-09.html', '38.99'),
    ('56-16', 'https://www.miniaturemarket.com/gw-56-13.html', '100.99'),
    ('P-TZAANGOR-ENL', 'https://www.miniaturemarket.com/gw-83-74.html', '51'),
    ('P-TZAANGOR-SHAMAN', 'https://www.miniaturemarket.com/gw-83-76.html', '31.99'),
    ('55-35', 'https://www.miniaturemarket.com/gw-55-21.html', '53.99'),
    ('prod2780228', 'https://www.miniaturemarket.com/gw-58-12.html', '38.99'),
    ('prod4870187', 'https://www.miniaturemarket.com/gw-46-16.html', '51'),
    ('prod3660120', 'https://www.miniaturemarket.com/gw-46-16.html', '51'),
    ('P-203611', 'https://www.miniaturemarket.com/warhammer-40k-aeldari-warp-spiders-gw-46-43-2025.html', '53.99'),
    ('P-203606', 'https://www.miniaturemarket.com/warhammer-40k-aeldari-war-walkers-gw-46-18-2025.html', '68'),
    ('prod3660121', 'https://www.miniaturemarket.com/gw-46-06.html', None),
    ('prod3590128', 'https://www.miniaturemarket.com/gw-46-13.html', None),
    ('prod3580144', 'https://www.miniaturemarket.com/gw-46-26.html', None),
    ('prod3530578', 'https://www.miniaturemarket.com/gw-46-17.html', None),
]


def apply(apps, schema_editor):
    """Create or update Miniature Market CurrentPrice rows for Phase 2/3/4 products."""
    Product = apps.get_model('products', 'Product')
    Retailer = apps.get_model('products', 'Retailer')
    CurrentPrice = apps.get_model('prices', 'CurrentPrice')

    mm_retailer, _ = Retailer.objects.get_or_create(
        slug='miniature-market',
        defaults={
            'name': 'Miniature Market',
            'website': 'https://www.miniaturemarket.com',
            'country': 'US',
            'is_active': True,
        },
    )

    created_count = 0
    updated_count = 0
    skipped_count = 0

    for gw_sku, url, price_str in MM_DATA:
        products = Product.objects.filter(gw_sku=gw_sku)
        if not products.exists():
            print(f'  [skip] No product found for SKU: {gw_sku}')
            skipped_count += 1
            continue

        price = Decimal(price_str) if price_str else None

        for product in products:
            defaults = {
                'url': url,
                'in_stock': True,
                'not_available': False,
                'manual_url_override': False,
            }
            if price is not None:
                defaults['price'] = price

            _, created = CurrentPrice.objects.update_or_create(
                product=product,
                retailer=mm_retailer,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

    print(f'  Miniature Market import: {created_count} created, {updated_count} updated, {skipped_count} SKUs not found')


def reverse(apps, schema_editor):
    """No meaningful reverse — leave prices as-is on rollback."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('prices', '0008_add_epn_affiliate_params_to_ebay_urls'),
        ('products', '0036_sku_specific_negative_keywords'),
    ]

    operations = [
        migrations.RunPython(apply, reverse),
    ]
