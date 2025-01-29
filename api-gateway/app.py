# api-gateway/app.py
from flask import Flask, request, Response
from enum import Enum
from datetime import datetime
import os
import docker
import json

app = Flask(__name__)

class State(Enum):
    INIT = "INIT"
    PAUSED = "PAUSED"
    RUNNING = "RUNNING"
    SHUTDOWN = "SHUTDOWN"

class StateManager:
    def __init__(self):
        self.current_state = State.INIT
        self.run_log = []
        self.docker_client = docker.from_env()
        
    def change_state(self, new_state):
        if not isinstance(new_state, State):
            try:
                new_state = State(new_state)
            except ValueError:
                return False, "Invalid state"
                
        if new_state == self.current_state:
            return True, "State unchanged"
            
        # Log the state change
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H.%M:%S.%fZ')[:-4]
        log_entry = f"{timestamp}: {self.current_state.value}->{new_state.value}"
        self.run_log.append(log_entry)
        
        # Handle special cases
        if new_state == State.SHUTDOWN:
            try:
                containers = self.docker_client.containers.list()
                for container in containers:
                    container.stop()
                self.current_state = new_state
                return True, "System shutdown initiated"
            except Exception as e:
                return False, f"Shutdown failed: {str(e)}"
                
        self.current_state = new_state
        return True, "State changed successfully"
        
    def get_state(self):
        return self.current_state.value
        
    def get_run_log(self):
        return "\n".join(self.run_log)
        
    def can_process_requests(self):
        return self.current_state == State.RUNNING

state_manager = StateManager()

@app.route('/state', methods=['GET', 'PUT'])
def handle_state():
    if request.method == 'GET':
        return Response(state_manager.get_state(), mimetype='text/plain')
    else:  # PUT
        new_state = request.data.decode('utf-8')
        success, message = state_manager.change_state(new_state)
        if success:
            return Response(message, status=200)
        return Response(message, status=400)

@app.route('/run-log', methods=['GET'])
def get_run_log():
    return Response(state_manager.get_run_log(), mimetype='text/plain')

@app.route('/request', methods=['GET'])
def handle_request():
    if not state_manager.can_process_requests():
        return Response("System is not in RUNNING state", status=503)
        
    try:
        # Forward request to one of the service1 instances through nginx
        import requests
        response = requests.get('http://nginx/api/')
        return Response(response.text, mimetype='text/plain')
    except Exception as e:
        return Response(f"Error processing request: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8197)