import requests
from datetime import datetime
import json

requests.packages.urllib3.disable_warnings()

fortigate_ip = '3.25.48.75'
post_url = "http://localhost:8088/fortigate_log"

base_url = f"https://{fortigate_ip}"

def send_fortigate_logs(api_key):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    log_endpoints = [
        "/api/v2/log/disk/event/system/raw",
        "/api/v2/log/disk/traffic/local/raw",
        "/api/v2/log/disk/traffic/forward/raw"
    ]

    params = {
        "rows": 100,
        "start": 0
    }

    parsed_logs = []
    for log_endpoint in log_endpoints:
        response = requests.get(f"{base_url}{log_endpoint}", headers=headers, params=params, verify=False)
        log_entries = response.text.strip().split('\n')
        for log_entry in log_entries:
            parsed_logs.append(parse_fortigate_log(log_entry))

    response = requests.post(post_url, json=parsed_logs)
    print("Response:", response.status_code)

def parse_fortigate_log(log_entry):
    log_data = {}
    pairs = log_entry.split(' ')
    for pair in pairs:
        parts = pair.split('=')
        if len(parts) == 2:
            key, value = parts
            log_data[key] = value.strip('"')
        elif len(parts) > 2:
            key = parts[0]
            value = '='.join(parts[1:])
            log_data[key] = value.strip('"')
    return log_data

# fortigate syslog udp/tcp 수집 시 파싱
async def fortigate_parse(log:str):
    clean_log = log[log.find('>') + 1:]
    log_dict = {}
    for item in clean_log.split(' '):
        if '=' in item:
            key, value = item.split('=', 1)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            log_dict[key] = value
    return log_dict