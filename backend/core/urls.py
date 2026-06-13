from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse, HttpResponse
import os


def api_root(request):
    return JsonResponse({"status": "success", "message": "Indomitable Backend is running!"})


def download_apk(request):
    apk_path = os.path.join(settings.BASE_DIR, 'apk', 'Indomitable.apk')
    if os.path.exists(apk_path):
        with open(apk_path, 'rb') as f:
            response = HttpResponse(
                f.read(), content_type='application/vnd.android.package-archive')
            response['Content-Disposition'] = 'attachment; filename="Indomitable.apk"'
            return response
    else:
        return HttpResponse("APK file not found", status=404)


urlpatterns = [
    path('', api_root),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/download-apk/', download_apk, name='download_apk'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
