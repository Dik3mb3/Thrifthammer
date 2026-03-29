"""
Product catalog models for Thrifthammer.

Includes Category, Faction, Retailer, and Product models.
Prices are stored in the separate `prices` app (CurrentPrice, PriceHistory).
"""

import uuid

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
    parent_faction = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sub_factions',
        help_text='Parent faction whose units this faction can also field (e.g. Space Marines for Ultramarines).',
    )

    # ── Faction page content ────────────────────────────────────────────────
    display_name = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Override the display name shown on the faction page (e.g. "Adeptus Custodes"). '
                  'Defaults to the faction name if blank.',
    )
    hero_tagline = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Short hero strapline shown on the faction page (e.g. "The Emperor\'s Elite").',
    )
    hero_image_url = models.URLField(
        blank=True, default='',
        help_text='URL to faction hero banner image.',
    )
    synopsis = models.TextField(
        blank=True, default='',
        help_text='SEO-optimised faction description (~150-200 words) shown on the faction page.',
    )
    difficulty = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Difficulty rating shown in the Quick Stats bar (e.g. "Beginner Friendly").',
    )
    model_count_rating = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Model count shown in the Quick Stats bar (e.g. "Low (20-40 models)").',
    )
    painting_complexity = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Painting complexity shown in the Quick Stats bar (e.g. "Easy-Medium").',
    )
    playstyle = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Playstyle summary shown in the Quick Stats bar (e.g. "Melee Elite").',
    )
    price_range_display = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Price range shown in the Quick Stats bar (e.g. "£-££").',
    )
    blog_tag = models.ForeignKey(
        'blog.Tag',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='factions',
        help_text='Blog tag whose posts appear in the Related Posts section of the faction page.',
    )

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

    IMPORTANT — cache invalidation:
    products/signals.py registers a post_save handler that clears the product
    detail cache and increments the list-page generation counter whenever a
    record is saved via .save() or update_or_create().

    DO NOT use QuerySet.update() to modify Product records in bulk.
    QuerySet.update() bypasses Django signals, which means caches will NOT be
    invalidated and the site will serve stale data.  Use .save() or
    update_or_create() instead.
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
    gw_search_name = models.CharField(
        max_length=300, blank=True, default='',
        help_text=(
            'Override name used when matching against the Games Workshop spreadsheet. '
            'Set this to the EXACT GW product title when the automatic matching picks '
            'the wrong product (e.g. "Khorne Berzerkers" for World Eaters Berzerkers, '
            '"Infiltrator Squad" for Space Marine Infiltrators). '
            'Leave blank to use the standard fuzzy-matching algorithm.'
        ),
    )
    ebay_search_name = models.CharField(
        max_length=200, blank=True, default='',
        help_text=(
            'Override name used when building eBay search queries. '
            'Leave blank to use the product name. '
            'Use this when eBay sellers list a product under a different name '
            'than its display name — e.g. Deathwatch units sold as Space Marine kits.'
        ),
    )
    ebay_allow_no_box = models.BooleanField(
        default=False,
        help_text=(
            'When True, eBay listings with "no box" in the title are not filtered '
            'out for this product. Use for kits commonly sold as loose sprues without '
            'retail packaging (e.g. Bloodletters, small infantry sets).'
        ),
    )
    ebay_negative_keywords = models.CharField(
        max_length=200, blank=True, default='',
        help_text=(
            'Space-separated words to exclude from eBay searches (eBay -word syntax). '
            'Use when eBay returns a similar but wrong product. '
            'e.g. "plastic" for Super Glue excludes "Citadel Plastic Glue" listings; '
            '"mk2" for Painting Handle XL excludes standard Mk2 handle listings.'
        ),
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
            self.slug = slugify(self.name).replace('warhammer-40000', 'warhammer-40k')
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


class NewsletterSignup(models.Model):
    """Email address submitted via the homepage deal-alert opt-in."""

    email = models.EmailField(
        unique=True,
        help_text='Email address for weekly deal alert emails.',
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text='Unique token used to generate a one-click unsubscribe link.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Newsletter Signup'
        verbose_name_plural = 'Newsletter Signups'

    def __str__(self):
        return self.email

    def get_unsubscribe_url(self):
        """Return the absolute unsubscribe URL for this subscriber."""
        return f'https://thrifthammer.com/products/newsletter/unsubscribe/{self.token}/'
