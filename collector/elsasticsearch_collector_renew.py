from elasticsearch_collector import elasticsearch
from elasticsearch import AsyncElasticsearch

class ElasticsearchCollector():
    def __init__(self, system: str):
        self.system = system
        self.es = AsyncElasticsearch([es_host]) # 생성 해야함 

    async def get_status(self):
        response = await self.es.get(index=f"{self.system}_logs", id=1)
        return response["_source"]
    
    async def update_status(self, status: str):
        await self.es.index(index="log_collection_status", id=self.system, body={"status": status}) # log_collection_status index 생성 수정 
        
    async def collect_logs(self):
        pass

    def test(self):
        pass
        

# @app.post("/add_integration/{system}")
# async def add_integration(request, system):
#     integration = ElasticsearchCollector(sytem=system)
#     pass

# @app.post("/collector/{action}/{system}")
# async def collector_action(request, system):
#     action = ElasticsearchCollector(sytem=system)
#     action.action()
#     pass

# @app.post("/collect_log/{system}")
# async def add_integration(request, system):
#     integration = ElasticsearchCollector(sytem=system)
#     pass