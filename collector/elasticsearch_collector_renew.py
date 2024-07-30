from elasticsearch import Elasticsearch, NotFoundError, AsyncElasticsearch

class ElasticsearchCollector():
    def __init__(self, system: str):
        es_host = Elasticsearch("http://3.35.81.217:9200/")
        self.system = system
        self.es = AsyncElasticsearch([es_host]) # 생성 해야함 

    async def get_status(self):
        response = await self.es.get(index=f"{self.system}_logs", id=1)
        return response["_source"]
    
    async def update_status(self, status: str):
        await self.es.index(index="log_collection_status", id=self.system, body={"status": status}) # log_collection_status index 생성 수정 
        
    async def collect_logs(self):
        pass