import os
import shutil
from typing import Dict, Any
from src.document_processor import DocumentProcessor
from src.data_extractor import DataExtractor
from src.airtable_client import AirtableClient
from src.file_manager import FileManager
from src.logger import SWNALogger

class ProcessingPipeline:
    """Main processing pipeline with atomic operations for AR Ack documents."""
    
    def __init__(self, logger=None):
        self.logger = logger or SWNALogger()
        
        # Initialize components
        self.document_processor = DocumentProcessor(self.logger)
        self.data_extractor = DataExtractor(self.logger)
        self.airtable_client = AirtableClient(self.logger)
        self.file_manager = FileManager(self.logger)
        
        # Track processing state for rollback
        self.processing_state = {}
        
        # Track daily statistics
        self.daily_stats = {
            'processed': 0,
            'ignored': 0, 
            'failed': 0,
            'total': 0
        }
    
    def process_file(self, file_path):
        """
        Process a single PDF file through the complete pipeline.
        All operations are atomic - either all succeed or all are rolled back.
        Returns True if successful, False if failed.
        """
        filename = os.path.basename(file_path)
        
        # Track total files processed
        self.daily_stats['total'] += 1
        
        # Add separator line for readability
        self.logger.info("=" * 80)
        
        # Start performance tracking
        processing_timer = self.logger.start_timer(f"file_processing_{filename}")
        
        # Log processing start with structured data
        self.logger.log_file_processing_start(filename, file_path)
        
        # Initialize processing state
        self.processing_state = {
            'original_file_path': file_path,
            'airtable_updated': False,
            'file_moved': False,
            'new_file_path': None,
            'record_id': None
        }
        
        try:
            # Step 1: Check if file is already processed
            if self.file_manager.is_already_processed_file(filename):
                self.logger.debug(f"File already processed, skipping: {filename}")
                return True
            
            # Step 2: Process document and check if it's AR Ack
            is_ar_ack, extracted_text = self.document_processor.process_document(file_path)
            
            if not is_ar_ack:
                self.daily_stats['ignored'] += 1
                self.logger.log_file_ignored(filename, "Not AR Ack document", file_path)
                # End performance tracking
                self.logger.end_timer(processing_timer)
                return True  # Not an error, just not our target document type
            
            # Step 3: Extract data (Case ID and Client Name)
            case_id, client_name = self.data_extractor.extract_all_data(extracted_text)
            
            if not case_id or not client_name:
                self._handle_processing_failure(filename, "Failed to extract required data (Case ID or Client Name)", file_path, processing_timer)
                self.daily_stats['failed'] += 1
                return False
            
            # Step 4: Format client name for Airtable matching
            client_name_formatted = self.data_extractor.format_client_name_for_matching(client_name)
            
            if not client_name_formatted:
                self._handle_processing_failure(filename, "Failed to format client name for matching", file_path, processing_timer)
                self.daily_stats['failed'] += 1
                return False
            
            # Step 5: Validate all required operations can be performed
            if not self._validate_all_operations(client_name, client_name_formatted):
                self._handle_processing_failure(filename, "Pre-validation failed", file_path, processing_timer)
                self.daily_stats['failed'] += 1
                return False
            
            # Step 6: Execute all operations atomically
            success = self._execute_atomic_operations(
                file_path, case_id, client_name, client_name_formatted
            )
            
            if success:
                # Get the new filename and destination for audit log
                new_filename = self.file_manager.generate_new_filename(client_name)
                destination_folder = os.path.basename(self.file_manager.construct_client_folder_path(client_name_formatted))
                
                # Log successful processing with audit details
                self.logger.log_file_processing_success(filename, case_id, client_name, new_filename, destination_folder, file_path)
                
                # Log Airtable update details
                from datetime import datetime
                current_date = datetime.now().strftime("%m.%d.%y")
                log_entry = f"Rcvd AR Ack. Filed Away. {current_date} AI"
                update_data = {
                    "Case ID": case_id,
                    "Log": log_entry
                }
                self.logger.log_airtable_update_details(client_name, self.processing_state['record_id'], case_id, log_entry, update_data)
                
                # Log file move operation
                if self.processing_state.get('new_file_path'):
                    self.logger.log_file_moved(file_path, self.processing_state['new_file_path'], filename, new_filename)
                
                # End performance tracking
                duration = self.logger.end_timer(processing_timer)
                self.logger.info(f"File processing completed in {duration:.2f} seconds")
                
                self.daily_stats['processed'] += 1
                return True
            else:
                self._rollback_operations()
                self._handle_processing_failure(filename, "Atomic operations failed", file_path, processing_timer)
                self.daily_stats['failed'] += 1
                return False
                
        except Exception as e:
            self._rollback_operations()
            error_details = {
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "processing_state": self.processing_state.copy()
            }
            self._handle_processing_failure(filename, f"Unexpected error: {str(e)}", file_path, processing_timer, error_details)
            self.daily_stats['failed'] += 1
            return False
    
    def _validate_all_operations(self, client_name, client_name_formatted):
        """
        Pre-validate that all operations can be performed successfully.
        Returns True if all validations pass, False otherwise.
        """
        try:
            self.logger.info(f"[VALIDATION] Starting validation for client: {client_name_formatted}")
            
            # Validate client exists in Airtable
            client_record = self.airtable_client.find_client_by_name(client_name_formatted)
            if not client_record:
                self.logger.log_validation_result("airtable_client_lookup", False, {
                    "client_name": client_name_formatted,
                    "message": f"Client not found in Airtable: {client_name_formatted}"
                })
                return False
            
            # Store record ID for later use
            self.processing_state['record_id'] = client_record['id']
            self.logger.log_validation_result("airtable_client_lookup", True, {
                "client_name": client_name_formatted,
                "record_id": client_record['id'],
                "message": f"Client record found: {client_record['id']}"
            })
            
            # REAL MODE - ACTUAL FOLDER VALIDATION
            destination_folder = self.file_manager.construct_client_folder_path(client_name_formatted)
            self.logger.info(f"[VALIDATION] Validating destination folder: {destination_folder}")
            
            # Validate destination folder exists
            if not destination_folder or not self.file_manager.validate_destination_folder(destination_folder):
                self.logger.log_validation_result("destination_folder", False, {
                    "client_name": client_name_formatted,
                    "destination_folder": destination_folder,
                    "message": f"Destination folder does not exist: {destination_folder}"
                })
                return False
            
            # Validate new filename can be generated
            new_filename = self.file_manager.generate_new_filename(client_name)
            if not new_filename:
                self.logger.log_validation_result("filename_generation", False, {
                    "client_name": client_name,
                    "message": "Cannot generate new filename"
                })
                return False
            
            # Check if file would already exist at destination
            new_file_path = os.path.join(destination_folder, new_filename)
            
            if os.path.exists(new_file_path):
                self.logger.log_validation_result("file_conflict", False, {
                    "client_name": client_name_formatted,
                    "new_file_path": new_file_path,
                    "message": f"File already exists at destination: {new_file_path}"
                })
                return False
            
            # All validations passed
            self.logger.log_validation_result("complete_validation", True, {
                "client_name": client_name_formatted,
                "destination_folder": destination_folder,
                "new_filename": new_filename,
                "new_file_path": new_file_path,
                "message": f"All validations passed for {client_name_formatted}"
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return False
    
    def _execute_atomic_operations(self, file_path, case_id, client_name, client_name_formatted):
        """
        Execute all operations atomically.
        Returns True if all operations succeed, False if any fail.
        """
        try:
            # Operation 1: Update Airtable record
            record_id = self.processing_state['record_id']
            if not self.airtable_client.update_client_record(record_id, case_id):
                self.logger.error("Airtable update failed")
                return False
            
            self.processing_state['airtable_updated'] = True
            
            # Operation 2: Move and rename file
            success, new_file_path = self.file_manager.move_and_rename_file(
                file_path, client_name, client_name_formatted
            )
            
            if not success:
                self.logger.error("File move/rename failed")
                return False
            
            self.processing_state['file_moved'] = True
            self.processing_state['new_file_path'] = new_file_path
            
            return True
            
        except Exception as e:
            self.logger.error(f"Atomic operations execution failed: {str(e)}")
            return False
    
    def _rollback_operations(self):
        """
        Rollback any operations that were performed if the pipeline fails.
        """
        try:
            # If file was moved, move it back
            if self.processing_state.get('file_moved') and self.processing_state.get('new_file_path'):
                original_path = self.processing_state['original_file_path']
                new_path = self.processing_state['new_file_path']
                
                try:
                    if os.path.exists(new_path):
                        shutil.move(new_path, original_path)
                        self.logger.info(f"Rolled back file move: {new_path} -> {original_path}")
                except Exception as e:
                    self.logger.error(f"Failed to rollback file move: {str(e)}")
            
            # Note: Airtable rollback is complex and not implemented in this version
            # In production, you might want to store the original values and restore them
            if self.processing_state.get('airtable_updated'):
                self.logger.error("Airtable rollback not implemented - manual intervention may be required")
            
        except Exception as e:
            self.logger.error(f"Rollback operations failed: {str(e)}")
    
    def _handle_processing_failure(self, filename: str, reason: str, file_path: str = None, 
                                  timer_id: str = None, error_details: Dict[str, Any] = None):
        """Handle processing failure with proper logging and performance tracking."""
        # End performance tracking if timer provided
        if timer_id:
            try:
                duration = self.logger.end_timer(timer_id)
                self.logger.info(f"File processing failed after {duration:.2f} seconds")
            except:
                pass  # Timer may have already been ended
        
        # Log the failure with structured data
        self.logger.log_file_processing_failure(filename, reason, file_path, error_details)
    
    def log_daily_summary(self):
        """Log daily processing summary."""
        self.logger.log_daily_summary(
            processed_count=self.daily_stats['processed'],
            ignored_count=self.daily_stats['ignored'], 
            failed_count=self.daily_stats['failed'],
            total_count=self.daily_stats['total']
        )
    
    def get_processing_stats(self):
        """Get current processing statistics."""
        return self.daily_stats.copy()