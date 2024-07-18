from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseBadRequest, FileResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import tempfile

def integration_action_genian(request):
    if request.method == 'POST':
        url = f"http://3.35.81.217:8088/genian_api_send?api_key={request.POST['access_key']}&TAG_NAME=genian_api"
        response = requests.get(url)
        return JsonResponse(response.json(), safe=False)
    else:
        return render(request, 'testing/finevo/integration_genian.html')

def integration_genian(request):
    if request.method == 'POST':
        return integration_action_genian(request)
    else:
        return render(request, 'testing/finevo/integration_genian.html')


def integration_action_fortigate(request):
    if request.method == 'POST':
        url = f"http://3.35.81.217:8088/fortigate_api_send?api_key={request.POST['access_key']}&TAG_NAME=fortigate_api"
        response = requests.get(url)
        return JsonResponse(response.json(), safe=False)
    else:
        return render(request, 'testing/finevo/integration_fortigate.html')

def integration_fortigate(request):
    if request.method == 'POST':
        return integration_action_fortigate(request)
    else:
        return render(request, 'testing/finevo/integration_fortigate.html')


def integration_action_linux(request):
    if request.method == 'POST':
        url = 'https://raw.githubusercontent.com/hw1186/rsys_conf/main/setup_linux.sh'
        response = requests.get(url)
        filename = url.split('/')[-1]
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(response.content)
        temp.close()
        return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)
    else:
        return render(request, 'testing/finevo/integration_linux.html')

def integration_linux(request):
    if request.method == 'POST':
        return integration_action_linux(request)
    else:
        return render(request, 'testing/finevo/integration_linux.html')


def integration_action_windows(request):
    if request.method == 'POST':
        url = 'https://raw.githubusercontent.com/hw1186/rsys_conf/main/setup_win.ps1'
        response = requests.get(url)
        filename = url.split('/')[-1]
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(response.content)
        temp.close()
        return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)
    else:
        return render(request, 'testing/finevo/integration_windows.html')

def integration_windows(request):
    if request.method == 'POST':
        return integration_action_windows(request)
    else:
        return render(request, 'testing/finevo/integration_windows.html')


def integration_action_mssql(request):
    if request.method == 'POST':
        server = request.POST.get('db_server')
        database = request.POST.get('db_name')
        username = request.POST.get('db_uid')
        password = request.POST.get('db_password')
        table_name = request.POST.get('db_table')
        TAG_NAME = "mssql_api"

        if not all([server, database, username, password, table_name]):
            return JsonResponse({"error": "모든 필드를 입력하세요."}, safe=False, json_dumps_params={'ensure_ascii':False}, status=400)

        url = "http://3.35.81.217:8088/start_mssql_collection"
        data = {
            'server': server,
            'database': database,
            'username': username,
            'password': password,
            'table_name': table_name,
            'TAG_NAME': TAG_NAME
        }
        response = requests.post(url, json=data)

        if response.status_code == 200:
            return JsonResponse(response.json(), safe=False, json_dumps_params={'ensure_ascii':False}, status=200)
        else:
            return JsonResponse({"error": "서버 요청 실패"}, safe=False, json_dumps_params={'ensure_ascii':False}, status=500)

    else:
        return JsonResponse({"error": "잘못된 요청"}, safe=False, json_dumps_params={'ensure_ascii':False}, status=405)

def integration_mssql(request):
    if request.method == 'POST':
        return integration_action_mssql(request)
    else:
        return render(request, 'testing/finevo/integration_mssql.html')


@csrf_exempt
def integration_snmp(request):
    if request.method == 'POST':
        client_ip = get_client_ip(request)
        request_data = request.POST.dict()
        request_data['teiren_request_ip'] = client_ip
        return JsonResponse(request_data)
    else:
        return render(request, 'testing/finevo/integration_snmp.html')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
def integration_action_transmission(request):
    if request.method == 'POST':
        protocol = request.POST.get('protocol')
        source_ip = request.POST.get('source_ip')
        dst_port = request.POST.get('dst_port')
        log_tag = request.POST.get('log_tag')
        
        data = {
            "new_protocol": protocol,
            "new_source_ip": source_ip,
            "new_dst_port": dst_port,
            "new_log_tag": log_tag
        }
        
        try:
            response = requests.post(
                'http://3.35.81.217:8088/add_config/',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(data)
            )
            if response.status_code == 200:
                return JsonResponse(response.json(), status=200)
            else:
                return JsonResponse({"error": "Failed to add configuration."}, status=response.status_code)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return HttpResponse(status=405)

def integration_transmission(request):
    if request.method == 'POST':
        return integration_action_transmission(request)
    else:
        return render(request, 'testing/finevo/integration_transmission.html')

# API 키 삭제
@csrf_exempt
def delete_api_key(request, system):
    if request.method == 'POST':
        tag_name = request.POST.get('TAG_NAME')
        if not tag_name:
            return JsonResponse({"error": "TAG_NAME is required."}, status=400)
        
        # Check the status
        status_url = "http://3.35.81.217:8088/log_collection_status"
        status_response = requests.post(status_url, json={"TAG_NAME": tag_name})
        if status_response.status_code == 200 and status_response.json().get("status") == "로그 수집이 진행중입니다.":
            return JsonResponse({"error": "Cannot delete API key while log collection is active."}, status=400)
        
        # Proceed with deletion
        url = f"http://3.35.81.217:8088/delete_{system}_api_key"
        response = requests.post(url, json={"TAG_NAME": tag_name})
        
        if response.status_code == 200:
            return JsonResponse(response.json(), status=200)
        else:
            return JsonResponse({"error": "Failed to delete API key."}, status=response.status_code)
    else:
        return HttpResponse(status=405)
