from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import HTTPException, Request
import datetime
import socket
from fortigate_deployment import fortigate_parse
from fluentd_deployment import FluentdDeployment

class ElasticsearchCollector:
    def __init__(self, system: str, TAG_NAME: str):
        self.system = system
        print("==================")
        print(f"Initializing ElasticsearchCollector with system: {system}, TAG_NAME: {TAG_NAME}")
        print("==================")
        self.TAG_NAME = TAG_NAME
        self.es = AsyncElasticsearch("http://localhost:9200/")

    def get_hostname(self, client_ip):
        try:
            hostname = socket.gethostbyaddr(client_ip)[0]
            print("==================")
            print(f"Resolved hostname for IP {client_ip}: {hostname}")
            print("==================")
            return hostname
        except Exception as e:
            print("==================")
            print(f"Failed to get hostname for IP {client_ip}: {e}")
            print("==================")
            return client_ip

    async def create_index_if_not_exists(self, index_name, mapping=None):
        try:
            await self.es.indices.get(index=index_name)
            print("==================")
            print(f"Index {index_name} already exists.")
            print("==================")
        except NotFoundError:
            if mapping:
                await self.es.indices.create(index=index_name, body={"mappings": mapping})
                print("==================")
                print(f"Created index {index_name} with mapping.")
                print("==================")
            else:
                await self.es.indices.create(index=index_name)
                print("==================")
                print(f"Created index {index_name} without mapping.")
                print("==================")

    async def collect_logs(self, request, client_ip):
        try:
            log_request = await request.json()
            print("==================")
            print(f"Received log request: {log_request}")
            print("==================")
            if self.system == "fluentd":
                index_name = f"{self.TAG_NAME}_syslog"
            else:
                index_name = f"{self.system}_syslog"
            for log in log_request:
                if self.system == "fortigate":
                    log = await fortigate_parse(log['message'])
                elif self.system == "windows":
                    log = {k.lower(): v for k, v in log.items()}
                    if 'date' in log:
                        log['date'] = round(log['date'], 7)
                log['request_ip'] = client_ip
                log['client_hostname'] = self.get_hostname(client_ip=client_ip)
                log['TAG_NAME'] = self.TAG_NAME
                response = await self.es.index(index=index_name, document=log)
                print("==================")
                print(f"Indexed log to {index_name}: {response}")
                print("==================")
            return {"message": f"{self.TAG_NAME.title()} Log received successfully"}
        except Exception as e:
            print("==================")
            print(f"Error while collecting logs: {str(e)}")
            print("==================")
            raise HTTPException(status_code=500, detail=f"Error while collecting logs: {str(e)}")

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
        print("==================")
        print(f"Saved integration info to {index_name}: {response['result']}")
        print("==================")
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
                status = res['hits']['hits'][0]['_source'].get("status", "unknown")
                print("==================")
                print(f"Current status for {self.system} with TAG_NAME {self.TAG_NAME}: {status}")
                print("==================")
                return status
            else:
                print("==================")
                print(f"No status found for {self.system} with TAG_NAME {self.TAG_NAME}")
                print("==================")
                return "not_found"
        except NotFoundError:
            print("==================")
            print(f"No status found for {self.system} with TAG_NAME {self.TAG_NAME}")
            print("==================")
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
                print("==================")
                print(f"Updated status to {status} for {self.system} with TAG_NAME {self.TAG_NAME}")
                print("==================")
            else:
                print("==================")
                print(f"No document found to update status for {self.system} with TAG_NAME {self.TAG_NAME}")
                print("==================")
                raise HTTPException(status_code=404, detail="TAG_NAME not found")
        except Exception as e:
            print("==================")
            print(f"Error updating status: {str(e)}")
            print("==================")
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
                print("==================")
                print(f"Updated integration info for {self.system} with TAG_NAME {self.TAG_NAME}: {response['result']}")
                print("==================")
                return response
            else:
                print("==================")
                print(f"No document found to update integration info for {self.system} with TAG_NAME {self.TAG_NAME}")
                print("==================")
                raise HTTPException(status_code=404, detail="TAG_NAME not found")
        except Exception as e:
            print("==================")
            print(f"Error updating integration: {str(e)}")
            print("==================")
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
                print("==================")
                print(f"Deleted integration info for {self.system} with TAG_NAME {self.TAG_NAME}: {response['result']}")
                print("==================")
                return response
            else:
                print("==================")
                print(f"No document found to delete integration info for {self.system} with TAG_NAME {self.TAG_NAME}")
                print("==================")
                raise HTTPException(status_code=404, detail="TAG_NAME not found")
        except Exception as e:
            print("==================")
            print(f"Error deleting integration: {str(e)}")
            print("==================")
            raise HTTPException(status_code=500, detail=str(e))

    async def manage_integration(self, action: str, request: Request):
        config = await request.json()
        print("==================")
        print(f"Managing integration with action: {action}, system: {self.system}, TAG_NAME: {self.TAG_NAME}")
        print("==================")

        if self.system not in ['linux', 'windows', 'fortigate']:
            if config['new_log_tag'] != self.TAG_NAME:
                raise HTTPException(status_code=400, detail="TAG_NAME과 new_log_tag 값이 동일하여야 합니다.")

        client_ip = request.client.host
        client_hostname = self.get_hostname(client_ip)

        if self.system in ['linux', 'windows']:
            config = {
                "client_ip": client_ip,
                "client_hostname": client_hostname
            }
            print("==================")
            print(f"Config for system {self.system}: {config}")
            print("==================")
            if self.system == 'windows':
                index_name = f"{self.system}_syslog"
                mapping = {
                    "properties": {
                        "date": {
                            "type": "scaled_float",
                            "scaling_factor": 10000000  # 7자리까지 인식 가능하도록 설정
                        }
                    }
                }
                await self.create_index_if_not_exists(index_name, mapping)

        fluentd = FluentdDeployment()
        try:
            if action == "add":
                await self.save_integration(config)
                if self.system not in ['linux', 'windows']:  # genian, fortigate api 사용시 예외처리가 없음
                    await fluentd.configure_fluentd(config, self.system, self.TAG_NAME)
            elif action == "start":
                await self.update_status("started")
            elif action == "stop":
                await self.update_status("stopped")
            elif action == "delete":
                await self.delete_integration()
            elif action == "update":
                await self.update_integration(config)
                if self.system not in ['linux', 'windows']: 
                    await fluentd.configure_fluentd(config, self.system, self.TAG_NAME)
            else:
                raise HTTPException(status_code=400, detail="Invalid action or missing config for update")
            print("==================")
            print(f"Action {action} completed successfully for {self.system} with TAG_NAME {self.TAG_NAME}")
            print("==================")
        except Exception as e:
            print("==================")
            print(f"Error managing integration: {str(e)}")
            print("==================")
            raise HTTPException(status_code=500, detail=f"Error managing integration: {str(e)}")

