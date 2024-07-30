from django.http import HttpResponse
from django.views import View
from django.urls import include, path
from django.shortcuts import render, redirect, HttpResponse

class AccountIndexView(View):
    def get(self, request, *args, **kwargs):
        return render(request, f"configurations/account.html")


class AccountConfigView(View):
    def get(self, request, *args, **kwargs):
        return render(request, f"configurations/account.html")

    def post(self, request, *args, **kwargs):
        """Account Configuration Class

        Example:
            HTML FORM:
                <form method="post" action="/my_view/">
                    <input type="hidden" name="action" value="delete">
                    <button type="submit">Delete</button>
                </form>

                <form method="post" action="/my_view/">
                    <input type="hidden" name="action" value="put">
                    <button type="submit">Update</button>
                </form>
        """
        # POST 요청에 대한 처리
        # request.POST를 통해 폼 데이터에 접근
        data = request.POST.get('data')
        action = request.POST.get('action')
        if action == 'PUT':
            pass
        if action == 'DELETE':
            pass
        return HttpResponse(f"Received POST data: {data}")


class DashboardView(View):
    def get(self, request, *args, **kwargs):
        return render(request, f"configurations/dashboard.html")
    

class TestView(View):
    def get(self, request, *args, **kwargs):
        print(kwargs)
        return HttpResponse('test')
    