# cli_modules/watchlist_manager.py
"""
Watchlist management functionality for the ransomware intelligence system.
"""

import os
import logging
import ipaddress
import re
from typing import List, Optional, Dict, Any
from sqlalchemy import text

from .ui import clear_screen, print_header
from utils.domain_utils import is_domain_match

class WatchlistManager:
    """Manages the watchlist of clients and their identifiers"""
    
    def __init__(self, database, alert_trigger):
        self.database = database
        self.alert_trigger = alert_trigger
        self.logger = logging.getLogger("watchlist_manager")
    
    def manage_watchlist(self):
        """Interactive CLI for managing the watchlist"""
        while True:
            clear_screen()
            print_header("WATCHLIST MANAGEMENT")
            print("1. View clients")
            print("2. Add new client")
            print("3. Manage client identifiers")
            print("4. Back to main menu")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == "1":
                self._view_clients()
            elif choice == "2":
                self._add_client()
            elif choice == "3":
                self._manage_identifiers()
            elif choice == "4":
                break
            else:
                input("Invalid choice. Press Enter to continue...")
    
    def _view_clients(self):
        """View all clients in the watchlist"""
        clear_screen()
        print_header("CLIENTS")
        
        clients = self.database.get_clients()
        if not clients:
            print("No clients found.")
        else:
            for client in clients:
                # Now using dictionary access instead of attribute access
                print(f"ID: {client['id']}, Name: {client['client_name']}")
        
        input("\nPress Enter to continue...")
    
    def _add_client(self):
        """Add a new client to the watchlist"""
        clear_screen()
        print_header("ADD CLIENT")
        
        client_name = input("Enter client name: ")
        if client_name:
            client_id = self.database.add_client(client_name)
            if client_id:
                print(f"\nClient '{client_name}' added successfully with ID {client_id}.")
            else:
                print("\nFailed to add client. It might already exist.")
        else:
            print("\nClient name cannot be empty.")
        
        input("\nPress Enter to continue...")
    
    def _manage_identifiers(self):
        """Manage identifiers for a client"""
        while True:
            clear_screen()
            print_header("MANAGE CLIENT IDENTIFIERS")
            
            clients = self.database.get_clients()
            if not clients:
                print("No clients found. Add a client first.")
                input("\nPress Enter to continue...")
                return
            
            print("Select a client:")
            for client in clients:
                print(f"{client['id']}. {client['client_name']}")
            
            client_choice = input("\nEnter client ID (or 'b' to go back): ")
            if client_choice.lower() == 'b':
                break
                
            try:
                client_id = int(client_choice)
                # Find client by ID
                client = next((c for c in clients if c['id'] == client_id), None)
                
                if client:
                    self._manage_client_identifiers(client)
                else:
                    print("\nInvalid client ID.")
                    input("Press Enter to continue...")
            except ValueError:
                print("\nInvalid input. Please enter a number.")
                input("Press Enter to continue...")
    
    def _manage_client_identifiers(self, client):
        """Manage identifiers for a specific client"""
        while True:
            clear_screen()
            print_header(f"IDENTIFIERS FOR {client['client_name']}")
            
            identifiers = self.database.get_client_identifiers(client['id'])
            if identifiers:
                print("Current identifiers:")
                for identifier in identifiers:
                    print(f"ID: {identifier['id']}, Type: {identifier['identifier_type']}, Value: {identifier['identifier_value']}")
            else:
                print("No identifiers found for this client.")
            
            print("\n1. Add identifier")
            print("2. Delete identifier")
            print("3. Back to client selection")
            
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == "1":
                self._add_identifier(client)
                # Update domain cache after adding new identifier
                if hasattr(self.alert_trigger, 'update_domain_cache'):
                    self.alert_trigger.update_domain_cache()
            elif choice == "2":
                self._delete_identifier(identifiers)
                # Update domain cache after deleting identifier
                if hasattr(self.alert_trigger, 'update_domain_cache'):
                    self.alert_trigger.update_domain_cache()
            elif choice == "3":
                break
            else:
                input("Invalid choice. Press Enter to continue...")
    
    def _add_identifier(self, client):
        """Add a new identifier for a client"""
        clear_screen()
        print_header(f"ADD IDENTIFIER FOR {client['client_name']}")
        
        print("Identifier types:")
        print("1. Name (Organization/Company name)")
        print("2. IP Address")
        print("3. Domain")
        
        type_choice = input("\nEnter identifier type (1-3): ")
        
        identifier_type = None
        if type_choice == "1":
            identifier_type = "name"
        elif type_choice == "2":
            identifier_type = "ip"
        elif type_choice == "3":
            identifier_type = "domain"
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            return
        
        identifier_value = input(f"Enter {identifier_type} value: ")
        if not identifier_value:
            print("\nIdentifier value cannot be empty.")
            input("Press Enter to continue...")
            return
        
        # Validate input based on type
        if identifier_type == "ip":
            try:
                ipaddress.ip_address(identifier_value)
            except ValueError:
                print("\nInvalid IP address format.")
                input("Press Enter to continue...")
                return
        elif identifier_type == "domain":
            import re
            if not re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$', identifier_value):
                print("\nInvalid domain format. Example of valid format: example.com or subdomain.example.com")
                input("Press Enter to continue...")
                return
        
        identifier_id = self.database.add_identifier(client['id'], identifier_type, identifier_value)
        if identifier_id:
            print(f"\nIdentifier added successfully with ID {identifier_id}.")
            # Update domain cache after adding a new identifier
            if identifier_type == "domain" and hasattr(self.alert_trigger, 'update_domain_cache'):
                self.alert_trigger.update_domain_cache()
            self._check_existing_claims_for_identifier(identifier_id)
        else:
            print("\nFailed to add identifier.")
        
        input("\nPress Enter to continue...")
    
    def _check_existing_claims_for_identifier(self, identifier_id):
        """Check existing claims against a new identifier"""
        print("\nChecking existing claims against the new identifier...")
        session = self.database.db.get_session() if hasattr(self.database, 'db') else self.database.Session()
        try:
            query = text("SELECT id, name_network_identifier, domain_network_identifier, ip_network_identifier, threat_actor, source, timestamp FROM claims")
            claims = session.execute(query).fetchall()
            
            match_count = 0
            for claim_row in claims:
                # Convert row to dictionary format expected by check_match
                claim = {
                    "id": claim_row[0],
                    "name_network_identifier": claim_row[1],
                    "domain_network_identifier": claim_row[2],
                    "ip_network_identifier": claim_row[3],
                    "threat_actor": claim_row[4],
                    "collector": claim_row[5],
                    "timestamp": claim_row[6],
                    "raw_data": "",
                    "claim_url": ""
                }
                
                # Get the new identifier
                identifier = self.database.get_identifier_by_id(identifier_id)
                if not identifier:
                    continue
                    
                # Check if this claim matches the new identifier
                matches = False
                if identifier['identifier_type'] == "domain" and claim["domain_network_identifier"]:
                    matches = is_domain_match(claim["domain_network_identifier"], identifier['identifier_value'])
                elif identifier['identifier_type'] == "name" and claim["name_network_identifier"]:
                    matches = identifier['identifier_value'].lower() in claim["name_network_identifier"].lower()
                elif identifier['identifier_type'] == "ip" and claim["ip_network_identifier"]:
                    matches = identifier['identifier_value'].lower() in claim["ip_network_identifier"].lower()
                
                if matches:
                    match_count += 1
                    message = f"ALERT: {claim['collector']} reported {claim['name_network_identifier']} " \
                            f"from threat actor {claim['threat_actor']} matches watchlist identifier " \
                            f"{identifier['identifier_type']}:{identifier['identifier_value']}"
                    
                    alert_id = self.database.add_alert(identifier['id'], message)
                    print(f"Created alert for claim ID {claim['id']}: {claim['name_network_identifier']}")
            
            print(f"Found {match_count} matching claims for the new identifier.")
        finally:
            session.close()
    
    def _delete_identifier(self, identifiers):
        """Delete an identifier"""
        if not identifiers:
            input("No identifiers to delete. Press Enter to continue...")
            return
            
        identifier_id = input("\nEnter ID of identifier to delete: ")
        try:
            id_to_delete = int(identifier_id)
            
            # Find the identifier type before deleting
            identifier_type = None
            for identifier in identifiers:
                if identifier['id'] == id_to_delete:
                    identifier_type = identifier['identifier_type']
                    break
                    
            if self.database.delete_identifier(id_to_delete):
                print(f"\nIdentifier {id_to_delete} deleted successfully.")
                # Update domain cache after deleting an identifier
                if identifier_type == "domain" and hasattr(self.alert_trigger, 'update_domain_cache'):
                    self.alert_trigger.update_domain_cache()
            else:
                print(f"\nFailed to delete identifier {id_to_delete}. It might not exist.")
        except ValueError:
            print("\nInvalid input. Please enter a number.")
        
        input("\nPress Enter to continue...")