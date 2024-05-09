from uvicorn import run
from fastapi import FastAPI, Request, BackgroundTasks
from elasticsearch import Elasticsearch
from datetime import datetime
from genian_deployment import get_logs, parse_log, send_genian_logs
import time

es = Elasticsearch("http://44.204.132.232:9200/")
should_stop = False
log_collection_started = False

app = FastAPI()

async def elasticsearch_input(log, system):
    response = es.index(index=f"test_{system}_syslog", document=log)
    print(f"{system}_log: {response['result']}")
    print(log)
    print('*'*50)
    return 0

@app.post("/linux_log")
async def receive_log(request: Request):
    log_request = await request.json()
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        await elasticsearch_input(log, 'linux')
    return {"message": "Log received successfully"}

@app.post('/win_log')
async def win_log(request: Request):
    log_request = await request.json()
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        await elasticsearch_input(log, 'window')
    return {"message": "Log received successfully"}

@app.post('/genian_log')
async def genian_log(request: Request):
    log_request = await request.json()
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        log['teiren_stamp'] = datetime.now()
        await elasticsearch_input(log, 'genian')

    return {"message": "Log received successfully"}

@app.post('/fortigate_log')
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
    global log_collection_started
    log_collection_started = True
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
    while not should_stop:
        send_genian_logs(api_key)
        time.sleep(5)
        # time.sleep(60) n 초당 한번 씩

# 전체적으로 조금 기다려야 함 
# api_key: b17eeffd-f8ca-4443-baf4-c4376ed48a9e
# curl -X GET http://44.204.132.232:8088/stop_genian_api_send 
@app.get("/stop_genian_api_send")
async def stop_genian_api_send():
    global should_stop
    should_stop = True
    return {"message": "Genian API 전송 중지 요청이 접수되었습니다."}

# curl http://44.204.132.232:8088/log_collection_status
@app.get("/log_collection_status")
async def get_log_collection_status():
    return {"log_collection_started": log_collection_started, "log_collection_stopped": should_stop} 
# started가 TRUE면 수집중 FALSE면 수집 안되는중 
# STOPPED가 TRUE면 수집중지 FALSE면 수잡 재개

# curl -X GET http://44.204.132.232:8088/resume_genian_api_send
@app.get("/resume_genian_api_send")
async def resume_genian_api_send():
    global should_stop
    should_stop = False
    return {"message": "Genian API 전송이 재개되었습니다."}
# 전송 재개 후 조금 기다리면 다시 전송 됨

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8088)
