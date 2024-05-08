from django.urls import path
from . import views

urlpatterns = [
    path('receive/', views.receive, name='receive'),
    path('agent/<str:uuid>/', views.get_metrics_by_uuid, name='get_metrics_by_uuid'),
    path('get_metric_data/<str:instance_id>/', views.get_metric_data, name='get_metric_data'),
    path('get_all_metrics/<str:uuid>/', views.get_all_metrics, name='get_all_metrics'),
    # path('get_metrics_by_uuid/<str:uuid>/', views.get_metrics_by_uuid, name='get_metrics_by_uuid'),
]