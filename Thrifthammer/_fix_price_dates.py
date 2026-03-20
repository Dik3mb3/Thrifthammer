"""
One-off script: stamp all CurrentPrice rows with last_seen = 2026-03-17
and clear the context-processor cache key so the footer updates immediately.

Run via: railway run python _fix_price_dates.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thrifthammer.settings')
django.setup()

from datetime import datetime, timezone
from prices.models import CurrentPrice
from django.core.cache import cache

target = datetime(2026, 3, 17, 12, 0, 0, tzinfo=timezone.utc)
updated = CurrentPrice.objects.all().update(last_seen=target)
cache.delete('site_last_price_update')

print(f'Done — updated {updated} CurrentPrice rows to {target.strftime("%d %b %Y")}')
print('Cache key "site_last_price_update" cleared.')
