from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from auth.src import register, authentication
from django.conf import settings
from py2neo import Graph

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

def login_view(request):
    if 1 > graph.evaluate("MATCH (a:Teiren:Account) RETURN COUNT(a)"):
        return redirect('/auth/register/')
    if request.method == 'POST':
        data = dict(request.POST.items())
        username, password = authentication.login_account(data, get_client_ip(request))
        if username == 'fail':
            data['error'] = password
            return render(request, 'auth/login.html', data)
        elif password == 'fail':
            data['error'] = f"Failed To Login. Please Try Again ({username} out of 5)"
            return render(request, 'auth/login.html', data)
        else:
            user = authenticate(request, username=username, password=password)
            if user is None:
                new_user = User.objects.create_user(username=username, password=password)
                new_user.set_password(password)
                new_user.save()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url is not None:
                return redirect(next_url)
            else:
                return redirect('/')
        else:
            data['error'] = "Failed To Login. Please Try Again"
            return render(request, 'auth/login.html', data)
    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('/auth/login/?next=/')

def register_view(request):
    context = {'color': 'teiren', 'message': ['Create Your Account', 'TEIREN CLOUD']}
    if request.method == "POST":
        data = dict(request.POST.items())
        message = register.check_account(data)
        if message == 'check':
            if register.register_account(data, get_client_ip(request)) == 'success':
                context = {'color': 'teiren', 'message': 'Register Success! Please Sign In'}
                return render(request, 'auth/register.html', context)
            else:
                message = "Fail To Register. Please Try Again"
        context = {'color': 'danger', 'message': message}
        context.update(data)
    return render(request, 'auth/register.html', context)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
    