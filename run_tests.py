# run_tests.py
"""
Comprehensive test runner for the Stamp Collection Manager application.
This script runs all unit tests and generates coverage reports.
"""

import unittest
import sys
import os
import argparse
from io import StringIO
import tempfile
from typing import Optional

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    import coverage
    coverage_module = coverage
    HAS_COVERAGE = True
except ImportError:
    coverage_module = None
    HAS_COVERAGE = False
    print("Coverage.py not installed. Install with: pip install coverage")


class TestResult:
    """Custom test result class to capture detailed test information"""
    
    def __init__(self):
        self.tests_run = 0
        self.failures = []
        self.errors = []
        self.successes = []
        self.skipped = []
    
    def add_success(self, test):
        self.successes.append(test)
        self.tests_run += 1
    
    def add_failure(self, test, err):
        self.failures.append((test, err))
        self.tests_run += 1
    
    def add_error(self, test, err):
        self.errors.append((test, err))
        self.tests_run += 1
    
    def add_skip(self, test, reason):
        self.skipped.append((test, reason))


def discover_tests(test_directory='.', pattern='test_*.py'):
    """Discover all test files in the given directory"""
    loader = unittest.TestLoader()
    suite = loader.discover(test_directory, pattern=pattern)
    return suite


def run_specific_test_module(module_name):
    """Run tests from a specific module"""
    try:
        module = __import__(module_name)
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        return suite
    except ImportError as e:
        print(f"Error importing test module {module_name}: {e}")
        return None


def print_test_summary(result):
    """Print a detailed test summary"""
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests Run: {total_tests}")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    
    if hasattr(result, 'skipped'):
        print(f"Skipped: {len(result.skipped)}")
    
    if total_tests > 0:
        success_rate = (successes / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    print(f"{'='*60}")
    
    # Print details of failures and errors
    if failures > 0:
        print(f"\nFAILURES ({failures}):")
        print("-" * 40)
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"{i}. {test}")
            print(f"   {traceback}")
    
    if errors > 0:
        print(f"\nERRORS ({errors}):")
        print("-" * 40)
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"{i}. {test}")
            print(f"   {traceback}")


def run_tests_with_coverage(test_suite, coverage_report=True):
    """Run tests with coverage measurement"""
    if not HAS_COVERAGE or coverage_module is None:
        print("Coverage measurement not available. Running tests without coverage.")
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(test_suite)
    
    # Initialize coverage
    cov = coverage_module.Coverage()
    cov.start()
    
    try:
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=StringIO())
        result = runner.run(test_suite)
        
        # Stop coverage measurement
        cov.stop()
        cov.save()
        
        if coverage_report:
            print("\n" + "="*60)
            print("COVERAGE REPORT")
            print("="*60)
            cov.report(show_missing=True)
            
            # Generate HTML coverage report
            try:
                cov.html_report(directory='htmlcov')
                print(f"\nHTML coverage report generated in 'htmlcov' directory")
            except Exception as e:
                print(f"Could not generate HTML report: {e}")
        
        return result
        
    except Exception as e:
        cov.stop()
        print(f"Error during coverage measurement: {e}")
        # Fall back to running without coverage
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(test_suite)


def run_integration_tests():
    """Run integration tests that require database setup"""
    print("Running integration tests...")
    
    # Create temporary database for integration tests
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Set environment variable for test database
        os.environ['TEST_DB_PATH'] = temp_db.name
        
        # Import and run integration tests
        from test_stamp_collection import TestDatabaseIntegration
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestDatabaseIntegration)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result
        
    finally:
        # Clean up
        try:
            os.unlink(temp_db.name)
        except OSError:
            pass
        
        if 'TEST_DB_PATH' in os.environ:
            del os.environ['TEST_DB_PATH']


