# collectors/base.py
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import requests
from utils.domain_utils import normalize_domain
from utils.time_utils import parse_timestamp
from utils.types import ClaimDict  # Import the type alias
import abc
from utils.error_utils import handle_exception, NetworkError



class BaseCollector(abc.ABC):
    """
    Abstract base class for intelligence collectors.
    
    This class provides common functionality for all collector implementations:
    - HTTP request handling
    - Domain normalization
    - Timestamp parsing
    - Logging
    
    All collector implementations should inherit from this class and implement
    the collect() method to gather and process data from their specific source.
    """
    
    def __init__(self, name: str, base_url: str) -> None:
        """
        Initialize the collector.
        
        Args:
            name: Name of the collector
            base_url: Base URL for API requests
        """
        self.name = name
        self.base_url = base_url
        self.logger = logging.getLogger(f"collector.{name}")
    
    @abc.abstractmethod
    def collect(self) -> List[ClaimDict]:
        """
        Collect data from the source API.
        
        This method must be implemented by all subclasses.
        
        Returns:
            List of processed claims
        """
        pass
    
    def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make a request to the API endpoint.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            JSON response or None if error occurred
        """
        try:
            url = f"{self.base_url}{endpoint}"
            self.logger.debug(f"Making request to {url}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return handle_exception(
                e, 
                self.logger, 
                f"Error making request to {url}", 
                reraise=False, 
                reraise_as=NetworkError,
                default_return=None
            )
    
    def normalize_domain(self, domain: Optional[str]) -> str:
        """
        Normalize domain for consistent comparison.
        
        Uses the utility function from utils.domain_utils.
        
        Args:
            domain: Domain string to normalize
            
        Returns:
            Normalized domain or empty string if input was None/empty
        """
        return normalize_domain(domain)
    
    def parse_timestamp(self, datetime_str: Optional[str]) -> datetime:
        """
        Parse a datetime string with flexible format handling.
        
        Args:
            datetime_str: String representation of datetime
            
        Returns:
            Parsed datetime object or current time if parsing fails
        """
        return parse_timestamp(datetime_str)
