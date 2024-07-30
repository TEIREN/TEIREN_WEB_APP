import requests

def fortinet_insert(request):
    url = f"http://3.35.81.217:8088/fortigate_api_send?api_key={request.POST['access_key']}"
    response = requests.get(url)
    return response.text