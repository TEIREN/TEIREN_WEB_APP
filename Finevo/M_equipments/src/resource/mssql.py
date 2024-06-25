from django.http import JsonResponse
import requests

def mssql_insert(request):
    if request.method == 'POST':
        server = request.POST.get('db_server')
        database = request.POST.get('db_name')
        username = request.POST.get('db_uid')
        password = request.POST.get('db_password')
        table_name = request.POST.get('db_table')

        if not all([server, database, username, password, table_name]):
            return "모든 필드를 입력하세요."

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
            return "MSSQL 로그 수집이 시작되었습니다."
        else:
            return "서버 요청 실패"
    else:
        return "잘못된 요청입니다. 다시 시도해주세요."