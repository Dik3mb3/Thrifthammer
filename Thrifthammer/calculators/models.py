"""
Models for the Warhammer 40,000 Army Cost Calculator.

Provides UnitType (linking Warhammer units to real product prices),
SavedArmy (user-saved army lists), and PrebuiltArmy (staff-curated sample lists).

Unit categories follow the 10th Edition / New Recruit battlefield role system:
  Epic Hero, Character, Battleline, Infantry, Mounted, Vehicle, Transport, Fortification
"""

import json

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class UnitType(models.Model):
    """
    A Warhammer 40,000 unit that can be added to an army list.

    Links a real GW unit to a Product so the calculator can display
    live retail prices alongside points costs.

    The `category` field uses 10th Edition / New Recruit battlefield roles.
    """

    CATEGORY_CHOICES = [
        ('epic_hero',     'Epic Hero'),
        ('character',     'Character'),
        ('battleline',    'Battleline'),
        ('infantry',      'Infantry'),
        ('mounted',       'Mounted'),
        ('vehicle',       'Vehicle'),
        ('transport',     'Transport'),
        ('fortification', 'Fortification'),
    ]

    name = models.CharField(max_length=200, help_text='Unit name as it appears in the army rules.')
    category = models.CharField(
        max_length=30, choices=CATEGORY_CHOICES, default='infantry', db_index=True,
    )
    faction = models.ForeignKey(
        'products.Faction',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='unit_types',
        help_text='40K faction this unit belongs to (e.g. Space Marines, Necrons, T\'au).',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='unit_types',
        help_text='Linked product — used to pull live retail prices.',
    )
    points_cost = models.PositiveIntegerField(
        default=0,
        help_text='Points cost per model (or per unit if fixed-size).',
    )
    typical_quantity = models.PositiveIntegerField(
        default=1,
        help_text='Default number of models in a standard unit.',
    )
    is_active = models.BooleanField(
        default=True, db_index=True,
        help_text='Inactive units are hidden from the calculator.',
    )
    description = models.TextField(
        blank=True,
        help_text='Brief rules flavour or role description shown in the UI.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['faction__name', 'category', 'name']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['faction', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def get_cost(self):
        """
        Return the cheapest current retail price for this unit's linked product.

        Returns:
            Decimal price if a linked product has current prices, else None.
        """
        if not self.product:
            return None
        best = self.product.get_cheapest_price()
        return best.price if best else None

    def get_retail_cost(self):
        """
        Return the GW MSRP for this unit's linked product.

        Returns:
            Decimal MSRP if product is linked, else None.
        """
        if not self.product:
            return None
        return self.product.msrp


class SavedArmy(models.Model):
    """
    A user-saved army list with cost breakdowns.

    Stores the selected units as a JSON snapshot so the list remains
    stable even if product prices change after saving.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_armies',
    )
    name = models.CharField(max_length=200, help_text='A memorable name for this army list.')
    faction = models.ForeignKey(
        'products.Faction',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='saved_armies',
    )
    slug = models.SlugField(unique=True, blank=True, max_length=220)
    points_total = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Best available retail cost at time of saving.',
    )
    total_retail = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='GW MSRP total at time of saving.',
    )
    total_savings = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Amount saved vs GW MSRP.',
    )
    # JSON snapshot: list of {unit_type_id, name, quantity, points, price, msrp}
    units_data = models.JSONField(default=list)
    is_public = models.BooleanField(
        default=False,
        help_text='Public armies can be viewed by anyone with the share link.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.name} ({self.points_total}pts)"

    def save(self, *args, **kwargs):
        """Auto-generate a unique slug from the user and army name."""
        if not self.slug:
            base = slugify(f"{self.user.username}-{self.name}")
            slug = base
            counter = 1
            while SavedArmy.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the shareable URL for this army list."""
        return reverse('calculators:view_army', kwargs={'slug': self.slug})

    def calculate_totals(self):
        """
        Recalculate points, cost, and savings from the current units_data snapshot.

        Updates self.points_total, self.total_cost, self.total_retail,
        and self.total_savings in place (does not call save()).
        """
        points = 0
        cost = 0
        retail = 0
        for unit in self.units_data:
            qty = unit.get('quantity', 1)
            points += unit.get('points', 0) * qty
            cost += float(unit.get('price', 0) or 0) * qty
            retail += float(unit.get('msrp', 0) or 0) * qty
        self.points_total = points
        self.total_cost = round(cost, 2)
        self.total_retail = round(retail, 2)
        self.total_savings = round(retail - cost, 2)


class PrebuiltArmy(models.Model):
    """
    A staff-curated sample army list shown on the calculator as a starting point.

    These give newcomers ready-made examples they can customise.
    """

    name = models.CharField(max_length=200)
    faction = models.ForeignKey(
        'products.Faction',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prebuilt_armies',
    )
    description = models.TextField(blank=True)
    points_total = models.PositiveIntegerField(default=0)
    # JSON list of {unit_type_id, name, quantity}
    units_data = models.JSONField(default=list)
    display_order = models.PositiveSmallIntegerField(
        default=0,
        help_text='Lower numbers appear first.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.points_total}pts)"
