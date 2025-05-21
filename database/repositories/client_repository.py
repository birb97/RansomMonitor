# database/repositories/client_repository.py
"""
Repository for client operations in the ransomware intelligence system.
"""

import logging
from typing import List, Optional
from sqlalchemy import exc
from database.models import Client

class ClientRepository:
    """Repository for client-related database operations"""
    
    def __init__(self, database):
        """
        Initialize the client repository.
        
        Args:
            database: Database instance
        """
        self.db = database
        self.logger = logging.getLogger("client_repository")
    
    def add_client(self, client_name: str) -> Optional[int]:
        """
        Add a new client to the database.
        
        Args:
            client_name: Name of the client
            
        Returns:
            ID of the added client or None if error
        """
        if not client_name or not client_name.strip():
            self.logger.warning("Cannot add client with empty name")
            return None
        
        # Clean the client name
        client_name = client_name.strip()
        
        def _add_client(session):
            # Check if client already exists
            existing = session.query(Client).filter(Client.client_name == client_name).first()
            if existing:
                self.logger.warning(f"Client already exists: {client_name}")
                return None
            
            # Create and add new client
            client = Client(client_name=client_name)
            session.add(client)
            session.flush()
            return client.id
        
        try:
            return self.db.execute_with_session(_add_client)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error adding client: {str(e)}")
            return None
    
    def get_clients(self) -> List[dict]:
        """
        Get all clients from the database.
        
        Returns:
            List of client dictionaries with id and client_name keys
        """
        def _get_clients(session):
            clients = session.query(Client).all()
            # Convert to dictionaries to avoid detached instance issues
            return [{"id": client.id, "client_name": client.client_name} for client in clients]
        
        try:
            return self.db.execute_with_session(_get_clients)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting clients: {str(e)}")
            return []
    
    def get_client_by_id(self, client_id: int) -> Optional[dict]:
        """
        Get a client by its ID.
        
        Args:
            client_id: ID of the client
            
        Returns:
            Client dictionary or None if not found
        """
        def _get_client(session):
            client = session.query(Client).filter(Client.id == client_id).first()
            if client:
                return {"id": client.id, "client_name": client.client_name}
            return None
        
        try:
            return self.db.execute_with_session(_get_client)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting client by ID: {str(e)}")
            return None
    
    def get_client_by_name(self, client_name: str) -> Optional[dict]:
        """
        Get a client by its name.
        
        Args:
            client_name: Name of the client
            
        Returns:
            Client dictionary or None if not found
        """
        def _get_client(session):
            client = session.query(Client).filter(Client.client_name == client_name).first()
            if client:
                return {"id": client.id, "client_name": client.client_name}
            return None
        
        try:
            return self.db.execute_with_session(_get_client)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting client by name: {str(e)}")
            return None
    
    def update_client_name(self, client_id: int, new_name: str) -> bool:
        """
        Update a client's name.
        
        Args:
            client_id: ID of the client
            new_name: New name for the client
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not new_name or not new_name.strip():
            self.logger.warning("Cannot update client with empty name")
            return False
        
        # Clean the client name
        new_name = new_name.strip()
        
        def _update_client(session):
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return False
            
            # Check if name is already used by another client
            existing = session.query(Client).filter(
                Client.client_name == new_name,
                Client.id != client_id
            ).first()
            
            if existing:
                self.logger.warning(f"Client name already in use: {new_name}")
                return False
            
            client.client_name = new_name
            return True
        
        try:
            return self.db.execute_with_session(_update_client)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error updating client name: {str(e)}")
            return False
    
    def delete_client(self, client_id: int) -> bool:
        """
        Delete a client from the database.
        
        Args:
            client_id: ID of the client to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        def _delete_client(session):
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return False
            
            # Check if client has identifiers
            if client.identifiers:
                self.logger.warning(f"Cannot delete client with identifiers: {client.client_name}")
                return False
            
            session.delete(client)
            return True
        
        try:
            return self.db.execute_with_session(_delete_client)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error deleting client: {str(e)}")
            return False