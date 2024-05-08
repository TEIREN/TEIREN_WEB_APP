from django.urls import include, path
from configurations import views
from .views import account_view, dashboard_view
from .test_views import AccountIndexView, DashboardView, TestView, AccountConfigView

# path:
#   ./configurations/
urlpatterns = [
    path('account/', AccountIndexView.as_view(), name='account'),
    path('account/<config_type>', AccountConfigView.as_view(), name='account_config'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('test/<args>/', TestView.as_view(), name='test'),
]
