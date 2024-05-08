from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from .src import log

# Log Management
@login_required
def log_view(request, resourceType, logType):
    if request.method == 'POST':
        context = dict(request.POST)
        context = (log.get_log_page(context, logType.split(' ')[0]))
        return render(request,f"M_logs/dataTable.html",context)
    context = dict(request.GET.items())
    context = (log.get_log_page(context, logType.split('_')[0]))
    if resourceType == 'cloud':
        context['logType']= logType.upper()
    else:
        logType = (' ').join(logType.split('_'))
        context['logType']= logType.title()
    context['resource'] = resourceType
    return render(request,f"M_logs/log.html",context)

## Detail Modal
def log_modal(request, resourceType, logType):
    if request.method == 'POST':
        if logType == 'help':
            return render(request, "M_logs/help.html")
        elif logType == 'details':
            context = log.get_log_detail_modal(dict(request.POST.items()))
            return render(request, "M_logs/detail_modal.html", context)