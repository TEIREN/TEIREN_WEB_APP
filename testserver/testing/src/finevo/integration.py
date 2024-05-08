# local
import json
import requests

from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest


class Integration():
    def __init__(self):
        pass
    
    def connect_integration(self):
        pass
    
    def integration_page(self):
        pass

def integration_action_genian(request):
    url = f"http://3.35.81.217:8000/genian/?api_key={request.POST['access_key']}"
    response = requests.get(url)
    return response.text

def integration_genian(request):
    if request.method == 'POST':
        return HttpResponse(integration_action_genian(request))
    else:
        return render(request,'testing/finevo/integration_genian.html')