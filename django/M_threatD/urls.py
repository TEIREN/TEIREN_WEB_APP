from django.urls import path
from . import views, rule_ajax
from .src.notification import detection

urlpatterns = [
    # Risk Management
    ## alert
    path('notifications/<threat>/', views.notification_view),
    # test
    # ## rules
    path('rules/<resourceType>/<logType>/', views.rules_view),
    ## visuals
    path('visuals/<threat>/', views.visuals_view),
    # User Threat AJAX ajax
    path('visuals/user/details/', views.user_details),

    path("neo4j/",detection.neo4j_graph),
]

urlpatterns +=[
    # Update Rule Table
    path('rules/<resourceType>/<logType>/<ruleType>/filter/', rule_ajax.rule_update),

    # Rule Detail Modal
    path('rules/<resourceType>/<logType>/<ruleType>/details/', rule_ajax.rule_details),

    # Rule Edit Modal
    path('rules/<resourceType>/<logType>/edit/', rule_ajax.rule_edit_modal),
    path('custom/edit/', rule_ajax.edit_rule),

    # Rule Delete Modal
    path('custom/delete/', rule_ajax.delete_rule),

    # Rule Add Modal
    path('rules/<resourceType>/<logType>/add/', rule_ajax.rule_add_modal),
    path('custom/add/<section>/', rule_ajax.add_rule_section),
    path('custom/add/', rule_ajax.add_rule),

    # Rule On/Off Action
    path('rules/<resourceType>/<logType>/on_off/', rule_ajax.on_off),
]
