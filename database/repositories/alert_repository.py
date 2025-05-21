# database/repositories/alert_repository.py
"""
Repository for alert operations in the ransomware intelligence system.
"""

import logging
from typing import List, Optional
from sqlalchemy import exc
from database.models import Alert
from datetime import datetime

class AlertRepository:
    """Repository for alert-related database operations"""
    
    def __init__(self, database):
        """
        Initialize the alert repository.
        
        Args:
            database: Database instance
        """
        self.db = database
        self.logger = logging.getLogger("alert_repository")
    
    def add_alert(self, identifier_id: int, message: str) -> Optional[int]:
        """
        Add a new alert to the database.
        
        Args:
            identifier_id: ID of the matched identifier
            message: Alert message
            
        Returns:
            ID of the added alert or None if error
        """
        def _add_alert(session):
            alert = Alert(
                identifier_id=identifier_id,
                message=message,
                timestamp=datetime.now()
            )
            
            session.add(alert)
            session.flush()
            return alert.id
        
        try:
            return self.db.execute_with_session(_add_alert)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error adding alert: {str(e)}")
            return None
    
    def get_recent_alerts(self, limit: int = 100) -> List[Alert]:
        """
        Get recent alerts from the database.
        
        Args:
            limit: Maximum number of alerts to retrieve
            
        Returns:
            List of recent alert objects
        """
        def _get_recent(session):
            return session.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()
        
        try:
            return self.db.execute_with_session(_get_recent)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting recent alerts: {str(e)}")
            return []
    
    def get_alerts_by_identifier(self, identifier_id: int) -> List[Alert]:
        """
        Get all alerts for a specific identifier.
        
        Args:
            identifier_id: ID of the identifier
            
        Returns:
            List of alert objects for the identifier
        """
        def _get_alerts(session):
            return session.query(Alert).filter(Alert.identifier_id == identifier_id).order_by(Alert.timestamp.desc()).all()
        
        try:
            return self.db.execute_with_session(_get_alerts)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting alerts by identifier: {str(e)}")
            return []
    
    def get_alert_count(self) -> int:
        """
        Get the total number of alerts.
        
        Returns:
            Total number of alerts
        """
        def _get_count(session):
            return session.query(Alert).count()
        
        try:
            return self.db.execute_with_session(_get_count)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error getting alert count: {str(e)}")
            return 0
    
    def delete_alert(self, alert_id: int) -> bool:
        """
        Delete an alert from the database.
        
        Args:
            alert_id: ID of the alert to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        def _delete_alert(session):
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return False
            
            session.delete(alert)
            return True
        
        try:
            return self.db.execute_with_session(_delete_alert)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error deleting alert: {str(e)}")
            return False
    
    def clear_old_alerts(self, days: int = 30) -> int:
        """
        Delete alerts older than the specified number of days.
        
        Args:
            days: Number of days to keep alerts for
            
        Returns:
            Number of alerts deleted
        """
        def _clear_old(session):
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            deleted = session.query(Alert).filter(Alert.timestamp < cutoff_date).delete()
            return deleted
        
        try:
            return self.db.execute_with_session(_clear_old)
        except exc.SQLAlchemyError as e:
            self.logger.error(f"Error clearing old alerts: {str(e)}")
            return 0