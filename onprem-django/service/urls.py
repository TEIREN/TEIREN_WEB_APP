"""
URL configuration for service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500
from django.views.static import serve

handler404 = 'common.views.error_page'
handler500 = 'common.views.error_page'

API_VERSION = 'v1'
AJAX_VERSION = 'v1'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('', include('common.urls')),
    path('auth/', include('_auth.urls')),
    path('integration/', include('M_equipments.urls')),
    path('logs/', include('M_logs.urls')),
    path('threat/', include('M_threatD.urls')),
    path('configurations/', include('configurations.urls')),
    path(f'api/{API_VERSION}/metrics/', include('api.metrics.urls')),
    path('compliance/', include('compliance.urls')),
    path('test/', include('testing.urls')),
    path('monitoring/', include('monitoring.urls')),
    # path("__debug__/", include("debug_toolbar.urls")),
    # path(f'compliance/{COMPLIANCE_VERSION}/', include(f'compliance.{COMPLIANCE_VERSION}.urls')),
    # path('', include(f'ajax_handler.{AJAX_VERSION}.urls')),
    # path('', include('TeirenSIEM.urls')),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)