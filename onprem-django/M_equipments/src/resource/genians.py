import requests

class GeniansIntegartion:
    def __init__(self, request:dict):
        self.integration = request.pop('integration_type', '')
        self.request = request
    
    # Elasticsearch Server에 연동하기 전에 예외처리 및 파싱 (TCP/UDP => fluentd)
    def check_network(self):
        """
        self.request =
        {'server_ip': '', 'dst_port': '', 'tag_name': ''}
        """
        for key, val in self.request.items():
            if val == '':
                return 'Please Insert All Required Items.'
        return 'network'
    
    # Elasticsearch Server에 연동하기 전에 예외처리 및 파싱 (API)
    def check_api(self):
        """
        self.request = 
        {'access_key': '', 'dst_port': '', 'tag_name': ''}
        """
        for key, val in self.request.items():
            if val == '':
                return 'Please Insert All Required Items.'
        return 'api'
    
    # Elasticsearch Server에 연동하기 (TCP/UDP => fluentd)
    def insert_network(self):
        pass
    
    # Elasticsearch Server에 연동하기 (API)
    def insert_api(self):
        pass

def genians_insert(request):
    if request.POST.get('integration_type', '') == '':
        return 'Please reload the page and try again.'
    integration =  GeniansIntegartion(request=request.POST.dict())
    response = getattr(integration, f'check_{integration.integration}')()
    
    
    # url = f"http://3.35.81.217:8088/genian_api_send?api_key={request.POST['access_key']}"
    # response = requests.get(url)
    
    return {'message': response}