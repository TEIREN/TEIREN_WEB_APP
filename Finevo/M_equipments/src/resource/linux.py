import requests
import tempfile
from django.http import FileResponse

def linux_insert(request):
    url = 'https://raw.githubusercontent.com/hw1186/rsys_conf/main/setup_linux.sh'
    response = requests.get(url)
    filename = url.split('/')[-1]
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(response.content)
    temp.close()
    return FileResponse(open(temp.name, 'rb'), as_attachment=True, filename=filename)