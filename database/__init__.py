# database/__init__.py
"""
Database components for the ransomware intelligence system.
"""

import logging

from database.models import Base

# Now import the Database class
from .models import Base
from .base import Database

# Import repository classes
from .repositories.claim_repository import ClaimRepository
from .repositories.client_repository import ClientRepository
from .repositories.identifier_repository import IdentifierRepository
from .repositories.alert_repository import AlertRepository

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

# Convenience function to create a DatabaseContext with all repositories
def create_database_context(connection_string="sqlite:///ransomware_intel.db"):
    """
    Create a database context with all repositories.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        Dictionary with database and repository instances
    """
    db = Database(connection_string, Base)
    
    return {
        "database": db,
        "claim_repo": ClaimRepository(db),
        "client_repo": ClientRepository(db),
        "identifier_repo": IdentifierRepository(db),
        "alert_repo": AlertRepository(db)
    }

# Define DatabaseService for compatibility with old code
class DatabaseService:
    """
    Combined database service providing a unified interface similar
    to the original Database class.
    """
    
    def __init__(self, connection_string="sqlite:///ransomware_intel.db"):
        """
        Initialize the database service.
        
        Args:
            connection_string: SQLAlchemy connection string
        """
        self.connection_string = connection_string
        self.db = Database(connection_string, Base)
        
        # Initialize repositories
        self.client_repo = ClientRepository(self.db)
        self.identifier_repo = IdentifierRepository(self.db)
        self.claim_repo = ClaimRepository(self.db)
        self.alert_repo = AlertRepository(self.db)
        
        self.logger = logging.getLogger("database_service")
    
    def initialize(self):
        """
        Initialize the database structure.
        
        Returns:
            True if successful, False otherwise
        """
        return self.db.initialize()
    
    # === Client methods ===
    
    def add_client(self, client_name):
        """Add a new client to the database."""
        return self.client_repo.add_client(client_name)
    
    def get_clients(self):
        """Get all clients from the database."""
        return self.client_repo.get_clients()
    
    def get_client_by_id(self, client_id):
        """Get a client by ID."""
        return self.client_repo.get_client_by_id(client_id)
    
    # === Identifier methods ===
    
    def add_identifier(self, client_id, identifier_type, identifier_value):
        """Add a new identifier to the database."""
        return self.identifier_repo.add_identifier(client_id, identifier_type, identifier_value)
    
    def get_all_identifiers(self):
        """Get all identifiers from the database."""
        return self.identifier_repo.get_all_identifiers()
    
    def get_client_identifiers(self, client_id):
        """Get all identifiers for a client."""
        return self.identifier_repo.get_client_identifiers(client_id)
    
    def get_identifier_by_id(self, identifier_id):
        """Get an identifier by ID."""
        return self.identifier_repo.get_identifier_by_id(identifier_id)
    
    def delete_identifier(self, identifier_id):
        """Delete an identifier from the database."""
        return self.identifier_repo.delete_identifier(identifier_id)
    
    # === Claim methods ===
    
    def add_claim(self, claim_data):
        """Add a claim to the database."""
        return self.claim_repo.add_claim(claim_data)
    
    def bulk_add_claims(self, claims_data):
        """Add multiple claims to the database in a batch."""
        return self.claim_repo.bulk_add_claims(claims_data)
    
    def get_claim_by_id(self, claim_id):
        """Get a claim by ID."""
        return self.claim_repo.get_claim_by_id(claim_id)
    
    def get_recent_claims(self, limit=100):
        """Get the most recent claims."""
        return self.claim_repo.get_recent_claims(limit)
    
    # === Alert methods ===
    
    def add_alert(self, identifier_id, message):
        """Add a new alert to the database."""
        return self.alert_repo.add_alert(identifier_id, message)
    
    def get_recent_alerts(self, limit=100):
        """Get the most recent alerts."""
        return self.alert_repo.get_recent_alerts(limit)
    
    # === Statistics methods ===
    
    def get_statistics(self):
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts of entities
        """
        # Use a session directly for complex query
        session = self.db.get_session()
        try:
            from database.models import Client, Identifier, Claim, Alert
            
            stats = {
                "client_count": session.query(Client).count(),
                "identifier_count": session.query(Identifier).count(),
                "claim_count": session.query(Claim).count(),
                "alert_count": session.query(Alert).count(),
                "domain_identifier_count": session.query(Identifier).filter(
                    Identifier.identifier_type == "domain").count(),
                "name_identifier_count": session.query(Identifier).filter(
                    Identifier.identifier_type == "name").count(),
                "ip_identifier_count": session.query(Identifier).filter(
                    Identifier.identifier_type == "ip").count()
            }
            return stats
        except Exception as e:
            self.logger.error(f"Error getting database statistics: {str(e)}")
            return {
                "client_count": 0,
                "identifier_count": 0,
                "claim_count": 0,
                "alert_count": 0,
                "domain_identifier_count": 0,
                "name_identifier_count": 0,
                "ip_identifier_count": 0
            }
        finally:
            session.close()
            
    # This is a special method used by some parts of the system to access Session directly
    def Session(self):
        """
        Get a session factory (for backward compatibility).
        """
        return self.db.Session