from django.urls import include, path
from configurations.views import AccountConfigView

# path:
#   ./configurations/
urlpatterns = [
    path('account/', AccountConfigView.as_view(), name='account'),
    path('account/<config_action>/', AccountConfigView.as_view(), name='account_config'),
    # path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # path('test/<args>/', TestView.as_view(), name='test'),
]
