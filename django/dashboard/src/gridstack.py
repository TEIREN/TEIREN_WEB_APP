from django.shortcuts import render, HttpResponse
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from . import gridstack_items as gitems
import json, types

def save_layout(request):
    from dashboard.src.models import GridLayout
    for check in GridLayout.objects.filter(name=request.POST['name']):
        check.delete()
    GridLayout(name=request.POST['name'], data=request.POST['data'], isDefault=request.POST['isDefault']).save()
    if request.POST['isDefault'] == '1':
        for check in GridLayout.objects.filter(name='default'):
            check.delete()
        GridLayout(name='default', data=request.POST['data'], isDefault=request.POST['isDefault']).save()
    layouts = GridLayout.objects.filter(name=request.POST['name'])
    if len(layouts) == 1:
        result = 'Saved Successfully'
    else:
        result = 'Failed To Save. Please Try Again'
    return HttpResponse(result)

def new_layout(request):
    from dashboard.src.models import GridLayout
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
    from dashboard.src.models import GridLayout
    try:
        layouts = GridLayout.objects.filter(name=request.POST['name'])
        for layout in layouts:
            items = json.loads(layout.data)
        for item in items:
            request_test = {'request': request}
            item['content'] = getattr(gitems, item['id'])(request_test)
        response = json.dumps(items)
    except Exception:
        return JsonResponse({}, status=400)
    return HttpResponse(response)

def delete_layout(request):
    from dashboard.src.models import GridLayout
    layouts = GridLayout.objects.filter(name=request.POST['name'])
    if len(layouts) < 1:
        return HttpResponse('Not Saved Layout')
    for layout in layouts:
        layout.delete()
    return HttpResponse('Deleted Successfully')

def list_layouts(request):
    from dashboard.src.models import GridLayout
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

def default_layout(request):
    if request.method == 'POST':
        items = json.loads(dict(request.POST.items())['layout'])
        try:
            for item in items:
                request_test = {'request': request}
                item['content'] = getattr(gitems, item['id'])(request_test)
            response = json.dumps(items)
        except Exception:
            return JsonResponse({}, status=400)
        return HttpResponse(response)