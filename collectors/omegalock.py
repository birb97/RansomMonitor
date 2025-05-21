# collectors/omegalock.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from .onion_base import OnionCollector

class OmegalockCollector(OnionCollector):
    """
    Collector implementation for the Omega Lock ransomware group.
    
    This collector retrieves victim data from the Omega Lock onion site
    and transforms it into the standardized claim format used by the application.
    """
    
    def __init__(self) -> None:
        """Initialize the Omega Lock collector"""
        # List of known addresses - primary first, fallbacks after
        onion_urls = [
            "http://omegalock5zxwbhswbisc42o2q2i54vdulyvtqqbudqousisjgc7j7yd.onion/",
            # Add alternative URLs when discovered
        ]
        
        super().__init__("Omegalock", onion_urls, "omegalock")
    
    def _process_victims(self, victims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process victim data into standardized claims.
        
        This method overrides the base class implementation to handle
        the specific data format from the Omegalock parser.
        
        Args:
            victims: List of victim dictionaries from the parser
            
        Returns:
            List of processed claims that match our database schema
        """
        processed_data = []
        
        for victim in victims:
            try:
                # Skip debug entries 
                if self._is_debug_entry(victim.get("name")):
                    continue
                
                # Parse timestamp using consistent format from the site
                timestamp_str = victim.get("date")
                if timestamp_str:
                    try:
                        # Site format appears to be YYYY-MM-DD
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d")
                    except ValueError:
                        # Fallback to base class parsing
                        timestamp = self.parse_timestamp(timestamp_str)
                else:
                    # Use current date if none provided
                    timestamp = datetime.now()
                
                # Process domain if it exists (not in current data)
                domain = None
                if victim.get("domain"):
                    domain = self.normalize_domain(victim.get("domain"))
                
                # Build claim URL, combining base URL with specific link if available
                claim_url = self.base_url
                if victim.get("link") and victim.get("link").startswith("/"):
                    # Handle relative URLs
                    base = self.base_url.rstrip("/")
                    claim_url = f"{base}{victim.get('link')}"
                elif victim.get("link"):
                    claim_url = victim.get("link")
                
                # Create a comprehensive comment with all available metadata
                comment_parts = []
                if victim.get("leak_percentage"):
                    comment_parts.append(f"Leak: {victim.get('leak_percentage')}")
                if victim.get("data_size"):
                    comment_parts.append(f"Size: {victim.get('data_size')}")  # Changed from "Data:" to "Size:" to match test
                if timestamp_str:
                    comment_parts.append(f"Published: {timestamp_str}")
                
                comment = " | ".join(comment_parts) if comment_parts else None
                
                # Create the processed claim with only the fields needed for our schema
                processed_item: Dict[str, Any] = {
                    "collector": self.name,
                    "threat_actor": "omegalock",
                    "name_network_identifier": victim.get("name"),
                    "ip_network_identifier": None,
                    "domain_network_identifier": domain,
                    "sector": victim.get("sector"),  # Use tags as sector
                    "comment": comment,
                    "raw_data": str(victim),  # Keep all original data in raw_data
                    "claim_url": claim_url,
                    "timestamp": timestamp
                }
                
                processed_data.append(processed_item)
                self.logger.debug(f"Processed victim: {processed_item['name_network_identifier']}")
                
            except Exception as e:
                self.logger.error(f"Error processing victim {victim.get('name', 'Unknown')}: {str(e)}")
                continue
                
        return processed_data
    
    def _is_debug_entry(self, name: Optional[str]) -> bool:
        """
        Check if an entry appears to be debugging information.
        
        Args:
            name: The name field to check
            
        Returns:
            True if this appears to be a debug entry
        """
        if not name:
            return True
            
        debug_indicators = ["debug:", "test:", "placeholder", "unknown"]
        name_lower = name.lower()
        
        for indicator in debug_indicators:
            if indicator in name_lower:
                return True
                
        return False