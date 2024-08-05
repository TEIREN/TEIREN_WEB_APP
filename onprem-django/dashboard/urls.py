# /webAPP/django/dashboard/
# 127.0.0.1/dashboard
from django.urls import path
from dashboard.src import gridstack_items
from dashboard.src import gridstack
from dashboard import views
from django.conf.urls.static import static

URL_PATH = 'dashboard'
# dashboard/
urlpatterns = [
    # path('', views.dashboard_view, name='root'),
    # path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.view_finevo_dashboard, name='root'),
    path('dashboard/', views.view_finevo_dashboard, name="finevo_dashboard")
]
# # /grid
# urlpatterns += [
#     path('grid/save/', gridstack.save_layout),
#     path('grid/load/', gridstack.load_layout),
#     path('grid/new/', gridstack.new_layout),
#     path('grid/delete/', gridstack.delete_layout),
#     path('grid/layouts/', gridstack.list_layouts),
#     path('grid/items/<type>/', gridstack.add_item),
#     path('grid/items/', gridstack.list_items),
#     path('grid/default/', gridstack.default_layout),
# ]

# # /status
# urlpatterns += [
#     path("status/", gridstack_items.get_server_status),
# ]