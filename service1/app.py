from flask import Flask, jsonify
import psutil
import socket
import time
import requests
import os
import signal

app = Flask(__name__)

def get_ip_address():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

def get_running_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        processes.append(proc.info)
    return processes

def get_disk_space():
    disk_info = psutil.disk_usage('/')
    return disk_info.free / (1024 ** 3)  # Convert to GB

def get_time_since_boot():
    return time.time() - psutil.boot_time()

def get_service2_info(service_url):
    retries = 10
    wait_time = 1
    while retries > 0:
        try:
            response = requests.get(service_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching service 2 info: {e}. Retrying...")
            retries -= 1
            time.sleep(wait_time)
    return {"error": "Could not fetch service info after multiple attempts."}


@app.route('/stop', methods=['POST'])
def stop_system():
    # Send SIGTERM to parent process (Docker container)
    os.kill(1, signal.SIGTERM)
    return jsonify({"message": "Shutting down..."})

@app.route('/')
def info():
    service1_info = {
        'Service1': {
            'ip_address': get_ip_address(),
            'running_processes': get_running_processes(),
            'disk_space': get_disk_space(),
            'time_since_boot_seconds': get_time_since_boot()
        }
    }
    service2_info = get_service2_info('http://service2:3000/info')
    response = {
        "Service 1": service1_info,
        "Service 2": service2_info
    }
    # Add 2-second delay after responding
    time.sleep(2)
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
