from uvicorn import run
from fastapi import FastAPI, Request, BackgroundTasks, Form, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch, NotFoundError
from datetime import datetime
from genian_deployment import get_logs, parse_log, send_genian_logs
from fortigate_deployment import send_fortigate_logs, parse_fortigate_log
from mssql_deployment import send_mssql_logs
import subprocess
import logging
import re
import os
import time
import json

es = Elasticsearch("http://3.35.81.217:9200/")
should_stop = False
log_collection_started = False

app = FastAPI()

conf_file_path = '/etc/fluent/fluentd.conf'

# ElasticSearch에 로그를 입력하는 함수
async def elasticsearch_input(log, system):
    index_name = f"test_{system}_syslog"  # 인덱스 이름 설정
    response = es.index(index=index_name, document=log)
    print(f"{system}_log: {response['result']}")
    return 0

# 인덱스가 존재하지 않으면 생성하는 함수
async def create_index_if_not_exists(index_name):
    try:
        es.indices.get(index=index_name)
    except NotFoundError:
        es.indices.create(index=index_name)

# API 키를 저장하는 함수
async def save_api_key(index_name, api_key):
    await create_index_if_not_exists(index_name)
    log = {
        "api_key": api_key,
        "inserted_at": datetime.now()
    }
    response = es.index(index=index_name, document=log)
    print(f"{index_name}_log: {response['result']}")
    return response

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
    client_ip = request.client.host

    for log in log_request:
        # Convert all keys to lowercase
        log = {k.lower(): v for k, v in log.items()}
        log['teiren_request_ip'] = client_ip
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

# Genian API 로그 수집 엔드포인트
#curl -X GET "http://localhost:8088/genian_api_send?api_key=b17eeffd-f8ca-4443-baf4-c4376ed48a9e"
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

    background_tasks.add_task(continue_log_collection, api_key)
    await save_api_key("genian_user_api", api_key)

    return {"message": "로그 수집이 진행 중입니다."}

# 로그 수집을 계속하는 함수
def continue_log_collection(api_key):
    while not should_stop:
        send_genian_logs(api_key)
        time.sleep(5)

# Genian API 로그 수집 중지 엔드포인트
# 전체적으로 조금 기다려야 함 
# api_key: b17eeffd-f8ca-4443-baf4-c4376ed48a9e
# curl -X GET http://localhost:8088/stop_genian_api_send 
@app.get("/stop_genian_api_send")
async def stop_genian_api_send():
    global should_stop
    should_stop = True
    return {"message": "Genian API 전송 중지 요청이 접수되었습니다."}

# 로그 수집 상태 확인 엔드포인트
# curl http://localhost:8088/log_collection_status

@app.get("/log_collection_status")
async def get_log_collection_status():
    return {"log_collection_started": log_collection_started, "log_collection_stopped": should_stop}
# started가 TRUE면 수집중 FALSE면 수집 안되는중 
# STOPPED가 TRUE면 수집중지 FALSE면 수잡 재개

# Genian API 로그 수집 재개 엔드포인트
@app.get("/resume_genian_api_send")
async def resume_genian_api_send():
    global should_stop
    should_stop = False
    return {"message": "Genian API 전송이 재개되었습니다."}
# 전송 재개 후 조금 기다리면 다시 전송 됨

# 얘도 상태 확인 멈춤 재개 만들면 됨

@app.post('/fortigate_log')
async def fortigate_log(request: Request):
    log_request = await request.json()
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        await elasticsearch_input(log, 'fortigate')
    return {"message": "Log received successfully"}

# Fortigate API 로그 수집 엔드포인트
@app.get("/fortigate_api_send")
async def get_fortigate_log(api_key: str = None, background_tasks: BackgroundTasks = None):
    if not api_key:
        return {"error": "API 키가 필요합니다."}

    global log_collection_started
    log_collection_started = True

    background_tasks.add_task(send_fortigate_logs, api_key)
    await save_api_key("fortigate_user_api", api_key)

    return {"message": "FortiGate 로그 수집이 진행 중입니다."}

