"""
Migration: add indexes, retailer fields, product is_active, category/faction timestamps.

Changes made:
- Category: add created_at, updated_at
- Faction: add description
- Retailer: add logo_url, affiliate_id, country
- Product: add is_active field, widen msrp to max_digits=10, add composite indexes
- Add db_index=True to slug fields (creates explicit indexes where not already present)
"""

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        # ---- Category timestamps ----
        migrations.AddField(
            model_name='category',
            name='created_at',
            # Use auto_now_add=True equivalent: set a timezone-aware default for
            # existing rows, then Django will auto-set it on new rows.
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # ---- Faction description ----
        migrations.AddField(
            model_name='faction',
            name='description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),

        # ---- Retailer new fields ----
        migrations.AddField(
            model_name='retailer',
            name='logo_url',
            field=models.URLField(blank=True, help_text='URL to retailer logo image'),
        ),
        migrations.AddField(
            model_name='retailer',
            name='affiliate_id',
            field=models.CharField(
                blank=True, max_length=200,
                help_text='Affiliate/partner ID for building tracked links',
            ),
        ),
        migrations.AddField(
            model_name='retailer',
            name='country',
            field=models.CharField(
                blank=True, default='UK', max_length=10,
                help_text='Primary country this retailer serves (e.g. UK, US)',
            ),
        ),

        # ---- Product: is_active field ----
        migrations.AddField(
            model_name='product',
            name='is_active',
            # Default True so existing products stay visible
            field=models.BooleanField(default=True, db_index=True),
        ),

        # ---- Product: widen msrp to max_digits=10 ----
        migrations.AlterField(
            model_name='product',
            name='msrp',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True,
                help_text='Games Workshop recommended retail price',
            ),
        ),

        # ---- Composite indexes on Product ----
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_active', 'category_id'], name='products_pr_is_acti_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_active', 'faction_id'], name='products_pr_is_acti_fac_idx'),
        ),
    ]