def validate_test_environment():
    """Validate that the test environment is properly set up"""
    print("Validating test environment...")
    
    required_modules = ['enhanced_stamp', 'database_manager']
    optional_modules = ['enhanced_gui']
    
    # Check required modules
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} - OK")
        except ImportError as e:
            print(f"✗ {module} - MISSING: {e}")
            return False
    
    # Check optional modules (GUI components may not be available in all environments)
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✓ {module} - OK")
        except ImportError as e:
            print(f"⚠ {module} - WARNING: {e} (GUI tests will be skipped)")
    
    # Check database connectivity
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        conn.close()
        print("✓ SQLite database - OK")
    except Exception as e:
        print(f"✗ SQLite database - ERROR: {e}")
        return False
    
    print("Environment validation complete.\n")
    return True


def create_test_config():
    """Create test configuration"""
    config = {
        'test_patterns': ['test_*.py'],
        'test_directories': ['.', 'tests'],
        'coverage_sources': ['enhanced_stamp.py', 'database_manager.py', 'enhanced_gui.py'],
        'exclude_patterns': ['test_*.py', '__pycache__/*'],
        'minimum_coverage': 80.0,
        'generate_html_report': True,
        'verbose_output': True
    }
    return config


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Run tests for Stamp Collection Manager')
    parser.add_argument('--module', help='Run tests from specific module')
    parser.add_argument('--no-coverage', action='store_true', help='Skip coverage measurement')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--gui', action='store_true', help='Run GUI tests only')
    parser.add_argument('--validate', action='store_true', help='Validate test environment only')
    parser.add_argument('--pattern', default='test_*.py', help='Test file pattern')
    parser.add_argument('--directory', default='.', help='Test directory')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    if args.validate:
        success = validate_test_environment()
        sys.exit(0 if success else 1)
    
    # Validate environment first
    if not validate_test_environment():
        print("Environment validation failed. Exiting.")
        sys.exit(1)
    
    config = create_test_config()
    
    print("="*60)
    print("STAMP COLLECTION MANAGER - TEST RUNNER")
    print("="*60)
    
    # Determine which tests to run
    if args.module:
        print(f"Running tests from module: {args.module}")
        test_suite = run_specific_test_module(args.module)
        if test_suite is None:
            sys.exit(1)
    elif args.integration:
        print("Running integration tests only...")
        result = run_integration_tests()
        print_test_summary(result)
        sys.exit(0 if result.wasSuccessful() else 1)
    elif args.unit:
        print("Running unit tests only...")
        test_suite = discover_tests(args.directory, 'test_stamp_collection.py')
    elif args.gui:
        print("Running GUI tests only...")
        try:
            test_suite = discover_tests(args.directory, 'test_gui.py')
        except Exception as e:
            print(f"GUI tests not available: {e}")
            sys.exit(1)
    else:
        print("Running all available tests...")
        test_suite = discover_tests(args.directory, args.pattern)
    
    # Run tests
    if args.no_coverage or not HAS_COVERAGE:
        runner = unittest.TextTestRunner(verbosity=2 if not args.quiet else 1)
        result = runner.run(test_suite)
    else:
        result = run_tests_with_coverage(test_suite, coverage_report=not args.quiet)
    
    # Print summary
    if not args.quiet:
        print_test_summary(result)
    
    # Check if tests passed
    if result.wasSuccessful():
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()


# ============================================================================
# pytest_config.py - Alternative pytest configuration
# ============================================================================

"""
Alternative pytest configuration for the Stamp Collection Manager tests.
To use pytest instead of unittest, install pytest and run: pytest -v
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def test_database():
    """Create a temporary test database for the session"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    yield temp_db.name
    
    # Cleanup
    try:
        os.unlink(temp_db.name)
    except OSError:
        pass


@pytest.fixture
def mock_gui():
    """Mock GUI components for testing"""
    with patch('sys.modules') as mock_modules:
        # Mock FreeSimpleGUI
        mock_sg = MagicMock()
        mock_sg.theme = MagicMock()
        mock_sg.Window = MagicMock()
        mock_sg.popup = MagicMock()
        mock_sg.popup_error = MagicMock()
        mock_sg.popup_yes_no = MagicMock(return_value='Yes')
        
        mock_modules['FreeSimpleGUI'] = mock_sg
        
        yield mock_sg


