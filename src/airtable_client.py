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
            # REAL MODE - ACTUAL AIRTABLE SEARCH
            self.logger.info(f"Searching Airtable for client: {client_name_formatted}")
            
            # Search for records that start with the client name (handles SSN suffix)
            # First try exact match
            records = self.table.all(formula=f"{{Name}} = '{client_name_formatted}'")
            
            # If no exact match, try prefix match for names with SSN suffix
            if not records:
                # Search for names that start with "Last, First" (may have " - SSSS" suffix)
                prefix_formula = f"LEFT({{Name}}, {len(client_name_formatted)}) = '{client_name_formatted}'"
                records = self.table.all(formula=prefix_formula)
                if records:
                    self.logger.info(f"Found client using prefix match (likely has SSN suffix)")
            
            records = records or []
            
            if records:
                if len(records) == 1:
                    record = records[0]
                    self.logger.log_client_matched(client_name_formatted, record['id'])
                    return record
                else:
                    # Multiple matches found - this shouldn't happen with exact matching
                    self.logger.error(f"Multiple client records found for: {client_name_formatted}")
                    return None
            else:
                self.logger.debug(f"No client record found for: {client_name_formatted}")
                return None
                
        except Exception as e:
            self.logger.error(f"Airtable client search failed: {str(e)}")
            return None
    
    def update_client_record(self, record_id, case_id):
        """
        Update client record with Case ID and add log entry.
        Returns True if successful, False otherwise.
        """
        try:
            # REAL MODE - ACTUAL AIRTABLE UPDATE
            self.logger.info(f"Getting current record: {record_id}")
            
            # Get current record to check existing data
            current_record = self.table.get(record_id)
            current_fields = current_record.get('fields', {})
            
            # Prepare update data
            current_date = datetime.now().strftime("%m.%d.%y")
            log_entry = f"Rcvd AR Ack. Filed Away. {current_date} AI"
            
            # Get existing log content
            existing_log = current_fields.get('Log', '')
            
            # Prepend new log entry to the beginning
            if existing_log:
                new_log = f"{log_entry}\n{existing_log}"
            else:
                new_log = log_entry
            
            # Check if Case ID already exists and matches
            existing_case_id = current_fields.get('Case ID', '')
            if existing_case_id == case_id:
                # Case ID is correct, but still update Log field
                update_data = {'Log': new_log}
                self.logger.info(f"Case ID {case_id} already correct for record {record_id} - updating Log only")
            else:
                # Case ID needs updating, update both fields
                update_data = {
                    'Case ID': case_id,
                    'Log': new_log
                }
                self.logger.info(f"Updating both Case ID and Log for record {record_id}")
            
            # Log what will be updated
            self.logger.info(f"Updating Airtable record {record_id} with: {update_data}")
            
            # Perform actual update
            updated_record = self.table.update(record_id, update_data)
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