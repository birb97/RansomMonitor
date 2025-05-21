# collectors/droplet_proxy.py
from typing import List, Dict, Any, Optional
from .base import BaseCollector
import requests
import hmac
import hashlib
import time
import logging
import random
from utils.error_utils import handle_exception, NetworkError

class DropletProxyCollector(BaseCollector):
    """Collector that delegates .onion requests to a dedicated Droplet"""
    
    def __init__(self, name, onion_url, parser_type="generic"):
        """
        Initialize the Droplet proxy collector.
        
        Args:
            name: Name of the collector
            onion_url: Onion URL to collect from
            parser_type: Type of parser to use on the Droplet
        """
        super().__init__(name, onion_url)
        # Load configuration from your existing config system
        from config import Config
        config = Config()
        self.endpoint = config.get_droplet_endpoint()
        self.api_secret = config.get_droplet_api_secret()
        self.parser_type = parser_type
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    def collect(self):
        """Default collect method that delegates to specialized methods"""
        self.logger.info(f"Collecting from {self.name} using {self.parser_type} parser")
        
        # Check if Tor proxy is available before attempting collection
        if not self._is_tor_proxy_available():
            self.logger.warning(f"Tor proxy not available. Skipping collection for {self.name}")
            return []
            
        return self._process_response(self._collect_via_droplet())
        
    def _collect_via_droplet(self):
        """
        Request collection via the Droplet API with retry mechanism.
        
        Returns:
            Dictionary with response data or None if error
        """
        retries = 0
        while retries < self.max_retries:
            try:
                # Generate a secure API key
                timestamp = str(int(time.time()))
                signature = hmac.new(
                    self.api_secret.encode(), 
                    timestamp.encode(),
                    hashlib.sha256
                ).hexdigest()
                api_key = f"{timestamp}:{signature}"
                
                # Make request to Droplet API
                self.logger.debug(f"Requesting {self.base_url} via Droplet with parser {self.parser_type}")
                
                # Ensure the URL is properly formatted
                target_url = self.base_url
                if not target_url.startswith(("http://", "https://")):
                    target_url = f"http://{target_url}"
                
                response = requests.post(
                    f"{self.endpoint}/collect",
                    headers={
                        "X-API-Key": api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": target_url, 
                        "parser": self.parser_type,
                        "timeout": 120  # Extended timeout for Tor
                    },
                    timeout=300  # 5 minutes total timeout for the API call
                )
                
                # Check for error status codes
                if response.status_code >= 400:
                    self.logger.error(f"Droplet API error: {response.status_code}")
                    if response.headers.get('Content-Type', '').startswith('application/json'):
                        try:
                            error_details = response.json()
                            self.logger.error(f"Error details: {error_details}")
                        except:
                            pass
                    
                    # Only retry on specific error codes or connection errors
                    if response.status_code in (429, 500, 502, 503, 504):
                        retries += 1
                        if retries < self.max_retries:
                            delay = self.retry_delay + random.uniform(0, 2)  # Add jitter
                            self.logger.info(f"Retrying in {delay:.1f} seconds...")
                            time.sleep(delay)
                            continue
                        else:
                            return None
                    else:
                        # Don't retry on 4xx errors except those listed above
                        return None
                
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                self.logger.error(f"Request error: {e}")
                retries += 1
                if retries < self.max_retries:
                    delay = self.retry_delay + random.uniform(0, 2)  # Add jitter
                    self.logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    return None
            except ValueError as e:
                self.logger.error(f"Error parsing JSON response from Droplet: {e}")
                return None
        
        return None
    
    def _process_response(self, data):
        """
        Process the response from the Droplet.
        This method should be overridden by subclasses for custom processing.
        
        Args:
            data: Response data from the Droplet
            
        Returns:
            List of processed claims
        """
        if not data:
            return []
            
        # Check for error in response
        if isinstance(data, dict) and "error" in data:
            self.logger.error(f"Error from Droplet: {data['error']}")
            return []
            
        # Default processing just returns an empty list
        # Subclasses should implement their own processing
        return []
    
    def _is_tor_proxy_available(self) -> bool:
        """
        Check if the Tor proxy is available by making a request to the health endpoint.
        
        Returns:
            bool: True if Tor proxy is available and working, False otherwise
        """
        try:
            import requests
            health_url = f"{self.endpoint}/health"
            
            # Make a quick health check request with short timeout
            response = requests.get(health_url, timeout=5)
            
            if response.status_code != 200:
                self.logger.warning(f"Tor proxy health check failed with status code: {response.status_code}")
                return False
                
            status = response.json()
            tor_working = status.get("tor_working", False)
            
            if not tor_working:
                self.logger.warning("Tor proxy is available but not properly configured")
                
            return tor_working
            
        except requests.RequestException as e:
            self.logger.warning(f"Tor proxy health check failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking Tor proxy: {str(e)}")
            return False