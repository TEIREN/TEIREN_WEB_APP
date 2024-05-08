# pip install pdfkit 필수
import pdfkit
import base64
import re

def embed_image(img_path):
    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f'data:image/png;base64,{encoded_string}'

def convert_img_to_base64(html_content):
    pattern = r'src="([^"]*)"'
    matches = re.findall(pattern, html_content)
    for img_path in matches:
        html_content = html_content.replace(img_path, embed_image(img_path=img_path))
    return html_content

def convert_html_to_pdf(html_content:str, pdf_path:str):
    html_content = convert_img_to_base64(html_content)
    print(pdf_path)
    try:
        options = {
            "enable-local-file-access": True,
            'encoding': "UTF-8",
            'margin-top': '0mm',
            'margin-right': '0mm',
            'margin-bottom': '0mm',
            'margin-left': '0mm',
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
        pdfkit.from_string(html_content, pdf_path, options=options, configuration=config)
        print(f"PDF generated and saved at {pdf_path}")
    except Exception as e:
        print(f"PDF generation failedf: {e}")

