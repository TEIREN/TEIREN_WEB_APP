from django.shortcuts import render
from django.urls import path
from . import views

urlpatterns = [
    path('info/', views.info),
    path('dashboard/', views.dashboard, name='redirect_dashboard'),
    path('dashboard/<uuid:uuid>/', views.dashboard_uuid, name='dashboard'),
]