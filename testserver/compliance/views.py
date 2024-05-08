from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.clickjacking import xframe_options_sameorigin, xframe_options_exempt

from .src.assets import AssetListAction, AssetTableAction, AssetFileAction, AssetDataAction
from .src.evidence import EvidenceDataList, EvidenceDataHandler, EvidenceFileHandler, ComplianceHandler
from .src.lists import ComplianceFileHandler, ComplianceListHandler
from .src.policy import CompliancePolicyHandler, PolicyFileHandler
from .src.file import get_file_preivew_details

from .models import Evidence, Asset, Policy


# Compliance List
@login_required
def compliance_lists_view(request, compliance_type=None):
    if compliance_type:
        with ComplianceListHandler(request=request) as listhandler:
            if compliance_type == 'ISMS-P':
                context= listhandler.get_lists_version('Isms_p')
            elif compliance_type == 'Another':
                context= 'Another'
            context.update({'compliance_type': compliance_type})
        return render(request, f"compliance/compliance_lists/lists.html", context)
    else:
        return render(request, f"compliance/compliance_lists.html")

def compliance_lists_modify(request, compliance_type):
    if request.method == "POST":
        data = dict(request.POST.items())
        with ComplianceListHandler(request=request) as listhandler:
            if "article" in data :
                return HttpResponse(listhandler.modify_lists_comply(
                    compliance_type=compliance_type.capitalize().replace('-','_'),
                    data=data))
            data.update({'compliance':listhandler.get_lists_version(
                compliance_type=compliance_type.capitalize().replace('-','_'),
                data=data)})
            
        data.update({'compliance_type': compliance_type})
        return render(request, f"compliance/compliance_lists/dataTable.html", data)

def download_compliance_report(reqeust, compliance_type):
    file_name = "[Teiren]ISMS-P Compliance Report.docx"
    file_path = f"/home/yoonan/teiren/media/docx/{file_name}"
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)

@login_required
def compliance_lists_detail_view(request, compliance_type):
    if request.method == 'POST':
        data = dict(request.POST.items())
        if data['no'] == '' or not compliance_type.lower().startswith('isms'):
            return redirect(f"/compliance/lists/{compliance_type}")
        else:
            with ComplianceListHandler(request=request) as listhandler:
                data.update(listhandler.get_lists_details(compliance_type=compliance_type.capitalize().replace('-','_'), 
                                                          data=data))
            data.update({'compliance_type': compliance_type})
            return render(request, f"compliance/compliance_lists/details.html", data)
    else:
        return redirect(f"/compliance/lists/{compliance_type}")

def compliance_lists_file_action(request, action_type):
    if request.method == 'POST':
        if action_type == 'download':
            documents = Evidence.objects.filter(title=request.POST.get('comment', '')) # commnet = title
            for document in documents:
                if document.uploadedFile.name:
                    file_path = document.uploadedFile.path
                    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=document.uploadedFile.name)
        else:
            with ComplianceFileHandler(request=request) as compliance_file:
                if action_type == 'add':
                    return HttpResponse(compliance_file.add_compliance_evidence_file())
                elif action_type == 'modify':
                    return HttpResponse(compliance_file.modify_compliance_evidence_file())
                elif action_type == 'delete':
                    return HttpResponse(compliance_file.delete_compliance_evidence_file())

def compliance_lists_policy_action(request, action_type):
    if request.method == 'POST':
        with ComplianceListHandler(request=request) as listhandler:
            if action_type == 'add':
                return HttpResponse(listhandler.add_related_policy())
            elif action_type == 'delete':
                return HttpResponse(listhandler.delete_related_policy())

#Assets Management
@login_required
def assets_view(request, asset_type=None):
    if request.method == 'POST':
        with AssetListAction(request=request) as listaction_handler:
            if asset_type == 'File':
                context = ({'files':listaction_handler.get_file_list()})
                return render(request, f"compliance/asset_management/file_view.html", context)
            elif asset_type == 'All' or asset_type == 'search':
                context = listaction_handler.get_all_asset_list()
            else:
                context = listaction_handler.get_asset_list(asset_type)
            return render(request, f"compliance/asset_management/dataTable.html", context)
    else:
        with AssetListAction(request=request) as listaction_handler:
            context= listaction_handler.get_all_asset_list()
        return render(request, f"compliance/asset_management.html", context)

@login_required
def assets_table(request, action_type):
    if request.method == 'POST':
        with AssetTableAction(request=request) as tableaction_handler:
            response = tableaction_handler.asset_table_action(action_type)
        return HttpResponse(response)
    else:
        redirect('/auth/login')

