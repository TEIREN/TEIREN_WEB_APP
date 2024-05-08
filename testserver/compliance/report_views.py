# local
import re
import os
import pytz
import traceback
from datetime import datetime
from common.neo4j.handler import Neo4jHandler
from .src.report.module import convert_html_to_pdf, capture_first_page_pdf

# django
from django.http import FileResponse
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.shortcuts import HttpResponse

class RenderCompliance(Neo4jHandler):
    def __init__(self, request) -> None:
        super().__init__()
        self.db_name = request.session.get('db_name')
    
    def get_report_data(self):
        cypher = """
        MATCH (i:Compliance:Version{name:'Isms_p'})-[:CHAPTER]->(c:Chapter:Compliance:Certification)-[:SECTION]->
            (s:Certification:Compliance:Section)-[:ARTICLE]->(a:Certification:Compliance:Article)
        WHERE i.date = date('2023-10-31')
        OPTIONAL MATCH (a)<-[r:COMPLY]-(p:Product:Evidence:Compliance)
        WHERE p.name = 'AWS'
        OPTIONAL MATCH (a)<-[:POLICY]-(d:Data:Evidence:Compliance)<-[:DATA]-(:Policy:Evidence:Compliance)
        OPTIONAL MATCH (a)<-[:EVIDENCE]-(data:Data:Evidence:Compliance)<-[:DATA]-(p)
        OPTIONAL MATCH (evi:File:Evidence:Compliance)<-[:FILE]-(data)
        OPTIONAL MATCH (a)<-[:MAPPED]->(law_a:Article)<-[*]-(law_v:Version)<-[:VERSION]-(law:Law)
        OPTIONAL MATCH (law_v)-[:CHAPTER]->(law_c:Chapter)-[:SECTION]->(law_s:Section)-[:ARTICLE]->(law_a)
        OPTIONAL MATCH (law_v)-[:CHAPTER]->(law_c1:Chapter)-[:ARTICLE]->(law_a)
        WITH split(a.no, '.') as articleNo, c, s, a, coalesce(r, {score: 0}) as r, p, i, COLLECT(d)[0] as d, evi,
            law, law_a, law_v, law_s, law_c, law_c1
        WITH toInteger(articleNo[0]) AS part1, toInteger(articleNo[1]) AS part2, toInteger(articleNo[2]) AS part3,
            c, s, a, r, p, i, d, evi,law, law_a, law_v, law_s, law_c, law_c1
        WITH part1, part2, part3, c, s, a, r, p, i, d,
            {
                lawname: COALESCE(law.name, ''),
                lawChapterNo: COALESCE(COALESCE(law_c.no + '장', '') + COALESCE(law_c1.no + '장', ''), ''),
                lawChapterName: COALESCE(COALESCE(law_c.name, '') + COALESCE(law_c1.name, ''), ''),
                lawSectionNo: COALESCE(law_s.no + '절', ''),
                lawSectionName: COALESCE(law_s.name, ''),
                lawArticleNo: COALESCE(law_a.no + '조', ''),
                lawArticleName: COALESCE(law_a.name, '')
            } AS law,
            {
                evidenceFileName: COALESCE(evi.name,''),
                evidenceFileComment: COALESCE(evi.comment,''),
                evidenceFileVersion: COALESCE(evi.version, ''),
                evidenceFileAuthor: COALESCE(evi.author,'')
            } AS evi
        WITH part1, part2, part3, c, s, a, r, p, i, d, COLLECT(evi) as evidence_list, COLLECT(law) as law
        RETURN
            c.no AS chapterNo,
            c.name AS chapterName,
            s.no AS sectionNo,
            s.name AS sectionName,
            a.no AS articleNo,
            a.name AS articleName,
            a.comment AS articleComment,
            a.checklist AS articleChecklist,
            r.score AS complyScore,
            i.date AS version,
            law,
            evidence_list
        ORDER BY part1, part2, part3
        """
        results = self.run_data(database=self.db_name, query=cypher)
        # for result in results:
        #     # send to make_html_to_data()
        #     yield result
        
        return results
    
