# cli_modules/__init__.py
"""
CLI component modules for the ransomware intelligence system.

This package contains the modular components of the CLI interface:
- collection_manager: Collection process management
- watchlist_manager: Watchlist management functionality
- settings_manager: Configuration management
- alert_manager: Alert testing and management
- test_manager: Test management functionality
- dashboard: System status dashboard
- ui: UI rendering functions
"""

from .ui import clear_screen, print_header, menu
from .collection_manager import CollectionManager
from .watchlist_manager import WatchlistManager
from .settings_manager import SettingsManager
from .alert_manager import AlertManager
from .test_manager import TestManager
from .dashboard import Dashboard

__all__ = [
    'clear_screen', 'print_header', 'menu',
    'CollectionManager', 'WatchlistManager', 'SettingsManager', 
    'AlertManager', 'TestManager', 'Dashboard'
]