from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch

app = FastAPI()
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

class RuleSet(BaseModel):
    name: str
    system: str
    query: dict
    severity: int

# Detected logs index 생성
detected_logs_index = "detected_logs"
if not es.indices.exists(index=detected_logs_index):
    es.indices.create(index=detected_logs_index)

@app.post("/ruleset/")
async def create_ruleset(ruleset: RuleSet):
    index_name = "custom_rulesets"
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
    
    res = es.index(index=index_name, body=ruleset.dict())
    if res['result'] != 'created':
        raise HTTPException(status_code=500, detail="Failed to create ruleset")
    return {"message": "Ruleset created successfully"}

@app.get("/ruleset/{name}")
async def get_ruleset(name: str):
    index_name = "custom_rulesets"
    res = es.search(index=index_name, body={"query": {"match": {"name": name}}})
    if res['hits']['total']['value'] == 0:
        raise HTTPException(status_code=404, detail="Ruleset not found")
    return res['hits']['hits'][0]["_source"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
