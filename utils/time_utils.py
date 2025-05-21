# utils/time_utils.py
"""
Utilities for handling time and date operations.
"""

from datetime import datetime
import logging

logger = logging.getLogger("utils.time_utils")

def parse_timestamp(datetime_str):
    """
    Parse a datetime string with flexible format handling.
    
    Attempts to parse the timestamp using several common formats.
    
    Args:
        datetime_str: String representation of datetime
        
    Returns:
        Parsed datetime object or current time if parsing fails
    """
    if not datetime_str:
        logger.warning("Empty timestamp string, using current time")
        return datetime.now()
        
    # Try different formats
    formats_to_try = [
        "%Y%m%d %H%M%S.%f",      # Original expected format
        "%Y-%m-%d %H:%M:%S.%f",   # ISO format with microseconds
        "%Y-%m-%d %H:%M:%S",      # ISO format without microseconds
        "%Y-%m-%d %H:%M",         # ISO format without seconds
        "%Y-%m-%d",               # Just date
    ]
    
    for format_str in formats_to_try:
        try:
            return datetime.strptime(datetime_str, format_str)
        except ValueError:
            continue
    
    # If all parsing attempts fail, use current time
    logger.warning(f"Could not parse timestamp: {datetime_str}, using current time")
    return datetime.now()