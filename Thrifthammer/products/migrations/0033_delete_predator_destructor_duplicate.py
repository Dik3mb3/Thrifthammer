# Generated 2026-04-14 — remove duplicate Predator Destructor product.
#
# Space Marine Predator (48-23, slug "space-marine-predator") already covers
# both build variants (Annihilator / Destructor) of this kit.  The separate
# "Predator Destructor" product (slug "space-marine-predator-destructor") was
# added in populate_sm_phase2_products but is a duplicate SKU pointing to the
# same GW box.  Deleting it (SET_NULL on FK) also nulls any UnitType rows
# that referenced it; we immediately re-link those UnitTypes to the canonical
# space-marine-predator (48-23) product so pricing is restored.

from django.db import migrations


def delete_and_relink(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    UnitType = apps.get_model('calculators', 'UnitType')

    # Delete the duplicate — FK is SET_NULL so linked UnitTypes get product=NULL
    Product.objects.filter(slug='space-marine-predator-destructor').delete()

    # Re-link any now-orphaned Predator Destructor UnitTypes to the real product
    canonical = Product.objects.filter(slug='space-marine-predator').first()
    if canonical:
        UnitType.objects.filter(
            name='Predator Destructor', product__isnull=True
        ).update(product=canonical)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0032_add_parts_negative_keyword'),
        ('calculators', '0010_unique_unit_type_name_per_faction'),
    ]

    operations = [
        migrations.RunPython(
            code=delete_and_relink,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
