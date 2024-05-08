from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


# login feature
# class CustomLoginView(LoginView):
#     template_name = 'login.html'

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('user_id')
        password = request.POST['password']
        if username == 'test':
            user = authenticate(request, username=username, password=password)
            if user is None:
                test = User.objects.create_user(username=username , password=password)
                test.set_password(password)
                test.save()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # User credentials are valid, log the user in
            login(request, user)
            next_url = request.GET.get('next')
            # Redirect to a success page
            return redirect(next_url)
        # else:
            # Invalid credentials, show an error message
            # return HttpResponse(username)
    return render(request, 'login/login.html')


def logout_view(request):
    logout(request)
    return redirect('/')