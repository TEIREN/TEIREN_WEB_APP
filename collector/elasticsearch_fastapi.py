from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from elasticsearch_collector_renew import ElasticsearchCollector
import json

app = FastAPI()

@app.post("/collector/{action}/{system}/{TAG_NAME}")
async def collector_action(request: Request, action: str, system: str, TAG_NAME: str):
    """
    {action}에는 시스템별로 추가(add) 시작(start) 중지(stop) 삭제(delete) 수정(update) 
    {system}에는 system name linux, windows, genian, fortigate, etc
    """
    try:
        es_collector = ElasticsearchCollector(system=system, TAG_NAME=TAG_NAME)
        if action == "status":
            response = await es_collector.get_status()
            return {"message": json.dumps({"status":response})}
        else:
            await es_collector.manage_integration(action=action, request=request)
            return {"message": f"{TAG_NAME} Integration saved successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")                

@app.post("/collect_log/{system}/{TAG_NAME}")
async def collect_log(request: Request, system: str, TAG_NAME: str):
    es_collector = ElasticsearchCollector(system=system, TAG_NAME=TAG_NAME)
    try:
        if await es_collector.get_status() != "started":
            raise HTTPException(status_code=400, detail="Log collection is not started")
        try:
            try:
                log_request = await request.body()
                log_request = json.loads(log_request.decode('euc-kr'))
            except:
                log_request = await request.json()
            client_ip = request.client.host
            response = await es_collector.collect_logs(request=log_request, client_ip=client_ip)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
    except Exception as e:
        response = {"error": str(e)}
    finally:
        print(response)
        return response
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)