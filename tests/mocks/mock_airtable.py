"""
Mock Airtable client with rollback tracking for integration tests
"""

from datetime import datetime

class MockAirtableClient:
    """Mock Airtable client that tracks operations for rollback testing."""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.operations = []  # Track all operations for rollback
        self.should_fail_at = None  # Inject failures at specific operations
        self.operation_count = 0
        
        # Test client database
        self.test_clients = {
            "ARACK, Test": {
                "id": "rec_test_001",
                "fields": {
                    "Name": "ARACK, Test",
                    "Case ID": "",
                    "Log": "Previous log entries..."
                }
            },
            "Client, Existing": {
                "id": "rec_test_002", 
                "fields": {
                    "Name": "Client, Existing",
                    "Case ID": "12345678",
                    "Log": "Previous entries..."
                }
            }
        }
        
        # Track updates for rollback
        self.original_states = {}
    
    def find_client_by_name(self, client_name_formatted):
        """Mock client search with failure injection."""
        self.operation_count += 1
        
        # Check if we should fail at this operation
        if self.should_fail_at == self.operation_count:
            if self.logger:
                self.logger.error(f"[MOCK] Injected failure at operation {self.operation_count}")
            raise Exception("Mock Airtable search failure")
        
        # Record operation
        operation = {
            "type": "search",
            "client_name": client_name_formatted,
            "operation_id": self.operation_count
        }
        self.operations.append(operation)
        
        if self.logger:
            self.logger.info(f"[MOCK] Searching for client: {client_name_formatted}")
        
        # Return mock client if exists
        if client_name_formatted in self.test_clients:
            client_record = self.test_clients[client_name_formatted].copy()
            if self.logger:
                self.logger.info(f"[MOCK] Found client record: {client_record['id']}")
            return client_record
        else:
            if self.logger:
                self.logger.info(f"[MOCK] Client not found: {client_name_formatted}")
            return None
    
    def update_client_record(self, record_id, case_id):
        """Mock record update with rollback tracking."""
        self.operation_count += 1
        
        # Check if we should fail at this operation
        if self.should_fail_at == self.operation_count:
            if self.logger:
                self.logger.error(f"[MOCK] Injected failure at operation {self.operation_count}")
            raise Exception("Mock Airtable update failure")
        
        # Find the original record to store for rollback
        original_record = None
        for client_name, client_data in self.test_clients.items():
            if client_data["id"] == record_id:
                # Store original state for rollback
                self.original_states[record_id] = client_data["fields"].copy()
                original_record = client_data
                break
        
        if not original_record:
            raise Exception(f"Mock record not found: {record_id}")
        
        # Check if Case ID already exists and matches
        existing_case_id = original_record["fields"].get("Case ID", "")
        if existing_case_id == case_id:
            if self.logger:
                self.logger.info(f"[MOCK] Case ID {case_id} already exists for record {record_id} - skipping update")
            
            # Still record the operation for test verification
            operation = {
                "type": "update",
                "record_id": record_id,
                "case_id": case_id,
                "operation_id": self.operation_count,
                "skipped": True,
                "reason": "case_id_already_exists"
            }
            self.operations.append(operation)
            return True
        
        # Simulate update
        current_date = datetime.now().strftime("%m.%d.%y")
        log_entry = f"Rcvd AR Ack. Filed Away. {current_date} AI"
        
        existing_log = original_record["fields"].get("Log", "")
        new_log = f"{existing_log}\n{log_entry}" if existing_log else log_entry
        
        # Update the mock data
        original_record["fields"]["Case ID"] = case_id
        original_record["fields"]["Log"] = new_log
        
        # Record operation for rollback
        operation = {
            "type": "update",
            "record_id": record_id,
            "case_id": case_id,
            "operation_id": self.operation_count,
            "original_state": self.original_states[record_id]
        }
        self.operations.append(operation)
        
        if self.logger:
            self.logger.info(f"[MOCK] Updated record {record_id} with Case ID: {case_id}")
        
        return True
    
    def validate_client_match(self, extracted_client_name, airtable_record):
        """Mock validation."""
        airtable_name = airtable_record.get('fields', {}).get('Name', '')
        return airtable_name == extracted_client_name
    
    def process_client_update(self, extracted_client_name, case_id):
        """Mock complete client processing."""
        try:
            # Find client record
            client_record = self.find_client_by_name(extracted_client_name)
            if not client_record:
                if self.logger:
                    self.logger.error(f"[MOCK] Client not found: {extracted_client_name}")
                return False
            
            # Validate match
            if not self.validate_client_match(extracted_client_name, client_record):
                return False
            
            # Update record
            record_id = client_record['id']
            return self.update_client_record(record_id, case_id)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"[MOCK] Client processing failed: {str(e)}")
            return False
    
    def rollback_operations(self):
        """Rollback all operations in reverse order."""
        if self.logger:
            self.logger.info(f"[MOCK] Rolling back {len(self.operations)} operations")
        
        # Process operations in reverse order
        for operation in reversed(self.operations):
            try:
                if operation["type"] == "update":
                    record_id = operation["record_id"]
                    original_state = operation["original_state"]
                    
                    # Find the record and restore original state
                    for client_name, client_data in self.test_clients.items():
                        if client_data["id"] == record_id:
                            client_data["fields"] = original_state.copy()
                            if self.logger:
                                self.logger.info(f"[MOCK] Rolled back update for record {record_id}")
                            break
                
                # Search operations don't need rollback
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[MOCK] Rollback failed for operation {operation['operation_id']}: {str(e)}")
        
        # Clear operations and states
        self.operations.clear()
        self.original_states.clear()
        self.operation_count = 0
    
    def set_failure_point(self, operation_number):
        """Set which operation should fail for testing."""
        self.should_fail_at = operation_number
    
    def reset(self):
        """Reset mock to initial state."""
        self.rollback_operations()
        self.should_fail_at = None
    
    def get_operations_log(self):
        """Get log of all operations performed."""
        return self.operations.copy()
    
    def get_client_state(self, client_name):
        """Get current state of a test client."""
        if client_name in self.test_clients:
            return self.test_clients[client_name]["fields"].copy()
        return None