from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .src import integration

# Integration
@login_required
def integration_view(request, pageType):
    if pageType == 'configuration':
        context = integration.list_integration()
        return render(request, f"M_equipment/{pageType}.html", context)
    return render(request, f"M_equipment/{pageType}.html")

def integration_config_ajax(request, actionType):
    if request.method == 'POST':
        data = dict(request.POST.items())
        if actionType == 'modal':
            return render(request, 'M_equipment/configuration/modal.html', data)
        elif actionType == 'delete':
            context = integration.delete_integration(data)
        elif actionType == 'trigger':
            context = integration.container_trigger(data)
        return JsonResponse(context)

@login_required
def registration_page(request, equipment, logType):
    context = {'logType': logType}
    return render(request, f"M_equipment/registration/{equipment}.html", context)

def integration_registration_ajax(request, equipment, logType, actionType):
    if request.method == 'POST':
        if actionType == 'check':
            context = integration.integration_check(request, equipment, logType)
            return JsonResponse(context)
        elif actionType == 'insert':
            context = integration.integration_insert(request, equipment)
            return HttpResponse(context)