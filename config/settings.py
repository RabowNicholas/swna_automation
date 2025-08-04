import os
from dotenv import load_dotenv

load_dotenv()

# Airtable Configuration
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
CLIENTS_TABLE_NAME = "Clients"

# File System Configuration
SYNC_FOLDER_PATH = os.getenv("SYNC_FOLDER_PATH", "")

# Processing Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Document Processing Patterns
AR_ACK_SIGNATURE = "According to our records, you have been designated as the authorized representative in the above case. As the authorized representative, you have the ability to receive correspondence, submit additional evidence, argue factual or legal issues and exercise claimant rights pertaining to the above claim."

CASE_ID_PATTERN = r'(?:Case ID Number|CASE ID|Case ID):\s*(\d+)'
CLIENT_NAME_PATTERN = r'(?:Employee Name|EMPLOYEE):\s*([^\n\r]+)'

# Validation
def validate_config():
    """Validate that all required configuration is present."""
    missing = []
    
    if not AIRTABLE_PAT:
        missing.append("AIRTABLE_PAT")
    if not AIRTABLE_BASE_ID:
        missing.append("AIRTABLE_BASE_ID")
    if not SYNC_FOLDER_PATH:
        missing.append("SYNC_FOLDER_PATH")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    if not os.path.exists(SYNC_FOLDER_PATH):
        raise ValueError(f"SYNC_FOLDER_PATH does not exist: {SYNC_FOLDER_PATH}")
    
    return True