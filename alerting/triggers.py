# alerting/triggers.py
import logging
from typing import List, Dict, Any, Optional
from utils.domain_utils import normalize_domain, DomainMatchCache
from utils.types import ClaimDict, AlertDict
from utils.domain_utils import is_domain_match


class AlertTrigger:
    """
    Alert trigger mechanism for matching claims against the watchlist.
    """
    
    def __init__(self, database) -> None:
        """
        Initialize the alert trigger.
        
        Args:
            database: Database instance for watchlist and alert storage
        """
        self.database = database
        self.logger = logging.getLogger("alert_trigger")
        self.domain_cache = DomainMatchCache()
        
        # Initially empty - will be populated on first use
        self.identifier_cache = []
        self._cached_domain_identifiers = []
    
    def _refresh_cache(self) -> None:
        """Refresh all cached data from the database"""
        # Get fresh data in a new session
        self.identifier_cache = list(self.database.get_all_identifiers())
        
        # Extract domain identifiers for domain cache
        self._cached_domain_identifiers = []
        self.domain_cache = DomainMatchCache()
        
        for identifier in self.identifier_cache:
            # Now using dictionary access
            if 'identifier_type' in identifier and 'identifier_value' in identifier:
                if identifier['identifier_type'].lower() == "domain":
                    self._cached_domain_identifiers.append({
                        'id': identifier['id'],
                        'type': identifier['identifier_type'],
                        'value': identifier['identifier_value'],
                        'original': identifier
                    })
                    self.domain_cache.add_domain(identifier['identifier_value'], identifier)
    
    def update_domain_cache(self) -> None:
        """
        Update the domain cache when the watchlist changes.
        This should be called after adding/removing identifiers.
        """
        self._refresh_cache()
    
    def check_match(self, claim: ClaimDict) -> List[Dict[str, Any]]:
        """
        Check if a claim matches any identifier on the watchlist.
        """
        # Refresh cache if empty
        if not self.identifier_cache:
            self._refresh_cache()
            
        matches = []
        
        # Normalize claim identifiers
        name_ident = claim.get("name_network_identifier", "").lower() if claim.get("name_network_identifier") else ""
        ip_ident = claim.get("ip_network_identifier", "").lower() if claim.get("ip_network_identifier") else ""
        domain_ident = claim.get("domain_network_identifier", "").lower() if claim.get("domain_network_identifier") else ""
        
        # Check domain matches manually without using the cache
        if domain_ident:
            self.logger.debug(f"Checking domain: {domain_ident}")
            normalized_domain = normalize_domain(domain_ident)
            
            for domain_info in self._cached_domain_identifiers:
                domain_value = domain_info['value']
                if is_domain_match(normalized_domain, domain_value):
                    matches.append(domain_info['original'])
                    self.logger.info(f"DOMAIN match found: {domain_value} ~ {domain_ident}")
        
        # Check other identifier types
        for identifier in self.identifier_cache:
            # Using dictionary access
            id_type = identifier['identifier_type'].lower()
            id_value = identifier['identifier_value'].lower() if identifier['identifier_value'] else ""
            
            # Skip domains as they're already handled
            if id_type == "domain":
                continue
                
            # Check for name matches
            elif id_type == "name" and name_ident:
                if id_value in name_ident.lower():
                    matches.append(identifier)
                    self.logger.info(f"NAME match found: {id_value} in {name_ident}")
            
            # Check for IP matches
            elif id_type == "ip" and ip_ident:
                if id_value in ip_ident.lower():
                    matches.append(identifier)
                    self.logger.info(f"IP match found: {id_value} in {ip_ident}")
                    
        return matches
    
    def process_claim(self, claim: ClaimDict) -> List[AlertDict]:
        """
        Process a claim and trigger alerts if matches are found.
        """
        if not claim:
            self.logger.debug("Empty claim received, skipping")
            return []
            
        # Ensure all required fields exist
        for field in ["collector", "threat_actor", "name_network_identifier"]:
            if field not in claim or claim[field] is None:
                self.logger.warning(f"Claim missing required field: {field}")
                claim[field] = "" if field not in claim else claim[field] or ""
        
        # Find matches
        matches = self.check_match(claim)
        self.logger.debug(f"Found {len(matches)} matches for claim")
        
        alerts = []
        for identifier in matches:
            # Get identifier info using dictionary access
            id_type = identifier['identifier_type'] if 'identifier_type' in identifier else "unknown"
            id_value = identifier['identifier_value'] if 'identifier_value' in identifier else "unknown"
            
            self.logger.info(f"Creating alert for match: {id_type}:{id_value}")
            
            message = f"ALERT: {claim['collector']} reported {claim['name_network_identifier']} " \
                    f"from threat actor {claim['threat_actor']} matches watchlist identifier " \
                    f"{id_type}:{id_value}"
            
            try:
                alert_id = self.database.add_alert(identifier['id'], message)
                if alert_id:
                    self.logger.warning(message)
                    alerts.append({
                        "id": alert_id,
                        "message": message,
                        "identifier": identifier
                    })
                else:
                    self.logger.error(f"Failed to add alert to database")
            except Exception as e:
                self.logger.error(f"Error creating alert: {str(e)}")
                    
        return alerts