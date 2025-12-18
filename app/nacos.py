import os
import nacos
import logging
import threading
import time
import socket

# Configure logging
logger = logging.getLogger(__name__)

class NacosManager:
    def __init__(self):
        self.server_addr = os.getenv("NACOS_SERVER_ADDR", "localhost:8848")
        self.username = os.getenv("NACOS_USERNAME", "nacos")
        self.password = os.getenv("NACOS_PASSWORD", "nacos")
        self.namespace = os.getenv("NACOS_NAMESPACE", "")
        self.service_name = os.getenv("NACOS_SERVICE_NAME", "ai-center")
        self.group_name = os.getenv("NACOS_GROUP_NAME", "DEFAULT_GROUP")
        
        # Determine internal IP
        self.ip = self._get_internal_ip()
        self.port = int(os.getenv("PORT", "8000"))
        
        self.client = None
        self._heartbeat_thread = None
        self._stop_heartbeat = False

    def _get_internal_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def register(self):
        try:
            logger.info(f"Registering service {self.service_name} to Nacos at {self.server_addr}")
            self.client = nacos.NacosClient(self.server_addr, namespace=self.namespace, username=self.username, password=self.password)
            
            # Register instance
            self.client.add_naming_instance(self.service_name, self.ip, self.port, group_name=self.group_name)
            logger.info(f"Successfully registered {self.service_name} ({self.ip}:{self.port}) to Nacos")
            
            # Start heartbeat thread (if needed by the SDK, though modern SDKs might handle it)
            # In some versions of nacos-sdk-python, heartbeat is automatic. 
            # In others, we might need to manually send heartbeats.
            # For 2.x, it's usually managed.
            
        except Exception as e:
            logger.error(f"Failed to register with Nacos: {e}")

    def deregister(self):
        if self.client:
            try:
                logger.info(f"Deregistering service {self.service_name} from Nacos")
                self.client.remove_naming_instance(self.service_name, self.ip, self.port, group_name=self.group_name)
            except Exception as e:
                logger.error(f"Failed to deregister from Nacos: {e}")

nacos_manager = NacosManager()
