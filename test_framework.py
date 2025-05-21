# test_framework.py
"""
Simple testing framework for the ransomware intelligence system.

This module provides a lightweight testing framework that allows
for writing and running tests against system components without
external dependencies.
"""

import inspect
import time
import logging
import traceback
import sys
from typing import Dict, List, Callable, Any, Optional, Tuple, Type
from datetime import datetime

# Configure logger for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_framework")


class TestResult:
    """Represents the result of a single test"""
    
    def __init__(self, test_name: str, test_class: str):
        self.test_name = test_name
        self.test_class = test_class
        self.success = False
        self.error_message: Optional[str] = None
        self.execution_time = 0.0
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        """
        Format the test result in a more human-readable way.
        Uses color-like formatting with ASCII characters.
        """
        if self.success:
            status = "[ PASS ]"
            details = f"{self.test_class}.{self.test_name} completed in {self.execution_time:.3f}s"
        else:
            status = "[ FAIL ]"
            error_info = f": {self.error_message}" if self.error_message else ""
            details = f"{self.test_class}.{self.test_name} failed in {self.execution_time:.3f}s{error_info}"
        
        return f"{status} {details}"


class TestCase:
    """Base class for all tests"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"test.{self.__class__.__name__}")
    
    def setUp(self):
        """Set up test fixtures, called before every test method"""
        pass
    
    def tearDown(self):
        """Tear down test fixtures, called after every test method"""
        pass
    
    def assertEqual(self, first: Any, second: Any, msg: Optional[str] = None):
        """Assert that two objects are equal"""
        if first != second:
            raise AssertionError(msg or f"{first} != {second}")
    
    def assertNotEqual(self, first: Any, second: Any, msg: Optional[str] = None):
        """Assert that two objects are not equal"""
        if first == second:
            raise AssertionError(msg or f"{first} == {second}")
    
    def assertTrue(self, expr: bool, msg: Optional[str] = None):
        """Assert that expression is true"""
        if not expr:
            raise AssertionError(msg or f"Expression is not True")
    
    def assertFalse(self, expr: bool, msg: Optional[str] = None):
        """Assert that expression is false"""
        if expr:
            raise AssertionError(msg or f"Expression is not False")
    
    def assertIsNone(self, obj: Any, msg: Optional[str] = None):
        """Assert that object is None"""
        if obj is not None:
            raise AssertionError(msg or f"{obj} is not None")
    
    def assertIsNotNone(self, obj: Any, msg: Optional[str] = None):
        """Assert that object is not None"""
        if obj is None:
            raise AssertionError(msg or "Object is None")
    
    def assertIn(self, member: Any, container: Any, msg: Optional[str] = None):
        """Assert that member is in container"""
        if member not in container:
            raise AssertionError(msg or f"{member} not in {container}")
    
    def assertNotIn(self, member: Any, container: Any, msg: Optional[str] = None):
        """Assert that member is not in container"""
        if member in container:
            raise AssertionError(msg or f"{member} in {container}")
    
    def assertRaises(self, exception_class, callable_obj=None, *args, **kwargs):
        """Assert that an exception is raised"""
        if callable_obj is None:
            return _AssertRaisesContext(exception_class, self)
        try:
            callable_obj(*args, **kwargs)
        except exception_class:
            return
        raise AssertionError(f"{exception_class.__name__} not raised")


class _AssertRaisesContext:
    """Context manager for assertRaises"""
    
    def __init__(self, expected, test_case):
        self.expected = expected
        self.test_case = test_case
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            raise AssertionError(f"{self.expected.__name__} not raised")
        if not issubclass(exc_type, self.expected):
            raise AssertionError(f"Expected {self.expected.__name__}, got {exc_type.__name__}")
        return True


class TestRunner:
    """Discovers and runs tests"""
    
    def __init__(self):
        self.results = []
        self.logger = logging.getLogger("test_runner")
    
    def run_test_case(self, test_case_class) -> List[TestResult]:
        """Run all test methods in a test case class"""
        test_case_results = []
        instance = test_case_class()
        
        # Find all test methods (start with 'test_')
        test_methods = [
            method for method in dir(instance)
            if method.startswith('test_') and callable(getattr(instance, method))
        ]
        
        # Print header for test case
        class_name = test_case_class.__name__
        print(f"\n{'=' * 70}")
        print(f"Test Case: {class_name}")
        print(f"{'-' * 70}")
        
        for method_name in test_methods:
            result = TestResult(method_name, test_case_class.__name__)
            test_method = getattr(instance, method_name)
            
            # Display test method name
            test_desc = method_name.replace('test_', '').replace('_', ' ').capitalize()
            print(f"Running: {test_desc}...", end='', flush=True)
            
            try:
                # Run setUp
                instance.setUp()
                
                # Run test and measure time
                start_time = time.time()
                test_method()
                result.execution_time = time.time() - start_time
                
                # Test passed
                result.success = True
                print("\r✓ " + " " * 60)  # Clear the line and mark as passed
            except Exception as e:
                # Test failed
                result.success = False
                result.error_message = str(e)
                self.logger.error(f"Error in {test_case_class.__name__}.{method_name}: {str(e)}")
                self.logger.debug(traceback.format_exc())
                print(f"\r✗ FAILED: {str(e)}" + " " * 20)  # Clear the line and mark as failed
            finally:
                # Run tearDown
                try:
                    instance.tearDown()
                except Exception as e:
                    self.logger.error(f"Error in tearDown for {test_case_class.__name__}: {str(e)}")
                    if result.success:  # Only override if test was successful
                        result.success = False
                        result.error_message = f"Error in tearDown: {str(e)}"
                        print(f"\r✗ FAILED in tearDown: {str(e)}" + " " * 20)
            
            # Add result
            test_case_results.append(result)
            self.results.append(result)
            
            # Log result
            self.logger.info(str(result))
        
        return test_case_results
    
    def run_test_cases(self, test_case_classes: List[Type]) -> List[TestResult]:
        """Run all test methods in a list of test case classes"""
        self.results = []
        
        total_start_time = time.time()
        for test_case_class in test_case_classes:
            self.run_test_case(test_case_class)
        total_time = time.time() - total_start_time
        
        # Print summary
        self._print_summary(total_time)
        
        return self.results
    
    def _print_summary(self, total_time: float):
        """Print a summary of test results with improved formatting"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        print("\n" + "=" * 70)
        print("TEST RESULTS SUMMARY")
        print("-" * 70)
        print(f"Total tests:    {total}")
        print(f"Passed:         {passed}")
        print(f"Failed:         {failed}")
        print(f"Success rate:   {(passed / total * 100) if total > 0 else 0:.1f}%")
        print(f"Total time:     {total_time:.3f}s")
        print("=" * 70)
        
        if failed > 0:
            print("\nFAILED TESTS:")
            print("-" * 70)
            for result in self.results:
                if not result.success:
                    print(f"  • {result.test_class}.{result.test_name}")
                    print(f"    Error: {result.error_message}")
                    print()
        else:
            print("\nAll tests passed successfully!")
        
        print()


