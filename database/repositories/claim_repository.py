# database/repositories/claim_repository.py
"""
Repository for claim operations in the ransomware intelligence system.
"""

import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import exc, or_, and_, func
from database.models import Claim
from datetime import datetime, timedelta

class ClaimRepository:
    """Repository for claim-related database operations"""
    
    def __init__(self, database):
        """Initialize the claim repository with database instance"""
        self.db = database
        self.logger = logging.getLogger("claim_repository")
    
    def add_claim(self, claim_data: Dict[str, Any]) -> Optional[int]:
        """
        Add a single claim to the database.
        
        Args:
            claim_data: Claim data dictionary
            
        Returns:
            ID of the added claim or None if duplicate/error
        """
        def _add_claim(session):
            # Validate claim data
            sanitized_data = self._validate_claim(claim_data)
            
            # Check for duplicates using enhanced detection
            if self._is_duplicate(session, sanitized_data):
                self.logger.debug(f"Duplicate claim found, skipping: {sanitized_data['name_network_identifier']}")
                return None
            
            # Create and add new claim
            new_claim = Claim(
                threat_actor=sanitized_data["threat_actor"],
                source=sanitized_data["collector"],
                ip_network_identifier=sanitized_data.get("ip_network_identifier"),
                domain_network_identifier=sanitized_data.get("domain_network_identifier"),
                name_network_identifier=sanitized_data["name_network_identifier"],
                sector=sanitized_data.get("sector"),
                comment=sanitized_data.get("comment"),
                raw_data=sanitized_data.get("raw_data", ""),
                timestamp=sanitized_data["timestamp"],
                claim_url=sanitized_data.get("claim_url", "")
            )
            
            session.add(new_claim)
            session.flush()  # Flush to get the ID
            self.logger.info(f"Added new claim: {sanitized_data['name_network_identifier']} from {sanitized_data['threat_actor']}")
            return new_claim.id
        
        try:
            return self.db.execute_with_session(_add_claim)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error adding claim: {str(e)}")
            return None
    
    def bulk_add_claims(self, claims_data: List[Dict[str, Any]]) -> List[Optional[int]]:
        """
        Add multiple claims to the database in a single transaction.
        
        Args:
            claims_data: List of claim data dictionaries
            
        Returns:
            List of IDs for added claims (None for duplicates)
        """
        def _bulk_add(session):
            added_ids = []
            
            # Process each claim
            for claim_data in claims_data:
                try:
                    sanitized_data = self._validate_claim(claim_data)
                    
                    # Check for duplicates using enhanced detection
                    if self._is_duplicate(session, sanitized_data):
                        self.logger.debug(f"Duplicate claim in bulk add, skipping: {sanitized_data['name_network_identifier']}")
                        added_ids.append(None)  # Mark as duplicate
                        continue
                    
                    # Create and add new claim
                    new_claim = Claim(
                        threat_actor=sanitized_data["threat_actor"],
                        source=sanitized_data["collector"],
                        ip_network_identifier=sanitized_data.get("ip_network_identifier"),
                        domain_network_identifier=sanitized_data.get("domain_network_identifier"),
                        name_network_identifier=sanitized_data["name_network_identifier"],
                        sector=sanitized_data.get("sector"),
                        comment=sanitized_data.get("comment"),
                        raw_data=sanitized_data.get("raw_data", ""),
                        timestamp=sanitized_data["timestamp"],
                        claim_url=sanitized_data.get("claim_url", "")
                    )
                    
                    session.add(new_claim)
                    session.flush()
                    added_ids.append(new_claim.id)
                    self.logger.info(f"Added new claim (bulk): {sanitized_data['name_network_identifier']} from {sanitized_data['threat_actor']}")
                    
                except ValueError as e:
                    self.logger.warning(f"Skipping invalid claim: {str(e)}")
                    added_ids.append(None)
            
            return added_ids
        
        try:
            return self.db.execute_with_session(_bulk_add)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error in bulk add claims: {str(e)}")
            return []
    
    def _is_duplicate(self, session, claim_data: Dict[str, Any]) -> bool:
        """
        Enhanced duplicate detection using multiple criteria.
        
        A claim is considered a duplicate if:
        1. Exact match on source, threat_actor, name, and timestamp
        2. Same source, threat_actor, name, and timestamp within 1 hour
        3. Same source, threat_actor, domain, and timestamp within 1 day
        """
        # Normalize fields for comparison
        source = claim_data["collector"].lower().strip()
        threat_actor = claim_data["threat_actor"].lower().strip()
        name = claim_data["name_network_identifier"].lower().strip()
        domain = claim_data.get("domain_network_identifier", "").lower().strip()
        timestamp = claim_data["timestamp"]
        
        # 1. Check for exact match
        exact_match = session.query(Claim).filter(
            func.lower(Claim.source) == source,
            func.lower(Claim.threat_actor) == threat_actor,
            func.lower(Claim.name_network_identifier) == name,
            Claim.timestamp == timestamp
        ).first()
        
        if exact_match:
            self.logger.debug(f"Exact duplicate found for {name} from {threat_actor}")
            return True
        
        # 2. Check for same data within time window
        time_window_start = timestamp - timedelta(hours=1)
        time_window_end = timestamp + timedelta(hours=1)
        
        time_match = session.query(Claim).filter(
            func.lower(Claim.source) == source,
            func.lower(Claim.threat_actor) == threat_actor,
            func.lower(Claim.name_network_identifier) == name,
            Claim.timestamp.between(time_window_start, time_window_end)
        ).first()
        
        if time_match:
            self.logger.debug(f"Time-based duplicate found for {name} from {threat_actor}")
            return True
        
        # 3. Check for domain match within larger time window
        if domain:
            domain_time_window_start = timestamp - timedelta(days=1)
            domain_time_window_end = timestamp + timedelta(days=1)
            
            domain_match = session.query(Claim).filter(
                func.lower(Claim.source) == source,
                func.lower(Claim.threat_actor) == threat_actor,
                func.lower(Claim.domain_network_identifier) == domain,
                Claim.timestamp.between(domain_time_window_start, domain_time_window_end)
            ).first()
            
            if domain_match:
                self.logger.debug(f"Domain-based duplicate found for {domain} from {threat_actor}")
                return True
        
        return False
    
    def get_claim_by_id(self, claim_id: int) -> Optional[Dict[str, Any]]:
        """Get a claim by its ID"""
        def _get_claim(session):
            claim = session.query(Claim).filter(Claim.id == claim_id).first()
            if claim:
                return self._to_dict(claim)
            return None
        
        try:
            return self.db.execute_with_session(_get_claim)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting claim: {str(e)}")
            return None
    
    def get_recent_claims(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent claims from the database"""
        def _get_recent(session):
            claims = session.query(Claim).order_by(Claim.timestamp.desc()).limit(limit).all()
            return [self._to_dict(claim) for claim in claims]
        
        try:
            return self.db.execute_with_session(_get_recent)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting recent claims: {str(e)}")
            return []
    
    def _to_dict(self, claim: Claim) -> Dict[str, Any]:
        """Convert a Claim object to a dictionary"""
        return {
            "id": claim.id,
            "collector": claim.source,
            "threat_actor": claim.threat_actor,
            "name_network_identifier": claim.name_network_identifier,
            "ip_network_identifier": claim.ip_network_identifier,
            "domain_network_identifier": claim.domain_network_identifier,
            "sector": claim.sector,
            "comment": claim.comment,
            "raw_data": claim.raw_data,
            "timestamp": claim.timestamp,
            "claim_url": claim.claim_url,
            "key": claim.key
        }
    
    def _validate_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize claim data.
        
        Raises:
            ValueError: If required fields are missing
        """
        # Create copy to avoid modifying original
        sanitized = claim_data.copy()
        
        # Check required fields
        required_fields = ["threat_actor", "collector", "name_network_identifier", "timestamp"]
        for field in required_fields:
            if field not in sanitized or sanitized[field] is None:
                raise ValueError(f"Missing required field: {field}")
        
        # Sanitize string fields
        string_fields = [
            "threat_actor", "collector", "name_network_identifier", 
            "ip_network_identifier", "domain_network_identifier", 
            "sector", "comment", "claim_url", "raw_data"
        ]
        
        for field in string_fields:
            if field in sanitized:
                # Convert None to empty string
                if sanitized[field] is None:
                    sanitized[field] = ""
                # Ensure it's a string
                elif not isinstance(sanitized[field], str):
                    sanitized[field] = str(sanitized[field])
                # Strip whitespace
                sanitized[field] = sanitized[field].strip()
        
        # Ensure raw_data is string
        if "raw_data" in sanitized and not isinstance(sanitized["raw_data"], str):
            sanitized["raw_data"] = str(sanitized["raw_data"])
        
        # Default empty string for optional fields
        if "claim_url" not in sanitized:
            sanitized["claim_url"] = ""
        
        return sanitized
    
    def find_duplicates(self, time_window_days: int = 7) -> List[Tuple[Claim, Claim]]:
        """Find potential duplicate claims in the database"""
        def _find_duplicates(session):
            duplicates = []
            
            # Get recent claims
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_window_days)
            
            claims = session.query(Claim).filter(
                Claim.timestamp.between(start_date, end_date)
            ).order_by(Claim.threat_actor, Claim.timestamp).all()
            
            # Group by threat actor
            claims_by_actor = {}
            for claim in claims:
                actor = claim.threat_actor.lower()
                if actor not in claims_by_actor:
                    claims_by_actor[actor] = []
                claims_by_actor[actor].append(claim)
            
            # Check each group
            for actor, actor_claims in claims_by_actor.items():
                for i in range(len(actor_claims)):
                    for j in range(i+1, len(actor_claims)):
                        claim1 = actor_claims[i]
                        claim2 = actor_claims[j]
                        
                        # Check if timestamps are close
                        time_diff = abs((claim1.timestamp - claim2.timestamp).total_seconds())
                        if time_diff > 86400:  # More than 1 day apart
                            continue
                            
                        # Check for name similarity
                        name1 = claim1.name_network_identifier.lower() if claim1.name_network_identifier else ""
                        name2 = claim2.name_network_identifier.lower() if claim2.name_network_identifier else ""
                        
                        if name1 and name2 and (name1 in name2 or name2 in name1):
                            duplicates.append((claim1, claim2))
                            continue
                            
                        # Check for domain match
                        domain1 = claim1.domain_network_identifier.lower() if claim1.domain_network_identifier else ""
                        domain2 = claim2.domain_network_identifier.lower() if claim2.domain_network_identifier else ""
                        
                        if domain1 and domain2 and (domain1 in domain2 or domain2 in domain1):
                            duplicates.append((claim1, claim2))
            
            return duplicates
            
        try:
            return self.db.execute_with_session(_find_duplicates)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error finding duplicates: {str(e)}")
            return []