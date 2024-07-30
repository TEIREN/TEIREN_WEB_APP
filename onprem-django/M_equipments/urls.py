# ~/integration/
from django.urls import path
from . import views

urlpatterns = [
    ## Configuration Ajax
    path('configuration/config/<actionType>/', views.integration_config_ajax),
    
    ## Registration Page/Ajax
    path('<equipment>/<logType>/', views.registration_page),
    path("<equipment>/<logType>/<actionType>/", views.integration_registration_ajax),
    

    
    # Integration Page
    path('refresh/', views.refresh_integration_section, name='refresh-section'),
    path('registration/', views.registration_view),
    path('configuration/', views.integration_view),
]