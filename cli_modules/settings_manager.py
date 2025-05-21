# cli_modules/settings_manager.py
"""
Settings management for the ransomware intelligence system.
"""

import logging
from .ui import clear_screen, print_header

class SettingsManager:
    """Manages application settings"""
    
    def __init__(self, config, collection_manager):
        self.config = config
        self.collection_manager = collection_manager
        self.logger = logging.getLogger("settings_manager")
    
    def manage_settings(self):
        """Interactive CLI for managing settings"""
        clear_screen()
        print_header("SETTINGS")
        
        current_interval = self.config.get_interval()
        print(f"Current poll interval: {current_interval} seconds")
        
        new_interval = input("\nEnter new interval in seconds (or press Enter to keep current): ")
        if new_interval:
            try:
                interval = int(new_interval)
                if interval > 0:
                    self.config.set_interval(interval)
                    print(f"\nInterval updated to {interval} seconds.")
                    
                    # If collection is running, restart it with the new interval
                    if self.collection_manager.is_running():
                        self.collection_manager.stop_collection()
                        self.collection_manager.start_collection()
                else:
                    print("\nInterval must be greater than 0.")
            except ValueError:
                print("\nInvalid input. Please enter a number.")
        
        # Add more settings as needed - logging level, database path, etc.
        print("\nLogging Settings:")
        current_log_level = self.config.get_log_level()
        print(f"Current log level: {current_log_level}")
        
        log_level_choice = input("\nChange log level? (DEBUG/INFO/WARNING/ERROR/CRITICAL or Enter to skip): ")
        if log_level_choice:
            log_level_choice = log_level_choice.upper()
            try:
                if log_level_choice in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    self.config.set_log_level(log_level_choice)
                    print(f"\nLog level updated to {log_level_choice}.")
                else:
                    print("\nInvalid log level. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
            except Exception as e:
                print(f"\nError setting log level: {str(e)}")
        
        input("\nPress Enter to continue...")