"""
Django admin configuration for the gundam app.

Mirrors products/admin.py's pattern for Category/Faction/Product.
"""

from django.contrib import admin
from django.db.models import Prefetch
from django.utils.html import format_html

from .models import CurrentPrice, Product, Series


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    """Admin for Gundam series."""

    list_display = ('name', 'slug', 'product_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    @admin.display(description='Products')
    def product_count(self, obj):
        """Show number of products primarily tagged to this series."""
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin for the Gundam product catalog.

    Includes a custom cheapest_current_price column, same pattern as
    products.ProductAdmin.
    """

    list_display = (
        'name', 'series', 'grade', 'scale', 'handle',
        'msrp', 'cheapest_current_price', 'is_active', 'updated_at',
    )
    list_filter = ('is_active', 'series', 'grade', 'created_at')
    search_fields = ('name', 'handle', 'barcode', 'description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('secondary_series',)
    readonly_fields = ('created_at', 'updated_at', 'cheapest_current_price')
    list_editable = ('is_active',)
    list_per_page = 50

    fieldsets = (
        ('Product Info', {
            'fields': ('name', 'slug', 'series', 'secondary_series', 'grade', 'scale', 'is_active'),
        }),
        ('Source data', {
            'fields': ('handle', 'barcode'),
        }),
        ('Content', {
            'fields': ('description', 'image_url'),
        }),
        ('Pricing', {
            'fields': ('msrp', 'cheapest_current_price'),
        }),
        ('Batch tracking', {
            'fields': ('batch_tag',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Prefetch current prices so list view doesn't fire 2 queries per product row."""
        return super().get_queryset(request).prefetch_related(
            Prefetch(
                'current_prices',
                queryset=CurrentPrice.objects.select_related('retailer').order_by('price'),
                to_attr='_prefetched_prices',
            )
        )

    @admin.display(description='Best price')
    def cheapest_current_price(self, obj):
        """Display the lowest current price with retailer name, using prefetched data."""
        prices = getattr(obj, '_prefetched_prices', None)
        if prices is None:
            prices = list(
                CurrentPrice.objects
                .filter(product=obj)
                .select_related('retailer')
                .order_by('price')
            )

        in_stock = [p for p in prices if p.in_stock and p.price is not None]
        best = in_stock[0] if in_stock else next(
            (p for p in prices if p.price is not None), None
        )

        if not best:
            return '—'
        if best.in_stock:
            return format_html('<strong>{}</strong> @ {}', f'${best.price}', best.retailer.name)
        return format_html(
            '<span style="color:#888">{} @ {} (OOS)</span>',
            f'${best.price}',
            best.retailer.name,
        )
