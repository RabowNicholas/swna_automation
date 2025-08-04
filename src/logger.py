import logging
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class ActionType(Enum):
    """Enumeration of all possible system actions for audit tracking."""
    FILE_PROCESSED = "file_processed"
    FILE_IGNORED = "file_ignored"
    FILE_FAILED = "file_failed"
    AIRTABLE_UPDATE = "airtable_update"
    FILE_MOVED = "file_moved"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ERROR_OCCURRED = "error_occurred"
    DAILY_SUMMARY = "daily_summary"

class LogLevel(Enum):
    """Log levels for different types of entries.""" 
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    AUDIT = "AUDIT"

class SWNALogger:
    """Centralized logging system for SWNA automation."""
    
    def __init__(self, log_level="INFO"):
        # Set up file paths
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        self.log_file = os.path.join(logs_dir, "swna_automation.log")
        self.audit_log_file = os.path.join(logs_dir, "audit.jsonl")
        self.performance_log_file = os.path.join(logs_dir, "performance.jsonl")
        
        # Ensure logs directory exists
        os.makedirs(logs_dir, exist_ok=True)
        
        # Set up loggers
        self.logger = self._setup_logger(log_level)
        self.session_id = self._generate_session_id()
        
        # Performance tracking
        self._operation_timers = {}
    
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
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID for tracking related operations."""
        return f"session_{int(time.time())}"
    
    def _write_structured_log(self, log_data: Dict[str, Any], log_file: str):
        """Write structured log entry to JSONL file."""
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, default=str) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write structured log: {str(e)}")
    
    def _create_base_log_entry(self, action_type: ActionType, level: LogLevel = LogLevel.INFO) -> Dict[str, Any]:
        """Create base log entry with common fields."""
        return {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "action_type": action_type.value,
            "level": level.value,
            "pid": os.getpid()
        }
    
    def info(self, message):
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message):
        """Log error message with ERROR prefix for easy identification."""
        self.logger.error(f"ERROR: {message}")
    
    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)
    
    # Performance Tracking Methods
    def start_timer(self, operation_name: str) -> str:
        """Start timing an operation. Returns timer ID."""
        timer_id = f"{operation_name}_{int(time.time() * 1000)}"
        self._operation_timers[timer_id] = {
            'operation': operation_name,
            'start_time': time.time(),
            'start_timestamp': datetime.now().isoformat()
        }
        return timer_id
    
    def end_timer(self, timer_id: str) -> float:
        """End timing an operation and return duration in seconds."""
        if timer_id not in self._operation_timers:
            self.logger.warning(f"Timer {timer_id} not found")
            return 0.0
        
        timer_data = self._operation_timers[timer_id]
        duration = time.time() - timer_data['start_time']
        
        # Log performance data
        perf_entry = self._create_base_log_entry(ActionType.FILE_PROCESSED, LogLevel.INFO)
        perf_entry.update({
            "operation": timer_data['operation'],
            "duration_seconds": round(duration, 3),
            "start_time": timer_data['start_timestamp'],
            "end_time": datetime.now().isoformat()
        })
        
        self._write_structured_log(perf_entry, self.performance_log_file)
        
        # Clean up
        del self._operation_timers[timer_id]
        return duration
    
    # Structured Audit Logging Methods
    def log_file_processing_start(self, filename: str, file_path: str):
        """Log start of file processing with structured data."""
        # Traditional log
        self.info(f"Processing started: {filename}")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.FILE_PROCESSED, LogLevel.AUDIT)
        audit_entry.update({
            "action": "processing_started",
            "filename": filename,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else None
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    def log_file_processing_success(self, filename: str, case_id: str, client_name: str, 
                                   new_filename: str, destination_folder: str, file_path: str = None,
                                   document_type: str = None, classification_confidence: float = None,
                                   classification_reason: str = None):
        """Log successful file processing with complete audit trail and classification data."""
        # Traditional log  
        self.info(f"✅ PROCESSED: {new_filename} | Case: {case_id} | Client: {client_name} | Action: Filed to {destination_folder}")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.FILE_PROCESSED, LogLevel.AUDIT)
        audit_entry.update({
            "action": "processing_success",
            "original_filename": filename,
            "new_filename": new_filename,
            "case_id": case_id,
            "client_name": client_name,
            "destination_folder": destination_folder,
            "file_path": file_path,
            "document_type": document_type,
            "classification_confidence": classification_confidence,
            "classification_reason": classification_reason,
            "status": "SUCCESS"
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    def log_file_processing_failure(self, filename: str, reason: str, file_path: str = None, 
                                   error_details: Dict[str, Any] = None):
        """Log file processing failure with detailed error context."""
        # Traditional log
        self.info(f"⚠️  FAILED: {filename} | Error: {reason}")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.FILE_FAILED, LogLevel.ERROR)
        audit_entry.update({
            "action": "processing_failed",
            "filename": filename,
            "file_path": file_path,
            "failure_reason": reason,
            "error_details": error_details or {},
            "status": "FAILED"
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    def log_file_ignored(self, filename: str, reason: str, file_path: str = None,
                        document_type: str = None, classification_confidence: float = None,
                        classification_reason: str = None):
        """Log when file is ignored with structured data."""
        # Traditional log
        self.info(f"❌ IGNORED: {filename} | Reason: {reason}")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.FILE_IGNORED, LogLevel.INFO)
        audit_entry.update({
            "action": "file_ignored",
            "filename": filename,
            "file_path": file_path,
            "ignore_reason": reason,
            "document_type": document_type,
            "classification_confidence": classification_confidence,
            "classification_reason": classification_reason,
            "status": "IGNORED"
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    def log_airtable_update_details(self, client_name: str, record_id: str, case_id: str, 
                                   log_entry: str, update_data: Dict[str, Any] = None):
        """Log Airtable update with complete audit trail."""
        # Traditional log
        self.info(f"📝 AIRTABLE UPDATE: {client_name} ({record_id}) | Case ID: {case_id} | Log: \"{log_entry}\"")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.AIRTABLE_UPDATE, LogLevel.AUDIT)
        audit_entry.update({
            "action": "airtable_update",
            "client_name": client_name,
            "record_id": record_id,
            "case_id": case_id,
            "log_entry": log_entry,
            "update_data": update_data or {},
            "status": "SUCCESS"
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    def log_file_moved(self, original_path: str, new_path: str, filename: str, new_filename: str):
        """Log file move operation with complete paths."""
        # Traditional log
        self.debug(f"File processed: {filename} -> {new_filename} moved to {os.path.dirname(new_path)}")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.FILE_MOVED, LogLevel.AUDIT)
        audit_entry.update({
            "action": "file_moved",
            "original_path": original_path,
            "new_path": new_path,
            "original_filename": filename,
            "new_filename": new_filename,
            "destination_directory": os.path.dirname(new_path),
            "status": "SUCCESS"
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    def log_validation_result(self, validation_type: str, success: bool, details: Dict[str, Any]):
        """Log validation results with structured data."""
        action_type = ActionType.VALIDATION_PASSED if success else ActionType.VALIDATION_FAILED
        level = LogLevel.INFO if success else LogLevel.WARNING
        
        # Traditional log
        status = "PASSED" if success else "FAILED"
        self.info(f"[VALIDATION] {validation_type} {status}: {details.get('message', '')}")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(action_type, level)
        audit_entry.update({
            "action": "validation",
            "validation_type": validation_type,
            "success": success,
            "details": details,
            "status": status
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    def log_daily_summary(self, processed_count: int, ignored_count: int, failed_count: int, 
                         total_count: int, renamed_count: int = 0, by_type_count: Dict[str, int] = None, 
                         date_str: str = None):
        """Log daily processing summary with structured data."""
        if not date_str:
            date_str = datetime.now().strftime("%m.%d.%y")
        
        if by_type_count is None:
            by_type_count = {}
            
        # Traditional log
        self.info("=" * 50)
        self.info(f"=== DAILY SUMMARY {date_str} ===")
        self.info(f"• Processed: {processed_count} AR Ack documents (full processing)")
        self.info(f"• Renamed: {renamed_count} other document types (rename only)")
        self.info(f"• Ignored: {ignored_count} unknown document types")
        self.info(f"• Failed: {failed_count} processing errors")
        self.info(f"• Total files scanned: {total_count}")
        
        # Document type breakdown
        if by_type_count:
            self.info("--- Document Type Breakdown ---")
            for doc_type, count in sorted(by_type_count.items()):
                self.info(f"  • {doc_type}: {count}")
        
        self.info("=" * 50)
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.DAILY_SUMMARY, LogLevel.AUDIT)
        audit_entry.update({
            "action": "daily_summary",
            "date": date_str,
            "statistics": {
                "processed_count": processed_count,
                "renamed_count": renamed_count,
                "ignored_count": ignored_count,
                "failed_count": failed_count,
                "total_count": total_count,
                "by_type_count": by_type_count,
                "success_rate": round((processed_count + renamed_count) / total_count * 100, 2) if total_count > 0 else 0
            }
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    # Keep old methods for backward compatibility but make them debug level
    def log_ar_ack_identified(self, filename):
        """Log AR Ack identification."""
        self.debug(f"AR Ack document identified: {filename}")
    
    def log_data_extracted(self, case_id, client_name):
        """Log successful data extraction."""
        self.debug(f"Data extracted - Case ID: {case_id}, Client: {client_name}")
    
    def log_client_matched(self, client_name, airtable_record):
        """Log successful client matching."""
        self.debug(f"Client matched in Airtable: {client_name} -> {airtable_record}")
    
    def log_airtable_updated(self, record_id, case_id):
        """Log Airtable update."""
        self.debug(f"Airtable updated - Record ID: {record_id}, Case ID: {case_id}")
    
    def log_file_renamed_moved(self, old_name, new_name, destination):
        """Log file rename and move operation."""
        self.debug(f"File processed: {old_name} -> {new_name} moved to {destination}")
    
    def log_startup(self, config_details: Dict[str, Any] = None):
        """Log system startup with configuration details."""
        # Traditional log
        self.info("SWNA Automation service started")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.SYSTEM_START, LogLevel.AUDIT)
        audit_entry.update({
            "action": "system_startup",
            "config": config_details or {},
            "status": "STARTED"
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)
    
    def log_shutdown(self, shutdown_reason: str = "normal"):
        """Log system shutdown with reason."""
        # Traditional log
        self.info("SWNA Automation service stopped")
        
        # Structured audit log
        audit_entry = self._create_base_log_entry(ActionType.SYSTEM_STOP, LogLevel.AUDIT)
        audit_entry.update({
            "action": "system_shutdown",
            "shutdown_reason": shutdown_reason,
            "status": "STOPPED"
        })
        
        self._write_structured_log(audit_entry, self.audit_log_file)