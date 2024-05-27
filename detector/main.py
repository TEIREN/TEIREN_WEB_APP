from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from elasticsearch import Elasticsearch

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

# 룰셋 인덱스 이름 매핑
ruleset_mapping = {
    1: "linux_ruleset",
    2: "window_ruleset",
    3: "genian_ruleset",
    4: "fortigate_ruleset"
}

# detected log 인덱스 이름 매핑
detected_log_mapping = {
    1: "linux_detected_log",
    2: "window_detected_log",
    3: "genian_detected_log",
    4: "fortigate_detected_log"
}

def create_index(index_name: str):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)

# 룰셋을 생성하는 API 엔드포인트
@app.post("/ruleset/")
async def create_ruleset(ruleset: RuleSet, index_choice: int = Query(..., ge=1, le=4)):
    if index_choice not in ruleset_mapping:
        raise HTTPException(status_code=400, detail="Invalid index choice")
    
    index_name = ruleset_mapping[index_choice]
    create_index(index_name)
    
    # 룰셋을 Elasticsearch에 저장합니다.
    res = es.index(index=index_name, body=ruleset.dict())
    if res['result'] not in ['created', 'updated']:
        raise HTTPException(status_code=500, detail="Failed to create ruleset")
    return {"message": f"Ruleset created successfully in {index_name}"}

# 특정 룰셋을 조회하는 API 엔드포인트
@app.get("/ruleset/{name}")
async def get_ruleset(name: str, index_choice: int = Query(..., ge=1, le=4)):
    if index_choice not in ruleset_mapping:
        raise HTTPException(status_code=400, detail="Invalid index choice")
    
    index_name = ruleset_mapping[index_choice]
    res = es.search(index=index_name, body={"query": {"match": {"name": name}}})
    if res['hits']['total']['value'] == 0:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    return res['hits']['hits'][0]["_source"]

# FastAPI 앱을 실행합니다.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
