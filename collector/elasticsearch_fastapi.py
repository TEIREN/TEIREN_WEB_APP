from fastapi import FastAPI, HTTPException, Request
from elsasticsearch_collector_renew import ElasticsearchCollector

app = FastAPI()

@app.post("/collector/{action}/{system}/{TAG_NAME}")
async def collector_action(request: Request, action: str, system: str, TAG_NAME: str):
    """
    {action}에는 시스템별로 추가(add) 시작(start) 중지(stop) 삭제(delete) 수정(update) 
    {system}에는 system name linux, window, genian, fortigate, etc
    """
    if action not in ["add", "start", "stop", "delete", "update", "status"]:
        raise HTTPException(status_code=400, detail=f"{action} action is not supported")
    
    es_collector = ElasticsearchCollector(system=system, TAG_NAME=TAG_NAME)
    
    if action == "status":
        response = await es_collector.get_status()
        return {"status": response}
    
    config = None
    if action in ["add", "update"]:
        config = await request.json()
    
    await es_collector.manage_integration(action=action, config=config)
    return {"result": f"{action} action completed for {system} with TAG_NAME {TAG_NAME}"}

@app.post("/collect_log/{system}/{TAG_NAME}")
async def collect_log(request: Request, system: str, TAG_NAME: str, status):
    es_collector = ElasticsearchCollector(system=system, TAG_NAME=TAG_NAME)
    if es_collector.get_status() != "started":
        raise HTTPException(status_code=400, detail="Log collection is not started")
    
    log_request = await request.json()
    client_ip = request.client.host
    response = await es_collector.collect_logs(request=log_request, client_ip=client_ip)
    return {"result": response}
