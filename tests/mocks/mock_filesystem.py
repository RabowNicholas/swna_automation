"""
Mock file manager with rollback tracking for integration tests
"""

import os
import shutil
from datetime import datetime

class MockFileManager:
    """Mock file manager that tracks operations for rollback testing."""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.file_operations = []  # Track all file operations
        self.should_fail_at = None  # Inject failures
        self.operation_count = 0
        
        # Mock file system state
        self.mock_files = {}  # Track file locations
        self.mock_folders = {
            "/test/sync/2. Active Clients/ARACK, Test/DOL Letters": True,
            "/test/sync/2. Active Clients/Client, Existing/DOL Letters": True
        }
    
    def generate_new_filename(self, client_name):
        """Mock filename generation."""
        try:
            name_parts = client_name.strip().split()
            if len(name_parts) < 2:
                return None
            
            first_name = name_parts[0]
            last_name = name_parts[-1]
            first_initial = first_name[0].upper()
            current_date = datetime.now().strftime("%m.%d.%y")
            
            return f"AR Ack - {first_initial}. {last_name} {current_date}.pdf"
        except Exception as e:
            if self.logger:
                self.logger.error(f"[MOCK] Filename generation failed: {str(e)}")
            return None
    
    def construct_client_folder_path(self, client_name_formatted):
        """Mock folder path construction."""
        return f"/test/sync/2. Active Clients/{client_name_formatted}/DOL Letters"
    
    def validate_destination_folder(self, destination_path):
        """Mock folder validation."""
        self.operation_count += 1
        
        # Check if we should fail at this operation
        if self.should_fail_at == self.operation_count:
            if self.logger:
                self.logger.error(f"[MOCK] Injected failure at operation {self.operation_count}")
            return False
        
        # Check mock folder existence
        exists = destination_path in self.mock_folders
        if self.logger:
            self.logger.info(f"[MOCK] Folder validation for {destination_path}: {exists}")
        return exists
    
    def move_and_rename_file(self, original_file_path, client_name, client_name_formatted):
        """Mock file move with rollback tracking."""
        self.operation_count += 1
        
        # Check if we should fail at this operation
        if self.should_fail_at == self.operation_count:
            if self.logger:
                self.logger.error(f"[MOCK] Injected failure at operation {self.operation_count}")
            raise Exception("Mock file move failure")
        
        try:
            # Generate new filename
            new_filename = self.generate_new_filename(client_name)
            if not new_filename:
                return False, None
            
            # Construct destination
            destination_folder = self.construct_client_folder_path(client_name_formatted)
            if not destination_folder:
                return False, None
            
            # Validate destination folder (in real mode, not logging mode)
            if not self.validate_destination_folder(destination_folder):
                if self.logger:
                    self.logger.error(f"[MOCK] Destination folder does not exist: {destination_folder}")
                return False, None
            
            destination_path = os.path.join(destination_folder, new_filename)
            
            # Check if file already exists at destination
            if destination_path in self.mock_files:
                if self.logger:
                    self.logger.error(f"[MOCK] File already exists at destination: {destination_path}")
                return False, None
            
            # Record the file move operation
            operation = {
                "type": "file_move",
                "original_path": original_file_path,
                "destination_path": destination_path,
                "operation_id": self.operation_count
            }
            self.file_operations.append(operation)
            
            # Simulate the move in mock file system
            if original_file_path in self.mock_files:
                del self.mock_files[original_file_path]
            self.mock_files[destination_path] = True
            
            if self.logger:
                original_filename = os.path.basename(original_file_path)
                self.logger.info(f"[MOCK] Moved file: {original_file_path} -> {destination_path}")
            
            return True, destination_path
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"[MOCK] File move failed: {str(e)}")
            return False, None
    
    def is_already_processed_file(self, filename):
        """Mock processed file check."""
        return filename.startswith("AR Ack - ") and filename.endswith(".pdf")
    
    def get_file_size_mb(self, file_path):
        """Mock file size check."""
        return 1.5  # Mock size
    
    def rollback_file_operations(self):
        """Rollback all file operations in reverse order."""
        if self.logger:
            self.logger.info(f"[MOCK] Rolling back {len(self.file_operations)} file operations")
        
        # Process operations in reverse order
        for operation in reversed(self.file_operations):
            try:
                if operation["type"] == "file_move":
                    original_path = operation["original_path"]
                    destination_path = operation["destination_path"]
                    
                    # Reverse the move in mock file system
                    if destination_path in self.mock_files:
                        del self.mock_files[destination_path]
                    self.mock_files[original_path] = True
                    
                    if self.logger:
                        self.logger.info(f"[MOCK] Rolled back file move: {destination_path} -> {original_path}")
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[MOCK] File rollback failed for operation {operation['operation_id']}: {str(e)}")
        
        # Clear operations
        self.file_operations.clear()
        self.operation_count = 0
    
    def set_failure_point(self, operation_number):
        """Set which operation should fail for testing."""
        self.should_fail_at = operation_number
    
    def reset(self):
        """Reset mock to initial state."""
        self.rollback_file_operations()
        self.should_fail_at = None
    
    def add_mock_file(self, file_path):
        """Add a file to the mock file system."""
        self.mock_files[file_path] = True
    
    def file_exists(self, file_path):
        """Check if file exists in mock system."""
        return file_path in self.mock_files
    
    def get_operations_log(self):
        """Get log of all file operations performed."""
        return self.file_operations.copy()
    
    def add_mock_folder(self, folder_path):
        """Add a folder to the mock file system."""
        self.mock_folders[folder_path] = True