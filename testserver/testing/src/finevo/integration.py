from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest, FileResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import tempfile
# from elasticsearch import Elasticsearch, ConnectionError

"""
임시적으로 추가한 check logs 함수
"""
# # Elasticsearch 클라이언트를 설정합니다.
# es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# # 탐지 대상 로그 인덱스
# log_index = {
#     1: "test_linux_syslog",
#     2: "test_window_syslog",
#     3: "test_genian_syslog",
#     4: "test_fortigate_syslog"
# }

# # 룰셋 인덱스 이름 매핑
# ruleset_mapping = {
#     1: "linux_ruleset",
#     2: "window_ruleset",
#     3: "genian_ruleset",
#     4: "fortigate_ruleset"
# }

# def check_logs(request): # http://3.35.81.217/test/integration/check_logs/?index_choice=1
#     index_choice = int(request.GET.get('index_choice', 1))
#     if index_choice not in [1, 2, 3, 4]:
#         return JsonResponse({"error": "Invalid index choice, please select a number between 1 and 4."}, status=400)
    
#     log_index_name = log_index[index_choice]
#     ruleset_index = ruleset_mapping[index_choice]

#     try:
#         # 모든 룰셋을 Elasticsearch에서 가져옵니다.
#         res = es.search(index=ruleset_index, body={"query": {"match_all": {}}, "size": 10000})
#         rulesets = res['hits']['hits']
#         logs_detected = {}

#         for rule in rulesets:
#             rule_query = rule["_source"]["query"]["query"]
#             rule_name = rule["_source"]["name"]
#             severity = rule["_source"]["severity"]

#             # 룰셋을 사용하여 로그를 탐지합니다.
#             log_res = es.search(index=log_index_name, body={"query": rule_query, "size": 10000})
#             logs_found = log_res['hits']['total']['value']

#             if logs_found > 0:
#                 for log in log_res['hits']['hits']:
#                     log_id = log["_id"]
#                     log_doc = log["_source"]

#                     if log_id not in logs_detected:
#                         logs_detected[log_id] = log_doc
#                         logs_detected[log_id]["detected_by_rules"] = []
#                         logs_detected[log_id]["severities"] = []

#                     logs_detected[log_id]["detected_by_rules"].append(rule_name)
#                     logs_detected[log_id]["severities"].append(severity)

#         response_data = {
#             "total_rules": len(rulesets),
#             "logs_detected": logs_detected
#         }

#         return JsonResponse(response_data, json_dumps_params={'indent': 4}, safe=False)

#     except ConnectionError as e:
#         return JsonResponse({"error": f"Connection error: {e}"}, status=500)
#     except Exception as e:
#         return JsonResponse({"error": f"An error occurred: {e}"}, status=500)



def integration_action_genian(request):
    url = f"http://3.35.81.217:8088/genian_api_send?api_key={request.POST['access_key']}"
    response = requests.get(url)
    return response.text

def integration_genian(request):
    if request.method == 'POST':
        return HttpResponse(integration_action_genian(request))
    else:
        return render(request, 'testing/finevo/integration_genian.html')


def integration_action_fortigate(request):
    url = f"http://3.35.81.217:8088/fortigate_api_send?api_key={request.POST['access_key']}"
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


def integration_action_windows(request):
    url = 'https://raw.githubusercontent.com/hw1186/rsys_conf/main/setup_win.ps1'
    response = requests.get(url)
    filename = url.split('/')[-1]
    temp = tempfile.NamedTemporaryFile(delete=False)
    # temp = tempfile.NamedTemporaryFile(suffix=".sh")
    temp.write(response.content)
    temp.close()
    return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)

def integration_windows(request):
    if request.method == 'POST':
        return integration_action_windows(request)
    else:
        return render(request, 'testing/finevo/integration_windows.html')
# Form 데이터 형식 사용

def integration_action_mssql(request): # alert가 잘 안됨
    if request.method == 'POST':
        server = request.POST.get('db_server')
        database = request.POST.get('db_name')
        username = request.POST.get('db_uid')
        password = request.POST.get('db_password')
        table_name = request.POST.get('db_table')

        if not all([server, database, username, password, table_name]):
            return JsonResponse({"error": "모든 필드를 입력하세요."}, safe=False, json_dumps_params={'ensure_ascii':False}, status=400)

        # 백그라운드 태스크 시작을 위한 요청을 보냄
        url = "http://3.35.81.217:8088/start_mssql_collection"
        data = {
            'server': server,
            'database': database,
            'username': username,
            'password': password,
            'table_name': table_name
        }
        response = requests.post(url, data=data)

        if response.status_code == 200:
            return JsonResponse({"message": "MSSQL 로그 수집이 시작되었습니다."}, safe=False, json_dumps_params={'ensure_ascii':False}, status=200)
        else:
            return JsonResponse({"error": "서버 요청 실패"}, safe=False, json_dumps_params={'ensure_ascii':False}, status=500)

    else:
        return JsonResponse({"error": "잘못된 요청"}, safe=False, json_dumps_params={'ensure_ascii':False}, status=405)


def integration_mssql(request):
    if request.method == 'POST':
        return HttpResponse(integration_action_mssql(request))
    else:
        return render(request, 'testing/finevo/integration_mssql.html')

# def integration_action_snmp(request):
#     print(request.POST.dict())
#     return str(request.POST.dict())

# def integration_snmp(request):
#     if request.method == 'POST':
#         return HttpResponse(integration_action_snmp(request))
#     else:
#         return render(request, 'testing/finevo/integration_snmp.html')

# integration.py 파일 내에 있는 integration_snmp 함수 수정
@csrf_exempt
def integration_snmp(request):
    if request.method == 'POST':
        client_ip = get_client_ip(request)  # 클라이언트 IP 얻기
        request_data = request.POST.dict()
        request_data['teiren_request_ip'] = client_ip  # 클라이언트 IP 로그 데이터에 추가
        return HttpResponse(str(request_data))
    else:
        return render(request, 'testing/finevo/integration_snmp.html')

# 클라이언트의 IP 주소를 얻는 함수
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# def integration_action_transmission(request):
#     pass

# def integration_transmission(request):
#     if request.method == 'POST':
#         return HttpResponse(integration_action_transmission(request))
#     else:
#         return render(request, 'testing/finevo/integration_transmission.html')


@csrf_exempt # alert가 잘 안됨
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
                return JsonResponse({"message": "Configuration added and Fluentd service restarted successfully."}, status=200)
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