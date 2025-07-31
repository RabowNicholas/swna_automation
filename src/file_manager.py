import os
import shutil
from datetime import datetime
from config.settings import SYNC_FOLDER_PATH
from src.logger import SWNALogger

class FileManager:
    """Handle file rename and move operations."""
    
    def __init__(self, logger=None):
        self.logger = logger or SWNALogger()
    
    def generate_new_filename(self, client_name):
        """
        Generate new filename in format: AR Ack - F. Last MM.DD.YY.pdf
        Returns new filename string or None if generation fails.
        """
        try:
            # Parse client name (expected format: "First Last" or "First Middle Last")
            name_parts = client_name.strip().split()
            
            if len(name_parts) < 2:
                self.logger.error(f"Cannot generate filename - invalid client name format: {client_name}")
                return None
            
            # Get first name initial and last name
            first_name = name_parts[0]
            last_name = name_parts[-1]  # Last part is surname
            
            first_initial = first_name[0].upper()
            
            # Get current date
            current_date = datetime.now().strftime("%m.%d.%y")
            
            # Generate filename
            new_filename = f"AR Ack - {first_initial}. {last_name} {current_date}.pdf"
            
            return new_filename
            
        except Exception as e:
            self.logger.error(f"Filename generation failed: {str(e)}")
            return None
    
    def construct_client_folder_path(self, client_name_formatted):
        """
        Construct path to client's DOL Letters folder.
        Expected format: /1. SWNA Shared Folder/2. Active Clients/{Last, First}/DOL Letters/
        Returns folder path string.
        """
        try:
            base_path = os.path.join(SYNC_FOLDER_PATH, "2. Active Clients")
            client_folder = os.path.join(base_path, client_name_formatted)
            dol_letters_folder = os.path.join(client_folder, "DOL Letters")
            
            return dol_letters_folder
            
        except Exception as e:
            self.logger.error(f"Client folder path construction failed: {str(e)}")
            return None
    
    def validate_destination_folder(self, destination_path):
        """
        Check if destination folder exists.
        Returns True if exists, False otherwise.
        """
        try:
            return os.path.exists(destination_path) and os.path.isdir(destination_path)
        except Exception as e:
            self.logger.error(f"Destination folder validation failed: {str(e)}")
            return False
    
    def move_and_rename_file(self, original_file_path, client_name, client_name_formatted):
        """
        Rename and move file to client folder.
        Returns (success, new_file_path) tuple.
        """
        try:
            # Generate new filename
            new_filename = self.generate_new_filename(client_name)
            if not new_filename:
                return False, None
            
            # Construct destination folder path
            destination_folder = self.construct_client_folder_path(client_name_formatted)
            if not destination_folder:
                return False, None
            
            # REAL MODE - ACTUAL FILE VALIDATION AND MOVE
            self.logger.info(f"Validating destination folder: {destination_folder}")
            
            # Validate destination folder exists
            if not self.validate_destination_folder(destination_folder):
                self.logger.error(f"Destination folder does not exist: {destination_folder}")
                return False, None
            
            # Construct full destination path
            destination_path = os.path.join(destination_folder, new_filename)
            
            # Check if file already exists at destination
            self.logger.info(f"Checking if file exists at: {destination_path}")
            if os.path.exists(destination_path):
                self.logger.error(f"File already exists at destination: {destination_path}")
                return False, None
            
            # Perform the actual move and rename
            self.logger.info(f"Moving file: {original_file_path} -> {destination_path}")
            shutil.move(original_file_path, destination_path)
            
            # Log the operation
            original_filename = os.path.basename(original_file_path)
            self.logger.log_file_renamed_moved(original_filename, new_filename, destination_folder)
            
            return True, destination_path
            
        except Exception as e:
            self.logger.error(f"File move and rename failed: {str(e)}")
            return False, None
    
    def is_already_processed_file(self, filename):
        """
        Check if file is already processed (has AR Ack naming pattern).
        Returns True if already processed, False otherwise.
        """
        try:
            return filename.startswith("AR Ack - ") and filename.endswith(".pdf")
        except Exception as e:
            self.logger.debug(f"File processed check failed: {str(e)}")
            return False
    
    def get_file_size_mb(self, file_path):
        """
        Get file size in MB for logging purposes.
        Returns file size as float or None if error.
        """
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            return round(size_mb, 2)
        except Exception as e:
            self.logger.debug(f"File size check failed: {str(e)}")
            return None