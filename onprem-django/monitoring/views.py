from datetime import datetime, timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import render, redirect
from api.metrics.models import Metrics


# Monitoring dashbaord without uuid
@login_required
def dashboard(request):
    user_uuid = request.session.get('uuid')
    print(f"dashboard page, uuid: {user_uuid}")
    return redirect('dashboard', uuid=user_uuid)

# Monitoring dashboard with uuid
def dashboard_uuid(request, uuid):
    return render(request, "monitoring/dashboard.html", {"uuid": uuid})

# Monitoring dashboard infomation page with uuid
def info(request):
    print(request.session.session_key)
    print(request.session.get('user_id'))
    print(request.session.get('uuid'))
    return render(request, "monitoring/info.html")


def get_metric_data(request, instance_id):
    metrics = list(Metrics.objects.filter(instance_id=instance_id).values())
    return JsonResponse(metrics, safe=False)

