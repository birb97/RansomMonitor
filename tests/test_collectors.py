# tests/test_collectors.py
"""
Test cases for data collectors.

This module contains tests for the collector classes to ensure
they correctly fetch and process data from intelligence sources.
"""

import json
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock
from datetime import datetime

from test_framework import TestCase
from tests.test_registry import register_test_case
# Make sure the imports are correct for your project structure
from collectors.base import BaseCollector
from collectors.ransomlook import RansomlookCollector
from collectors.ransomwarelive import RansomwareLiveCollector

@register_test_case
class CollectorTestCase(TestCase):
    """Tests for collector classes"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock data for tests
        self.ransomlook_data = [
            {
                "post_title": "Test Company",
                "discovered": "20250222 185730.920941",
                "description": "Test description",
                "link": "/companies/123456",
                "magnet": None,
                "screen": "screenshots/group/TestCompany.png",
                "group_name": "testgroup"
            }
        ]
        
        self.ransomwarelive_data = [
            {
                "activity": "Technology",
                "attackdate": "20250222 165844.000000",
                "claim_url": "https://example.onion/companies/123456",
                "country": "US",
                "description": "Test description",
                "discovered": "20250222 172021.809152",
                "domain": "www.testcompany.com",
                "duplicates": [],
                "group": "testgroup",
                "infostealer": "",
                "press": None,
                "screenshot": "https://images.example.com/victims/123.png",
                "url": "https://example.com/id/123",
                "victim": "Test Company"
            }
        ]
    
    @patch('collectors.base.BaseCollector.make_request')
    def test_ransomlook_collector(self, mock_make_request):
        """Test RansomlookCollector data processing"""
        # Configure the mock
        mock_make_request.return_value = self.ransomlook_data
        
        # Create collector and collect data
        collector = RansomlookCollector()
        claims = collector.collect()
        
        # Verify make_request was called correctly
        mock_make_request.assert_called_once_with("/recent")
        
        # Verify processed data
        self.assertEqual(len(claims), 1)
        claim = claims[0]
        
        self.assertEqual(claim["collector"], "Ransomlook")
        self.assertEqual(claim["threat_actor"], "testgroup")
        self.assertEqual(claim["name_network_identifier"], "Test Company")
        self.assertIsNone(claim["ip_network_identifier"])
        self.assertEqual(claim["comment"], "Test description")
        self.assertEqual(claim["claim_url"], "/companies/123456")
    
    @patch('collectors.base.BaseCollector.make_request')
    def test_ransomwarelive_collector(self, mock_make_request):
        """Test RansomwareLiveCollector data processing"""
        # Configure the mock
        mock_make_request.return_value = self.ransomwarelive_data
        
        # Create collector and collect data
        collector = RansomwareLiveCollector()
        claims = collector.collect()
        
        # Verify make_request was called correctly
        mock_make_request.assert_called_once_with("/v2/recentvictims")
        
        # Verify processed data
        self.assertEqual(len(claims), 1)
        claim = claims[0]
        
        self.assertEqual(claim["collector"], "Ransomware.live")
        self.assertEqual(claim["threat_actor"], "testgroup")
        self.assertEqual(claim["name_network_identifier"], "Test Company")
        self.assertIsNone(claim["ip_network_identifier"])
        self.assertEqual(claim["domain_network_identifier"], "www.testcompany.com")
        self.assertEqual(claim["sector"], "Technology")
        self.assertEqual(claim["comment"], "Test description")
        self.assertEqual(claim["claim_url"], "https://example.onion/companies/123456")
    
    @patch('collectors.base.BaseCollector.make_request')
    def test_empty_response_handling(self, mock_make_request):
        """Test handling of empty responses"""
        # Configure the mock to return None (network error)
        mock_make_request.return_value = None
        
        # Test with RansomlookCollector
        collector = RansomlookCollector()
        claims = collector.collect()
        self.assertEqual(len(claims), 0)
        
        # Test with RansomwareLiveCollector
        collector = RansomwareLiveCollector()
        claims = collector.collect()
        self.assertEqual(len(claims), 0)
    
    def test_base_collector_abstract(self):
        """Test that BaseCollector is abstract"""
        # Attempting to instantiate BaseCollector should raise TypeError
        with self.assertRaises(TypeError):
            BaseCollector("Test", "http://example.com")
            
    def test_normalize_domain(self):
        """Test domain normalization in BaseCollector"""
        # Create a subclass to test BaseCollector methods
        class TestCollector(BaseCollector):
            def collect(self):
                return []
        
        collector = TestCollector("Test", "http://example.com")
        
        # Test domain normalization
        self.assertEqual(collector.normalize_domain("http://example.com"), "example.com")
        self.assertEqual(collector.normalize_domain("https://www.test.org/"), "www.test.org")
        self.assertEqual(collector.normalize_domain(None), "")
    
    def test_parse_timestamp(self):
        """Test timestamp parsing in BaseCollector"""
        # Create a subclass to test BaseCollector methods
        class TestCollector(BaseCollector):
            def collect(self):
                return []
        
        collector = TestCollector("Test", "http://example.com")
        
        # Test timestamp parsing
        self.assertEqual(
            collector.parse_timestamp("20250222 185730.920941").date(),
            datetime(2025, 2, 22).date()
        )