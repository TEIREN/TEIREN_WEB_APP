# local
import json
## class handler
from .src.rule.default import Default
from .src.visual.user.user import UserThreat
from .src.visual.ip.folium import folium_test
from .src.notification.detection import Detection
from .src.notification.notification import Notification
from .src.rule.elasticsearch_rule import rule_config_page

# django
from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect


# Notifications
@login_required
def notification_view(request, threat):
    print(f'notifications, {threat}')
    print(request.method == 'POST')
    if request.method == 'POST':
        context = dict(request.POST.items())
        if threat == 'details':
            with Notification(request=request) as __notification:
                __notification.alert_off()
            with Detection(request=request) as __detection:
                context.update(__detection.neo4j_graph())
            return render(request, f"M_threatD/notifications/{threat}.html", context)
        elif threat == 'filter':
            with Notification(request=request) as __notification:
                context.update(__notification.get_alert_logs())
            return render(request, f"M_threatD/notifications/dataTable.html", context)
    else:
        if threat == 'details':
            return HttpResponseRedirect('/threat/notifications/logs/')
    with Notification(request=request) as __notification:
        context = (__notification.get_alert_logs())
        context.update(__notification.get_filter_list())
    return render(request, f"M_threatD/notifications/{threat}.html", context)

# Rules
@login_required
def rules_view(request, resourceType, logType):
    if logType in ['aws', 'teiren_cloud']:
        with Default(request=request) as __default:
            context = __default.get_custom_rules(logType)
            context.update(__default.get_default_rules(logType))
        if resourceType == 'cloud':
            logType = (' ').join(logType.split('_')).upper()
        else:
            logType = (' ').join(logType.split('_')).title()
        context.update({'logType': logType})
        context.update({'resourceType': resourceType})
        return render(request, f"M_threatD/rules/rule.html", context)
    else:
        return rule_config_page(request=request, system=logType)


## Visuals
@login_required
def visuals_view(request, threat):
    if threat == 'user':
        with UserThreat(request) as __uthreat:
            context = {'accounts': sorted(__uthreat.get_user_visuals(), key=lambda x: x['total'], reverse=True)}
    elif threat == 'ip':
        map = folium_test('37.5985', '126.97829999999999')
        context = {'map': map}
    else:
        context = {}
    return render(request, f"M_threatD/visuals/{threat}.html", context)

## Visuals User Details Modal
@login_required
def user_details(request):
    context = dict(request.POST.items())
    if request.method == 'POST':
        with UserThreat(request) as __uthreat:
            context.update(__uthreat.user_graph())
        return render(request, 'M_threatD/visuals/user/details.html', context)
    
import json
def neo4j_graph(request):
    with Detection(request) as __detection:
        if isinstance(request, dict):
            data = __detection.get_data()
            details = __detection.get_log_details()
            context = {'graph': json.dumps(data), 'details': details }
            return context
        elif request.method == 'POST':
            data = __detection.get_data()
            details = __detection.get_log_details()
            context = {'graph': json.dumps(data), 'details': details}
            return render(request, 'graphdb/graph.html', context)
        return HttpResponse('다시 시도')