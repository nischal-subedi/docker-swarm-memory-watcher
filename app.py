import docker
import time
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os
from notification import send_notification

# set your server ip here
# TODO: fetch ip from system via os module
server_ip='192.168.123.123'

def setup_logging(log_dir='logs'):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    log_file = os.path.join(log_dir, 'memorywatcher.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # perfile size is 10mb which is the maximum before rotation
        backupCount=5,  # max 5 files kept before their deletion
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    logger = logging.getLogger('DockerMonitor')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

class DockerServiceMonitor:
    def __init__(self, service_name, memory_threshold_mb=300, log_dir='logs'):
        self.service_name = service_name
        self.memory_threshold = memory_threshold_mb * 1024 * 1024  #this is mb to byte
        self.logger = setup_logging(log_dir)
        self.client = self.get_docker_client()

    def get_docker_client(self):
        try:
            return docker.from_env()
        except Exception as e:
            self.logger.error(f"Failed to connect to Docker: {str(e)}")
            self.logger.error(f"Is the docker daemon running??")
            raise

    def get_service(self):
        try:
            services = self.client.services.list(filters={'name': self.service_name})
            if services:
                return services[0]
            raise Exception(f"Service {self.service_name} not found")
        except Exception as e:
            self.logger.error(f"Error getting service: {str(e)}")
            raise

    def get_container_stats(self, container):
        try:
            stats = container.stats(stream=False)
            memory_usage = stats['memory_stats']['usage']
            return memory_usage
        except Exception as e:
            self.logger.error(f"Error getting container stats: {str(e)}")
            return None

    def force_update_service(self, service):
        try:
            self.logger.info(f"Force updating service {self.service_name}")
            service.update(force_update=True)
            self.logger.info("Service update initiated successfully")
        except Exception as e:
            self.logger.error(f"Error updating service: {str(e)}")
            raise

    def clean_old_logs(self, max_age_days=30):
        try:
            current_time = time.time()
            log_dir = 'logs'
            for filename in os.listdir(log_dir):
                if filename.startswith('memorywatcher.log.'):
                    filepath = os.path.join(log_dir, filename)
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > (max_age_days * 86400): 
                        os.remove(filepath)
                        self.logger.info(f"Removed old log file: {filename}")
        except Exception as e:
            self.logger.error(f"Error cleaning old logs: {str(e)}")

    def monitor(self, check_interval=30):
        self.logger.info(f"Starting monitoring of service {self.service_name}")
        self.logger.info(f"Memory threshold set at: {self.memory_threshold/(1024*1024):.2f} MB")
        
        while True:
            try:

                service = self.get_service()
                tasks = service.tasks(filters={'desired-state': 'running'})
                
                if not tasks:
                    self.logger.warning("No running tasks found")
                    time.sleep(check_interval)
                    continue

                container_id = tasks[0]['Status']['ContainerStatus']['ContainerID']
                container = self.client.containers.get(container_id)
                memory_usage = self.get_container_stats(container)

                if memory_usage is None:
                    continue

                self.logger.info(f"Current {self.service_name} memory usage: {memory_usage / (1024*1024):.2f} MB")

                if memory_usage > self.memory_threshold:
                    self.logger.warning(f"Memory threshold exceeded: {memory_usage / (1024*1024):.2f} MB/ {self.memory_threshold/(1024*1024):.2f} MB")
                    send_notification(self.service_name, server_ip)
                    self.force_update_service(service)
                    self.logger.info("Waiting 30s for service to stabilize...")
                    time.sleep(30)

            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")
                time.sleep(check_interval)
            
            time.sleep(check_interval)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Swarm service memory monitor')
    parser.add_argument('--service', default='fastapi', help='service name to be monitored')
    parser.add_argument('--threshold', type=int, default=1024, help='Memory threshold before update is trigerred')
    parser.add_argument('--interval', type=int, default=10, help='Polling interval')
    parser.add_argument('--log-dir', default='logs', help='Log directory')

    args = parser.parse_args()

    try:
        monitor = DockerServiceMonitor(
            service_name=args.service,
            memory_threshold_mb=args.threshold,
            log_dir=args.log_dir
        )
        
        monitor.monitor(check_interval=args.interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"\nFailed to start monitoring: {str(e)}")