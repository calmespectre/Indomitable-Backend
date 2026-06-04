from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def api_root(request):
    return JsonResponse({"status": "success", "message": "Indomitable Backend is running!"})


urlpatterns = [
    path('', api_root),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    # path('api/orders/', include('orders.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
