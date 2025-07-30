import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from config.settings import SYNC_FOLDER_PATH
from src.logger import SWNALogger

class PDFFileHandler(FileSystemEventHandler):
    """Handle PDF file system events for processing."""
    
    def __init__(self, process_callback, logger=None):
        self.process_callback = process_callback
        self.logger = logger or SWNALogger()
        self.processing_files = set()  # Track files currently being processed
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and self._is_pdf_file(event.src_path):
            self._schedule_file_processing(event.src_path)
    
    def on_moved(self, event):
        """Handle file move events (which can occur during file copies)."""
        if not event.is_directory and self._is_pdf_file(event.dest_path):
            self._schedule_file_processing(event.dest_path)
    
    def _is_pdf_file(self, file_path):
        """Check if file is a PDF."""
        return file_path.lower().endswith('.pdf')
    
    def _schedule_file_processing(self, file_path):
        """Schedule file for processing with delay to ensure file is fully written."""
        if file_path in self.processing_files:
            self.logger.debug(f"File already being processed: {file_path}")
            return
        
        self.processing_files.add(file_path)
        self.logger.debug(f"Scheduling file for processing: {file_path}")
        
        # Small delay to ensure file is fully written
        time.sleep(1)
        
        try:
            # Verify file still exists and is readable
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                self.process_callback(file_path)
            else:
                self.logger.debug(f"File no longer exists or is empty: {file_path}")
        finally:
            self.processing_files.discard(file_path)

class FolderMonitor:
    """Monitor sync folder for new PDF files and trigger processing."""
    
    def __init__(self, process_callback, logger=None):
        self.logger = logger or SWNALogger()
        self.process_callback = process_callback
        self.observer = None
        self.is_running = False
        
        # Build monitoring paths
        self.monitored_paths = self._build_monitoring_paths()
    
    def _build_monitoring_paths(self):
        """Build list of paths to monitor for daily temp scan folders."""
        paths = []
        
        try:
            # Main daily temp scans path pattern
            daily_scans_base = os.path.join(SYNC_FOLDER_PATH, "1. Daily Temp Scans")
            
            # Check if base path exists
            if os.path.exists(daily_scans_base):
                paths.append(daily_scans_base)
                self.logger.debug(f"Added monitoring path: {daily_scans_base}")
            
            # Also look for dated folders (MM.DD.YY format)
            parent_folder = os.path.join(SYNC_FOLDER_PATH)
            if os.path.exists(parent_folder):
                for item in os.listdir(parent_folder):
                    if item.startswith("1. Daily Temp Scans"):
                        full_path = os.path.join(parent_folder, item)
                        if os.path.isdir(full_path) and full_path not in paths:
                            paths.append(full_path)
                            self.logger.debug(f"Added monitoring path: {full_path}")
            
            if not paths:
                self.logger.error("No valid monitoring paths found")
            
            return paths
            
        except Exception as e:
            self.logger.error(f"Failed to build monitoring paths: {str(e)}")
            return []
    
    def start_monitoring(self):
        """Start monitoring folders for new PDF files."""
        if self.is_running:
            self.logger.debug("Folder monitor already running")
            return False
        
        if not self.monitored_paths:
            self.logger.error("No paths to monitor - cannot start monitoring")
            return False
        
        try:
            self.observer = Observer()
            
            # Set up file handler
            event_handler = PDFFileHandler(self.process_callback, self.logger)
            
            # Add watchers for each monitored path
            for path in self.monitored_paths:
                if os.path.exists(path):
                    self.observer.schedule(event_handler, path, recursive=False)
                    self.logger.info(f"Started monitoring: {path}")
                else:
                    self.logger.error(f"Cannot monitor non-existent path: {path}")
            
            # Start observer
            self.observer.start()
            self.is_running = True
            self.logger.info("Folder monitoring started successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start folder monitoring: {str(e)}")
            self.is_running = False
            return False
    
    def stop_monitoring(self):
        """Stop monitoring folders."""
        if not self.is_running or not self.observer:
            return
        
        try:
            self.observer.stop()
            self.observer.join(timeout=5)  # Wait up to 5 seconds for clean shutdown
            self.is_running = False
            self.logger.info("Folder monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping folder monitoring: {str(e)}")
    
    def process_existing_files(self):
        """Process any existing PDF files in monitored folders on startup."""
        self.logger.info("Processing existing files in monitored folders")
        
        processed_count = 0
        
        for folder_path in self.monitored_paths:
            if not os.path.exists(folder_path):
                continue
                
            try:
                for filename in os.listdir(folder_path):
                    if filename.lower().endswith('.pdf'):
                        file_path = os.path.join(folder_path, filename)
                        
                        # Skip if file is currently being written (very recent)
                        if self._is_file_ready(file_path):
                            self.logger.debug(f"Processing existing file: {file_path}")
                            self.process_callback(file_path)
                            processed_count += 1
                        else:
                            self.logger.debug(f"Skipping file still being written: {file_path}")
                            
            except Exception as e:
                self.logger.error(f"Error processing existing files in {folder_path}: {str(e)}")
        
        self.logger.info(f"Processed {processed_count} existing PDF files")
    
    def _is_file_ready(self, file_path):
        """Check if file is ready for processing (not currently being written)."""
        try:
            # Check if file was modified recently (within last 5 seconds)
            mod_time = os.path.getmtime(file_path)
            current_time = time.time()
            
            if current_time - mod_time < 5:
                return False
            
            # Check if file has reasonable size
            if os.path.getsize(file_path) == 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"File readiness check failed for {file_path}: {str(e)}")
            return False