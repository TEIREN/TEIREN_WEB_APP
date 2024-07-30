import docker

class DockerHandler:
    def __init__(self) -> None:
        self.client = docker.from_env()
    
    def get_container_list(self) -> list:
        return self.client.containers.list()
    
    def get_container(self, container_id):
        return self.client.containers.get(container_id)
    
    def start_container(self, container_id) -> None:
        self.client.containers.get(container_id).start()
    
    def stop_container(self, container_id) -> None:
        self.client.containers.get(container_id).stop()
    
    def remove_container(self, container_id) -> None:
        self.client.containers.get(container_id).remove()
    
    def create_container(self, image_name, environment):
        container = self.client.containers.run(
            image_name,
            detach=True,
            environment=environment,
        )
        return container
        
    """Docker Images"""
    def get_docker_image_list(self) -> list:
        return self.client.images.list()