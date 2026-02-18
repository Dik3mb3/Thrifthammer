"""
Product catalog models for Thrifthammer.

Includes Category, Faction, Retailer, and Product models.
Prices are stored in the separate `prices` app (CurrentPrice, PriceHistory).
"""

from django.core.cache import cache
from django.db import models
from django.utils.text import slugify

# Sentinel object used by get_cheapest_price() to distinguish a cached None
# (product has no prices) from a cache miss. Using `is not None` would cause
# products with no prices to skip the cache and re-query on every request.
_CACHE_MISS = object()


class Category(models.Model):
    """
    Warhammer product category (e.g. 40K, Age of Sigmar, Paints, etc.).

    Categories are top-level groupings. Factions belong to categories.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not set. Never allow user-controlled slugs."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Faction(models.Model):
    """
    Warhammer faction within a category (e.g. Space Marines within 40K).

    Factions help users filter products by army/faction.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='factions',
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not set."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Retailer(models.Model):
    """
    A store that sells Warhammer products.

    Retailers are linked to CurrentPrice records. Only active retailers
    are shown in price comparisons.
    """

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    website = models.URLField()
    logo_url = models.URLField(
        blank=True,
        help_text='URL to retailer logo image',
    )
    affiliate_id = models.CharField(
        max_length=200, blank=True,
        help_text='Affiliate/partner ID for building tracked links',
    )
    country = models.CharField(
        max_length=10, blank=True, default='UK',
        help_text='Primary country this retailer serves (e.g. UK, US)',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not set."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    A Warhammer kit or product listed in the catalog.

    Products have a canonical GW retail price (msrp) and are linked to
    CurrentPrice records from various retailers for price comparison.

    Performance notes:
    - slug and gw_sku are indexed for fast lookups
    - Use select_related('category', 'faction') when fetching product lists
    - Use prefetch_related('current_prices__retailer') for price comparison pages
    """

    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, db_index=True)
    gw_sku = models.CharField(
        max_length=50, blank=True, db_index=True,
        help_text='Games Workshop SKU / product code',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
        db_index=True,
    )
    faction = models.ForeignKey(
        Faction,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
        db_index=True,
    )
    description = models.TextField(blank=True)
    gw_url = models.URLField(blank=True, help_text='Official GW product page')
    image_url = models.URLField(blank=True)
    msrp = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Games Workshop recommended retail price',
    )
    # Allows soft-deletion: inactive products are hidden from catalog
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            # Composite index for common filter: active products in a category
            models.Index(fields=['is_active', 'category']),
            # Composite index for active products in a faction
            models.Index(fields=['is_active', 'faction']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not set.
        Invalidate cached price data when product is saved.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        # Bust any cached price data for this product
        cache.delete(f'cheapest_price_{self.pk}')

    @property
    def best_price(self):
        """
        Return the lowest CurrentPrice object across all retailers.

        Kept as a property alias for backwards compatibility with templates.
        """
        return self.get_cheapest_price()

    def get_cheapest_price(self):
        """
        Return the cheapest in-stock CurrentPrice, cached for 1 hour.

        Falls back to cheapest out-of-stock price if nothing is in stock.
        Results are cached to avoid repeated DB hits on detail pages.

        Cache sentinel: we use a dedicated _MISSING sentinel object rather
        than checking `if cached is not None`, because a product with no
        prices would cache None and then always re-query on every request.
        """
        cache_key = f'cheapest_price_{self.pk}'
        cached = cache.get(cache_key, _CACHE_MISS)
        if cached is not _CACHE_MISS:
            return cached

        # Prefer in-stock, fall back to cheapest overall
        from prices.models import CurrentPrice  # avoid circular import at module level
        result = (
            CurrentPrice.objects
            .filter(product=self, in_stock=True)
            .select_related('retailer')
            .order_by('price')
            .first()
        ) or (
            CurrentPrice.objects
            .filter(product=self)
            .select_related('retailer')
            .order_by('price')
            .first()
        )

        # Cache for 1 hour — None is a valid result (no prices yet)
        cache.set(cache_key, result, timeout=3600)
        return result

    def get_best_deal(self):
        """
        Return the Retailer offering the lowest current price.

        Returns None if no prices are available.
        """
        cheapest = self.get_cheapest_price()
        return cheapest.retailer if cheapest else None

    def get_savings_vs_retail(self):
        """
        Calculate the monetary saving vs GW retail price (msrp).

        Returns a dict with 'amount' and 'percent', or None if msrp/price
        data is not available.
        """
        if not self.msrp:
            return None
        cheapest = self.get_cheapest_price()
        if not cheapest:
            return None

        amount = self.msrp - cheapest.price
        percent = round((amount / self.msrp) * 100, 1)
        return {
            'amount': amount,
            'percent': percent,
            'retailer': cheapest.retailer,
        }
