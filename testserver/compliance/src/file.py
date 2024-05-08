from ..models import Evidence, Asset, Policy
import traceback
import mimetypes
import docx2pdf
from aspose.slides import Presentation

def get_file_preivew_details(request, evidence_type):
    title = request.POST.get('comment', '')
    user_uuid = request.session.get('uuid')
    try:
        # user_uuid = request.session.get('uuid')
        if evidence_type == 'policy':
            documents = Policy.objects.filter(user_uuid=user_uuid, title=title)
        elif evidence_type == 'asset':
            documents = Asset.objects.filter(user_uuid=user_uuid, title=title)
        else:
            documents = Evidence.objects.filter(user_uuid=user_uuid, title=title, product=evidence_type)
            
        for document in documents:
            print('='*50)
            name = request.POST.get('name', '')
            if document.uploadedFile.name:
                print(f"document.name: {document.uploadedFile.name}")
                print(f"document.path: {document.uploadedFile.path}")
                mime_type, _ = mimetypes.guess_type(document.uploadedFile.path)
                file_path = document.uploadedFile.path
                
                if mime_type == 'image/png' or mime_type == 'image/jpg' or mime_type == 'image/jpeg':
                    return file_path, mime_type
                elif 'docx' in mime_type:
                    file_url, mime_type = docx_to_pdf(file_path, file_url)
                    return '/home/yoonan/webAPP/testserver'+file_url, mime_type
                elif 'ppt' in mime_type:
                    file_url, mime_type = ppt_to_img(file_path, file_url)
                    return '/home/yoonan/webAPP/testserver'+file_url, mime_type
    except Exception:
        print(traceback.format_exc())
        return '/home/yoonan/DATABASE/system/file_not_found.png', 'image/png'

def docx_to_pdf(file_path, file_url):
    preview_path = '\\'.join(file_path.split('\\')[:-1])+'\\preview.pdf'
    preview_url = '/'.join(file_url.split('/')[:-1]) + '/preview.pdf'
    docx2pdf.convert(file_path, preview_path)
    return preview_url, 'application/pdf'

def ppt_to_img(file_path, file_url):
    presentation = Presentation(file_path)
    for slide in presentation.slides:
        image_path = '\\'.join(file_path.split('\\')[:-1])+'\\preview.png'
        slide.get_thumbnail().save(image_path)
        break
    preview_url = '/'.join(file_url.split('/')[:-1]) + '/preview.png'
    return preview_url, 'image/png'