@login_required
def assets_action(request, asset_type, action_type):
    if request.method == 'POST':
        if action_type == 'download':
            documents = Asset.objects.filter(title=request.POST.get('comment', ''))
            for document in documents:
                if document.uploadedFile.name.endswith(request.POST.get('name', '').replace('[','').replace(']','')):
                    file_path = document.uploadedFile.path
                    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=document.uploadedFile.name)
        else:
            if asset_type == 'file':
                with AssetFileAction(request=request) as fileaction_handler:
                    return HttpResponse(fileaction_handler.asset_file_action(action_type))
            elif asset_type == 'data':
                with AssetDataAction(request=request) as dataaction_handler:
                    return HttpResponse(dataaction_handler.asset_data_action(action_type))
    else:
        redirect('/auth/login')

# Evidence Management
@login_required
def evidence_view(request):
    with EvidenceDataList(request=request) as datalist_handler:
        context = {
            'data_list': datalist_handler.get_data_list(),
            'product_list': datalist_handler.get_product_list(),
            'compliance_list': datalist_handler.get_compliance_list()
            }
    if request.method == 'POST':
        return render(request, "compliance/evidence_management/dataTable.html", context)
    else:
        return render(request, "compliance/evidence_management.html", context)

def evidence_data_action(request, action_type):
    if request.method == 'POST':
        with EvidenceDataHandler(request=request) as evidencedata_handler:
            if action_type == 'get_version':
                version_list = evidencedata_handler.get_compliance_version_list()
                return JsonResponse({'version_list':version_list})
            elif action_type == 'get_article':
                article_list = evidencedata_handler.get_compliance_article_list()
                return JsonResponse({"article_list" :article_list})
            elif action_type == 'add':
                return HttpResponse(evidencedata_handler.add_evidence_data())
            elif action_type == 'modify':
                return HttpResponse(evidencedata_handler.modify_evidence_data())
            elif action_type == 'delete':
                return HttpResponse(evidencedata_handler.delete_evidence_data())

## Evidence Data Management
@login_required
def evidence_data_detail_view(request, product_name, data_name):
    if data_name:
        with EvidenceDataList(request=request) as datalist_handler:
            context = {
                'product_name': product_name,
                'data_name': data_name,
                'data_list': datalist_handler.get_data_list(data_name),
                'file_list': datalist_handler.get_file_list(data_name),
                'related_compliance_list': datalist_handler.get_data_related_compliance(search_cate='evidence', search_content=data_name),
                'compliance_list': datalist_handler.get_compliance_list()
            }
        try:    
            context['related_compliance_list'][0]['version'] = dict(context['related_compliance_list'][0]['version']) 
            context['related_compliance_list'][0]['version']['name'] = context['related_compliance_list'][0]['version']['name'].upper().replace("_", "-")
        except IndexError:
            return render(request, f"compliance/evidence_management/details.html", context)
        return render(request, f"compliance/evidence_management/details.html", context)

def evidence_file_action(request, action_type):
    if request.method == 'POST':
        if action_type == 'download':
            documents = Evidence.objects.filter(title=request.POST.get('comment', ''))
            for document in documents:
                if document.uploadedFile.name.endswith(request.POST.get('name', '').replace('[','').replace(']','')):
                    file_path = document.uploadedFile.path
                    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=document.uploadedFile.name)
        else:
            with EvidenceFileHandler(request=request) as file_handler:
                if action_type == 'add':
                    return HttpResponse(file_handler.add_evidence_file())
                elif action_type == 'modify':
                    return HttpResponse(file_handler.modify_evidence_file())
                elif action_type == 'delete':
                    return HttpResponse(file_handler.delete_evidence_file())

def evidence_related_compliance(request, action_type):
    if request.method == 'POST':
        with ComplianceHandler(request=request) as compliance_handler:
            if action_type == 'add':
                return HttpResponse(compliance_handler.add_related_compliance())
            elif action_type == 'delete':
                return HttpResponse(compliance_handler.delete_related_compliance())
    return HttpResponse('test')

@login_required
def policy_view(request):
    with CompliancePolicyHandler(request=request) as compliance_policy:
        context = {'policy': compliance_policy.get_policy_data_list()}
    return render(request, f"compliance/policy_management.html", context)

def policy_action(request, action_type):
    if request.method == 'POST':
        with CompliancePolicyHandler(request=request) as compliance_policy:
            if action_type == 'add':
                return HttpResponse(compliance_policy.add_policy())
            elif action_type == 'modify':
                return HttpResponse(compliance_policy.modify_policy())
            elif action_type == 'delete':
                return HttpResponse(compliance_policy.delete_policy())

