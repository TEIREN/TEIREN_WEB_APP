# from django.template.loader import render_to_string
# from django.shortcuts import render, redirect, HttpResponse
# from django.utils.decorators import method_decorator
# from django.contrib.auth import authenticate, login, logout
# from django.http import JsonResponse, HttpResponseRedirect
# from django.contrib.auth.decorators import login_required
# from configurations.src import account

from django.views import View
from django.shortcuts import render, HttpResponse
from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.hashers import make_password, check_password

from .src import account
from _auth.forms import FinevoUserCreationForm

HTML_FILE_PATH = 'configurations'
@method_decorator(login_required, name='dispatch')
class AccountConfigView(View):
    def get(self, request):
        # print([user.__dict__ for user in get_user_model().objects.all()] )
        fields = ['username', 'email', 'date_joined', 'is_active', 'last_login']
        context = {
            'account_list': get_user_model().objects.values(*fields)
        }
        return render(request, f"{HTML_FILE_PATH}/account.html", context=context)
    
    def post(self, request, config_action):
        try:
            response = getattr(AccountConfigView, config_action)(request=request)
            return response
        except Exception as e:
            print(e)
            if str(e).startswith('['):
                return HttpResponse(str(e))
        
    def verify(request):
        try:
            username = request.POST.get('user_name', '')
            password = request.POST.get('user_password', '')
            user = get_user_model().objects.filter(username=username).values('username', 'email', 'password').first()
            print(user)
            if user is not None and check_password(password, user['password']):
                user.pop('password')
                return render(request, f"{HTML_FILE_PATH}/account/edit.html", user)
            else:
                raise Exception('[Verification Fail] Unknown Information. Please Try Again.')
        except Exception as e:
            print(e)
            raise Exception('[Verification Fail] Unknown Information. Please Try Again.')
        
    def update(request):
        try:
            post_data = request.POST.dict()
            og_username = post_data.pop('og_username', '')
            if any(item == '' for item in post_data.values()):
                raise Exception(f'[Invalid Information] Please Insert All Properties.')
            print(request.user)
            form = FinevoUserCreationForm(request.POST, instance=request.user)
            if form.is_valid():
                user = form.save()
                user.password = make_password(request.POST.get('password'))
                user.save()
                update_session_auth_hash(request, user)
                return HttpResponse(f'Successfully Edited Account {og_username} to {request.user}')
            else:
                raise Exception
        except Exception as e:
            print(e)
            if str(e).startswith('['):
                raise Exception(str(e))
            else:
                raise Exception('[Account Edition Fail] Invalid Information. Please Try Again.')
        
    
    
    

# @login_required
# def dashboard_view(request):
#     if request.method == 'POST':
#         context = account.get_account_list()
#         return render(request, f"{HTML_FILE_PATH}/dashboard.html", context)
#     return render(request, f"{HTML_FILE_PATH}/dashboard.html")

# @login_required
# def account_config(request, config_type):
#     if request.method == 'POST':
#         data = dict(request.POST.items())
#         if config_type == 'verify':
#             context = account.verify_account(data)
#             if not isinstance(context, str):
#                 return render(request, f"{HTML_FILE_PATH}/account/edit.html", context)
#         elif config_type == 'edit':
#             context = account.edit_account(data)
#         elif config_type == 'delete':
#             context = account.delete_account(data)
#             if context == 'Deleted Account Successfully':
#                 if data['user_name'] == request.user.username:
#                     return HttpResponse('reload')
#         return HttpResponse(context)