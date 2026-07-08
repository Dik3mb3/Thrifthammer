"""
Views for the Warhammer 40,000 Army Cost Calculator.

Provides:
- ArmyCalculatorView: main calculator page with faction filter + live price lookups
- SaveArmyView: AJAX endpoint to persist a named army list
- ViewSavedArmyView: public/private shareable army detail page
- UserArmiesListView: dashboard listing the user's saved armies
- CalculateArmyCostView: AJAX API that returns real-time price totals
"""

import json
import decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from accounts.models import WatchlistItem
from collections_app.models import CollectionItem
from prices.models import CurrentPrice
from products.models import Faction

from .models import PrebuiltArmy, SavedArmy, UnitType

# 10th Edition / New Recruit battlefield role display order
CATEGORY_ORDER = [
    'epic_hero',
    'character',
    'battleline',
    'infantry',
    'mounted',
    'vehicle',
    'transport',
    'fortification',
    'combo_box',
]


class ArmyCalculatorView(TemplateView):
    """
    Warhammer 40,000 Army Cost Calculator page.

    Supports filtering by faction via the ?faction=<slug> query parameter.
    When no faction is selected, all active units across all factions are shown.
    Units are grouped by 10th Edition battlefield role (Epic Hero → Fortification).
    """

    template_name = 'calculators/army_calculator.html'

    def get(self, request, *args, **kwargs):
        """Redirect to canonical faction URLs; default bare /army-calculator/ to Space Marines.

        1. Legacy ?faction=<slug> GET-param URLs → permanent 301 to clean path.
        2. Bare /army-calculator/ (no faction kwarg) → 302 to /army-calculator/space-marines/
           so Space Marines is always the default landing experience.
        """
        faction_slug = request.GET.get('faction', '').strip()
        if faction_slug and not self.kwargs.get('faction'):
            return redirect(f'/army-calculator/{faction_slug}/', permanent=True)
        # Default: send bare /army-calculator/ straight to Space Marines
        if not self.kwargs.get('faction') and not faction_slug:
            return redirect('/army-calculator/space-marines/')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Build context with faction selector, units grouped by role, and prebuilt armies."""
        context = super().get_context_data(**kwargs)

        # Determine selected faction — URL path kwargs take priority over query param
        # (e.g. /army-calculator/blood-angels/ sets kwargs['faction'] = 'blood-angels')
        faction_slug = (self.kwargs.get('faction') or self.request.GET.get('faction', '')).strip()
        selected_faction = None
        if faction_slug:
            selected_faction = Faction.objects.filter(
                slug=faction_slug,
                category__slug='warhammer-40000',
            ).first()

        # All 40K factions that have at least one active unit
        available_factions = list(
            Faction.objects
            .filter(
                category__slug='warhammer-40000',
                unit_types__is_active=True,
            )
            .distinct()
            .order_by('name')
        )

        # Fetch units — only when a faction is selected.
        # Include units from the selected faction AND its parent faction (if any),
        # so sub-factions like Ultramarines automatically show Space Marines units.
        if selected_faction:
            faction_filter = Q(faction=selected_faction)
            if selected_faction.parent_faction_id:
                faction_filter |= Q(faction=selected_faction.parent_faction)
            unit_qs = (
                UnitType.objects
                .filter(is_active=True)
                .filter(faction_filter)
                .filter(Q(product__isnull=True) | Q(product__is_active=True))
                .select_related('product', 'faction')
                .prefetch_related(
                    'product__current_prices__retailer',
                    'weapon_profiles',
                    'abilities',
                )
                .order_by('category', 'name')
            )
            raw_units = list(unit_qs)

            # Deduplicate by product_id when parent faction units are included.
            # If both a sub-faction unit and a parent-faction unit reference the
            # same product, prefer the sub-faction unit (more specific category/
            # naming). This prevents e.g. "Space Marine Aggressors" and
            # "Aggressor Squad" both appearing when Ultramarines is selected.
            if selected_faction.parent_faction_id:
                seen_product_ids: set = set()
                units = []
                # First pass: add all sub-faction units, recording their product_ids
                for u in raw_units:
                    if u.faction_id == selected_faction.pk:
                        units.append(u)
                        if u.product_id is not None:
                            seen_product_ids.add(u.product_id)
                # Second pass: add parent-faction units only if their product
                # hasn't already been claimed by a sub-faction unit
                for u in raw_units:
                    if u.faction_id != selected_faction.pk:
                        if u.product_id is None or u.product_id not in seen_product_ids:
                            units.append(u)
                            if u.product_id is not None:
                                seen_product_ids.add(u.product_id)
                # Re-sort after manual assembly (mirrors DB order_by)
                units.sort(key=lambda u: (u.category, u.name))
            else:
                units = raw_units
        else:
            units = []

        # Group units by their 10th Edition battlefield role
        categories: dict = {}
        for unit in units:
            cat_key = unit.category
            if cat_key not in categories:
                categories[cat_key] = {
                    'label': unit.get_category_display(),
                    'units': [],
                }
            categories[cat_key]['units'].append(unit)

        # Preserve 10th Edition role ordering
        ordered_categories = [
            (key, categories[key])
            for key in CATEGORY_ORDER
            if key in categories
        ]

        # Prebuilt armies — filter to selected faction if applicable
        prebuilt_qs = (
            PrebuiltArmy.objects
            .filter(is_active=True)
            .select_related('faction')
            .order_by('display_order', 'name')
        )
        if selected_faction:
            prebuilt_qs = prebuilt_qs.filter(faction=selected_faction)
        prebuilt_armies = list(prebuilt_qs)

        # User's saved armies for the load-list panel
        saved_armies = []
        if self.request.user.is_authenticated:
            saved_armies = list(
                SavedArmy.objects
                .filter(user=self.request.user)
                .order_by('-created_at')[:10]
            )

        # Timestamp of the most recently updated unit — auto-reflects every seed run
        points_last_updated = UnitType.objects.aggregate(
            latest=Max('updated_at')
        )['latest']

        context.update({
            'ordered_categories': ordered_categories,
            'prebuilt_armies': prebuilt_armies,
            'prebuilt_armies_list': [
                {'name': a.name, 'points': a.points_total, 'units': a.units_data}
                for a in prebuilt_armies
            ],
            'saved_armies': saved_armies,
            'available_factions': available_factions,
            'selected_faction': selected_faction,
            'points_last_updated': points_last_updated,
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
            return qs.filter(Q(is_public=True) | Q(user=self.request.user))
        return qs.filter(is_public=True)

    def get_context_data(self, **kwargs):
        """
        Enrich each unit in units_data with live top-3 retailer prices,
        watchlist/collection membership, and the product slug so the
        template can render expandable price rows and action buttons.
        """
        context = super().get_context_data(**kwargs)
        army = self.object

        # Gather all unit_type_ids referenced in this army's snapshot
        unit_ids = [u['unit_type_id'] for u in (army.units_data or [])]
        unit_map = {
            ut.pk: ut
            for ut in UnitType.objects.filter(pk__in=unit_ids).select_related('product')
        }

        # Collect product IDs that have a linked Product
        product_ids = [ut.product_id for ut in unit_map.values() if ut.product_id]

        # Fetch all in-stock US prices for those products, ordered cheapest first
        all_prices = (
            CurrentPrice.objects
            .filter(product_id__in=product_ids, in_stock=True, not_available=False)
            .exclude(retailer__is_uk=True)
            .select_related('retailer')
            .order_by('product_id', 'price')
        )
        # Keep at most 3 prices per product
        prices_by_product: dict = {}
        for cp in all_prices:
            lst = prices_by_product.setdefault(cp.product_id, [])
            if len(lst) < 3:
                lst.append(cp)


        # Watchlist / collection membership for authenticated users
        watchlist_pids: set = set()
        collection_pids: set = set()
        if self.request.user.is_authenticated:
            watchlist_pids = set(
                WatchlistItem.objects
                .filter(user=self.request.user, product_id__in=product_ids)
                .values_list('product_id', flat=True)
            )
            collection_pids = set(
                CollectionItem.objects
                .filter(user=self.request.user, product_id__in=product_ids)
                .values_list('product_id', flat=True)
            )

        # Build enriched unit list
        unit_details = []
        for entry in (army.units_data or []):
            ut = unit_map.get(entry['unit_type_id'])
            product = ut.product if ut else None
            pid = product.pk if product else None
            unit_details.append({
                **entry,
                'product_slug': product.slug if product else None,
                'top_prices': prices_by_product.get(pid, []),
                'on_watchlist': pid in watchlist_pids,
                'in_collection': pid in collection_pids,
                'gw_msrp': product.msrp if product else None,
            })

        # Recalculate totals using live product.msrp so the stat cards and
        # MSRP column are never stale from an old snapshot.  The snapshot's
        # 'msrp' value is overridden in-place so the template column is correct.
        live_retail = decimal.Decimal('0')
        live_cost = decimal.Decimal('0')
        for ud in unit_details:
            qty = ud.get('quantity', 1)
            # Prefer live product.msrp; fall back to snapshot value if product gone
            live_msrp = ud.get('gw_msrp') or decimal.Decimal(str(ud.get('msrp') or 0))
            live_price = decimal.Decimal(str(ud.get('price') or 0))
            live_retail += live_msrp * qty
            live_cost += live_price * qty
            # Override so {{ unit.msrp }} in the template shows the live value
            ud['msrp'] = live_msrp
            # Pre-calculated line totals for the table (price × qty, msrp × qty)
            ud['price_total'] = (live_price * qty).quantize(decimal.Decimal('0.01')) if live_price else None
            ud['msrp_total'] = (live_msrp * qty).quantize(decimal.Decimal('0.01')) if live_msrp else None

        live_savings = live_retail - live_cost
        context['unit_details'] = unit_details
        context['live_total_retail'] = live_retail.quantize(decimal.Decimal('0.01'))
        context['live_total_savings'] = live_savings.quantize(decimal.Decimal('0.01'))
        return context


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


class DeleteArmyView(LoginRequiredMixin, View):
    """
    POST-only view to delete a saved army list.

    Only the army's owner may delete it. Redirects to My Armies on success.
    """

    def post(self, request, slug):
        """Delete the army if it belongs to the current user."""
        army = get_object_or_404(SavedArmy, slug=slug, user=request.user)
        army_name = army.name
        army.delete()
        messages.success(request, f'"{army_name}" has been deleted.')
        return redirect('calculators:my_armies')
