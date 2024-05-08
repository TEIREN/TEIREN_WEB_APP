from django.shortcuts import render, HttpResponse
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from TeirenSIEM.models import GridLayout
from . import gridstack_items as gitems
import json, types

def save_layout(request):
    for check in GridLayout.objects.filter(name=request.POST['name']):
        check.delete()
    GridLayout(name=request.POST['name'], data=request.POST['data'], isDefault=request.POST['isDefault']).save()
    if request.POST['isDefault'] == '1':
        for check in GridLayout.objects.filter(name='default'):
            check.delete()
        GridLayout(name='default', data=request.POST['data'], isDefault=request.POST['isDefault']).save()
    layouts = GridLayout.objects.filter(name=request.POST['name'])
    if len(layouts) == 1:
        result = '정상적으로 저장되었습니다.'
    else:
        result = '오류가 발생했습니다. 다시 시도해주세요.'
    return HttpResponse(result)

def new_layout(request):
    if len(GridLayout.objects.filter(name=request.POST['name'])) > 0:
        return HttpResponse('이미 저장된 이름입니다.')
    layout = GridLayout(name=request.POST['name'], data=request.POST['data'])
    layout.save()
    layouts = GridLayout.objects.filter(name=request.POST['name'])
    if len(layouts) == 1:
        result = '정상적으로 저장되었습니다.'
    else:
        result = '오류가 발생했습니다. 다시 시도해주세요.'
    return HttpResponse(result)

def load_layout(request):
    layouts = GridLayout.objects.filter(name=request.POST['name'])
    for layout in layouts:
        items = json.loads(layout.data)
    for item in items:
        request_test = {'request': request}
        item['content'] = getattr(gitems, item['id'])(request_test)
    response = json.dumps(items)
    return HttpResponse(response)

def delete_layout(request):
    layouts = GridLayout.objects.filter(name=request.POST['name'])
    if len(layouts) < 1:
        return HttpResponse('저장되지 않은 레이아웃입니다.')
    for layout in layouts:
        layout.delete()
    return HttpResponse('정상적으로 삭제되었습니다.')

def list_layouts(request):
    if request.method == 'POST':
        names = list(GridLayout.objects.values_list('name', flat=True))
        if 'default' in names:
            names.remove('default')
        return JsonResponse(names, safe=False)

def add_item(request, type):
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
