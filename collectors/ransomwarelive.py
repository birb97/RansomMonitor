# collectors/ransomwarelive.py
from typing import List, Dict, Any, Optional
from .base import BaseCollector


class RansomwareLiveCollector(BaseCollector):
    """
    Collector implementation for the Ransomware.live API.
    
    This collector retrieves recent ransomware victim data from
    the Ransomware.live API and transforms it into the standardized
    claim format used by the application.
    """
    
    def __init__(self) -> None:
        """Initialize the Ransomware.live collector"""
        super().__init__("Ransomware.live", "https://api.ransomware.live")
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect recent ransomware victims from Ransomware.live API.
        
        Returns:
            List of processed claim dictionaries
        """
        self.logger.info("Collecting data from Ransomware.live")
        data = self.make_request("/v2/recentvictims")
        
        if not data:
            self.logger.warning("No data received from Ransomware.live API")
            return []
            
        self.logger.info(f"Processing {len(data)} claims from Ransomware.live")
        processed_data: List[Dict[str, Any]] = []
        
        for item in data:
            # Parse timestamp using base class method
            timestamp = self.parse_timestamp(item.get("attackdate", ""))
            
            # Normalize domain using base class method
            domain = self.normalize_domain(item.get("domain"))
            
            processed_item: Dict[str, Any] = {
                "collector": self.name,
                "threat_actor": item.get("group"),
                "name_network_identifier": item.get("victim"),
                "ip_network_identifier": None,
                "domain_network_identifier": domain,
                "sector": item.get("activity"),
                "comment": item.get("description"),
                "raw_data": str(item),
                "claim_url": item.get("claim_url"),  # No need for NULL handling here, database will handle it
                "timestamp": timestamp
            }
            processed_data.append(processed_item)
            
        self.logger.info(f"Processed {len(processed_data)} claims from Ransomware.live")
        return processed_data
