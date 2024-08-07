from django.urls import path
from .views import RuleView

urlpatterns = [
    # Risk Management
    # ## alert
    # path('notifications/<threat>/', views.notification_view),
    # # ## rules
    path('rules/<resource_type>/<system>/', RuleView.as_view(), name="rule_page"),
    path('rules/<resource_type>/<system>/elasticsearch/<action_type>/', RuleView.as_view(), name="rule_config"),
    
    # ## visuals
    # path('visuals/<threat>/', views.visuals_view),
    # # User Threat AJAX ajax
    # path('visuals/user/details/', views.user_details),

    # path("neo4j/",views.neo4j_graph),
    
    # # Detail Modal
    # path('rules/<resourceType>/<logType>/<ruleType>/details/', ajax_views.rule_details),

    # # Edit Modal
    # path('custom/edit/', ajax_views.edit_rule),
    # path('rules/<resourceType>/<logType>/edit/', ajax_views.rule_edit_modal),

    # # Delete Modal
    # path('custom/delete/', ajax_views.delete_rule),

    # # Add Modal
    # path('custom/add/', ajax_views.add_rule),
    # path('custom/add/<section>/', ajax_views.add_rule_section),
    # path('rules/<resourceType>/<logType>/add/', ajax_views.rule_add_modal),

    # # On/Off Action
    # path('rules/<resourceType>/<logType>/on_off/', ajax_views.on_off)
]
