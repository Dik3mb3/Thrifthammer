"""
Django admin configuration for the calculators app.

Provides admin interfaces for UnitType, SavedArmy, and PrebuiltArmy,
allowing staff to manage unit data and curate prebuilt army lists.

UnitType categories follow 10th Edition / New Recruit battlefield roles:
  Epic Hero, Character, Battleline, Infantry, Mounted, Vehicle, Transport, Fortification

To add units for a faction:
  1. Find the Product in the product admin (use SKU search)
  2. Create a UnitType: link the product, set faction to the 40K faction,
     choose the correct battlefield role, set points and typical quantity
  3. Leave is_active=True — the unit appears in the calculator immediately
"""

from django.contrib import admin

from .models import PrebuiltArmy, SavedArmy, UnitType


@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    """
    Admin for 40K unit types (all factions).

    Use the Faction filter to view units for a specific army.
    The Category filter uses 10th Edition battlefield roles.
    Staff can link units to Products to pull live retail prices.
    """

    list_display = ('name', 'get_category_display', 'faction', 'points_cost', 'typical_quantity', 'is_active')
    list_filter = ('category', 'faction', 'is_active')
    search_fields = ('name', 'description', 'product__name', 'product__gw_sku')
    list_editable = ('is_active',)
    raw_id_fields = ('product', 'faction')
    list_per_page = 50
    ordering = ('faction__name', 'category', 'name')
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'faction', 'is_active'),
            'description': (
                'Category = 10th Ed battlefield role. '
                'Faction must be a Warhammer 40,000 faction.'
            ),
        }),
        ('Points & Quantity', {
            'fields': ('points_cost', 'typical_quantity'),
            'description': 'points_cost = per-model points. typical_quantity = standard unit size.',
        }),
        ('Product Link', {
            'fields': ('product',),
            'description': (
                'Link this unit to a Product SKU to show live retail prices. '
                'Do not link multi-unit box sets here — only single-kit entries.'
            ),
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
