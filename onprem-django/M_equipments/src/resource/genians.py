import requests

def genians_insert(request):
    url = f"http://3.35.81.217:8088/genian_api_send?api_key={request.POST['access_key']}"
    response = requests.get(url)
    return response.text