# database/repositories/identifier_repository.py
"""
Repository for identifier operations in the ransomware intelligence system.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import exc
from database.models import Identifier

class IdentifierRepository:
    """Repository for identifier-related database operations"""
    
    def __init__(self, database):
        """
        Initialize the identifier repository.
        
        Args:
            database: Database instance
        """
        self.db = database
        self.logger = logging.getLogger("identifier_repository")
    
    def add_identifier(self, client_id: int, identifier_type: str, identifier_value: str) -> Optional[int]:
        """
        Add a new identifier to the database.
        
        Args:
            client_id: ID of the client
            identifier_type: Type of identifier ('name', 'ip', or 'domain')
            identifier_value: Value of the identifier
            
        Returns:
            ID of the added identifier or None if error
        """
        # Validate identifier type
        if identifier_type not in ["name", "ip", "domain"]:
            self.logger.warning(f"Invalid identifier type: {identifier_type}")
            return None
        
        def _add_identifier(session):
            # Check if identifier already exists for this client
            existing = session.query(Identifier).filter(
                Identifier.client_id == client_id,
                Identifier.identifier_type == identifier_type,
                Identifier.identifier_value == identifier_value
            ).first()
            
            if existing:
                self.logger.warning(f"Identifier already exists: {identifier_type}:{identifier_value}")
                return None
            
            # Create and add new identifier
            identifier = Identifier(
                client_id=client_id,
                identifier_type=identifier_type,
                identifier_value=identifier_value
            )
            
            session.add(identifier)
            session.flush()
            return identifier.id
        
        try:
            return self.db.execute_with_session(_add_identifier)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error adding identifier: {str(e)}")
            return None
    
    def get_all_identifiers(self) -> List[Dict[str, Any]]:
        """
        Get all identifiers from the database.
        
        Returns:
            List of all identifier dictionaries
        """
        def _get_all(session):
            identifiers = session.query(Identifier).all()
            # Extract data to avoid detached instance issues
            return [
                {
                    'id': identifier.id,
                    'client_id': identifier.client_id,
                    'identifier_type': identifier.identifier_type,
                    'identifier_value': identifier.identifier_value,
                }
                for identifier in identifiers
            ]
        
        try:
            return self.db.execute_with_session(_get_all)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting all identifiers: {str(e)}")
            return []
    
    def get_client_identifiers(self, client_id: int) -> List[Dict[str, Any]]:
        """
        Get all identifiers for a specific client.
        
        Args:
            client_id: ID of the client
            
        Returns:
            List of identifier dictionaries for the client
        """
        def _get_client_identifiers(session):
            identifiers = session.query(Identifier).filter(Identifier.client_id == client_id).all()
            # Extract data to avoid detached instance issues
            return [
                {
                    'id': identifier.id,
                    'client_id': identifier.client_id,
                    'identifier_type': identifier.identifier_type,
                    'identifier_value': identifier.identifier_value,
                }
                for identifier in identifiers
            ]
        
        try:
            return self.db.execute_with_session(_get_client_identifiers)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting client identifiers: {str(e)}")
            return []
    
    def get_identifier_by_id(self, identifier_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an identifier by its ID.
        
        Args:
            identifier_id: ID of the identifier
            
        Returns:
            Identifier dictionary or None if not found
        """
        def _get_identifier(session):
            identifier = session.query(Identifier).filter(Identifier.id == identifier_id).first()
            if identifier:
                return {
                    'id': identifier.id,
                    'client_id': identifier.client_id,
                    'identifier_type': identifier.identifier_type,
                    'identifier_value': identifier.identifier_value,
                }
            return None
        
        try:
            return self.db.execute_with_session(_get_identifier)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting identifier: {str(e)}")
            return None
    
    def delete_identifier(self, identifier_id: int) -> bool:
        """
        Delete an identifier from the database.
        
        Args:
            identifier_id: ID of the identifier to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        def _delete_identifier(session):
            identifier = session.query(Identifier).filter(Identifier.id == identifier_id).first()
            if not identifier:
                return False
            
            session.delete(identifier)
            return True
        
        try:
            return self.db.execute_with_session(_delete_identifier)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error deleting identifier: {str(e)}")
            return False
    
    def get_identifiers_by_type(self, identifier_type: str) -> List[Dict[str, Any]]:
        """
        Get all identifiers of a specific type.
        
        Args:
            identifier_type: Type of identifier ('name', 'ip', or 'domain')
            
        Returns:
            List of identifier dictionaries of the specified type
        """
        def _get_by_type(session):
            identifiers = session.query(Identifier).filter(Identifier.identifier_type == identifier_type).all()
            # Extract data to avoid detached instance issues
            return [
                {
                    'id': identifier.id,
                    'client_id': identifier.client_id,
                    'identifier_type': identifier.identifier_type,
                    'identifier_value': identifier.identifier_value,
                }
                for identifier in identifiers
            ]
        
        try:
            return self.db.execute_with_session(_get_by_type)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting identifiers by type: {str(e)}")
            return []