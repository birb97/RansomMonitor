#!/usr/bin/env python3
# background_collector.py
"""
Background collection process for the ransomware intelligence system.

This script runs the collection process in the background, independent
of the CLI. It's designed to be started and stopped via the CLI or
run directly as a standalone script.
"""

import io
import os
import sys
import time
import logging
import signal
import argparse
import traceback
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules
from config import Config
from database import DatabaseService
from collectors import RansomlookCollector, RansomwareLiveCollector, RansomwatchCollector, OmegalockCollector
from alerting import AlertTrigger, ConsoleNotifier
from utils.process_utils import write_pid_file, delete_pid_file

# Fix console encoding if needed (Windows especially)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def setup_logging():
    """
    Set up logging configuration.
    
    Returns:
        logging.Logger: Configured logger
    """
    config = Config()
    log_file = config.get_log_file()
    log_level = getattr(logging, config.get_log_level())
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("background_collector")

def handle_exit(signum, frame):
    """Signal handler for graceful termination."""
    logger.info("Received termination signal, shutting down...")
    delete_pid_file()
    sys.exit(0)

def collect_and_process(database, collectors, alert_trigger, notifier, logger):
    """
    Collect and process data from all sources.
    
    Args:
        database: Database instance
        collectors: List of collector instances
        alert_trigger: Alert trigger instance
        notifier: Notifier instance
        logger: Logger instance
    """
    logger.info("Starting collection cycle")
    for collector in collectors:
        try:
            logger.info(f"Collecting from {collector.name}")
            claims = collector.collect()
            logger.info(f"Collected {len(claims)} claims from {collector.name}")
            
            if not claims:
                logger.info(f"No claims to process from {collector.name}")
                continue
                
            # Use bulk add for efficiency
            added_ids = database.bulk_add_claims(claims)
            logger.info(f"Added {len(added_ids)} new claims to database from {collector.name}")
            
            # Process each new claim for alerts
            alert_count = 0
            for i, claim in enumerate(claims):
                if i < len(added_ids) and added_ids[i]:  # Only process if it's a new claim
                    logger.info(f"Processing claim ID {added_ids[i]} for alerts")
                    alerts = alert_trigger.process_claim(claim)
                    alert_count += len(alerts)
                    
                    # Send notifications for each alert
                    for alert in alerts:
                        success = notifier.send_alert(alert)
                        if not success:
                            logger.warning(f"Failed to send alert notification for claim ID {added_ids[i]}")
            
            if alert_count > 0:
                logger.info(f"Generated {alert_count} alerts from {collector.name}")
                
        except Exception as e:
            logger.error(f"Error collecting from {collector.name}: {str(e)}")
            logger.error(traceback.format_exc())
    
    logger.info("Collection cycle completed")

def main():
    """Main function for the background collector."""
    global logger
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Ransomware Intelligence Background Collector")
    parser.add_argument("--interval", type=int, help="Override collection interval (seconds)")
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting background collector process")
    
    # Register signal handlers for graceful termination
    if os.name == 'posix':
        signal.signal(signal.SIGTERM, handle_exit)
        signal.signal(signal.SIGINT, handle_exit)
    
    # Write PID file
    pid = os.getpid()
    if not write_pid_file(pid):
        logger.error("Failed to write PID file, exiting")
        sys.exit(1)
    
    logger.info(f"Background collector process started with PID {pid}")
    
    try:
        # Initialize components
        config = Config()
        interval = args.interval or config.get_interval()
        
        database = DatabaseService(config.get_database_path())
        database.initialize()
        
        collectors = [
            RansomlookCollector(),
            RansomwareLiveCollector(),
            OmegalockCollector(),
            RansomwatchCollector()
        ]
        
        alert_trigger = AlertTrigger(database)
        notifier = ConsoleNotifier()
        
        logger.info(f"Configured to collect data every {interval} seconds")
        
        # Main collection loop
        while True:
            try:
                start_time = time.time()
                
                # Collect and process data
                collect_and_process(database, collectors, alert_trigger, notifier, logger)
                
                # Calculate sleep time based on how long collection took
                elapsed = time.time() - start_time
                sleep_time = max(1, interval - elapsed)
                
                logger.info(f"Sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in collection cycle: {str(e)}")
                logger.error(traceback.format_exc())
                # Don't exit, just continue to the next cycle
                time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        delete_pid_file()
        logger.info("Background collector stopped")

if __name__ == "__main__":
    main()