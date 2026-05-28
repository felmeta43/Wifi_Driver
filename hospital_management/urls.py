from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('doctors/', include('doctors.urls')),
    path('appointments/', include('appointments.urls')),
    path('billing/', include('billing.urls')),
    path('pharmacy/', include('pharmacy.urls')),
    path('laboratory/', include('laboratory.urls')),
    path('services/', include('services.urls')),
    path('clinical/', include('clinical.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
