import requests
import tempfile
from django.http import FileResponse

def windows_insert(request):
    url = 'https://raw.githubusercontent.com/hw1186/rsys_conf/main/setup_win.ps1'
    response = requests.get(url)
    filename = url.split('/')[-1]
    temp = tempfile.NamedTemporaryFile(delete=False)
    # temp = tempfile.NamedTemporaryFile(suffix=".sh")
    temp.write(response.content)
    temp.close()
    return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)