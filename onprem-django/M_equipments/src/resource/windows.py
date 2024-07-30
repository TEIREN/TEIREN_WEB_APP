import os
import requests
import random
import string
import tempfile
from django.http import FileResponse, HttpResponse
from django.conf import settings

def windows_insert(request):
    config = {
            'server_ip':'', 
            'tag_name': f'windows_{''.join(random.choices(string.ascii_letters, k=5))}'.lower()
        }
    for item in ['server_ip','tag_name']:
        value = request.POST.get(item, '')
        if value == '' and item == 'server_ip':
            return 'Please Insert Server IP'
        elif value != '':
            config[item] = value
    # FastAPI를 통해서 integration_info index에 잘 들어가는지 확인 
    if windows_check() == "fail":
        raise Exception
    
    # 파일 열어서 변수값 수정
    file_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'M_equipment', 'setup','setup_win.ps1')
    with open(file_path, 'r') as file:
        context = ''.join(file.readlines())
        context = context.replace("{teiren_server_ip}", config['server_ip'])
        context = context.replace("{tag_name}", config['tag_name'])
        context = context.encode('utf-8')
    
    # 다운로드 가능한 파일로 return       
    filename = "teiren_windows_setup.ps1"
    temp = tempfile.NamedTemporaryFile(delete=False)
    # temp = tempfile.NamedTemporaryFile(suffix=".sh")
    temp.write(context)
    temp.close()
    return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)


##### 현우야 여기에서 integration 잘 되는지 안 되는지 확인하는 코드 작성해주세요
def windows_check():
    pass


# import requests
# import tempfile
# from django.http import FileResponse

# def windows_insert(request):
#     url = 'https://raw.githubusercontent.com/hw1186/rsys_conf/main/setup_win.ps1'
#     response = requests.get(url)
#     filename = url.split('/')[-1]
#     temp = tempfile.NamedTemporaryFile(delete=False)
#     # temp = tempfile.NamedTemporaryFile(suffix=".sh")
#     temp.write(response.content)
#     temp.close()
#     return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)