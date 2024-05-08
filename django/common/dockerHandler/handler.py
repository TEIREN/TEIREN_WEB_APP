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
        result = self.client.containers.get(container_id).stop()
        return result
    
    def remove_container(self, container_id) -> None:
        self.client.containers.get(container_id).remove()
    
    def create_container(self, image_name, environment):
        try:
            self.client.images.get(image_name)
        except docker.errors.ImageNotFound:
            print(f"Downloading image {image_name}...")
            try:
                self.client.images.pull(image_name)
            except Exception as e:
                print(f"Wrong image name {e}")
                
        container = self.client.containers.run(
            image_name,
            detach=True,
            environment=environment,
            command='python /app/proc.py'
        )
        return container
        
    """Docker Images"""
    def get_docker_image_list(self) -> list:
        return self.client.images.list()