@app.post('/mssql_log')
async def mssql_log(request: Request):
    log = await request.form()
    log_dict = {key: log[key] for key in log.keys()}
    log_dict['teiren_request_ip'] = request.client.host
    print(log_dict)
    await elasticsearch_input(log_dict, 'mssql')
    return {"message": "Log received successfully"}

# MSSQL 로그 수집 시작 엔드포인트
@app.post("/start_mssql_collection")
async def start_mssql_collection(
    server: str = Form(...),
    database: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    table_name: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    # 이 부분에서 백그라운드 태스크를 시작하고 사용자 정보를 넘김
    background_tasks.add_task(send_mssql_logs, server, database, username, password, table_name)
    return {"message": "MSSQL 로그 수집이 시작되었습니다."}

@app.post('/snmp_log')
async def snmp_log(request: Request):
    log_request = await request.body()
    print(log_request)
    print('-'*50)
    log_request = [json.loads(obj) for obj in log_request.decode('utf-8').split('\n') if obj]
    print(log_request)
    print('*'*50)
    return {"message": "Log received successfully"}

class FluentdConfig(BaseModel):
    new_protocol: str
    new_source_ip: str
    new_dst_port: str
    new_log_tag: str

# Fluentd 설정 추가 엔드포인트
@app.post("/add_config/")
def add_config(config: FluentdConfig):
    new_endpoint = f"http://localhost:8000/{config.new_log_tag}"
    
    new_conf_text = f"""
<source>
  @type {config.new_protocol}
  port {config.new_dst_port}
  bind {config.new_source_ip}
  tag {config.new_log_tag}
  <parse>
    @type json
  </parse>
</source>

<match {config.new_log_tag}>
  @type http
  endpoint {new_endpoint}
  json_array true
  <format>
    @type json
  </format>
  <buffer>
    flush_interval 10s
  </buffer>
</match>
"""
        
    try:
        with open(conf_file_path, 'a') as file:
            file.write(new_conf_text)
    except Exception as e:
        logging.error(f"Failed to write to the configuration file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to write to the configuration file: {e}")
    
    try:
        subprocess.run([
            'ssh', '-i', '/app/teiren-test.pem',
            '-o', 'StrictHostKeyChecking=no',
            'ubuntu@3.35.81.217',
            'sudo systemctl restart fluentd'
        ], check=True)
        return {"status": "success", "message": "Fluentd service restarted successfully"}
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to restart Fluentd service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart Fluentd service: {e}")

class DeleteTag(BaseModel):
    tag: str

# Fluentd 설정 삭제 엔드포인트
@app.post("/delete_tag/")
def delete_tag(request: DeleteTag):
    tag_to_delete = request.tag
    
    if not os.path.isfile(conf_file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {conf_file_path}")
    
    section_start_pattern = re.compile(r'<(source|match)[^>]*>')
    section_end_pattern = re.compile(r'</(source|match)>')
    tag_pattern = re.compile(r'\b{}\b'.format(re.escape(tag_to_delete)))
    
    try:
        with open(conf_file_path, 'r') as file:
            lines = file.readlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read the configuration file: {e}")
    
    new_lines = []
    section_lines = []
    in_section = False
    delete_section = False
    
    for line in lines:
        if section_start_pattern.match(line):
            in_section = True
            section_lines = [line]
            delete_section = False
            continue
        
        if in_section:
            section_lines.append(line)
            if tag_pattern.search(line):
                delete_section = True
            
            if section_end_pattern.match(line):
                in_section = False
                if not delete_section:
                    new_lines.extend(section_lines)
                section_lines = []
        else:
            new_lines.append(line)
    
    try:
        with open(conf_file_path, 'w') as file:
            file.writelines(new_lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write to the configuration file: {e}")
    
    try:
        subprocess.run([
            'ssh', '-i', '/app/teiren-test.pem',
            '-o', 'StrictHostKeyChecking=no',
            'ubuntu@3.35.81.217',
            'sudo systemctl restart fluentd'
        ], check=True)
        return {"status": "success", "message": "Fluentd service restarted successfully"}
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to restart Fluentd service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart Fluentd service: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
