"""
Fix eBay search names for four products:

- Nuln Oil: product name has parentheses that break keyword parsing
- Hellblaster Squad: GW now calls the box "Hellblasters" — "Squad" never appears in titles
- Rangers: product name "Rangers" is too generic; scoped to Aeldari (2 keywords)
- Citadel Colour Base Paint Set: previous search name included "tools" and "40K"
  which never appear in paint set listings
"""

from django.db import migrations

UPDATES = {
    'SP-001':       'Nuln Oil Citadel Shade',
    '48-117':       'Hellblasters Space Marines Warhammer 40k',
    'prod4900144':  'Aeldari Rangers',
    'BS-001':       'Citadel Colour Base Paint Set',
}


def update_search_names(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for sku, name in UPDATES.items():
        Product.objects.filter(gw_sku=sku).update(ebay_search_name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0041_flesh_hounds_search_name'),
    ]

    operations = [
        migrations.RunPython(update_search_names, migrations.RunPython.noop),
    ]
