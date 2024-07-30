from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .src.integration import(integration_check, integration_insert, 
delete_integration, container_trigger, list_integration)
from .src.refresh_integrations import refresh_container_status

# Integration
@login_required
def integration_view(request):
    context = list_integration(request.session.get('db_name'))
    return render(request, f"M_equipment/configuration.html", context)

def refresh_integration_section(request):
    context_ = list_integration(request.session.get('db_name'))
    context = refresh_container_status(integration_list=context_, user_db=request.session.get('db_name'))
    return render(request, f"M_equipment/integration_section.html", context)

def integration_config_ajax(request, actionType):
    if request.method == 'POST':
        data = dict(request.POST.items())
        if actionType == 'modal':
            return render(request, 'M_equipment/configuration/modal.html', data)
        if actionType == 'check':
            return 
        if actionType == 'delete':
            context = delete_integration(request=request)
            return JsonResponse(context)
        if actionType == 'trigger':
            context = container_trigger(request=request)
            return JsonResponse(context)

@login_required
def registration_page(request, equipment, logType):
    context = {'logType': logType}
    return render(request, f"M_equipment/registration/{equipment}.html", context)

@login_required
def registration_view(request):
    return render(request, f"M_equipment/registration.html")

def integration_registration_ajax(request, equipment, logType, actionType):
    if request.method == 'POST':
        if actionType == 'check':
            context = integration_check(request, equipment, logType)
            return JsonResponse(context)
        elif actionType == 'insert':
            context = integration_insert(request, equipment)
            if type(context) != str:
                return context
            else:
                return HttpResponse(context)