def run_tests(test_modules: Optional[List[str]] = None) -> bool:
    """
    Run tests from specified modules or discover all test modules.
    
    Args:
        test_modules: List of module names to run tests from
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    runner = TestRunner()
    
    print("\n" + "=" * 70)
    print("RANSOMWARE INTELLIGENCE SYSTEM - TEST RUNNER")
    print("=" * 70)
    
    if test_modules is None:
        # Import test registry to find test cases
        from tests import test_registry
        test_case_classes = test_registry.get_all_test_cases()
        
        print(f"Discovered {len(test_case_classes)} test case classes")
    else:
        test_case_classes = []
        for module_name in test_modules:
            try:
                module = __import__(module_name, fromlist=[''])
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and issubclass(obj, TestCase) 
                            and obj != TestCase):
                        test_case_classes.append(obj)
            except ImportError as e:
                print(f"Error importing test module {module_name}: {str(e)}")
    
    if not test_case_classes:
        print("\nNo test cases found. Check your test modules and registration.")
        return False
        
    results = runner.run_test_cases(test_case_classes)
    
    # Return True if all tests passed
    return all(result.success for result in results)


if __name__ == "__main__":
    # Simple command-line interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for the ransomware intelligence system")
    parser.add_argument("modules", nargs="*", help="Test module(s) to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        # Set logging level to DEBUG
        for handler in logging.root.handlers:
            handler.setLevel(logging.DEBUG)
    
    success = run_tests(args.modules if args.modules else None)
    sys.exit(0 if success else 1)