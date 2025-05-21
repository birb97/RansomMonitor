# collectors/ransomwatch.py
from typing import List, Dict, Any, Optional
from .base import BaseCollector


class RansomwatchCollector(BaseCollector):
    """
    Collector implementation for the Ransomwatch API.
    
    This collector retrieves ransomware post data from
    the Ransomwatch GitHub repository and transforms it into the standardized
    claim format used by the application.
    """
    
    def __init__(self) -> None:
        """Initialize the Ransomwatch collector"""
        super().__init__("Ransomwatch", "https://raw.githubusercontent.com/joshhighet/ransomwatch/main")
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect the 100 most recent ransomware posts from Ransomwatch API.
        
        Returns:
            List of processed claim dictionaries (limited to 100 newest)
        """
        self.logger.info("Collecting data from Ransomwatch")
        data = self.make_request("/posts.json")
        
        if not data:
            self.logger.warning("No data received from Ransomwatch API")
            return []
            
        self.logger.info(f"Retrieved {len(data)} total claims from Ransomwatch")
        
        # Convert timestamps and sort by newest first
        for item in data:
            item['parsed_timestamp'] = self.parse_timestamp(item.get("discovered", ""))
            
        # Sort by timestamp (newest first)
        sorted_data = sorted(data, key=lambda x: x['parsed_timestamp'], reverse=True)
        
        # Limit to newest 100 claims
        limited_data = sorted_data[:100]
        self.logger.info(f"Processing {len(limited_data)} newest claims from Ransomwatch")
        
        processed_data: List[Dict[str, Any]] = []
        
        for item in limited_data:
            processed_item: Dict[str, Any] = {
                "collector": self.name,
                "threat_actor": item.get("group_name"),
                "name_network_identifier": item.get("post_title"),
                "ip_network_identifier": None,
                "domain_network_identifier": None,
                "sector": None,
                "comment": None,
                "raw_data": str(item),
                "claim_url": None,  # No URL available in the data
                "timestamp": item['parsed_timestamp']  # Use already parsed timestamp
            }
            processed_data.append(processed_item)
            
        self.logger.info(f"Processed {len(processed_data)} newest claims from Ransomwatch")
        return processed_data