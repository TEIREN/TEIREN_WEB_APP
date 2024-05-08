from django.urls import path
from . import views

urlpatterns = [
    # Integration Page
    path('<pageType>/', views.integration_view),

    ## Configuration Ajax
    path('configuration/config/<actionType>/', views.integration_config_ajax),

    ## Registration Page/Ajax
    path('<equipment>/<logType>/', views.registration_page),
    path("<equipment>/<logType>/<actionType>/", views.integration_registration_ajax),
]
