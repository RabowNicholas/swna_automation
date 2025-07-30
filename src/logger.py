import logging
import os
from datetime import datetime

class SWNALogger:
    """Centralized logging system for SWNA automation."""
    
    def __init__(self, log_level="INFO"):
        self.log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "swna_automation.log")
        self.logger = self._setup_logger(log_level)
    
    def _setup_logger(self, log_level):
        """Set up logger with file and console handlers."""
        logger = logging.getLogger("swna_automation")
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatter
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        
        # File handler - append mode
        file_handler = logging.FileHandler(self.log_file, mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message):
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message):
        """Log error message with ERROR prefix for easy identification."""
        self.logger.error(f"ERROR: {message}")
    
    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)
    
    def log_file_processing_start(self, filename):
        """Log start of file processing."""
        self.info(f"Processing started: {filename}")
    
    def log_file_processing_success(self, filename, case_id, client_name):
        """Log successful file processing."""
        self.info(f"Processing completed successfully: {filename} - Case ID: {case_id}, Client: {client_name}")
    
    def log_file_processing_failure(self, filename, reason):
        """Log file processing failure."""
        self.error(f"Processing failed: {filename} - Reason: {reason}")
    
    def log_ar_ack_identified(self, filename):
        """Log AR Ack identification."""
        self.info(f"AR Ack document identified: {filename}")
    
    def log_data_extracted(self, case_id, client_name):
        """Log successful data extraction."""
        self.info(f"Data extracted - Case ID: {case_id}, Client: {client_name}")
    
    def log_client_matched(self, client_name, airtable_record):
        """Log successful client matching."""
        self.info(f"Client matched in Airtable: {client_name} -> {airtable_record}")
    
    def log_airtable_updated(self, record_id, case_id):
        """Log Airtable update."""
        self.info(f"Airtable updated - Record ID: {record_id}, Case ID: {case_id}")
    
    def log_file_renamed_moved(self, old_name, new_name, destination):
        """Log file rename and move operation."""
        self.info(f"File processed: {old_name} -> {new_name} moved to {destination}")
    
    def log_startup(self):
        """Log system startup."""
        self.info("SWNA Automation service started")
    
    def log_shutdown(self):
        """Log system shutdown."""
        self.info("SWNA Automation service stopped")