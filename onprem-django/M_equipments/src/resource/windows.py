import os
import requests
import json
from django.conf import settings

class WindowsIntegration:
    def __init__(self, request: dict):
        self.integration = request.pop('integration_type', '')
        self.request = request
    
    def check_agent(self):
        try:
            if any(val == '' for val in self.request.values()):
                return {"error": "Please Insert All Required Items."}
            
            return self.insert_agent()
        except Exception as e:
            print(e)
            return {"error": "Wrong Agent Configurations. Please Try Again"}
    
    def check_network(self):
        return {"error": "Network Transmission Integration Not Ready. Please Use Network Transmission."}
    
    def insert_agent(self):
        try:
            url = f"http://{self.request['server_ip']}/windows/{self.request['tag_name']}"
            headers = {
                "Context-Type": "application/json"
            }
            data = {
                "teiren_server_ip": self.request['server_ip'],
                "tag_name": self.request['tag_name'],
                "integration_type": self.integration
            }
            # result = requests.post(url=url, headers=headers, data=data)
            # print(result)
            return self.download_agent()
        except Exception as e:
            print(e)
            return {"error": "Wrong Agent Configurations. Please Try Again"}
        
    def download_agent(self):
        message_data = {
            "Teiren Server IP": self.request['server_ip'],
            "Tag Name": self.request['tag_name']
        }
        try:
            file_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'M_equipment', 'setup','setup_win.ps1')
            with open(file_path, 'r', encoding='utf-8') as file:
                context = ''.join(file.readlines())
                context = context.replace("{teiren_server_ip}", self.request['server_ip'])
                context = context.replace("{tag_name}", self.request['tag_name'])
            
            
            return {"message": f"Succcessfully Integrated Windows Eventlog: \n{message_data}", "file": context}
        except Exception as e:
            print(e)
            return {"error": f"Failed to Integrate Windows Eventlog: \n{message_data}"}

def windows_insert(request):
    try:
        if request.POST.get('integration_type', '') == '':
            return 'Please reload the page and try again.'
        integration =  WindowsIntegration(request=request.POST.dict())
        response = getattr(integration, f'check_{integration.integration}')()
    except Exception as e:
        print(e)
        response = {"error": 'Wrong Configurations. Please Try Again'}
    finally:
        return json.dumps(response)
        
    
    # # 다운로드 가능한 파일로 return       
    # filename = "teiren_windows_setup.ps1"
    # temp = tempfile.NamedTemporaryFile(delete=False)
    # # temp = tempfile.NamedTemporaryFile(suffix=".sh")
    # temp.write(context)
    # temp.close()
    # return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)



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