def policy_data_action(request, action_type):
    if request.method == 'POST':
        with CompliancePolicyHandler(request=request) as compliance_policy:
            if action_type == 'add':
                return HttpResponse(compliance_policy.add_policy_data())
            elif action_type == 'modify':
                return HttpResponse(compliance_policy.modify_policy_data())
            elif action_type == 'delete':
                return HttpResponse(compliance_policy.delete_policy_data())
@login_required
def policy_data_view(request, policy_type, data_type):
    context={'policy': policy_type}
    with CompliancePolicyHandler(request=request) as compliance_policy:
        context.update(compliance_policy.get_policy_data_details(policy_type=policy_type, data_type=data_type))
    return render(request, f"compliance/policy_management/file.html", context)

def policy_data_file_action(request, policy_type, data_type, action_type):
    if request.method == 'POST':
        if action_type == 'download':
            documents = Policy.objects.filter(title=request.POST.get('comment', ''))
            for document in documents:
                if document.uploadedFile.name.endswith(request.POST.get('name', '').replace('[','').replace(']','')):
                    file_path = document.uploadedFile.path
                    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=document.uploadedFile.name)
        else:
            with PolicyFileHandler(request=request) as file_handler:
                if action_type == 'add':
                    return HttpResponse(file_handler.add_policy_data_file())
                elif action_type == 'modify':
                    return HttpResponse(file_handler.modify_policy_data_file())
                elif action_type == 'delete':
                    return HttpResponse(file_handler.delete_policy_data_file())

def data_file_preview(request, evidence_type):
    if request.method == 'POST':
        file_url, mime_type = get_file_preivew_details(request, evidence_type)
        print("---------")
        print(file_url)
        print(mime_type)
        return render(request, "compliance/file_preview.html", {'file': file_url, 'file_type':mime_type})

#-------------------------------------------------------------------------------------------

# # Compliance lists_2 - 현경
# def integration(request):
#     if request.method == 'GET':
#         # Ajax GET 요청에서 전달된 파라미터 가져오기
#         product_list=evidence.get_product()
        
#         context={
#             'product_list':product_list
#         }

#         if product_list:
#             return render(request, f"compliance/integration.html", context)
#         else:
#             # title이 없을 경우 에러 응답
#             return JsonResponse({'error': 'Missing title parameter'}, status=400)
#     else:
#         # GET 이외의 메소드에 대한 처리
#         return JsonResponse({'error': 'Invalid method'}, status=400)

# # Data 추가
# def add_integration(request):
#     if request.method=="POST":
#         product=dict(request.POST.items())
   
#         try:
#             #이걸 JsonResponse로 어케 바꾸지
#             return HttpResponse(evidence.add_integration(product))
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)
#     else:
#         return JsonResponse({'error': 'Invalid method'}, status=400)
  

# def get_policy_data(request):
#     if request.method == 'GET':
#         # Ajax GET 요청에서 전달된 파라미터 가져오기
#         policy_name = request.GET.get('policy_name', None)
#         data_name = request.GET.get('data_name', None)

#         data=policy.get_policy_data(policy_name, data_name)
#         file_list=evidence.get_file(data_name)
        
#         context={
#             'policy':policy_name,
#             'data': data,
#             'file_list': file_list,
#         }

#         if policy_name:
#             return render(request, f"compliance/policy/file.html", context)
#         else:
#             # title이 없을 경우 에러 응답
#             return JsonResponse({'error': 'Missing title parameter'}, status=400)
#     else:
#         # GET 이외의 메소드에 대한 처리
#         return JsonResponse({'error': 'Invalid method'}, status=400)
    
# # def add_policy_file(request):
# #     if request.method=="POST":
# #         data=dict(request.POST.items())

# #         uploaded_file = request.FILES.get("add_file")
# #         file_name = data.get('add_name', '')

# #         # Saving the information in the database
# #         document = Document(
# #             title=file_name,
# #             uploadedFile=uploaded_file
# #         )
# #         document.save()
   
# #         try:
# #             #이걸 JsonResponse로 어케 바꾸지
# #             return HttpResponse(policy.add_policy_file(data))
# #         except Exception as e:
# #             return JsonResponse({'error': str(e)}, status=500)
# #     else:
# #         return JsonResponse({'error': 'Invalid method'}, status=400)
    
    
# def del_policy_file(request):
#     if request.method=="POST":
#         data=dict(request.POST.items())
   
#         try:
#             #이걸 JsonResponse로 어케 바꾸지
#             return HttpResponse(policy.del_policy_file(data))
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)
#     else:
#         return JsonResponse({'error': 'Invalid method'}, status=400)