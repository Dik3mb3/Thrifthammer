"""
Django admin configuration for the calculators app.

Provides admin interfaces for UnitType, SavedArmy, and PrebuiltArmy,
allowing staff to manage unit data and curate prebuilt army lists.
"""

from django.contrib import admin

from .models import PrebuiltArmy, SavedArmy, UnitType


@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    """
    Admin for Space Marine unit types.

    Staff can search by name, filter by category or faction,
    and link units to real products for live pricing.
    """

    list_display = ('name', 'category', 'faction', 'points_cost', 'typical_quantity', 'is_active')
    list_filter = ('category', 'faction', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    raw_id_fields = ('product', 'faction')
    list_per_page = 50
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'faction', 'is_active'),
        }),
        ('Points & Quantity', {
            'fields': ('points_cost', 'typical_quantity'),
        }),
        ('Product Link', {
            'fields': ('product',),
            'description': 'Link this unit to a Product to pull live retail prices.',
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',),
        }),
    )


@admin.register(SavedArmy)
class SavedArmyAdmin(admin.ModelAdmin):
    """
    Admin for user-saved army lists.

    Read-mostly — armies are created via the calculator UI.
    Staff can view, filter by public/private, and delete if needed.
    """

    list_display = ('name', 'user', 'faction', 'points_total', 'total_cost', 'is_public', 'created_at')
    list_filter = ('is_public', 'faction', 'created_at')
    search_fields = ('name', 'user__username')
    raw_id_fields = ('user', 'faction')
    readonly_fields = ('slug', 'total_cost', 'total_retail', 'total_savings', 'points_total', 'created_at', 'updated_at')
    list_per_page = 50


@admin.register(PrebuiltArmy)
class PrebuiltArmyAdmin(admin.ModelAdmin):
    """
    Admin for staff-curated sample army lists.

    These are shown on the calculator page as quick-start options.
    Use display_order to control the sort order in the UI.
    """

    list_display = ('name', 'faction', 'points_total', 'display_order', 'is_active')
    list_filter = ('faction', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('display_order', 'is_active')
    raw_id_fields = ('faction',)
