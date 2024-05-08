from django.shortcuts import render, HttpResponse
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from TeirenSIEM.integration import integrations
from TeirenSIEM.log import log
from TeirenSIEM import risk
import math
import xlwt

# Dashboard
@login_required
def dashboard_view(request):
    return render(request, "dashboard/dashboard.html")

# Log Management
@login_required
def log_view(request, cloud):
    if request.method == 'POST':
        context = dict(request.POST.items())
        context = (log.get_log_page(context, cloud))
        return render(request,f"log/dataTable.html",context)
    context = dict(request.GET.items())
    context = (log.get_log_page(context, cloud))
    context['cloud']= cloud.capitalize()
    context.update(risk.alert.alert.check_topbar_alert())
    return render(request,f"log/log.html",context)


# Risk Management
## Alert
@login_required
def alert_view(request, type):
    if request.method == 'POST':
        if request.POST['cloud'] == 'Aws':
            context = risk.alert.alert.alert_off(dict(request.POST.items()))
            context.update(risk.alert.detection.neo4j_graph(context))
            context.update(risk.alert.alert.check_topbar_alert())
        return render(request, f"risk/alert/{type}.html", context)
    else:
        if type == 'details':
            return HttpResponseRedirect('/alert/logs/')
    context = (risk.alert.alert.get_alert_logs())
    context.update(risk.alert.alert.check_topbar_alert())
    return render(request, f"risk/alert/{type}.html", context)

## Rules
@login_required
def rules_view(request, type):
    context = risk.rule.default.get_custom_rules(type)
    context.update(risk.rule.default.get_default_rules(type))
    context.update({'cloud': type.capitalize()})
    context.update(risk.alert.alert.check_topbar_alert())
    return render(request, f"risk/rules/rule.html", context)

## Visuals
@login_required
def visuals_view(request, type):
    if type == 'user':
        context = {'accounts': sorted(risk.visual.user.user.get_user_visuals(), key=lambda x: x['total'], reverse=True)}
    elif type == 'ip':
        map = risk.visual.ip.folium.folium_test('37.5985', '126.97829999999999')
        context = {'map': map}
    else:
        context = {}
    context.update(risk.alert.alert.check_topbar_alert())
    return render(request, f"risk/visuals/{type}.html", context)

# Settings
@login_required
def settings_view(request, type):
    context = (risk.alert.alert.check_topbar_alert())
    return render(request, f"settings/{type}.html", context)

# Integration
@login_required
def integration_view(request):
    context = integrations.list_integration()
    context.update(risk.alert.alert.check_topbar_alert())
    return render(request, "integration/integration.html", context)

@login_required
def integration_type(request, type):
    if type == 'delete':
        if request.method == 'POST':
            data = dict(request.POST.items())
            context = integrations.delete_integration(data)
            return HttpResponse(context)
    context=(risk.alert.alert.check_topbar_alert())
    return render(request, f"integration/{type}.html", context)


# Compliance
def compliance_view(request):
    context=(risk.alert.alert.check_topbar_alert())
    return render(request, "compliance/compliance.html", context)

# Report
@login_required
def report_view(request):
    context=(risk.alert.alert.check_topbar_alert())
    return render(request, "compliance/report.html", context)

def report_month_view(request):
    return render(request, "compliance/report.html")