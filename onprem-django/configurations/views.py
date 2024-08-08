# from django.template.loader import render_to_string
# from django.shortcuts import render, redirect, HttpResponse
# from django.utils.decorators import method_decorator
# from django.contrib.auth import authenticate, login, logout
# from django.http import JsonResponse, HttpResponseRedirect
# from django.contrib.auth.decorators import login_required
# from configurations.src import account

from django.views import View
from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model, update_session_auth_hash, logout
from django.contrib.auth.hashers import make_password, check_password

from .forms import FinevoUserCreationForm


HTML_FILE_PATH = 'configurations'
@method_decorator(login_required, name='dispatch')
class AccountConfigView(View):
    def get(self, request):
        try:
            # print([user.__dict__ for user in get_user_model().objects.all()] )
            fields = ['username', 'email', 'date_joined', 'is_active', 'last_login']
            context = {
                'account_list': get_user_model().objects.values(*fields)
            }
            return render(request, f"{HTML_FILE_PATH}/account.html", context=context)
        except:
            return render(request, f"{HTML_FILE_PATH}/account.html")
    
    def post(self, request, config_action):
        try:
            response = getattr(self, config_action)(request=request)
            return response
        except Exception as e:
            if str(e):
                return HttpResponse(str(e))
            else:
                return HttpResponse('[Invalid Information] Please Try Again.')
    
    def register(self, request):
        try:
            post_data = request.POST.dict()
            if any(item == '' for item in post_data.values()):
                raise Exception(f'[Invalid Information] Please Insert All Properties.')
            form = FinevoUserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                user.password = make_password(post_data['password1'])
                user.save()
                return HttpResponse(f'Successfully Edited Account {user}')
            else:
                raise Exception(form.errors.as_text())
        except Exception as e:
            if str(e):
                raise Exception(str(e))
            else:
                raise Exception('[Account Register Fail] Invalid Information. Please Try Again.')
        
        
    def verify(self, request):
        try:
            username = request.POST.get('user_name', '')
            if not request.user.is_superuser and username != str(request.user):
                raise Exception("[Verification Fail] Different User's Information. Please Try Again.")
            password = request.POST.get('user_password', '')
            user = get_user_model().objects.filter(username=username).values('username', 'email', 'password').first()
            if user is not None and check_password(password, user['password']):
                user.pop('password')
                return render(request, f"{HTML_FILE_PATH}/account/edit.html", user)
            else:
                raise Exception('[Verification Fail] Invalid Information. Please Try Again.')
        except Exception as e:
            if str(e):
                raise Exception(str(e))
            else:
                raise Exception('[Verification Fail] Unknown Information. Please Try Again.')
        
    def update(self, request):
        try:
            post_data = request.POST.dict()
            og_username = post_data.pop('og_username', '')
            if any(item == '' for item in post_data.values()):
                raise Exception(f'[Invalid Information] Please Insert All Properties.')
            if request.user.is_superuser and str(request.user) != og_username:
                user = get_user_model().objects.filter(username=og_username).first()
                form = FinevoUserCreationForm(request.POST, instance=user)
                if form.is_valid():
                    new_user = form.save()
                    new_user.password = make_password(request.POST.get('password1'))
                    new_user.save()
                    return HttpResponse(f'Successfully Edited Account {og_username} to {new_user}')
                else:
                    raise Exception(form.errors.as_text())
            else:
                form = FinevoUserCreationForm(request.POST, instance=request.user)
                if form.is_valid():
                    user = form.save()
                    user.password = make_password(request.POST.get('password1'))
                    user.save()
                    update_session_auth_hash(request, user)
                    return HttpResponse(f'Successfully Edited Account {og_username} to {user}')
                else:
                    raise Exception(form.errors.as_text())
        except Exception as e:
            if str(e):
                print(e)
                raise Exception(str(e))
            else:
                raise Exception('[Account Edition Fail] Invalid Information. Please Try Again.')
    
    def delete(self, request):
        try:
            username = request.POST.get('username', '')
            if not request.user.is_superuser and username != request.user:
                raise Exception("[Verification Fail] Different User's Information. Please Try Again.")
            password = request.POST.get('password', '')
            user = get_user_model().objects.filter(username=username).first()
            if user is not None and check_password(password, user.password):
                user.delete()
                if user == request.user:
                    logout(request)
                return HttpResponse(f"Successfully Deleted Account {request.POST.get('username')}")
            else:
                raise Exception
        except Exception as e:
            if str(e):
                print(e)
                raise Exception(str(e))
            else:
                raise Exception('[Account Deletion Fail] Invalid Information. Please Try Again.')
    
    
    

# @login_required
# def dashboard_view(request):
#     if request.method == 'POST':
#         context = account.get_account_list()
#         return render(request, f"{HTML_FILE_PATH}/dashboard.html", context)
#     return render(request, f"{HTML_FILE_PATH}/dashboard.html")