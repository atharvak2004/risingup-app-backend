from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("rising-up-admin/", admin.site.urls),

    # JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # App-specific APIs
    path("api/core/", include("core.api_urls")),
    path("api/learning/", include("learning.api_urls")),
    path("api/accounts/", include("accounts.api_urls")),

    # ERP APIs
    path("api/erp/", include("erp.urls")),
    
    # Admin Panel APIs
    path("api/admin/", include("adminpanel.urls")),
]

# SERVE STATIC + MEDIA IN DEVELOPMENT
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
