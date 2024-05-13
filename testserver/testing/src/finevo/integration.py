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

# Form 데이터 형식 사용

def integration_action_mssql(request):
    if request.method == 'POST':
        server = request.POST.get('db_server')
        database = request.POST.get('db_name')
        username = request.POST.get('db_uid')
        password = request.POST.get('db_password')
        table_name = request.POST.get('db_table')

        if not all([server, database, username, password, table_name]):
            return JsonResponse({"error": "모든 필드를 입력하세요."}, status=400)

        # 백그라운드 태스크 시작을 위한 요청을 보냄
        url = "http://44.204.132.232:8088/start_mssql_collection"
        data = {
            'server': server,
            'database': database,
            'username': username,
            'password': password,
            'table_name': table_name
        }
        response = requests.post(url, data=data)

        if response.status_code == 200:
            return JsonResponse({"message": "MSSQL 로그 수집이 시작되었습니다."}, status=200)
        else:
            return JsonResponse({"error": "서버 요청 실패"}, status=500)

    else:
        return JsonResponse({"error": "잘못된 요청"}, status=405)


def integration_mssql(request):
    if request.method == 'POST':
        return HttpResponse(integration_action_mssql(request))
    else:
        return render(request, 'testing/finevo/integration_mssql.html')
