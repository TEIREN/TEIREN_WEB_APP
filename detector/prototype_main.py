from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch

"""
프로토타입
"""

# FastAPI 앱을 설정합니다.
app = FastAPI()

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# RuleSet 클래스 정의 (FastAPI에서 사용할 모델)
class RuleSet(BaseModel):
    name: str
    system: str
    query: dict
    severity: int

# Detected logs index 생성
detected_logs_index = "detected_logs"
if not es.indices.exists(index=detected_logs_index):
    es.indices.create(index=detected_logs_index)

# 룰셋을 생성하는 API 엔드포인트
@app.post("/ruleset/")
async def create_ruleset(ruleset: RuleSet):
    index_name = "custom_rulesets"
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
    
    # 룰셋을 Elasticsearch에 저장합니다.
    res = es.index(index=index_name, body=ruleset.dict())
    if res['result'] != 'created':
        raise HTTPException(status_code=500, detail="Failed to create ruleset")
    return {"message": "Ruleset created successfully"}

# 특정 룰셋을 조회하는 API 엔드포인트
@app.get("/ruleset/{name}")
async def get_ruleset(name: str):
    index_name = "custom_rulesets"
    res = es.search(index=index_name, body={"query": {"match": {"name": name}}})
    if res['hits']['total']['value'] == 0:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    return res['hits']['hits'][0]["_source"]

# FastAPI 앱을 실행합니다.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)