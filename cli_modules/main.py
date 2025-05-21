# cli/main.py
import os
import logging
from config import Config
from storage import Database
from collectors import RansomlookCollector, RansomwareLiveCollector
from alerting import AlertTrigger, ConsoleNotifier

from .collection_manager import CollectionManager
from .watchlist_manager import WatchlistManager
from .settings_manager import SettingsManager
from .alert_manager import AlertManager
from .ui import clear_screen, print_header

class CLI:
    def __init__(self):
        self.config = Config()
        self.database = Database(self.config.get_database_path())
        self.database.initialize()
        
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, self.config.get_log_level()),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(self.config.get_log_file()),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("cli")
        self.collectors = [
            RansomlookCollector(),
            RansomwareLiveCollector()
        ]
        
        self.alert_trigger = AlertTrigger(self.database)
        self.notifier = ConsoleNotifier()
        
        # Initialize managers
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
    
    def main_menu(self):
        """Main CLI menu"""
        while True:
            clear_screen()
            print_header("RANSOMWARE INTELLIGENCE SYSTEM")
            
            status = "RUNNING" if self.collection_manager.is_running() else "STOPPED"
            print(f"Collection Status: {status}")
            print(f"Poll Interval: {self.config.get_interval()} seconds")
            
            print("\n1. Start/Stop collection")
            print("2. Manage watchlist")
            print("3. Settings")
            print("4. Test domain matching")
            print("5. Check database")
            print("6. Check existing claims")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ")
            
            if choice == "1":
                if self.collection_manager.is_running():
                    self.collection_manager.stop_collection()
                    input("Collection stopped. Press Enter to continue...")
                else:
                    self.collection_manager.start_collection()
                    input("Collection started. Press Enter to continue...")
            elif choice == "2":
                self.watchlist_manager.manage_watchlist()
            elif choice == "3":
                self.settings_manager.manage_settings()
            elif choice == "4":
                self.alert_manager.test_domain_match()
            elif choice == "5":
                self.alert_manager.check_database()
            elif choice == "6":
                self.alert_manager.check_existing_claims()
            elif choice == "7":
                if self.collection_manager.is_running():
                    self.collection_manager.stop_collection()
                print("\nExiting program. Goodbye!")
                break
            else:
                input("Invalid choice. Press Enter to continue...")

def main():
    cli = CLI()
    cli.main_menu()

if __name__ == "__main__":
    main()