from django.db import models


class Category(models.Model):
    """Warhammer product category (e.g. 40K, Age of Sigmar, Paints, etc.)."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Faction(models.Model):
    """Warhammer faction (e.g. Space Marines, Orks, Stormcast Eternals)."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='factions',
    )

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"


class Retailer(models.Model):
    """A store that sells Warhammer products."""
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    website = models.URLField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """A Warhammer kit / product."""
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    gw_sku = models.CharField(
        max_length=50, blank=True,
        help_text='Games Workshop SKU / product code',
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
    )
    faction = models.ForeignKey(
        Faction, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
    )
    description = models.TextField(blank=True)
    gw_url = models.URLField(blank=True, help_text='Official GW product page')
    image_url = models.URLField(blank=True)
    msrp = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text='Games Workshop recommended retail price (USD)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def best_price(self):
        """Return the lowest current price across all retailers."""
        from prices.models import CurrentPrice
        best = CurrentPrice.objects.filter(product=self).order_by('price').first()
        return best
