from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
# from .src.log import DashboardLogHandler
from .src.elasticsearch_log import list_logs

# Log Management
@login_required
def log_view(request, resourceType, logType):
    context = list_logs(request=request, resource_type=resourceType, system=logType.split('_')[0])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return context
    else:
        context.update({'system_name': (' ').join(logType.split('_'))})
        return render(request, "M_logs/elasticsearch/eslog.html", context)

## Detail Modal
def log_modal(request, resourceType, logType):
    if request.method == 'POST':
        if logType == 'help':
            return render(request, "M_logs/help.html")
        # elif logType == 'details':
        #     with DashboardLogHandler(request=request) as lhandler:
        #         context = lhandler.get_log_detail_modal()
        #     return render(request, "M_logs/detail_modal.html", context)
        
        
        


# @login_required
# def log_view(request, resourceType, logType):
#     if logType in ['aws', 'teiren_cloud']:
#         # if request.method == 'POST':
#         #     with DashboardLogHandler(request=request) as lhandler:
#         #         context = (lhandler.get_log_page(logType.split('_')[0]))
#         #         return render(request,f"M_logs/dataTable.html",context)
#         # else:
#         #     with DashboardLogHandler(request=request) as lhandler:
#         #         context = (lhandler.get_log_page(logType.split('_')[0]))
#         #         context['resource'] = resourceType
                
#         #         if resourceType == 'cloud':
#         #             context['logType']= logType.upper()
#         #         else:
#         #             logType = (' ').join(logType.split('_'))
#         #             context['logType']= logType.title()
                
#                 return render(request, "M_logs/log.html",context)
#     else:
#         context = list_logs(request=request, resource_type=resourceType, system=logType.split('_')[0])
#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return context
#         else:
#             context.update({'system_name': (' ').join(logType.split('_'))})
#             return render(request, "M_logs/elasticsearch/eslog.html", context)