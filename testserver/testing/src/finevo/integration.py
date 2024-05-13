from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest, FileResponse
import requests
import tempfile

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
    url = f"http://44.204.132.232:8088/fortigate_api_send?api_key={request.POST['access_key']}"
    response = requests.get(url)
    return response.text


def integration_fortigate(request):
    if request.method == 'POST':
        return HttpResponse(integration_action_fortigate(request))
    else:
        return render(request, 'testing/finevo/integration_fortigate.html')
    
def integration_action_linux(request):
    url = 'https://raw.githubusercontent.com/hw1186/rsys_conf/main/setup_linux.sh'
    response = requests.get(url)
    filename = url.split('/')[-1]
    temp = tempfile.NamedTemporaryFile(delete=False)
    # temp = tempfile.NamedTemporaryFile(suffix=".sh")
    temp.write(response.content)
    temp.close()
    return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)

def integration_linux(request):
    if request.method == 'POST':
        return integration_action_linux(request)
    else:
        return render(request, 'testing/finevo/integration_linux.html')

def integration_action_mssql(request):
    # url = f"http://44.204.132.232:8088/fortigate_api_send?api_key={request.POST['access_key']}"
    # response = requests.get(url)
    # return response.text
    return str(request.POST.dict())

def integration_mssql(request):
    if request.method == 'POST':
        return HttpResponse(integration_action_mssql(request))
    else:
        return render(request, 'testing/finevo/integration_mssql.html')