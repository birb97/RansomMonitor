# utils/processor_utils.py
"""
Common utilities for data processing, validation, and extraction.
"""
import re
import ipaddress
import logging

logger = logging.getLogger("utils.processor_utils")

def validate_ip(ip_address):
    """
    Validate if a string is a valid IP address.
    
    Args:
        ip_address (str): String to validate as IP
        
    Returns:
        bool: True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip_address)
        return True
    except (ValueError, TypeError):
        return False

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
    if not text:
        return []
        
    # IPv4 pattern
    ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ipv4_matches = re.findall(ipv4_pattern, text)
    
    # Validate the matches using the utility function
    ips = []
    for match in ipv4_matches:
        if validate_ip(match) and match not in ips:
            ips.append(match)
            
    logger.debug(f"Extracted {len(ips)} potential IP addresses from text")
    return ips