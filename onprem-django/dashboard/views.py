from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .src.finevo import FortigateDashboard

@login_required
def dashboard_view(request, uuid=None):
    """Dashboard View using uuid
    각 사용자 별 UUID 를 사용하여서 각 사용자들의 대시보드로 redirect.
    """
    # user_uuid = request.session.get('uuid')
    # print(user_uuid)
    # if not user_uuid:
    #     #return 404 page
    #     pass
    
    return render(request, "dashboard/dashboard.html")

@login_required
def view_finevo_dashboard(request):
    context = FortigateDashboard().get_dashboard_data()
    return render(request, "dashboard/finevo/dashboard.html", context=context)


