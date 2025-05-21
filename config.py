# config.py
"""
Configuration management for the ransomware intelligence system.

This module handles loading, saving, and accessing configuration settings.
"""

import configparser
import os
import logging
from utils.error_utils import ConfigError, handle_exception

class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass

class Config:
    """
    Configuration manager for the ransomware intelligence system.
    
    This class handles loading and saving configuration settings,
    with defaults for when a configuration file doesn't exist.
    """
    
    def __init__(self, config_path="config.ini"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str): Path to the configuration file
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger("config")
        
        # Set defaults
        self.config["General"] = {
            "interval": "300",
            "database_path": "sqlite:///ransomware_intel.db"
        }
        
        self.config["Logging"] = {
            "level": "INFO",
            "file": "ransomware_intel.log"
        }
        
        # Load configuration if exists
        if os.path.exists(config_path):
            try:
                self.config.read(config_path)
                self.logger.info(f"Loaded configuration from {config_path}")
            except configparser.Error as e:
                self.logger.error(f"Error loading configuration: {str(e)}")
                # Continue with defaults
        else:
            self.logger.info(f"Configuration file {config_path} not found, using defaults")
            self.save()
            
    def save(self):
        """
        Save configuration to file.
        
        Raises:
            ConfigError: If the configuration cannot be saved
        """
        try:
            with open(self.config_path, "w") as f:
                self.config.write(f)
            self.logger.info(f"Saved configuration to {self.config_path}")
        except (IOError, PermissionError) as e:
            handle_exception(
                e,
                self.logger,
                f"Error saving configuration to {self.config_path}",
                reraise=True,
                reraise_as=ConfigError
            )
            
    def get_interval(self) -> int:
        """
        Get polling interval in seconds.
        
        Returns:
            int: Polling interval in seconds
        
        Raises:
            ConfigError: If the interval cannot be parsed as an integer
        """
        try:
            return int(self.config["General"]["interval"])
        except (KeyError, ValueError) as e:
            error_msg = f"Invalid interval in configuration: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigError(error_msg) from e
    
    def set_interval(self, interval: int) -> None:
        """
        Set polling interval in seconds.
        
        Args:
            interval (int): Polling interval in seconds
            
        Raises:
            ConfigError: If the interval is not a positive integer
        """
        if not isinstance(interval, int) or interval <= 0:
            error_msg = f"Invalid interval: {interval}, must be a positive integer"
            self.logger.error(error_msg)
            raise ConfigError(error_msg)
            
        self.config["General"]["interval"] = str(interval)
        self.save()
        self.logger.info(f"Set polling interval to {interval} seconds")
        
    def get_database_path(self) -> str:
        """
        Get database connection string.
        
        Returns:
            str: Database connection string
        """
        return self.config["General"]["database_path"]
    
    def set_database_path(self, path: str) -> None:
        """
        Set database connection string.
        
        Args:
            path (str): Database connection string
        """
        self.config["General"]["database_path"] = path
        self.save()
        self.logger.info(f"Set database path to {path}")
    
    def get_log_level(self) -> str:
        """
        Get logging level.
        
        Returns:
            str: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level = self.config["Logging"]["level"].upper()
        
        # Validate level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level not in valid_levels:
            self.logger.warning(f"Invalid log level: {level}, defaulting to INFO")
            return "INFO"
            
        return level
    
    def set_log_level(self, level):
        """
        Set logging level.
        
        Args:
            level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Raises:
            ConfigError: If the level is not valid
        """
        level = level.upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        if level not in valid_levels:
            error_msg = f"Invalid log level: {level}, must be one of {valid_levels}"
            self.logger.error(error_msg)
            raise ConfigError(error_msg)
            
        self.config["Logging"]["level"] = level
        self.save()
        self.logger.info(f"Set log level to {level}")
    
    def get_log_file(self):
        """
        Get log file path.
        
        Returns:
            str: Log file path
        """
        return self.config["Logging"]["file"]
    
    def set_log_file(self, file_path):
        """
        Set log file path.
        
        Args:
            file_path (str): Log file path
        """
        self.config["Logging"]["file"] = file_path
        self.save()
        self.logger.info(f"Set log file to {file_path}")

    def get_droplet_endpoint(self) -> str:
        """
        Get the endpoint URL for the Droplet API.
        
        Returns:
            str: Droplet API endpoint URL
        """
        try:
            return self.config.get("Droplet", "endpoint", fallback="http://localhost:5000")
        except (KeyError, configparser.NoSectionError):
            # If section doesn't exist, create it with defaults
            if "Droplet" not in self.config:
                self.config["Droplet"] = {}
            self.config["Droplet"]["endpoint"] = "http://localhost:5000"
            self.save()
            return "http://localhost:5000"

    def get_droplet_api_secret(self) -> str:
        """
        Get the API secret for authenticating with the Droplet API.
        
        Returns:
            str: Droplet API secret
        """
        try:
            return self.config.get("Droplet", "api_secret", fallback="test-secret")
        except (KeyError, configparser.NoSectionError):
            # If section doesn't exist, create it with defaults
            if "Droplet" not in self.config:
                self.config["Droplet"] = {}
            self.config["Droplet"]["api_secret"] = "test-secret"
            self.save()
            return "test-secret"

    def set_droplet_endpoint(self, endpoint: str) -> None:
        """
        Set the endpoint URL for the Droplet API.
        
        Args:
            endpoint: URL for the Droplet API
        """
        if "Droplet" not in self.config:
            self.config["Droplet"] = {}
        self.config["Droplet"]["endpoint"] = endpoint
        self.save()
        self.logger.info(f"Set Droplet endpoint to {endpoint}")

    def set_droplet_api_secret(self, secret: str) -> None:
        """
        Set the API secret for authenticating with the Droplet API.
        
        Args:
            secret: API secret
        """
        if "Droplet" not in self.config:
            self.config["Droplet"] = {}
        self.config["Droplet"]["api_secret"] = secret
        self.save()
        self.logger.info("Updated Droplet API secret")