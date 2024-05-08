from common.dockerHandler.handler import DockerHandler
from common.neo4j.handler import Neo4jHandler


def refresh_container_status(integration_list, user_db) -> dict:
    ihandler = IntegrationHandler(integration_list, user_db)
    integration_result = ihandler.update_container_status()
    return {
        'integrations': integration_result
    }

class IntegrationHandler(DockerHandler, Neo4jHandler):
    """This Class is Integration handler.
    - refresh integration list

    Args:
        DockerHandler (class) Docker SDK
        Neo4jHandler (class): Neo4j Controller
    """
    def __init__(self, integration_list, user_db) -> None:
        super().__init__()
        DockerHandler.__init__(self)
        Neo4jHandler.__init__(self)
        self.integration_list = integration_list
        self.user_db = user_db
    
    def update_container_status(self) -> dict:
        __integration_list = list()
        for _ in self.integration_list['integrations']:
            data = dict(_)
            container_status = self.status(data['container_id'])
            if container_status in ['exited', 'Not Found', 'Error'] and data['isRunning'] == 1:
                data['status'] = container_status
                data['isRunning'] = 0 if self.change_container_status(container_id=data['container_id'], status=0) else 2
            if container_status == 'running' and data['isRunning'] == 0:
                data['status'] = 'running'
                data['isRunning'] = 1 if self.change_container_status(container_id=data['container_id'], status=0) else 2
            __integration_list.append(data)
            
        return __integration_list
                
    def change_container_status(self, container_id:str, status:int):
        cypher = f"""
        MATCH (i:Integration)
        WHERE i.container_id = '{container_id}'
        SET i.isRunning = {status}
        RETURN 1
        """
        try:
            self.run(database=self.user_db, query=cypher)
            return True
        except Exception as e:
            print(e)
            return False