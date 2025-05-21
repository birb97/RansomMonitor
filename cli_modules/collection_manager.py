# cli_modules/collection_manager.py
"""
Collection process management for the ransomware intelligence system.
"""

import logging
import time
import threading
import subprocess
import os
import sys
from typing import List

from utils.process_utils import (
    is_background_process_running,
    stop_background_process,
    write_pid_file,
    read_pid_file
)

class CollectionManager:
    """Manages the collection process for ransomware intelligence data"""
    
    def __init__(self, config, database, collectors, alert_trigger, notifier):
        self.config = config
        self.database = database
        self.collectors = collectors
        self.alert_trigger = alert_trigger
        self.notifier = notifier
        self.logger = logging.getLogger("collection_manager")
        self.running = False
        self.collection_thread = None
    
    def is_running(self) -> bool:
        """
        Check if collection process is running (either foreground or background).
        
        Returns:
            bool: True if any collection process is running
        """
        # Check foreground process
        if self.running:
            return True
            
        # Check background process
        return is_background_process_running()
    
    def is_background_running(self) -> bool:
        """
        Check if a background collection process is running.
        
        Returns:
            bool: True if background process is running
        """
        return is_background_process_running()
    
    def start_collection(self) -> None:
        """
        Start the collection process in a separate thread (foreground mode).
        
        Returns:
            None
        """
        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        self.logger.info("Collection process started in foreground mode")
    
    def start_background_collection(self) -> bool:
        """
        Start the collection process as a background process that continues
        after the CLI exits.
        
        Returns:
            bool: True if successfully started
        """
        if self.is_background_running():
            self.logger.warning("Background collection is already running")
            return False
            
        # If foreground collection is running, stop it first
        if self.running:
            self.stop_collection()
            
        try:
            # Get the path to the background_collector.py script
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "background_collector.py"
            )
            
            # Ensure the script is executable on Unix-like systems
            if os.name == 'posix' and not os.access(script_path, os.X_OK):
                os.chmod(script_path, 0o755)
            
            # Start the background process
            self.logger.info(f"Starting background collection: {script_path}")
            
            # Different command based on OS
            if os.name == 'posix':
                # Use nohup on Unix-like systems to detach process
                process = subprocess.Popen(
                    ["nohup", sys.executable, script_path, "--interval", str(self.config.get_interval())],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setpgrp  # Detach from parent process
                )
            else:
                # On Windows, use pythonw for windowless operation
                python_exe = sys.executable
                if python_exe.endswith('python.exe'):
                    python_exe = python_exe.replace('python.exe', 'pythonw.exe')
                    
                process = subprocess.Popen(
                    [python_exe, script_path, "--interval", str(self.config.get_interval())],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            
            # Wait a short time for the process to start and write its PID file
            time.sleep(1)
            
            # Check if the background process is running
            if self.is_background_running():
                self.logger.info("Background collection started successfully")
                return True
            else:
                self.logger.error("Failed to start background collection")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting background collection: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def stop_background_collection(self) -> bool:
        """
        Stop the background collection process.
        
        Returns:
            bool: True if successfully stopped
        """
        self.logger.info("Stopping background collection")
        return stop_background_process()
    
    def stop_collection(self) -> None:
        """
        Stop the foreground collection process.
        
        Returns:
            None
        """
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        self.logger.info("Collection process stopped")
    
    def _collection_loop(self) -> None:
        """Main collection loop that runs at the configured interval"""
        while self.running:
            self.collect_and_process()
            time.sleep(self.config.get_interval())
    
    def collect_and_process(self):
        """Collect and process data from all sources"""
        self.logger.info("Starting collection cycle")
        for collector in self.collectors:
            try:
                self.logger.info(f"Collecting from {collector.name}")
                claims = collector.collect()
                self.logger.info(f"Collected {len(claims)} claims from {collector.name}")
                
                if not claims:
                    self.logger.info(f"No claims to process from {collector.name}")
                    continue
                    
                # Use bulk add for efficiency
                added_ids = self.database.bulk_add_claims(claims)
                self.logger.info(f"Added {len(added_ids)} new claims to database from {collector.name}")
                
                # Process each new claim for alerts
                for i, claim in enumerate(claims):
                    if i < len(added_ids) and added_ids[i]:  # Only process if it's a new claim
                        self.logger.info(f"Processing claim ID {added_ids[i]} for alerts")
                        alerts = self.alert_trigger.process_claim(claim)
                        self.logger.info(f"Found {len(alerts)} alerts for claim ID {added_ids[i]}")
                        
                        # Send notifications for each alert
                        for alert in alerts:
                            success = self.notifier.send_alert(alert)
                            self.logger.info(f"Alert notification sent: {success}")
                    
            except Exception as e:
                self.logger.error(f"Error collecting from {collector.name}: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
        
        self.logger.info("Collection cycle completed")