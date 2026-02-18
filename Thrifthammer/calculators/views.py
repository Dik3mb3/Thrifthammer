"""
Views for the Space Marine Army Cost Calculator.

Provides:
- ArmyCalculatorView: main calculator page with live price lookups
- SaveArmyView: AJAX endpoint to persist a named army list
- ViewSavedArmyView: public/private shareable army detail page
- UserArmiesListView: dashboard listing the user's saved armies
- CalculateArmyCostView: AJAX API that returns real-time price totals
"""

import json
import decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView, TemplateView

from products.models import Faction

from .models import PrebuiltArmy, SavedArmy, UnitType


class ArmyCalculatorView(TemplateView):
    """
    Main Space Marine Army Cost Calculator page.

    Loads all active Space Marine unit types grouped by battlefield role,
    along with any prebuilt sample armies for quick-start selection.
    """

    template_name = 'calculators/army_calculator.html'

    def get_context_data(self, **kwargs):
        """Build the context with units grouped by category and prebuilt armies."""
        context = super().get_context_data(**kwargs)

        # Fetch all active Space Marine units with related product/prices
        units = (
            UnitType.objects
            .filter(is_active=True)
            .select_related('product', 'faction')
            .prefetch_related('product__current_prices__retailer')
            .order_by('category', 'name')
        )

        # Group units by their display category
        categories = {}
        category_order = [
            'hq', 'troops', 'elites', 'fast_attack',
            'heavy_support', 'dedicated_transport', 'lord_of_war',
        ]
        for unit in units:
            cat_key = unit.category
            if cat_key not in categories:
                categories[cat_key] = {
                    'label': unit.get_category_display(),
                    'units': [],
                }
            categories[cat_key]['units'].append(unit)

        # Preserve logical category ordering
        ordered_categories = [
            (key, categories[key])
            for key in category_order
            if key in categories
        ]

        # Prebuilt armies for the quick-start panel
        prebuilt_armies = (
            PrebuiltArmy.objects
            .filter(is_active=True)
            .select_related('faction')
            .order_by('display_order', 'name')
        )

        # User's saved armies (if logged in) for the load-list panel
        saved_armies = []
        if self.request.user.is_authenticated:
            saved_armies = (
                SavedArmy.objects
                .filter(user=self.request.user)
                .order_by('-created_at')[:10]
            )

        context.update({
            'ordered_categories': ordered_categories,
            'prebuilt_armies': prebuilt_armies,
            'saved_armies': saved_armies,
        })
        return context


class CalculateArmyCostView(View):
    """
    AJAX API endpoint: POST a list of unit IDs and quantities, get back price totals.

    Request body (JSON):
        {"units": [{"id": 1, "quantity": 2}, ...]}

    Response (JSON):
        {
            "units": [...],          # unit details with prices
            "points_total": 500,
            "total_cost": "120.00",
            "total_retail": "145.00",
            "total_savings": "25.00"
        }
    """

    def post(self, request, *args, **kwargs):
        """Calculate totals for the given unit list and return JSON."""
        try:
            body = json.loads(request.body)
            requested_units = body.get('units', [])
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

        if not isinstance(requested_units, list):
            return JsonResponse({'error': 'units must be a list.'}, status=400)

        # Validate and clamp quantities
        unit_map = {}
        for entry in requested_units:
            try:
                uid = int(entry['id'])
                qty = max(1, min(20, int(entry.get('quantity', 1))))
                unit_map[uid] = qty
            except (KeyError, ValueError, TypeError):
                continue

        if not unit_map:
            return JsonResponse({'points_total': 0, 'total_cost': '0.00',
                                 'total_retail': '0.00', 'total_savings': '0.00',
                                 'units': []})

        units = (
            UnitType.objects
            .filter(pk__in=unit_map.keys(), is_active=True)
            .select_related('product')
            .prefetch_related('product__current_prices__retailer')
        )

        points_total = 0
        total_cost = decimal.Decimal('0')
        total_retail = decimal.Decimal('0')
        result_units = []

        for unit in units:
            qty = unit_map[unit.pk]
            unit_price = unit.get_cost() or decimal.Decimal('0')
            unit_msrp = unit.get_retail_cost() or decimal.Decimal('0')
            unit_points = unit.points_cost * unit.typical_quantity

            points_total += unit_points * qty
            total_cost += unit_price * qty
            total_retail += unit_msrp * qty

            result_units.append({
                'id': unit.pk,
                'name': unit.name,
                'category': unit.get_category_display(),
                'points': unit_points,
                'quantity': qty,
                'price': str(unit_price),
                'msrp': str(unit_msrp),
            })

        total_savings = total_retail - total_cost

        return JsonResponse({
            'units': result_units,
            'points_total': points_total,
            'total_cost': str(total_cost.quantize(decimal.Decimal('0.01'))),
            'total_retail': str(total_retail.quantize(decimal.Decimal('0.01'))),
            'total_savings': str(total_savings.quantize(decimal.Decimal('0.01'))),
        })


