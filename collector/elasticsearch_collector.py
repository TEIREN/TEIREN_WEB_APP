from uvicorn import run  # port 열어주는 plugin
from fastapi import FastAPI, Request, BackgroundTasks #API 사용가능하게 해주는 plugin
from elasticsearch import Elasticsearch
from datetime import datetime
from genian_deployment import get_logs, parse_log, send_genian_logs
import time
import requests
import urllib3

# Connect to local Elasticsearch instance
es = Elasticsearch("http://44.204.132.232:9200/") # Elasticsearch 연결
# es = Elasticsearch("http://10.0.3.81:9200/") # 호스트 IP 주소와 포트로 Elasticsearch 연결

should_stop = False

app = FastAPI()

# elasticsearch에 로그 저장하는 함수
async def elasticsearch_input(log, system):
    response = es.index(index=f"test_{system}_syslog", document=log) # 해당하는 index에 로그 저장
    print(f"{system}_log: {response['result']}")

    print(log)
    print('*'*50)
    return 0


# 리눅스 로그 수집 (<ip>:8088/linux_log 로 post보내서 실행)
@app.post("/linux_log")
async def receive_log(request: Request):
    log_request = await request.json() # request받은 로그를 json 형식으로 변경
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        await elasticsearch_input(log, 'linux') # elasticsearch에 로그 저장하는 함수 실행
    return {"message": "Log received successfully"}

# 윈도우 로그 수집
@app.post('/win_log')
async def win_log(request: Request):
    log_request = await request.json()
    # print(log_request)
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        await elasticsearch_input(log, 'window')
    return {"message": "Log received successfully"}

@app.post('/genian_log') # Genian 로그 수집
async def genian_log(request: Request):
    log_request = await request.json()
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        print(log)
        await elasticsearch_input(log, 'genian')

    return {"message": "Log received successfully"}

@app.post('/fortigate_log') # Genian 로그 수집
async def fortigate_log(request: Request):
    log_request = await request.json()
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        await elasticsearch_input(log, 'fortigate')
    return {"message": "Log received successfully"}

@app.get("/genian_api_send")
async def get_genian_logs(api_key: str = None, page: int = 1, page_size: int = 30, background_tasks: BackgroundTasks = None):
    if not api_key:
        return {"error": "API 키가 필요합니다."}
    logs = []
    while True:
        new_logs = get_logs(api_key, page, page_size)
        if not new_logs:
            break
        logs.extend(new_logs)
        page += 1
    parsed_logs = [parse_log(log) for log in logs]
    background_tasks.add_task(continue_log_collection, api_key)
    return {"message": "로그 수집이 진행 중입니다."}

def continue_log_collection(api_key):
    while True:
        send_genian_logs(api_key)
        time.sleep(60)

@app.get("/stop_genian_api_send")
async def stop_genian_logs():
    global should_stop
    should_stop = True
    return {"message": "로그 수집을 중지하겠습니다."}

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8088) # listen하는 ip랑 포트 열어줘서 FastAPI 실행하기
