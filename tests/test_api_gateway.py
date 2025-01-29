# tests/test_api_gateway.py
import pytest
import requests
import time
from enum import Enum

class State(Enum):
    INIT = "INIT"
    PAUSED = "PAUSED"
    RUNNING = "RUNNING"
    SHUTDOWN = "SHUTDOWN"

class TestAPIGateway:
    BASE_URL = "http://localhost:8197"
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and cleanup after tests"""
        # Wait for services to be ready
        max_retries = 30
        retry_count = 0
        while retry_count < max_retries:
            try:
                requests.get(f"{self.BASE_URL}/state")
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                retry_count += 1
        
        yield
        
        # Cleanup: Set state to SHUTDOWN at the end
        requests.put(f"{self.BASE_URL}/state", data="SHUTDOWN")
    
    def test_initial_state(self):
        """Test that system starts in INIT state"""
        response = requests.get(f"{self.BASE_URL}/state")
        assert response.status_code == 200
        assert response.text == State.INIT.value
    
    def test_state_change(self):
        """Test state transition to RUNNING"""
        response = requests.put(f"{self.BASE_URL}/state", data="RUNNING")
        assert response.status_code == 200
        assert "State changed successfully" in response.text
        
        response = requests.get(f"{self.BASE_URL}/state")
        assert response.status_code == 200
        assert response.text == State.RUNNING.value
    
    def test_invalid_state_change(self):
        """Test invalid state transition"""
        response = requests.put(f"{self.BASE_URL}/state", data="INVALID_STATE")
        assert response.status_code == 400
        assert "Invalid state" in response.text
    
    def test_run_log(self):
        """Test run log recording"""
        # Change state multiple times
        requests.put(f"{self.BASE_URL}/state", data="RUNNING")
        requests.put(f"{self.BASE_URL}/state", data="PAUSED")
        
        response = requests.get(f"{self.BASE_URL}/run-log")
        assert response.status_code == 200
        log_entries = response.text.split('\n')
        assert len(log_entries) >= 2  # At least two state changes
        assert "INIT->RUNNING" in response.text
        assert "RUNNING->PAUSED" in response.text
    
    def test_request_handling(self):
        """Test request handling in different states"""
        # Test in INIT state
        response = requests.get(f"{self.BASE_URL}/request")
        assert response.status_code == 503
        assert "System is not in RUNNING state" in response.text
        
        # Test in RUNNING state
        requests.put(f"{self.BASE_URL}/state", data="RUNNING")
        response = requests.get(f"{self.BASE_URL}/request")
        assert response.status_code in [200, 503]  # Either success or service unavailable
        
        # Test in PAUSED state
        requests.put(f"{self.BASE_URL}/state", data="PAUSED")
        response = requests.get(f"{self.BASE_URL}/request")
        assert response.status_code == 503
        assert "System is not in RUNNING state" in response.text

if __name__ == "__main__":
    pytest.main(["-v"])