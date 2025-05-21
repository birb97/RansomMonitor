# processors/validators.py
"""
Validation utilities for data integrity.

This module provides validation functions for different types of data:
- IP addresses
- Domain names
- Claim structure
"""

import logging
from utils.processor_utils import validate_ip, extract_ips_from_text

logger = logging.getLogger("validators")

class DataValidator:
    """
    Utility class for validating different types of data.
    
    This class provides static methods for common validation tasks 
    related to network identifiers and claim data.
    """
    
    @staticmethod
    def validate_ip(ip_address):
        """
        Validate if a string is a valid IP address.
        
        Args:
            ip_address (str): String to validate as IP
            
        Returns:
            bool: True if valid IP address, False otherwise
        """
        return validate_ip(ip_address)
    
    @staticmethod
    def extract_ips_from_text(text):
        """
        Extract potential IP addresses from raw text.
        
        This is an experimental feature that can find IPs in
        unstructured text like comments or descriptions.
        
        Args:
            text (str): Text to extract IPs from
            
        Returns:
            list: List of potential IP addresses
        """
        return extract_ips_from_text(text)
    
    @staticmethod
    def validate_domain(domain):
        """
        Validate if a string is a valid domain name.
        
        Args:
            domain (str): String to validate as domain
            
        Returns:
            bool: True if valid domain, False otherwise
        """
        if not domain:
            return False
            
        # Simple validation - more complex validation would use regex
        parts = domain.split('.')
        
        # Must have at least two parts and all parts must be valid
        if len(parts) < 2:
            return False
            
        for part in parts:
            # Each part must contain at least one character and only valid chars
            if not part or not all(c.isalnum() or c == '-' for c in part):
                return False
                
        # Top level domain can't be all numeric
        if parts[-1].isdigit():
            return False
            
        return True
        
    @staticmethod
    def validate_claim_data(claim_data):
        """
        Validate that claim data has all required fields.
        
        Args:
            claim_data (dict): Claim data to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = [
            "collector", 
            "threat_actor", 
            "name_network_identifier", 
            "timestamp"
        ]
        
        for field in required_fields:
            if field not in claim_data or claim_data[field] is None:
                return False, f"Missing required field: {field}"
                
        return True, None