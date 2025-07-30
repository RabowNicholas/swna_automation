#!/usr/bin/env python3
"""
SWNA AR Acknowledgment Automation Service
Main entry point for the automated document processing system.
"""

import sys
import signal
import time
from config.settings import validate_config, LOG_LEVEL
from src.logger import SWNALogger
from src.folder_monitor import FolderMonitor
from src.processing_pipeline import ProcessingPipeline

class SWNAAutomationService:
    """Main service class for SWNA automation."""
    
    def __init__(self):
        self.logger = SWNALogger(LOG_LEVEL)
        self.pipeline = ProcessingPipeline(self.logger)
        self.folder_monitor = FolderMonitor(self.pipeline.process_file, self.logger)
        self.running = False
    
    def start(self):
        """Start the automation service."""
        try:
            self.logger.log_startup()
            
            # Validate configuration
            self.logger.info("Validating configuration...")
            validate_config()
            self.logger.info("Configuration validation passed")
            
            # Process existing files on startup
            self.logger.info("Processing existing files...")
            self.folder_monitor.process_existing_files()
            
            # Start folder monitoring
            self.logger.info("Starting folder monitoring...")
            if not self.folder_monitor.start_monitoring():
                self.logger.error("Failed to start folder monitoring")
                return False
            
            self.running = True
            self.logger.info("SWNA Automation service is now running")
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Main service loop
            try:
                while self.running:
                    time.sleep(1)  # Small sleep to prevent high CPU usage
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Service startup failed: {str(e)}")
            return False
    
    def stop(self):
        """Stop the automation service."""
        if not self.running:
            return
        
        self.logger.info("Stopping SWNA Automation service...")
        
        # Stop folder monitoring
        self.folder_monitor.stop_monitoring()
        
        self.running = False
        self.logger.log_shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        self.logger.info(f"Received signal {signum}")
        self.stop()

def main():
    """Main entry point."""
    print("SWNA AR Acknowledgment Automation Service")
    print("=" * 50)
    
    # Create and start service
    service = SWNAAutomationService()
    
    try:
        success = service.start()
        if not success:
            print("Failed to start service. Check logs for details.")
            sys.exit(1)
    except Exception as e:
        print(f"Service error: {str(e)}")
        sys.exit(1)
    finally:
        service.stop()

if __name__ == "__main__":
    main()