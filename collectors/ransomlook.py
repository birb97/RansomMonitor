# collectors/ransomlook.py
from typing import List, Dict, Any, Optional
from .base import BaseCollector


class RansomlookCollector(BaseCollector):
    """
    Collector implementation for the Ransomlook API.
    
    This collector retrieves recent ransomware post data from
    the Ransomlook API and transforms it into the standardized
    claim format used by the application.
    """
    
    def __init__(self) -> None:
        """Initialize the Ransomlook collector"""
        super().__init__("Ransomlook", "https://www.ransomlook.io/api")
    
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect recent ransomware posts from Ransomlook API.
        
        Returns:
            List of processed claim dictionaries
        """
        self.logger.info("Collecting data from Ransomlook")
        data = self.make_request("/recent")
        
        if not data:
            self.logger.warning("No data received from Ransomlook API")
            return []
            
        self.logger.info(f"Processing {len(data)} claims from Ransomlook")
        processed_data: List[Dict[str, Any]] = []
        
        for item in data:
            # Parse timestamp using base class method
            timestamp = self.parse_timestamp(item.get("discovered", ""))
            
            # Process domain if it exists (even though the current API example doesn't include it)
            domain = None
            if "domain" in item:
                domain = self.normalize_domain(item.get("domain"))
            
            processed_item: Dict[str, Any] = {
                "collector": self.name,
                "threat_actor": item.get("group_name"),
                "name_network_identifier": item.get("post_title"),
                "ip_network_identifier": None,
                "domain_network_identifier": domain,
                "sector": None,
                "comment": item.get("description"),
                "raw_data": str(item),
                "claim_url": item.get("link"),  # No need for NULL handling here, database will handle it
                "timestamp": timestamp
            }
            processed_data.append(processed_item)
            
        self.logger.info(f"Processed {len(processed_data)} claims from Ransomlook")
        return processed_data
