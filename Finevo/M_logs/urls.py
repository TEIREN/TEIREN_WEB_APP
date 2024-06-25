from django.urls import path
from . import views
from .src import elasticsearch_log

urlpatterns = [
    # Log Management
    path('<resourceType>/<logType>/', views.log_view),
    path("<resourceType>/modal/<logType>/", views.log_modal),
    path('<resource_type>/<system>/ruleset/<ruleset_name>/', elasticsearch_log.logs_by_ruleset, name='logs_by_ruleset'),  # logs_by_ruleset
    
]
