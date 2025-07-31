#!/usr/bin/env python3
"""
Integration tests for SWNA Automation Pipeline
Tests the complete workflow with rollback scenarios
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the classes we're testing
from src.processing_pipeline import ProcessingPipeline
from src.logger import SWNALogger

# Import our mocks
from tests.mocks.mock_airtable import MockAirtableClient
from tests.mocks.mock_filesystem import MockFileManager
from tests.test_pdf_generator import create_test_ar_ack_pdf, create_invalid_pdf, create_malformed_ar_ack_pdf


class TestIntegrationPipeline:
    """Integration tests for the complete processing pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup_test(self, tmp_path):
        """Setup for each test."""
        self.tmp_path = tmp_path
        self.test_files_dir = tmp_path / "test_files"
        self.test_files_dir.mkdir()
        
        # Create logger for testing
        self.logger = SWNALogger()
        
        # Create mock instances
        self.mock_airtable = MockAirtableClient(self.logger)
        self.mock_file_manager = MockFileManager(self.logger)
        
        # Create test PDF path
        self.test_pdf_path = str(self.test_files_dir / "test_ar_ack.pdf")
        
        # Reset mocks before each test
        self.mock_airtable.reset()
        self.mock_file_manager.reset()
    
    def create_pipeline_with_mocks(self):
        """Create a pipeline with mocked components."""
        pipeline = ProcessingPipeline(self.logger)
        
        # Replace real components with mocks
        pipeline.airtable_client = self.mock_airtable
        pipeline.file_manager = self.mock_file_manager
        
        # Override the rollback method to use our mock rollbacks
        original_rollback = pipeline._rollback_operations
        def mock_rollback():
            try:
                # Use mock rollbacks instead of real ones
                if pipeline.processing_state.get('file_moved'):
                    self.mock_file_manager.rollback_file_operations()
                if pipeline.processing_state.get('airtable_updated'):
                    self.mock_airtable.rollback_operations()
            except Exception as e:
                self.logger.error(f"Mock rollback failed: {str(e)}")
        
        pipeline._rollback_operations = mock_rollback
        return pipeline
    
    def test_happy_path_success(self):
        """Test successful processing of Test ARACK case 50001234."""
        # Create test PDF
        create_test_ar_ack_pdf("Test ARACK", "50001234", self.test_pdf_path)
        
        # Add the file to mock filesystem
        self.mock_file_manager.add_mock_file(self.test_pdf_path)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file
        result = pipeline.process_file(self.test_pdf_path)
        
        # Verify success
        assert result is True, "Pipeline should succeed"
        
        # Verify operations were performed
        airtable_ops = self.mock_airtable.get_operations_log()
        file_ops = self.mock_file_manager.get_operations_log()
        
        # Should have search and update operations
        assert len(airtable_ops) == 2, f"Expected 2 Airtable operations, got {len(airtable_ops)}"
        assert airtable_ops[0]["type"] == "search", "First operation should be search"
        assert airtable_ops[1]["type"] == "update", "Second operation should be update"
        assert airtable_ops[1]["case_id"] == "50001234", "Case ID should match"
        
        # Should have file move operation
        assert len(file_ops) >= 1, f"Expected at least 1 file operation, got {len(file_ops)}"
        assert file_ops[-1]["type"] == "file_move", "Should have file move operation"
        
        # Verify client state was updated
        client_state = self.mock_airtable.get_client_state("ARACK, Test")
        assert client_state["Case ID"] == "50001234", "Case ID should be updated"
        assert "Rcvd AR Ack. Filed Away." in client_state["Log"], "Log should be updated"
    
    def test_airtable_failure_rollback(self):
        """Test rollback when Airtable operation fails."""
        # Create test PDF
        create_test_ar_ack_pdf("Test ARACK", "50001234", self.test_pdf_path)
        self.mock_file_manager.add_mock_file(self.test_pdf_path)
        
        # Set Airtable to fail at update operation (operation 2)
        self.mock_airtable.set_failure_point(2)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file - should fail
        result = pipeline.process_file(self.test_pdf_path)
        
        # Verify failure
        assert result is False, "Pipeline should fail when Airtable fails"
        
        # Verify no file operations were performed (atomic behavior)
        file_ops = self.mock_file_manager.get_operations_log()
        assert len(file_ops) == 0, "No file operations should be performed if Airtable fails"
        
        # Verify client state was not changed
        client_state = self.mock_airtable.get_client_state("ARACK, Test")
        assert client_state["Case ID"] == "", "Case ID should not be updated after failure"
        
        # Verify file is still in original location
        assert self.mock_file_manager.file_exists(self.test_pdf_path), "File should remain in original location"
    
    def test_file_operation_failure_rollback(self):
        """Test rollback when file operation fails."""
        # Create test PDF
        create_test_ar_ack_pdf("Test ARACK", "50001234", self.test_pdf_path)
        self.mock_file_manager.add_mock_file(self.test_pdf_path)
        
        # Set file manager to fail at move operation (operation 2 in file manager)
        self.mock_file_manager.set_failure_point(2)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file - should fail
        result = pipeline.process_file(self.test_pdf_path)
        
        # Verify failure
        assert result is False, "Pipeline should fail when file operation fails"
        
        # Verify Airtable operations were rolled back
        client_state = self.mock_airtable.get_client_state("ARACK, Test")
        assert client_state["Case ID"] == "", "Airtable changes should be rolled back"
        
        # Verify file is still in original location
        assert self.mock_file_manager.file_exists(self.test_pdf_path), "File should remain in original location"
    
    def test_client_not_found_failure(self):
        """Test failure when client is not found in Airtable."""
        # Create test PDF for non-existent client
        create_test_ar_ack_pdf("Nonexistent Client", "50001234", self.test_pdf_path)
        self.mock_file_manager.add_mock_file(self.test_pdf_path)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file - should fail
        result = pipeline.process_file(self.test_pdf_path)
        
        # Verify failure
        assert result is False, "Pipeline should fail when client not found"
        
        # Verify no operations were performed
        airtable_ops = self.mock_airtable.get_operations_log()
        file_ops = self.mock_file_manager.get_operations_log()
        
        # Should only have search operation, no update
        assert len(airtable_ops) == 1, f"Expected 1 Airtable operation, got {len(airtable_ops)}"
        assert airtable_ops[0]["type"] == "search", "Should only have search operation"
        
        # Should have no file operations
        assert len(file_ops) == 0, f"Expected 0 file operations, got {len(file_ops)}"
    
    def test_invalid_pdf_skipped(self):
        """Test that non-AR Ack PDFs are skipped."""
        # Create invalid PDF
        invalid_pdf_path = str(self.test_files_dir / "invalid.pdf")
        create_invalid_pdf(invalid_pdf_path)
        self.mock_file_manager.add_mock_file(invalid_pdf_path)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file - should succeed but skip processing
        result = pipeline.process_file(invalid_pdf_path)
        
        # Verify success (skipped files return True)
        assert result is True, "Invalid PDFs should be skipped successfully"
        
        # Verify no operations were performed
        airtable_ops = self.mock_airtable.get_operations_log()
        file_ops = self.mock_file_manager.get_operations_log()
        
        assert len(airtable_ops) == 0, "No Airtable operations should be performed for invalid PDFs"
        assert len(file_ops) == 0, "No file operations should be performed for invalid PDFs"
    
    def test_malformed_ar_ack_missing_case_id(self):
        """Test handling of AR Ack PDF missing Case ID."""
        # Create malformed PDF missing case ID
        malformed_pdf_path = str(self.test_files_dir / "malformed_case_id.pdf")
        create_malformed_ar_ack_pdf(malformed_pdf_path, missing_field="case_id")
        self.mock_file_manager.add_mock_file(malformed_pdf_path)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file - should fail
        result = pipeline.process_file(malformed_pdf_path)
        
        # Verify failure
        assert result is False, "Pipeline should fail when Case ID is missing"
        
        # Verify no operations were performed
        airtable_ops = self.mock_airtable.get_operations_log()
        file_ops = self.mock_file_manager.get_operations_log()
        
        assert len(airtable_ops) == 0, "No Airtable operations should be performed when Case ID missing"
        assert len(file_ops) == 0, "No file operations should be performed when Case ID missing"
    
    def test_malformed_ar_ack_missing_client_name(self):
        """Test handling of AR Ack PDF missing Client Name."""
        # Create malformed PDF missing client name
        malformed_pdf_path = str(self.test_files_dir / "malformed_client.pdf")
        create_malformed_ar_ack_pdf(malformed_pdf_path, missing_field="client_name")
        self.mock_file_manager.add_mock_file(malformed_pdf_path)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file - should fail
        result = pipeline.process_file(malformed_pdf_path)
        
        # Verify failure
        assert result is False, "Pipeline should fail when Client Name is missing"
        
        # Verify no operations were performed
        airtable_ops = self.mock_airtable.get_operations_log()
        file_ops = self.mock_file_manager.get_operations_log()
        
        assert len(airtable_ops) == 0, "No Airtable operations should be performed when Client Name missing"
        assert len(file_ops) == 0, "No file operations should be performed when Client Name missing"
    
    def test_already_processed_file_skipped(self):
        """Test that already processed files are skipped."""
        # Create file with processed naming pattern
        processed_file_path = str(self.test_files_dir / "AR Ack - T. ARACK 01.01.25.pdf")
        create_test_ar_ack_pdf("Test ARACK", "50001234", processed_file_path)
        self.mock_file_manager.add_mock_file(processed_file_path)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file - should succeed but skip
        result = pipeline.process_file(processed_file_path)
        
        # Verify success (already processed files return True)
        assert result is True, "Already processed files should be skipped successfully"
        
        # Verify no operations were performed
        airtable_ops = self.mock_airtable.get_operations_log()
        file_ops = self.mock_file_manager.get_operations_log()
        
        assert len(airtable_ops) == 0, "No operations should be performed for already processed files"
        assert len(file_ops) == 0, "No operations should be performed for already processed files"
    
    def test_case_id_already_exists_in_airtable(self):
        """Test handling when Case ID already exists in Airtable record."""
        # Create test PDF (client name will be formatted as "CLIENT, Existing")
        create_test_ar_ack_pdf("Existing Client", "12345678", self.test_pdf_path)
        self.mock_file_manager.add_mock_file(self.test_pdf_path)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Process the file - should succeed but skip update
        result = pipeline.process_file(self.test_pdf_path)
        
        # Verify success
        assert result is True, "Pipeline should succeed when Case ID already exists"
        
        # Verify search was performed and update was attempted but skipped
        airtable_ops = self.mock_airtable.get_operations_log()
        assert len(airtable_ops) == 2, "Should have search and update operations"
        assert airtable_ops[0]["type"] == "search", "First operation should be search"
        assert airtable_ops[1]["type"] == "update", "Second operation should be update"
        assert airtable_ops[1].get("skipped") == True, "Update should be marked as skipped"
        
        # Verify file was still moved (since Airtable update succeeded, even if skipped)
        file_ops = self.mock_file_manager.get_operations_log()
        assert len(file_ops) >= 1, "File should still be moved when Case ID already exists"
    
    def test_validation_failure_rollback(self):
        """Test rollback when pre-validation fails."""
        # Create test PDF
        create_test_ar_ack_pdf("Test ARACK", "50001234", self.test_pdf_path)
        self.mock_file_manager.add_mock_file(self.test_pdf_path)
        
        # Set file manager to fail at folder validation (this happens in validation phase)
        # We need to set failure at the right operation number for validation
        self.mock_file_manager.set_failure_point(1)
        
        # Create pipeline with mocks
        pipeline = self.create_pipeline_with_mocks()
        
        # Get initial state
        initial_client_state = self.mock_airtable.get_client_state("ARACK, Test")
        
        # Process the file - should fail
        result = pipeline.process_file(self.test_pdf_path)
        
        # Verify failure
        assert result is False, "Pipeline should fail when file operation fails"
        
        # Verify client state was rolled back to original state
        final_client_state = self.mock_airtable.get_client_state("ARACK, Test")
        assert final_client_state["Case ID"] == initial_client_state["Case ID"], "Client state should be rolled back"
        
        # Verify file is still in original location
        assert self.mock_file_manager.file_exists(self.test_pdf_path), "File should remain in original location after rollback"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])