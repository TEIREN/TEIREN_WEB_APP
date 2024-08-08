from django.urls import path
from .views import LogManagementView
from .src import elasticsearch_log
from . import views

urlpatterns = [
    # Log Management
    # path('<resourceType>/<logType>/', views.log_view),
    # path('<resourceType>/<logType>/filter/', views.log_view),
    # path("<resourceType>/modal/<logType>/", views_old.log_modal),
    # path('<resource_type>/<system>/property/save/', elasticsearch_log.log_property_setting),
    
    path('<resource_type>/<system>/', LogManagementView.as_view(), name="log_management_page"),
    path('<resource_type>/<system>/ruleset/<ruleset_name>/', elasticsearch_log.logs_by_ruleset, name='logs_by_ruleset'),  # logs_by_ruleset
    # path('<resource_type>/<system>/ruleset/<ruleset_name>/', LogManagementView.as_view(), name='logs_by_ruleset'),  # logs_by_ruleset
    path('<resource_type>/<system>/property/save/', LogManagementView.as_view(), name="log_property_save"),
    
]
