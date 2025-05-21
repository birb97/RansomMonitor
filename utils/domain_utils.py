# utils/domain_utils.py
"""
Utility functions for working with domain names.

This module provides functions for normalizing and matching domains.
"""

from typing import Optional, Set, Dict, List, Tuple, Any

def is_domain_match(test_domain, watchlist_domain):
    """
    Determine if two domains match according to our matching rules.
    
    Rules:
    1. Exact match after normalization
    2. Match with/without www prefix
    3. Subdomain relationship (one is subdomain of the other)
    
    Args:
        test_domain (str): Domain to test
        watchlist_domain (str): Domain from watchlist
        
    Returns:
        bool: True if domains match, False otherwise
    """
    # Normalize both domains
    test_norm = normalize_domain(test_domain)
    watchlist_norm = normalize_domain(watchlist_domain)
    
    if not test_norm or not watchlist_norm:
        return False
    
    # 1. Exact match
    if test_norm == watchlist_norm:
        return True
    
    # 2. WWW prefix match
    if test_norm.startswith("www.") and test_norm[4:] == watchlist_norm:
        return True
    if watchlist_norm.startswith("www.") and test_norm == watchlist_norm[4:]:
        return True
    
    # 3. Subdomain relationship
    return (test_norm.endswith("." + watchlist_norm) or 
            watchlist_norm.endswith("." + test_norm))


def normalize_domain(domain: Optional[str]) -> str:
    """
    Normalize domain for consistent comparison.
    
    Args:
        domain: Domain string to normalize
        
    Returns:
        Normalized domain or empty string if input was None/empty
    """
    if not domain:
        return ""
        
    # Remove protocol
    if domain.startswith("http://"):
        domain = domain[7:]
    elif domain.startswith("https://"):
        domain = domain[8:]
        
    # Remove trailing slashes
    domain = domain.rstrip("/")
    
    # Remove trailing/leading whitespace
    domain = domain.strip()
    
    return domain.lower()


def is_subdomain_of(potential_subdomain: str, potential_parent: str) -> bool:
    """
    Check if one domain is a subdomain of another.
    
    Args:
        potential_subdomain: Domain that might be a subdomain
        potential_parent: Domain that might be a parent
        
    Returns:
        True if potential_subdomain is a subdomain of potential_parent
    """
    if not potential_subdomain or not potential_parent:
        return False
        
    # Normalize both domains
    sub = normalize_domain(potential_subdomain)
    parent = normalize_domain(potential_parent)
    
    # Quick check - parent must be shorter and must be suffix of subdomain
    if len(parent) >= len(sub) or not sub.endswith(parent):
        return False
    
    # Check if parent is actually the domain part (not just any suffix)
    # The character before the parent domain should be a dot
    prefix_end = len(sub) - len(parent) - 1
    return prefix_end >= 0 and sub[prefix_end] == '.'


class DomainMatchCache:
    """
    Cache for efficient domain matching operations.
    
    This cache preprocesses domains for faster lookups during claim processing.
    """
    
    def __init__(self):
        """Initialize an empty domain match cache"""
        # Map from normalized domains to original domains with metadata
        self.exact_matches: Dict[str, List[Tuple[str, Any]]] = {}
        # Map from parent domains to potential subdomains with metadata
        self.parent_domains: Dict[str, List[Tuple[str, Any]]] = {}
        # Map from domain without www to the same domain with www
        self.www_variants: Dict[str, List[Tuple[str, Any]]] = {}
    
    def add_domain(self, original_domain: str, metadata: Any = None) -> None:
        """
        Add a domain to the cache with associated metadata.
        
        Args:
            original_domain: Domain to add
            metadata: Any associated data to store with this domain
        """
        normalized = normalize_domain(original_domain)
        if not normalized:
            return
            
        # Store exact match
        if normalized not in self.exact_matches:
            self.exact_matches[normalized] = []
        self.exact_matches[normalized].append((original_domain, metadata))
        
        # Store www variant
        if normalized.startswith("www.") and len(normalized) > 4:
            no_www = normalized[4:]
            if no_www not in self.www_variants:
                self.www_variants[no_www] = []
            self.www_variants[no_www].append((original_domain, metadata))
        else:
            www_version = f"www.{normalized}"
            if normalized not in self.www_variants:
                self.www_variants[normalized] = []
            self.www_variants[normalized].append((original_domain, metadata))
        
        # Store parent domain references for subdomain matching
        parts = normalized.split('.')
        if len(parts) > 2:
            parent = '.'.join(parts[1:])
            if parent not in self.parent_domains:
                self.parent_domains[parent] = []
            self.parent_domains[parent].append((original_domain, metadata))
    
    def find_matches(self, test_domain: str) -> List[Tuple[str, Any]]:
        """
        Find all potential domain matches in the cache.
        
        Args:
            test_domain: Domain to match against the cache
            
        Returns:
            List of (domain, metadata) tuples for matching domains
        """
        if not test_domain:
            return []
            
        normalized = normalize_domain(test_domain)
        if not normalized:
            return []
            
        matches = []
        
        # Check exact matches
        if normalized in self.exact_matches:
            matches.extend(self.exact_matches[normalized])
        
        # Check www variants
        if normalized.startswith("www.") and len(normalized) > 4:
            no_www = normalized[4:]
            if no_www in self.exact_matches:
                matches.extend(self.exact_matches[no_www])
        else:
            if normalized in self.www_variants:
                matches.extend(self.www_variants[normalized])
        
        # Check subdomain relationships (test_domain could be a subdomain)
        parts = normalized.split('.')
        for i in range(1, len(parts)):
            parent = '.'.join(parts[i:])
            if parent in self.exact_matches:
                matches.extend(self.exact_matches[parent])
        
        # Check parent relationships (test_domain could be a parent domain)
        if normalized in self.parent_domains:
            matches.extend(self.parent_domains[normalized])
            
        return matches