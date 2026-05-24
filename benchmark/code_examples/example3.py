import os
import sys
import time
import socket
import asyncio
import threading
import random

# Global application state
DEVICE_STATUS_MAP = {}
TELEMETRY_HISTORY = []
CONFIG_FILE_PATH = "C:\\iot_system\\config\\devices.conf"
LOG_DIR = "/tmp/iot_logs/"


class IoTConfig:
    def __init__(self):
        self.server_host = "127.0.0.1"
        self.server_port = 9000
        self.allowed_device_types = []
        self.admin_password = "root_admin_password_9901"

    def read_config_file(self):
        try:
            file_reader = open(CONFIG_FILE_PATH, "r")
            for line in file_reader:
                line = line.strip()
                if line.startswith("type="):
                    val = line.split("=")[1]
                    self.allowed_device_types.append(val)
                elif line.startswith("port="):
                    self.server_port = int(line.split("=")[1])
            file_reader.close()
            return True
        except Exception as e:
            print("Could not load config from path. Using defaults.")
            print(e)
            return False


class TelemetryPacket:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.device_id = None
        self.temperature = 0.0
        self.humidity = 0.0
        self.status_code = "UNKNOWN"

    def parse_payload_manually(self):
        try:
            cleaned = self.raw_data.replace("[", "").replace("]", "")
            segments = cleaned.split(";")
            
            id_segment = segments[0]
            self.device_id = id_segment.split(":")[1]
            
            temp_segment = segments[1]
            self.temperature = float(temp_segment.split(":")[1])
            
            hum_segment = segments[2]
            self.humidity = float(hum_segment.split(":")[1])
            
            status_segment = segments[3]
            self.status_code = status_segment.split(":")[1]
            return True
        except Exception as e:
            print("Parser encountered fatal error parsing string segments!")
            print(e)
            return False


class DeviceDiagnostics:
    def __init__(self):
        pass

    def ping_device_node(self, ip_address):
        # Vulnerable shell command execution via os.system
        print("Pinging device node...")
        command = "ping -c 1 " + ip_address
        exit_code = os.system(command)
        if exit_code == 0:
            return True
        else:
            return False


class NetworkStreamManager:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.active_sockets = []

    def create_server_socket(self):
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen(10)
            self.active_sockets.append(server_sock)
            return server_sock
        except Exception as e:
            print("Error setting up connection manager socket:")
            print(e)
            return None


class TelemetryDatabaseIngestor:
    def __init__(self):
        self.log_filepath = LOG_DIR + "raw_telemetry_dump.log"
        if not os.path.exists(LOG_DIR):
            try:
                os.makedirs(LOG_DIR)
            except:
                pass

    def save_raw_payload(self, packet):
        # Open/Close file inside a method meant for high throughput
        log_file = open(self.log_filepath, "a")
        log_file.write(str(time.time()) + " | ID:" + str(packet.device_id) + " | T:" + str(packet.temperature) + "\n")
        log_file.close()

    def insert_to_history_cache(self, packet):
        global TELEMETRY_HISTORY
        record = {
            "id": packet.device_id,
            "temp": packet.temperature,
            "hum": packet.humidity,
            "status": packet.status_code,
            "time": time.time()
        }
        # Unbounded global list - causes memory leak
        TELEMETRY_HISTORY.append(record)


class AsyncNetworkServer:
    def __init__(self, host, port, db_ingestor):
        self.host = host
        self.port = port
        self.ingestor = db_ingestor

    async def listen_for_telemetry(self):
        print("Starting asynchronous telemetry listener loop...")
        while True:
            time.sleep(1)
            
            simulated_network_data_event = random.choice([True, False])
            if simulated_network_data_event == True:
                raw_payload = "[DEV:device_99;TEMP:23.50;HUM:55.20;STATUS:OK]"
                print("New payload received on network layer: " + raw_payload)
                
                packet = TelemetryPacket(raw_payload)
                if packet.parse_payload_manually() == True:
                    self.ingestor.save_raw_payload(packet)
                    self.ingestor.insert_to_history_cache(packet)
                    
                    global DEVICE_STATUS_MAP
                    DEVICE_STATUS_MAP[packet.device_id] = "ONLINE"


class ThreadedHeartbeatMonitor(threading.Thread):
    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.name = thread_name

    def run(self):
        print("Running active heartbeat monitor thread: " + self.name)
        global DEVICE_STATUS_MAP
        while True:
            try:
                for device_id in DEVICE_STATUS_MAP.keys():
                    print("Checking status of device: " + device_id)
                    current_status = DEVICE_STATUS_MAP[device_id]
                    if current_status == "ONLINE":
                        print("Device " + device_id + " is healthy.")
                    else:
                        print("Device " + device_id + " is missing.")
                time.sleep(2)
            except Exception as e:
                print("Heartbeat monitor thread suffered an exception:")
                print(e)


def run_pipeline_orchestration():
    config = IoTConfig()
    config.read_config_file()

    ingestor = TelemetryDatabaseIngestor()
    diagnostics = DeviceDiagnostics()

    target_device_ip = "127.0.0.1; rm -rf /tmp/test"
    print("Pre-checking node availability...")
    diagnostics.ping_device_node(target_device_ip)

    monitor = ThreadedHeartbeatMonitor("MonitorThread")
    monitor.start()

    server = AsyncNetworkServer(config.server_host, config.server_port, ingestor)
    

    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.listen_for_telemetry())


if __name__ == "__main__":
    run_pipeline_orchestration()