from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import HTTPException
import datetime
import logging
import socket
from fortigate_deployment import fortigate_parse
from fluentd_deployment import FluentdDeployment

class ElasticsearchCollector:
    def __init__(self, system: str, TAG_NAME: str):
        self.system = system
        self.TAG_NAME = TAG_NAME
        self.es = AsyncElasticsearch("http://localhost:9200/")

    def get_hostname(self, client_ip):
        try:
            return socket.gethostbyaddr(client_ip)[0]
        except Exception as e:
            logging.error(f"Failed to get hostname: {e}")
            return client_ip

    async def create_index_with_mapping(self, index_name, mapping):
        try:
            if not await self.es.indices.exists(index=index_name):
                await self.es.indices.create(index=index_name, body={"mappings": mapping})
        except Exception as e:
            logging.error(f"Failed to create index with mapping: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create index with mapping: {e}")

    async def create_index_if_not_exists(self, index_name):
        try:
            await self.es.indices.get(index=index_name)
        except NotFoundError:
            await self.es.indices.create(index=index_name)

    async def collect_logs(self, request, client_ip):
        try : 
            if self.system == "fluentd":
                index_name = f"{self.TAG_NAME}_syslog"
            else:
                index_name = f"{self.system}_syslog"
            for log in request:
                if self.system == "fortigate":
                    log = await fortigate_parse(log['message'])
                log['request_ip'] = client_ip
                log['client_hostname'] = self.get_hostname(client_ip=client_ip)
                log['TAG_NAME'] = self.TAG_NAME
                response = await self.es.index(index=index_name, document=log)

            return {"message": f"{self.TAG_NAME.title()} Log received successfully"}
        
        except :
            raise HTTPException(status_code=500, detail=str("no logs found"))

    async def save_integration(self, config):
        index_name = "integration_info"
        await self.create_index_if_not_exists(index_name)
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"SYSTEM": self.system}},
                        {"match": {"TAG_NAME": self.TAG_NAME}}
                    ]
                }
            }
        }
        res = await self.es.search(index=index_name, body=query)
        if res['hits']['total']['value'] > 0:
            raise HTTPException(status_code=400, detail=f"{self.TAG_NAME}이 이미 사용중입니다.")
        log = {
            "SYSTEM": self.system,
            "TAG_NAME": self.TAG_NAME,
            "inserted_at": datetime.datetime.now(),
            "status": "started",
            "config": config
        }
        response = await self.es.index(index=index_name, document=log)
        print(f"{index_name}_log: {response['result']}")
        return response

    async def get_status(self):
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"SYSTEM": self.system}},
                            {"match": {"TAG_NAME": self.TAG_NAME}}
                        ]
                    }
                }
            }
            res = await self.es.search(index="integration_info", body=query)
            if res['hits']['total']['value'] > 0:
                return res['hits']['hits'][0]['_source'].get("status", "unknown")
            else:
                return "not_found"
        except NotFoundError:
            return "not_found"

    async def update_status(self, status: str):
        index_name = "integration_info"
        await self.create_index_if_not_exists(index_name)
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"SYSTEM": self.system}},
                        {"match": {"TAG_NAME": self.TAG_NAME}}
                    ]
                }
            }
        }
        try:
            res = await self.es.search(index=index_name, body=query)
            if res['hits']['total']['value'] > 0:
                doc_id = res['hits']['hits'][0]['_id']
                await self.es.update(index=index_name, id=doc_id, body={"doc": {"status": status}})
            else:
                raise HTTPException(status_code=404, detail="TAG_NAME not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def update_integration(self, config):
        index_name = "integration_info"
        await self.create_index_if_not_exists(index_name)
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"SYSTEM": self.system}},
                        {"match": {"TAG_NAME": self.TAG_NAME}}
                    ]
                }
            }
        }
        try:
            res = await self.es.search(index=index_name, body=query)
            if res['hits']['total']['value'] > 0:
                doc_id = res['hits']['hits'][0]['_id']
                log = {
                    "SYSTEM": self.system,
                    "TAG_NAME": self.TAG_NAME,
                    "inserted_at": datetime.datetime.now(),
                    "status": "started",
                    "config": config
                }
                response = await self.es.index(index=index_name, id=doc_id, document=log)
                print(f"{index_name}_log: {response['result']}")
                return response
            else:
                raise HTTPException(status_code=404, detail="TAG_NAME not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_integration(self):
        index_name = "integration_info"
        await self.create_index_if_not_exists(index_name)
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"SYSTEM": self.system}},
                        {"match": {"TAG_NAME": self.TAG_NAME}}
                    ]
                }
            }
        }
        try:
            res = await self.es.search(index=index_name, body=query)
            if res['hits']['total']['value'] > 0:
                doc_id = res['hits']['hits'][0]['_id']
                response = await self.es.delete(index=index_name, id=doc_id)
                print(f"{index_name}_log: {response['result']}")
                return response
            else:
                raise HTTPException(status_code=404, detail="TAG_NAME not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def manage_integration(self, action: str, request):
        if action == "add":
            config = await request.json()
            await self.save_integration(config)
            fluentd = FluentdDeployment()
            await fluentd.configure_fluentd(config, self.system, self.TAG_NAME)
        elif action == "start":
            await self.update_status("started")
        elif action == "stop":
            await self.update_status("stopped")
        elif action == "delete":
            await self.delete_integration()
        elif action == "update":
            config = await request.json()
            await self.update_integration(config)
            fluentd = FluentdDeployment()
            await fluentd.configure_fluentd(config, self.system, self.TAG_NAME)
        else:
            raise HTTPException(status_code=400, detail="Invalid action or missing config for update")
