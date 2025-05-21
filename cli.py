# cli.py
"""
Command-line interface for the ransomware intelligence system.

This module provides the main CLI entry point and orchestrates the
component modules to provide a unified interface.
"""

import logging
import io
import sys
from config import Config
from database import DatabaseService
from collectors import RansomlookCollector, RansomwareLiveCollector, OmegalockCollector, RansomwatchCollector
from alerting import AlertTrigger, ConsoleNotifier
from utils.process_utils import read_pid_file, is_process_running, is_background_process_running

# Import component modules
from cli_modules.collection_manager import CollectionManager
from cli_modules.watchlist_manager import WatchlistManager
from cli_modules.settings_manager import SettingsManager
from cli_modules.alert_manager import AlertManager
from cli_modules.test_manager import TestManager
from cli_modules.dashboard import Dashboard
from cli_modules.ui import clear_screen, print_header

# Fix console encoding if needed (Windows especially)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class CLI:
    """
    Main CLI interface for the ransomware intelligence system.
    
    This class orchestrates the different components and provides
    a unified interface for the user.
    """
    
    def __init__(self):
        """Initialize the CLI and its components"""
        # Load configuration
        self.config = Config()
        # Updated to use DatabaseService
        self.database = DatabaseService(self.config.get_database_path())
        self.database.initialize()
        
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, self.config.get_log_level()),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(self.config.get_log_file(), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("cli")
        
        # Initialize collectors
        self.collectors = [
            RansomlookCollector(),
            RansomwareLiveCollector(),
            OmegalockCollector(),
            RansomwatchCollector()
        ]
        
        # Initialize alert system
        self.alert_trigger = AlertTrigger(self.database)
        self.notifier = ConsoleNotifier()
        
        # Initialize component managers
        self.collection_manager = CollectionManager(
            self.config, 
            self.database, 
            self.collectors, 
            self.alert_trigger, 
            self.notifier
        )
        
        self.watchlist_manager = WatchlistManager(self.database, self.alert_trigger)
        self.settings_manager = SettingsManager(self.config, self.collection_manager)
        self.alert_manager = AlertManager(self.database, self.alert_trigger)
        self.test_manager = TestManager()
        
        # Initialize dashboard
        self.dashboard = Dashboard(self.database, self.collection_manager, self.config)
    
    def main_menu(self):
        """Main CLI menu"""
        while True:
            clear_screen()
            print_header("RANSOMWARE INTELLIGENCE SYSTEM")
            
            # Get and display dashboard
            dashboard_data = self.dashboard.get_dashboard_data()
            dashboard_text = self.dashboard.format_dashboard(dashboard_data)
            print(dashboard_text)
            
            # Check if background or foreground collection is running
            foreground_running = self.collection_manager.running
            background_running = self.collection_manager.is_background_running()
            
            if background_running:
                pid = read_pid_file()
                print(f"\n1. Stop background collection")
                print("2. Restart background collection")
            elif foreground_running:
                print(f"\n1. Stop foreground collection")
                print("2. Switch to background collection and exit")
            else:
                print(f"\n1. Start foreground collection")
                print("2. Start background collection and exit")
            print("3. Manage watchlist")
            print("4. Settings")
            print("5. Domain Matching Explorer")
            print("6. Database Inspector")
            print("7. Scan Existing Claims")
            print("8. Run Tests")
            print("9. Exit")
            
            choice = input("\nEnter your choice (1-9): ")
            
            if choice == "1":
                if background_running:
                    if self.collection_manager.stop_background_collection():
                        input("Background collection stopped. Press Enter to continue...")
                    else:
                        input("Failed to stop background collection. Press Enter to continue...")
                elif foreground_running:
                    self.collection_manager.stop_collection()
                    input("Foreground collection stopped. Press Enter to continue...")
                else:
                    self.collection_manager.start_collection()
                    input("Foreground collection started. Press Enter to continue...")
            elif choice == "2":
                if background_running:
                    # Restart background collection
                    self.collection_manager.stop_background_collection()
                    success = self.collection_manager.start_background_collection()
                    if success:
                        print("\nBackground collection restarted successfully.")
                        input("\nPress Enter to continue...")
                    else:
                        input("\nFailed to restart background collection. Press Enter to continue...")
                elif foreground_running:
                    # Switch from foreground to background
                    self.collection_manager.stop_collection()
                    success = self.collection_manager.start_background_collection()
                    if success:
                        print("\nSwitched to background collection successfully.")
                        print("The collection process will continue running after you exit the CLI.")
                        print("You can stop it by running the CLI again and selecting 'Stop background collection'.")
                        input("\nPress Enter to exit...")
                        return  # Exit the CLI
                    else:
                        input("\nFailed to switch to background collection. Press Enter to continue...")
                else:
                    # Start background collection (original behavior)
                    success = self.collection_manager.start_background_collection()
                    if success:
                        print("\nBackground collection started successfully.")
                        print("The collection process will continue running after you exit the CLI.")
                        print("You can stop it by running the CLI again and selecting 'Stop background collection'.")
                        input("\nPress Enter to exit...")
                        return  # Exit the CLI
                    else:
                        input("\nFailed to start background collection. Press Enter to continue...")
            elif choice == "3":
                self.watchlist_manager.manage_watchlist()
            elif choice == "4":
                self.settings_manager.manage_settings()
            elif choice == "5":
                self.alert_manager.domain_matching_explorer()
            elif choice == "6":
                self.alert_manager.database_inspector()
            elif choice == "7":
                self.alert_manager.scan_existing_claims()
            elif choice == "8":
                self.test_manager.manage_tests()
            elif choice == "9":
                if foreground_running:
                    self.collection_manager.stop_collection()
                    
                # Note about background process
                if background_running:
                    print("\nNote: The background collection process will continue running.")
                    print("You can stop it by running the CLI again and selecting 'Stop background collection'.")
                
                print("\nExiting program. Goodbye!")
                break
            else:
                input("Invalid choice. Press Enter to continue...")

def main():
    """Main entry point for the CLI"""
    # Check if running from command line arguments
    if len(sys.argv) > 1:
        # Simple command line control for background collection
        if sys.argv[1] == "start-background":
            cm = CollectionManager(
                Config(),
                DatabaseService(Config().get_database_path()),
                [RansomlookCollector(), RansomwareLiveCollector()],
                AlertTrigger(DatabaseService(Config().get_database_path())),
                ConsoleNotifier()
            )
            if cm.start_background_collection():
                print("Background collection started successfully")
                return 0
            else:
                print("Failed to start background collection")
                return 1
        elif sys.argv[1] == "stop-background":
            cm = CollectionManager(
                Config(),
                DatabaseService(Config().get_database_path()),
                [RansomlookCollector(), RansomwareLiveCollector()],
                AlertTrigger(DatabaseService(Config().get_database_path())),
                ConsoleNotifier()
            )
            if cm.stop_background_collection():
                print("Background collection stopped successfully")
                return 0
            else:
                print("Failed to stop background collection")
                return 1
        elif sys.argv[1] == "status":
            if is_background_process_running():
                pid = read_pid_file()
                print(f"Background collection is running (PID: {pid})")
                return 0
            else:
                print("Background collection is not running")
                return 1
        else:
            print("Unknown command. Available commands: start-background, stop-background, status")
            return 1
    
    # Normal CLI operation
    cli = CLI()
    cli.main_menu()
    return 0

if __name__ == "__main__":
    sys.exit(main())