from pyairtable import Table
from datetime import datetime
from config.settings import AIRTABLE_PAT, AIRTABLE_BASE_ID, CLIENTS_TABLE_NAME
from src.logger import SWNALogger

class AirtableClient:
    """Handle all Airtable operations for client matching and record updates."""
    
    def __init__(self, logger=None):
        self.logger = logger or SWNALogger()
        self.table = Table(AIRTABLE_PAT, AIRTABLE_BASE_ID, CLIENTS_TABLE_NAME)
    
    def find_client_by_name(self, client_name_formatted):
        """
        Find client record in Airtable by exact name match.
        Returns record dict or None if not found.
        """
        try:
            # LOGGING ONLY MODE - ACTUAL SEARCH COMMENTED OUT
            self.logger.info(f"[LOGGING MODE] Would search Airtable for client: {client_name_formatted}")
            
            # Search for exact match in the Name field - COMMENTED OUT
            # records = self.table.all(formula=f"{{Name}} = '{client_name_formatted}'")
            
            # Simulate finding a record for logging purposes
            simulated_record = {
                'id': 'rec123456789',
                'fields': {
                    'Name': client_name_formatted,
                    'Case ID': '',
                    'Log': 'Previous log entries...'
                }
            }
            
            self.logger.info(f"[LOGGING MODE] Simulated finding client record: {simulated_record['id']}")
            self.logger.log_client_matched(client_name_formatted, simulated_record['id'])
            return simulated_record
            
            # Original logic commented out:
            # if records:
            #     if len(records) == 1:
            #         record = records[0]
            #         self.logger.log_client_matched(client_name_formatted, record['id'])
            #         return record
            #     else:
            #         # Multiple matches found - this shouldn't happen with exact matching
            #         self.logger.error(f"Multiple client records found for: {client_name_formatted}")
            #         return None
            # else:
            #     self.logger.debug(f"No client record found for: {client_name_formatted}")
            #     return None
                
        except Exception as e:
            self.logger.error(f"Airtable client search failed: {str(e)}")
            return None
    
    def update_client_record(self, record_id, case_id):
        """
        Update client record with Case ID and add log entry.
        Returns True if successful, False otherwise.
        """
        try:
            # LOGGING ONLY MODE - ACTUAL UPDATE COMMENTED OUT
            self.logger.info(f"[LOGGING MODE] Would get current record: {record_id}")
            
            # Get current record to check existing data
            # current_record = self.table.get(record_id)
            # current_fields = current_record.get('fields', {})
            
            # Simulate current fields for logging
            current_fields = {'Case ID': '', 'Log': 'Previous log entries...'}
            
            # Check if Case ID already exists and matches
            existing_case_id = current_fields.get('Case ID', '')
            if existing_case_id == case_id:
                self.logger.info(f"[LOGGING MODE] Case ID {case_id} already exists for record {record_id} - would skip update")
                return True
            
            # Prepare update data
            current_date = datetime.now().strftime("%m.%d.%y")
            log_entry = f"Rcvd AR Ack. Filed Away. {current_date} AI"
            
            # Get existing log content
            existing_log = current_fields.get('Log', '')
            
            # Append new log entry
            if existing_log:
                new_log = f"{existing_log}\n{log_entry}"
            else:
                new_log = log_entry
            
            # Update fields
            update_data = {
                'Case ID': case_id,
                'Log': new_log
            }
            
            # Log what would be updated
            self.logger.info(f"[LOGGING MODE] Would update Airtable record {record_id} with: {update_data}")
            
            # Perform update - COMMENTED OUT FOR LOGGING MODE
            # updated_record = self.table.update(record_id, update_data)
            self.logger.log_airtable_updated(record_id, case_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Airtable record update failed for {record_id}: {str(e)}")
            return False
    
    def validate_client_match(self, extracted_client_name, airtable_record):
        """
        Validate that the extracted client name matches the Airtable record.
        This is an additional safety check.
        Returns True if valid match, False otherwise.
        """
        try:
            airtable_name = airtable_record.get('fields', {}).get('Name', '')
            
            if not airtable_name:
                self.logger.error("Airtable record missing Name field")
                return False
            
            # The names should be identical since we used exact matching
            if airtable_name == extracted_client_name:
                return True
            else:
                self.logger.error(f"Client name mismatch: extracted='{extracted_client_name}', airtable='{airtable_name}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Client validation failed: {str(e)}")
            return False
    
    def process_client_update(self, extracted_client_name, case_id):
        """
        Complete client processing: find record, validate, and update.
        Returns True if all steps successful, False otherwise.
        """
        try:
            # Find client record
            client_record = self.find_client_by_name(extracted_client_name)
            if not client_record:
                self.logger.error(f"Client not found in Airtable: {extracted_client_name}")
                return False
            
            # Validate match
            if not self.validate_client_match(extracted_client_name, client_record):
                return False
            
            # Update record
            record_id = client_record['id']
            if self.update_client_record(record_id, case_id):
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Client processing failed: {str(e)}")
            return False