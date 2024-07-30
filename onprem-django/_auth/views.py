# local
from .forms import CustomUserCreationForm
from .src.mail import send_mail
from .src.initial import InitDatabase
from .src.authentication import login_success
from _auth.src import authentication
from common.neo4j.handler import Neo4jHandler, Cypher

# django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect, HttpResponse
## Excpetion
from django.core.exceptions import ObjectDoesNotExist

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']

def login_(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        try:
            user = get_user_model().objects.get(username=username)
        except ObjectDoesNotExist:
            # 사용자가 없는경우
            messages.warning(request, 'Username or Password is incorrect. Please try again')
            return render(request, 'auth/login.html')
            
        user_is_active = user.is_active
        if not user_is_active:
            messages.warning(request, 'Please log in after verifying your email.')
            return render(request, 'auth/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            # session
            request.session['user_id'] = username
            request.session['uuid'] = str(user.uuid)
            request.session['db_name'] = str(user.db_name)
            if next_url is not None:
                # graph db에 저장
                login_success(userName=username, srcip=_get_client_ip(request), db_name=user.db_name)
                return redirect(next_url)
            else:
                return redirect('/dashboard/')
            
        else:
            # 로그인 실패한 경우
            messages.warning(request, 'Username or Password is incorrect. Please try again')
            return render(request, 'auth/login.html')
        
    return render(request, 'auth/login.html')

def logout_(request):
    logout(request)
    return redirect('/auth/login/?next=/')

import uuid
def register_(request):
    context = {'color': 'teiren', 'message': ['Create Your Account', 'TEIREN CLOUD']}
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the user form
            uuid_ = uuid.uuid4()
            
            user = form.save(commit=False)
            user.uuid = uuid_
            user.db_name = f"t{str(uuid_)}"
            user.email = request.POST.get('email')
            user.user_layout = 'default'
            user.is_active = False
            user.is_staff = False
            user.is_superuser = False
            user.save()
                
            if send_mail(request.POST, user):
                messages.success(request, 'Registration is complete. Please log in after email verification!')
                return render(request, 'auth/register.html', context)
            else:
                messages.warning(request, {'mail': 'fail to send mail'})
        
        else:
            # 폼이 유효하지 않은 경우 에러 메시지를 표시
            for field, errors in form.errors.items():
                for error in errors:
                    if field == 'password1':
                        field = 'password'
                    elif field == 'password2':
                        field = 'password verification'
                    messages.warning(request, f'{field.title()}: {error}')
                
    return render(request, 'auth/register.html', context)

# 이메일 인증 view
def activate_(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
        # 토큰 검증
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            # 메일 인증 이후, neo4j에 사용자 테이블 생성
            try:
                neohandler = Neo4jHandler()
                neohandler.create_database(user.db_name)
                neohandler.close()
            except Exception as e:
                print(f"neo4j: can't create database: {e}")
            
            if init_database(user.db_name):
                print('neo4j: Create Done.')
            else:
                print('neo4j: Can not write database.')
            
            # neo4j 데이터베이스에 저장
            cypher = Cypher()
            cypher.push_user(user, _get_client_ip(request))
            cypher.close()
            return render(request, 'registration/activation_success.html')
        else:
            return render(request, 'registration/activation_failure.html')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, 'registration/activation_failure.html')

def init_database(db_name):
    with InitDatabase(db_name) as __init:
        try:
            if not __init.compliance():
                return False
            if not __init.product():
                return False
            if not __init.product_2():
                return False
            if not __init.isms_p_mapping():
                return False
            if not __init.gdpr():
                return False
            if not __init.super_node():
                return False
            if not __init.sub_node():
                return False
            if not __init.detect_node():
                return False
        except Exception as e:
            print(e)
    return True

def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
    