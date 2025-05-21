# processors/extractors.py
"""
Network identifier extraction utilities.

This module provides functionality for extracting network identifiers
from various data sources, particularly ransomware claims.
"""

import logging
import re
from utils.domain_utils import normalize_domain
from utils.processor_utils import extract_ips_from_text

logger = logging.getLogger("extractors")

class NetworkIdentifierExtractor:
    """
    Utility for extracting network identifiers from data.
    
    This class provides methods for extracting identifiers from:
    - Claim data structures
    - Raw text (experimental)
    """
    
    @staticmethod
    def extract_identifiers(claim):
        """
        Extract network identifiers from a claim.
        
        Args:
            claim (dict): Claim data to extract identifiers from
            
        Returns:
            list: List of identifier dictionaries with 'type' and 'value' keys
        """
        identifiers = []
        
        # Extract name identifier
        if claim.get("name_network_identifier"):
            identifiers.append({
                "type": "name",
                "value": claim["name_network_identifier"]
            })
            
        # Extract IP identifier
        if claim.get("ip_network_identifier"):
            identifiers.append({
                "type": "ip",
                "value": claim["ip_network_identifier"]
            })
            
        # Extract domain identifier
        if claim.get("domain_network_identifier"):
            identifiers.append({
                "type": "domain",
                "value": claim["domain_network_identifier"]
            })
            
        logger.debug(f"Extracted {len(identifiers)} identifiers from claim")
        return identifiers
    
    @staticmethod
    def extract_domains_from_text(text):
        """
        Extract potential domain names from raw text.
        
        This is an experimental feature that can find domains in
        unstructured text like comments or descriptions.
        
        Args:
            text (str): Text to extract domains from
            
        Returns:
            list: List of potential domain names
        """
        if not text:
            return []
            
        # Basic domain pattern (simplified)
        pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
        matches = re.findall(pattern, text)
        
        # Normalize the domains
        domains = []
        for match in matches:
            normalized = normalize_domain(match)
            if normalized and normalized not in domains:
                domains.append(normalized)
                
        logger.debug(f"Extracted {len(domains)} potential domains from text")
        return domains
    
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