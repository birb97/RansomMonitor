# cli_modules/alert_manager.py
"""
Alert management and diagnostic tools for the ransomware intelligence system.

This module provides utility functions for:
- Exploring domain matching behavior
- Inspecting database content
- Processing existing claims against the watchlist
"""

import logging
from datetime import datetime
from sqlalchemy import text
from .ui import clear_screen, print_header
from utils.domain_utils import is_domain_match, normalize_domain

class AlertManager:
    """
    Manages alert-related diagnostic and operational tools.
    
    These tools help users understand, troubleshoot, and operate
    the ransomware intelligence system.
    """
    
    def __init__(self, database, alert_trigger):
        self.database = database
        self.alert_trigger = alert_trigger
        self.logger = logging.getLogger("alert_manager")
    
    def domain_matching_explorer(self):
        """
        Interactive exploration of the domain matching system.
        
        This tool helps users understand how domain matching works by:
        - Showing the normalized form of domains
        - Displaying which matching rules apply
        - Checking against the actual watchlist
        """
        clear_screen()
        print_header("DOMAIN MATCHING EXPLORER")
        
        # Create a test claim with the domain we want to test
        test_domain = input("Enter a domain to test (default: www.tjmachine.com): ") or "www.tjmachine.com"
        test_claim = {
            "collector": "Test",
            "threat_actor": "test",
            "name_network_identifier": "Test Company",
            "ip_network_identifier": None,
            "domain_network_identifier": test_domain,
            "sector": None,
            "comment": None,
            "raw_data": "{}",
            "timestamp": datetime.now(),
            "claim_url": "http://example.com"
        }
        
        # Get all identifiers from the watchlist
        identifiers = self.database.get_all_identifiers()
        print(f"Found {len(identifiers)} identifiers in the watchlist")
        
        # Print domain identifiers
        domain_identifiers = [i for i in identifiers if i['identifier_type'].lower() == "domain"]
        print(f"Found {len(domain_identifiers)} domain identifiers:")
        for i, identifier in enumerate(domain_identifiers):
            print(f"{i+1}. {identifier['identifier_value']}")
        
        # Normalize the test domain
        normalized_test_domain = normalize_domain(test_domain)
        print(f"\nNormalized test domain: '{normalized_test_domain}'")
        
        # Manually check for matches
        print("\nChecking for matches with the test domain:")
        for identifier in domain_identifiers:
            watchlist_value = identifier['identifier_value']
            
            print(f"\nComparing '{watchlist_value}' with '{test_domain}':")
            
            # Use our centralized function
            match_result = is_domain_match(test_domain, watchlist_value)
            print(f"  Match result: {match_result}")
            
            # For more detailed information
            normalized_watchlist_domain = normalize_domain(watchlist_value)
            
            # Check exact match
            exact_match = normalized_watchlist_domain == normalized_test_domain
            print(f"  Exact match: {exact_match}")
            
            # Check www prefix
            www_match = (normalized_watchlist_domain.startswith("www.") and normalized_test_domain == normalized_watchlist_domain[4:]) or \
                    (normalized_test_domain.startswith("www.") and normalized_watchlist_domain == normalized_test_domain[4:])
            print(f"  WWW prefix match: {www_match}")
            
            # Check subdomain relationship
            subdomain_match = normalized_test_domain.endswith("." + normalized_watchlist_domain) or \
                          normalized_watchlist_domain.endswith("." + normalized_test_domain)
            print(f"  Subdomain match: {subdomain_match}")
        
        # Test using the AlertTrigger
        print("\nChecking for matches using the AlertTrigger:")
        matches = self.alert_trigger.check_match(test_claim)
        print(f"Found {len(matches)} matches")
        for match in matches:
            print(f"  Matched: {match['identifier_type']}:{match['identifier_value']}")
        
        input("\nPress Enter to continue...")
    
    def scan_existing_claims(self):
        """
        Scan existing claims against the current watchlist.
        
        This tool allows you to:
        - Process all claims in the database
        - Check for matches against the current watchlist
        - Create alerts for any matches found
        """
        clear_screen()
        print_header("SCAN EXISTING CLAIMS")
        
        # Get a session using the appropriate method
        session = self.database.db.get_session() if hasattr(self.database, 'db') else self.database.Session()
        try:
            query = text("SELECT id, name_network_identifier, domain_network_identifier, ip_network_identifier, threat_actor, source, timestamp FROM claims")
            claims = session.execute(query).fetchall()
            
            print(f"Found {len(claims)} total claims in database")
            
            process_all = input("Process all claims? This could create many alerts. (y/n): ")
            if process_all.lower() != 'y':
                print("Operation cancelled.")
                input("\nPress Enter to continue...")
                return
            
            # Process each claim through the alert trigger
            matched_count = 0
            alert_count = 0
            
            print("\nProcessing claims... (this may take a while)")
            for claim_row in claims:
                # Convert row to dictionary format expected by check_match
                claim = {
                    "id": claim_row[0],
                    "name_network_identifier": claim_row[1],
                    "domain_network_identifier": claim_row[2],
                    "ip_network_identifier": claim_row[3],
                    "threat_actor": claim_row[4],
                    "collector": claim_row[5],  # source column
                    "timestamp": claim_row[6],
                    "raw_data": "",  # Not needed for matching
                    "claim_url": ""  # Not needed for matching
                }
                
                # Check for matches
                matches = self.alert_trigger.check_match(claim)
                if matches:
                    matched_count += 1
                    print(f"\nFound {len(matches)} matches for claim ID {claim['id']}:")
                    print(f"  Name: {claim['name_network_identifier']}")
                    print(f"  Domain: {claim['domain_network_identifier']}")
                    
                    for match in matches:
                        print(f"  Match: {match['identifier_type']}:{match['identifier_value']}")
                        
                        # Create an alert for this match
                        message = f"ALERT: {claim['collector']} reported {claim['name_network_identifier']} " \
                                f"from threat actor {claim['threat_actor']} matches watchlist identifier " \
                                f"{match['identifier_type']}:{match['identifier_value']}"
                        
                        alert_id = self.database.add_alert(match['id'], message)
                        if alert_id:
                            alert_count += 1
                            print(f"  Alert created with ID: {alert_id}")
            
            print(f"\nFound matches for {matched_count} out of {len(claims)} claims")
            print(f"Created {alert_count} new alerts")
            
        finally:
            session.close()
        
        input("\nPress Enter to continue...")

    def database_inspector(self):
        """
        Interactive database inspection tool.
        
        This tool allows you to:
        - Search for claims by domain
        - View recent alerts
        - Check database statistics
        """
        clear_screen()
        print_header("DATABASE INSPECTOR")

        # Access session via the appropriate method depending on database implementation
        session = self.database.db.get_session() if hasattr(self.database, 'db') else self.database.Session()
        try:
            # Get domain to check
            domain_to_check = input("Enter domain to search for (leave empty for all): ")
            domain_clause = ""
            if domain_to_check:
                domain_clause = f" WHERE domain_network_identifier LIKE '%{domain_to_check}%'"
            
            # Check for claims with domain
            query = text(f"SELECT id, name_network_identifier, domain_network_identifier FROM claims{domain_clause}")
            result = session.execute(query)

            print(f"Claims{' with ' + domain_to_check if domain_to_check else ''}:")
            count = 0
            for row in result:
                count += 1
                print(f"ID: {row[0]}, Name: {row[1]}, Domain: {row[2]}")
                if count >= 20:  # Limit display to 20 entries
                    print("(More results available, showing first 20)")
                    break

            if count == 0:
                print("No matching claims found in database.")

            # Check alerts table
            query = text("SELECT COUNT(*) FROM alerts")
            alert_count = session.execute(query).scalar()
            print(f"\nTotal alerts in database: {alert_count}")

            if alert_count > 0:
                query = text("SELECT id, message FROM alerts ORDER BY id DESC LIMIT 5")
                result = session.execute(query)
                print("\nMost recent alerts:")
                for row in result:
                    print(f"Alert ID: {row[0]}, Message: {row[1]}")

            # Show database statistics
            stats = self.database.get_statistics()
            print("\nDatabase Statistics:")
            print(f"  Clients: {stats['client_count']}")
            print(f"  Identifiers: {stats['identifier_count']} (Domains: {stats['domain_identifier_count']}, " +
                  f"Names: {stats['name_identifier_count']}, IPs: {stats['ip_identifier_count']})")
            print(f"  Claims: {stats['claim_count']}")
            print(f"  Alerts: {stats['alert_count']}")

        finally:
            session.close()

        input("\nPress Enter to continue...")