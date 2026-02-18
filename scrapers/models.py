from django.db import models


class ScrapeJob(models.Model):
    """Tracks individual scrape runs."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    retailer = models.ForeignKey(
        'products.Retailer', on_delete=models.CASCADE, related_name='scrape_jobs',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    products_found = models.IntegerField(default=0)
    prices_updated = models.IntegerField(default=0)
    errors = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.retailer.name} scrape — {self.status} ({self.created_at:%Y-%m-%d %H:%M})"
