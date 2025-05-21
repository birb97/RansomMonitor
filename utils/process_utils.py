# utils/process_utils.py
"""
Process management utilities for the ransomware intelligence system.

This module provides utilities for:
- Managing background processes
- Handling process IDs (PIDs)
- Checking if processes are running
"""

import os
import signal
import logging
import subprocess
import sys
import time

logger = logging.getLogger("utils.process_utils")

def get_pid_file_path():
    """
    Get the path to the PID file.
    
    Returns:
        str: Path to the PID file
    """
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ransom-monitor.pid")

def is_process_running(pid):
    """
    Check if a process with the given PID is running.
    
    Args:
        pid (int): Process ID to check
        
    Returns:
        bool: True if the process is running, False otherwise
    """
    try:
        # POSIX-based systems (Linux, macOS)
        if os.name == 'posix':
            # Sending signal 0 doesn't kill the process but checks if it exists
            os.kill(pid, 0)
            return True
        # Windows systems
        elif os.name == 'nt':
            # Check for process existence using 'tasklist' command
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return str(pid) in result.stdout
        return False
    except OSError:
        return False

def write_pid_file(pid):
    """
    Write a PID to the PID file.
    
    Args:
        pid (int): Process ID to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(get_pid_file_path(), 'w') as f:
            f.write(str(pid))
        return True
    except Exception as e:
        logger.error(f"Error writing PID file: {str(e)}")
        return False

def read_pid_file():
    """
    Read the PID from the PID file.
    
    Returns:
        int or None: Process ID if file exists, None otherwise
    """
    pid_file = get_pid_file_path()
    if not os.path.exists(pid_file):
        return None
        
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        return pid
    except Exception as e:
        logger.error(f"Error reading PID file: {str(e)}")
        return None

def delete_pid_file():
    """
    Delete the PID file.
    
    Returns:
        bool: True if successful, False otherwise
    """
    pid_file = get_pid_file_path()
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
            return True
        except Exception as e:
            logger.error(f"Error deleting PID file: {str(e)}")
            return False
    return True  # File didn't exist, so deletion is "successful"

def is_background_process_running():
    """
    Check if a background process is running.
    
    Returns:
        bool: True if a background process is running, False otherwise
    """
    pid = read_pid_file()
    if pid is None:
        return False
    
    # Check if the process is actually running
    if is_process_running(pid):
        return True
    
    # Process is not running but PID file exists, clean up
    delete_pid_file()
    return False

def stop_background_process():
    """
    Stop the background process if running.
    
    Returns:
        bool: True if stopped successfully or not running, False on error
    """
    pid = read_pid_file()
    if pid is None:
        return True  # No process to stop
    
    try:
        if is_process_running(pid):
            if os.name == 'posix':
                os.kill(pid, signal.SIGTERM)
            elif os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
            
            # Wait a moment to ensure process terminates
            time.sleep(0.5)
            
            # Check if process is still running after terminate signal
            if is_process_running(pid):
                logger.warning(f"Process {pid} did not terminate gracefully, forcing...")
                if os.name == 'posix':
                    os.kill(pid, signal.SIGKILL)
                # Windows already used /F (force) flag
                
                # Wait again
                time.sleep(0.5)
                
                if is_process_running(pid):
                    logger.error(f"Failed to kill process {pid}")
                    return False
        
        delete_pid_file()
        return True
    except Exception as e:
        logger.error(f"Error stopping background process: {str(e)}")
        return False