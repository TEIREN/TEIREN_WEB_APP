import pymssql
import json
import requests

def send_mssql_logs(server, database, username, password, table_name):
    POST_URL = "http://localhost:8088/mssql_log"  # Elasticsearch에 데이터를 보낼 URL

    # 데이터베이스 연결 설정
    conn = pymssql.connect(server=server, user=username, password=password, database=database)
    cursor = conn.cursor()

    # 테이블명을 사용하여 데이터를 선택하는 쿼리
    query = f"SELECT * FROM {table_name}"
    cursor.execute(query)

    # 결과를 JSON으로 변환
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]  # 모든 데이터 가져옴

    # 데이터베이스 연결 종료
    cursor.close()
    conn.close()

    # 각 결과를 JSON 문자열로 변환하고 POST 요청으로 보냄
    headers = {'Content-Type': 'application/json'}
    for result in results:
        json_result = json.dumps(result, ensure_ascii=False)
        response = requests.post(POST_URL, headers=headers, data=json_result.encode('utf-8'))
        print(response.text)  # 서버 응답 출력