class SaveArmyView(LoginRequiredMixin, View):
    """
    AJAX endpoint to save a named army list for the logged-in user.

    Request body (JSON):
        {
            "name": "My 2000pt List",
            "units": [{"id": 1, "quantity": 2}, ...],
            "is_public": false
        }

    Response (JSON):
        {"success": true, "slug": "username-my-2000pt-list", "url": "/army-calculator/share/..."}
    """

    def post(self, request, *args, **kwargs):
        """Validate input and persist the army list."""
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

        name = str(body.get('name', '')).strip()[:200]
        if not name:
            return JsonResponse({'error': 'Army name is required.'}, status=400)

        requested_units = body.get('units', [])
        is_public = bool(body.get('is_public', False))

        # Build the units snapshot
        unit_map = {}
        for entry in requested_units:
            try:
                uid = int(entry['id'])
                qty = max(1, min(20, int(entry.get('quantity', 1))))
                unit_map[uid] = qty
            except (KeyError, ValueError, TypeError):
                continue

        db_units = (
            UnitType.objects
            .filter(pk__in=unit_map.keys(), is_active=True)
            .select_related('product')
        )

        units_data = []
        for unit in db_units:
            qty = unit_map[unit.pk]
            price = unit.get_cost()
            msrp = unit.get_retail_cost()
            units_data.append({
                'unit_type_id': unit.pk,
                'name': unit.name,
                'category': unit.category,
                'quantity': qty,
                'points': unit.points_cost * unit.typical_quantity,
                'price': str(price) if price is not None else None,
                'msrp': str(msrp) if msrp is not None else None,
            })

        army = SavedArmy(
            user=request.user,
            name=name,
            units_data=units_data,
            is_public=is_public,
        )
        army.calculate_totals()
        army.save()

        return JsonResponse({
            'success': True,
            'slug': army.slug,
            'url': army.get_absolute_url(),
        })


class ViewSavedArmyView(DetailView):
    """
    Public/private shareable view of a saved army list.

    Private armies are only visible to their owner; public armies
    can be viewed by anyone with the share link.
    """

    model = SavedArmy
    template_name = 'calculators/view_army.html'
    context_object_name = 'army'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """
        Return armies visible to the current user.

        Public armies are visible to all; private armies only to their owner.
        """
        qs = SavedArmy.objects.select_related('user', 'faction')
        if self.request.user.is_authenticated:
            # Show own armies (any privacy) + all public armies
            from django.db.models import Q
            return qs.filter(Q(is_public=True) | Q(user=self.request.user))
        return qs.filter(is_public=True)


class UserArmiesListView(LoginRequiredMixin, ListView):
    """
    Dashboard page listing all army lists saved by the logged-in user.

    Ordered newest-first; shows cost, points, and a share link for each.
    """

    model = SavedArmy
    template_name = 'calculators/my_armies.html'
    context_object_name = 'armies'
    paginate_by = 20

    def get_queryset(self):
        """Return only the current user's saved armies."""
        return (
            SavedArmy.objects
            .filter(user=self.request.user)
            .select_related('faction')
            .order_by('-created_at')
        )
