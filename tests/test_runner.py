#!/usr/bin/env python3
"""
Test runner script for SWNA Automation integration tests
"""

import sys
import os
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests():
    """Run the integration tests with proper reporting."""
    print("=" * 80)
    print("SWNA Automation Integration Tests")
    print("=" * 80)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("ERROR: pytest not installed. Install with: pip install pytest")
        return 1
    
    # Check if reportlab is available (needed for PDF generation)
    try:
        import reportlab
    except ImportError:
        print("ERROR: reportlab not installed. Install with: pip install reportlab")
        return 1
    
    # Run tests
    test_args = [
        "tests/test_integration.py",
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ]
    
    result = pytest.main(test_args)
    
    print("\n" + "=" * 80)
    if result == 0:
        print("✅ All integration tests PASSED!")
        print("\nThe pipeline is working correctly with proper rollback functionality.")
    else:
        print("❌ Some tests FAILED!")
        print("\nCheck the output above for details on what went wrong.")
    print("=" * 80)
    
    return result

def run_specific_test(test_name):
    """Run a specific test by name."""
    print(f"Running specific test: {test_name}")
    test_args = [
        f"tests/test_integration.py::{test_name}",
        "-v",
        "--tb=long",
    ]
    
    return pytest.main(test_args)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        exit_code = run_specific_test(test_name)
    else:
        # Run all tests
        exit_code = run_tests()
    
    sys.exit(exit_code)