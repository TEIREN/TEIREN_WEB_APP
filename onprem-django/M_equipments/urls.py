# ~/integration/
from django.urls import path
from .views import IntegrationView
from . import views_old

urlpatterns = [
    path('', IntegrationView.as_view(), name="integration"),
    path('<system>/<log_type>/', IntegrationView.as_view(), name="register_page"),
    path('<system>/<log_type>/<action_type>/', IntegrationView.as_view(), name="registration_ajax"),
]