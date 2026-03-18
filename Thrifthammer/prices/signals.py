"""
Price history signal for the prices app.

Automatically records a PriceHistory snapshot whenever a CurrentPrice row
is created or updated with a meaningful change (price moves or stock status
flips).  This powers future price-trend charts without requiring any changes
to the import commands themselves — every code path that writes a
CurrentPrice (Octoparse imports, batch-fix waves, eBay scraper, etc.) is
captured automatically.

Logic:
  - On CREATE: record initial history if price is not None.
  - On UPDATE: record history if price OR in_stock changed.
  - Skips recording when price is None (not_available products have no
    meaningful price to chart).
  - Skips recording when nothing changed (idempotent re-runs stay clean).
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import CurrentPrice, PriceHistory


@receiver(pre_save, sender=CurrentPrice)
def track_price_history(sender, instance, **kwargs):
    """
    Record a PriceHistory snapshot on meaningful CurrentPrice changes.

    Fires before every CurrentPrice.save(), including those triggered by
    update_or_create, save(update_fields=[...]), and direct saves.
    """
    # Nothing to chart if the price is unknown / product is not available.
    if instance.price is None:
        return

    if instance.pk:
        # ── UPDATE path: compare new values against what is in the DB ─────────
        try:
            old = CurrentPrice.objects.get(pk=instance.pk)
        except CurrentPrice.DoesNotExist:
            # Race condition edge-case — treat as create.
            PriceHistory.objects.create(
                product=instance.product,
                retailer=instance.retailer,
                price=instance.price,
                in_stock=instance.in_stock,
            )
            return

        price_changed = old.price != instance.price
        stock_changed = old.in_stock != instance.in_stock

        if price_changed or stock_changed:
            PriceHistory.objects.create(
                product=instance.product,
                retailer=instance.retailer,
                price=instance.price,
                in_stock=instance.in_stock,
            )
    else:
        # ── CREATE path: always record initial snapshot ────────────────────────
        PriceHistory.objects.create(
            product=instance.product,
            retailer=instance.retailer,
            price=instance.price,
            in_stock=instance.in_stock,
        )
