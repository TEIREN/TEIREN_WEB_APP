# local
# pip install pdfkit 필수
import re
import pdfkit
import base64
import urllib.parse

# 3rd party
from pdf2image import convert_from_path


def embed_image(img_path):
    try:
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        img_path = '/home/yoonan/DATABASE/system/file_not_found.png'
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
    return f'data:image/png;base64,{encoded_string}'

def convert_img_to_base64(html_content):
    pattern = r'src="([^"]*)"'
    matches = re.findall(pattern, html_content)
    for img_path in matches:
        print(f"img_path is: {img_path}")
        html_content = html_content.replace(img_path, embed_image(img_path=img_path))
    return html_content
#* 
def convert_html_to_pdf(html_content:str, pdf_path:str):
    html_content = convert_img_to_base64(html_content)
    try:
        options = {
            # "enable-local-file-access": True,
            'encoding': "UTF-8",
            'page-size': "A4",
            # 'page-width': '794px',  # HTML과 일치하는 픽셀 단위 사용
            # 'page-height': '1123px',  # HTML과 일치하는 픽셀 단위 사용
            'margin-top': '0mm',
            'margin-right': '0mm',
            'margin-bottom': '0mm',
            'margin-left': '0mm',
            'image-dpi': 300,  # 이미지 해상도 조정
            'image-quality': 100,  # 이미지 품질 조정
        }
        # wkhtmltopdf의 설치 경로를 지정-- docker에 올렸을 때 이 부분을 어떻게 설정해야 되는지 모르겠음. linux에서는 할 필요 없을 수도 있음
        # # linux에 다운은 받아야 됨. linux 다운로드 방법
        # # sudo apt-get update
        # # sudo apt-get install -y xfonts-75dpi xfonts-base libxrender1 fontconfig xvfb
        # # wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb
        # # sudo dpkg -i wkhtmltox_0.12.5-1.bionic_amd64.deb
        # # sudo apt-get install -f
        path_wkhtmltopdf = r'/usr/bin/wkhtmltopdf' # <- wkhtmltopdf 경로
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        pdfkit.from_string(html_content, pdf_path, configuration=config, options=options)
        
        return True
    except Exception as e:
        return False


def capture_first_page_pdf(pdf_path, output_image_path, file_name):
    # pdf_path = urllib.parse.quote(pdf_path)
    # file_name = urllib.parse.quote(file_name)
    # PDF 파일에서 이미지로 변환
    images = convert_from_path(pdf_path, first_page=1, last_page=1)
    # 첫 번째 페이지 이미지 저장
    print('이미지 저장')
    try:
        images[0].save(f"{output_image_path}/convert-image-{file_name}.png", 'PNG')
    except Exception as e:
        print(e)

