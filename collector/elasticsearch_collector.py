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
import socket

es = Elasticsearch("http://3.35.81.217:9200/")
should_stop = {}
log_collection_started = {}

app = FastAPI()

conf_file_path = '/etc/fluent/fluentd.conf'

# Elasticsearch 인덱스 매핑 설정 함수
async def create_index_with_mapping(index_name, mapping):
    try:
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name, body={"mappings": mapping})
    except Exception as e:
        logging.error(f"Failed to create index with mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create index with mapping: {e}")

# 인덱스가 존재하지 않으면 생성하는 함수
async def create_index_if_not_exists(index_name):
    try:
        es.indices.get(index=index_name)
    except NotFoundError:
        es.indices.create(index=index_name)

# ElasticSearch에 로그를 입력하는 함수
async def elasticsearch_input(log, system, TAG_NAME):
    index_name = f"test_{system}_syslog"  # 인덱스 이름 설정
    log['TAG_NAME'] = TAG_NAME  # 로그에 TAG_NAME 추가
    response = es.index(index=index_name, document=log)
    print(f"{system}_log: {response['result']}")
    return 0

# API 키를 저장하는 함수
async def save_api_key(system, TAG_NAME, config):
    index_name = "userinfo"
    await create_index_if_not_exists(index_name)
    log = {
        "SYSTEM": system,
        "TAG_NAME": TAG_NAME,
        "inserted_at": datetime.now(),
        "config": config
    }
    response = es.index(index=index_name, document=log)
    print(f"{index_name}_log: {response['result']}")
    return response

