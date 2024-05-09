from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
import requests

def integration_action_genian(request):
    url = f"http://44.204.132.232:8088/genian_api_send?api_key={request.POST['access_key']}"
    response = requests.get(url)
    return response.text

def integration_genian(request):
    if request.method == 'POST':
        return HttpResponse(integration_action_genian(request))
    else:
        return render(request, 'testing/finevo/integration_genian.html')



def integration_action_fortigate(request):
    url = f"http://44.204.132.232:8088/?api_key={request.POST['access_key']}"
    response = requests.get(url)
    return response.text


def integration_fortigate(request):
    if request.method == 'POST':
        return HttpResponse(integration_action_fortigate(request))
    else:
        return render(request, 'testing/finevo/integration_fortigate.html')