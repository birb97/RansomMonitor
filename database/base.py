# database/base.py
"""
Base database connection management for the ransomware intelligence system.
"""

import logging
from sqlalchemy import create_engine, exc, inspect
from sqlalchemy.orm import sessionmaker

class Database:
    """
    Base database class that handles connection management and session creation.
    """
    
    def __init__(self, connection_string="sqlite:///ransomware_intel.db", base_class=None):
        """
        Initialize the database connection.
        
        Args:
            connection_string: SQLAlchemy connection string
            base_class: SQLAlchemy declarative base class (passed in to avoid circular imports)
        """
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.logger = logging.getLogger("database")
        self.Base = base_class  # Store the base class for initialize()
    
    def initialize(self):
        """
        Create tables if they don't exist.
        """
        try:
            if self.Base:
                self.Base.metadata.create_all(self.engine)
                self.logger.info("Database initialized successfully")
                return True
            else:
                self.logger.error("Cannot initialize database: Base class not provided")
                return False
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            return False
    
    def get_session(self):
        """
        Get a new database session. Remember to close it when done!
        
        Returns:
            SQLAlchemy session
        """
        return self.Session()
    
    def execute_with_session(self, operation):
        """
        Execute an operation with session handling.
        
        Args:
            operation: Function that takes a session parameter
            
        Returns:
            Result of the operation
        """
        session = self.Session()
        try:
            result = operation(session)
            session.commit()
            return result
        except exc.SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()
    
    def to_dict(self, model_instance):
        """
        Convert a model instance to a dictionary.
        
        This is useful to avoid detached instance issues by extracting data
        before the session is closed.
        
        Args:
            model_instance: SQLAlchemy model instance
            
        Returns:
            Dictionary of model attributes
        """
        if model_instance is None:
            return None
            
        result = {}
        for key in inspect(model_instance).mapper.column_attrs.keys():
            result[key] = getattr(model_instance, key)
        return result
    
    def to_dict_list(self, model_instances):
        """
        Convert a list of model instances to a list of dictionaries.
        
        Args:
            model_instances: List of SQLAlchemy model instances
            
        Returns:
            List of dictionaries of model attributes
        """
        return [self.to_dict(instance) for instance in model_instances]