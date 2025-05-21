# tests/test_registry.py
"""
Registry for test cases.

This module provides a registry for test cases to allow for
automatic discovery and running of tests.
"""

import importlib
import sys
import os
import logging
import pkgutil
from typing import Dict, List, Type, Any

logger = logging.getLogger("test_registry")

# Dictionary to store registered test case classes
_test_case_registry = {}

def register_test_case(test_case_class):
    """
    Register a test case class in the registry.
    
    Args:
        test_case_class: Class derived from TestCase
        
    Returns:
        The test case class (for decorator usage)
    """
    _test_case_registry[test_case_class.__name__] = test_case_class
    logger.debug(f"Registered test case: {test_case_class.__name__}")
    return test_case_class

def get_all_test_cases() -> List[Type]:
    """
    Get all registered test case classes.
    
    Returns:
        List of test case classes
    """
    # Import all test modules to ensure all test cases are registered
    _import_all_test_modules()
    
    # Return the registered test cases
    logger.debug(f"Returning {len(_test_case_registry)} registered test cases")
    return list(_test_case_registry.values())

def get_test_case(name: str) -> Type:
    """
    Get a specific test case class by name.
    
    Args:
        name: Name of the test case class
        
    Returns:
        Test case class
    """
    return _test_case_registry.get(name)

def _import_all_test_modules():
    """
    Import all test modules in the tests package using discovery.
    
    This automatically finds and imports all modules in the tests package
    to ensure their test cases are registered.
    """
    tests_dir = os.path.dirname(__file__)
    
    # If running as a script, __file__ might not be available
    if not tests_dir:
        return _import_known_modules()
    
    try:
        # Import known test modules first
        _import_known_modules()
        
        # Then try to dynamically discover others
        for _, name, is_pkg in pkgutil.iter_modules([tests_dir]):
            if name.startswith('test_') and not is_pkg:
                module_name = f'tests.{name}'
                if module_name not in sys.modules:
                    try:
                        importlib.import_module(module_name)
                        logger.debug(f"Discovered and imported test module: {module_name}")
                    except ImportError as e:
                        logger.warning(f"Failed to import discovered module {module_name}: {str(e)}")
    except Exception as e:
        logger.warning(f"Error during test module discovery: {str(e)}")
        # Fall back to known modules if discovery fails
        _import_known_modules()

def _import_known_modules():
    """Import explicitly known test modules as a fallback."""
    known_modules = [
        'tests.test_collectors',
        'tests.test_domain_utils',
        'tests.test_alerts'
    ]
    
    # Only try to import tor_collector if we think it might exist
    tor_test_path = os.path.join(os.path.dirname(__file__), 'test_tor_collector.py')
    if os.path.exists(tor_test_path):
        known_modules.append('tests.test_tor_collector')
    
    # Import all known modules
    for module_name in known_modules:
        _import_module(module_name)

def _import_module(module_name):
    """
    Import a module safely.
    
    Args:
        module_name: Name of the module to import
    """
    try:
        if module_name not in sys.modules:
            importlib.import_module(module_name)
            logger.debug(f"Imported module: {module_name}")
    except ImportError as e:
        logger.warning(f"Failed to import module {module_name}: {str(e)}")