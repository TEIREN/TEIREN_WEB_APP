from django.urls import path
from . import views

urlpatterns = [
    # Log Management
    path('<resourceType>/<logType>/', views.log_view),
    path("<resourceType>/modal/<logType>/", views.log_modal)
]