def make_html_to_data(request, results):
    context = {
        'page': [1, 2],
        'results': results
    }
    return render(request, f"report/index.html", context)

def make_compliance_file_name(compliance_type):
    KTZ = pytz.timezone('Asia/Seoul')
    kr_time = datetime.now(KTZ)

    return f"[Teiren] {compliance_type} Compliance Report-{kr_time.strftime('%y%m%d_%H%M')}.pdf"

def get_file_type(file_name) -> str:
    file_type = 'None'
    if file_name.endswith('.pdf'):
        file_type = 'pdf'
    elif file_name.endswith('.png'):
        file_type = 'png'
    elif file_name.endswith('.jpg'):
        file_type = 'jpg'
    elif file_name.endswith('.jpeg'):
        file_type = 'jpeg'
    return file_type
        
@login_required
def report(request, compliance_type):
    user_uuid = request.session.get('uuid')
    file_name = make_compliance_file_name(compliance_type)
    compliance_folder_path = f"{settings.MEDIA_ROOT}{user_uuid}/compliance_report"
    compliance_all_folder_path = f"{settings.MEDIA_ROOT}{user_uuid}/compliance_report/file-image"
    compliance_file_path = f"{compliance_folder_path}/{file_name}"
    
    try:
        os.makedirs(compliance_all_folder_path, exist_ok=True)
    except FileExistsError:
        return HttpResponse("Error: User Database Not Found")
    except Exception as e:
        print(e)
        os.makedirs(f"{settings.MEDIA_ROOT}{user_uuid}/Error", exist_ok=True)
        user_uuid += '/Error'
    
    with RenderCompliance(request=request) as comphandler:
        results:list = comphandler.get_report_data()
    context = {
        'page': [1,2],
        'results': results,
        'uuid': request.session.get('uuid')
    }
    # settings.MEDIA_URL: /home/yoonan/webAPP/DATABASE/
    """
    evidence_list = [
            {
                'evidenceFileAuthor': 'testuser1', 
                'evidenceFileComment': 'test2', 
                'evidenceFileName': '서폿이_말대꾸.png', 
                'evidenceFileVersion': 'v_1.0'
            }, 
            {
                'evidenceFileAuthor': 'testuser1', 
                'evidenceFileComment': 'test file comment', 
                'evidenceFileName': '컨설팅이_말대꾸.png', 
                'evidenceFileVersion': ''
            }
        ]
    """
    try:
        print('='*50)
        for result in results:
            for evidence_data in result['evidence_list']:
                if evidence_data['evidenceFileName']:
                    print(f"evidence_data filename: {evidence_data['evidenceFileName']}")
                    print(result)
                    file_type = get_file_type(evidence_data['evidenceFileName'])
                    if file_type == 'pdf':
                        # make first page of pdf file to image
                        # file_name = re.sub(r'[^\w\-_\. ]', '', evidence_data['evidenceFileName'])
                        capture_first_page_pdf(pdf_path=f"{settings.MEDIA_ROOT}{user_uuid}/Evidence/aws/{evidence_data['evidenceFileName']}",
                                            output_image_path=compliance_all_folder_path,
                                            file_name=evidence_data['evidenceFileName'])
                    evidence_data.update({
                        'fileType': file_type
                    })
                    
        html_content =  render_to_string('report/index.html', context=context)
        result = convert_html_to_pdf(html_content=html_content, pdf_path=compliance_file_path)
        if not result:
            return HttpResponse("Error: Fail to Export Compliance PDF File")
        if os.path.exists(compliance_folder_path+'/'):
            return FileResponse(open(compliance_file_path, 'rb'), as_attachment=True, filename=file_name)
        else:
            return HttpResponse("Error: User Database Not Found")
    except:
        print(traceback.format_exc())
