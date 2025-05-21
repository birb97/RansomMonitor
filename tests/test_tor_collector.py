# tests/test_tor_collector.py
"""
Test cases for the Tor collection service.

This module contains tests for verifying the Tor proxy connection
and the collection agent functionality.
"""

import requests
import time
import hmac
import hashlib
import json
import socket
from unittest.mock import patch

from test_framework import TestCase
from tests.test_registry import register_test_case

@register_test_case
class TorCollectorTestCase(TestCase):
    """Tests for Tor collector functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent_url = "http://localhost:5000"
        self.api_secret = "test-secret"
    
    def create_api_key(self):
        """Create a properly formatted API key with current timestamp"""
        timestamp = str(int(time.time()))
        signature = hmac.new(
            self.api_secret.encode(),
            timestamp.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}:{signature}"
    
    def test_health_endpoint(self):
        """Test the health endpoint responds correctly"""
        try:
            response = requests.get(f"{self.agent_url}/health")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("tor_configured", data)
            self.logger.info(f"Tor configuration: {data['tor_configured']}")
        except requests.RequestException as e:
            self.fail(f"Health endpoint test failed: {str(e)}")
    
    def test_tor_collection(self):
        """Test the collect endpoint with Tor functionality"""
        try:
            # Generate proper API key
            api_key = self.create_api_key()
            
            response = requests.post(
                f"{self.agent_url}/collect",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": api_key
                },
                json={
                    "url": "https://check.torproject.org",
                    "parser": "generic"
                },
                timeout=30
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Verify we're using Tor
            self.assertTrue(data.get("is_using_tor", False), 
                           "Tor connection not confirmed")
            
            # Check for test victim data
            self.assertIn("victims", data)
            if data["victims"]:
                self.logger.info(f"Found test data: {data['victims'][0]['name']}")
        except requests.RequestException as e:
            self.fail(f"Tor collection test failed: {str(e)}")
    
    def test_tor_port_isolation(self):
        """Verify the Tor port is not accessible directly from host"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex(('localhost', 9150))
            self.assertNotEqual(result, 0, "Security risk: Tor SOCKS port is accessible from host")
            s.close()
        except Exception as e:
            self.fail(f"Port check failed: {str(e)}")