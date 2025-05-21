# tests/test_alerts.py
"""
Test cases for alert mechanisms.

This module contains tests for the alert trigger and notification
mechanisms to ensure they correctly identify and notify about matches.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

from test_framework import TestCase
from tests.test_registry import register_test_case

# Import the modules to test
from alerting.triggers import AlertTrigger
from alerting.notifiers import ConsoleNotifier

@register_test_case
class AlertTestCase(TestCase):
    """Tests for alert mechanisms"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock database for testing
        self.mock_db = MagicMock()
        
        # Set up identifiers for testing
        self.identifiers = [
            {
                'id': 1,
                'client_id': 1,
                'identifier_type': 'domain',
                'identifier_value': 'example.com'
            },
            {
                'id': 2,
                'client_id': 1,
                'identifier_type': 'name',
                'identifier_value': 'Test Company'
            }
        ]
        
        # Configure the mock database
        self.mock_db.get_all_identifiers.return_value = self.identifiers
        
        # Initialize the alert trigger with mock database
        self.alert_trigger = AlertTrigger(self.mock_db)
    
    def test_check_match_domain(self):
        """Test matching against domain identifiers"""
        # Create a claim with matching domain
        claim = {
            "collector": "Test",
            "threat_actor": "testgroup",
            "name_network_identifier": "Some Company",
            "ip_network_identifier": None,
            "domain_network_identifier": "www.example.com",
            "sector": "Technology",
            "comment": "Test description",
            "raw_data": "{}",
            "timestamp": datetime.now(),
            "claim_url": "http://example.com"
        }
        
        # Check for matches - force refresh of cache
        self.alert_trigger._refresh_cache()
        matches = self.alert_trigger.check_match(claim)
        
        # Verify the domain match was found
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['id'], 1)
        self.assertEqual(matches[0]['identifier_type'], 'domain')
        self.assertEqual(matches[0]['identifier_value'], 'example.com')
    
    def test_console_notifier(self):
        """Test console notifier"""
        notifier = ConsoleNotifier()
        
        # Create a mock identifier object with attributes instead of dictionary keys
        mock_identifier = MagicMock()
        mock_identifier.identifier_type = "domain"
        mock_identifier.identifier_value = "example.com"
        mock_identifier.client = MagicMock()
        mock_identifier.client.client_name = "Test Client"
        
        # Create a test alert
        alert = {
            "id": 100,
            "message": "Test alert message",
            "identifier": mock_identifier
        }
        
        # Mock print to prevent output during test
        with patch('builtins.print') as mock_print:
            # Send the alert
            result = notifier.send_alert(alert)
            
            # Verify the alert was sent
            self.assertTrue(result)