# cli_modules/dashboard.py
"""
Dashboard functionality for the ransomware intelligence system.

This module provides functions to gather and display system status
information for the main CLI dashboard.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

class Dashboard:
    """
    Dashboard component for displaying system status.
    
    This class gathers and formats information about the current
    state of the ransomware intelligence system for display in the CLI.
    """
    
    def __init__(self, database, collection_manager, config):
        """
        Initialize the dashboard.
        
        Args:
            database: Database instance
            collection_manager: Collection manager instance
            config: Configuration instance
        """
        self.database = database
        self.collection_manager = collection_manager
        self.config = config
        self.logger = logging.getLogger("dashboard")
    
    def get_process_status(self) -> Dict[str, Any]:
        """
        Get status of system processes.
        
        Returns:
            Dict with process status information
        """
        status = {
            "foreground_running": self.collection_manager.running,
            "background_running": self.collection_manager.is_background_running(),
        }
        
        # Get process ID for background collection if running
        if status["background_running"]:
            from utils.process_utils import read_pid_file
            status["background_pid"] = read_pid_file()
        
        return status
    
    def get_recent_alerts(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get recent alerts from the database.
        
        Args:
            limit: Maximum number of alerts to retrieve
            
        Returns:
            List of recent alert dictionaries
        """
        try:
            # Use a more direct approach to get alert data using raw SQL
            # This avoids SQLAlchemy session issues with detached objects
            session = None
            result = []
            
            try:
                # Get session using the appropriate method
                if hasattr(self.database, 'db') and hasattr(self.database.db, 'get_session'):
                    session = self.database.db.get_session()
                elif hasattr(self.database, 'Session'):
                    session = self.database.Session()
                
                if session:
                    # Use direct SQL to avoid ORM object detachment issues
                    from sqlalchemy import text
                    query = text(f"SELECT id, message, timestamp FROM alerts ORDER BY timestamp DESC LIMIT {limit}")
                    rows = session.execute(query).fetchall()
                    
                    for row in rows:
                        result.append({
                            'id': row[0],
                            'message': row[1],
                            'timestamp': row[2]
                        })
            finally:
                if session:
                    session.close()
                    
            return result
        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {str(e)}")
            return []
    
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dict with database statistics
        """
        try:
            return self.database.get_statistics()
        except Exception as e:
            self.logger.error(f"Error getting database statistics: {str(e)}")
            return {
                "client_count": 0,
                "identifier_count": 0,
                "claim_count": 0,
                "alert_count": 0
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about data collection.
        
        Returns:
            Dict with collection statistics
        """
        stats = {}
        
        try:
            # Get session using the appropriate method
            session = None
            if hasattr(self.database, 'db') and hasattr(self.database.db, 'get_session'):
                session = self.database.db.get_session()
            elif hasattr(self.database, 'Session'):
                session = self.database.Session()
            
            if session:
                try:
                    # Get most recent claim timestamp
                    from sqlalchemy import func
                    from database.models import Claim
                    
                    latest_timestamp = session.query(func.max(Claim.timestamp)).scalar()
                    if latest_timestamp:
                        stats["latest_collection"] = latest_timestamp
                        stats["collection_age"] = (datetime.now() - latest_timestamp).total_seconds() / 60
                    
                    # Get claim count by source
                    from sqlalchemy import text
                    source_query = text("SELECT source, COUNT(*) FROM claims GROUP BY source")
                    sources = session.execute(source_query).fetchall()
                    
                    stats["sources"] = {src: count for src, count in sources}
                    
                finally:
                    session.close()
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
        
        return stats
    
    def get_tor_status(self) -> Dict[str, Any]:
        """
        Check Tor connection status if applicable.
        
        Returns:
            Dict with Tor status information
        """
        # Default values
        result = {
            "enabled": False,
            "connected": False,
            "container_running": False
        }
        
        try:
            # First check if Tor collector functionality is present
            import importlib
            droplet_spec = importlib.util.find_spec("collectors.droplet_proxy")
            result["enabled"] = droplet_spec is not None
            
            # Since Tor is running in Docker, we should check if containers are running
            try:
                import subprocess
                # Check if docker is available and containers are running
                docker_ps = subprocess.run(
                    ["docker", "ps"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Check if tor-proxy container is running
                result["container_running"] = "tor-proxy" in docker_ps.stdout
                
                # If the container is running, we'll assume it's connected
                # For a more accurate check, we would need to query the health endpoint
                if result["container_running"]:
                    result["connected"] = True
                
                # Alternative: Try to connect to the collection agent and check its health
                if result["container_running"]:
                    import requests
                    try:
                        response = requests.get("http://localhost:5000/health", timeout=2)
                        if response.status_code == 200:
                            data = response.json()
                            result["connected"] = data.get("tor_working", False)
                    except:
                        # If we can't connect to the agent, leave the status as is
                        pass
                
            except (subprocess.SubprocessError, FileNotFoundError):
                # Docker commands not available, fall back to simple socket check
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                try:
                    # Try connecting to the agent port instead
                    s.connect(("localhost", 5000))
                    result["container_running"] = True
                    result["connected"] = True
                except (socket.timeout, ConnectionRefusedError):
                    pass
                finally:
                    s.close()
                    
        except Exception as e:
            self.logger.error(f"Error checking Tor status: {str(e)}")
        
        return result
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get all dashboard data.
        
        Returns:
            Dict with all dashboard information
        """
        return {
            "timestamp": datetime.now(),
            "processes": self.get_process_status(),
            "alerts": self.get_recent_alerts(),
            "database": self.get_database_stats(),
            "tor": self.get_tor_status(),
            "collection": self.get_collection_stats()
        }
    
    def format_dashboard(self, data: Dict[str, Any], width: int = 80) -> str:
        """
        Format dashboard data for display.
        
        Args:
            data: Dashboard data to format
            width: Width of the dashboard in characters
            
        Returns:
            Formatted dashboard as a string
        """
        lines = []
        
        # Format header
        lines.append("=" * width)
        lines.append(self._center_text("SYSTEM DASHBOARD", width))
        lines.append("=" * width)
        
        # Process status section
        processes = data["processes"]
        if processes["foreground_running"]:
            status_text = "RUNNING IN FOREGROUND"
        elif processes["background_running"]:
            status_text = f"RUNNING IN BACKGROUND (PID: {processes.get('background_pid', 'Unknown')})"
        else:
            status_text = "STOPPED"
            
        lines.append(f"Collection: {status_text}")
        lines.append(f"Poll Interval: {self.config.get_interval()} seconds")
        
        # Component status section
        lines.append("-" * width)
        
        # Database status 
        db_stats = data["database"]
        db_line = f"Database: {db_stats.get('claim_count', 0)} claims, {db_stats.get('alert_count', 0)} alerts"
        
        # Tor status if applicable
        tor = data["tor"]
        tor_text = ""
        if tor.get("enabled"):
            container_status = "RUNNING" if tor.get("container_running") else "STOPPED"
            connection_status = "CONNECTED" if tor.get("connected") else "DISCONNECTED"
            tor_text = f"Tor: {container_status}/{connection_status}"
            db_line = f"{db_line} | {tor_text}"
        
        lines.append(db_line)
            
        # Collection info
        collection = data.get("collection", {})
        if "latest_collection" in collection:
            latest = collection["latest_collection"]
            age_mins = collection.get("collection_age", 0)
            
            if age_mins < 60:
                age_str = f"{int(age_mins)} min ago"
            else:
                age_str = f"{int(age_mins/60)} hours ago"
                
            sources = collection.get("sources", {})
            source_counts = []
            for src, count in sources.items():
                source_counts.append(f"{src}: {count}")
                
            lines.append(f"Last Update: {latest.strftime('%Y-%m-%d %H:%M')} ({age_str}) | Sources: {', '.join(source_counts)}")
        
        # Recent alerts section
        lines.append("-" * width)
        lines.append("Recent Alerts:")
        
        alerts = data["alerts"]
        if alerts:
            for i, alert in enumerate(alerts[:3]):  # Limit to 3 alerts
                # Alert might be a dictionary or an object
                message = alert.get('message', str(alert)) if isinstance(alert, dict) else getattr(alert, 'message', str(alert))
                
                # Truncate and format message
                if len(message) > width - 4:
                    message = message[:width - 7] + "..."
                
                lines.append(f"  {i+1}. {message}")
        else:
            lines.append("  No recent alerts.")
        
        lines.append("=" * width)
        
        return "\n".join(lines)
    
    def _center_text(self, text: str, width: int, fill_char: str = " ") -> str:
        """
        Center text in a field of specified width.
        
        Args:
            text: Text to center
            width: Width of the field
            fill_char: Character to use for padding
            
        Returns:
            Centered text string
        """
        text_len = len(text)
        if text_len >= width:
            return text
        
        left_padding = (width - text_len) // 2
        right_padding = width - text_len - left_padding
        
        return f"{fill_char * left_padding}{text}{fill_char * right_padding}"