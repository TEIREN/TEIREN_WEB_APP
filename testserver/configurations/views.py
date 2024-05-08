from django.template.loader import render_to_string
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from configurations.src import account

HTML_FILE_PATH = 'configurations'

@login_required
def account_view(request):
    if request.method == 'POST':
        context = account.get_account_list()
        return render(request, f"{HTML_FILE_PATH}/account.html", context)
    return render(request, f"{HTML_FILE_PATH}/account.html")

@login_required
def dashboard_view(request):
    if request.method == 'POST':
        context = account.get_account_list()
        return render(request, f"{HTML_FILE_PATH}/dashboard.html", context)
    return render(request, f"{HTML_FILE_PATH}/dashboard.html")

@login_required
def account_config(request, config_type):
    if request.method == 'POST':
        data = dict(request.POST.items())
        if config_type == 'verify':
            context = account.verify_account(data)
            if not isinstance(context, str):
                return render(request, f"{HTML_FILE_PATH}/account/edit.html", context)
        elif config_type == 'edit':
            context = account.edit_account(data)
        elif config_type == 'delete':
            context = account.delete_account(data)
            if context == 'Deleted Account Successfully':
                if data['user_name'] == request.user.username:
                    return HttpResponse('reload')
        return HttpResponse(context)