@pytest.fixture
def sample_stamp():
    """Create a sample stamp for testing"""
    from enhanced_stamp import Stamp
    from decimal import Decimal
    
    return Stamp(
        scott_number="TEST001",
        description="Test Stamp",
        country="TestLand",
        year=2000,
        catalog_value_mint=Decimal('10.00'),
        qty_mint=1
    )


@pytest.fixture
def sample_stamps():
    """Create multiple sample stamps for testing"""
    from enhanced_stamp import Stamp
    from decimal import Decimal
    
    stamps = [
        Stamp("US001", "Washington", "USA", 1932, 
              catalog_value_mint=Decimal('5.00'), qty_mint=1),
        Stamp("US002", "Lincoln", "USA", 1909, used=True,
              catalog_value_used=Decimal('2.50'), qty_used=1),
        Stamp("CA001", "Maple Leaf", "Canada", 1935,
              catalog_value_mint=Decimal('15.00'), qty_mint=1, want_list=True),
    ]
    return stamps


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "gui: mark test as a GUI test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location/name"""
    for item in items:
        # Add markers based on test file name
        if "test_gui" in str(item.fspath):
            item.add_marker(pytest.mark.gui)
        elif "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if any(keyword in item.name.lower() for keyword in ['slow', 'performance', 'load']):
            item.add_marker(pytest.mark.slow)


# ============================================================================
# Makefile equivalent commands (for Windows/cross-platform)
# ============================================================================

"""
# test_commands.py - Cross-platform test commands

This file provides cross-platform equivalents to Makefile commands.
Run with: python test_commands.py <command>

Available commands:
  test          - Run all tests
  test-unit     - Run unit tests only
  test-gui      - Run GUI tests only
  test-integration - Run integration tests only
  coverage      - Generate coverage report
  clean         - Clean up test artifacts
  validate      - Validate test environment
"""

import subprocess
import sys
import os
import shutil
import glob


def run_command(command, shell=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def clean_test_artifacts():
    """Clean up test artifacts and temporary files"""
    print("Cleaning test artifacts...")
    
    patterns_to_remove = [
        '*.pyc',
        '__pycache__',
        '.coverage',
        'htmlcov',
        '.pytest_cache',
        '*.db',
        'test_*.log'
    ]
    
    for pattern in patterns_to_remove:
        if pattern.startswith('.') and os.path.exists(pattern):
            if os.path.isdir(pattern):
                shutil.rmtree(pattern)
                print(f"Removed directory: {pattern}")
            else:
                os.remove(pattern)
                print(f"Removed file: {pattern}")
        else:
            for file_path in glob.glob(pattern):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Removed directory: {file_path}")
                else:
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
    
    print("Cleanup complete.")


def run_test_command(command_name):
    """Run the specified test command"""
    commands = {
        'test': 'python run_tests.py',
        'test-unit': 'python run_tests.py --unit',
        'test-gui': 'python run_tests.py --gui',
        'test-integration': 'python run_tests.py --integration',
        'coverage': 'python run_tests.py',
        'validate': 'python run_tests.py --validate',
        'clean': clean_test_artifacts,
    }
    
    if command_name not in commands:
        print(f"Unknown command: {command_name}")
        print("Available commands:", list(commands.keys()))
        return False
    
    if callable(commands[command_name]):
        commands[command_name]()
        return True
    
    success, stdout, stderr = run_command(commands[command_name])
    
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    
    return success


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python test_commands.py <command>")
        print("Available commands: test, test-unit, test-gui, test-integration, coverage, validate, clean")
        sys.exit(1)
    
    command = sys.argv[1]
    success = run_test_command(command)
    sys.exit(0 if success else 1)