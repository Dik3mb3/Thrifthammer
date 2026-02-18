from django.contrib import admin
from django.urls import path, include

from products.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('prices/', include('prices.urls')),
    path('collection/', include('collections_app.urls')),
]
