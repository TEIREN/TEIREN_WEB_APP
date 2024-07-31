import os
import requests
import random
import string
import tempfile
from django.http import FileResponse, HttpResponse
from django.conf import settings

def linux_insert(request):
    try:
        config = {
            'server_ip':'',
            'agent_port':'5140', 
            'tag_name': f'linux_{''.join(random.choices(string.ascii_letters, k=5))}'.lower()
        }
        for item in ['server_ip', 'agent_port','tag_name']:
            value = request.POST.get(item, '')
            if value == '' and item == 'server_ip':
                return 'Please Insert Correct Server IP'
            elif value != '':
                config[item] = value
                
        # FastAPI를 통해서 integration_info index에 잘 들어가는지 확인 
        if linux_check() == "fail":
            raise Exception
        
        file_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'M_equipment', 'setup','setup_linux.sh')
        with open(file_path, 'r') as file:
            context = ''.join(file.readlines())
            context = context.replace("{teiren_server_ip}", config['server_ip'])
            context = context.replace("{agent_port}", config['agent_port'])
            context = context.replace("{tag_name}", config['tag_name'])
            context = context.encode('utf-8')
        
        filename = "teiren_linux_setup.sh"
        temp = tempfile.NamedTemporaryFile(delete=False)        
        temp.write(context)
        temp.close()
        return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)
    except Exception as e:
        print(e)
        return 'Wrong Configurations. Please Try Again'

##### 예외처리 / "/collector/{action}/{system}/{TAG_NAME}" 에 보내기
def linux_check():
    pass

# import requests
# import tempfile
# from django.http import FileResponse

# def linux_insert(request):
#     url = 'https://raw.githubusercontent.com/hw1186/rsys_conf/main/setup_linux.sh'
#     response = requests.get(url)
#     filename = url.split('/')[-1]
#     temp = tempfile.NamedTemporaryFile(delete=False)
#     temp.write(response.content)
#     temp.close()
#     return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)