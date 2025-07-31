"""
Pytest configuration and fixtures for SWNA Automation tests
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch

# Ensure we can import from the parent directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def test_env_setup():
    """Set up test environment variables."""
    original_env = {}
    
    # Store original values
    env_vars = ["AIRTABLE_PAT", "AIRTABLE_BASE_ID", "SYNC_FOLDER_PATH", "LOG_LEVEL"]
    for var in env_vars:
        original_env[var] = os.environ.get(var)
    
    # Set test values
    os.environ["AIRTABLE_PAT"] = "test_pat_token"
    os.environ["AIRTABLE_BASE_ID"] = "test_base_id"
    os.environ["SYNC_FOLDER_PATH"] = "/test/sync"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    yield
    
    # Restore original values
    for var, value in original_env.items():
        if value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = value

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="swna_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_settings():
    """Mock the settings module for testing."""
    with patch('config.settings.AIRTABLE_PAT', 'test_pat'), \
         patch('config.settings.AIRTABLE_BASE_ID', 'test_base'), \
         patch('config.settings.SYNC_FOLDER_PATH', '/test/sync'), \
         patch('config.settings.CLIENTS_TABLE_NAME', 'Clients'):
        yield

@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """Set up logging for tests."""
    import logging
    caplog.set_level(logging.DEBUG)
    yield caplog

@pytest.fixture
def sample_ar_ack_text():
    """Sample AR Ack document text for testing."""
    return """
    Case ID Number: 50001234
    
    Employee Name: Test ARACK
    
    According to our records, you have been designated as the authorized representative in the above case. As the authorized representative, you have the ability to receive correspondence, submit additional evidence, argue factual or legal issues and exercise claimant rights pertaining to the above claim.
    """

@pytest.fixture
def sample_invalid_text():
    """Sample non-AR Ack document text for testing."""
    return """
    This is just a regular document.
    It does not contain the AR Ack signature text.
    It should be ignored by the system.
    """

# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "rollback: mark test as rollback test")
    config.addinivalue_line("markers", "slow: mark test as slow running")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "rollback" in item.name:
            item.add_marker(pytest.mark.rollback)