# API 키를 업데이트하는 함수
async def update_api_key(system, TAG_NAME, config):
    index_name = "userinfo"
    await create_index_if_not_exists(index_name)
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"SYSTEM": system}},
                    {"match": {"TAG_NAME": TAG_NAME}}
                ]
            }
        }
    }
    try:
        res = es.search(index=index_name, body=query)
        if res['hits']['total']['value'] > 0:
            doc_id = res['hits']['hits'][0]['_id']
            log = {
                "SYSTEM": system,
                "TAG_NAME": TAG_NAME,
                "inserted_at": datetime.now(),
                "config": config
            }
            response = es.index(index=index_name, id=doc_id, document=log)
            print(f"{index_name}_log: {response['result']}")
            return response
        else:
            raise HTTPException(status_code=404, detail="TAG_NAME not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API를 삭제하는 함수
async def delete_api_key(system, TAG_NAME):
    index_name = "userinfo"
    await create_index_if_not_exists(index_name)
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"SYSTEM": system}},
                    {"match": {"TAG_NAME": TAG_NAME}}
                ]
            }
        }
    }
    try:
        res = es.search(index=index_name, body=query)
        if res['hits']['total']['value'] > 0:
            doc_id = res['hits']['hits'][0]['_id']
            response = es.delete(index=index_name, id=doc_id)
            print(f"{index_name}_log: {response['result']}")
            return response
        else:
            raise HTTPException(status_code=404, detail="TAG_NAME not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 호스트 이름을 얻는 함수
def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception as e:
        logging.error(f"Failed to get hostname: {e}")
        return "unknown"

# 요청 객체 모델
class UpdateAPIKeyRequest(BaseModel):
    api_key: str
    TAG_NAME: str

class DeleteAPIKeyRequest(BaseModel):
    TAG_NAME: str

# 엔드포인트 정의
@app.post("/linux_log")
async def receive_log(request: Request):
    log_request = await request.json()
    client_ip = request.client.host
    client_hostname = get_hostname(client_ip)

    for log in log_request:
        log['teiren_request_ip'] = client_ip
        log['client_hostname'] = client_hostname
        await elasticsearch_input(log, 'linux', client_hostname)

    config = {
        "client_ip": client_ip,
        "client_hostname": client_hostname
    }
    await save_api_key("linux", client_hostname, config)

    return {"message": "Log received successfully"}

@app.post("/stop_linux_log")
async def stop_linux_log(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = True
        return {"message": f"{request.TAG_NAME} 로그 수집이 중지되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/resume_linux_log")
async def resume_linux_log(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = False
        return {"message": f"{request.TAG_NAME} 로그 수집이 재개되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post('/win_log')
async def win_log(request: Request):
    log_request = await request.json()
    client_ip = request.client.host
    client_hostname = get_hostname(client_ip)

    # 인덱스 생성 시 매핑을 설정하도록 호출
    await create_index_with_mapping("test_window_syslog", {
        "properties": {
            "date": {
                "type": "scaled_float",
                "scaling_factor": 10000000  # 7자리까지 인식 가능하도록 설정
            }
        }
    })

    for log in log_request:
        log = {k.lower(): v for k, v in log.items()}
        log['teiren_request_ip'] = client_ip
        log['client_hostname'] = client_hostname
        # Convert 'date' field to scaled_float
        if 'date' in log:
            log['date'] = round(log['date'], 7)
        await elasticsearch_input(log, 'window', client_hostname)

    config = {
        "client_ip": client_ip,
        "client_hostname": client_hostname
    }
    await save_api_key("window", client_hostname, config)

    return {"message": "Log received successfully"}

@app.post("/stop_win_log")
async def stop_win_log(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = True
        return {"message": f"{request.TAG_NAME} 로그 수집이 중지되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/resume_win_log")
async def resume_win_log(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = False
        return {"message": f"{request.TAG_NAME} 로그 수집이 재개되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post('/genian_log')
async def genian_log(request: Request):
    log_request = await request.json()
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        log['teiren_stamp'] = datetime.now()
        await elasticsearch_input(log, 'genian', 'genian_api')

    return {"message": "Log received successfully"}

@app.get("/genian_api_send")
async def get_genian_logs(api_key: str = None, TAG_NAME: str = None, page: int = 1, page_size: int = 30, background_tasks: BackgroundTasks = None):
    if not api_key or not TAG_NAME:
        return {"error": "API 키와 이름이 필요합니다."}
    global log_collection_started
    global should_stop
    log_collection_started[TAG_NAME] = True
    should_stop[TAG_NAME] = False
    logs = []
    while True:
        new_logs = get_logs(api_key, page, page_size)
        if not new_logs:
            break
        logs.extend(new_logs)
        page += 1

    background_tasks.add_task(continue_log_collection, api_key, "genian", TAG_NAME)
    await save_api_key("genian", TAG_NAME, {"api_key": api_key})

    return {"message": f"{TAG_NAME} 로그 수집이 시작되었습니다."}

@app.post("/update_genian_api_key")
async def update_genian_api_key(request: UpdateAPIKeyRequest):
    response = await update_api_key("genian", request.TAG_NAME, {"api_key": request.api_key})
    return {"result": response['result']}

@app.post("/delete_genian_api_key")
async def delete_genian_api_key(request: DeleteAPIKeyRequest):
    response = await delete_api_key("genian", request.TAG_NAME)
    return {"result": response['result']}

def continue_log_collection(api_key, system, TAG_NAME):
    while not should_stop[TAG_NAME]:
        if system == "genian":
            send_genian_logs(api_key)
        elif system == "fortigate":
            send_fortigate_logs(api_key)
        elif system == "mssql":
            send_mssql_logs(api_key)
        time.sleep(5)

@app.post("/stop_genian_api_send")
async def stop_genian_api_send(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = True
        return {"message": f"{request.TAG_NAME} 로그 수집이 중지되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/resume_genian_api_send")
async def resume_genian_api_send(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = False
        return {"message": f"{request.TAG_NAME} 로그 수집이 재개되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post('/fortigate_log')
async def fortigate_log(request: Request):
    log_request = await request.json()
    for log in log_request:
        log['teiren_request_ip'] = request.client.host
        await elasticsearch_input(log, 'fortigate', 'fortigate_api')
    return {"message": "Log received successfully"}

@app.get("/fortigate_api_send")
async def get_fortigate_log(api_key: str = None, TAG_NAME: str = None, background_tasks: BackgroundTasks = None):
    if not api_key or not TAG_NAME:
        return {"error": "API 키와 이름이 필요합니다."}

    global log_collection_started
    global should_stop
    log_collection_started[TAG_NAME] = True
    should_stop[TAG_NAME] = False

    background_tasks.add_task(continue_log_collection, api_key, "fortigate", TAG_NAME)
    await save_api_key("fortigate", TAG_NAME, {"api_key": api_key})

    return {"message": f"{TAG_NAME} 로그 수집이 시작되었습니다."}

@app.post("/update_fortigate_api_key")
async def update_fortigate_api_key(request: UpdateAPIKeyRequest):
    response = await update_api_key("fortigate", request.TAG_NAME, {"api_key": request.api_key})
    return {"result": response['result']}

@app.post("/delete_fortigate_api_key")
async def delete_fortigate_api_key(request: DeleteAPIKeyRequest):
    response = await delete_api_key("fortigate", request.TAG_NAME)
    return {"result": response['result']}

@app.post("/stop_fortigate_api_send")
async def stop_fortigate_api_send(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = True
        return {"message": f"{request.TAG_NAME} 로그 수집이 중지되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/resume_fortigate_api_send")
async def resume_fortigate_api_send(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = False
        return {"message": f"{request.TAG_NAME} 로그 수집이 재개되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/log_collection_status")
async def get_log_collection_status(request: DeleteAPIKeyRequest):
    if request.TAG_NAME not in log_collection_started:
        raise HTTPException(status_code=400, detail="Invalid TAG_NAME")
    status = "로그 수집이 진행중입니다." if log_collection_started[request.TAG_NAME] and not should_stop[request.TAG_NAME] else "로그 수집이 중지되었습니다."
    return {"status": status}

@app.post('/mssql_log')
async def mssql_log(request: Request):
    log = await request.form()
    log_dict = {key: log[key] for key in log.keys()}
    log_dict['teiren_request_ip'] = request.client.host
    print(log_dict)
    await elasticsearch_input(log_dict, 'mssql', 'mssql_api')
    return {"message": "Log received successfully"}

class StartMSSQLCollectionRequest(BaseModel):
    server: str
    database: str
    username: str
    password: str
    table_name: str
    TAG_NAME: str

@app.post("/start_mssql_collection")
async def start_mssql_collection(request: StartMSSQLCollectionRequest, background_tasks: BackgroundTasks = None):
    config = {
        "server": request.server,
        "database": request.database,
        "username": request.username,
        "table_name": request.table_name
    }
    background_tasks.add_task(send_mssql_logs, request.server, request.database, request.username, request.password, request.table_name)
    await save_api_key("mssql", request.TAG_NAME, config)
    return {"message": "MSSQL 로그 수집이 시작되었습니다."}

@app.post("/stop_mssql_api_send")
async def stop_mssql_api_send(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = True
        return {"message": f"{request.TAG_NAME} 로그 수집이 중지되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/resume_mssql_api_send")
async def resume_mssql_api_send(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = False
        return {"message": f"{request.TAG_NAME} 로그 수집이 재개되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/update_mssql_api_key")
async def update_mssql_api_key(request: UpdateAPIKeyRequest):
    response = await update_api_key("mssql", request.TAG_NAME, {"api_key": request.api_key})
    return {"result": response['result']}

@app.post("/delete_mssql_api_key")
async def delete_mssql_api_key(request: DeleteAPIKeyRequest):
    response = await delete_api_key("mssql", request.TAG_NAME)
    return {"result": response['result']}

class FluentdConfig(BaseModel):
    new_protocol: str
    new_source_ip: str
    new_dst_port: str
    new_log_tag: str

@app.post("/add_config/")
async def add_config(config: FluentdConfig):
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
        await save_api_key("fluentd", config.new_log_tag, config.dict())
        return {"status": "success", "message": "Fluentd service restarted successfully"}
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to restart Fluentd service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart Fluentd service: {e}")

@app.post("/delete_tag/")
async def delete_tag(request: DeleteAPIKeyRequest):
    tag_to_delete = request.TAG_NAME
    
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
        await delete_api_key("fluentd", tag_to_delete)
        return {"status": "success", "message": "Fluentd service restarted successfully"}
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to restart Fluentd service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart Fluentd service: {e}")

@app.post("/stop_fluentd_api_send")
async def stop_fluentd_api_send(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = True
        return {"message": f"{request.TAG_NAME} 로그 수집이 중지되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/resume_fluentd_api_send")
async def resume_fluentd_api_send(request: DeleteAPIKeyRequest):
    global should_stop
    if request.TAG_NAME in should_stop:
        should_stop[request.TAG_NAME] = False
        return {"message": f"{request.TAG_NAME} 로그 수집이 재개되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="TAG_NAME not found")

@app.post("/update_fluentd_api_key")
async def update_fluentd_api_key(request: FluentdConfig):
    tag_to_update = request.new_log_tag
    config = {
        "new_protocol": request.new_protocol,
        "new_source_ip": request.new_source_ip,
        "new_dst_port": request.new_dst_port,
        "new_log_tag": request.new_log_tag
    }
    await update_api_key("fluentd", tag_to_update, config)
    return {"status": "success", "message": f"{tag_to_update} 설정이 업데이트 되었습니다."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

