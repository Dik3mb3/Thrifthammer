"""
Django admin configuration for the products app.

Provides rich admin interfaces for Category, Faction, Retailer, and Product
models, with custom columns and bulk-management helpers.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Faction, Product, Retailer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for product categories."""

    list_display = ('name', 'slug', 'faction_count', 'product_count', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Factions')
    def faction_count(self, obj):
        """Show number of factions in this category."""
        return obj.factions.count()

    @admin.display(description='Products')
    def product_count(self, obj):
        """Show number of products in this category."""
        return obj.products.count()


@admin.register(Faction)
class FactionAdmin(admin.ModelAdmin):
    """Admin for Warhammer factions."""

    list_display = ('name', 'category', 'slug', 'product_count')
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    @admin.display(description='Products')
    def product_count(self, obj):
        """Show number of products for this faction."""
        return obj.products.count()


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
    """Admin for retailers."""

    list_display = ('name', 'country', 'website_link', 'is_active', 'price_count')
    list_filter = ('is_active', 'country')
    search_fields = ('name', 'website')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('price_count',)

    @admin.display(description='Website')
    def website_link(self, obj):
        """Render clickable website link in the list view."""
        return format_html('<a href="{}" target="_blank">{}</a>', obj.website, obj.website)

    @admin.display(description='Prices tracked')
    def price_count(self, obj):
        """Show how many current prices this retailer has."""
        return obj.current_prices.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin for the product catalog.

    Includes a custom cheapest_current_price column so staff can quickly
    see where each product is cheapest without opening individual records.
    """

    list_display = (
        'name', 'category', 'faction', 'gw_sku',
        'msrp', 'cheapest_current_price', 'is_active', 'updated_at',
    )
    list_filter = ('is_active', 'category', 'faction', 'created_at')
    search_fields = ('name', 'gw_sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    # Use dropdowns (not raw_id) for category/faction — small enough tables
    autocomplete_fields = []
    readonly_fields = ('created_at', 'updated_at', 'cheapest_current_price')
    list_editable = ('is_active',)
    list_per_page = 50

    fieldsets = (
        ('Product Info', {
            'fields': ('name', 'slug', 'gw_sku', 'category', 'faction', 'is_active'),
        }),
        ('Content', {
            'fields': ('description', 'image_url', 'gw_url'),
        }),
        ('Pricing', {
            'fields': ('msrp', 'cheapest_current_price'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Best price')
    def cheapest_current_price(self, obj):
        """
        Display the lowest current price with retailer name.

        Shown in both list view and the detail fieldset so staff can
        quickly assess how competitive a product's pricing is.
        """
        from prices.models import CurrentPrice  # avoid circular import at module level
        best = (
            CurrentPrice.objects
            .filter(product=obj, in_stock=True)
            .select_related('retailer')
            .order_by('price')
            .first()
        )
        if best:
            return format_html(
                '<strong>{}</strong> @ {}',
                f'${best.price}',
                best.retailer.name,
            )
        # Fall back to out-of-stock prices if no in-stock option exists
        best_oos = (
            CurrentPrice.objects
            .filter(product=obj)
            .select_related('retailer')
            .order_by('price')
            .first()
        )
        if best_oos:
            return format_html(
                '<span style="color:#888">{} @ {} (OOS)</span>',
                f'${best_oos.price}',
                best_oos.retailer.name,
            )
        return '—'
