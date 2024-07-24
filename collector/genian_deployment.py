import requests
from datetime import datetime
import json
import time
from fastapi import Request, BackgroundTasks

NAC_URL = 'https://10.214.26.251/mc2/rest/logs'
POST_URL = "http://localhost:8088/genian_log"

def get_logs(api_key, page=1, page_size=30):
    """Genian NAC 감사로그 조회"""
    url = f"{NAC_URL}?page={page}&pageSize={page_size}&logschema=auditlog&periodType=custom&apiKey={api_key}"
    headers = {
        'accept': 'application/json;charset=UTF-8',
    }
    response = requests.get(url, headers=headers, verify=False)
    return response.json()['result']


def parse_log(log):
    timestamp = datetime.fromtimestamp(log['LOG_TIME'] / 1000).isoformat()
    event_type = log['LOG_TYPESTR']
    ip_address = log['LOG_IP']
    mac_address = log['LOG_MAC']
    detail = log['LOG_DETAIL']
    log_id = log['LOG_LOGIDSTR']
    extra_info = log['LOG_EXTRAINFO']
    user_id = log['LOG_USERID']
    username = log['LOG_USERNAME']
    dept_name = log['LOG_DEPTNAME']
    parent_name = log['LOG_PARENTNAME']
    msg = log['LOG_MSG']
    log_type = log['LOG_TYPE']
    log_parent_id = log['LOG_PARENTID']
    log_ip6str = log['LOG_IP6STR']

    # 위험도 판단 기준
    if 'ERROR' in msg or 'ANOMALY' in msg or 'WARN' in msg:
        risk_level = 'High'
    elif log_type == '2':
        risk_level = 'Medium'
    else:
        risk_level = 'Low'

    return {
        '@timestamp': timestamp,
        'event_type': event_type,
        'ip_address': ip_address,
        'mac_address': mac_address,
        'detail': detail,
        'log_id': log_id,
        'extra_info': extra_info,
        'user_id': user_id,
        'username': username,
        'dept_name': dept_name,
        'parent_name': parent_name,
        'msg': msg,
        'log_type': log_type,
        'log_parent_id': log_parent_id,
        'log_ip6str': log_ip6str,
        'risk_level': risk_level
    }


def send_genian_logs(api_key):
    logs = get_logs(api_key)
    parsed_logs = [parse_log(log) for log in logs]
    response = requests.post(POST_URL, json=parsed_logs)
    print("Response:", response.status_code)
