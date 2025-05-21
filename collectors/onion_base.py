# collectors/onion_base.py
from typing import List, Dict, Any, Optional
from .droplet_proxy import DropletProxyCollector
from datetime import datetime
import logging

class OnionCollector(DropletProxyCollector):
    """
    Base collector for ransomware groups with .onion sites.
    
    Features:
    - Fallback addresses when primary is unreachable
    - Graceful handling of offline sites
    """
    
    def __init__(self, name: str, onion_urls: List[str], parser_type: str = "generic"):
        """
        Initialize the Onion collector.
        
        Args:
            name: Name of the ransomware group
            onion_urls: List of potential onion URLs to try (primary first)
            parser_type: Parser to use
        """
        # Use the first URL as primary, store the rest as fallbacks
        self.primary_url = onion_urls[0] if onion_urls else None
        self.fallback_urls = onion_urls[1:] if len(onion_urls) > 1 else []
        self.parser_type = parser_type
        
        # Initialize base class
        super().__init__(name, self.primary_url, parser_type)
        
        # Override default retries
        self.max_retries = 2  # Lower for primary site to quickly try fallbacks
        
    def collect(self) -> List[Dict[str, Any]]:
        """
        Collect data from this ransomware group's onion site.
        
        Strategy:
        1. Check if Tor proxy is available
        2. Try primary URL
        3. If unreachable, try fallbacks in sequence
        4. Return whatever data we can get
        
        Returns:
            List of processed claims
        """
        self.logger.info(f"Collecting data from {self.name}")
        
        # First check if the Tor proxy is running
        if not self._is_tor_proxy_available():
            self.logger.warning(f"Tor proxy not available. Skipping collection for {self.name}")
            return []
            
        # Try primary URL first
        data = self._collect_with_fallbacks()
        
        if not data:
            self.logger.warning(f"No data received from any {self.name} onion sites")
            return []
            
        victims = data.get("victims", [])
        self.logger.info(f"Processing {len(victims)} victims from {self.name}")
        
        # Process the victims data
        processed_data = self._process_victims(victims)
        
        self.logger.info(f"Processed {len(processed_data)} claims from {self.name}")
        return processed_data
    
    def _collect_with_fallbacks(self) -> Optional[Dict[str, Any]]:
        """
        Try collecting data from primary URL, falling back to alternatives if needed.
        
        Returns:
            Data dictionary or None if all URLs failed
        """
        # Try primary URL first
        self.logger.info(f"Trying primary URL: {self.base_url}")
        data = self._collect_via_droplet()
        
        # If successful, return the data
        if data and not (isinstance(data, dict) and "error" in data):
            self.logger.info(f"Successfully collected data from primary URL")
            return data
            
        # Log the failure
        if data and isinstance(data, dict) and "error" in data:
            self.logger.error(f"Error collecting from primary URL: {data.get('error')}")
        else:
            self.logger.error(f"Failed to collect data from primary URL")
        
        # Try fallback URLs
        for fallback_url in self.fallback_urls:
            self.logger.info(f"Trying fallback URL: {fallback_url}")
            
            # Temporarily change the base URL
            original_url = self.base_url
            self.base_url = fallback_url
            
            # Try collecting from this fallback
            data = self._collect_via_droplet()
            
            # Restore original URL
            self.base_url = original_url
            
            # If successful, return the data
            if data and not (isinstance(data, dict) and "error" in data):
                self.logger.info(f"Successfully collected data from fallback URL: {fallback_url}")
                return data
                
            # Log the failure
            if data and isinstance(data, dict) and "error" in data:
                self.logger.error(f"Error collecting from fallback URL: {data.get('error')}")
            else:
                self.logger.error(f"Failed to collect data from fallback URL: {fallback_url}")
        
        # All URLs failed
        self.logger.error(f"All {self.name} onion URLs are unreachable")
        return None
    
    def _process_victims(self, victims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process victim data into standardized claims.
        
        Args:
            victims: List of victim dictionaries from the parser
            
        Returns:
            List of processed claims
        """
        processed_data = []
        
        for victim in victims:
            try:
                # Parse timestamp using base class method
                timestamp_str = victim.get("date")
                if not timestamp_str:
                    # Use current date if none provided
                    timestamp = datetime.now()
                else:
                    timestamp = self.parse_timestamp(timestamp_str)
                
                # Process domain if it exists
                domain = None
                if victim.get("domain"):
                    domain = self.normalize_domain(victim.get("domain"))
                
                # Create the processed claim
                processed_item: Dict[str, Any] = {
                    "collector": self.name,
                    "threat_actor": victim.get("group", self.name.lower()),
                    "name_network_identifier": victim.get("name"),
                    "ip_network_identifier": None,
                    "domain_network_identifier": domain,
                    "sector": victim.get("sector"),
                    "comment": f"Published: {victim.get('date', 'Unknown')}" if victim.get('date') else None,
                    "raw_data": str(victim),
                    "claim_url": self.base_url + (victim.get("path", "") or ""),
                    "timestamp": timestamp
                }
                
                # Skip entries that look like debugging info
                if isinstance(processed_item["name_network_identifier"], str) and \
                   processed_item["name_network_identifier"].startswith("Debug:"):
                    self.logger.debug(f"Skipping debug entry: {processed_item['name_network_identifier']}")
                    continue
                
                processed_data.append(processed_item)
                self.logger.debug(f"Processed victim: {processed_item['name_network_identifier']}")
                
            except Exception as e:
                self.logger.error(f"Error processing victim {victim.get('name', 'Unknown')}: {str(e)}")
                continue
                
        return processed_data