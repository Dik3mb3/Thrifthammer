from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .models import ScrapeJob


@staff_member_required
def scrape_dashboard(request):
    """Admin-only dashboard showing recent scrape jobs."""
    jobs = ScrapeJob.objects.select_related('retailer')[:50]
    return render(request, 'scrapers/dashboard.html', {'jobs': jobs})
