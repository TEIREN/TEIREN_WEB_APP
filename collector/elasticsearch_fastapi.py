from fastapi import FastAPI, HTTPException
from elsasticsearch_collector_renew import ElasticsearchCollector

import requests
import asyncio


app = FastAPI()


@app.post("/add_integration/{system}")
async def add_integration(request, system):
    integration = ElasticsearchCollector(sytem=system)
    pass

@app.post("/collector/{action}/{system}")
async def collector_action(request, action, system):
    es = ElasticsearchCollector(sytem=system)
    result = getattr(es,action)()
    pass 

@app.post("/collect_log/{system}")
async def add_integration(request, system):
    integration = ElasticsearchCollector(sytem=system)
    pass