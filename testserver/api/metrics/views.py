import json
from .models import Metrics

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


# AWS Lambda, api-gateway API TESTING #
@csrf_exempt
@require_POST # Only recived Post
def receive(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            uuid = request.META.get('HTTP_UUID')
            Metrics.objects.create(
                uuid=uuid,
                cpu=data['cpu'],
                memory=data['memory'],
                disk_usage=data['disk_usage'],
                
                read_count=data['disk_io']['read_count'],
                write_count=data['disk_io']['write_count'],
                
                read_bytes=data['disk_io']['read_bytes'],
                write_bytes=data['disk_io']['write_bytes'],
                read_time=data['disk_io']['read_time'],
                write_time=data['disk_io']['write_time'],
                
                read_merged_count=data['disk_io']['read_merged_count'],
                write_merged_count=data['disk_io']['write_merged_count'],
                busy_time=data['disk_io']['busy_time'],
                
                bytes_sent=data['net_io']['bytes_sent'],
                bytes_recv=data['net_io']['bytes_recv'],
                packets_sent=data['net_io']['packets_sent'],
                packets_recv=data['net_io']['packets_recv'],
                
                errin=data['net_io']['errin'],
                errout=data['net_io']['errout'],
                dropin=data['net_io']['dropin'],
                dropout=data['net_io']['dropout'],
                
                instance_id=data['instance-id'],
                instance_type=data['instance-type'],
                public_ipv4=data['public-ipv4'],
                local_ipv4=data['local-ipv4']
            )
            # print(f"  Metrics Recived Alerm")
            # print(f"  USER:        [{data['uuid']}]")
            # print(f"  Instance ID: [{data['instance-id']}]")
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError as e:
            # JSON 디코딩 오류 처리
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'message': 'Invaild Method'})

def get_metric_data(request, instance_id):
    print(f"instance ID is: {instance_id}")
    try:
        metrics = list(Metrics.objects.filter(instance_id=instance_id).values())
    except Exception as e:
        print(e)
    print(f"metrics data: {metrics}")
    return JsonResponse(metrics, safe=False)

from django.db.models import Max
from django.utils import timezone
import datetime

def get_all_metrics(request, uuid):
    ten_min_ago = timezone.now() - datetime.timedelta(minutes=1)

    # 지난 10분 동안의 사용자 UUID에 해당하는 메트릭 데이터 가져오기
    metrics_data = Metrics.objects.filter(timestamp__gte=ten_min_ago, user_uuid=uuid)
    
    latest_metrics = {}
    for metric in metrics_data:
        if metric.instance_id not in latest_metrics:
            latest_metrics[metric.instance_id] = []
        latest_metrics[metric.instance_id].append({
            'instance_id': metric.instance_id,
            'cpu': metric.cpu,
            'memory': metric.memory,
            'disk_usage': metric.disk_usage,
            # 추가 필드...
            'timestamp': metric.timestamp
        })

    # latest_metrics는 이제 각 instance_id에 대한 메트릭 리스트를 포함하는 dict입니다.
    # JsonResponse로 변환하기 위해 리스트로 변경합니다.
    metrics_list = [metrics for metrics in latest_metrics.values()]

    print(f"Metrics Type is: {type(metrics_list)}")
    return JsonResponse(metrics_list, safe=False)

def get_metrics_by_uuid(request, uuid):
    ten_min_ago = timezone.now() - datetime.timedelta(minutes=1)

    # 지난 10분 동안의 사용자 UUID에 해당하는 메트릭 데이터 가져오기
    metrics_data = Metrics.objects.filter(timestamp__gte=ten_min_ago, uuid=uuid)
    
    latest_metrics = {}
    for metric in metrics_data:
        if metric.instance_id not in latest_metrics:
            latest_metrics[metric.instance_id] = []
        latest_metrics[metric.instance_id].append({
            'instance_id': metric.instance_id,
            'cpu': metric.cpu,
            'memory': metric.memory,
            'disk_usage': metric.disk_usage,
            'timestamp': metric.timestamp
        })

    # latest_metrics는 이제 각 instance_id에 대한 메트릭 리스트를 포함하는 dict입니다.
    # JsonResponse로 변환하기 위해 리스트로 변경합니다.
    metrics_list = [metrics for metrics in latest_metrics.values()]
    return JsonResponse(metrics_list, safe=False)
    
def show_metrics(request):
    latest_metrics = Metrics.objects.last()
    return render(request, 'metrics.html', {'metrics': latest_metrics})