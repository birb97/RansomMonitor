# tests/test_domain_utils.py
"""
Test cases for domain utility functions.

This module contains tests for the domain-related utility functions
to ensure they work correctly for matching and normalizing domains.
"""

from typing import List, Dict, Any
from test_framework import TestCase
from tests.test_registry import register_test_case
from utils.domain_utils import normalize_domain, is_domain_match, generate_domain_variants, DomainMatchCache

@register_test_case
class DomainUtilsTestCase(TestCase):
    """Tests for domain utility functions"""
    
    def test_normalize_domain(self):
        """Test domain normalization function"""
        # Test with protocol prefixes
        self.assertEqual(normalize_domain("http://example.com"), "example.com")
        self.assertEqual(normalize_domain("https://example.com"), "example.com")
        
        # Test with trailing slashes
        self.assertEqual(normalize_domain("example.com/"), "example.com")
        self.assertEqual(normalize_domain("example.com/path/"), "example.com/path")
        
        # Test with whitespace
        self.assertEqual(normalize_domain(" example.com "), "example.com")
        
        # Test with uppercase
        self.assertEqual(normalize_domain("EXAMPLE.COM"), "example.com")
        
        # Test with None or empty
        self.assertEqual(normalize_domain(None), "")
        self.assertEqual(normalize_domain(""), "")
    
    def test_is_domain_match(self):
        """Test domain matching function"""
        # Test exact match
        self.assertTrue(is_domain_match("example.com", "example.com"))
        
        # Test case insensitivity
        self.assertTrue(is_domain_match("EXAMPLE.com", "example.COM"))
        
        # Test www prefix
        self.assertTrue(is_domain_match("www.example.com", "example.com"))
        self.assertTrue(is_domain_match("example.com", "www.example.com"))
        
        # Test subdomain relationship
        self.assertTrue(is_domain_match("sub.example.com", "example.com"))
        
        # Test non-matches
        self.assertFalse(is_domain_match("example.org", "example.com"))
        self.assertFalse(is_domain_match("another.com", "example.com"))