from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

@login_required
def dashboard_view(request, uuid=None):
    """Dashboard View using uuid
    각 사용자 별 UUID 를 사용하여서 각 사용자들의 대시보드로 redirect.
    
    Args:
        request (_type_): _description_

    Returns:
        _type_: _description_
    """
    # user_uuid = request.session.get('uuid')
    # print(user_uuid)
    # if not user_uuid:
    #     #return 404 page
    #     pass
    
    return render(request, "dashboard/dashboard.html")

