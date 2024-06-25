# local
import json, types
from . import gridstack_items as gitems
from .gridstack_items import DashboardHandler
from dashboard.src.models import GridLayout
import traceback
# django
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model

def save_layout(request):
    if request.method == 'POST':
        data = request.POST
        user = get_user_model().objects.get(username=request.session.get('user_id'))
        user_layout = user.user_layout
        for check in GridLayout.objects.filter(name=request.POST['name']):
            check.delete()
        GridLayout(name=request.POST['name'], data=request.POST['data'], isDefault=request.POST['isDefault']).save()
        if request.POST['isDefault'] == '1':
            for check in GridLayout.objects.filter(name='default'):
                check.delete()
            GridLayout(name='default', 
                       user_uuid=user.uuid,
                       data=request.POST['data'], 
                       isDefault=request.POST['isDefault']).save()
        layouts = GridLayout.objects.filter(name=request.POST['name'])
        if len(layouts) == 1:
            result = 'Saved Successfully'
        else:
            result = 'Failed To Save. Please Try Again'
        return HttpResponse(result)
    return False

def new_layout(request):
    try:
        if len(GridLayout.objects.filter(name=request.POST['name'])) > 0:
            return HttpResponse('Already Existing Name')
    finally:
        layout = GridLayout(name=request.POST['name'], data=request.POST['data'])
        layout.save()
        layouts = GridLayout.objects.filter(name=request.POST['name'])
        if len(layouts) == 1:
            result = 'Saved Successfully'
        else:
            result = 'Failed To Save. Please Try Again'
        return HttpResponse(result)

def load_layout(request):
    request_test = {'request': request}
    dhandler = DashboardHandler(request_test)
    # 1.User DB에 default_layout 저장
    # 2.layout 디비에는 사용자의 uuid를 pk로, 여러 레이아웃 저장
    # 3.레이아웃 불라오는건 default_layout 불러오기
    
    try:
        print("==> load layout")
        layouts = GridLayout.objects.filter(name=request.POST['name'])
        for layout in layouts:
            items = json.loads(layout.data)
        items:list = json.loads(layouts[0]) # ==> unique data
        
        for item in items:
            if item['id'] == 'logTotal':
                item['content'] = dhandler.logTotal()
                continue
            if item['id'] == 'integrationTotal':
                item['content'] = dhandler.integrationTotal()
                continue
            if item['id'] == 'threatlogTotal':
                item['content'] = dhandler.threatlogTotal()
                continue
            if item['id'] == 'threatRatio':
                item['content'] = dhandler.threatRatio()
                continue
            if item['id'] == 'recentCollectedOverview':
                item['content'] = dhandler.recentCollectedOverview()
                continue
            if item['id'] == 'threatRule':
                item['content'] = dhandler.threatRule()
                continue
            if item['id'] == 'threatUser':
                item['content'] = dhandler.threatUser()
                continue
            if item['id'] == 'threatLevel':
                item['content'] = dhandler.threatLevel()
                continue
            if item['id'] == 'threatDetectionOverview':
                item['content'] = dhandler.threatDetectionOverview()
                continue
            if item['id'] == 'threatIp':
                item['content'] = dhandler.threatIp()
                continue
            if item['id'] == 'threatEquipment':
                item['content'] = dhandler.threatEquipment()
                continue
            if item['id'] == 'threatSenario':
                item['content'] = dhandler.threatSenario()
                continue
            if item['id'] == 'graphitem':
                item['content'] = dhandler.graphitem()
                continue
            if item['id'] == 'recentDetection':
                item['content'] = dhandler.recentDetection()
                continue
        response = json.dumps(items)
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({}, status=400)
    return HttpResponse(response)

def delete_layout(request):
    layouts = GridLayout.objects.filter(name=request.POST['name'])
    if len(layouts) < 1:
        return HttpResponse('Not Saved Layout')
    for layout in layouts:
        layout.delete()
    return HttpResponse('Deleted Successfully')

def list_layouts(request):
    if request.method == 'POST':
        names = list(GridLayout.objects.values_list('name', flat=True))
        if 'default' in names:
            names.remove('default')
        return JsonResponse(names, safe=False)

def add_item(request, type) -> json:
    if request.method == 'POST':
        return getattr(gitems, type)(request)

def list_items(request):
    if request.method == 'POST':
        items = []
        for name, obj in vars(gitems).items():
            if isinstance(obj, types.FunctionType):
                if not any(x in name for x in ['render', '_', 'graph']):
                    items.append(name)
        response = {'items': items}
        return JsonResponse(response)

import traceback
def default_layout(request):
    if request.method == 'POST':
        request_test = {'request': request}
        items = json.loads(dict(request.POST.items())['layout'])
        try:
            print('===> default layout')
            with DashboardHandler(request_test) as dhandler:
                for item in items:
                    if item['id'] == 'logTotal':
                        item['content'] = dhandler.logTotal()
                        continue
                    if item['id'] == 'integrationTotal':
                        item['content'] = dhandler.integrationTotal()
                        continue
                    if item['id'] == 'threatlogTotal':
                        item['content'] = dhandler.threatlogTotal()
                        continue
                    if item['id'] == 'threatRatio':
                        item['content'] = dhandler.threatRatio()
                        continue
                    if item['id'] == 'recentCollectedOverview':
                        item['content'] = dhandler.recentCollectedOverview()
                        continue
                    if item['id'] == 'threatRule':
                        item['content'] = dhandler.threatRule()
                        continue
                    if item['id'] == 'threatUser':
                        item['content'] = dhandler.threatUser()
                        continue
                    if item['id'] == 'threatLevel':
                        item['content'] = dhandler.threatLevel()
                        continue
                    if item['id'] == 'threatDetectionOverview':
                        item['content'] = dhandler.threatDetectionOverview()
                        continue
                    if item['id'] == 'threatIp':
                        item['content'] = dhandler.threatIp()
                        continue
                    if item['id'] == 'threatEquipment':
                        item['content'] = dhandler.threatEquipment()
                        continue
                    if item['id'] == 'threatSenario':
                        item['content'] = dhandler.threatSenario()
                        continue
                    if item['id'] == 'graphitem':
                        item['content'] = dhandler.graphitem()
                        continue
                    if item['id'] == 'recentDetection':
                        item['content'] = dhandler.recentDetection()
                        continue
                    
                # for item in items:
                #     print(item)
                response = json.dumps(items)
        except Exception:
            traceback_message = traceback.format_exc()
            print(f"error is {traceback_message}")
            return JsonResponse({}, status=400)
        return HttpResponse(response)