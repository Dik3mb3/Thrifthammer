from django.contrib import admin
from django.urls import path, include

from products.views import about, home, privacy_policy

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('prices/', include('prices.urls')),
    path('collection/', include('collections_app.urls')),
    path('army-calculator/', include('calculators.urls')),
    path('blog/', include('blog.urls')),
]

