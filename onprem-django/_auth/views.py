from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, HttpResponse
from django.http.response import JsonResponse

from django.core.exceptions import ObjectDoesNotExist


def login_(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                # session
                request.session['user_id'] = username
                if next_url is not None:
                    return redirect(next_url)
                else:
                    return redirect('/dashboard/')
            else:
                raise Exception
        except:
            messages.warning(request, 'Username or Password is incorrect. Please try again')
            return render(request, 'auth/login.html')
    return render(request, 'auth/finevo/login.html')


def logout_(request):
    logout(request)
    return redirect('/auth/login/')