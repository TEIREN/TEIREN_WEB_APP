from _auth import views
from _auth.src.finevo import finevo
from django.urls import path


urlpatterns = [
    # path('login/', views.login_, name='login'),
    # path('logout/', views.logout_, name='logout'),
    # path('register/', views.register_, name='register'),
    # path('activate/<str:uidb64>/<str:token>/', views.activate_, name='activate'),
    path('login/', finevo.login_, name='login'),
    path('logout/', finevo.logout_, name='logout'),
]
