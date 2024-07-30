from django.http import JsonResponse
import json
import requests


def transmission_insert(request):
    if request.method == 'POST':
        try:
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
            if not all([protocol, source_ip, dst_port, log_tag]):
                return "모든 필드를 입력하세요."
            response = requests.post(
                'http://3.35.81.217:8088/add_config/',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(data)
            )
            if response.status_code == 200:
                return "Configuration added and Fluentd service restarted successfully."
            else:
                return "Failed to add configuration."
        except Exception as error:
            return error
    else:
        return "잘못된 요청입니다. 다시 시도해주세요."