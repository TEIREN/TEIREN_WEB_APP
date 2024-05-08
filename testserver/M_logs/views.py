from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from .src.log import DashboardLogHandler

# Log Management
@login_required
def log_view(request, resourceType, logType):
    if request.method == 'POST':
        with DashboardLogHandler(request=request) as lhandler:
            context = (lhandler.get_log_page(logType.split(' ')[0]))
            return render(request,f"M_logs/dataTable.html",context)
    
    with DashboardLogHandler(request=request) as lhandler:
        context = (lhandler.get_log_page(logType.split('_')[0]))
        context['resource'] = resourceType
        
        if resourceType == 'cloud':
            context['logType']= logType.upper()
        else:
            logType = (' ').join(logType.split('_'))
            context['logType']= logType.title()
        
        return render(request, "M_logs/log.html",context)

## Detail Modal
def log_modal(request, resourceType, logType):
    if request.method == 'POST':
        if logType == 'help':
            return render(request, "M_logs/help.html")
        elif logType == 'details':
            with DashboardLogHandler(request=request) as lhandler:
                context = lhandler.get_log_detail_modal()
            return render(request, "M_logs/detail_modal.html", context)